"""Fail on tracked user libraries, local configuration or secret environment files (adapted from Qualia).

Also refuses the owner's private design-system libraries (see atlas/layers.py): by path shape, and, where those
libraries exist on this machine, by comparing the bytes of every file in the Git index (what a commit would contain) with theirs: size first,
then SHA-256."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

DESIGN_SYSTEMS = ('archive-of-looking', 'garden-of-lingering', 'citadel-of-watching', 'harbour-of-drifting')


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


def staged_blobs(repo: Path) -> dict[str, tuple[str, int]]:
    """path -> (blob id, size) for every file in the Git index: what a commit would contain, whatever is on disk."""
    entries = {}
    for record in subprocess.check_output(['git', 'ls-files', '-s', '-z'], cwd=repo).decode().split('\0'):
        if record:
            meta, path = record.split('\t', 1)
            entries[path] = meta.split()[1]
    if not entries:
        return {}
    checked = subprocess.run(['git', 'cat-file', '--batch-check'], cwd=repo, check=True, capture_output=True,
                             input='\n'.join(entries.values()).encode()).stdout.decode().splitlines()
    sizes = {line.split()[0]: int(line.split()[2]) for line in checked if line.endswith(tuple('0123456789'))}
    return {path: (blob, sizes[blob]) for path, blob in entries.items() if blob in sizes}


def design_system_copies(repo: Path, libraries: list[Path]) -> list[str]:
    """Staged files whose bytes equal any file in a design-system library (renamed or re-extensioned copies too)."""
    by_size: dict[int, list[Path]] = {}
    for library in libraries:
        for item in library.glob('*') if library.is_dir() else []:
            if item.is_file():
                by_size.setdefault(item.stat().st_size, []).append(item)
    found = []
    for path, (blob, size) in staged_blobs(repo).items():
        if size in by_size:  # only same-size pairs are hashed
            data = subprocess.run(['git', 'cat-file', 'blob', blob], cwd=repo, check=True, capture_output=True).stdout
            digest = hashlib.sha256(data).hexdigest()
            if any(hashlib.sha256(twin.read_bytes()).hexdigest() == digest for twin in by_size[size]):
                found.append(path)
    return found


def libraries() -> list[Path]:
    """The four known libraries plus any folders configured for the desk (VISUAL_ATLAS_DESIGN_SYSTEMS)."""
    roots = [Path.home() / '.claude' / 'skills' / name for name in DESIGN_SYSTEMS]
    configured = os.environ.get('VISUAL_ATLAS_DESIGN_SYSTEMS', '')
    if configured.lower() not in ('', 'auto', 'off', '0', 'no', 'false'):
        roots += [Path(part.strip()) for part in configured.split(';') if part.strip()]
    try:  # the same lookup the desk uses, including the data home's .env file
        from atlas.layers import enabled_systems
        roots += enabled_systems()
    except (ImportError, ValueError, OSError):
        pass
    return [root / 'assets' / 'library' for root in dict.fromkeys(roots)]


if __name__ == '__main__':
    files = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    bad = [path for path in files if path and forbidden(path)]
    bad += design_system_copies(Path.cwd(), libraries())
    if bad:
        print('Tracked local data forbidden: ' + ', '.join(bad))
        sys.exit(1)
    print('No tracked libraries, design-system images, local settings or secret files.')
