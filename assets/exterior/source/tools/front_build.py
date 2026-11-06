"""Background Blender job: game meshes for the finished three-arch pavilion. Godot coordinates
throughout: x along the avenue, y up, z towards the street.
usage: blender -b --factory-startup --python front_build.py -- <out dir> <ornament dir>"""
import importlib, json, math, pathlib, sys
import bmesh
import bpy
import numpy as np

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import ext_dims as D
importlib.reload(D)

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(argv[0])
ORN = pathlib.Path(argv[1])
OUT.mkdir(parents=True, exist_ok=True)
TAU = 2 * math.pi
rng = np.random.default_rng(7)
LAYOUT = json.load(open(HERE / "relief_layout.json"))

CAP_H = 1.92
CAP_Y = D.COL_TOP_Y - CAP_H
BASE_H = 0.82
ZF = 10.75            # frieze face over the wall
ZB = 13.28            # frieze face over the columns
W_BREAK = D.PED_W / 2 + 0.05
ROWS = dict(egg=(0.00, 0.25), bead=(0.25, 0.375), leaf=(0.375, 0.70))
METRES_PER_U = 1.2
MATS = ["ext_shaft", "ext_ashlar", "ext_stone", "ext_granite", "ext_riser", "ext_rough", "ext_trim", "ext_bronze", "ext_glass", "ext_paving",
        "ext_carved", "ext_relief", "ext_door", "ext_banner", "ext_lantern", "ext_rail"]


class Part:
    """One material's geometry, as Godot-space points; rotated to Blender on the way out."""

    def __init__(self):
        self.v, self.f, self.uv = [], [], []

    def add(self, verts, faces, uvs=None):
        base = len(self.v)
        self.v += [(float(x), -float(z), float(y)) for x, y, z in verts]
        uvs = uvs if uvs is not None else [(0.0, 0.0)] * len(verts)
        self.uv += [(float(a), float(b)) for a, b in uvs]
        for f in faces:
            self.f.append([int(i) + base for i in f])


parts = {m: Part() for m in MATS}


def grid(mat, rows, closed_u=False, uvs=None, flip=False):
    """Quads between rows of points, rows being (nv, nu, 3). Open sheets keep their written direction."""
    rows = np.asarray(rows, dtype=np.float64)
    nv, nu = rows.shape[:2]
    f = []
    for j in range(nv - 1):
        for i in range(nu - 1 + int(closed_u)):
            a = j * nu + i
            b = j * nu + (i + 1) % nu
            c = (j + 1) * nu + (i + 1) % nu
            d = (j + 1) * nu + i
            f.append((d, c, b, a) if flip else (a, b, c, d))
    parts[mat].add(rows.reshape(-1, 3), f, None if uvs is None else np.asarray(uvs).reshape(-1, 2))


def box(mat, x0, x1, y0, y1, z0, z1, skip=()):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    faces = {"w": (0, 1, 3, 2), "e": (4, 6, 7, 5), "d": (0, 4, 5, 1), "u": (2, 3, 7, 6), "n": (0, 2, 6, 4), "s": (1, 5, 7, 3)}
    parts[mat].add(v, [q for k, q in faces.items() if k not in skip])


def bevel_box(mat, x0, x1, y0, y1, z0, z1, b):
    """A block with cut corners. Cut stone never has knife edges, and the bevels catch the light."""
    xs, ys, zs = (x0, x0 + b, x1 - b, x1), (y0, y0 + b, y1 - b, y1), (z0, z0 + b, z1 - b, z1)
    pts, idx = [], {}

    def p(i, j, k):
        if (i, j, k) not in idx:
            idx[(i, j, k)] = len(pts)
            pts.append((xs[i], ys[j], zs[k]))
        return idx[(i, j, k)]

    f = [(p(0, 1, 2), p(0, 2, 2), p(0, 2, 1), p(0, 1, 1)), (p(3, 1, 1), p(3, 2, 1), p(3, 2, 2), p(3, 1, 2)),
         (p(2, 0, 1), p(2, 0, 2), p(1, 0, 2), p(1, 0, 1)), (p(2, 3, 2), p(2, 3, 1), p(1, 3, 1), p(1, 3, 2)),
         (p(1, 2, 0), p(2, 2, 0), p(2, 1, 0), p(1, 1, 0)), (p(2, 2, 3), p(1, 2, 3), p(1, 1, 3), p(2, 1, 3))]
    for j, jo, ji in ((0, 0, 1), (2, 3, 2)):
        f.append((p(1, ji, 0), p(2, ji, 0), p(2, jo, 1), p(1, jo, 1)))
        f.append((p(2, ji, 3), p(1, ji, 3), p(1, jo, 2), p(2, jo, 2)))
        f.append((p(0, ji, 2), p(1, jo, 2), p(1, jo, 1), p(0, ji, 1)))
        f.append((p(3, ji, 1), p(2, jo, 1), p(2, jo, 2), p(3, ji, 2)))
    f.append((p(1, 1, 0), p(1, 2, 0), p(0, 2, 1), p(0, 1, 1)))
    f.append((p(2, 2, 0), p(2, 1, 0), p(3, 1, 1), p(3, 2, 1)))
    f.append((p(1, 2, 3), p(1, 1, 3), p(0, 1, 2), p(0, 2, 2)))
    f.append((p(2, 1, 3), p(2, 2, 3), p(3, 2, 2), p(3, 1, 2)))
    parts[mat].add(pts, f)


def lathe(mat, x, z, rings, segs=48):
    """Round shape from (y, radius) rings."""
    a = np.linspace(0, TAU, segs, endpoint=False)
    grid(mat, [[(x + r * math.cos(t), y, z + r * math.sin(t)) for t in a] for y, r in rings], closed_u=True, flip=True)


def band_uv(row, count, s):
    f0, f1 = ROWS[row]
    return [[(si / METRES_PER_U, 1.0 - (f0 + (f1 - f0) * j / (count - 1))) for si in s] for j in range(count)]


def sweep(mat, path, profile, closed=False, bands=()):
    """A moulding run along a plan path: path is (x, z), profile is (out, y), and out is measured
    to the path's outer side. Corners are mitred; bands name profile spans that carry the carved strip."""
    p = np.asarray(path, dtype=np.float64)
    n = len(p)
    seg = np.roll(p, -1, 0) - p if closed else np.diff(p, axis=0)
    seg /= np.linalg.norm(seg, axis=1, keepdims=True)
    nor = np.stack([-seg[:, 1], seg[:, 0]], -1)
    miter = np.zeros_like(p)
    for i in range(n):
        a = nor[i - 1] if closed else nor[max(i - 1, 0)]
        b = nor[i] if closed else nor[min(i, len(nor) - 1)]
        miter[i] = (a + b) / (1 + a @ b)
    rows = [[(p[i, 0] + miter[i, 0] * o, y, p[i, 1] + miter[i, 1] * o) for i in range(n)] for o, y in profile]
    if not bands:
        grid(mat, rows, closed_u=closed)
        return
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    start = 0
    for i0, i1, row in sorted(bands):
        if i0 > start:
            grid(mat, rows[start:i0 + 1], closed_u=closed)
        sub = rows[i0:i1 + 1]
        grid("ext_trim", sub, closed_u=closed, uvs=band_uv(row, len(sub), s)[::-1])
        start = i1
    if start < len(rows) - 1:
        grid(mat, rows[start:], closed_u=closed)


def cell_uv(rect):
    """UVs for a quad given in order bottom left, bottom right, top right, top left, from an atlas
    cell given in image pixels, top-left origin."""
    x0, y0, x1, y1 = rect
    s = 2048.0
    return [(x0 / s, 1 - y1 / s), (x1 / s, 1 - y1 / s), (x1 / s, 1 - y0 / s), (x0 / s, 1 - y0 / s)]


# --- Columns -----------------------------------------------------------------------------------
def shaft(x, z):
    flutes = 24
    y0 = D.PED_Y + BASE_H
    y1 = CAP_Y - 0.06
    h = y1 - y0
    us = np.array([-1.0, -0.74, -0.62, -0.38, -0.13, 0.13, 0.38, 0.62])
    head = 0.17
    t_rows = sorted({0.0, 0.03, 0.07, 0.12, 0.18, 0.5, 2.0, 5.0, 8.0, h - 0.4, h - 0.2, h - 0.12, h - 0.07, h - 0.03, h})
    rows = []
    for t in t_rows:
        s = t / h
        R = D.COL_R - (D.COL_R - D.COL_R_TOP) * max(0.0, (s - 0.33) / 0.67) ** 1.5
        if t < head:
            e = math.sqrt(max(1 - ((head - t) / head) ** 2, 0.0))
        elif t > h - head:
            e = math.sqrt(max(1 - ((t - (h - head)) / head) ** 2, 0.0))
        else:
            e = 1.0
        width = 0.74 * e
        ring = []
        for k in range(flutes):
            for u in us:
                a = TAU * (k + (u + 1) / 2) / flutes
                dd = 0.0
                if abs(u) < width and e > 0:
                    dd = 0.046 * e * math.sqrt(max(1 - (u / width) ** 2, 0.0))
                ring.append((x + (R - dd) * math.cos(a), y0 + t, z + (R - dd) * math.sin(a)))
        rows.append(ring)
    grid("ext_shaft", rows, closed_u=True, flip=True)


def base(x, z):
    y = D.PED_Y
    prof = [(0, 1.12), (0.05, 1.19), (0.13, 1.22), (0.22, 1.19), (0.27, 1.12), (0.29, 1.09), (0.31, 1.07), (0.36, 1.02), (0.42, 1.0),
            (0.47, 1.0), (0.50, 1.04), (0.54, 1.075), (0.58, 1.06), (0.61, 1.02), (0.625, 0.93), (0.64, 0.925), (0.69, 0.885), (0.76, 0.84),
            (BASE_H, D.COL_R + 0.015), (BASE_H + 0.02, D.COL_R)]
    lathe("ext_shaft", x, z, [(y + a, r) for a, r in prof], 64)


def pedestal(px):
    w = D.PED_W / 2
    z0, z1 = D.PED_Z
    cap = [(0.0, D.PED_Y - 0.62), (0.05, D.PED_Y - 0.56), (0.12, D.PED_Y - 0.48), (0.20, D.PED_Y - 0.42), (0.20, D.PED_Y - 0.34), (0.28, D.PED_Y - 0.26),
           (0.32, D.PED_Y - 0.20), (0.32, D.PED_Y - 0.06), (0.26, D.PED_Y), (-w, D.PED_Y)]
    foot = [(-0.02, 0.0), (0.26, 0.0), (0.26, 0.34), (0.20, 0.40), (0.16, 0.46), (0.06, 0.54), (0.0, 0.62)]
    path = [(px - w, z0), (px - w, z1), (px + w, z1), (px + w, z0)]
    sweep("ext_stone", path, foot)
    sweep("ext_stone", path, cap, bands=[(3, 6, "egg")])
    box("ext_ashlar", px - w, px + w, 0.62, D.PED_Y - 0.62, z0, z1, skip=("d", "u", "n"))


def pilaster(x):
    w = 0.72
    z = D.WALL_Z
    y0, y1 = D.PED_Y, CAP_Y - 0.06
    us = np.linspace(-w, w, 41)
    prof = []
    for u in us:
        t = (u + w) / (2 * w) * 5
        ph = t % 1.0
        dd = 0.035 * math.sin(math.pi * min(max((ph - 0.14) / 0.72, 0), 1)) if 0.04 < t < 4.96 else 0.0
        prof.append((x + u, z + 0.30 - dd))
    prof = [(x - w, z)] + prof + [(x + w, z)]
    grid("ext_shaft", [[(a, y, b) for a, b in prof] for y in (y0 + 0.8, y1)])
    box("ext_stone", x - w - 0.14, x + w + 0.14, y0, y0 + 0.3, z, z + 0.46)
    box("ext_stone", x - w - 0.08, x + w + 0.08, y0 + 0.3, y0 + 0.8, z, z + 0.38)


# --- Walls, arches and niches ------------------------------------------------------------------
def ray_rect(cx, cy, ang, x0, x1, y1):
    dx, dy = math.cos(ang), math.sin(ang)
    ts = []
    if dx > 1e-9:
        ts.append((x1 - cx) / dx)
    if dx < -1e-9:
        ts.append((x0 - cx) / dx)
    if dy > 1e-9:
        ts.append((y1 - cy) / dy)
    t = min(ts)
    return cx + t * dx, cy + t * dy


def arch_wall(x0, x1, y0, y1, zf, zb, cx, half, ys, n=40, mat="ext_ashlar"):
    """A wall panel with a round-headed opening through it."""
    angs = sorted({math.pi * i / n for i in range(n + 1)} | {math.atan2(y1 - ys, x1 - cx), math.atan2(y1 - ys, x0 - cx)})
    inner = [(cx + half, y0)] + [(cx + half * math.cos(a), ys + half * math.sin(a)) for a in angs] + [(cx - half, y0)]
    outer = [(x1, y0)] + [ray_rect(cx, ys, a, x0, x1, y1) for a in angs] + [(x0, y0)]
    m = len(inner)
    v = [(x, y, zf) for x, y in inner] + [(x, y, zf) for x, y in outer] + [(x, y, zb) for x, y in inner]
    f = []
    for i in range(m - 1):
        f.append((i, i + m, i + 1 + m, i + 1))
        f.append((i, i + 1, i + 1 + 2 * m, i + 2 * m))
    parts[mat].add(v, f)


def arch_band(cx, ys, prof, bands, n=48):
    angs = np.linspace(0, math.pi, n + 1)
    rows = [[(cx + r * math.cos(a), ys + r * math.sin(a), z) for a in angs] for r, z in prof]
    start = 0
    for i0, i1, row in sorted(bands):
        if i0 > start:
            grid("ext_stone", rows[start:i0 + 1], flip=True)
        s = angs * (prof[i0][0] + prof[i1][0]) / 2
        grid("ext_trim", rows[i0:i1 + 1], uvs=band_uv(row, i1 - i0 + 1, s), flip=True)
        start = i1
    if start < len(rows) - 1:
        grid("ext_stone", rows[start:], flip=True)


def arch(cx):
    half = D.ARCH_W / 2
    ys = D.ARCH_SPRING_Y
    prof = [(half - 0.01, D.WALL_Z), (half + 0.02, D.WALL_Z + 0.10), (half + 0.06, D.WALL_Z + 0.14), (half + 0.32, D.WALL_Z + 0.14), (half + 0.35, D.WALL_Z + 0.17),
            (half + 0.39, D.WALL_Z + 0.26), (half + 0.64, D.WALL_Z + 0.26), (half + 0.68, D.WALL_Z + 0.30), (half + 0.76, D.WALL_Z + 0.37), (half + 0.82, D.WALL_Z + 0.37),
            (half + 0.86, D.WALL_Z + 0.25), (half + 0.88, D.WALL_Z)]
    arch_band(cx, ys, prof, [(1, 3, "bead"), (7, 9, "egg")])
    for sx in (-1, 1):
        o = [(cx + sx * r, z) for r, z in prof]
        rows = [[(x, y, z) for x, z in o] for y in (0.0, ys)]
        grid("ext_stone", rows if sx > 0 else [r[::-1] for r in rows])
        xa, xb = sorted((cx + sx * (half - 0.05), cx + sx * (half + 0.92)))
        box("ext_stone", xa, xb, ys - 0.22, ys + 0.02, D.WALL_Z, D.WALL_Z + 0.44)
        box("ext_stone", xa - 0.03, xb + 0.03, ys - 0.34, ys - 0.22, D.WALL_Z, D.WALL_Z + 0.36)
        box("ext_stone", xa - 0.06, xb + 0.06, ys + 0.02, ys + 0.12, D.WALL_Z, D.WALL_Z + 0.50)
    place("ext_carved", KEY, lambda q: (q[0] + cx, q[1] + D.ARCH_CROWN_Y + 0.10, q[2] + D.WALL_Z), flip=False)


def arch_infill(cx, tag):
    half = D.ARCH_W / 2
    ys = D.ARCH_SPRING_Y
    z = D.DOOR_Z
    transom = D.TRANSOM_Y
    box("ext_ashlar", cx - half, cx + half, 6.0, transom - 0.75, z - 0.2, z + 0.05, skip=("d", "u", "n"))
    box("ext_ashlar", cx - half, cx - D.DOOR_W / 2 - 0.3, 0, 6.0, z - 0.2, z + 0.05, skip=("d", "u", "n"))
    box("ext_ashlar", cx + D.DOOR_W / 2 + 0.3, cx + half, 0, 6.0, z - 0.2, z + 0.05, skip=("d", "u", "n"))
    for dy0, dy1, dz in ((-0.75, -0.42, 0.20), (-0.42, -0.30, 0.34), (-0.30, -0.12, 0.42), (-0.12, 0.0, 0.34)):
        box("ext_stone", cx - half, cx + half, transom + dy0, transom + dy1, z, z + dz)
    # Door lintel and a frame of small columns, the way the real doorways are built
    box("ext_stone", cx - 2.75, cx + 2.75, 3.9, 4.5, z, z + 0.44)
    box("ext_stone", cx - 2.95, cx + 2.95, 4.5, 4.72, z, z + 0.62)
    box("ext_stone", cx - 2.75, cx + 2.75, 4.72, 5.9, z, z + 0.16)
    box("ext_stone", cx - 2.95, cx + 2.95, 5.9, 6.1, z, z + 0.40)
    for sx in (-1, 1):
        for dx in (1.85, 2.45):
            lathe("ext_stone", cx + sx * dx, z + 0.30, [(0.0, 0.27), (0.22, 0.27), (0.30, 0.21), (3.5, 0.18), (3.62, 0.22), (3.9, 0.25)], 16)
    bronze_doors(cx, z - 0.05)
    # Mullions dividing the window into three lights
    for sx in (-1, 1):
        x = cx + sx * 1.18
        box("ext_stone", x - 0.24, x + 0.24, transom, D.ARCH_CROWN_Y - 0.5, z, z + 0.32)
        box("ext_stone", x - 0.31, x + 0.31, ys + 1.15, ys + 1.42, z, z + 0.42)
    lattice(cx, transom, ys, half, z + 0.10)
    banner(cx, tag)


def stud(x, y, z, r, h, n=8):
    """A domed bronze boss standing out from a door."""
    a = [TAU * i / n for i in range(n)]
    v = [(x + r * math.cos(q), y + r * math.sin(q), z) for q in a]
    v += [(x + r * 0.72 * math.cos(q), y + r * 0.72 * math.sin(q), z + h * 0.7) for q in a]
    v.append((x, y, z + h))
    f = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [(n + i, n + (i + 1) % n, 2 * n) for i in range(n)]
    parts["ext_bronze"].add(v, f)


def ring_pull(x, y, z):
    stud(x, y + 0.09, z, 0.075, 0.06)
    a = np.linspace(-math.pi / 2, 1.5 * math.pi, 17)
    tube([(x + 0.085 * math.cos(q), y + 0.085 * math.sin(q), z + 0.075) for q in a], 0.018, 6, ref=(0.0, 0.0, 1.0))


LEAVES = ({m: Part() for m in MATS}, {m: Part() for m in MATS})


def bronze_doors(cx, z):
    """A pair of bronze doors in eight panels: the story of the Book, read top left to bottom right.
    The centre pair are built apart from the rest, so they can swing on their hinges."""
    global parts
    w, h = D.DOOR_W / 2, D.DOOR_H
    main = parts
    if cx != 0:
        box("ext_bronze", cx - w - 0.1, cx + w + 0.1, 0, h + 0.1, z - 0.05, z)
    panels = LAYOUT["door_panels"]
    pw, ph = (w - 0.20) / 2 * 2, (h - 0.5) / 4
    for leaf, sx in enumerate((-1, 1)):
        if cx == 0:
            parts = LEAVES[leaf]
            a, b = sorted((0.0, sx * (w + 0.1)))
            box("ext_bronze", a, b, 0.0, h + 0.1, z - 0.05, z)
            box("ext_bronze", a, b, 0.0, 0.09, z, z + 0.08)
        x0 = cx - w + 0.08 if sx < 0 else cx + 0.06
        for row in range(4):
            y1 = h - 0.14 - row * (ph + 0.06)
            y0 = y1 - ph
            x1 = x0 + w - 0.14
            v = [(x0, y0, z + 0.02), (x1, y0, z + 0.02), (x1, y1, z + 0.02), (x0, y1, z + 0.02)]
            parts["ext_door"].add(v, [(0, 1, 2, 3)], cell_uv(panels[leaf * 4 + row]))
            # raised bronze frame round each panel
            box("ext_bronze", x0 - 0.05, x1 + 0.05, y0 - 0.05, y0, z, z + 0.05)
            box("ext_bronze", x0 - 0.05, x1 + 0.05, y1, y1 + 0.05, z, z + 0.05)
            box("ext_bronze", x0 - 0.05, x0, y0, y1, z, z + 0.05)
            box("ext_bronze", x1, x1 + 0.05, y0, y1, z, z + 0.05)
            for xs in (x0 - 0.025, x1 + 0.025):
                for ys in (y0 - 0.025, y1 + 0.025):
                    stud(xs, ys, z + 0.05, 0.03, 0.03)
        ring_pull(cx + sx * 0.27, 0.945, z + 0.05)
        if cx == 0 and sx > 0:
            box("ext_bronze", -0.04, 0.04, 0, h - 0.02, z, z + 0.075)
    parts = main
    # The meeting stile where the leaves close, and the sill
    if cx != 0:
        box("ext_bronze", cx - 0.04, cx + 0.04, 0, h - 0.02, z, z + 0.075)
        box("ext_bronze", cx - w - 0.1, cx + w + 0.1, 0, 0.09, z, z + 0.08)
    else:
        door_passage()


def door_passage():
    """The short stone passage from the doors into the building."""
    x, top, z0, z1 = 1.8, 3.9, 5.6, D.DOOR_Z - 0.2
    box("ext_paving", -x, x, -0.5, 0.0, 6.0, z1, skip=("w", "e", "d", "n", "s"))
    box("ext_ashlar", -x - 0.6, -x, 0.0, top, z0, z1, skip=("w", "d", "u", "n", "s"))
    box("ext_ashlar", x, x + 0.6, 0.0, top, z0, z1, skip=("e", "d", "u", "n", "s"))
    box("ext_stone", -x, x, top, top + 0.5, z0, z1, skip=("w", "e", "u", "n", "s"))


def banner(cx, tag):
    """A great cloth hanging in the arch. It is a fine grid, so the wind can move it in the shader."""
    x0, x1 = cx - 3.25, cx + 3.25
    y1, y0 = D.TRANSOM_Y - 0.95, 6.35
    z = D.DOOR_Z + 0.42
    nx, ny = 14, 16
    rows, uvs = [], []
    u0, u1 = LAYOUT["banners"][tag]
    for j in range(ny + 1):
        t = j / ny
        row, ur = [], []
        for i in range(nx + 1):
            s = i / nx
            row.append((x0 + (x1 - x0) * s, y1 + (y0 - y1) * t, z + 0.05 * math.sin(s * 19 + t * 2) * (0.3 + t)))
            ur.append((u0 + (u1 - u0) * s, t))
        rows.append(row)
        uvs.append(ur)
    uv = [[(a, 1 - b) for a, b in r] for r in uvs]
    grid("ext_banner", rows[::-1], uvs=uv[::-1])
    tube([(x0 - 0.2, y1 + 0.03, z), (x1 + 0.2, y1 + 0.03, z)], 0.045)


def lattice(cx, y0, ys, half, z):
    """The dark star-pattern grille of the real windows, as thin bronze bars over dim glass."""
    pts = [(cx + half - 0.02, y0)] + [(cx + half * 0.995 * math.cos(a), ys + half * 0.995 * math.sin(a)) for a in np.linspace(0, math.pi, 32)] + [(cx - half + 0.02, y0)]
    v = [(x, y, z - 0.03) for x, y in pts]
    parts["ext_glass"].add(v, [tuple(range(len(v)))])
    pitch, t, d = 1.06, 0.035, 0.05

    def inside(x, y):
        rx = x - cx
        return y >= y0 and (y <= ys or rx * rx + (y - ys) ** 2 < (half - 0.02) ** 2) and abs(rx) < half

    def bar(a, b):
        steps = 10
        run = [(a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps) for i in range(steps + 1)]
        run = [p for p in run if inside(*p)]
        if len(run) < 2:
            return
        p0, p1 = np.array(run[0]), np.array(run[-1])
        dv = p1 - p0
        ln = np.linalg.norm(dv)
        if ln < 0.01:
            return
        n = np.array([-dv[1], dv[0]]) / ln * t
        quad = [p0 + n, p1 + n, p1 - n, p0 - n]
        verts = [(q[0], q[1], z) for q in quad] + [(q[0], q[1], z + d) for q in quad]
        parts["ext_bronze"].add(verts, [(7, 6, 5, 4), (4, 5, 1, 0), (6, 7, 3, 2), (5, 6, 2, 1), (7, 4, 0, 3)])

    nx = int(half / pitch) + 2
    ny = int((D.ARCH_CROWN_Y - y0) / pitch) + 2
    for i in range(-nx, nx + 1):
        for j in range(ny):
            x, y = cx + i * pitch, y0 + j * pitch
            h = pitch / 2
            bar((x - h, y), (x + h, y))
            bar((x, y - h), (x, y + h))
            bar((x - h, y - h), (x + h, y + h))
            bar((x - h, y + h), (x + h, y - h))
            # a small bronze boss at each crossing
            if inside(x, y):
                box("ext_bronze", x - 0.07, x + 0.07, y - 0.07, y + 0.07, z, z + 0.07, skip=("n",))


def niche(x, y0, spring, half, zf, depth_scale, sign):
    """A tall round-headed niche with a scallop-shell head and an empty plinth."""
    n = 18
    a = np.linspace(0, math.pi, n + 1)
    # Curved back wall
    grid("ext_ashlar", [[(x + half * math.cos(t), y, zf - depth_scale * half * math.sin(t)) for t in a] for y in (y0, spring)], flip=True)
    # Half dome, its ribs fanning out from a shell at the foot of the head
    rows = []
    for k in range(7):
        e = k / 6 * math.pi / 2
        ring = []
        for j, t in enumerate(a):
            rib = 1.0 - 0.07 * abs(math.sin(t * 9)) * math.sin(e * 2 + 0.3)
            r = half * rib
            ring.append((x + r * math.cos(t) * math.cos(e), spring + r * math.sin(e) * 1.02, zf - depth_scale * r * math.sin(t) * math.cos(e)))
        rows.append(ring)
    grid("ext_stone", rows, flip=True)
    box("ext_stone", x - half, x + half, y0 - 0.01, y0 + 0.02, zf - depth_scale * half, zf + 0.02, skip=("w", "e", "d", "n", "s"))
    # Empty plinth, with its small bronze notice
    pw = half * 0.72
    bevel_box("ext_stone", x - pw, x + pw, y0, y0 + 0.62, zf - depth_scale * half * 0.8, zf + 0.06, 0.03)
    sx0, sx1, sy0, sy1 = x - 0.52, x + 0.52, y0 + 0.20, y0 + 0.44
    v = [(sx0, sy0, zf + 0.075), (sx1, sy0, zf + 0.075), (sx1, sy1, zf + 0.075), (sx0, sy1, zf + 0.075)]
    parts["ext_door"].add(v, [(0, 1, 2, 3)], cell_uv(LAYOUT["sign"]))
    # Surround on the wall
    prof = [(half - 0.01, zf), (half + 0.03, zf + 0.09), (half + 0.2, zf + 0.09), (half + 0.23, zf)]
    ang = np.linspace(0, math.pi, 25)
    grid("ext_stone", [[(x + r * math.cos(t), spring + r * math.sin(t), z) for t in ang] for r, z in prof], flip=True)
    for sx in (-1, 1):
        o = [(x + sx * r, z) for r, z in prof]
        rows2 = [[(q[0], y, q[1]) for q in o] for y in (y0, spring)]
        grid("ext_stone", rows2 if sx > 0 else [r[::-1] for r in rows2])


def walls():
    half = D.ARCH_W / 2
    ys = D.ARCH_SPRING_Y
    arch_wall(-7.0, 7.0, 0.0, D.COL_TOP_Y, D.WALL_Z, D.DOOR_Z, 0.0, half, ys)
    for sx in (-1, 1):
        # Bay wall with the arch, then the niche between the outer columns, then the strip to the end bay
        a0, a1 = sorted((sx * 7.0, sx * 19.8))
        arch_wall(a0, a1, 0.0, D.COL_TOP_Y, D.WALL_Z, D.DOOR_Z, sx * 14.0, half, ys)
        n0, n1 = sorted((sx * 19.8, sx * 22.2))
        y0, spring = 3.75, 9.6
        arch_wall(n0, n1, y0, D.COL_TOP_Y, D.WALL_Z, D.WALL_Z - 0.01, sx * 21.0, 0.68, spring, n=20)
        box("ext_ashlar", n0, n1, 0.0, y0, D.WALL_Z - 0.2, D.WALL_Z, skip=("w", "e", "d", "n"))
        niche(sx * 21.0, y0, spring, 0.68, D.WALL_Z, 1.0, sx)
        s0, s1 = sorted((sx * 22.2, sx * D.END_BAY_X))
        box("ext_ashlar", s0, s1, 0.0, D.COL_TOP_Y, D.WALL_Z - 0.2, D.WALL_Z, skip=("w", "e", "d", "u", "n"))
        end_bay(sx)


def banded(x0, x1, y0, y1, z, axis="x"):
    """Horizontal channels cut across a face, the banded stonework of the real end bays."""
    pitch = 0.92
    n = int((y1 - y0) / pitch)
    rows = []
    for i in range(n):
        y = y0 + i * pitch
        for dy, dz in ((0.0, -0.075), (0.05, -0.075), (0.09, 0.0), (pitch - 0.04, 0.0), (pitch, -0.05)):
            rows.append((y + dy, dz))
    rows.append((y1, 0.0))
    if axis == "x":
        grid("ext_stone", [[(x, y, z + dz) for x in (x0, x1)] for y, dz in rows])
    else:
        grid("ext_stone", [[(z + dz, y, x) for x in (x1, x0)] for y, dz in rows])


def end_bay(sx):
    """The banded corner of the pavilion, with a second tall niche."""
    x_in, x_out = D.END_BAY_X, D.PAV_X
    zf = D.WALL_Z + 0.55
    cx = (x_in + x_out) / 2
    half = 0.95
    y0, spring = 1.9, 12.0
    strips = [(x_in, cx - half - 0.3), (cx + half + 0.3, x_out)]
    for a, b in strips:
        s0, s1 = sorted((sx * a, sx * b))
        banded(s0, s1, 0.0, D.COL_TOP_Y, zf)
    s0, s1 = sorted((sx * (cx - half - 0.3), sx * (cx + half + 0.3)))
    banded(s0, s1, 0.0, y0, zf)
    arch_wall(s0, s1, y0, D.COL_TOP_Y, zf, zf - 0.02, sx * cx, half, spring, n=24, mat="ext_stone")
    niche(sx * cx, y0, spring, half, zf, 0.62, sx)
    # Inner return of the bay against the wall, and the outer side of the pavilion
    a, b = sorted((sx * x_in, sx * x_in))
    v = [(sx * x_in, 0, D.WALL_Z), (sx * x_in, D.COL_TOP_Y, D.WALL_Z), (sx * x_in, D.COL_TOP_Y, zf), (sx * x_in, 0, zf)]
    parts["ext_stone"].add(v, [(0, 1, 2, 3) if sx > 0 else (3, 2, 1, 0)])
    if sx > 0:
        banded(5.8, zf, 0.0, D.COL_TOP_Y, x_out, "z")
    else:
        rows_z = [5.8, zf]
        pitch = 0.92
        rows = []
        y = 0.0
        while y + pitch < D.COL_TOP_Y:
            for dy, dz in ((0.0, 0.075), (0.05, 0.075), (0.09, 0.0), (pitch - 0.04, 0.0), (pitch, 0.05)):
                rows.append((y + dy, dz))
            y += pitch
        grid("ext_stone", [[(-x_out + dz, yy, z) for z in rows_z] for yy, dz in rows])


# --- Entablature, attic and blocks -------------------------------------------------------------
def plan_path():
    w = W_BREAK
    p = [(-D.PAV_X - 0.02, 7.0), (-D.PAV_X - 0.02, ZF)]
    p = [(-D.PAV_X + 0.8, 7.0), (-D.PAV_X + 0.8, ZF)]
    for px in D.PAIRS_X:
        p += [(px - w, ZF), (px - w, ZB), (px + w, ZB), (px + w, ZF)]
    p += [(D.PAV_X - 0.8, ZF), (D.PAV_X - 0.8, 7.0)]
    return p


def entablature():
    y = D.COL_TOP_Y
    path = plan_path()
    prof = [(-1.2, y), (-0.16, y), (-0.16, y + 0.31), (-0.13, y + 0.34), (-0.09, y + 0.37), (-0.09, y + 0.69), (-0.06, y + 0.72), (-0.03, y + 0.75),
            (-0.03, y + 1.03), (0.02, y + 1.06), (0.12, y + 1.13), (0.16, y + 1.20), (0.16, y + 1.27), (0.02, y + 1.30),
            (0.02, y + 2.22), (0.06, y + 2.25), (0.10, y + 2.30), (0.10, y + 2.36),
            (0.20, y + 2.36), (0.20, y + 2.66), (0.27, y + 2.70), (0.40, y + 2.83), (0.46, y + 2.86), (0.46, y + 3.12),
            (1.46, y + 3.12), (1.46, y + 3.16), (1.52, y + 3.16), (1.52, y + 3.48), (1.58, y + 3.52), (1.66, y + 3.56), (1.72, y + 3.66), (1.82, y + 3.80), (1.90, y + 3.84), (1.92, y + 3.90), (0.6, y + 3.90)]
    sweep("ext_stone", path, prof, bands=[(8, 11, "egg"), (14, 17, "bead"), (19, 22, "egg"), (28, 33, "leaf")])
    for px in D.PAIRS_X:
        box("ext_stone", px - W_BREAK + 0.17, px + W_BREAK - 0.17, y - 0.002, y, 9.9, ZB - 1.0, skip=("w", "e", "u", "n", "s"))
    # Close the main run's underside over the end bays
    for sx in (-1, 1):
        a, b = sorted((sx * D.END_BAY_X, sx * (D.PAV_X - 0.8)))
        box("ext_stone", a, b, y - 0.002, y, 7.0, 9.7, skip=("w", "e", "u", "n", "s"))
    dentils(path)
    modillions(path)
    soffit_panels(path)
    inscriptions()


def on_path(path, pitch, margin):
    for a, b in zip(path[:-1], path[1:]):
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        d = b - a
        ln = float(np.linalg.norm(d))
        if ln < 0.1:
            continue
        d /= ln
        nor = np.array([-d[1], d[0]])
        n = int((ln - 2 * margin) / pitch)
        off = (ln - n * pitch) / 2
        for i in range(n + 1):
            yield a + d * (off + i * pitch), d, nor


def oriented_box(mat, p, d, nor, along, o0, o1, y0, y1):
    def pt(s, o, y):
        q = p + d * s + nor * o
        return (q[0], y, q[1])

    v = [pt(-along, o0, y0), pt(along, o0, y0), pt(along, o1, y0), pt(-along, o1, y0),
         pt(-along, o0, y1), pt(along, o0, y1), pt(along, o1, y1), pt(-along, o1, y1)]
    parts[mat].add(v, [(0, 1, 2, 3), (2, 6, 7, 3), (3, 7, 4, 0), (5, 6, 2, 1)])


def dentils(path):
    y0 = D.COL_TOP_Y + 2.38
    for p, d, nor in on_path(path, 0.30, 0.15):
        oriented_box("ext_stone", p, d, nor, 0.085, 0.19, 0.33, y0, y0 + 0.27)


def load_game(tag, u0, v0, size):
    z = np.load(ORN / f"{tag}_game.npz")
    return z["verts"], z["tris"], z["uvs"] * size + np.array([u0, v0], dtype=np.float32)


BRACKET = load_game("modillion", 0.0, 0.75, 0.25)
KEY = load_game("keystone", 0.25, 0.75, 0.25)
MASK = load_game("mask_athena", 0.5, 0.75, 0.25)
SHUSH = load_game("mask_shush", 0.75, 0.75, 0.25)


def place(mat, piece, fn, flip):
    v, tris, uvs = piece
    world = [fn(q) for q in v]
    pts, faces, tuv = [], [], []
    for i, (a, b, c) in enumerate(tris):
        k = len(pts)
        pts += [world[a], world[b], world[c]]
        tuv += list(uvs[i])
        faces.append((k, k + 2, k + 1) if flip else (k, k + 1, k + 2))
    parts[mat].add(pts, faces, tuv)


def modillions(path):
    y1 = D.COL_TOP_Y + 3.12
    for p, d, nor in on_path(path, 1.06, 0.40):
        def fn(q, p=p, d=d, nor=nor):
            w = p + d * q[0] + nor * (0.46 + q[1])
            return (w[0], y1 + q[2], w[1])
        place("ext_carved", BRACKET, fn, flip=True)


def soffit_panels(path):
    y = D.COL_TOP_Y + 3.095
    for p, d, nor in on_path(path, 1.06, 0.40):
        c = p + d * 0.53
        a, o0, o1 = 0.30, 0.52, 1.36

        def pt(s, o):
            q = c + d * s + nor * o
            return (q[0], y, q[1])

        parts["ext_trim"].add([pt(-a, o0), pt(a, o0), pt(a, o1), pt(-a, o1)], [(0, 1, 2, 3)], [(0.0, 0.0), (1 / 3, 0.0), (1 / 3, 0.3), (0.0, 0.3)])


def inscriptions():
    """The name and two lines of warning, cut into the frieze, where a person on the ground can read them."""
    y0 = D.COL_TOP_Y + 1.46
    y1 = y0 + 0.56
    z = ZF + 0.05
    for key, cx, half in (("name", 0.0, 4.25), ("touch", -14.0, 3.75), ("know", 14.0, 3.75)):
        v = [(cx - half, y0, z), (cx + half, y0, z), (cx + half, y1, z), (cx - half, y1, z)]
        parts["ext_relief"].add(v, [(0, 1, 2, 3)], cell_uv(LAYOUT["inscriptions"][key]))


def attic():
    y0, y1 = D.ENT_TOP_Y, D.ATTIC_TOP_Y
    z = D.WALL_Z - 0.4
    X = D.PAV_X - 0.9
    box("ext_ashlar", -X, X, y0, y1 - 0.5, -4.0, z, skip=("d", "u", "n"))
    box("ext_stone", -X, X, y0, y0 + 0.5, z, z + 0.24, skip=("w", "e", "d", "n"))
    prof = [(0.0, y1 - 0.62), (0.06, y1 - 0.56), (0.16, y1 - 0.46), (0.30, y1 - 0.34), (0.42, y1 - 0.28), (0.44, y1 - 0.12), (0.52, y1 - 0.06), (0.56, y1), (-0.6, y1)]
    sweep("ext_stone", [(-X, -4.0), (-X, z), (X, z), (X, -4.0)], prof)
    box("ext_paving", -X, X, y1 - 0.01, y1, -4.0, z, skip=("w", "e", "d", "n", "s"))
    # Body of the great hall behind the attic, closing the block
    box("ext_stone", -D.PAV_X + 0.2, D.PAV_X - 0.2, 0.0, y0, -4.0, 7.2, skip=("d", "u", "n", "s"))
    # The crest along the roofline: Athena's helmeted masks, with one librarian among them
    xs = []
    spans = [(-X + 0.4, -24.9), (-17.1, -10.9), (-3.1, 3.1), (10.9, 17.1), (24.9, X - 0.4)]
    for a, b in spans:
        n = max(int((b - a) / 2.3), 1)
        xs += [a + (b - a) * (i + 0.5) / n for i in range(n)]
    for i, x in enumerate(xs):
        piece = SHUSH if i == 5 else MASK
        place("ext_carved", piece, lambda q, x=x: (q[0] * 1.5 + x, q[1] * 1.5 + y1, q[2] * 1.5 + z - 0.34), flip=False)
    return xs


def stacked_blocks(px):
    """The great unfinished blocks above each column pair: courses of rough stone, stepping in."""
    tiers = [(D.ENT_TOP_Y, 3.75, 3.0), (D.ENT_TOP_Y + 1.15, 3.55, 2.8), (D.ENT_TOP_Y + 2.3, 3.2, 2.5), (D.ENT_TOP_Y + 3.35, 2.75, 2.1), (D.ENT_TOP_Y + 4.3, 2.2, 1.6)]
    zc = D.COL_Z - 0.55
    for y0, hw, hd in tiers:
        h = 1.13 if y0 < D.ENT_TOP_Y + 3 else 1.0
        if y0 + h > D.BLOCK_TOP_Y + 0.2:
            h = D.BLOCK_TOP_Y + 0.2 - y0
        n = max(int(2 * hw / 1.7), 2)
        for i in range(n):
            x0 = px - hw + i * 2 * hw / n
            x1 = x0 + 2 * hw / n
            jit = rng.uniform(-0.05, 0.05, 3)
            bevel_box("ext_rough", x0 + 0.012, x1 - 0.012, y0, y0 + h, zc - hd + jit[0] * 0.5, zc + hd + jit[1], 0.05 + abs(jit[2]) * 0.6)


def medallions():
    """Six round portraits in the spandrels, each in a beaded ring with its name around it."""
    r = 0.62
    keys = ["homer", "achilles", "helen", "horse", "library", "guard"]
    centres = []
    for cx in D.ARCHES_X:
        centres += [(cx - 3.62, 17.92), (cx + 3.62, 17.92)]
    for (x, y), key in zip(centres, keys):
        n = 40
        a = np.linspace(0, TAU, n, endpoint=False)
        z = D.WALL_Z
        prof = [(r + 0.05, 0.0), (r + 0.05, 0.10), (r, 0.14)]
        grid("ext_stone", [[(x + rr * math.cos(t), y + rr * math.sin(t), z + dz) for t in a] for rr, dz in prof], closed_u=True)
        x0, y0, x1, y1 = LAYOUT["medallions"][key]
        cu, cv = (x0 + x1) / 2 / 2048, 1 - (y0 + y1) / 2 / 2048
        ru = (x1 - x0) / 2 / 2048
        verts = [(x, y, z + 0.14)] + [(x + r * math.cos(t), y + r * math.sin(t), z + 0.14) for t in a]
        uvs = [(cu, cv)] + [(cu + ru * math.cos(t), cv + ru * math.sin(t)) for t in a]
        faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
        parts["ext_relief"].add(verts, faces, uvs)


# --- Stairs, terrace and base ------------------------------------------------------------------
def stairs():
    run = (D.STAIR_Z_BOT - D.STAIR_Z_TOP) / D.STAIR_STEPS
    rise = (D.TERRACE_Y - D.PLAZA_Y) / D.STAIR_STEPS
    xs = np.linspace(-D.STAIR_X, D.STAIR_X, 41)

    def dip(x):
        return 0.028 * math.exp(-(x / 7.5) ** 2)

    for i in range(D.STAIR_STEPS):
        y = D.TERRACE_Y - i * rise
        z0 = D.STAIR_Z_TOP + i * run
        z1 = z0 + run
        wob = rng.uniform(-0.2, 0.2)
        nos, under = 0.022, 0.035
        back = z0 - under if i else z0
        tread = [(back, y, 0.8), (z0 + run * 0.55, y, 1.0), (z1 - nos, y, 1.0), (z1, y - nos, 1.0)]
        riser = [(z1, y - nos, 1.0), (z1, y - 0.05, 0.95), (z1 - under, y - 0.065, 0.9), (z1 - under, y - rise, 0.8)]
        grid("ext_granite", [[(float(x), yy - dip(x - wob) * k, zz) for x in xs] for zz, yy, k in tread], flip=True)
        grid("ext_riser", [[(float(x), yy - dip(x - wob) * k, zz) for x in xs] for zz, yy, k in riser], flip=True)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * D.STAIR_X, sx * (D.STAIR_X + D.CHEEK_W)))
        v = [(x0, D.PLAZA_Y, D.STAIR_Z_TOP), (x0, D.CHEEK_H, D.STAIR_Z_TOP), (x0, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_BOT), (x0, D.PLAZA_Y, D.STAIR_Z_BOT),
             (x1, D.PLAZA_Y, D.STAIR_Z_TOP), (x1, D.CHEEK_H, D.STAIR_Z_TOP), (x1, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_BOT), (x1, D.PLAZA_Y, D.STAIR_Z_BOT)]
        parts["ext_ashlar"].add(v, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6)])
    for x in (-7.5, 7.5):
        z0, z1 = D.STAIR_Z_TOP - 0.2, D.STAIR_Z_BOT + 0.25
        h = 0.92

        def yy(z):
            return D.TERRACE_Y - (min(max(z, D.STAIR_Z_TOP), D.STAIR_Z_BOT) - D.STAIR_Z_TOP) / (D.STAIR_Z_BOT - D.STAIR_Z_TOP) * 4.5

        tube([(x, yy(z) + h, z) for z in (z0, D.STAIR_Z_TOP + 0.05, D.STAIR_Z_BOT - 0.05, z1)], 0.03, mat="ext_rail")
        for i in range(5):
            z = D.STAIR_Z_TOP + 0.4 + i * 2.2
            tube([(x, yy(z) - 0.01, z), (x, yy(z) + h, z)], 0.018, mat="ext_rail")


def tube(path, r, n=8, mat="ext_bronze", ref=None):
    """A round bar along a path. Give ref, a direction the path never runs along, for any path that
    turns through a right angle, or the cross section collapses there."""
    path = np.asarray(path, dtype=np.float64)
    a = np.linspace(0, TAU, n, endpoint=False)
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    if ref is None:
        ref = np.array([1.0, 0.0, 0.0]) if abs(tang[0, 0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    ref = np.asarray(ref, dtype=np.float64)
    rows = []
    for p, t in zip(path, tang):
        s = np.cross(t, ref)
        s /= np.linalg.norm(s)
        u = np.cross(s, t)
        rows.append([tuple(p + r * (s * math.cos(q) + u * math.sin(q))) for q in a])
    grid(mat, rows, closed_u=True, flip=True)


def terrace_and_base():
    """Stone terrace from the doors to the stairs, on the heavy base wall that lifts the whole front."""
    Z = D.TERRACE_Z_FRONT
    box("ext_paving", -D.PAV_X, D.PAV_X, D.TERRACE_Y - 0.5, D.TERRACE_Y, D.DOOR_Z - 0.1, Z, skip=("w", "e", "d", "n", "s"))
    prof = [(0.82, D.PLAZA_Y), (0.82, -4.06), (0.70, -3.96), (0.46, -3.90), (0.30, -3.86), (0.30, -0.78), (0.46, -0.72), (0.58, -0.62), (0.58, -0.52), (0.70, -0.42), (0.74, -0.30), (0.74, -0.08), (0.66, 0.0), (0.0, 0.0)]
    for sx in (-1, 1):
        path = [(sx * (D.STAIR_X + D.CHEEK_W), Z), (sx * D.PAV_X, Z), (sx * D.PAV_X, 7.0)]
        if sx < 0:
            path = path[::-1]
        # the profile runs along the outer side of the path
        sweep("ext_stone", path, prof, bands=[(7, 9, "egg")] if False else ())
        railing(sx)
    # The base's big plain face is coursed stone
    for sx in (-1, 1):
        a, b = sorted((sx * (D.STAIR_X + D.CHEEK_W), sx * (D.PAV_X + 0.4)))
        box("ext_ashlar", a, b, -3.86, -0.78, Z + 0.4, Z + 0.405, skip=("w", "e", "d", "u", "n"))
        z0, z1 = 7.0, Z + 0.4
        x = sx * (D.PAV_X + 0.4)
        if sx > 0:
            box("ext_ashlar", x, x + 0.005, -3.86, -0.78, z0, z1, skip=("w", "d", "u", "n", "s"))
        else:
            box("ext_ashlar", x - 0.005, x, -3.86, -0.78, z0, z1, skip=("e", "d", "u", "n", "s"))


def railing(sx):
    """Bronze railings along the terraces, in lattice panels like the real ones."""
    Z = D.TERRACE_Z_FRONT - 0.28
    x0, x1 = D.STAIR_X + D.CHEEK_W + 0.1, D.PAV_X - 0.25
    n = int((x1 - x0) / 1.9)
    pw = (x1 - x0) / n
    h = 1.08
    for i in range(n + 1):
        x = sx * (x0 + i * pw)
        box("ext_bronze", x - 0.04, x + 0.04, 0.0, h + 0.1, Z - 0.04, Z + 0.04)
        lathe("ext_bronze", x, Z, [(h + 0.1, 0.05), (h + 0.16, 0.075), (h + 0.22, 0.03)], 8)
    a, b = sorted((sx * x0, sx * x1))
    box("ext_bronze", a, b, h, h + 0.06, Z - 0.03, Z + 0.03)
    box("ext_bronze", a, b, 0.12, 0.16, Z - 0.02, Z + 0.02)
    for i in range(n):
        xa, xb = sx * (x0 + i * pw), sx * (x0 + (i + 1) * pw)
        for p, q in (((xa, 0.16), (xb, h)), ((xa, h), (xb, 0.16))):
            tube([(p[0], p[1], Z), (q[0], q[1], Z)], 0.013, 6)
        cx, cy = (xa + xb) / 2, (0.16 + h) / 2
        a2 = np.linspace(0, TAU, 12)
        tube([(cx + 0.14 * math.cos(t), cy + 0.14 * math.sin(t), Z) for t in a2], 0.012, 5)


def lanterns():
    """Bronze lanterns on the inner pedestals, flanking the main doors: a visible home for the warm door light."""
    for sx in (-1, 1):
        x = sx * 3.82
        y0 = 1.85
        z = 12.2
        # A swan neck out from the pedestal, so the lantern hangs clear in the passage
        tube([(sx * 4.42, y0 + 0.62, z), (sx * 4.32, y0 + 0.86, z), (sx * 4.16, y0 + 1.16, z), (sx * 3.98, y0 + 1.36, z), (x, y0 + 1.34, z), (x, y0 + 1.2, z)], 0.03, 7)
        tube([(sx * 4.42, y0 + 1.1, z), (sx * 4.26, y0 + 1.08, z), (sx * 4.2, y0 + 1.05, z)], 0.016, 6)
        box("ext_bronze", min(sx * 4.46, sx * 4.40), max(sx * 4.46, sx * 4.40), y0 + 0.5, y0 + 1.22, z - 0.09, z + 0.09)
        lathe("ext_bronze", x, z, [(y0 - 0.05, 0.06), (y0, 0.14), (y0 + 0.05, 0.2), (y0 + 0.1, 0.19)], 8)
        lathe("ext_lantern", x, z, [(y0 + 0.1, 0.13), (y0 + 0.45, 0.2), (y0 + 0.82, 0.24)], 6)
        lathe("ext_bronze", x, z, [(y0 + 0.82, 0.27), (y0 + 0.9, 0.29), (y0 + 1.06, 0.14), (y0 + 1.16, 0.05), (y0 + 1.22, 0.02)], 6)
        for i in range(6):
            a = TAU * i / 6
            tube([(x + 0.14 * math.cos(a), y0 + 0.1, z + 0.14 * math.sin(a)), (x + 0.25 * math.cos(a), y0 + 0.82, z + 0.25 * math.sin(a))], 0.012, 5)


def build_all():
    for px in D.PAIRS_X:
        pedestal(px)
        for sx in (-1, 1):
            shaft(px + sx * D.PAIR_GAP, D.COL_Z)
            base(px + sx * D.PAIR_GAP, D.COL_Z)
            pilaster(px + sx * D.PAIR_GAP)
        stacked_blocks(px)
    walls()
    for cx, tag in zip(D.ARCHES_X, ("achilles", "book", "helen")):
        arch(cx)
        arch_infill(cx, tag)
    medallions()
    entablature()
    attic()
    stairs()
    terrace_and_base()
    lanterns()


def export(sections, filename):
    """Each section's parts become separate meshes, so a section out of view can be culled whole."""
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    total, objs = 0, []
    for section, name, part in [(s, n, q) for s, group in sections.items() for n, q in group.items()]:
        if not part.f:
            continue
        me = bpy.data.meshes.new(section + "_" + name)
        me.from_pydata(part.v, [], part.f)
        me.update()
        layer = me.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", np.array([part.uv[i] for f in part.f for i in f], dtype=np.float32).ravel())
        bm = bmesh.new()
        bm.from_mesh(me)
        if name not in ("ext_trim", "ext_carved", "ext_relief", "ext_door", "ext_banner"):
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0004)
        bm.faces.ensure_lookup_table()
        seen = set()
        for start in bm.faces:
            if start.index in seen:
                continue
            island, stack = [], [start]
            seen.add(start.index)
            closed = True
            while stack:
                f = stack.pop()
                island.append(f)
                for e in f.edges:
                    if len(e.link_faces) != 2:
                        closed = False
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index)
                            stack.append(g)
            if closed:
                bmesh.ops.recalc_face_normals(bm, faces=island)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(bpy.data.materials.get(name) or bpy.data.materials.new(name))
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(38))
        ob = bpy.data.objects.new(me.name, me)
        scene.collection.objects.link(ob)
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        total += tris
        print("PART", section, name, tris, flush=True)
        objs.append(ob)
    print("FRONT_TRIS", total, flush=True)
    for ob in scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{filename}.glb"), export_format="GLB", use_selection=True, export_yup=True,
                              export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT", export_tangents=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{filename}.blend"), compress=True)


if __name__ == "__main__":
    build_all()
    export({"Front": parts}, "front")
    export({"DoorL": LEAVES[0], "DoorR": LEAVES[1]}, "doors")
    print("DONE", flush=True)
