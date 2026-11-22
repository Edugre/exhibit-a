"""Shared helpers for the interior's texture scripts (plain Python: numpy and Pillow).
Each set's art script draws its own atlas and writes the atlas layout next to itself, as
<set>_atlas.json, for its Blender build script to read."""
import json
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = "C:/Windows/Fonts/"
SANS_BOLD = FONTS + "arialbd.ttf"
SERIF_BOLD = FONTS + "palab.ttf"
SERIF = FONTS + "pala.ttf"
SERIF_ITAL = FONTS + "palai.ttf"


def blur_noise(rng, w, h, radius):
    """Zero-mean, unit-spread noise, blurred to the given grain size in pixels."""
    img = Image.fromarray((rng.random((h, w)) * 255).astype(np.uint8))
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
    return (a - a.mean()) / max(a.std(), 1e-4)


def streaks(rng, w, h, length, axis=0):
    """Noise stretched along one axis: brushed metal, wood grain, fibres."""
    a = rng.random((h, w)).astype(np.float32)
    img = Image.fromarray((a * 255).astype(np.uint8))
    box = (1, length) if axis == 0 else (length, 1)
    img = img.resize((max(w // box[0], 1), max(h // box[1], 1)), Image.BILINEAR).resize((w, h), Image.BICUBIC)
    a = np.asarray(img, dtype=np.float32) / 255
    return (a - a.mean()) / max(a.std(), 1e-4)


def to_image(rgb):
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))


def fit_font(draw, text, path, size, max_width):
    """The largest font at or below `size` that fits `text` in `max_width` pixels."""
    while size > 8:
        font = ImageFont.truetype(path, size)
        x0, _, x1, _ = draw.textbbox((0, 0), text, font=font)
        if x1 - x0 <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(path, size)


def write_layout(path, size, rects):
    """rects: name -> (x0, y0, x1, y1) in pixels, origin top-left."""
    pathlib.Path(path).write_text(json.dumps({"size": size, "rects": rects}, indent=1))
