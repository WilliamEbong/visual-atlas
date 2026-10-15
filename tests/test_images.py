import hashlib
import io

import pytest
from PIL import Image, ImageOps

from atlas import images


def encode(image, kind='PNG', **kwargs):
    out = io.BytesIO()
    image.save(out, kind, **kwargs)
    return out.getvalue()


@pytest.mark.parametrize('kind', ['JPEG', 'PNG', 'WEBP'])
def test_open_checked_accepts_supported_formats(kind):
    image, actual = images.open_checked(encode(Image.new('RGB', (40, 30), 'red'), kind))
    assert actual == kind
    assert image.mode == 'RGB'
    assert image.size == (40, 30)


@pytest.mark.parametrize('kind', ['GIF', 'BMP'])
def test_open_checked_rejects_other_formats(kind):
    with pytest.raises(images.ImageRejected) as error:
        images.open_checked(encode(Image.new('RGB', (40, 30)), kind))
    assert error.value.code == 'wrong_type'


@pytest.mark.parametrize('data', [b'not an image', b'', encode(Image.new('RGB', (40, 30)))[:30]])
def test_open_checked_rejects_corrupt_bytes(data):
    with pytest.raises(images.ImageRejected) as error:
        images.open_checked(data)
    assert error.value.code == 'corrupt'


def test_open_checked_rejects_decompression_bomb(monkeypatch):
    data = encode(Image.new('RGB', (30, 30)))
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 100)
    with pytest.raises(images.ImageRejected) as error:
        images.open_checked(data)
    assert error.value.code == 'too_many_pixels'


def test_exif_orientation_is_applied():
    source = Image.new('RGB', (40, 20), 'red')
    source.paste('blue', (20, 0, 40, 20))
    exif = Image.Exif()
    exif[274] = 6
    image, _ = images.open_checked(encode(source, exif=exif))
    assert image.size == (20, 40)
    assert image.getpixel((10, 5)) == (255, 0, 0)
    assert image.getpixel((10, 35)) == (0, 0, 255)
    assert image.getexif().get(274) is None


def test_dhash_survives_resize_and_reencoding_but_distinguishes_other_image():
    source = Image.linear_gradient('L').rotate(90).convert('RGB')
    copy, _ = images.open_checked(encode(source.resize((130, 190)), 'JPEG', quality=65))
    original_hash = images.dhash(source)
    assert len(original_hash) == 16
    assert images.hamming(original_hash, images.dhash(copy)) <= 6
    assert images.hamming(original_hash, images.dhash(ImageOps.mirror(source))) >= 32


@pytest.mark.parametrize(('size', 'orientation'), [
    ((800, 400), 'landscape'), ((400, 800), 'portrait'), ((700, 700), 'square'),
])
@pytest.mark.parametrize(('color', 'families'), [
    ('red', {'red'}), ('blue', {'blue'}), ('grey', {'monochrome', 'neutral'}),
])
def test_solid_color_metrics(size, orientation, color, families):
    stats = images.metrics(Image.new('RGB', size, color))
    assert stats['orientation'] == orientation
    assert stats['color_family'] in families
    assert stats['aspect'] == pytest.approx(size[0] / size[1], abs=0.0001)
    assert stats['contrast'] == 0
    assert sum(swatch['share'] for swatch in stats['palette']) == pytest.approx(1)


@pytest.mark.parametrize(('size', 'flat', 'problem'), [
    ((100, 100), False, 'too small'),
    ((2100, 400), False, 'extreme proportions'),
    ((400, 2100), False, 'extreme proportions'),
    ((800, 600), True, 'almost no tonal variation'),
    ((800, 600), False, None),
])
def test_quality_problem(size, flat, problem):
    image = Image.new('RGB', size, 'grey') if flat else Image.linear_gradient('L').resize(size).convert('RGB')
    actual = images.quality_problem(image, images.metrics(image))
    if problem is None:
        assert actual is None
    else:
        assert actual.startswith(problem)


@pytest.mark.parametrize(('kind', 'extension', 'mime'), [
    ('JPEG', 'jpg', 'image/jpeg'), ('PNG', 'png', 'image/png'), ('WEBP', 'webp', 'image/webp'),
])
def test_prepared_files_are_content_addressed_and_strips_analysis_metadata(tmp_path, kind, extension, mime):
    exif = Image.Exif()
    exif[315] = 'Private artist metadata'
    data = encode(Image.new('RGB', (1600, 1200), 'red'), kind, exif=exif)
    image, actual_kind = images.open_checked(data)
    stored, blobs = images.prepare_files(data, image, actual_kind)
    assert not any(tmp_path.iterdir())  # nothing is written until the caller has saved the row
    images.write_files(tmp_path, blobs)
    sha = hashlib.sha256(data).hexdigest()
    assert stored['file_sha256'] == sha
    assert stored['original_path'] == f'originals/{sha[:2]}/{sha}.{extension}'
    assert stored['analysis_path'] == f'analysis/{sha[:2]}/{sha}.jpg'
    assert stored['thumb_path'] == f'thumbs/{sha[:2]}/{sha}.jpg'
    assert (stored['width'], stored['height'], stored['bytes'], stored['mime']) == (1600, 1200, len(data), mime)
    assert (tmp_path / stored['original_path']).read_bytes() == data
    for key, edge in [('analysis_path', 1024), ('thumb_path', 480)]:
        path = tmp_path / stored[key]
        with Image.open(path) as copy:
            assert copy.format == 'JPEG'
            assert max(copy.size) <= edge
            assert copy.width / copy.height == pytest.approx(4 / 3)
            assert not copy.getexif()
        if key == 'analysis_path':
            assert stored['analysis_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert images.prepare_files(data, image, actual_kind)[0] == stored  # deterministic, so a resume can rewrite
    assert len([p for p in tmp_path.rglob('*') if p.is_file()]) == 3
    assert not list(tmp_path.rglob('*.part'))


@pytest.mark.parametrize('outside_path', ['../outside.txt', 'originals/../../outside.txt', 'absolute'])
def test_delete_files_cannot_escape_media_root(tmp_path, outside_path):
    media = tmp_path / 'media'
    media.mkdir()
    outside = tmp_path / 'outside.txt'
    outside.write_text('keep')
    inside = media / 'inside.jpg'
    inside.write_bytes(b'delete')
    images.delete_files(media, {'original_path': str(outside) if outside_path == 'absolute' else outside_path,
                               'analysis_path': 'inside.jpg', 'thumb_path': None})
    assert outside.read_text() == 'keep'
    assert not inside.exists()


def test_sweep_orphans_keeps_referenced_files_and_removes_partial_files(tmp_path):
    referenced = set()
    for kind in ('originals', 'analysis', 'thumbs'):
        folder = tmp_path / kind / 'ab'
        folder.mkdir(parents=True)
        for name in ('kept.jpg', 'orphan.jpg', 'orphan.jpg.part'):
            (folder / name).write_bytes(b'image')
        referenced.add(f'{kind}/ab/kept.jpg')
    assert images.sweep_orphans(tmp_path, referenced) == 6
    assert {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*') if p.is_file()} == referenced
    assert images.sweep_orphans(tmp_path, referenced) == 0
