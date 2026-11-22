"""The conservation crates' one texture (asset item P1.1): plywood faces with stencils and shipping
labels, pine battens, the canvas drop cloth and its paper tag, all worn and dirty, plus a normal map,
the import settings and the two materials. Run crates_build.py first: it bakes the shading in the
cloth's folds into the source folder, and this script lays it into the cloth.
usage: python make_crates_art.py <assets/interior/crates folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True    # no __pycache__ next to the scripts
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import crates_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/crates/"
CLOTH_AO = TOOLS.parent / "crates_cloth_ao.png"
N = L.ATLAS
STENCIL = "C:/Windows/Fonts/impact.ttf"
TYPED = "C:/Windows/Fonts/courbd.ttf"
STAMP = "C:/Windows/Fonts/ariblk.ttf"
HAND = "C:/Windows/Fonts/Inkfree.ttf"
INK = np.array([0.11, 0.11, 0.12])
RED = np.array([0.55, 0.13, 0.10])
rng = np.random.default_rng(4111)

colour = np.zeros((N, N, 3))
height = np.zeros((N, N))


def noise(shape, sigma, seed):
    n = gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-9)


def mask_from(draw_fn, w, h, ss=3):
    """Draws black-and-white art at three times the size, then reduces it to a soft 0..1 mask."""
    img = Image.new("L", (w * ss, h * ss), 0)
    draw_fn(ImageDraw.Draw(img), ss, img)
    return np.asarray(img.resize((w, h), Image.BOX), dtype=float) / 255


def fit_text(text, font_path, max_w, max_h, ss):
    size = int(max_h * ss)
    while size > 6:
        font = ImageFont.truetype(font_path, size)
        box = font.getbbox(text)
        if box[2] - box[0] <= max_w * ss and box[3] - box[1] <= max_h * ss:
            return font
        size = int(size * 0.92)
    return ImageFont.truetype(font_path, 6)


def spray(m, seed, fade=0.25):
    """Stencil paint: a soft edge, a little overspray, and patches rubbed thin."""
    soft = gaussian_filter(m, 0.6)
    over = gaussian_filter(m, 2.5) * (noise(m.shape, 0.7, seed) > 0.62) * 0.3
    rubbed = 1 - fade + fade * noise(m.shape, 6, seed + 1)
    worn = np.clip((noise(m.shape, 2.0, seed + 2) - 0.12) * 4, 0, 1)
    return np.clip((soft * worn + over) * rubbed, 0, 1)


def paint(region, ink, alpha, cell):
    x, y, w, h = cell
    a = alpha[..., None]
    region[...] = region * (1 - a) + ink * a


# --- Wood ---------------------------------------------------------------------------------------------
def plywood(w, h, seed, vertical=False):
    shape = (h, w)
    if vertical:
        grain = noise(shape, (18, 0.9), seed)
        figure = noise(shape, (60, 3.0), seed + 1)
    else:
        grain = noise(shape, (0.9, 18), seed)
        figure = noise(shape, (3.0, 60), seed + 1)
    tone = rng.normal(0, 1)
    base = np.array([0.63, 0.54, 0.41]) * (1 + 0.05 * tone)
    c = base * (0.88 + 0.22 * grain[..., None]) * (1 - 0.1 * np.clip((figure[..., None] - 0.6) * 4, 0, 1))
    hgt = grain * 0.00025 + figure * 0.0002
    return c, hgt


def batten_strip(cell):
    x, y, w, h = cell
    grain = noise((h, w), (1.0, 30), 4120)
    knots = np.zeros((h, w))
    for _ in range(9):
        kx, ky = rng.uniform(0, w), rng.uniform(4, h - 4)
        yy, xx = np.mgrid[0:h, 0:w]
        knots = np.maximum(knots, np.exp(-(((xx - kx) / 7) ** 2 + ((yy - ky) / 3.5) ** 2)))
    c = np.array([0.58, 0.46, 0.31]) * (0.85 + 0.25 * grain[..., None]) * (1 - 0.5 * knots[..., None])
    dirt = noise((h, w), 12, 4121)
    c *= (1 - 0.18 * dirt)[..., None]
    colour[y:y + h, x:x + w] = c
    height[y:y + h, x:x + w] = grain * 0.0004 - knots * 0.0003


# --- Marks on the faces -------------------------------------------------------------------------------
def stencil_text(face, cell, text, box, seed, ink=INK, rotate=0, fade=0.25):
    """box is (left, top, width, height) as fractions of the cell."""
    x, y, w, h = cell
    bx, by, bw, bh = int(box[0] * w), int(box[1] * h), max(int(box[2] * w), 4), max(int(box[3] * h), 4)

    def draw(d, ss, img):
        font = fit_text(text, STENCIL, bw, bh, ss)
        d.text((bw * ss / 2, bh * ss / 2), text, font=font, fill=255, anchor="mm")

    m = mask_from(draw, bw, bh)
    # Stencil bridges: thin uncut strips where the stencil held its middles in place
    for cut in rng.uniform(0.1, 0.9, 3 + len(text) // 3):
        cx = int(cut * bw)
        m[:, max(cx - 1, 0):cx + 1] *= 0.15
    if rotate:
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).rotate(rotate, expand=False, resample=Image.BICUBIC), dtype=float) / 255
    a = spray(m, seed, fade)
    region = face[by:by + bh, bx:bx + bw]
    region[...] = region * (1 - a[..., None]) + ink * a[..., None] * 0.95


def arrows(face, cell, box, seed, count=2, ink=INK):
    x, y, w, h = cell
    bx, by, bw, bh = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)

    def draw(d, ss, img):
        for i in range(count):
            cx = (i + 0.5) / count * bw * ss
            aw, ah = bw * ss / count * 0.32, bh * ss
            d.polygon([(cx, 0), (cx + aw, ah * 0.42), (cx + aw * 0.4, ah * 0.42), (cx + aw * 0.4, ah),
                       (cx - aw * 0.4, ah), (cx - aw * 0.4, ah * 0.42), (cx - aw, ah * 0.42)], fill=255)

    a = spray(mask_from(draw, bw, bh), seed)
    region = face[by:by + bh, bx:bx + bw]
    region[...] = region * (1 - a[..., None]) + ink * a[..., None] * 0.95


def paper_label(face, face_h, cell, box, lines, seed, stamp=None, rotate=0.0):
    x, y, w, h = cell
    bx, by, bw, bh = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    paper = np.array([0.86, 0.83, 0.74]) * (0.95 + 0.08 * noise((bh, bw), 5, seed)[..., None])
    edge = np.minimum.reduce([np.arange(bw)[None, :].repeat(bh, 0), np.arange(bw)[::-1][None, :].repeat(bh, 0),
                              np.arange(bh)[:, None].repeat(bw, 1), np.arange(bh)[::-1][:, None].repeat(bw, 1)])
    paper *= (0.82 + 0.18 * np.clip(edge / 4, 0, 1))[..., None]

    def typed(d, ss, img):
        line_h = bh * ss / (len(lines) + 1.2)
        for i, line in enumerate(lines):
            font = fit_text(line, TYPED, bw * 0.88, line_h / ss * 0.8, ss)
            d.text((bw * ss * 0.06, line_h * (i + 0.7)), line, font=font, fill=255, anchor="lm")

    t = gaussian_filter(mask_from(typed, bw, bh), 0.35) * (0.75 + 0.25 * noise((bh, bw), 1.5, seed + 1))
    paper = paper * (1 - t[..., None]) + np.array([0.15, 0.14, 0.18]) * t[..., None]
    if stamp:
        def stamped(d, ss, img):
            font = fit_text(stamp, STAMP, bw * 0.75, bh * 0.3, ss)
            d.text((bw * ss * 0.58, bh * ss * 0.62), stamp, font=font, fill=255, anchor="mm")
            d.rectangle([bw * ss * 0.12, bh * ss * 0.44, bw * ss * 0.98, bh * ss * 0.82], outline=255, width=int(ss * 2))
        s = mask_from(stamped, bw, bh)
        s = np.asarray(Image.fromarray((s * 255).astype(np.uint8)).rotate(-12, resample=Image.BICUBIC), dtype=float) / 255
        s = spray(s, seed + 2, 0.45)
        paper = paper * (1 - s[..., None] * 0.85) + RED * s[..., None] * 0.85
    if rotate:
        img = Image.fromarray(np.clip(paper * 255, 0, 255).astype(np.uint8)).convert("RGBA").rotate(rotate, expand=False, resample=Image.BICUBIC)
        arr = np.asarray(img, dtype=float) / 255
        paper, alpha = arr[..., :3], arr[..., 3]
    else:
        alpha = np.ones((bh, bw))
    region = face[by:by + bh, bx:bx + bw]
    region[...] = region * (1 - alpha[..., None]) + paper * alpha[..., None]
    face_h[by:by + bh, bx:bx + bw] += alpha * 0.0003


def stain_ring(face, cell, at, r, seed):
    x, y, w, h = cell
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - at[0] * w) ** 2 + (yy - at[1] * h) ** 2)
    ring = np.exp(-((d - r) / 2.2) ** 2) * (0.5 + 0.5 * noise((h, w), 3, seed)) + (d < r) * 0.12
    face *= (1 - 0.22 * ring)[..., None]


def wear_face(face, cell, seed, margin):
    """Shade where the battens meet the plywood, then dirt, scuffs and the odd pencil mark."""
    x, y, w, h = cell
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]).astype(float)
    shade = np.clip((edge - margin) / 22, 0, 1)
    face *= (0.72 + 0.28 * shade)[..., None]
    dirt = np.clip((noise((h, w), 16, seed) * 0.7 + noise((h, w), 3, seed + 1) * 0.3 - 0.45) * 2.2, 0, 1)
    low = np.clip((yy / h - 0.55) * 2.2, 0, 1)    # grime gathers low down, where boots and trolleys hit
    face *= (1 - 0.28 * dirt * (0.4 + 0.6 * low))[..., None]
    scuffs = Image.new("L", (w, h), 0)
    pen = ImageDraw.Draw(scuffs)
    for _ in range(int(w * h / 900)):
        sx, sy = rng.uniform(0, w), rng.uniform(h * 0.3, h)
        a = rng.normal(0.3, 0.5)
        ln = rng.uniform(3, 18)
        pen.line([(sx, sy), (sx + np.cos(a) * ln, sy + np.sin(a) * ln)], fill=int(rng.uniform(80, 200)), width=1)
    sc = np.asarray(scuffs, dtype=float) / 255
    face *= (1 - 0.35 * sc)[..., None]


# --- Each crate's faces -------------------------------------------------------------------------------
MARGIN = int(L.BATTEN_W * L.PX_PER_M)    # the battens hide this much of every face's edge


def face(name, seed, vertical=False):
    cell = L.RECTS[name]
    x, y, w, h = cell
    c, hgt = plywood(w, h, seed, vertical)
    return cell, c, hgt


def finish(cell, c, hgt, seed):
    wear_face(c, cell, seed, MARGIN)
    x, y, w, h = cell
    colour[y:y + h, x:x + w] = c
    height[y:y + h, x:x + w] = hgt


def crate_faces():
    m = MARGIN / 1.0
    # Small crate: fragile antiquities
    cell, c, hgt = face("crate_small.front", 4130)
    w, h = cell[2], cell[3]
    inner = lambda fx, fy, fw, fh: (m / w + fx * (1 - 2 * m / w), m / h + fy * (1 - 2 * m / h), fw * (1 - 2 * m / w), fh * (1 - 2 * m / h))
    stencil_text(c, cell, "FRAGILE", inner(0.08, 0.08, 0.84, 0.42), 1)
    stencil_text(c, cell, "ANTIQUITIES - HANDLE WITH CARE", inner(0.1, 0.62, 0.8, 0.16), 2, fade=0.35)
    finish(cell, c, hgt, 4131)

    cell, c, hgt = face("crate_small.side", 4132)
    w, h = cell[2], cell[3]
    arrows(c, cell, inner(0.2, 0.08, 0.6, 0.36), 3)
    stencil_text(c, cell, "No. 0417", inner(0.12, 0.6, 0.76, 0.24), 4)
    finish(cell, c, hgt, 4133)

    cell, c, hgt = face("crate_small.top", 4134)
    w, h = cell[2], cell[3]
    paper_label(c, hgt, cell, inner(0.08, 0.14, 0.5, 0.62), ["MUSEUM CONSERVATION", "GALLERY 3 - SHELF B", "LOT 0417 / 1 OF 3"], 5, rotate=4)
    stain_ring(c, cell, (0.78, 0.55), 15, 6)
    finish(cell, c, hgt, 4135)

    # Cover crate: Pandora, and a gift from the Greeks
    cell, c, hgt = face("crate_cover.front", 4140)
    w, h = cell[2], cell[3]
    stencil_text(c, cell, "DO NOT OPEN", inner(0.06, 0.06, 0.88, 0.2), 7)
    paper_label(c, hgt, cell, inner(0.12, 0.36, 0.76, 0.34), ["CONTENTS: 1 (ONE) JAR", "OWNER: PANDORA", "DO NOT OPEN.", "NOT EVEN A LITTLE."], 8, rotate=-2)
    arrows(c, cell, inner(0.3, 0.78, 0.4, 0.18), 9)
    finish(cell, c, hgt, 4141)

    cell, c, hgt = face("crate_cover.side", 4142)
    w, h = cell[2], cell[3]
    stencil_text(c, cell, "GIFT FROM", inner(0.08, 0.1, 0.84, 0.16), 10)
    stencil_text(c, cell, "THE GREEKS", inner(0.08, 0.28, 0.84, 0.16), 11)
    paper_label(c, hgt, cell, inner(0.14, 0.56, 0.72, 0.3), ["CUSTOMS: TROY", "DECLARED: NOTHING", "INSIDE. HONEST."], 12, stamp="INSPECTED", rotate=3)
    finish(cell, c, hgt, 4143)

    cell, c, hgt = face("crate_cover.top", 4144)
    w, h = cell[2], cell[3]
    arrows(c, cell, inner(0.3, 0.12, 0.4, 0.34), 13)
    stencil_text(c, cell, "THIS SIDE UP", inner(0.12, 0.6, 0.76, 0.18), 14)
    stain_ring(c, cell, (0.24, 0.3), 17, 15)
    finish(cell, c, hgt, 4145)

    # Painting crate: tall and flat
    cell, c, hgt = face("crate_painting.front", 4150, vertical=True)
    w, h = cell[2], cell[3]
    stencil_text(c, cell, "ARTWORK", inner(0.1, 0.06, 0.8, 0.12), 16)
    stencil_text(c, cell, "KEEP UPRIGHT", inner(0.14, 0.2, 0.72, 0.07), 17)
    paper_label(c, hgt, cell, inner(0.16, 0.42, 0.68, 0.2), ["NARCISSUS,", "SELF-PORTRAIT #48", "HANDLE WITH MIRRORS"], 18, rotate=2)
    arrows(c, cell, inner(0.2, 0.72, 0.6, 0.18), 19, count=3)
    finish(cell, c, hgt, 4151)

    cell, c, hgt = face("crate_painting.side", 4152, vertical=True)
    w, h = cell[2], cell[3]
    arrows(c, cell, inner(0.15, 0.06, 0.7, 0.12), 20, count=1)
    stencil_text(c, cell, "UP", inner(0.15, 0.22, 0.7, 0.1), 21)
    finish(cell, c, hgt, 4153)

    cell, c, hgt = face("crate_painting.top", 4154)
    w, h = cell[2], cell[3]
    stencil_text(c, cell, "TOP", inner(0.3, 0.12, 0.4, 0.76), 22)
    finish(cell, c, hgt, 4155)


# --- Drop cloth and its tag ---------------------------------------------------------------------------
def cloth():
    x, y, w, h = L.RECTS["cloth"]
    yy, xx = np.mgrid[0:h, 0:w]
    weave = ((xx // 1 + yy // 1) % 2) * 0.03 + noise((h, w), 0.6, 4160) * 0.06
    base = np.array([0.80, 0.77, 0.70]) * (0.93 + 0.1 * noise((h, w), 25, 4161)[..., None])
    c = base * (0.97 + weave[..., None])
    # Old paint drips and splashes from whatever the decorators did last
    for col in ([0.55, 0.55, 0.56], [0.70, 0.60, 0.38], [0.92, 0.91, 0.88]):
        spots = noise((h, w), 4, int(rng.integers(1e6)))
        a = np.clip((spots - 0.83) * 9, 0, 1) * 0.7
        c = c * (1 - a[..., None]) + np.array(col) * a[..., None]
    dust = np.clip((noise((h, w), 14, 4162) - 0.4) * 2, 0, 1)
    c *= (1 - 0.15 * dust)[..., None]
    if CLOTH_AO.exists():
        ao = np.asarray(Image.open(CLOTH_AO).convert("L").resize((N, N), Image.BOX), dtype=float) / 255
        ao = np.clip(gaussian_filter(ao[y:y + h, x:x + w], 1.2) / 0.75, 0, 1)
        c *= (0.62 + 0.38 * ao)[..., None]      # shade the folds, never so dark they read as holes
    colour[y:y + h, x:x + w] = c
    height[y:y + h, x:x + w] = weave * 0.004 + noise((h, w), 2, 4163) * 0.0003


def tag():
    x, y, w, h = L.RECTS["tag"]
    card = np.array([0.88, 0.85, 0.76]) * (0.95 + 0.07 * noise((h, w), 3, 4170)[..., None])

    def hand(d, ss, img):
        lines = ["MEDUSA (on loan)", "DO NOT UNCOVER.", "Seriously."]
        for i, line in enumerate(lines):
            font = fit_text(line, HAND, w * 0.8, h * 0.22, ss)
            d.text((w * ss * 0.56, h * ss * (0.24 + i * 0.27)), line, font=font, fill=255, anchor="mm")
        d.ellipse([w * ss * 0.04, h * ss * 0.42, w * ss * 0.12, h * ss * 0.58], outline=255, width=ss * 2)

    t = mask_from(hand, w, h)
    card = card * (1 - t[..., None]) + np.array([0.12, 0.14, 0.32]) * t[..., None]
    colour[y:y + h, x:x + w] = card


def bleed():
    """Fill the gaps between cells with the nearest cell's colour, so mipmaps don't pull in black."""
    filled = np.zeros((N, N), bool)
    for name, (x, y, w, h) in L.RECTS.items():
        filled[y:y + h, x:x + w] = True
    for _ in range(L.PAD + 2):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            shifted = np.roll(filled, step, axis)
            grow = shifted & ~filled
            colour[grow] = np.roll(colour, step, axis)[grow]
            height[grow] = np.roll(height, step, axis)[grow]
            filled |= grow


def write():
    batten_strip(L.RECTS["batten"])
    crate_faces()
    cloth()
    tag()
    bleed()
    Image.fromarray(np.clip(colour * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_crates_albedo.png", optimize=True)
    px = 1.0 / L.PX_PER_M
    hgt = gaussian_filter(height, 0.5)
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
    ln = np.sqrt(dx * dx + dy * dy + 1)
    nrm = np.stack([-dx / ln, dy / ln, 1 / ln], -1)
    Image.fromarray(np.clip((nrm * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_crates_normal.png", optimize=True)


IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]


def write_imports():
    for png in sorted(OUT.glob("*.png")):
        target = png.with_suffix(".png.import")
        if not target.exists():
            normal = 1 if png.stem.endswith("_normal") else 0
            target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")


def write_materials():
    for name, rough, extra in (("int_crates", 0.86, ""), ("int_cloth", 0.95, "cull_mode = 2\n")):
        (OUT / (name + ".tres")).write_text(
            '[gd_resource type="StandardMaterial3D" format=3]\n\n'
            '[ext_resource type="Texture2D" path="%sint_crates_albedo.png" id="1_albedo"]\n'
            '[ext_resource type="Texture2D" path="%sint_crates_normal.png" id="2_normal"]\n\n'
            '[resource]\n%salbedo_texture = ExtResource("1_albedo")\nroughness = %.2f\nnormal_enabled = true\n'
            'normal_texture = ExtResource("2_normal")\n' % (RES, RES, extra, rough), encoding="utf8", newline="\n")


write()
write_imports()
write_materials()
print("crate art written to", OUT, "(cloth shading %s)" % ("baked in" if CLOTH_AO.exists() else "not baked yet: run crates_build.py first"))
