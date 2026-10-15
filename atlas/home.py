"""Where the user's library lives: outside the repository and outside OneDrive."""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / 'data'


def _inside(path: Path, parent: Path) -> bool:
    try:
        return path.resolve().is_relative_to(parent.resolve())
    except OSError:
        return False


def home_dir(home: Path | str | None = None) -> Path:
    """The data home: VISUAL_ATLAS_HOME, or %USERPROFILE%\\VisualAtlas.

    Refused inside the app checkout (code and data stay apart) and inside OneDrive, whose
    sync can corrupt a live SQLite database in WAL mode."""
    path = Path(home or os.environ.get('VISUAL_ATLAS_HOME') or Path.home() / 'VisualAtlas')
    if _inside(path, REPO):
        raise ValueError('The Visual Atlas library cannot live inside the application folder.')
    for name in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        cloud = os.environ.get(name)
        if cloud and _inside(path, Path(cloud)):
            raise ValueError('The Visual Atlas library cannot live inside OneDrive; '
                             'choose a folder that is not synced.')
    return path


def local_setting(name: str, home: Path | None = None) -> str | None:
    """Read one allowed setting from the environment or the data home's .env file."""
    if name not in ('VISUAL_ATLAS_PORT', 'SMITHSONIAN_API_KEY'):
        raise ValueError('unknown setting')
    if os.environ.get(name):
        return os.environ[name]
    try:
        env = home_dir(home) / '.env'
        for line in env.read_text(encoding='utf-8').splitlines():
            key, _, value = line.partition('=')
            if key.strip() == name and value.strip():
                return value.strip().strip('"\'')
    except (OSError, ValueError):
        pass
    return None
