"""Double-click entry point: Visual Atlas in its own browser app window; it stops once the window is closed.

Adapted from Qualia's launcher (same owner). A running job counts as activity, so closing the window
during a job lets the job finish first."""

import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

# A windowless (GUI-script) launch has no console, so messages need a dialog instead of stderr.
_CONSOLE = sys.stderr is not None
_PROGRAMS = {'edge': 'Microsoft/Edge/Application/msedge.exe', 'chrome': 'Google/Chrome/Application/chrome.exe'}
_MAC_APPS = ('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
_COMMANDS = ('msedge', 'microsoft-edge', 'google-chrome', 'chromium', 'chromium-browser')
# Open pages check in every 30 s (browsers slow hidden windows to about once a minute). Counting
# checks instead of clock time means a sleeping laptop never counts as idle.
CHECK_SECONDS = 10
IDLE_CHECKS = 18  # ponytail: ~3 awake minutes without page contact; shorten if users want faster exit


def _default_browser():
    """'chrome' or 'edge' when that is the Windows default browser, else None."""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\Shell\Associations'
                            r'\UrlAssociations\https\UserChoice') as key:
            program = winreg.QueryValueEx(key, 'ProgId')[0]
    except (ImportError, OSError):
        return None
    return 'chrome' if program.startswith('ChromeHTML') else 'edge' if program.startswith('MSEdgeHTM') else None


def find_browser():
    """Edge or Chrome, whose app mode gives Visual Atlas a window without tabs or address bar.

    The person's default browser wins when it is one of the two; otherwise Edge, which every
    Windows 10/11 PC has."""
    order = ('chrome', 'edge') if _default_browser() == 'chrome' else ('edge', 'chrome')
    roots = [os.environ.get(name) for name in ('ProgramFiles(x86)', 'ProgramFiles', 'LOCALAPPDATA')]
    paths = [Path(root, _PROGRAMS[browser]) for browser in order for root in roots if root]
    for path in [*paths, *map(Path, _MAC_APPS)]:
        if path.is_file():
            return str(path)
    return next((found for name in _COMMANDS if (found := shutil.which(name))), None)


def _probe(port):
    """'atlas' if Visual Atlas already serves the port, 'other' if another program does, None if free."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/', timeout=2) as response:
            return 'atlas' if b'atlas-token' in response.read(65536) else 'other'
    except urllib.request.HTTPError:
        return 'other'
    except OSError:
        return None


def _notify(message):
    if os.name == 'nt' and not _CONSOLE:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, 'Visual Atlas', 0x40)
    else:
        print(message, file=sys.stderr)


def _open(url):
    browser = find_browser()
    if browser:
        # The person's normal browser profile: no first-run or sign-in prompts for a new profile.
        subprocess.Popen([browser, f'--app={url}', '--window-size=1280,860'])
    else:
        webbrowser.open(url)


def _watch(server, app, url):
    while not server.started:
        if server.should_exit:
            return
        time.sleep(.05)
    _open(url)
    seen, idle = None, 0
    while not server.should_exit:
        time.sleep(CHECK_SECONDS)
        activity = (app.state.activity, app.state.worker.activity)
        idle = 0 if activity != seen else idle + 1
        seen = activity
        if idle >= IDLE_CHECKS:
            server.should_exit = True


def main(port=None):
    try:
        _run(port)
    except Exception as error:  # a windowless launch must never fail silently
        _notify(f'Visual Atlas could not start: {error}')
        if _CONSOLE:
            raise


def _run(port):
    from atlas.home import home_dir, local_setting

    home = home_dir()
    if not _CONSOLE:
        # Keep a log for troubleshooting a windowless launch.
        home.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = open(home / 'visual-atlas-app.log', 'a', encoding='utf-8')
    try:
        port = int(port or local_setting('VISUAL_ATLAS_PORT') or 8775)
    except ValueError:
        return _notify('VISUAL_ATLAS_PORT in the .env file of your Visual Atlas folder must be a number.')
    url = f'http://127.0.0.1:{port}'
    state = _probe(port)
    if state == 'atlas':
        return _open(url)
    if state == 'other':
        return _notify(f'Port {port} is used by another program. Close that program, or set VISUAL_ATLAS_PORT '
                       'in the .env file of your Visual Atlas folder to another number such as 8776.')
    import uvicorn

    from atlas.server import create_app

    app = create_app(start_worker=True)
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, access_log=False))
    threading.Thread(target=_watch, args=(server, app, url), daemon=True).start()
    server.run()
    if not server.started:
        _notify(f'Visual Atlas could not start on port {port}. See {home / "visual-atlas-app.log"} for details.')
