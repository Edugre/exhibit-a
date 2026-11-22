"""The glass display cases' one texture (asset item P1.2): walnut cabinets, brass, smudged glass, a
black-figure amphora with a familiar wooden horse on it, coins, a scroll, velvet and the curators'
cards. The alpha channel only matters on the glass: it's how much the pane shows, smudges and all.
Writes the texture, a normal map, their import settings and the three materials.
usage: python make_cases_art.py <assets/interior/cases folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True    # no __pycache__ next to the scripts
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import cases_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/cases/"
N = L.ATLAS
SERIF = "C:/Windows/Fonts/pala.ttf"
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
SERIF_ITAL = "C:/Windows/Fonts/palai.ttf"
BLACK_GLAZE = np.array([0.07, 0.055, 0.05])
CLAY = np.array([0.70, 0.38, 0.21])

rgb = np.zeros((N, N, 3))
alpha = np.ones((N, N))
height = np.zeros((N, N))


def noise(shape, sigma, seed):
    n = gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-9)


def region(name):
    x, y, w, h = L.REGIONS[name]
    return (slice(y, y + h), slice(x, x + w)), w, h


def drawn(w, h, fn, ss=3):
    img = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(img), ss)
    return np.asarray(img.resize((w, h), Image.BOX), dtype=float) / 255


def fit(text, path, max_w, max_h, ss):
    size = int(max_h * ss)
    while size > 6:
        font = ImageFont.truetype(path, size)
        b = font.getbbox(text)
        if b[2] - b[0] <= max_w * ss and b[3] - b[1] <= max_h * ss:
            return font
        size = int(size * 0.93)
    return ImageFont.truetype(path, 6)


# --- Cabinet wood, brass, glass and velvet --------------------------------------------------------------
def wood():
    s, w, h = region("wood")
    grain = noise((h, w), (40, 1.0), 5101)
    figure = noise((h, w), (90, 3.5), 5102)
    rings = np.sin(np.linspace(0, 60, w)[None, :] + figure * 9) * 0.5 + 0.5
    base = np.array([0.30, 0.19, 0.12])
    c = base * (0.82 + 0.25 * grain[..., None] + 0.1 * rings[..., None])
    worn = np.clip((noise((h, w), 14, 5103) - 0.55) * 3, 0, 1)
    c = c * (1 - worn[..., None] * 0.15) + np.array([0.42, 0.30, 0.2]) * worn[..., None] * 0.15
    rgb[s] = c
    height[s] = grain * 0.0003 + rings * 0.0001


def brass():
    s, w, h = region("brass")
    brushed = noise((h, w), (0.6, 25), 5110)
    tarnish = noise((h, w), 6, 5111)
    rgb[s] = np.array([0.72, 0.55, 0.30]) * (0.85 + 0.2 * brushed[..., None]) * (1 - 0.25 * np.clip(tarnish - 0.5, 0, 1)[..., None])


def glass():
    """Mostly clear, with greasy fingerprints at hand height and dust gathered at the corners."""
    s, w, h = region("glass")
    rgb[s] = np.array([0.80, 0.88, 0.86])
    yy, xx = np.mgrid[0:h, 0:w] / max(w, h)
    smudge = np.clip((noise((h, w), 5, 5120) - 0.62) * 3, 0, 1) * (1 - np.abs(yy - 0.55) * 1.6).clip(0, 1)
    prints = np.zeros((h, w))
    rng = np.random.default_rng(5121)
    for _ in range(9):
        cx, cy = rng.uniform(0.15, 0.85, 2) * [w, h]
        rr = np.sqrt((np.mgrid[0:h, 0:w][1] - cx) ** 2 + (np.mgrid[0:h, 0:w][0] - cy) ** 2)
        prints = np.maximum(prints, np.exp(-(rr / 4.5) ** 2) * (0.6 + 0.4 * np.sin(rr * 2.2)))
    edge = np.minimum.reduce([xx, 1 - xx, yy, 1 - yy])
    dust = np.clip(1 - edge * 14, 0, 1) * 0.5
    alpha[s] = np.clip(0.07 + smudge * 0.12 + prints * 0.1 + dust * 0.16, 0, 1)


def velvet():
    s, w, h = region("velvet")
    fuzz = noise((h, w), 0.7, 5130)
    crush = noise((h, w), (4, 18), 5131)
    rgb[s] = np.array([0.32, 0.06, 0.08]) * (0.75 + 0.3 * crush[..., None] + 0.12 * fuzz[..., None])
    height[s] = fuzz * 0.0004 + crush * 0.0006


# --- The amphora: black-figure, with a wooden horse in the frieze ---------------------------------------
def horse(d, x, y, sc):
    """A wheeled wooden horse, in profile."""
    p = lambda pts: [(x + a * sc, y + b * sc) for a, b in pts]
    d.polygon(p([(-30, -6), (22, -8), (26, 6), (-28, 8)]), fill=255)             # body
    d.polygon(p([(14, -6), (24, -34), (34, -38), (40, -32), (30, -24), (24, -2)]), fill=255)   # neck and head
    d.polygon(p([(30, -40), (34, -50), (36, -40)]), fill=255)                      # ear
    for lx in (-22, -12, 8, 18):                                                   # legs
        d.rectangle(p([(lx, 6), (lx + 5, 24)])[0] + p([(lx + 5, 24)])[0], fill=255)
    d.rectangle(p([(-30, 24), (26, 28)])[0] + p([(26, 28)])[0], fill=255)          # the board it stands on
    for wx in (-22, 16):                                                           # wheels
        cx, cy = p([(wx, 32)])[0]
        r = 6 * sc
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    d.polygon(p([(-30, -4), (-40, 8), (-36, 10), (-28, 2)]), fill=255)            # tail


def warrior(d, x, y, sc, facing):
    p = lambda pts: [(x + a * sc * facing, y + b * sc) for a, b in pts]
    cx, cy = p([(0, -36)])[0]
    d.ellipse([cx - 6 * sc, cy - 6 * sc, cx + 6 * sc, cy + 6 * sc], fill=255)      # head
    d.polygon(p([(-6, -40), (8, -40), (2, -52)]), fill=255)                        # helmet crest
    d.polygon(p([(-5, -30), (5, -30), (7, 0), (-7, 0)]), fill=255)                 # body
    d.polygon(p([(-7, 0), (-2, 0), (-8, 30), (-13, 30)]), fill=255)                # legs
    d.polygon(p([(2, 0), (7, 0), (12, 30), (7, 30)]), fill=255)
    sx, sy = p([(10, -16)])[0]
    d.ellipse([sx - 11 * sc, sy - 11 * sc, sx + 11 * sc, sy + 11 * sc], fill=255)  # round shield
    d.line(p([(-4, -26), (-4, -62)]), fill=255, width=int(2 * sc))                 # spear


def pottery():
    s, w, h = region("pottery")
    t = 1 - (np.arange(h) + 0.5) / h       # 0 at the foot, 1 at the lip, matching cases_build.py
    clay = CLAY * (0.92 + 0.12 * noise((h, w), 3, 5140)[..., None])
    c = np.repeat(clay[None, 0], h, 0) if False else clay.copy()
    black = (t > 0.93) | ((t > 0.08) & (t < 0.36)) | ((t > 0.75) & (t < 0.77)) | ((t > 0.405) & (t < 0.42))
    c[black] = BLACK_GLAZE

    def frieze(d, ss):
        top, bottom = (1 - 0.75) * h * ss, (1 - 0.42) * h * ss
        mid = (top + bottom) / 2 + 6 * ss
        sc = (bottom - top) / 70
        for k in range(3):                 # three scenes round the pot; whole numbers keep the seam hidden
            base = (k + 0.5) / 3 * w * ss
            horse(d, base, mid, sc)
            warrior(d, base - 55 * sc, mid + 4 * sc, sc * 0.95, 1)
            warrior(d, base + 58 * sc, mid + 4 * sc, sc * 0.95, -1)
        # A meander under the neck, and tongues round the neck
        y0, y1 = (1 - 0.80) * h * ss, (1 - 0.77) * h * ss
        step = w * ss / 24
        for i in range(24):
            x = i * step
            d.line([(x, y1), (x, y0), (x + step * 0.7, y0), (x + step * 0.7, (y0 + y1) / 2), (x + step * 0.35, (y0 + y1) / 2)], fill=255, width=int(1.2 * ss))
        for i in range(30):
            x = (i + 0.5) / 30 * w * ss
            d.ellipse([x - step * 0.3, (1 - 0.92) * h * ss, x + step * 0.3, (1 - 0.84) * h * ss], fill=255)

    m = drawn(w, h, frieze)
    m *= np.clip((noise((h, w), 1.5, 5141) - 0.08) * 4, 0, 1)     # chipped glaze
    c = c * (1 - m[..., None]) + BLACK_GLAZE * m[..., None]
    # Incised details: thin clay-coloured lines scratched through the black, as the painters did
    inc = drawn(w, h, lambda d, ss: [d.line([((k + 0.5) / 3 * w * ss - 20 * ss, (1 - 0.6) * h * ss), ((k + 0.5) / 3 * w * ss + 18 * ss, (1 - 0.6) * h * ss)], fill=255, width=ss) for k in range(3)])
    c = c * (1 - inc[..., None] * 0.6) + CLAY * inc[..., None] * 0.6
    c *= (1 - 0.18 * np.clip((noise((h, w), 10, 5142) - 0.55) * 3, 0, 1))[..., None]      # two and a half thousand years
    rgb[s] = c
    ms, mw, mh = region("mouth")
    rgb[ms] = BLACK_GLAZE * 0.4


# --- Coins, scroll and labels --------------------------------------------------------------------------
def coin(name, metal, motif, seed):
    s, w, h = region(name)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - w / 2 + 0.5) ** 2 + (yy - h / 2 + 0.5) ** 2) / (w / 2)

    def art(d, ss):
        c = w * ss / 2
        if motif == "owl":
            d.ellipse([c - 14 * ss, c - 18 * ss, c + 14 * ss, c + 20 * ss], fill=200)
            for ex in (-6, 6):
                d.ellipse([c + ex * ss - 5 * ss, c - 12 * ss, c + ex * ss + 5 * ss, c - 2 * ss], fill=255)
        else:
            horse(d, c + 2 * ss, c + 4 * ss, ss * 0.42)
        d.ellipse([c - 28 * ss, c - 28 * ss, c + 28 * ss, c + 28 * ss], outline=255, width=2 * ss)

    relief = drawn(w, h, art)
    worn = noise((h, w), 2, seed)
    c = metal * (0.75 + 0.3 * worn[..., None]) * (0.8 + 0.3 * relief[..., None])
    c *= (1 - 0.35 * np.clip((r - 0.85) * 6, 0, 1))[..., None]
    rgb[s] = c
    height[s] = relief * 0.0012


def parchment():
    s, w, h = region("parchment")
    c = np.array([0.80, 0.70, 0.52]) * (0.85 + 0.2 * noise((h, w), 6, 5150)[..., None])

    def lines(d, ss):
        rng = np.random.default_rng(5151)
        for row in range(9):
            y = (row + 1.2) / 10.5 * h * ss
            x = 12 * ss
            while x < w * ss - 20 * ss:
                ln = rng.uniform(6, 22) * ss
                d.line([(x, y), (x + ln, y + rng.uniform(-0.6, 0.6) * ss)], fill=255, width=ss)
                x += ln + rng.uniform(3, 6) * ss

    m = drawn(w, h, lines)
    c = c * (1 - m[..., None] * 0.7) + np.array([0.18, 0.12, 0.08]) * m[..., None] * 0.7
    edge = np.minimum.reduce([np.arange(w)[None, :].repeat(h, 0), np.arange(w)[::-1][None, :].repeat(h, 0)])
    c *= (0.7 + 0.3 * np.clip(edge / 12, 0, 1))[..., None]
    rgb[s] = c
    height[s] = noise((h, w), 3, 5152) * 0.0004


def card(name, title, lines):
    s, w, h = region(name)
    c = np.array([0.90, 0.88, 0.82]) * (0.96 + 0.05 * noise((h, w), 3, sum(map(ord, name)))[..., None])

    def text(d, ss):
        d.text((w * ss / 2, h * ss * 0.2), title, font=fit(title, SERIF_BOLD, w * 0.86, h * 0.17, ss), fill=255, anchor="mm")
        for i, line in enumerate(lines):
            d.text((w * ss * 0.07, h * ss * (0.42 + i * 0.17)), line, font=fit(line, SERIF_ITAL, w * 0.86, h * 0.13, ss), fill=255, anchor="lm")

    m = drawn(w, h, text)
    rgb[s] = c * (1 - m[..., None]) + np.array([0.12, 0.11, 0.10]) * m[..., None]


def plate():
    s, w, h = region("plate")
    c = np.array([0.72, 0.55, 0.30]) * (0.88 + 0.15 * noise((h, w), (0.6, 20), 5160)[..., None])
    msg = "PLEASE DO NOT TOUCH THE GLASS. SHE WILL KNOW."
    m = drawn(w, h, lambda d, ss: d.text((w * ss / 2, h * ss / 2), msg, font=fit(msg, SERIF_BOLD, w * 0.9, h * 0.5, ss), fill=255, anchor="mm"))
    rgb[s] = c * (1 - m[..., None] * 0.8) + np.array([0.18, 0.12, 0.06]) * m[..., None] * 0.8
    height[s] = -m * 0.0004


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            filled |= grow


wood()
brass()
glass()
velvet()
pottery()
coin("coin_gold", np.array([0.80, 0.62, 0.25]), "owl", 5170)
coin("coin_silver", np.array([0.66, 0.66, 0.68]), "horse", 5171)
parchment()
card("card_tall", "AMPHORA, c. 520 B.C.", ["Shows a large wooden horse.", "Curators disagree on whether", "it was a gift."])
card("card_low", "COINS OF TROY", ["Spent in full on one horse.", "SCROLL, Library of Alexandria.", "Overdue."])
plate()
bleed()
Image.fromarray(np.dstack([np.clip(rgb * 255 + 0.5, 0, 255), np.clip(alpha * 255 + 0.5, 0, 255)]).astype(np.uint8), "RGBA").save(OUT / "int_cases_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 0.004
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_cases_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")

MATERIALS = {
    "int_cases": "roughness = 0.6\n",
    "int_brass": "metallic = 1.0\nroughness = 0.38\n",
    "int_glass": "transparency = 1\nroughness = 0.04\nmetallic_specular = 0.8\n",
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(
        '[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_cases_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_cases_normal.png" id="2_normal"]\n\n'
        '[resource]\n%salbedo_texture = ExtResource("1_albedo")\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n'
        % (RES, RES, extra), encoding="utf8", newline="\n")
print("case art written to", OUT)
