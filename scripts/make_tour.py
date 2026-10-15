"""Assemble the README tour GIF from numbered screenshots (taken with Playwright from the real app).

  uv run python scripts/make_tour.py docs/media/tour-frames docs/media/tour.gif"""

import sys
from pathlib import Path

from PIL import Image


def main(frames: Path, out: Path, width: int = 960, seconds: float = 2.2):
    paths = sorted(frames.glob('*.png'))
    if not paths:
        raise SystemExit(f'no frames in {frames}')
    images = []
    for path in paths:
        frame = Image.open(path).convert('RGB')
        frame = frame.resize((width, round(frame.height * width / frame.width)), Image.Resampling.LANCZOS)
        images.append(frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    height = max(image.height for image in images)
    padded = []
    for image in images:
        canvas = Image.new('P', (width, height))
        canvas.putpalette(image.getpalette())
        canvas.paste(image, (0, 0))
        padded.append(canvas)
    padded[0].save(out, save_all=True, append_images=padded[1:], duration=int(seconds * 1000), loop=0, optimize=True)
    print(f'{out}: {len(padded)} frames, {out.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
