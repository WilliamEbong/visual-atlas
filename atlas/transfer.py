"""Credits, collection export, backup and restore, all ordinary code over the Store and media folder."""

from atlas.store import Store


def referenced_media(store: Store) -> set[str]:
    """Every media path a database row refers to (anything else in media/ is a crash leftover)."""
    paths = set()
    for row in store.rows('SELECT original_path, analysis_path, thumb_path FROM images'):
        paths.update(p for p in row.values() if p)
    return paths
