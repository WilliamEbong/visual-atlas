"""Codex CLI adapter: the user's own ChatGPT sign-in, every tool feature disabled, images via --image.

Pattern from Qualia's codex_cli.py; image input proven live on 2026-10-15 (CLI 0.160.0)."""

import copy
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

MIN_VERSION = '0.160.0'
NAME = 'codex'
PROVIDER_ID = 'atlas-subscription'
DISABLED_FEATURES = (
    'shell_tool', 'apps', 'plugins', 'browser_use', 'browser_use_external', 'browser_use_full_cdp_access',
    'computer_use', 'in_app_browser', 'image_generation', 'view_image', 'multi_agent', 'multi_agent_v2',
    'code_mode', 'code_mode_only', 'code_mode_host', 'hooks', 'goals', 'memories', 'sleep_tool',
    'tool_suggest', 'skill_search', 'workspace_dependencies', 'request_permissions_tool',
    'send_message_to_user_async',
)
_CHECKED: dict = {}  # ponytail: per-process cache of version + sign-in (10 min)


def resolve_command():
    found = shutil.which('codex')
    if not found:
        return None
    path = Path(found).resolve()
    if os.name != 'nt' or path.suffix.lower() == '.exe':
        return [str(path)]
    wrapper = path.parent / 'node_modules/@openai/codex/bin/codex.js'
    node = shutil.which('node')
    if wrapper.is_file() and node:
        return [str(Path(node).resolve()), str(wrapper)]  # avoid .cmd/.ps1 shells
    return None


def load_catalog(model: str) -> dict:
    """Clone the CLI's non-secret model record, switching off every tool capability for this run."""
    home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    try:
        data = (home / 'models_cache.json').read_bytes()
        if len(data) > 8_388_608:
            raise ValueError
        matches = [record for record in json_object(data)['models'] if record.get('slug') == model]
        if len(matches) != 1 or 'image' not in matches[0].get('input_modalities', []):
            raise ValueError
        record = copy.deepcopy(matches[0])
        record.update(apply_patch_tool_type=None, experimental_supported_tools=[], shell_type='disabled',
                      tool_mode='direct', supports_search_tool=False)
        return {'models': [record]}
    except (OSError, KeyError, TypeError, AttributeError, ValueError, UnicodeError, RecursionError):
        raise BackendError('unavailable') from None


def build_argv(command, model, schema_path, output_path, catalog_path, images):
    if not isinstance(model, str) or not re.fullmatch(r'gpt-[a-zA-Z0-9_.-]{1,110}', model):
        raise BackendError('invalid_model')
    argv = [*command, 'exec', '--ignore-user-config', '--strict-config', '-s', 'read-only', '--ephemeral',
            '--skip-git-repo-check', '--output-schema', str(schema_path), '-o', str(output_path), '-m', model,
            '--json']
    settings = {'web_search': 'disabled', 'model_reasoning_effort': 'low', 'agents.enabled': False,
                'tools.update_plan.enabled': False, 'tools.experimental_request_user_input.enabled': False,
                'project_doc_max_bytes': 0, 'model_catalog_json': str(catalog_path),
                'model_provider': PROVIDER_ID, 'forced_login_method': 'chatgpt',
                f'model_providers.{PROVIDER_ID}.name': 'OpenAI',
                f'model_providers.{PROVIDER_ID}.requires_openai_auth': True,
                f'model_providers.{PROVIDER_ID}.wire_api': 'responses',
                f'model_providers.{PROVIDER_ID}.supports_websockets': False,
                f'model_providers.{PROVIDER_ID}.request_max_retries': 0,
                f'model_providers.{PROVIDER_ID}.stream_max_retries': 0}
    for key, value in settings.items():
        argv.extend(('-c', key + '=' + json.dumps(value)))
    for feature in DISABLED_FEATURES:
        argv.extend(('--disable', feature))
    # '=' form: the multi-value --image flag must not swallow the trailing '-' (prompt on stdin).
    return [*argv, *(f'--image={path}' for path in images), '-']


def _usage(data: bytes):
    inputs = outputs = 0
    seen, violation = False, None
    for line in data.decode('utf-8', errors='replace').splitlines():
        if not line.strip():
            continue
        try:
            event = json_object(line)
            if event.get('type') == 'turn.completed':
                inputs += token_count(event['usage']['input_tokens'])
                outputs += token_count(event['usage']['output_tokens'])
                seen = True
            if event.get('type') in ('item.started', 'item.completed', 'item.updated'):
                if event['item'].get('type') not in ('agent_message', 'reasoning'):
                    violation = 'tool_call'
            if event.get('type') in ('function_call', 'custom_tool_call', 'tool_call'):
                violation = 'tool_call'
            if event.get('type') in ('error', 'turn.failed'):
                text = json.dumps(event).lower()
                violation = violation or ('quota' if any(w in text for w in ('limit', 'quota', 'rate')) else
                                          'provider_error')
        except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
            violation = violation or 'invalid_response'
    return inputs, outputs, seen, violation


def check(runner=run_process, force=False) -> str:
    if not force and _CHECKED.get('until', 0) > time.monotonic():
        return _CHECKED['version']
    command = resolve_command()
    if command is None:
        raise BackendError('unavailable')
    environment = subscription_environment()
    with tempfile.TemporaryDirectory(prefix='atlas-codex-') as directory:
        probe = runner([*command, '--version'], prompt='', cwd=directory, env=environment,
                       timeout_seconds=15, max_output_bytes=8192)
        version = cli_version(probe, MIN_VERSION)
        status = runner([*command, 'login', 'status'], prompt='', cwd=directory, env=environment,
                        timeout_seconds=15, max_output_bytes=8192)
    text = (status.stdout + status.stderr).strip()
    if status.failure or status.returncode or not text.startswith(b'Logged in using ChatGPT'):
        raise BackendError('subscription_auth_required', cli_version=version)
    _CHECKED.update(version=version, until=time.monotonic() + 600)
    return version


def run(prompt: str, schema: dict, images: list[Path], *, model: str, record=None, timeout: int = 180,
        cancel=None, runner=run_process) -> dict:
    version = check(runner)
    command = resolve_command()
    catalog = load_catalog(model)
    with tempfile.TemporaryDirectory(prefix='atlas-codex-') as directory:
        root = Path(directory)
        cwd = root / 'cwd'
        cwd.mkdir()
        copies = []
        for index, path in enumerate(images):
            target = root / f'image{index + 1}.jpg'
            target.write_bytes(Path(path).read_bytes())
            copies.append(target)
        schema_path, output_path, catalog_path = root / 'schema.json', root / 'result.json', root / 'catalog.json'
        schema_path.write_text(json.dumps(schema, allow_nan=False), encoding='utf-8')
        catalog_path.write_text(json.dumps(catalog, allow_nan=False), encoding='utf-8')
        argv = build_argv(command, model, schema_path, output_path, catalog_path, copies)
        result = runner(argv, prompt=prompt, cwd=cwd, env=subscription_environment(), timeout_seconds=timeout,
                        max_output_bytes=1_048_576, output_path=output_path, cancel=cancel)
        inputs, outputs, seen, violation = _usage(result.stdout)
        metadata = {'input_tokens': inputs, 'output_tokens': outputs, 'cli_version': version}
        if violation == 'tool_call':
            raise BackendError('tool_call', record, **metadata)
        check_unsupported_flag(result, argv, record, **metadata)
        if result.failure:
            raise BackendError(result.failure, record, **metadata)
        if violation:
            raise BackendError(violation, record, **metadata)
        if result.returncode:
            raise BackendError('provider_error', record, **metadata)
        try:
            data = output_path.read_bytes()
            if len(data) > 1_048_576 or not seen:
                raise ValueError
            output = json_object(data)
        except (OSError, ValueError, UnicodeError, RecursionError):
            raise BackendError('invalid_response', record, **metadata) from None
    return {'result': output, **metadata, 'model_version': model}
