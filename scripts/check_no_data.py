"""Fail on tracked user libraries, local configuration or secret environment files (adapted from Qualia)."""

import subprocess
import sys


def forbidden(path: str) -> bool:
    lower = path.lower().replace(chr(92), '/')  # backslash
    parts = lower.split('/')
    return (lower.endswith(('.db', '.sqlite', '.sqlite3', '.local'))
            or any(suffix in parts[-1] for suffix in ('.db-', '.db.', '.sqlite-', '.sqlite.', '.sqlite3-', '.sqlite3.'))
            or (parts[-1].startswith('.env') and parts[-1] != '.env.example')
            or parts[-1] in ('owner-needed.md',)
            or (parts[0] == 'starter' and 'originals' in parts))


if __name__ == '__main__':
    files = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    bad = [path for path in files if path and forbidden(path)]
    if bad:
        print('Tracked local data forbidden: ' + ', '.join(bad))
        sys.exit(1)
    print('No tracked libraries, local settings or secret files.')
