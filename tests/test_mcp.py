"""MCP server: a real stdio round trip in a subprocess, protocol errors, validation, and read-only behaviour."""

import base64
import io
import json
import os
import subprocess
import sys

import pytest
from PIL import Image

from atlas import jobs, layers, mcp_server, transfer
from atlas.home import REPO


@pytest.fixture(scope='module')
def starter_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('mcp') / 'home'
    with jobs.open_store(home) as store:
        transfer.import_starter(store, home, REPO / 'starter')
    return home


@pytest.fixture
def env(starter_home, monkeypatch, tmp_path):
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(starter_home))
    monkeypatch.delenv('VISUAL_ATLAS_DESIGN_SYSTEMS', raising=False)
    monkeypatch.setattr(layers, 'GENERATED', tmp_path / 'none')
    return starter_home


def rpc(mid, method, params=None):
    return {'jsonrpc': '2.0', 'id': mid, 'method': method, **({'params': params} if params is not None else {})}


def call(name, arguments):
    return mcp_server.handle(rpc(1, 'tools/call', {'name': name, 'arguments': arguments}))['result']


def test_stdio_round_trip_in_a_subprocess(starter_home):
    messages = [rpc(1, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                      'clientInfo': {'name': 'test', 'version': '1'}}),
                {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                rpc(2, 'tools/list'),
                rpc(3, 'tools/call', {'name': 'advise', 'arguments': {'brief': 'a calm scene with one small boat'}}),
                rpc(4, 'tools/call', {'name': 'nope', 'arguments': {}}),
                rpc(5, 'resources/list')]
    environment = {**os.environ, 'VISUAL_ATLAS_HOME': str(starter_home), 'PYTHONIOENCODING': 'utf-8'}
    environment.pop('VISUAL_ATLAS_DESIGN_SYSTEMS', None)
    process = subprocess.run([sys.executable, '-c', 'from atlas.mcp_server import serve; serve()'],
                             input='\n'.join(json.dumps(m) for m in messages) + '\nnot json\n', capture_output=True,
                             text=True, encoding='utf-8', env=environment, cwd=REPO, timeout=120)
    replies = [json.loads(line) for line in process.stdout.splitlines()]
    assert [r['id'] for r in replies] == [1, 2, 3, 4, 5, None]  # the notification gets no reply
    assert replies[0]['result']['protocolVersion'] == '2025-06-18'
    assert replies[0]['result']['capabilities'] == {'tools': {'listChanged': False}}
    tools = replies[1]['result']['tools']
    assert {t['name'] for t in tools} == {'advise', 'search_references', 'get_reference', 'view_reference',
                                         'list_techniques', 'get_technique', 'route_brief', 'suggest_directions',
                                         'similar_references', 'search_open_collections'}
    assert all(t['annotations']['readOnlyHint'] and not t['annotations']['destructiveHint'] for t in tools)
    assert [t['name'] for t in tools if t['annotations']['openWorldHint']] == ['search_open_collections']
    advice = replies[2]['result']
    assert advice['isError'] is False and advice['structuredContent']['results']
    assert json.loads(advice['content'][0]['text']) == advice['structuredContent']
    assert replies[3]['error']['code'] == -32602 and replies[4]['error']['code'] == -32601
    assert replies[5]['error']['code'] == -32700


def test_unknown_protocol_version_gets_the_servers_latest():
    reply = mcp_server.handle(rpc(1, 'initialize', {'protocolVersion': '1999-01-01'}))
    assert reply['result']['protocolVersion'] == mcp_server.VERSIONS[0]


@pytest.mark.parametrize('name, arguments, message', [
    ('advise', {}, 'brief is required'), ('advise', {'brief': 'x', 'extra': 1}, 'unknown argument'),
    ('advise', {'brief': 'x', 'use': 'sell'}, 'must be one of'), ('advise', {'brief': 'x', 'limit': 99}, 'whole number'),
    ('advise', {'brief': 'x', 'limit': True}, 'whole number'), ('search_references', {'techniques': 'silhouette'}, 'list'),
    ('get_reference', {'ref': 'C:\\Windows\\win.ini'}, 'ref looks like'), ('view_reference', {'ref': '../../x'}, 'ref'),
    ('get_technique', {'id': 'nope'}, 'unknown technique'), ('list_techniques', {'goal': 'nope'}, 'unknown goal'),
    ('get_reference', {'ref': 'library:99999'}, 'no reference')])
def test_bad_arguments_are_tool_errors_not_crashes(env, name, arguments, message):
    result = call(name, arguments)
    assert result['isError'] is True and message in result['content'][0]['text']


def test_view_reference_returns_a_bounded_jpeg_with_its_credit(env):
    ref = call('search_references', {'techniques': ['silhouette'], 'limit': 1})['structuredContent']['results'][0]
    result = call('view_reference', {'ref': ref['ref'], 'max_size': 256})
    image, caption = result['content']
    assert image['type'] == 'image' and image['mimeType'] == 'image/jpeg'
    with Image.open(io.BytesIO(base64.b64decode(image['data']))) as picture:
        assert max(picture.size) <= 256
    assert json.loads(caption['text'])['credit']


def test_publish_use_keeps_only_free_licences(env):
    result = call('advise', {'brief': 'make one thing stand out', 'use': 'publish', 'limit': 10})['structuredContent']
    assert result['results'] and all(r['licence']['code'] in ('cc0', 'pd', 'cc-by') for r in result['results'])


def test_tools_never_write_or_start_jobs(env):
    with jobs.open_store(env) as store:
        before = {table: store.one(f'SELECT COUNT(*) AS n FROM {table}')['n']
                  for table in ('jobs', 'images', 'annotations', 'annotation_history', 'analyses', 'collections')}
    for name, arguments in (('advise', {'brief': 'show scale'}), ('list_techniques', {}),
                            ('get_technique', {'id': 'framing'}), ('route_brief', {'brief': 'tea house'}),
                            ('search_references', {'goals': ['create-calm']}),
                            ('suggest_directions', {'brief': 'calm cover', 'goals': ['create-calm']}),
                            ('similar_references', {'ref': 'library:1', 'limit': 2})):
        assert call(name, arguments)['isError'] is False
    with jobs.open_store(env) as store:
        after = {table: store.one(f'SELECT COUNT(*) AS n FROM {table}')['n'] for table in before}
    assert after == before


def test_cli_advise_refs_and_ref(env):
    from typer.testing import CliRunner

    from atlas.cli import app
    runner = CliRunner()
    advice = runner.invoke(app, ['advise', 'a lone figure in a wide empty landscape', '--limit', '3'])
    assert advice.exit_code == 0, advice.output
    data = json.loads(advice.output)
    assert data['results'] and data['guidance']
    text = runner.invoke(app, ['refs', '--technique', 'silhouette', '--limit', '2', '--text'])
    assert text.exit_code == 0 and 'Shows Silhouette' in text.output and 'library:' in text.output
    one = runner.invoke(app, ['ref', data['results'][0]['ref']])
    assert one.exit_code == 0 and json.loads(one.output)['licence']['label']
    assert runner.invoke(app, ['ref', 'library:999999']).exit_code == 1
    steered = json.loads(runner.invoke(app, ['advise', 'zzqx', '--technique', 'silhouette']).output)
    assert [t['id'] for t in steered['reading']['techniques']] == ['silhouette']
    options = runner.invoke(app, ['directions', 'calm slide', '--goal', 'create-calm', '--count', '2', '--text'])
    assert options.exit_code == 0 and options.output.startswith('1. ') and '\n2. ' in options.output
    empty = runner.invoke(app, ['advise', 'zzqx', '--text'])
    assert 'No reference matched' in empty.output


def test_an_agent_can_pass_the_ids_the_words_missed(env):
    missed = call('advise', {'brief': 'cover for a report on urban heat islands'})['structuredContent']
    assert not missed['reading']['techniques'] and len(missed['codebook']['techniques']) == 26
    steered = call('advise', {'brief': 'cover for a report on urban heat islands', 'techniques': ['silhouette']})
    result = steered['structuredContent']
    assert [t['id'] for t in result['reading']['techniques']] == ['silhouette'] and 'codebook' not in result
    assert result['guidance'][0]['id'] == 'silhouette'
    assert call('advise', {'brief': 'x', 'techniques': ['not-a-technique']})['isError'] is True


def test_directions_are_distinct_techniques_each_shown_by_its_references(env):
    result = call('suggest_directions', {'brief': 'opening slide that feels calm', 'goals': ['create-calm'],
                                         'count': 3})['structuredContent']
    ids = [d['technique']['id'] for d in result['directions']]
    assert len(ids) == len(set(ids)) == 3
    for direction in result['directions']:
        assert direction['references'] and direction['make_sure'] and direction['serves'] == ['Create calm and order']
        assert all(any(t['id'] == direction['technique']['id'] for t in r['techniques']) for r in direction['references'])
    assert call('suggest_directions', {'brief': 'x', 'count': 9})['isError'] is True
