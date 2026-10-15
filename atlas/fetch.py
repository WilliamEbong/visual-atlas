"""The only network path: https to allowlisted provider hosts, public addresses, bounded bytes."""

import ipaddress
import json
import socket
import threading
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

import httpx

MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_IMAGE_BYTES = 25 * 1024 * 1024
IMAGE_TYPES = ('image/jpeg', 'image/png', 'image/webp')
MAX_REDIRECTS = 3


class FetchError(Exception):
    """Plain-language network failure with a stable code; never contains response bodies."""

    def __init__(self, code: str, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.code = code
        self.retry_after = retry_after


def _public(address: str) -> bool:
    try:
        return ipaddress.ip_address(address.split('%')[0]).is_global
    except ValueError:
        return False


class Fetcher:
    def __init__(self, policies: dict, *, transport=None, resolver=socket.getaddrinfo, sleep=time.sleep):
        self.policies = {p['id']: p for p in policies['providers'] if p.get('status') == 'enabled'}
        self.user_agent = policies['user_agent']
        self.resolver = resolver
        self.sleep = sleep
        self.client = httpx.Client(transport=transport, follow_redirects=False, trust_env=False,
                                   timeout=httpx.Timeout(30, connect=10),
                                   headers={'User-Agent': self.user_agent})
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def close(self):
        self.client.close()

    def check_url(self, provider: str, url: str):
        policy = self.policies.get(provider)
        if policy is None:
            raise FetchError('provider_disabled', f'{provider} is not an enabled source.')
        try:
            parts = urlsplit(url)
            port = parts.port
        except ValueError:
            raise FetchError('blocked_url', 'Only plain https addresses are fetched.') from None
        host = (parts.hostname or '').lower()
        if parts.scheme != 'https' or parts.username is not None or parts.password is not None or port not in (None, 443):
            raise FetchError('blocked_url', 'Only plain https addresses are fetched.')
        if host not in policy['hosts']:
            raise FetchError('blocked_host', f'{host or "That address"} is not one of {policy["name"]}\'s hosts.')
        try:
            addresses = {info[4][0] for info in self.resolver(host, 443, type=socket.SOCK_STREAM)}
        except OSError:
            raise FetchError('dns_failed', f'Could not look up {host}. Check the internet connection.') from None
        if not addresses or not all(_public(address) for address in addresses):
            raise FetchError('blocked_address', f'{host} resolved to a private or local address.')

    def _throttle(self, provider: str):
        gap = float(self.policies[provider].get('min_interval_seconds', 1))
        with self._lock:
            wait = self._last.get(provider, 0) + gap - time.monotonic()
            if wait > 0:
                self.sleep(wait)
            self._last[provider] = time.monotonic()

    def get(self, provider: str, url: str, *, max_bytes: int, types: tuple[str, ...], headers=None) -> bytes:
        for _ in range(MAX_REDIRECTS + 1):
            self.check_url(provider, url)
            self._throttle(provider)
            try:
                with self.client.stream('GET', url, headers=headers or {}) as response:
                    stream = response.extensions.get('network_stream')
                    if stream is not None:
                        peer = stream.get_extra_info('server_addr')
                        if peer and not _public(str(peer[0])):
                            raise FetchError('blocked_address', 'The connection reached a private address.')
                    if response.is_redirect:
                        location = response.headers.get('location', '')
                        try:
                            url = urljoin(url, location)
                        except ValueError:
                            raise FetchError('blocked_url', 'The redirect contains an invalid address.') from None
                        continue
                    if response.status_code in (429, 503):
                        retry = response.headers.get('retry-after', '')
                        try:
                            retry_after = (float(retry) if retry.isdigit() else
                                           max(0.0, parsedate_to_datetime(retry).timestamp() - time.time()))
                        except (TypeError, ValueError, OverflowError):
                            retry_after = None
                        raise FetchError('rate_limited', f'{self.policies[provider]["name"]} asked us to slow down.',
                                         retry_after)
                    if response.status_code != 200:
                        raise FetchError(f'http_{response.status_code}',
                                         f'{self.policies[provider]["name"]} answered HTTP {response.status_code}.')
                    kind = response.headers.get('content-type', '').split(';')[0].strip().lower()
                    if kind not in types:
                        raise FetchError('wrong_type', f'Expected {" or ".join(types)}, received {kind or "nothing"}.')
                    declared = response.headers.get('content-length', '')
                    if declared.isdigit() and int(declared) > max_bytes:
                        raise FetchError('too_large', 'The file is larger than the size limit.')
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > max_bytes:
                            raise FetchError('too_large', 'The file is larger than the size limit.')
                    return bytes(data)
            except httpx.TimeoutException:
                raise FetchError('timeout', f'{self.policies[provider]["name"]} did not answer in time.') from None
            except httpx.HTTPError:
                raise FetchError('network', f'Could not reach {self.policies[provider]["name"]}.') from None
        raise FetchError('too_many_redirects', 'The address redirected too many times.')

    def get_json(self, provider: str, url: str, params: dict | None = None, headers=None) -> dict:
        if params:
            self.check_url(provider, url)  # Validate before HTTPX can normalize away invalid userinfo.
            url = str(httpx.URL(url, params=params))
        data = self.get(provider, url, max_bytes=MAX_JSON_BYTES, types=('application/json',), headers=headers)
        try:
            value = json.loads(data)
        except (ValueError, UnicodeDecodeError):
            raise FetchError('bad_json', 'The source returned unreadable data.') from None
        if not isinstance(value, dict):
            raise FetchError('bad_json', 'The source returned unexpected data.')
        return value

    def get_image(self, provider: str, url: str, headers=None) -> bytes:
        return self.get(provider, url, max_bytes=MAX_IMAGE_BYTES, types=IMAGE_TYPES, headers=headers)
