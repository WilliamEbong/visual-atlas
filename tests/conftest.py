import pytest


@pytest.fixture
def home(tmp_path, monkeypatch):
    """An isolated data home (never the user's real library)."""
    path = tmp_path / 'home'
    monkeypatch.setenv('VISUAL_ATLAS_HOME', str(path))
    return path
