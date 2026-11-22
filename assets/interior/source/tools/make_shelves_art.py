"""The archive bookcases' one texture (asset item P2.3): three strips of book spines in three heights,
leather, gilt bands and the odd title you can read if you stand close, plus page edges, covers, dark oak
and the brass shelf marks. Every run of books on a shelf shows a different stretch of a strip.
Writes the texture, a normal map, their import settings and the material.
usage: python make_shelves_art.py <assets/interior/shelves folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True    # no __pycache__ next to the scripts
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import shelves_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/shelves/"
N = L.ATLAS
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
GOLD = np.array([0.74, 0.58, 0.28])
LEATHER = [np.array(c) for c in ([0.38, 0.10, 0.08], [0.16, 0.24, 0.16], [0.13, 0.15, 0.26], [0.42, 0.28, 0.16],
                                 [0.10, 0.09, 0.08], [0.30, 0.18, 0.10], [0.46, 0.38, 0.26], [0.28, 0.08, 0.14])]
# Titles big enough to read up close. The rest are gilt marks that only look like titles.
TITLES = ["ILIAD", "ODYSSEY", "OVERDUE", "FIRE CODES", "DO NOT LEND", "SHUSH", "MEDUSA: A STUDY", "HORSES", "PANDORA", "VOL. II"]

rgb = np.zeros((N, N, 3))
height = np.zeros((N, N))


def noise(shape, sigma, seed):
    n = gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-9)


def region(name):
    x, y, w, h = L.REGIONS[name]
    return (slice(y, y + h), slice(x, x + w)), w, h


def spines(name, seed):
    """One strip of books standing side by side: each its own width, leather and wear, rounded at its edges."""
    s, w, h = region(name)
    rng = np.random.default_rng(seed)
    c = np.zeros((h, w, 3))
    hgt = np.zeros((h, w))
    gilt = Image.new("L", (w * 3, h * 3), 0)
    pen = ImageDraw.Draw(gilt)
    x = 0
    while x < w:
        bw = int(rng.choice([rng.integers(14, 28), rng.integers(28, 46), rng.integers(46, 64)], p=[0.45, 0.4, 0.15]))
        bw = min(bw, w - x)
        leather = LEATHER[rng.integers(len(LEATHER))] * rng.uniform(0.8, 1.15)
        t = (np.arange(bw) + 0.5) / bw
        round_ = np.sin(t * np.pi) ** 0.5             # a rounded spine catches the light in the middle
        grain = noise((h, bw), (2, 1.2), int(rng.integers(1e6)))
        book = leather * (0.55 + 0.45 * round_[None, :, None]) * (0.85 + 0.25 * grain[..., None])
        fade = rng.uniform(0, 0.25)                    # sun-faded at the top, where the light reached
        book *= (1 - fade * np.clip(1 - np.arange(h) / (h * 0.6), 0, 1))[:, None, None] + fade * 0.0
        c[:, x:x + bw] = book
        hgt[:, x:x + bw] = round_[None, :] * 0.003
        # Gilt bands near the head and the foot, and a title panel or a real title between them
        for band in (0.08, 0.14, 0.86, 0.92):
            if rng.random() < 0.75:
                pen.rectangle([x * 3 + 2, int(band * h * 3), (x + bw) * 3 - 2, int(band * h * 3) + 4], fill=200)
        if bw >= 26 and rng.random() < 0.35:
            title = TITLES[int(rng.integers(len(TITLES)))]
            label = Image.new("L", (int(h * 3 * 0.62), bw * 3), 0)
            ld = ImageDraw.Draw(label)
            size = int(bw * 3 * 0.5)
            font = ImageFont.truetype(SERIF_BOLD, size)
            while font.getbbox(title)[2] > label.width * 0.95 and size > 8:
                size = int(size * 0.9)
                font = ImageFont.truetype(SERIF_BOLD, size)
            ld.text((label.width / 2, label.height / 2), title, font=font, fill=255, anchor="mm")
            gilt.paste(255, (x * 3, int(h * 3 * 0.2)), label.rotate(90, expand=True))
        else:
            for k in range(int(rng.integers(1, 3))):
                y0 = int(h * 3 * (0.3 + k * 0.12))
                pen.rectangle([x * 3 + bw * 3 * 0.25, y0, (x + bw) * 3 - bw * 3 * 0.25, y0 + 12], fill=170)
        x += bw
        if x < w - 2 and rng.random() < 0.15:
            c[:, x:x + 2] = 0.03                        # a dark gap between two books
            x += 2
    g = np.asarray(gilt.resize((w, h), Image.BOX), dtype=float) / 255
    worn = np.clip((noise((h, w), 1.2, seed + 1) - 0.25) * 3, 0, 1)
    g *= worn
    c = c * (1 - g[..., None]) + GOLD * g[..., None] * (0.7 + 0.3 * noise((h, w), 2, seed + 2)[..., None])
    c *= (1 - 0.25 * np.clip((noise((h, w), 8, seed + 3) - 0.6) * 3, 0, 1))[..., None]       # dust and handling
    rgb[s] = c
    height[s] = hgt + g * 0.0006


def wood():
    s, w, h = region("wood")
    grain = noise((h, w), (36, 1.0), 6101)
    figure = noise((h, w), (80, 3), 6102)
    c = np.array([0.24, 0.15, 0.09]) * (0.8 + 0.28 * grain[..., None]) * (1 - 0.12 * np.clip((figure[..., None] - 0.6) * 4, 0, 1))
    worn = np.clip((noise((h, w), 12, 6103) - 0.6) * 3, 0, 1)
    rgb[s] = c * (1 + 0.25 * worn[..., None])
    height[s] = grain * 0.0003


def pages():
    s, w, h = region("pages")
    lines = (np.sin(np.arange(h) * 2.4) * 0.5 + 0.5)[:, None] * noise((h, w), (0.5, 6), 6110)
    rgb[s] = np.array([0.78, 0.72, 0.58]) * (0.85 + 0.15 * lines[..., None]) * (0.9 + 0.1 * noise((h, w), 5, 6111)[..., None])


def cover():
    s, w, h = region("cover")
    rgb[s] = np.array([0.26, 0.12, 0.08]) * (0.8 + 0.3 * noise((h, w), 2, 6120)[..., None])


def labels():
    marks = ["A - D", "E - K", "L - P", "Q - Z"]
    for name, mark in zip(L.LABELS, marks):
        s, w, h = region(name)
        img = Image.new("L", (w * 3, h * 3), 0)
        d = ImageDraw.Draw(img)
        d.rectangle([4, 4, w * 3 - 5, h * 3 - 5], outline=255, width=6)
        font = ImageFont.truetype(SERIF_BOLD, int(h * 3 * 0.5))
        d.text((w * 1.5, h * 1.5), mark, font=font, fill=255, anchor="mm")
        m = np.asarray(img.resize((w, h), Image.BOX), dtype=float) / 255
        card = np.array([0.86, 0.82, 0.70])
        frame = np.array([0.62, 0.47, 0.25])
        edge = np.zeros((h, w))
        edge[:3], edge[-3:], edge[:, :3], edge[:, -3:] = 1, 1, 1, 1
        c = card * (1 - edge[..., None]) + frame * edge[..., None]
        rgb[s] = c * (1 - m[..., None] * 0.85) + np.array([0.12, 0.1, 0.08]) * m[..., None] * 0.85


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            height[grow] = np.roll(height, step, axis)[grow]
            filled |= grow


spines("spines_tall", 6131)
spines("spines_mid", 6132)
spines("spines_short", 6133)
wood()
pages()
cover()
labels()
bleed()
Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_shelves_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 1.0 / L.SPINE_PX_PER_M
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_shelves_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")
(OUT / "int_shelves.tres").write_text(
    '[gd_resource type="StandardMaterial3D" format=3]\n\n'
    '[ext_resource type="Texture2D" path="%sint_shelves_albedo.png" id="1_albedo"]\n'
    '[ext_resource type="Texture2D" path="%sint_shelves_normal.png" id="2_normal"]\n\n'
    '[resource]\nalbedo_texture = ExtResource("1_albedo")\nroughness = 0.78\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n'
    % (RES, RES), encoding="utf8", newline="\n")
print("shelf art written to", OUT)
