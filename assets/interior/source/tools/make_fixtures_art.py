"""The fixtures' one small texture (asset item P1.5): brushed brass and off-white painted steel, the
warm opal glass of a pendant's bowl, an office light panel's prismatic diffuser (one tube going grey),
the green EXIT sign, the dark behind a vent's louvres, and the brass plate under the vent. Writes the
texture, a normal map, their import settings and two materials: the metal, and everything that glows.
usage: python make_fixtures_art.py <assets/interior/fixtures folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import fixtures_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/fixtures/"
N = L.ATLAS
SANS_BOLD = "C:/Windows/Fonts/arialbd.ttf"
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
SERIF_ITAL = "C:/Windows/Fonts/palai.ttf"
BRASS = np.array([0.78, 0.6, 0.3])
EXIT_GREEN = np.array([0.1, 0.85, 0.35])

rgb = np.zeros((N, N, 3))
height = np.zeros((N, N))


def noise(shape, sigma, seed):
    n = gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-9)


def region(name):
    x, y, w, h = L.REGIONS[name]
    return (slice(y, y + h), slice(x, x + w)), w, h


def drawn(w, h, fn, ss=4):
    img = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(img), ss)
    return np.asarray(img.resize((w, h), Image.BOX), dtype=float) / 255


def brass():
    s, w, h = region("brass")
    streak = gaussian_filter(np.random.default_rng(5101).random((h, w)), (0.35, 20), mode="wrap")
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-9)
    tarnish = np.clip((noise((h, w), 3, 5102) - 0.6) * 3, 0, 1)
    rgb[s] = BRASS * (0.8 + 0.3 * streak)[..., None] * (1 - 0.25 * tarnish)[..., None]


def steel():
    """Off-white paint on steel, with dust settled on it and a few rust freckles."""
    s, w, h = region("steel")
    c = np.array([0.82, 0.8, 0.74]) * (0.9 + 0.1 * noise((h, w), 3, 5201))[..., None]
    dust = np.clip((noise((h, w), 6, 5202) - 0.5) * 2, 0, 1)
    rust = noise((h, w), 0.8, 5203) > 0.93
    c = c * (1 - 0.15 * dust)[..., None]
    c = np.where(rust[..., None], np.array([0.45, 0.25, 0.12]), c)
    rgb[s] = c
    height[s] = rust * -0.0003


def opal():
    s, w, h = region("opal")
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - w / 2, yy - h / 2) / (w / 2)
    rgb[s] = np.array([1.0, 0.9, 0.72]) * (0.75 + 0.25 * np.clip(1 - r, 0, 1))[..., None]


def panel():
    """An office light panel seen from below: a prismatic lens over three tubes, the middle one going
    grey at its ends, dead flies in a corner."""
    s, w, h = region("panel")
    yy, xx = np.mgrid[0:h, 0:w]
    tubes = np.zeros((h, w))
    for k, y in enumerate((0.22, 0.5, 0.78)):
        band = np.exp(-((yy / h - y) / 0.07) ** 2)
        if k == 1:
            band = band * (0.55 + 0.45 * np.clip(np.minimum(xx, w - xx) / (w * 0.18), 0, 1))
        tubes = np.maximum(tubes, band)
    prism = 0.92 + 0.08 * ((xx // 3 + yy // 3) % 2)
    c = np.array([0.86, 0.94, 1.0]) * (0.45 + 0.55 * tubes)[..., None] * prism[..., None]
    flies = (noise((h, w), 0.7, 5301) > 0.97) & (xx < w * 0.2) & (yy > h * 0.7)
    c = np.where(flies[..., None], c * 0.25, c)
    edge = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy])
    c = np.where((edge < 4)[..., None], np.array([0.75, 0.74, 0.7]), c)
    rgb[s] = c


def exit_sign():
    """EXIT in white on green, the running figure and an arrow toward the door."""
    s, w, h = region("exit")
    c = EXIT_GREEN * (0.92 + 0.08 * noise((h, w), 4, 5401))[..., None]

    def art(d, ss):
        d.rectangle([3 * ss, 3 * ss, (w - 4) * ss, (h - 4) * ss], outline=255, width=2 * ss)
        d.text((w * 0.36 * ss, h * 0.5 * ss), "EXIT", font=ImageFont.truetype(SANS_BOLD, int(56 * ss)), fill=255, anchor="mm")
        cx, cy = w * 0.8 * ss, h * 0.5 * ss                            # the arrow, pointing the way out
        d.polygon([(cx - 24 * ss, cy - 7 * ss), (cx + 2 * ss, cy - 7 * ss), (cx + 2 * ss, cy - 20 * ss), (cx + 26 * ss, cy),
                   (cx + 2 * ss, cy + 20 * ss), (cx + 2 * ss, cy + 7 * ss), (cx - 24 * ss, cy + 7 * ss)], fill=255)

    white = drawn(w, h, art)
    c = c * (1 - white[..., None]) + np.array([0.95, 1.0, 0.95]) * white[..., None]
    rgb[s] = c


def exit_side():
    s, w, h = region("exit_side")
    rgb[s] = np.array([0.9, 0.9, 0.86]) * (0.85 + 0.15 * noise((h, w), 2, 5501))[..., None]


def vent_back():
    s, w, h = region("vent_back")
    rgb[s] = np.array([0.05, 0.05, 0.05]) + 0.05 * noise((h, w), 2, 5601)[..., None]


def vent_plate():
    """The little brass plate under the vent, for anyone who has seen too many heist films."""
    s, w, h = region("vent_plate")
    c = BRASS * (0.85 + 0.2 * noise((h, w), 1, 5701))[..., None]

    def engrave(d, ss):
        d.rectangle([2 * ss, 2 * ss, (w - 3) * ss, (h - 3) * ss], outline=255, width=ss)
        d.text((w * ss / 2, h * ss * 0.4), "NOT AN ESCAPE ROUTE", font=ImageFont.truetype(SERIF_BOLD, int(15 * ss)), fill=255, anchor="mm")
        d.text((w * ss / 2, h * ss * 0.76), "We checked.", font=ImageFont.truetype(SERIF_ITAL, int(11 * ss)), fill=255, anchor="mm")

    cut = drawn(w, h, engrave)
    rgb[s] = c * (1 - cut[..., None]) + np.array([0.1, 0.08, 0.05]) * cut[..., None]
    height[s] = -cut * 0.0006


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            filled |= grow


brass()
steel()
opal()
panel()
exit_sign()
exit_side()
vent_back()
vent_plate()
bleed()
Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_fixtures_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 0.002
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_fixtures_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")
MATERIALS = {
    "int_fixtures": 'metallic = 0.5\nroughness = 0.45\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n',
    "int_fixtures_glow": 'emission_enabled = true\nemission_texture = ExtResource("1_albedo")\nemission_energy_multiplier = 2.2\n',
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(
        '[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_fixtures_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_fixtures_normal.png" id="2_normal"]\n\n'
        '[resource]\nalbedo_texture = ExtResource("1_albedo")\n%s' % (RES, RES, extra), encoding="utf8", newline="\n")
print("fixtures art written to", OUT)
