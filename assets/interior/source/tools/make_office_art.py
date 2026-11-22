"""The Security Office set's one texture (asset item P3.4): chipped grey-green steel and locker doors,
desk laminate, dark plastic, the librarian's cardigan, a mug and a logbook, and the camera feeds the
screens show: grainy night views of the museum, timestamped, one of them a lot more interesting than
the rest. Writes the texture, a normal map, their import settings and the two materials (the screens
glow, so they get their own).
usage: python make_office_art.py <assets/interior/office folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True    # no __pycache__ next to the scripts
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import office_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/office/"
N = L.ATLAS
MONO = "C:/Windows/Fonts/consolab.ttf"
SANS = "C:/Windows/Fonts/arialbd.ttf"
HAND = "C:/Windows/Fonts/Inkfree.ttf"

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


def chipped_paint(w, h, colour, seed, chips=0.06):
    """Old institutional paint: brushed a little uneven, chipped to bare metal at the edges."""
    c = np.array(colour) * (0.88 + 0.16 * noise((h, w), 6, seed)[..., None])
    edge = np.minimum.reduce([np.arange(w)[None, :].repeat(h, 0), np.arange(w)[::-1][None, :].repeat(h, 0),
                              np.arange(h)[:, None].repeat(w, 1), np.arange(h)[::-1][:, None].repeat(w, 1)]).astype(float)
    chip = (noise((h, w), 1.5, seed + 1) > 1 - chips - 0.25 * np.exp(-edge / 6)).astype(float)
    c = c * (1 - chip[..., None]) + np.array([0.45, 0.45, 0.46]) * chip[..., None]
    grime = np.clip((noise((h, w), 14, seed + 2) - 0.55) * 2.5, 0, 1)
    return c * (1 - 0.2 * grime[..., None]), chip


def steel():
    s, w, h = region("steel")
    c, chip = chipped_paint(w, h, [0.36, 0.42, 0.38], 7101)
    rgb[s] = c
    height[s] = -chip * 0.0003


def doors():
    names = ["GUARD", "GUARD", "L. KEEP OUT"]
    for i, name in enumerate(names):
        s, w, h = region("door_%d" % i)
        c, chip = chipped_paint(w, h, [0.36, 0.42, 0.38], 7110 + i)

        def art(d, ss):
            for k in range(6):                 # the vents near the top
                y = (0.08 + k * 0.035) * h * ss
                d.rectangle([w * ss * 0.25, y, w * ss * 0.75, y + 3 * ss], fill=255)
            d.rectangle([w * ss * 0.2, h * ss * 0.36, w * ss * 0.8, h * ss * 0.44], fill=128)       # the name slot
            d.rectangle([w * ss * 0.78, h * ss * 0.55, w * ss * 0.86, h * ss * 0.68], fill=200)      # the handle

        m = drawn(w, h, art)
        vents = np.clip(m - 0.6, 0, 1) * 2.5
        slot = np.clip(1 - np.abs(m - 0.5) * 10, 0, 1)
        c = c * (1 - vents[..., None] * 0.8)
        label = drawn(w, h, lambda d, ss: d.text((w * ss * 0.5, h * ss * 0.4), name, font=ImageFont.truetype(HAND if i == 2 else SANS, int(h * ss * 0.05)), fill=255, anchor="mm"))
        paper = slot[..., None] * np.array([0.82, 0.80, 0.70])
        c = c * (1 - slot[..., None]) + paper
        c = c * (1 - label[..., None] * 0.85) + np.array([0.12, 0.1, 0.1]) * label[..., None] * 0.85
        if i == 2:                              # her locker has a sticker on it
            st = drawn(w, h, lambda d, ss: d.ellipse([w * ss * 0.3, h * ss * 0.5, w * ss * 0.7, h * ss * 0.6], fill=255))
            word = drawn(w, h, lambda d, ss: d.text((w * ss * 0.5, h * ss * 0.55), "SHH", font=ImageFont.truetype(SANS, int(h * ss * 0.035)), fill=255, anchor="mm"))
            c = c * (1 - st[..., None]) + np.array([0.80, 0.18, 0.15]) * st[..., None]
            c = c * (1 - word[..., None]) + np.array([0.95, 0.92, 0.85]) * word[..., None]
        rgb[s] = c
        height[s] = -vents * 0.002 - chip * 0.0003


def laminate():
    s, w, h = region("laminate")
    c = np.array([0.55, 0.44, 0.32]) * (0.85 + 0.2 * noise((h, w), (1, 30), 7120)[..., None])
    rings = np.clip((noise((h, w), 4, 7121) - 0.7) * 6, 0, 1)    # cup rings, decades of them
    rgb[s] = c * (1 - 0.15 * rings[..., None])


def dark():
    s, w, h = region("dark")
    rgb[s] = np.array([0.09, 0.09, 0.1]) * (0.85 + 0.25 * noise((h, w), 1.5, 7130)[..., None])


def knit():
    s, w, h = region("knit")
    yy, xx = np.mgrid[0:h, 0:w]
    stitch = (np.sin(xx * 1.6 + np.sin(yy * 0.8) * 1.4) * 0.5 + 0.5) * (np.sin(yy * 0.8) * 0.5 + 0.5)
    rgb[s] = np.array([0.36, 0.22, 0.30]) * (0.75 + 0.35 * stitch[..., None])     # the same plum as her own
    height[s] = stitch * 0.0012


def fabric():
    s, w, h = region("fabric")
    rgb[s] = np.array([0.18, 0.2, 0.24]) * (0.8 + 0.3 * noise((h, w), 0.8, 7140)[..., None])


def mug():
    s, w, h = region("mug")
    c = np.ones((h, w, 3)) * 0.88
    m = drawn(w, h, lambda d, ss: [d.text((w * ss / 2, h * ss * y), line, font=ImageFont.truetype(SANS, int(h * ss * 0.13)), fill=255, anchor="mm")
                                   for line, y in (("WORLD'S OKAYEST", 0.38), ("GUARD", 0.62))])
    rgb[s] = c * (1 - m[..., None]) + np.array([0.6, 0.12, 0.1]) * m[..., None]


def logbook():
    s, w, h = region("logbook")
    c = np.array([0.20, 0.25, 0.42]) * (0.85 + 0.2 * noise((h, w), 2, 7150)[..., None])
    m = drawn(w, h, lambda d, ss: d.text((w * ss / 2, h * ss / 2), "NIGHT LOG", font=ImageFont.truetype(SANS, int(h * ss * 0.18)), fill=255, anchor="mm"))
    rgb[s] = c * (1 - m[..., None]) + np.array([0.85, 0.80, 0.6]) * m[..., None]


def keyboard():
    s, w, h = region("keyboard")
    c = np.ones((h, w, 3)) * 0.12
    keys = drawn(w, h, lambda d, ss: [d.rectangle([(x * 10 + 3) * ss, (y * 11 + 3) * ss, (x * 10 + 11) * ss, (y * 11 + 11) * ss], fill=255) for x in range(15) for y in range(4)])
    rgb[s] = c * (1 - keys[..., None]) + np.array([0.82, 0.8, 0.74]) * keys[..., None]


def key_board():
    s, w, h = region("keyboard_board")
    c = np.array([0.55, 0.42, 0.28]) * (0.85 + 0.2 * noise((h, w), 3, 7160)[..., None])

    def art(d, ss):
        for i in range(12):
            x, y = (14 + (i % 6) * 24) * ss, (16 + (i // 6) * 50) * ss
            d.ellipse([x - 2 * ss, y - 2 * ss, x + 2 * ss, y + 2 * ss], fill=255)
            if i not in (4, 9):            # two keys missing. Somebody's in the vault.
                d.polygon([(x - 3 * ss, y + 4 * ss), (x + 3 * ss, y + 4 * ss), (x + 2 * ss, y + 22 * ss), (x - 2 * ss, y + 22 * ss)], fill=200)
        d.text((w * ss / 2, h * ss * 0.93), "KEYS - SIGN OUT", font=ImageFont.truetype(SANS, int(h * ss * 0.08)), fill=255, anchor="mm")

    m = drawn(w, h, art)
    rgb[s] = c * (1 - m[..., None]) + np.array([0.80, 0.70, 0.40]) * m[..., None]


def feed(name, title, scene, seed):
    """A grainy night-camera frame: a room drawn in a few lines, a label and a ticking clock."""
    s, w, h = region(name)
    rng = np.random.default_rng(seed)

    def room(d, ss):
        cx, cy = w * ss * 0.5, h * ss * 0.55
        d.polygon([(0, h * ss), (w * ss, h * ss), (cx + w * ss * 0.18, cy), (cx - w * ss * 0.18, cy)], fill=70)   # floor
        d.rectangle([cx - w * ss * 0.18, cy - h * ss * 0.3, cx + w * ss * 0.18, cy], fill=40)                    # far wall
        if scene == "statues":
            for x in (-0.12, 0.0, 0.12):
                d.polygon([(cx + x * w * ss - 6 * ss, cy + 10 * ss), (cx + x * w * ss + 6 * ss, cy + 10 * ss), (cx + x * w * ss, cy - 14 * ss)], fill=170)
        elif scene == "shelves":
            for k in range(4):
                d.rectangle([w * ss * (0.06 + k * 0.05), h * ss * (0.25 - k * 0.02), w * ss * (0.09 + k * 0.05), h * ss * (0.95 + k * 0.01)], fill=120)
        elif scene == "vault":
            d.rectangle([cx - 8 * ss, cy - 4 * ss, cx + 8 * ss, cy + 8 * ss], fill=150)
            d.rectangle([cx - 5 * ss, cy - 12 * ss, cx + 5 * ss, cy - 4 * ss], fill=255)      # the book, glowing on the stand
        elif scene == "van":
            d.polygon([(cx - 26 * ss, cy + 14 * ss), (cx + 22 * ss, cy + 14 * ss), (cx + 20 * ss, cy - 6 * ss), (cx + 30 * ss, cy - 22 * ss),
                       (cx + 36 * ss, cy - 18 * ss), (cx + 26 * ss, cy - 2 * ss), (cx - 24 * ss, cy - 4 * ss)], fill=150)     # a horse. On wheels.
        elif scene == "steps":
            for k in range(6):
                d.rectangle([0, h * ss * (0.6 + k * 0.07), w * ss, h * ss * (0.62 + k * 0.07)], fill=110)
        elif scene == "nothing":
            pass

    m = drawn(w, h, room)
    grain = rng.random((h, w)) * 0.28
    lines = (np.sin(np.arange(h) * 1.7) * 0.5 + 0.5)[:, None] * 0.08
    base = 0.08 + m * 0.6 + grain - lines
    if scene == "nothing":
        base = 0.2 + rng.random((h, w)) * 0.7                       # NO SIGNAL
    tint = np.array([0.70, 0.95, 0.80])
    c = np.clip(base, 0, 1)[..., None] * tint
    label = drawn(w, h, lambda d, ss: (d.text((4 * ss, 4 * ss), title, font=ImageFont.truetype(MONO, int(11 * ss)), fill=255),
                                       d.text((4 * ss, (h - 14) * ss), "03:14:%02d" % (seed % 60), font=ImageFont.truetype(MONO, int(10 * ss)), fill=255)))
    c = np.maximum(c, label[..., None] * np.array([0.95, 1.0, 0.95]))
    rgb[s] = c


def log_screen():
    s, w, h = region("desk_log")
    c = np.zeros((h, w, 3)) + np.array([0.02, 0.06, 0.03])
    lines = ["SECURITY LOG", "DAY 2,071:", "BOOK STILL", "OVERDUE.", "SHE KNOWS."]
    m = drawn(w, h, lambda d, ss: [d.text((6 * ss, (8 + i * 21) * ss), line, font=ImageFont.truetype(MONO, int(15 * ss)), fill=255) for i, line in enumerate(lines)])
    rgb[s] = c + m[..., None] * np.array([0.45, 1.0, 0.55])


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            filled |= grow


steel()
doors()
laminate()
dark()
knit()
fabric()
mug()
logbook()
keyboard()
key_board()
for name, title, scene, seed in (("cam1", "CAM 1 FRONT STEPS", "steps", 7201), ("cam2", "CAM 2 SCULPTURE", "statues", 7202),
                                 ("cam3", "CAM 3 ARCHIVES", "shelves", 7203), ("cam4", "CAM 4 VAULT", "vault", 7204),
                                 ("cam5", "CAM 5 CURB", "van", 7205), ("cam6", "CAM 6", "nothing", 7206), ("desk_feed", "CAM 4 VAULT", "vault", 7207)):
    feed(name, title, scene, seed)
log_screen()
bleed()
Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_office_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 0.004
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_office_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")
MATERIALS = {
    "int_office": 'roughness = 0.62\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n',
    "int_screens": 'roughness = 0.15\nemission_enabled = true\nemission_texture = ExtResource("1_albedo")\nemission_energy_multiplier = 1.6\n',
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(
        '[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_office_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_office_normal.png" id="2_normal"]\n\n'
        '[resource]\nalbedo_texture = ExtResource("1_albedo")\n%s' % (RES, RES, extra), encoding="utf8", newline="\n")
print("office art written to", OUT)
