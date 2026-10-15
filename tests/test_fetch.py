import socket
from datetime import UTC, datetime
from email.utils import format_datetime

import httpx
import pytest

from atlas import fetch
from atlas.catalog import load
from atlas.fetch import Fetcher, FetchError

URL = 'https://api.artic.edu/test'


@pytest.fixture
def make_fetcher():
    clients = []

    def make(handler, *, addresses=('8.8.8.8',), sleep=lambda _: None):
        def resolver(host, port, **kwargs):
            return [(socket.AF_INET6 if ':' in ip else socket.AF_INET, socket.SOCK_STREAM,
                     6, '', (ip, port)) for ip in addresses]

        client = Fetcher(load()[1], transport=httpx.MockTransport(handler), resolver=resolver, sleep=sleep)
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.close()


@pytest.mark.parametrize('params', [None, {'q': 'lighthouse'}])
@pytest.mark.parametrize(('provider', 'url', 'code'), [
    ('aic', 'http://api.artic.edu/test', 'blocked_url'),
    ('aic', 'https://user:password@api.artic.edu/test', 'blocked_url'),
    ('aic', 'https://@api.artic.edu/test', 'blocked_url'),
    ('aic', 'https://api.artic.edu:444/test', 'blocked_url'),
    ('aic', 'https://api.artic.edu:invalid/test', 'blocked_url'),
    ('aic', 'https://api.artic.edu:99999/test', 'blocked_url'),
    ('aic', 'https://[invalid/test', 'blocked_url'),
    ('aic', 'https://images.metmuseum.org/test', 'blocked_host'),
    ('aic', 'https://api.artic.edu.evil.example/test', 'blocked_host'),
    ('unsplash', 'https://images.unsplash.com/test', 'provider_disabled'),
])
def test_blocked_urls_never_reach_transport(make_fetcher, provider, url, code, params):
    client = make_fetcher(lambda _: pytest.fail('blocked URL reached transport'))
    with pytest.raises(FetchError) as error:
        client.get_json(provider, url, params=params)
    assert error.value.code == code


@pytest.mark.parametrize('addresses', [
    ('10.1.2.3',), ('192.168.1.2',), ('127.0.0.1',), ('::1',),
    ('169.254.169.254',), ('fc00::1',), ('8.8.8.8', '10.0.0.1'), (),
])
def test_non_public_dns_is_refused(make_fetcher, addresses):
    client = make_fetcher(lambda _: pytest.fail('private address reached transport'), addresses=addresses)
    with pytest.raises(FetchError) as error:
        client.get_json('aic', URL)
    assert error.value.code == 'blocked_address'


@pytest.mark.parametrize(('location', 'code'), [
    ('https://evil.example/file', 'blocked_host'),
    ('http://api.artic.edu/file', 'blocked_url'),
    ('https://[invalid/file', 'blocked_url'),
])
def test_redirect_target_is_validated(make_fetcher, location, code):
    requests = []

    def handler(request):
        requests.append(request)
        assert len(requests) == 1
        return httpx.Response(302, headers={'Location': location})

    with pytest.raises(FetchError) as error:
        make_fetcher(handler).get_json('aic', URL)
    assert error.value.code == code
    assert len(requests) == 1


@pytest.mark.parametrize('redirects', [3, 4])
def test_redirect_limit(make_fetcher, redirects):
    requests = []

    def handler(request):
        requests.append(request)
        if len(requests) <= redirects:
            return httpx.Response(302, headers={'Location': f'/next/{len(requests)}'})
        return httpx.Response(200, json={'ok': True})

    client = make_fetcher(handler)
    if redirects == 3:
        assert client.get_json('aic', URL) == {'ok': True}
    else:
        with pytest.raises(FetchError) as error:
            client.get_json('aic', URL)
        assert error.value.code == 'too_many_redirects'
    assert len(requests) == 4


class Chunks(httpx.SyncByteStream):
    def __init__(self):
        self.reads = 0
        self.closed = False

    def __iter__(self):
        for chunk in (b'123', b'456', b'789'):
            self.reads += 1
            yield chunk

    def close(self):
        self.closed = True


@pytest.mark.parametrize(('declared', 'reads'), [('100', 0), (None, 2), ('3', 2)])
def test_size_cap_checks_header_and_stream(make_fetcher, declared, reads):
    stream = Chunks()
    headers = {'Content-Type': 'image/png'}
    if declared is not None:
        headers['Content-Length'] = declared
    client = make_fetcher(lambda _: httpx.Response(200, headers=headers, stream=stream))
    with pytest.raises(FetchError) as error:
        client.get('aic', URL, max_bytes=5, types=('image/png',))
    assert error.value.code == 'too_large'
    assert stream.reads == reads
    assert stream.closed


def test_exact_size_cap_and_content_type_parameters_are_accepted(make_fetcher):
    client = make_fetcher(lambda _: httpx.Response(
        200, content=b'12345', headers={'Content-Type': 'Image/PNG; charset=binary'}))
    assert client.get('aic', URL, max_bytes=5, types=('image/png',)) == b'12345'


def test_wrong_content_type(make_fetcher):
    client = make_fetcher(lambda _: httpx.Response(200, text='not an image'))
    with pytest.raises(FetchError) as error:
        client.get_image('aic', URL)
    assert error.value.code == 'wrong_type'


@pytest.mark.parametrize(('status', 'retry', 'code', 'expected'), [
    (429, '12', 'rate_limited', 12.0), (503, '5', 'rate_limited', 5.0),
    (429, 'invalid', 'rate_limited', None), (404, '', 'http_404', None),
])
def test_http_error_codes(make_fetcher, status, retry, code, expected):
    client = make_fetcher(lambda _: httpx.Response(status, headers={'Retry-After': retry}))
    with pytest.raises(FetchError) as error:
        client.get_json('aic', URL)
    assert error.value.code == code
    assert error.value.retry_after == expected


def test_retry_after_http_date(make_fetcher, monkeypatch):
    now = 1_800_000_000
    monkeypatch.setattr(fetch.time, 'time', lambda: now)
    retry = format_datetime(datetime.fromtimestamp(now + 60, UTC), usegmt=True)
    client = make_fetcher(lambda _: httpx.Response(429, headers={'Retry-After': retry}))
    with pytest.raises(FetchError) as error:
        client.get_json('aic', URL)
    assert error.value.code == 'rate_limited'
    assert error.value.retry_after == 60


@pytest.mark.parametrize('body', [b'[]', b'null', b'42', b'"text"', b'{broken', b'\xff'])
def test_json_requires_an_object(make_fetcher, body):
    client = make_fetcher(lambda _: httpx.Response(
        200, content=body, headers={'Content-Type': 'application/json'}))
    with pytest.raises(FetchError) as error:
        client.get_json('aic', URL)
    assert error.value.code == 'bad_json'


def test_throttle_sleeps_between_requests_to_same_provider(make_fetcher, monkeypatch):
    monkeypatch.setattr(fetch.time, 'monotonic', lambda: 100)
    sleeps = []
    client = make_fetcher(lambda _: httpx.Response(200, json={}), sleep=sleeps.append)
    client.get_json('aic', URL)
    assert sleeps == []
    client.get_json('aic', URL)
    assert sleeps == [pytest.approx(client.policies['aic']['min_interval_seconds'])]
    client.get_json('met', 'https://collectionapi.metmuseum.org/test')
    assert len(sleeps) == 1


def test_a_provider_cooldown_refuses_at_once_without_calling_or_sleeping(make_fetcher, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(fetch.time, 'monotonic', lambda: clock[0])
    calls, slept = [], []

    def handler(request):
        calls.append(request.url)
        return httpx.Response(429, headers={'Retry-After': '120'})

    client = make_fetcher(handler, sleep=slept.append)
    with pytest.raises(FetchError):
        client.get_json('aic', URL)
    clock[0] += 30
    with pytest.raises(FetchError) as error:
        client.get_image('aic', URL)  # any later request to that provider waits out the same cooldown
    assert error.value.code == 'rate_limited' and error.value.retry_after == pytest.approx(90)
    assert len(calls) == 1 and all(wait <= 1 for wait in slept)
    clock[0] += 91
    with pytest.raises(FetchError):
        client.get_json('aic', URL)
    assert len(calls) == 2  # asked again once the provider's wait was over
