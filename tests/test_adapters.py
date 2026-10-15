"""The two subscription CLI adapters: fixed tool-free argv, filtered environment, strict event handling."""

import json

import pytest

from atlas.ai import claude_cli, codex_cli
from atlas.ai.process import BackendError, ProcessResult, subscription_environment


def test_codex_argv_disables_every_tool_and_keeps_stdin_last(tmp_path):
    argv = codex_cli.build_argv(['codex'], 'gpt-6-luna', tmp_path / 's.json', tmp_path / 'o.json', tmp_path / 'c.json',
                                [tmp_path / 'image1.jpg'])
    assert argv[argv.index('-s') + 1] == 'read-only' and '--ephemeral' in argv and '--ignore-user-config' in argv
    disabled = {argv[i + 1] for i, value in enumerate(argv) if value == '--disable'}
    assert set(codex_cli.DISABLED_FEATURES) <= disabled and {'shell_tool', 'browser_use', 'view_image'} <= disabled
    assert argv[-2] == f'--image={tmp_path / "image1.jpg"}' and argv[-1] == '-'
    assert 'web_search="disabled"' in argv
    with pytest.raises(BackendError):
        codex_cli.build_argv(['codex'], 'gpt-x; rm -rf /', tmp_path / 's', tmp_path / 'o', tmp_path / 'c', [])


def test_claude_argv_has_no_tools_and_ignores_local_settings():
    argv = claude_cli.build_argv(['claude'], 'sonnet', {'type': 'object'})
    assert argv[argv.index('--tools') + 1] == ''
    assert argv[argv.index('--disallowedTools') + 1] == 'mcp__*'
    assert argv[argv.index('--setting-sources') + 1] == '' and '--strict-mcp-config' in argv
    assert argv[argv.index('--permission-mode') + 1] == 'dontAsk' and '--no-session-persistence' in argv
    with pytest.raises(BackendError):
        claude_cli.build_argv(['claude'], 'sonnet --dangerously-skip-permissions', {})


def test_api_keys_never_reach_the_cli(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'secret')
    monkeypatch.setenv('OPENAI_API_KEY', 'secret')
    monkeypatch.setenv('SMITHSONIAN_API_KEY', 'secret')
    environment = subscription_environment()
    assert not {k for k in environment if 'KEY' in k.upper()}
    assert 'PATH' in {k.upper() for k in environment}


def fake_claude(events, monkeypatch):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['claude'])
    monkeypatch.setattr(claude_cli, '_CHECKED', {})
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == '--version':
            return ProcessResult(0, b'2.1.284 (Claude Code)', b'')
        if argv[1:3] == ['auth', 'status']:
            return ProcessResult(0, json.dumps({'loggedIn': True, 'authMethod': 'claude.ai',
                                                'apiProvider': 'firstParty'}).encode(), b'')
        return ProcessResult(0, '\n'.join(json.dumps(e) for e in events).encode(), b'')

    return runner


def result(**extra):
    return {'type': 'result', 'is_error': False, 'structured_output': {'ok': 'yes'},
            'usage': {'input_tokens': 10, 'output_tokens': 5}, 'modelUsage': {'claude-sonnet-5-5': {}}, **extra}


def test_claude_answer_is_returned_with_usage(monkeypatch, tmp_path):
    image = tmp_path / 'a.jpg'
    image.write_bytes(b'jpeg')
    answer = claude_cli.run('look', {}, [image], model='sonnet', runner=fake_claude([result()], monkeypatch))
    assert answer['result'] == {'ok': 'yes'} and answer['model_version'] == 'claude-sonnet-5-5'


@pytest.mark.parametrize('events, code', [
    ([{'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {}}]}}, result()],
     'tool_call'),
    ([result(permission_denials=[{'tool': 'Read'}])], 'tool_call'),
    ([result(is_error=True, result='You have hit your usage limit.')], 'quota'),
    ([result(is_error=True, result='Could not generate a response.')], 'provider_error'),
    ([result(structured_output=None)], 'invalid_response'),
    ([], 'invalid_response'),
])
def test_claude_failures_are_classified(events, code, monkeypatch):
    with pytest.raises(BackendError) as raised:
        claude_cli.run('look', {}, [], model='sonnet', runner=fake_claude(events, monkeypatch))
    assert raised.value.code == code


def test_codex_tool_events_and_usage_limits_are_detected():
    tool = json.dumps({'type': 'item.started', 'item': {'type': 'command_execution', 'command': 'dir'}})
    assert codex_cli._usage(tool.encode())[3] == 'tool_call'
    limit = json.dumps({'type': 'error', 'message': 'Rate limit reached for requests'})
    assert codex_cli._usage(limit.encode())[3] == 'quota'
    other = json.dumps({'type': 'error', 'message': 'Could not generate'})
    assert codex_cli._usage(other.encode())[3] == 'provider_error'
    done = json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 3, 'output_tokens': 2}})
    assert codex_cli._usage(done.encode())[:3] == (3, 2, True)
