"""Double-click launcher (adapted from Qualia): app window, idle shutdown, port reuse and plain-language failures."""

import http.server
import re
import socket
import threading
import time
import urllib.request

import pytest

from atlas import launcher


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


@pytest.fixture
def quiet(monkeypatch, tmp_path):
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(tmp_path / 'home'))
    monkeypatch.setattr(launcher, 'find_browser', lambda: 'edge.exe')
    monkeypatch.setattr(launcher, 'CHECK_SECONDS', .1)
    monkeypatch.setattr(launcher, 'IDLE_CHECKS', 5)
    messages = []
    monkeypatch.setattr(launcher, '_notify', messages.append)
    return messages


def serve(body):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_server_stays_up_while_the_page_checks_in_and_stops_when_it_goes_quiet(quiet, monkeypatch):
    port, opened = free_port(), []
    monkeypatch.setattr(launcher.subprocess, 'Popen', opened.append)
    runner = threading.Thread(target=launcher.main, args=(port,))
    runner.start()
    deadline = time.monotonic() + 30
    while not opened and time.monotonic() < deadline:
        time.sleep(.05)
    assert opened and opened[0][:2] == ['edge.exe', f'--app=http://127.0.0.1:{port}']
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=5) as response:
        token = re.search(rb'name="atlas-token" content="([^"]+)"', response.read()).group(1).decode()
    ping = urllib.request.Request(f'http://127.0.0.1:{port}/api/health', headers={'x-atlas-token': token})
    for _ in range(12):  # 1.2 s of check-ins, longer than the 0.5 s idle limit
        urllib.request.urlopen(ping, timeout=5).close()
        time.sleep(.1)
        assert runner.is_alive(), 'stopped while the window was still checking in'
    runner.join(timeout=10)
    assert not runner.is_alive(), 'kept running after the window went quiet'
    assert quiet == []


def test_second_launch_only_opens_another_window(quiet, monkeypatch):
    running = serve(b'<html><head><meta name="atlas-token" content="x"></head></html>')
    opened = []
    monkeypatch.setattr(launcher.subprocess, 'Popen', opened.append)
    try:
        launcher.main(running.server_port)
    finally:
        running.shutdown()
    assert len(opened) == 1 and quiet == []


def test_foreign_program_on_the_port_is_explained(quiet, monkeypatch):
    other = serve(b'<html>someone else</html>')
    monkeypatch.setattr(launcher.subprocess, 'Popen', lambda command: pytest.fail('opened a window'))
    try:
        launcher.main(other.server_port)
    finally:
        other.shutdown()
    assert len(quiet) == 1 and 'used by another program' in quiet[0]


def test_without_edge_or_chrome_the_default_browser_is_used(quiet, monkeypatch):
    running = serve(b'<html><head><meta name="atlas-token" content="x"></head></html>')
    monkeypatch.setattr(launcher, 'find_browser', lambda: None)
    opened = []
    monkeypatch.setattr(launcher.webbrowser, 'open', opened.append)
    try:
        launcher.main(running.server_port)
    finally:
        running.shutdown()
    assert opened == [f'http://127.0.0.1:{running.server_port}'] and quiet == []


@pytest.mark.parametrize('default,expected', [('chrome', 'chrome'), ('edge', 'edge'), (None, 'edge')])
def test_find_browser_follows_the_default_browser_then_edge(monkeypatch, tmp_path, default, expected):
    paths = {'edge': tmp_path / 'Microsoft/Edge/Application/msedge.exe',
             'chrome': tmp_path / 'Google/Chrome/Application/chrome.exe'}
    for path in paths.values():
        path.parent.mkdir(parents=True)
        path.write_text('')
    monkeypatch.setenv('ProgramFiles(x86)', str(tmp_path))
    monkeypatch.setattr(launcher, '_default_browser', lambda: default)
    assert launcher.find_browser() == str(paths[expected])


def test_default_browser_is_read_from_windows_settings(monkeypatch):
    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    winreg = type('winreg', (), {'HKEY_CURRENT_USER': 0, 'OpenKey': lambda *args: Key(),
                                 'QueryValueEx': lambda key, name: (prog, 1)})
    monkeypatch.setitem(__import__('sys').modules, 'winreg', winreg)
    for prog, expected in (('ChromeHTML', 'chrome'), ('MSEdgeHTM', 'edge'), ('FirefoxURL-308046B0AF4A39CB', None)):
        assert launcher._default_browser() == expected
