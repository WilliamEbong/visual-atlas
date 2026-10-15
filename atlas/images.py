"""Image validation, stored copies and measurements — all ordinary code, no AI."""

import colorsys
import hashlib
import io
import math
import os
from pathlib import Path

from PIL import Image, ImageOps, ImageStat

Image.MAX_IMAGE_PIXELS = 80_000_000  # Pillow raises DecompressionBombError above twice this
FORMATS = {'JPEG': ('jpg', 'image/jpeg'), 'PNG': ('png', 'image/png'), 'WEBP': ('webp', 'image/webp')}
ANALYSIS_EDGE = 1024
THUMB_EDGE = 480
MIN_LONG_EDGE = 700
MIN_SHORT_EDGE = 380


class ImageRejected(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def open_checked(data: bytes) -> tuple[Image.Image, str]:
    """Decode untrusted bytes safely; return an RGB image (orientation applied) and its format."""
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        image = Image.open(io.BytesIO(data))
        kind = image.format
        if kind not in FORMATS:
            raise ImageRejected('wrong_type', f'{kind or "Unknown"} images are not accepted.')
        image.load()
    except ImageRejected:
        raise
    except Image.DecompressionBombError:
        raise ImageRejected('too_many_pixels', 'The image has too many pixels to process safely.') from None
    except (OSError, ValueError, SyntaxError):
        raise ImageRejected('corrupt', 'The file is not a readable image.') from None
    image = ImageOps.exif_transpose(image)
    if image.mode != 'RGB':
        image = image.convert('RGBA').convert('RGB') if 'A' in image.getbands() or image.mode == 'P' else image.convert('RGB')
    return image, kind


def dhash(image: Image.Image) -> str:
    """64-bit difference hash: robust to resizing and re-encoding, used for near-duplicates."""
    small = image.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    bits = 0
    for row in range(8):
        for column in range(8):
            bits = (bits << 1) | (pixels[row * 9 + column] > pixels[row * 9 + column + 1])
    return f'{bits:016x}'


def hamming(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


_HUES = ((15, 'red'), (40, 'orange'), (65, 'yellow'), (160, 'green'), (195, 'cyan'), (255, 'blue'),
         (290, 'purple'), (335, 'pink'), (360, 'red'))


def color_name(rgb) -> str:
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    if v < .18:
        return 'black'
    if s < .15:
        return 'white' if v > .85 else 'grey'
    degrees = h * 360
    name = next(label for limit, label in _HUES if degrees <= limit)
    if name in ('orange', 'red') and v < .6 and s > .3:
        return 'brown'
    return name


def metrics(image: Image.Image) -> dict:
    width, height = image.size
    aspect = width / height
    small = image.resize((96, 96), Image.Resampling.BILINEAR)
    luma = ImageStat.Stat(small.convert('L'))
    pixels = list(small.getdata())
    rg = [r - g for r, g, b in pixels]
    yb = [(r + g) / 2 - b for r, g, b in pixels]

    def spread(values):
        mean = sum(values) / len(values)
        return mean, math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

    (rg_mean, rg_std), (yb_mean, yb_std) = spread(rg), spread(yb)
    colorfulness = math.hypot(rg_std, yb_std) + .3 * math.hypot(rg_mean, yb_mean)  # Hasler & Süsstrunk
    saturation = ImageStat.Stat(small.convert('HSV')).mean[1] / 255
    quantized = small.quantize(colors=5, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette() or []
    counts = sorted(quantized.getcolors() or [], reverse=True)
    swatches = [{'hex': '#%02x%02x%02x' % tuple(palette[i * 3:i * 3 + 3]), 'share': round(count / (96 * 96), 3),
                 'name': color_name(palette[i * 3:i * 3 + 3])} for count, i in counts]
    chromatic = [s for s in swatches if s['name'] not in ('black', 'white', 'grey')]
    family = chromatic[0]['name'] if chromatic and chromatic[0]['share'] >= .12 else (
        'monochrome' if saturation < .08 else 'neutral')
    return {'aspect': round(aspect, 4),
            'orientation': 'landscape' if aspect > 1.15 else 'portrait' if aspect < .87 else 'square',
            'mean_luma': round(luma.mean[0], 2), 'contrast': round(luma.stddev[0], 2),
            'colorfulness': round(colorfulness, 2), 'saturation': round(saturation, 4),
            'palette': swatches, 'color_family': family}


def quality_problem(image: Image.Image, stats: dict) -> str | None:
    width, height = image.size
    if max(width, height) < MIN_LONG_EDGE or min(width, height) < MIN_SHORT_EDGE:
        return f'too small ({width}×{height})'
    if not .25 <= stats['aspect'] <= 4:
        return 'extreme proportions (likely a strip, scroll or scan edge)'
    if stats['contrast'] < 8:
        return 'almost no tonal variation (blank or faded scan)'
    return None


def _write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    temporary = path.with_name(path.name + '.part')
    temporary.write_bytes(data)
    os.replace(temporary, path)


def _jpeg(image: Image.Image, edge: int) -> bytes:
    copy = image.copy()
    copy.thumbnail((edge, edge), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    copy.save(out, 'JPEG', quality=88, optimize=True)  # fresh encode: no EXIF/XMP/ICC text carried over
    return out.getvalue()


def store_files(data: bytes, image: Image.Image, kind: str, media_root: Path) -> dict:
    """Content-addressed original, ≤1024 px analysis copy and thumbnail. Returns paths relative to media_root."""
    sha = hashlib.sha256(data).hexdigest()
    extension, mime = FORMATS[kind]
    analysis = _jpeg(image, ANALYSIS_EDGE)
    paths = {'original_path': f'originals/{sha[:2]}/{sha}.{extension}',
             'analysis_path': f'analysis/{sha[:2]}/{sha}.jpg', 'thumb_path': f'thumbs/{sha[:2]}/{sha}.jpg'}
    _write(media_root / paths['original_path'], data)
    _write(media_root / paths['analysis_path'], analysis)
    _write(media_root / paths['thumb_path'], _jpeg(image, THUMB_EDGE))
    return {**paths, 'file_sha256': sha, 'analysis_sha256': hashlib.sha256(analysis).hexdigest(),
            'mime': mime, 'bytes': len(data), 'width': image.size[0], 'height': image.size[1]}


def delete_files(media_root: Path, image: dict):
    for key in ('original_path', 'analysis_path', 'thumb_path'):
        relative = image.get(key)
        if relative:
            path = (media_root / relative).resolve()
            if path.is_relative_to(media_root.resolve()) and path.is_file():
                path.unlink()


def sweep_orphans(media_root: Path, referenced: set[str]) -> int:
    """Delete stray .part files and media no database row refers to (left by a crash)."""
    removed = 0
    for kind in ('originals', 'analysis', 'thumbs'):
        folder = media_root / kind
        if not folder.is_dir():
            continue
        for path in folder.rglob('*'):
            if path.is_file() and path.relative_to(media_root).as_posix() not in referenced:
                path.unlink()
                removed += 1
    return removed
