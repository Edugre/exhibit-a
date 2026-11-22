"""The Twin Archives set's one texture (asset item P3.2): oak with a worn varnish, a card catalogue's
forty-eight drawers with their brass label holders and pulls, pigeonholes stuffed with scrolls, open
books, tooled leather, a green glass lamp shade and a little brass sign on the reading table. Writes the
texture, a normal map, their import settings and three materials (wood and paper, the glass shades, and
the lamps' glow).
usage: python make_archives_art.py <assets/interior/archives folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import archives_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/archives/"
N = L.ATLAS
SERIF = "C:/Windows/Fonts/pala.ttf"
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
SERIF_ITAL = "C:/Windows/Fonts/palai.ttf"
TYPE = "C:/Windows/Fonts/cour.ttf"
BRASS = np.array([0.78, 0.6, 0.3])
PAPER = np.array([0.86, 0.8, 0.66])

rgb = np.zeros((N, N, 3))
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


def grain(w, h, seed, base, dark=0.55):
    """Oak, the grain running down the texture: long streaks, the odd ring, open pores, then a varnish
    worn pale where hands go and darkened where dust collects."""
    rng = np.random.default_rng(seed)
    streak = gaussian_filter(rng.random((h, w)), (14, 0.7), mode="wrap")
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-9)
    yy, xx = np.mgrid[0:h, 0:w]
    wave = noise((h, w), 18, seed + 1) * 9
    rings = 0.5 + 0.5 * np.sin((xx + wave) * 0.32 + noise((h, w), 30, seed + 2) * 6)
    pores = (noise((h, w), 0.6, seed + 3) > 0.8) & (rings < 0.4)
    v = 0.78 + 0.22 * streak - 0.12 * (rings < 0.25) - 0.15 * pores
    c = np.array(base) * v[..., None]
    wear = np.clip((noise((h, w), 10, seed + 4) - 0.62) * 3, 0, 1)
    grime = np.clip((noise((h, w), 6, seed + 5) - 0.6) * 2.5, 0, 1)
    c = c * (1 + 0.18 * wear[..., None]) * (1 - (1 - dark) * 0.5 * grime[..., None])
    hgt = streak * 0.0003 - pores * 0.0004 - (rings < 0.25) * 0.0002
    return c, hgt


def wood(name, seed, base):
    s, w, h = region(name)
    c, hgt = grain(w, h, seed, base)
    rgb[s] = c
    height[s] = hgt


def drawers():
    """The catalogue's front: six by eight drawers, each with a bevelled edge, a brass frame holding a
    typed card and a brass cup pull, gone dark with handling around the pull."""
    s, w, h = region("drawers")
    cols, rows = L.CATALOGUE_DRAWERS
    c, hgt = grain(w, h, 3101, (0.34, 0.2, 0.1))
    cw, ch = w / cols, h / rows
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = (xx % cw) / cw, (yy % ch) / ch
    edge = np.minimum.reduce([u, 1 - u, v, 1 - v])
    bevel = np.clip(edge / 0.06, 0, 1)
    c = c * (0.55 + 0.45 * bevel)[..., None]
    hgt = hgt + bevel * 0.002
    handled = np.exp(-(((u - 0.5) / 0.22) ** 2 + ((v - 0.72) / 0.18) ** 2))
    c = c * (1 - 0.3 * handled)[..., None]
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def furniture(d, ss):
        for r in range(rows):
            for k in range(cols):
                x0, y0 = k * cw * ss, r * ch * ss
                d.rectangle([x0 + cw * 0.22 * ss, y0 + ch * 0.18 * ss, x0 + cw * 0.78 * ss, y0 + ch * 0.46 * ss], outline=255, width=int(1.5 * ss))
                d.ellipse([x0 + cw * 0.38 * ss, y0 + ch * 0.6 * ss, x0 + cw * 0.62 * ss, y0 + ch * 0.84 * ss], outline=255, width=int(2 * ss))

    def cards(d, ss):
        for r in range(rows):
            for k in range(cols):
                x0, y0 = k * cw * ss, r * ch * ss
                d.rectangle([x0 + cw * 0.25 * ss, y0 + ch * 0.21 * ss, x0 + cw * 0.75 * ss, y0 + ch * 0.43 * ss], fill=255)

    def typing(d, ss):
        font = ImageFont.truetype(TYPE, int(7 * ss))
        n = 0
        for r in range(rows):
            for k in range(cols):
                a = letters[n % 26]
                label = "%s%s-%s%s" % (a, "a" if r % 2 else "e", a, "l" if r % 2 else "z")
                x0, y0 = k * cw * ss, r * ch * ss
                d.text((x0 + cw * 0.5 * ss, y0 + ch * 0.32 * ss), label, font=font, fill=255, anchor="mm")
                n += 1

    metal = drawn(w, h, furniture)
    card = drawn(w, h, cards)
    ink = drawn(w, h, typing)
    tarnish = noise((h, w), 2, 3103)
    c = c * (1 - metal[..., None]) + BRASS * (0.7 + 0.4 * tarnish)[..., None] * metal[..., None]
    paper = PAPER * (0.85 + 0.15 * noise((h, w), 3, 3104))[..., None]
    c = c * (1 - card[..., None]) + paper * card[..., None]
    c = c * (1 - 0.75 * ink[..., None])
    hgt = hgt + metal * 0.0015
    rgb[s] = c
    height[s] = hgt


def cubbies():
    """The scroll rack's front: pigeonholes in dark oak, most of them holding scrolls seen end on,
    parchment rolled tight with the odd red tie, some holes empty to the back."""
    s, w, h = region("cubbies")
    cols, rows = L.RACK_CELLS
    c, hgt = grain(w, h, 3201, (0.22, 0.13, 0.07))
    cw, ch = w / cols, h / rows
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = (xx % cw) / cw, (yy % ch) / ch
    inside = (u > 0.1) & (u < 0.9) & (v > 0.08) & (v < 0.92)
    depth_shade = 0.12 + 0.25 * np.clip(np.minimum.reduce([u - 0.1, 0.9 - u, v - 0.08, 0.92 - v]) / 0.3, 0, 1)
    c = np.where(inside[..., None], c * depth_shade[..., None], c)
    hgt = hgt - inside * 0.01
    rng = np.random.default_rng(3202)
    scrolls = []                                  # (x, y, radius, tied) in pixels, worked out once for both passes
    for r in range(rows):
        for k in range(cols):
            for i in range(rng.choice([0, 2, 3, 3, 4, 5])):
                scrolls.append(((k + rng.uniform(0.3, 0.7)) * cw, (r + rng.uniform(0.38, 0.72)) * ch,
                                rng.uniform(0.15, 0.22) * cw, rng.random() < 0.3, rng.uniform(170, 235)))

    def ends(d, ss):
        for cx, cy, rad, _, tone in scrolls:
            d.ellipse([(cx - rad) * ss, (cy - rad) * ss, (cx + rad) * ss, (cy + rad) * ss], fill=int(tone))

    def spirals(d, ss):
        for cx, cy, rad, tied, _ in scrolls:
            for f in (0.7, 0.42):
                d.ellipse([(cx - rad * f) * ss, (cy - rad * f) * ss, (cx + rad * f) * ss, (cy + rad * f) * ss], outline=255, width=max(1, ss))

    def ties(d, ss):
        for cx, cy, rad, tied, _ in scrolls:
            if tied:
                d.line([(cx - rad) * ss, (cy + rad * 0.25) * ss, (cx + rad) * ss, (cy - rad * 0.25) * ss], fill=255, width=2 * ss)

    roll = drawn(w, h, ends)
    lines = drawn(w, h, spirals)
    parchment = PAPER * (0.75 + 0.35 * roll)[..., None] * (0.9 + 0.1 * noise((h, w), 2, 3203))[..., None]
    mask = (roll > 0.05)[..., None]
    c = np.where(mask, parchment * (1 - 0.35 * lines)[..., None], c)
    tie = drawn(w, h, ties)
    c = c * (1 - tie[..., None]) + np.array([0.55, 0.1, 0.08]) * tie[..., None]
    hgt = hgt + (roll > 0.05) * 0.008
    rgb[s] = c
    height[s] = hgt


def pages(name, seed, heading):
    """An open book: two yellowed pages, a dark gutter, lines of small type and a heading."""
    s, w, h = region(name)
    yy, xx = np.mgrid[0:h, 0:w]
    gutter = np.exp(-((xx - w / 2) / (w * 0.035)) ** 2)
    edge = np.clip(1 - np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / 10, 0, 1)
    c = PAPER * (0.92 + 0.08 * noise((h, w), 4, seed))[..., None]
    c = c * (1 - 0.4 * gutter[..., None]) * (1 - 0.25 * edge[..., None])
    rng = np.random.default_rng(seed + 1)

    def text(d, ss):
        d.text((w * 0.25 * ss, h * 0.14 * ss), heading, font=ImageFont.truetype(SERIF_BOLD, int(14 * ss)), fill=255, anchor="mm")
        for side in (0, 1):
            x0 = (0.07 + side * 0.5) * w
            for k in range(13 if side else 10):
                y = (0.26 + k * 0.055) * h if side == 0 else (0.1 + k * 0.06) * h
                x = x0
                while x < x0 + w * 0.36:
                    word = rng.uniform(5, 16)
                    d.line([x * ss, y * ss, min(x + word, x0 + w * 0.37) * ss, y * ss], fill=200, width=int(1.6 * ss))
                    x += word + rng.uniform(2.5, 4)

    ink = drawn(w, h, text)
    c = c * (1 - 0.7 * ink[..., None])
    rgb[s] = c
    height[s] = -gutter * 0.003


def leather():
    s, w, h = region("leather")
    bands = [np.array([0.42, 0.1, 0.08]), np.array([0.14, 0.26, 0.15]), np.array([0.32, 0.2, 0.1]), np.array([0.12, 0.14, 0.26])]
    c = np.zeros((h, w, 3))
    for i, col in enumerate(bands):
        c[i * h // 4:(i + 1) * h // 4] = col
    pebble = noise((h, w), 0.8, 3301)
    c = c * (0.8 + 0.3 * pebble)[..., None] * (0.85 + 0.25 * noise((h, w), 6, 3302))[..., None]
    yy = np.arange(h)[:, None].repeat(w, 1)
    gilt = ((yy % (h // 4)) < 2) | ((yy % (h // 4)) > h // 4 - 3)
    c = np.where(gilt[..., None], BRASS * 0.9, c)
    rgb[s] = c
    height[s] = pebble * 0.0004


def brass():
    s, w, h = region("brass")
    streak = gaussian_filter(np.random.default_rng(3401).random((h, w)), (0.35, 25), mode="wrap")
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-9)
    rgb[s] = BRASS * (0.8 + 0.3 * streak)[..., None]


def glass():
    """The banker's lamp shade: green glass, darker at its rims, with a long pale highlight."""
    s, w, h = region("glass")
    t = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    c = np.array([0.08, 0.38, 0.2]) * (0.6 + 0.6 * np.sin(np.pi * t))[..., None]
    c = c + np.array([0.5, 0.7, 0.55]) * np.exp(-((t - 0.3) / 0.06) ** 2)[..., None] * 0.6
    rgb[s] = np.clip(c * (0.95 + 0.1 * noise((h, w), 3, 3501))[..., None], 0, 1)


def sign():
    """A brass plate on a little oak block, on the reading table."""
    s, w, h = region("sign")
    streak = gaussian_filter(np.random.default_rng(3601).random((h, w)), (0.35, 25), mode="wrap")
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-9)
    c = BRASS * (0.8 + 0.3 * streak)[..., None]

    def engrave(d, ss):
        d.rectangle([3 * ss, 3 * ss, (w - 4) * ss, (h - 4) * ss], outline=255, width=ss)
        d.text((w * ss / 2, h * ss * 0.4), "S I L E N C E", font=ImageFont.truetype(SERIF_BOLD, int(17 * ss)), fill=255, anchor="mm")
        d.text((w * ss / 2, h * ss * 0.75), "She can hear you.", font=ImageFont.truetype(SERIF_ITAL, int(12 * ss)), fill=255, anchor="mm")

    cut = drawn(w, h, engrave)
    rgb[s] = c * (1 - cut[..., None]) + np.array([0.1, 0.08, 0.05]) * cut[..., None]
    height[s] = -cut * 0.0008


def chair_back():
    """A library chair's padded back: green leather buttoned in a grid."""
    s, w, h = region("chair_back")
    c = np.array([0.12, 0.24, 0.14]) * (0.8 + 0.3 * noise((h, w), 0.8, 3701))[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    buttons = np.zeros((h, w))
    for by in range(1, 4):
        for bx in range(1, 4):
            cx, cy = bx * w / 4 + (by % 2) * 0, by * h / 4
            buttons = np.maximum(buttons, np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / 18)))
    puff = 0.5 + 0.5 * np.cos(xx / w * 8 * np.pi) * np.cos(yy / h * 8 * np.pi)
    c = c * (0.75 + 0.3 * puff)[..., None] * (1 - 0.6 * buttons)[..., None]
    c = c + BRASS * 0.5 * (buttons > 0.6)[..., None]
    rgb[s] = np.clip(c, 0, 1)
    height[s] = puff * 0.003 - buttons * 0.003


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            filled |= grow


wood("oak", 3001, (0.38, 0.23, 0.12))
wood("oak_dark", 3011, (0.21, 0.12, 0.065))
drawers()
cubbies()
pages("pages", 3801, "OVERDUE")
pages("pages_2", 3811, "Fines, Vol. VII")
leather()
brass()
glass()
s, w, h = region("glow")
rgb[s] = np.array([1.0, 0.9, 0.68])
sign()
chair_back()
bleed()
Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_archives_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 0.002
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_archives_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")
MATERIALS = {
    "int_archives": 'roughness = 0.58\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n',
    # Green glass, lit from inside: it glows a little, as a lamp left on would
    "int_archives_glass": 'roughness = 0.12\nemission_enabled = true\nemission_texture = ExtResource("1_albedo")\nemission_energy_multiplier = 0.9\n',
    "int_archives_glow": 'emission_enabled = true\nemission_texture = ExtResource("1_albedo")\nemission_energy_multiplier = 3.0\n',
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(
        '[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_archives_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_archives_normal.png" id="2_normal"]\n\n'
        '[resource]\nalbedo_texture = ExtResource("1_albedo")\n%s' % (RES, RES, extra), encoding="utf8", newline="\n")
print("archives art written to", OUT)
