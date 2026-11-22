"""The doorway set's one texture (asset item K1): worn limestone for the arch stones, the carved strips
and blocks round the doorways, an owl on the keystone (the library's bird), and a brass plaque with
each room's name engraved in it. Writes the texture, a normal map, their import settings and three
materials: the stone, the brass (it catches its little lamp's light) and the lamp itself.
usage: python make_doorway_art.py <assets/interior/doorways folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import doorway_layout as L  # noqa: E402
import int_dims as D  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/doorways/"
N = L.ATLAS
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
SERIF_ITAL = "C:/Windows/Fonts/palai.ttf"
STONE = np.array(D.MOULDING_TINT)
BRASS = np.array([0.8, 0.62, 0.3])
PATINA = np.array([0.11, 0.085, 0.05])

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


def edge_distance(w, h):
    x = np.arange(w)[None, :].repeat(h, 0)
    y = np.arange(h)[:, None].repeat(w, 1)
    return np.minimum.reduce([x, w - 1 - x, y, h - 1 - y]).astype(float)


def limestone(w, h, seed, grime=0.0):
    """Cream limestone: a little uneven in colour, pitted with pores, with the odd darker fleck."""
    c = STONE * (0.86 + 0.14 * noise((h, w), 9, seed)[..., None])
    c = c * (0.96 + 0.06 * noise((h, w), 1.2, seed + 1)[..., None])
    pores = (noise((h, w), 0.7, seed + 2) > 0.83).astype(float)
    flecks = (noise((h, w), 2.5, seed + 3) > 0.9).astype(float) * 0.5
    c = c * (1 - 0.3 * pores[..., None]) * (1 - 0.12 * flecks[..., None])
    soot = np.clip((noise((h, w), 16, seed + 4) - 0.5) * 2.2, 0, 1) * grime
    c = c * (1 - 0.35 * soot[..., None])
    # Old water runs: faint darker streaks down the face, and a warmer cast where it stained
    runs = gaussian_filter(np.random.default_rng(seed + 5).random((h, w)), (14, 0.9), mode="wrap")
    runs = np.clip((runs - runs.mean()) / (runs.std() + 1e-9) - 0.6, 0, 3) / 3
    c = c * (1 - 0.16 * runs[..., None]) * (1 + np.array([0.02, 0.0, -0.04]) * runs[..., None])
    c = c * (0.93 + 0.1 * noise((h, w), 4, seed + 6)[..., None])
    return c, -pores * 0.0004


def dressed_block(name, seed):
    """One dressed stone: a smooth drafted margin round a claw-tooled field, chipped arrises, and a dark
    joint at the very edge where it meets its neighbour."""
    s, w, h = region(name)
    c, hgt = limestone(w, h, seed, grime=0.25)
    e = edge_distance(w, h)
    rng = np.random.default_rng(seed + 10)
    angle = rng.uniform(-0.5, 0.5)
    yy, xx = np.mgrid[0:h, 0:w]
    tool = np.sin((xx * np.cos(angle) + yy * np.sin(angle)) * 1.6 + noise((h, w), 3, seed + 11) * 4)
    field = e > 9
    c = c * (1 + np.where(field, 0.04 * tool, 0.05)[..., None])
    hgt = hgt + np.where(field, 0.00025 * tool - 0.0006, 0.0)
    chips = (noise((h, w), 2.0, seed + 12) > 0.9 - 0.25 * np.exp(-e / 4)) & (e < 12)
    c = np.where(chips[..., None], c * 0.82 + 0.06, c)
    hgt = hgt - chips * 0.0012
    joint = np.clip(1 - e / 2.5, 0, 1)
    c = c * (1 - 0.55 * joint[..., None])
    hgt = hgt - joint * 0.002
    rgb[s] = c
    height[s] = hgt


def plain_stone():
    s, w, h = region("stone")
    c, hgt = limestone(w, h, 9101, grime=0.3)
    rgb[s] = c
    height[s] = hgt


def profile_strip(name, seed, profile, along_x=False, scuff_end=None):
    """A carved moulding: `profile` gives its height across the strip (0 to 1), the shading follows the
    curves, and the low end collects scuffs."""
    s, w, h = region(name)
    c, hgt = limestone(w, h, seed, grime=0.2)
    across = np.linspace(0, 1, h if along_x else w)
    p = np.array([profile(u) for u in across])
    prof = p[:, None].repeat(w, 1) if along_x else p[None, :].repeat(h, 0)
    curve = gaussian_filter(prof, 1.5) - prof
    shade = np.clip(0.82 + 0.5 * prof + 6.0 * curve, 0.55, 1.08)
    c = c * shade[..., None]
    if scuff_end is not None:
        t = np.linspace(0, 1, h)[:, None].repeat(w, 1)
        low = np.clip((t - scuff_end) / (1 - scuff_end), 0, 1) ** 1.5
        scuffs = noise((h, w), 1.5, seed + 5) * low
        c = c * (1 - 0.35 * scuffs[..., None]) * (1 - 0.15 * low[..., None])
    rgb[s] = c
    height[s] = hgt + prof * 0.012


def casing_profile(u):
    """Across a doorway's side strip, from the opening's edge out to the wall: a bead, two stepped faces
    and an ogee down to the wall."""
    if u < 0.09:
        return 0.55 + 0.45 * np.sqrt(max(0.0, 1 - ((u - 0.045) / 0.045) ** 2))
    if u < 0.14:
        return 0.55
    if u < 0.5:
        return 0.85
    if u < 0.56:
        return 0.7
    if u < 0.62:
        return 0.62
    t = (u - 0.62) / 0.38
    return 0.62 * (0.5 + 0.5 * np.cos(np.pi * t)) + 0.04 * np.sin(np.pi * t)


def impost_profile(v):
    """Top to bottom of the cap the arch springs from: a flat top, a cyma, a fillet and a bead."""
    if v < 0.25:
        return 1.0
    if v < 0.7:
        t = (v - 0.25) / 0.45
        return 1.0 - 0.5 * (1 - np.cos(np.pi * t)) / 2 - 0.15 * t
    if v < 0.8:
        return 0.55
    return 0.35 + 0.25 * np.sin(np.pi * (v - 0.8) / 0.2)


def plinth():
    s, w, h = region("plinth")
    c, hgt = limestone(w, h, 9301, grime=0.6)
    t = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    torus = np.clip(1 - ((t - 0.1) / 0.08) ** 2, 0, 1)
    c = c * (0.8 + 0.25 * torus)[..., None]
    kicks = noise((h, w), 1.2, 9302) * np.clip((t - 0.35) / 0.65, 0, 1)
    c = c * (1 - 0.45 * kicks[..., None]) * 0.92
    e = edge_distance(w, h)
    c = c * (1 - 0.4 * np.clip(1 - e / 2.5, 0, 1))[..., None]
    rgb[s] = c
    height[s] = hgt + torus * 0.004 - kicks * 0.0005


def relief(name, seed, shapes):
    """A carved panel: `shapes` draws the raised parts (white is highest) inside a raised border."""
    s, w, h = region(name)
    c, hgt = limestone(w, h, seed, grime=0.3)
    raised = drawn(w, h, shapes)
    raised = gaussian_filter(raised, 0.9)
    e = edge_distance(w, h)
    border = np.clip((10 - e) / 3, 0, 1) * (e > 2)
    form = np.maximum(raised, border * 0.8)
    cavity = np.clip(gaussian_filter(form, 3) - form, 0, 1)
    c = c * (0.86 + 0.18 * form - 1.4 * cavity)[..., None]
    c = c * (1 - 0.5 * np.clip(1 - e / 2.5, 0, 1))[..., None]
    rgb[s] = np.clip(c, 0, 1)
    height[s] = hgt + form * 0.01


def owl(d, ss):
    """Athena's owl, perched on a closed book: the library's bird."""
    W, H = 128 * ss, 192 * ss
    f = lambda x, y: (x * W, y * H)
    d.rectangle([*f(0.22, 0.8), *f(0.78, 0.9)], fill=200)                     # the book
    d.line([f(0.24, 0.85), f(0.76, 0.85)], fill=120, width=2 * ss)
    d.ellipse([*f(0.26, 0.36), *f(0.74, 0.82)], fill=170)                     # body
    d.ellipse([*f(0.27, 0.16), *f(0.73, 0.5)], fill=210)                      # head
    d.polygon([f(0.28, 0.24), f(0.33, 0.1), f(0.4, 0.2)], fill=210)           # ear tufts
    d.polygon([f(0.72, 0.24), f(0.67, 0.1), f(0.6, 0.2)], fill=210)
    for cx in (0.39, 0.61):                                                     # eyes: rings with deep pupils
        d.ellipse([*f(cx - 0.1, 0.24), *f(cx + 0.1, 0.39)], fill=255)
        d.ellipse([*f(cx - 0.045, 0.285), *f(cx + 0.045, 0.345)], fill=70)
    d.polygon([f(0.47, 0.37), f(0.53, 0.37), f(0.5, 0.45)], fill=255)         # beak
    for k in range(4):                                                          # folded wings
        y = 0.5 + k * 0.07
        d.arc([*f(0.27, y), *f(0.5, y + 0.2)], 90, 200, fill=90, width=2 * ss)
        d.arc([*f(0.5, y), *f(0.73, y + 0.2)], -20, 90, fill=90, width=2 * ss)
    for cx in (0.42, 0.58):                                                     # talons on the book
        d.rectangle([*f(cx - 0.04, 0.77), *f(cx + 0.04, 0.81)], fill=230)


def scroll(d, ss):
    """A console's face: a rolled volute over a long leaf."""
    W = 128 * ss
    f = lambda x, y: (x * W, y * W)
    d.ellipse([*f(0.2, 0.02), *f(0.8, 0.62)], fill=150)
    turns = [(0.5 + (0.28 - 0.25 * a / 18.85) * np.cos(a), 0.32 + (0.28 - 0.25 * a / 18.85) * np.sin(a)) for a in np.linspace(0, 18.85, 160)]
    d.line([f(x, y) for x, y in turns], fill=255, width=5 * ss, joint="curve")
    d.ellipse([*f(0.46, 0.28), *f(0.54, 0.36)], fill=255)
    d.polygon([f(0.32, 0.55), f(0.68, 0.55), f(0.56, 0.97), f(0.44, 0.97)], fill=200)
    d.line([f(0.5, 0.58), f(0.5, 0.95)], fill=110, width=2 * ss)
    for k in range(4):
        y = 0.62 + k * 0.08
        d.line([f(0.5, y), f(0.38 + k * 0.02, y + 0.06)], fill=120, width=ss)
        d.line([f(0.5, y), f(0.62 - k * 0.02, y + 0.06)], fill=120, width=ss)


def brushed_brass(w, h, seed):
    streak = gaussian_filter(np.random.default_rng(seed).random((h, w)), (0.35, 30), mode="wrap")
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-9)
    tarnish = np.clip((noise((h, w), 4, seed + 1) - 0.62) * 3, 0, 1)
    c = BRASS * (0.8 + 0.3 * streak[..., None])
    c = c * (1 - 0.2 * tarnish[..., None]) + np.array([0.0, 0.02, 0.01]) * tarnish[..., None]
    return c


def brass():
    s, w, h = region("brass")
    rgb[s] = brushed_brass(w, h, 9501)
    height[s] = 0


def lamp():
    s, w, h = region("lamp")
    rgb[s] = np.array([1.0, 0.86, 0.62])


def plaque(name, title, subtitle, seed):
    """Engraved brass: a double border line, the room's name in capitals and a line under it in italics,
    filled with dark patina; screws at the corners, and the edges rubbed bright."""
    s, w, h = region("plaque_" + name)
    c = brushed_brass(w, h, seed)
    e = edge_distance(w, h)
    c = c * (1 + 0.12 * np.clip(1 - e / 5, 0, 1))[..., None]

    def engrave(d, ss):
        d.rectangle([7 * ss, 7 * ss, (w - 8) * ss, (h - 8) * ss], outline=255, width=int(1.6 * ss))
        d.rectangle([11 * ss, 11 * ss, (w - 12) * ss, (h - 12) * ss], outline=255, width=ss)
        size = 44 * ss
        font = ImageFont.truetype(SERIF_BOLD, size)
        spaced = " ".join(title)   # letter-spaced, with three spaces between words
        while d.textlength(spaced, font=font) > (w - 60) * ss:
            size -= ss
            font = ImageFont.truetype(SERIF_BOLD, size)
        d.text((w * ss / 2, h * ss * 0.42), spaced, font=font, fill=255, anchor="mm")
        small = ImageFont.truetype(SERIF_ITAL, int(17 * ss))
        d.text((w * ss / 2, h * ss * 0.76), subtitle, font=small, fill=255, anchor="mm")
        for x, y in ((18, 18), (w - 19, 18), (18, h - 19), (w - 19, h - 19)):
            d.ellipse([(x - 5) * ss, (y - 5) * ss, (x + 5) * ss, (y + 5) * ss], outline=255, width=int(1.5 * ss))
            d.line([(x - 3) * ss, (y + 2) * ss, (x + 3) * ss, (y - 2) * ss], fill=255, width=ss)

    cut = drawn(w, h, engrave)
    grime = np.clip(gaussian_filter(cut, 1.2) * 1.3, 0, 1)
    c = c * (1 - 0.25 * grime[..., None])
    c = c * (1 - cut[..., None]) + PATINA * cut[..., None]
    rgb[s] = c
    height[s] = -gaussian_filter(cut, 0.6) * 0.0015


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            filled |= grow


for k in range(8):
    dressed_block("block_%d" % k, 9001 + 17 * k)
plain_stone()
profile_strip("casing", 9201, casing_profile, scuff_end=0.75)
profile_strip("impost", 9401, impost_profile, along_x=True)
plinth()
relief("keystone", 9601, owl)
relief("console", 9701, scroll)
brass()
lamp()
for i, (name, title, subtitle) in enumerate(L.PLAQUES):
    plaque(name, title, subtitle, 9801 + 13 * i)
bleed()
Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_doorway_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 0.002
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_doorway_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")
MATERIALS = {
    "int_doorway": 'roughness = 0.8\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n',
    # The brass glows a little, as if its lamp were on it, so the room's name reads in the dark
    "int_plaque": 'metallic = 0.85\nroughness = 0.38\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n'
                  'emission_enabled = true\nemission_texture = ExtResource("1_albedo")\nemission_energy_multiplier = 0.35\n',
    "int_plaque_lamp": 'emission_enabled = true\nemission_texture = ExtResource("1_albedo")\nemission_energy_multiplier = 3.0\n',
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(
        '[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_doorway_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_doorway_normal.png" id="2_normal"]\n\n'
        '[resource]\nalbedo_texture = ExtResource("1_albedo")\n%s' % (RES, RES, extra), encoding="utf8", newline="\n")
print("doorway art written to", OUT)
