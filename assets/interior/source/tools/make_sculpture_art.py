"""The Sculpture Hall set's one texture (asset item P3.1): the four brass labels, the grime laid over the
statues' marble, Homer's green marble pier, and Icarus's feathers, wax, reed frame and straps. Then a
normal map, their import settings and the materials. Run sculpture_build.py first: this reads the statues'
game meshes and the light baked into their carving.
usage: python make_sculpture_art.py <assets/interior/sculpture folder>

The statues wear assets/plates/statue_marble.tres, the marble players turn into on a plinth. Their grime
is a second, multiplying layer (int_statue_grime.tres): white where the stone is clean, soot in the
crevices, a little dust on top, faint streaks, and fresh white where a chip came off or an arm broke."""
import json
import pathlib
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import int_art as A  # noqa: E402
import int_dims as D  # noqa: E402
import sculpture_figures as S  # noqa: E402
import sculpture_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
BAKES = TOOLS.parent
RES = "res://assets/interior/sculpture/"
N = L.ATLAS
rgb = np.zeros((N, N, 3))
alpha = np.ones((N, N))
height = np.zeros((N, N))
filled = np.zeros((N, N), bool)


def region(name):
    x, y, w, h = L.REGIONS[name]
    filled[y:y + h, x:x + w] = True
    return (slice(y, y + h), slice(x, x + w)), w, h


def noise(shape, sigma, seed):
    n = gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-9)


def drawn(w, h, fn, ss=3):
    img = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(img), ss)
    return np.asarray(img.resize((w, h), Image.BOX), dtype=float) / 255


# --- Brass labels, the same make as the plinths' VACANT label -------------------------------------------

INK = np.array([44, 30, 14]) / 255
LIGHT = np.array([214, 176, 104]) / 255
GEORGIA_B, GEORGIA, GEORGIA_I = "C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/georgiai.ttf"


def label(name, seed):
    title, sub, note, last = L.LABELS[name]
    s, w, h = region("label_" + name)
    rng = np.random.default_rng(seed)
    brass = np.ones((h, w, 3)) * np.array([168, 128, 62]) / 255
    streak = np.cumsum(rng.standard_normal((h, w)) * 7.0, axis=1) * 0.12 / 255
    brass += (streak - streak.mean(axis=1, keepdims=True))[..., None]
    vy, vx = np.mgrid[0:h, 0:w].astype(float)
    edge = ((vx - w / 2) / (w / 2)) ** 2 + ((vy - h / 2) / (h / 2)) ** 2
    brass *= (1 - 0.2 * np.clip(edge - 0.35, 0, 1))[..., None]
    brass *= (0.94 + 0.1 * noise((h, w), 12, seed + 1))[..., None]           # handled, unevenly polished
    k = w / 1024

    def cut(d, ss, dy=0):
        f = ss * k
        d.rectangle([18 * f, (18 + dy) * f, (1024 - 18) * f, (440 - 18 + dy) * f], outline=255, width=max(1, int(4 * f)))
        d.rectangle([28 * f, (28 + dy) * f, (1024 - 28) * f, (440 - 28 + dy) * f], outline=255, width=max(1, int(1.2 * f)))
        for x, y in ((48, 48), (1024 - 48, 48), (48, 440 - 48), (1024 - 48, 440 - 48)):
            d.ellipse([(x - 11) * f, (y - 11 + dy) * f, (x + 11) * f, (y + 11 + dy) * f], outline=255, width=max(1, int(2 * f)))
            d.line([(x - 8) * f, (y - 3 + dy) * f, (x + 8) * f, (y + 3 + dy) * f], fill=255, width=max(1, int(3 * f)))
        lines = [(title, GEORGIA_B, 76, 106), (sub, GEORGIA_I, 44, 184), (note, GEORGIA, 46, 282), (last, GEORGIA_I, 52, 350)]
        for text, font, size, y in lines:
            ft = A.fit_font(d, text, font, int(size * f), int(900 * f))
            d.text((512 * f, (y + dy) * f), text, font=ft, fill=255, anchor="mm")
        d.line([(512 - 170) * f, (226 + dy) * f, (512 + 170) * f, (226 + dy) * f], fill=255, width=max(1, int(2 * f)))

    ink = drawn(w, h, lambda d, ss: cut(d, ss))
    lit = drawn(w, h, lambda d, ss: cut(d, ss, 2))
    c = brass * (1 - lit[..., None]) + LIGHT * lit[..., None]
    c = c * (1 - ink[..., None]) + INK * ink[..., None]
    # Grime collects in the letters and round the screws; a thumb has polished the middle
    c *= (1 - 0.12 * gaussian_filter(ink, 2.0))[..., None]
    rgb[s] = np.clip(c, 0, 1)
    height[s] = -gaussian_filter(ink, 0.6) * 0.0006


# --- The statues' grime -------------------------------------------------------------------------------

def read_glb(path):
    """The statue's own surface from its .glb: positions, normals, atlas UVs and triangles."""
    b = path.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    doc = json.loads(b[20:20 + n])
    blob = b[20 + n + 8:]

    def get(i):
        acc = doc["accessors"][i]
        view = doc["bufferViews"][acc["bufferView"]]
        kind = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[acc["componentType"]]
        width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[acc["type"]]
        start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        return np.frombuffer(blob, kind, acc["count"] * width, start).reshape(acc["count"], width)

    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            if doc["materials"][prim["material"]]["name"] == "statue_marble":
                a = prim["attributes"]
                return get(a["POSITION"]), get(a["NORMAL"]), get(a["TEXCOORD_0"]), get(prim["indices"]).reshape(-1, 3)
    raise ValueError("no statue in " + str(path))


def rasterise(name, lift):
    """Every texel of the statue's region: where on the statue it lies and which way it faces, in statue space."""
    pos, nor, uv, tris = read_glb(OUT / (name + ".glb"))
    pos = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1] - lift], 1)              # back to Blender's axes, off the plinth
    nor = np.stack([nor[:, 0], -nor[:, 2], nor[:, 1]], 1)
    x0, y0, w, h = L.REGIONS[name]
    px = uv * N - np.array([x0, y0])
    P = np.zeros((h, w, 3))
    Nm = np.zeros((h, w, 3))
    hit = np.zeros((h, w), bool)
    for t in tris:
        a, b, c = px[t[0]], px[t[1]], px[t[2]]
        lo = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        hi = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        lo, hi = np.clip(lo, 0, [w - 1, h - 1]), np.clip(hi, 0, [w - 1, h - 1])
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + 0.5, np.arange(lo[1], hi[1] + 1) + 0.5)
        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(det) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / det
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / det
        l3 = 1 - l1 - l2
        inside = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not inside.any():
            continue
        yy, xx = (gy[inside] - 0.5).astype(int), (gx[inside] - 0.5).astype(int)
        wts = np.stack([l1[inside], l2[inside], l3[inside]], 1)
        P[yy, xx] = wts @ pos[t]
        Nm[yy, xx] = wts @ nor[t]
        hit[yy, xx] = True
    Nm /= np.maximum(np.linalg.norm(Nm, axis=-1, keepdims=True), 1e-9)
    return P, Nm, hit


def grime(name, lift, seed):
    s, w, h = region(name)
    P, Nm, hit = rasterise(name, lift)
    ao = np.asarray(Image.open(BAKES / ("sculpture_%s_ao.png" % name)).convert("RGB"), dtype=float) / 255
    tight, wide = ao[..., 0], ao[..., 1]
    flat = P.reshape(-1, 3)
    n3 = lambda f, sd, o=3: S.fbm(flat * np.asarray(f), 1.0, sd, o).reshape(h, w)
    c = np.ones((h, w, 3)) * np.array([0.95, 0.925, 0.875])                  # old marble yellows a little
    c *= (1 + 0.05 * n3((5, 5, 5), seed))[..., None]                          # cloudy
    c *= (0.68 + 0.32 * wide)[..., None]                                      # the broad shadow under every form
    crevice = np.clip((0.95 - tight) / 0.4, 0, 1) ** 0.85
    soot = np.array([0.34, 0.3, 0.255])
    c = c * (1 - 0.75 * crevice[..., None]) + soot * (0.75 * crevice[..., None])
    up = np.clip(Nm[..., 2], 0, 1) ** 3
    c *= (1 - 0.08 * up)[..., None]                                           # dust on everything facing up
    streak = np.clip(n3((26, 26, 1.8), seed + 10, 2) * 2.2 - 0.35, 0, 1) * (1 - up)
    c *= (1 - 0.09 * streak)[..., None]                                        # old runs down the stone
    blot = np.clip(n3((3.5, 3.5, 3.5), seed + 20) * 2 - 0.25, 0, 1)
    c *= (1 - 0.07 * blot[..., None] * np.array([0.6, 0.85, 1.25]))           # warm stains
    base = np.clip((S.SLAB_H + 0.006 - P[..., 2]) / 0.012, 0, 1)
    c *= (1 - base * (0.05 + 0.05 * n3((40, 40, 40), seed + 30, 2)))[..., None]   # the slab is a little dirtier
    fresh = np.zeros((h, w))
    rim = np.zeros((h, w))
    for point, normal, reach, _ in S.BREAKS[name].values():
        nrm = S.unit(normal)
        dist = (P - point) @ nrm
        near = np.linalg.norm(P - point, axis=-1) < reach
        face = (np.abs(dist) < 0.02) & near & (Nm @ nrm > 0.55)
        fresh = np.maximum(fresh, face)
        rim = np.maximum(rim, near & (np.abs(dist) < 0.03) & ~face)
    for centre, r, _ in S.CHIPS[name]:
        d = np.linalg.norm(P - np.asarray(centre), axis=-1)
        fresh = np.maximum(fresh, np.clip((r * 1.2 - d) / (r * 0.3), 0, 1))
        if r >= 0.015:
            rim = np.maximum(rim, (d > r * 1.15) & (d < r * 1.5))
    grain = 0.9 + 0.1 * n3((300, 300, 300), seed + 40, 1)
    c = c * (1 - fresh[..., None]) + (np.array([1.0, 0.99, 0.965]) * grain[..., None]) * fresh[..., None]
    c *= (1 - 0.18 * rim)[..., None]
    rgb[s] = np.where(hit[..., None], np.clip(c, 0, 1), 1.0)
    return s, hit


# --- Homer's pier: verde antico, dark green marble with pale veins ----------------------------------

def pier(seed):
    for k, name in enumerate(("ped_shaft", "ped_top", "ped_base", "ped_cap")):
        s, w, h = region(name)
        u = np.linspace(0, 1, w)[None, :] * (w / 280)
        v = np.linspace(0, 1, h)[:, None] * (h / 280)
        P = np.stack(np.broadcast_arrays(u + k * 3.1, v, np.zeros_like(u * v) + k * 0.7), -1).reshape(-1, 3)
        f = lambda fq, sd, o=4: S.fbm(P * fq, 1.0, sd, o).reshape(h, w)
        ridge = np.abs(f(4, seed) + 0.6 * f(9, seed + 9) * 0.5)
        veins = np.exp(-(ridge / 0.035) ** 2)
        fine = np.exp(-(np.abs(f(14, seed + 20, 3)) / 0.02) ** 2) * 0.5
        clast = np.clip(f(6, seed + 30, 3) * 2.5 - 0.6, 0, 1)                 # the broken pebbles verde antico is made of
        c = np.array([0.055, 0.085, 0.07]) * (0.85 + 0.3 * noise((h, w), 3, seed + 40 + k))[..., None]
        c = c + np.array([0.12, 0.2, 0.15]) * clast[..., None] * 0.6
        c = c * (1 - np.maximum(veins, fine)[..., None]) + np.array([0.62, 0.68, 0.62]) * np.maximum(veins, fine)[..., None]
        chips = noise((h, w), 1.2, seed + 50 + k) > 0.985
        dust = np.clip(noise((h, w), 10, seed + 60 + k) - 0.45, 0, 1)
        c = np.where(chips[..., None], np.array([0.45, 0.5, 0.45]), c) * (1 + 0.35 * dust[..., None])
        if name == "ped_base":
            c *= np.linspace(0.75, 1.0, h)[::-1, None, None] ** 0.5               # scuffed by shoes and mops
        rgb[s] = np.clip(c, 0, 1)
        height[s] = veins * 0.0001 - chips * 0.0008


# --- Icarus's wings -----------------------------------------------------------------------------------

def feathers(kind, k, seed):
    """A feather, tip up: quill, shaft, and two vanes of barbs, split here and there and ragged at the edge."""
    s, w, h = region("%s_%d" % (kind, k))
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    t = 1 - (yy + 0.5) / h                                                    # 0 at the quill, 1 at the tip
    x = (xx + 0.5 - w / 2) / (w / 2)                                          # -1..1 across the cell
    start = 0.14 if kind != "covert" else 0.1
    grow = np.clip((t - start) / 0.25, 0, 1) ** 0.6
    tip = np.sqrt(np.clip(1 - ((t - 0.5) / 0.5) ** 6, 0, 1))
    width = grow * tip * np.interp(t, [0, 0.45, 1], [0.34, 0.94, 0.66])
    outer = 0.38 if kind == "primary" else (0.8 if kind == "secondary" else 1.0)   # flight feathers are lopsided
    edge = np.where(x < 0, width * outer, width) * (1 + 0.06 * noise((h, w), 1.5, seed))
    barb = (t * h * 0.9 + np.abs(x) * w * 0.45) / 2.2
    splits = np.zeros((h, w))
    for _ in range(rng.integers(2, 5)):
        at = rng.uniform(0.25, 0.9)
        side = rng.choice([-1, 1])
        band = np.exp(-((t - at - np.abs(x) * 0.12) / 0.012) ** 2) * (np.sign(x) == side) * (np.abs(x) > rng.uniform(0.1, 0.5))
        splits = np.maximum(splits, band)
    inside = (np.abs(x) < edge) & (splits < 0.5) & (t > start * 0.4)
    shaft = np.exp(-(x / (0.07 * (1 - 0.6 * t))) ** 2) * (t < 0.97)
    quill = (np.abs(x) < 0.07) & (t <= start * 1.2)
    a = (inside | quill | (shaft > 0.5)).astype(float)
    palette = {0: ([0.9, 0.88, 0.82], [0.55, 0.52, 0.48]), 1: ([0.45, 0.32, 0.2], [0.24, 0.16, 0.1]),
               2: ([0.82, 0.8, 0.76], [0.13, 0.1, 0.08])}[k % 3]
    light, dark = np.array(palette[0]), np.array(palette[1])
    mix = np.clip((t - 0.62) / 0.38, 0, 1) ** 1.5                             # darker towards the tip
    if k % 3 == 1:
        mix = np.maximum(mix, (0.5 + 0.5 * np.sin(t * 26 + x * 1.5)) ** 6 * 0.8)   # an eagle's bars
    if k % 3 == 2:
        mix = np.clip((t - 0.78) / 0.15 + noise((h, w), 2, seed + 1) * 0.6 - 0.3, 0, 1)   # scorched at the tip
    c = light * (1 - mix[..., None]) + dark * mix[..., None]
    c *= (0.86 + 0.14 * (0.5 + 0.5 * np.sin(barb * 2.6)))[..., None]
    c *= (1 - 0.25 * np.clip(np.abs(x) / np.maximum(edge, 1e-3) - 0.75, 0, 1))[..., None]
    c = c * (1 - shaft[..., None] * 0.6) + np.array([0.92, 0.9, 0.84]) * shaft[..., None] * 0.6
    c = np.where(quill[..., None], np.array([0.86, 0.8, 0.62]), c)          # the quill, waxed
    rgb[s] = np.clip(c, 0, 1)
    alpha[s] = a
    height[s] = shaft * 0.0012 + 0.0002 * np.sin(barb * 2.6)


def strips(seed):
    s, w, h = region("wood")                                                  # the reed frame, along its length
    g = A.streaks(np.random.default_rng(seed), w, h, 24, axis=1)
    c = np.array([0.5, 0.38, 0.22]) * (1 + 0.12 * g[..., None])
    nodes = np.exp(-((np.linspace(0, 1, w)[None, :] * 5.3 % 1 - 0.5) / 0.03) ** 2)
    c *= (1 - 0.3 * nodes[..., None])
    c *= (0.8 + 0.2 * np.sin(np.linspace(0, np.pi, h))[:, None, None])
    rgb[s] = np.clip(c, 0, 1)
    height[s] = g * 0.0002 - nodes * 0.0008
    s, w, h = region("leather")
    grain = noise((h, w), 0.8, seed + 1)
    c = np.array([0.28, 0.17, 0.1]) * (0.8 + 0.4 * grain[..., None])
    stitch = ((np.arange(w)[None, :] % 8) < 4) & (np.abs(np.arange(h)[:, None] - h / 2) < 1.2)
    c = np.where(stitch[..., None], np.array([0.6, 0.52, 0.4]), c)
    rgb[s] = np.clip(c * (0.7 + 0.3 * np.sin(np.linspace(0, np.pi, h))[:, None, None]), 0, 1)
    height[s] = grain * 0.0003 + stitch * 0.0004
    s, w, h = region("wax")
    lumps = noise((h, w), 3, seed + 2)
    c = np.array([0.74, 0.55, 0.22]) * (0.75 + 0.45 * lumps[..., None])
    soot = noise((h, w), 1.5, seed + 3) > 0.9
    rgb[s] = np.clip(np.where(soot[..., None], c * 0.45, c), 0, 1)
    height[s] = lumps * 0.002
    s, w, h = region("steel")
    rgb[s] = np.array([0.28, 0.28, 0.29]) * (0.9 + 0.2 * noise((h, w), 1, seed + 4)[..., None])


def bleed(mask, steps):
    """Push colour out past each part's edge, so mipmaps never pull in the background."""
    global rgb
    have = mask.copy()
    for _ in range(steps):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(have, step, axis) & ~have
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            have |= grow


for name in L.LABELS:
    label(name, 8100 + list(L.LABELS).index(name) * 10)
for k, name in enumerate(("venus", "discus_thrower", "bust_homer")):
    lift = L.PED_H if name == "bust_homer" else D.PLINTH_H
    s, hit = grime(name, lift, 8200 + k * 50)
    whole = np.zeros((N, N), bool)
    whole[s] = True
    have = np.zeros((N, N), bool)
    have[s] = hit
    keep = rgb.copy()
    bleed(have, 8)
    rgb[~whole] = keep[~whole]                                                # bleed only inside the statue's own cell
pier(8400)
for k in range(3):
    feathers("primary", k, 8500 + k)
    feathers("secondary", k, 8510 + k)
for k in range(6):
    feathers("covert", k, 8520 + k)
strips(8600)
feather_mask = np.zeros((N, N), bool)
for name, (x, y, w, h) in L.REGIONS.items():
    if name.startswith(("primary", "secondary", "covert")):
        cell = np.zeros((N, N), bool)
        cell[y:y + h, x:x + w] = True
        keep = rgb.copy()
        bleed(cell & (alpha > 0.5), 6)
        rgb[~cell] = keep[~cell]
bleed(filled, 4)

img = np.dstack([np.clip(rgb, 0, 1), alpha])
Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(OUT / "int_sculpture_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.6)
px = 0.002
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_sculpture_normal.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")

HEAD = ('[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_sculpture_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_sculpture_normal.png" id="2_normal"]\n\n'
        '[resource]\nalbedo_texture = ExtResource("1_albedo")\n' % (RES, RES))
MATERIALS = {
    "int_sculpture": 'roughness = 0.55\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n',
    "int_sculpture_feathers": ('transparency = 2\nalpha_scissor_threshold = 0.5\ncull_mode = 2\nroughness = 0.85\n'
                               'normal_enabled = true\nnormal_texture = ExtResource("2_normal")\n'
                               'backlight_enabled = true\nbacklight = Color(0.42, 0.38, 0.3, 1)\n'),
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(HEAD + extra, encoding="utf8", newline="\n")
# The grime multiplies whatever the marble already shows, so it needs no light of its own
(OUT / "int_statue_grime.tres").write_text(
    '[gd_resource type="StandardMaterial3D" format=3]\n\n'
    '[ext_resource type="Texture2D" path="%sint_sculpture_albedo.png" id="1_albedo"]\n\n'
    '[resource]\nblend_mode = 3\nshading_mode = 0\ndisable_fog = true\nalbedo_texture = ExtResource("1_albedo")\n' % RES,
    encoding="utf8", newline="\n")
# Each label shows its own stretch of the texture on a plain quad, lit like the plinths' brass
for name in L.LABELS:
    x, y, w, h = L.REGIONS["label_" + name]
    (OUT / ("int_label_%s.tres" % name)).write_text(
        HEAD + 'metallic = 0.45\nroughness = 0.5\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n'
        'emission_enabled = true\nemission_energy_multiplier = 0.4\nemission_texture = ExtResource("1_albedo")\n'
        'uv1_scale = Vector3(%.6f, %.6f, 1)\nuv1_offset = Vector3(%.6f, %.6f, 0)\n' % ((w - 3) / N, (h - 3) / N, (x + 1.5) / N, (y + 1.5) / N),
        encoding="utf8", newline="\n")
print("sculpture art written to", OUT)
