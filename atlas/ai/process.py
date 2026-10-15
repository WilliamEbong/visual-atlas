"""Bounded subprocess transport (adapted from Qualia); vendor arguments live in claude_cli.py / codex_cli.py."""

import ctypes
import json
import math
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

MAX_INPUT_BYTES = 6_291_456  # base64 images travel on stdin for Claude
MAX_OUTPUT_BYTES = 262_144


class BackendError(ValueError):
    """Safe failure metadata for ledger accounting, never provider text or credentials."""

    def __init__(self, code, record=None, *, input_tokens=0, output_tokens=0,
                 cli_version='unknown'):
        self.code = code
        self.record = record
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cli_version = cli_version
        self.usage = {'input_tokens': input_tokens, 'output_tokens': output_tokens}
        label = str(record).replace('\n', ' ').replace('\r', ' ')[:80]
        super().__init__(f'AI backend {code}; record {label}')


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    failure: str | None = None


class _WindowsJob:
    """Kill ordinary child-process descendants when the private job handle closes.

    Assigned before supplying stdin: an untrusted classification prompt is never
    delivered unless lifecycle containment succeeds. This is not a file sandbox.
    """

    def __init__(self, process):
        from ctypes import wintypes as w

        class BasicLimits(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                        ('flags', w.DWORD), ('min_working_set', ctypes.c_size_t),
                        ('max_working_set', ctypes.c_size_t), ('active_processes', w.DWORD),
                        ('affinity', ctypes.c_size_t), ('priority', w.DWORD),
                        ('scheduling', w.DWORD)]

        class Limits(ctypes.Structure):
            _fields_ = [('basic', BasicLimits), ('io_counters', ctypes.c_uint64 * 6),
                        ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                        ('peak_process_memory', ctypes.c_size_t),
                        ('peak_job_memory', ctypes.c_size_t)]

        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int,
                                                     ctypes.c_void_p, w.DWORD]
        self.api.SetInformationJobObject.restype = w.BOOL
        self.api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.api.AssignProcessToJobObject.restype = w.BOOL
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.api.CloseHandle.restype = w.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError('process containment unavailable')
        limits = Limits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        if (not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits),
                                                ctypes.sizeof(limits))
                or not self.api.AssignProcessToJobObject(self.handle, int(process._handle))):
            self.close()
            raise OSError('process containment unavailable')

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def _stop_tree(process, job):
    if job is not None:
        job.close()
    elif os.name != 'nt':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass


def run_process(argv, *, prompt, cwd, env, timeout_seconds=90,
                max_output_bytes=MAX_OUTPUT_BYTES, output_path=None, cancel=None):
    """Collect bounded bytes with a deadline, including non-reading stdin/descendants.

    Limits protect local processing; they do not imply a provider token/billing cap.
    Provider text remains private to the calling adapter and is never in exceptions.
    """
    data = prompt.encode('utf-8')
    if (not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 600
            or not isinstance(max_output_bytes, int) or not 0 < max_output_bytes <= 1_048_576
            or len(data) > MAX_INPUT_BYTES):
        return ProcessResult(-1, b'', b'', 'input_limit')
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, env=env, shell=False, close_fds=True,
            start_new_session=os.name != 'nt',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
    except (OSError, ValueError):
        return ProcessResult(-1, b'', b'', 'unavailable')
    job = None
    try:
        if os.name == 'nt':
            job = _WindowsJob(process)
    except OSError:
        _stop_tree(process, job)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        return ProcessResult(-1, b'', b'', 'containment_unavailable')

    output = [bytearray(), bytearray()]
    lock = threading.Lock()
    overflow = threading.Event()

    def read_stream(stream, index):
        try:
            while chunk := stream.read(min(8192, max_output_bytes + 1)):
                with lock:
                    remaining = max_output_bytes - len(output[0]) - len(output[1])
                    output[index].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        overflow.set()
        except (OSError, ValueError):
            pass
        finally:
            stream.close()

    def write_input():
        try:
            process.stdin.write(data)
            process.stdin.flush()
        except (OSError, ValueError):
            pass
        finally:
            process.stdin.close()

    readers = [threading.Thread(target=read_stream, args=(process.stdout, 0), daemon=True),
               threading.Thread(target=read_stream, args=(process.stderr, 1), daemon=True)]
    writer = threading.Thread(target=write_input, daemon=True)
    for thread in (*readers, writer):
        thread.start()
    failure = None
    try:
        while True:
            if output_path is not None:
                try:
                    if Path(output_path).stat().st_size > max_output_bytes:
                        overflow.set()
                except FileNotFoundError:
                    pass
                except OSError:
                    failure = 'invalid_response'
            if overflow.is_set():
                failure = 'output_limit'
            if cancel is not None and cancel.is_set():
                failure = 'cancelled'
            if time.monotonic() - started >= timeout_seconds:
                failure = failure or 'timeout'
            if failure:
                break
            if process.poll() is not None:
                # Also stops descendants that inherited pipes after the parent exited.
                _stop_tree(process, job)
                if not any(thread.is_alive() for thread in readers):
                    break
            time.sleep(.01)
    finally:
        _stop_tree(process, job)
        for thread in (*readers, writer):
            thread.join(timeout=1)
    if overflow.is_set():
        failure = 'output_limit'
    return ProcessResult(process.returncode if process.returncode is not None else -1,
                         bytes(output[0]), bytes(output[1]), failure)


def subscription_environment():
    """Allow runtime/login-location variables, never API keys or executable injection."""
    allowed = {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP',
               'HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA',
               'PROGRAMFILES', 'PROGRAMFILES(X86)', 'USERNAME', 'USERDOMAIN',
               'LANG', 'LC_ALL', 'LC_CTYPE', 'CODEX_HOME', 'CLAUDE_CONFIG_DIR',
               'SSL_CERT_FILE', 'SSL_CERT_DIR', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY'}
    return {key: value for key, value in os.environ.items() if key.upper() in allowed}


def cli_version(probe, minimum, record=None):
    """Return the installed CLI version; only versions below the supported minimum are refused."""
    match = re.search(rb'\b(\d+\.\d+\.\d+)(?:[-+][a-zA-Z0-9.-]+)*', probe.stdout)
    version = match.group().decode('ascii') if match else 'unknown'
    if probe.failure or probe.returncode:
        raise BackendError('unavailable', record, cli_version=version)
    if not match or tuple(map(int, match.group(1).split(b'.'))) < tuple(map(int, minimum.split('.'))):
        error = BackendError('unsupported_version', record, cli_version=version)
        error.args = (f'{error}; update your CLI to {minimum} or newer',)
        raise error
    return version


def check_unsupported_flag(result, argv, record=None, **metadata):
    """Name a flag Visual Atlas passed that a newer CLI no longer accepts; never echo CLI output."""
    if result.failure or not result.returncode:
        return
    for line in (result.stderr + b'\n' + result.stdout).decode('utf-8', errors='replace').splitlines():
        if not re.search(r'unknown\s+(?:option|argument)|unexpected\s+argument|unrecogni[sz]ed', line, re.I):
            continue
        for flag in re.findall(r'(?<![\w-])--?[A-Za-z][A-Za-z0-9-]*(?![\w-])', line):
            if flag in argv:
                error = BackendError('unsupported_flag', record, **metadata)
                error.flag = flag
                error.args = (f'{error}; flag {flag}',)
                raise error from None


def token_count(value):
    if type(value) is not int or value < 0:
        raise ValueError('invalid usage')
    return value


def json_object(data):
    def reject_constant(_):
        raise ValueError('nonfinite JSON')

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON property')
            result[key] = value
        return result

    result = json.loads(data, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(result, dict):
        raise ValueError('expected object')
    return result
