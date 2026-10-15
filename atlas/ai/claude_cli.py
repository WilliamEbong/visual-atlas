"""Claude Code CLI adapter: the user's own subscription, no tools, images as base64 blocks on stdin.

Pattern from Qualia's claude_cli.py; image input proven live on 2026-10-15 (CLI 2.1.284)."""

import base64
import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path

from atlas.ai.process import (
    BackendError,
    check_unsupported_flag,
    cli_version,
    json_object,
    run_process,
    subscription_environment,
    token_count,
)

MIN_VERSION = '2.1.284'
NAME = 'claude'
_CHECKED: dict = {}  # ponytail: per-process cache of version + sign-in (10 min); restart picks up changes


def resolve_command():
    """Native claude.exe; never a .cmd/.ps1 shim, so prompts never pass through a shell."""
    found = shutil.which('claude')
    if not found:
        return None
    path = Path(found).resolve()
    if os.name != 'nt' or path.suffix.lower() == '.exe':
        return [str(path)]
    native = path.parent / 'node_modules/@anthropic-ai/claude-code/bin/claude.exe'
    return [str(native)] if native.is_file() else None


def build_argv(command, model, schema):
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,119}', model):
        raise BackendError('invalid_model')
    return [*command, '-p', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
            '--json-schema', json.dumps(schema, allow_nan=False), '--model', model, '--max-turns', '2',
            '--no-session-persistence', '--tools', '', '--disallowedTools', 'mcp__*', '--strict-mcp-config',
            '--setting-sources', '', '--safe-mode', '--disable-slash-commands', '--no-chrome',
            '--permission-mode', 'dontAsk', '--permission-prompts', 'none']


def message(prompt: str, images: list[Path]) -> str:
    content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg',
                                            'data': base64.b64encode(Path(path).read_bytes()).decode('ascii')}}
               for path in images]
    content.append({'type': 'text', 'text': prompt})
    return json.dumps({'type': 'user', 'message': {'role': 'user', 'content': content}}) + '\n'


def _environment():
    environment = subscription_environment()
    environment.update(CLAUDE_CODE_MAX_RETRIES='0', MAX_STRUCTURED_OUTPUT_RETRIES='1',
                       CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1', CLAUDE_CODE_MAX_OUTPUT_TOKENS='8192')
    return environment


def check(runner=run_process, force=False) -> str:
    """Return the CLI version after confirming a claude.ai subscription sign-in. Cached for 10 minutes."""
    if not force and _CHECKED.get('until', 0) > time.monotonic():
        return _CHECKED['version']
    command = resolve_command()
    if command is None:
        raise BackendError('unavailable')
    environment = _environment()
    with tempfile.TemporaryDirectory(prefix='atlas-claude-') as directory:
        probe = runner([*command, '--version'], prompt='', cwd=directory, env=environment,
                       timeout_seconds=15, max_output_bytes=8192)
        version = cli_version(probe, MIN_VERSION)
        auth = runner([*command, 'auth', 'status', '--json'], prompt='', cwd=directory, env=environment,
                      timeout_seconds=15, max_output_bytes=8192)
    try:
        status = json_object(auth.stdout)
        if (auth.failure or auth.returncode or status.get('loggedIn') is not True
                or status.get('authMethod') != 'claude.ai' or status.get('apiProvider') != 'firstParty'):
            raise ValueError
    except (ValueError, TypeError, UnicodeError, RecursionError):
        # Status output can contain account details; never keep or echo it.
        raise BackendError('subscription_auth_required', cli_version=version) from None
    _CHECKED.update(version=version, until=time.monotonic() + 600)
    return version


def run(prompt: str, schema: dict, images: list[Path], *, model: str, record=None, timeout: int = 180,
        cancel=None, runner=run_process) -> dict:
    version = check(runner)
    argv = build_argv(resolve_command(), model, schema)
    with tempfile.TemporaryDirectory(prefix='atlas-claude-') as directory:
        result = runner(argv, prompt=message(prompt, images), cwd=directory, env=_environment(),
                        timeout_seconds=timeout, max_output_bytes=1_048_576, cancel=cancel)
    final, violation = None, None
    for line in result.stdout.decode('utf-8', errors='replace').splitlines():
        try:
            event = json_object(line)
        except (ValueError, RecursionError):
            continue
        if event.get('type') == 'assistant':
            for block in (event.get('message') or {}).get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'tool_use' and block.get('name') != 'StructuredOutput':
                    violation = 'tool_call'
        if event.get('type') == 'result':
            final = event
    if final is None:
        check_unsupported_flag(result, argv, record, cli_version=version)
        raise BackendError(result.failure or 'invalid_response', record, cli_version=version)
    try:
        usage = final.get('usage') or {}
        inputs = sum(token_count(usage.get(key, 0)) for key in
                     ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))
        outputs = token_count(usage.get('output_tokens', 0))
    except ValueError:
        inputs = outputs = 0
    metadata = {'input_tokens': inputs, 'output_tokens': outputs, 'cli_version': version}
    if result.failure:
        raise BackendError(result.failure, record, **metadata)
    if violation or final.get('permission_denials'):
        raise BackendError('tool_call', record, **metadata)
    if result.returncode or final.get('is_error') is True:
        text = str(final.get('result', '')).lower()
        code = 'quota' if any(word in text for word in ('limit', 'quota', 'rate')) else 'provider_error'
        raise BackendError(code, record, **metadata)
    output = final.get('structured_output')
    if not isinstance(output, dict):
        raise BackendError('invalid_response', record, **metadata)
    used = final.get('modelUsage')
    names = sorted(name for name in used if isinstance(name, str)) if isinstance(used, dict) else []
    model_version = ','.join(n for n in names if re.fullmatch(r'[A-Za-z0-9._:@/-]{1,120}', n))[:400] or None
    return {'result': output, **metadata, 'model_version': model_version}
