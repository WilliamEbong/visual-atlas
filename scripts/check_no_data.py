"""Fail on tracked user libraries, local configuration or secret environment files (adapted from Qualia).

Also refuses the owner's private design-system libraries (see atlas/layers.py): by path shape, and, where those
libraries exist on this machine, by comparing every tracked image's bytes with theirs (size first, then SHA-256)."""

import hashlib
import subprocess
import sys
from pathlib import Path

DESIGN_SYSTEMS = ('archive-of-looking', 'garden-of-lingering', 'citadel-of-watching', 'harbour-of-drifting')
IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp')


def forbidden(path: str) -> bool:
    lower = path.lower().replace(chr(92), '/')  # backslash
    parts = lower.split('/')
    return (lower.endswith(('.db', '.sqlite', '.sqlite3', '.local'))
            or any(suffix in parts[-1] for suffix in ('.db-', '.db.', '.sqlite-', '.sqlite.', '.sqlite3-', '.sqlite3.'))
            or (parts[-1].startswith('.env') and parts[-1] != '.env.example')
            or parts[-1] in ('owner-needed.md',)
            or (parts[0] == 'starter' and 'originals' in parts)
            or lower.endswith('.skill')
            or 'assets/library/' in lower or lower.endswith('references/images.csv')
            or any(name in parts for name in DESIGN_SYSTEMS))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design_system_copies(files: list[str], repo: Path, libraries: list[Path]) -> list[str]:
    """Tracked images whose bytes equal a design-system image (renamed copies included)."""
    by_size: dict[int, list[Path]] = {}
    for library in libraries:
        for image in library.glob('*'):
            if image.suffix.lower() in IMAGE_SUFFIXES:
                by_size.setdefault(image.stat().st_size, []).append(image)
    found = []
    for name in files:
        path = repo / name
        if not name.lower().endswith(IMAGE_SUFFIXES) or not path.is_file():
            continue
        twins = by_size.get(path.stat().st_size)
        if twins and _sha(path) in {_sha(twin) for twin in twins}:
            found.append(name)
    return found


if __name__ == '__main__':
    files = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    bad = [path for path in files if path and forbidden(path)]
    skills = Path.home() / '.claude' / 'skills'
    bad += design_system_copies([f for f in files if f], Path.cwd(),
                                [skills / name / 'assets' / 'library' for name in DESIGN_SYSTEMS])
    if bad:
        print('Tracked local data forbidden: ' + ', '.join(bad))
        sys.exit(1)
    print('No tracked libraries, design-system images, local settings or secret files.')
