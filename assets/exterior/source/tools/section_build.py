"""Background Blender job: game meshes for the style test bay. Godot coordinates throughout:
+x east, +y up, +z south. usage: blender -b --factory-startup --python section_build.py -- <out dir>"""
import importlib, math, pathlib, sys, time
import bmesh
import bpy
import numpy as np

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import ext_dims as D
importlib.reload(D)

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(argv[0])
OUT.mkdir(parents=True, exist_ok=True)
TAU = 2 * math.pi
rng = np.random.default_rng(7)

CAP_H = 1.92
CAP_Y = D.COL_TOP_Y - CAP_H
BASE_H = 0.82
ZF = 10.75            # frieze face over the wall
ZB = 13.28            # frieze face over the columns
W_BREAK = D.PED_W / 2 + 0.05
SPAN_X = 14.0         # how far the finished entablature and attic run each side


class Part:
    """One material's geometry, as Godot-space points; flipped to Blender on the way out."""

    def __init__(self):
        self.v, self.f, self.uv = [], [], []

    def add(self, verts, faces, uvs=None):
        base = len(self.v)
        self.v += [(float(x), -float(z), float(y)) for x, y, z in verts]
        uvs = uvs if uvs is not None else [(0.0, 0.0)] * len(verts)
        self.uv += [(float(a), float(b)) for a, b in uvs]
        for f in faces:
            self.f.append([int(i) + base for i in f])


MATS = ["ext_shaft", "ext_ashlar", "ext_stone", "ext_granite", "ext_rough", "ext_trim", "ext_bronze", "ext_glass", "ext_paving", "ext_carved", "ext_riser"]
parts = {m: Part() for m in MATS}


def grid(mat, rows, closed_u=False, closed_v=False, uvs=None, flip=False):
    """Quads between rows of points. rows has shape (nv, nu, 3). Open sheets keep the direction they
    are written with, so a sheet that faces the wrong way passes flip."""
    rows = np.asarray(rows, dtype=np.float64)
    nv, nu = rows.shape[:2]
    f = []
    for j in range(nv - 1 + int(closed_v)):
        for i in range(nu - 1 + int(closed_u)):
            a = j * nu + i
            b = j * nu + (i + 1) % nu
            c = ((j + 1) % nv) * nu + (i + 1) % nu
            d = ((j + 1) % nv) * nu + i
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

    faces = []
    # six main faces
    faces += [(p(0, 1, 1), p(0, 2, 1), p(0, 2, 2), p(0, 1, 2)), (p(3, 1, 2), p(3, 2, 2), p(3, 2, 1), p(3, 1, 1)),
              (p(1, 0, 1), p(1, 0, 2), p(2, 0, 2), p(2, 0, 1)), (p(1, 3, 2), p(1, 3, 1), p(2, 3, 1), p(2, 3, 2)),
              (p(1, 1, 0), p(2, 1, 0), p(2, 2, 0), p(1, 2, 0)), (p(2, 1, 3), p(1, 1, 3), p(1, 2, 3), p(2, 2, 3))]
    # twelve edge bevels
    for j in (0, 2):
        j2 = j + 1
        faces.append((p(1, 0 if j == 0 else 3, 1), p(2, 0 if j == 0 else 3, 1), p(2, 1 if j == 0 else 2, 0), p(1, 1 if j == 0 else 2, 0)))
        faces.append((p(2, 0 if j == 0 else 3, 2), p(1, 0 if j == 0 else 3, 2), p(1, 1 if j == 0 else 2, 3), p(2, 1 if j == 0 else 2, 3)))
        faces.append((p(0, 1 if j == 0 else 2, 1), p(1, 0 if j == 0 else 3, 1), p(1, 0 if j == 0 else 3, 2), p(0, 1 if j == 0 else 2, 2)))
        faces.append((p(3, 1 if j == 0 else 2, 2), p(2, 0 if j == 0 else 3, 2), p(2, 0 if j == 0 else 3, 1), p(3, 1 if j == 0 else 2, 1)))
    faces.append((p(0, 1, 1), p(0, 2, 1), p(1, 2, 0), p(1, 1, 0)))
    faces.append((p(3, 2, 1), p(3, 1, 1), p(2, 1, 0), p(2, 2, 0)))
    faces.append((p(0, 2, 2), p(0, 1, 2), p(1, 1, 3), p(1, 2, 3)))
    faces.append((p(3, 1, 2), p(3, 2, 2), p(2, 2, 3), p(2, 1, 3)))
    # eight corner triangles
    for a, b2, c in ((0, 0, 0), (3, 0, 0), (0, 3, 0), (3, 3, 0), (0, 0, 3), (3, 0, 3), (0, 3, 3), (3, 3, 3)):
        i2, j2, k2 = (1 if a == 0 else 2), (1 if b2 == 0 else 2), (1 if c == 0 else 2)
        faces.append((p(a, j2, k2), p(i2, b2, k2), p(i2, j2, c)))
    parts[mat].add(pts, faces)


def lathe(mat, x, z, rings, segs=48):
    """Round shape from (y, radius) rings."""
    a = np.linspace(0, TAU, segs, endpoint=False)
    rows = [[(x + r * math.cos(t), y, z + r * math.sin(t)) for t in a] for y, r in rings]
    grid(mat, rows, closed_u=True, flip=True)


ROWS = dict(egg=(0.00, 0.25), bead=(0.25, 0.375), leaf=(0.375, 0.70))
METRES_PER_U = 1.2


def band_uv(row, count, s):
    """UVs for rows of a moulding. Blender's v runs up the image, so the strip's top is v = 1 - f."""
    f0, f1 = ROWS[row]
    return [[(si / METRES_PER_U, 1.0 - (f0 + (f1 - f0) * j / (count - 1))) for si in s] for j in range(count)]


def sweep(mat, path, profile, closed=False, bands=()):
    """A moulding run along a plan path. path is (x, z) points; profile is (out, y) points, where
    out is measured away from the path to its right-hand (outer) side. Corners are mitred."""
    p = np.asarray(path, dtype=np.float64)
    n = len(p)
    seg = np.roll(p, -1, 0) - p if closed else np.diff(p, axis=0)
    seg /= np.linalg.norm(seg, axis=1, keepdims=True)
    nor = np.stack([-seg[:, 1], seg[:, 0]], -1)                 # right-hand side of travel, seen from above
    miter = np.zeros_like(p)
    for i in range(n):
        if closed:
            a, b = nor[i - 1], nor[i]
        else:
            a = nor[max(i - 1, 0)]
            b = nor[min(i, len(nor) - 1)]
        m = a + b
        miter[i] = m / (1 + a @ b)
    rows = [[(p[i, 0] + miter[i, 0] * o, y, p[i, 1] + miter[i, 1] * o) for i in range(n)] for o, y in profile]
    if not bands:
        grid(mat, rows, closed_u=closed)
        return
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    start = 0
    for i0, i1, row in sorted(bands):
        if i0 > start:
            grid(mat, rows[start:i0 + 1], closed_u=closed)
        # The strip reads from its top edge down, so a band is given bottom first and flipped
        sub = rows[i0:i1 + 1]
        grid("ext_trim", sub, closed_u=closed, uvs=band_uv(row, len(sub), s)[::-1])
        start = i1
    if start < len(rows) - 1:
        grid(mat, rows[start:], closed_u=closed)


# --- Columns -----------------------------------------------------------------------------------
def shaft(x, z):
    flutes, per = 24, 8
    y0 = D.PED_Y + BASE_H
    y1 = CAP_Y - 0.06
    h = y1 - y0
    # Across one flute: fillet, then a round channel
    us = np.array([-1.0, -0.74, -0.62, -0.38, -0.13, 0.13, 0.38, 0.62])
    # Rows: tight near the rounded flute heads, sparse up the long shaft
    head = 0.17
    t_rows = [0.0, 0.012, 0.04, 0.075, 0.11, head, 0.3, 0.55, 0.8, 1.0 / 1.0 * (h - head * 1.4), h - head * 0.9, h - head * 0.55, h - head * 0.28, h - head * 0.09, h]
    t_rows = sorted(set([0.0, 0.03, 0.07, 0.12, 0.18, 0.5, 2.0, 5.0, 8.0, h - 0.4, h - 0.2, h - 0.12, h - 0.07, h - 0.03, h]))
    rows = []
    for t in t_rows:
        s = t / h
        R = D.COL_R - (D.COL_R - D.COL_R_TOP) * max(0.0, (s - 0.33) / 0.67) ** 1.5
        # the flutes close in round heads at both ends
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
    # The body in plain stone, with mouldings round its foot and cap
    cap = [(0.0, D.PED_Y - 0.62), (0.05, D.PED_Y - 0.56), (0.12, D.PED_Y - 0.48), (0.20, D.PED_Y - 0.42), (0.20, D.PED_Y - 0.34), (0.28, D.PED_Y - 0.26),
           (0.32, D.PED_Y - 0.20), (0.32, D.PED_Y - 0.06), (0.26, D.PED_Y), (-w, D.PED_Y)]
    foot = [(-0.02, 0.0), (0.26, 0.0), (0.26, 0.34), (0.20, 0.40), (0.16, 0.46), (0.06, 0.54), (0.0, 0.62)]
    path = [(px - w, z0), (px - w, z1), (px + w, z1), (px + w, z0)]
    # Godot's z grows towards the viewer, so this path turns with its outer side facing away from the block
    sweep("ext_stone", path, [(o, y) for o, y in foot])
    sweep("ext_stone", path, [(o, y) for o, y in cap if o > -1])
    box("ext_stone", px - w - 0.26, px + w + 0.26, D.PED_Y - 0.001, D.PED_Y, z0, z1 + 0.26)
    box("ext_ashlar", px - w, px + w, 0.62, D.PED_Y - 0.62, z0, z1, skip=("d", "u", "n"))


# --- Wall and arch -----------------------------------------------------------------------------
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


def arch_wall(x0, x1, y0, y1, zf, zb, cx, half, ys, n=40):
    angs = sorted({math.pi * i / n for i in range(n + 1)} | {math.atan2(y1 - ys, x1 - cx), math.atan2(y1 - ys, x0 - cx)})
    inner = [(cx + half, y0)] + [(cx + half * math.cos(a), ys + half * math.sin(a)) for a in angs] + [(cx - half, y0)]
    outer = [(x1, y0)] + [ray_rect(cx, ys, a, x0, x1, y1) for a in angs] + [(x0, y0)]
    v, f = [], []
    m = len(inner)
    v += [(x, y, zf) for x, y in inner] + [(x, y, zf) for x, y in outer] + [(x, y, zb) for x, y in inner]
    for i in range(m - 1):
        f.append((i, i + m, i + 1 + m, i + 1))
        f.append((i, i + 1, i + 1 + 2 * m, i + 2 * m))
    parts["ext_ashlar"].add(v, f)


def arch_band(cx, ys, prof, bands, n=48):
    """A moulding that follows the arch; prof is (radius, z) across it."""
    angs = np.linspace(0, math.pi, n + 1)
    rows = []
    for r, z in prof:
        rows.append([(cx + r * math.cos(a), ys + r * math.sin(a), z) for a in angs])
    start = 0
    for i0, i1, row in sorted(bands):
        if i0 > start:
            grid("ext_stone", rows[start:i0 + 1], flip=True)
        r_mid = (prof[i0][0] + prof[i1][0]) / 2
        s = angs * r_mid
        grid("ext_trim", rows[i0:i1 + 1], uvs=band_uv(row, i1 - i0 + 1, s), flip=True)
        start = i1
    if start < len(rows) - 1:
        grid("ext_stone", rows[start:], flip=True)


def arch():
    half = D.ARCH_W / 2
    ys = D.ARCH_CROWN_Y - half
    arch_wall(-10.2, 10.2, 0.0, D.COL_TOP_Y, D.WALL_Z, D.DOOR_Z, 0.0, half, ys)
    prof = [(half - 0.01, D.WALL_Z), (half + 0.02, D.WALL_Z + 0.10), (half + 0.06, D.WALL_Z + 0.14), (half + 0.34, D.WALL_Z + 0.14), (half + 0.37, D.WALL_Z + 0.17),
            (half + 0.42, D.WALL_Z + 0.27), (half + 0.72, D.WALL_Z + 0.27), (half + 0.76, D.WALL_Z + 0.31), (half + 0.84, D.WALL_Z + 0.38), (half + 0.90, D.WALL_Z + 0.38),
            (half + 0.95, D.WALL_Z + 0.26), (half + 0.97, D.WALL_Z)]
    arch_band(0.0, ys, prof, [(1, 3, "bead"), (7, 9, "egg")])
    place_keystone(0.0, D.ARCH_CROWN_Y, D.WALL_Z)
    # Straight jambs under the arch, down to the terrace, and the impost block they carry
    for sx in (-1, 1):
        o = [(sx * r, z) for r, z in prof]
        rows = [[(x, y, z) for x, z in o] for y in (0.0, ys)]
        grid("ext_stone", rows if sx > 0 else [r[::-1] for r in rows])
        xa, xb = sorted((sx * (half - 0.05), sx * (half + 1.02)))
        box("ext_stone", xa, xb, ys - 0.22, ys + 0.02, D.WALL_Z, D.WALL_Z + 0.44)
        box("ext_stone", xa - 0.03, xb + 0.03, ys - 0.34, ys - 0.22, D.WALL_Z, D.WALL_Z + 0.36)
        box("ext_stone", xa - 0.06, xb + 0.06, ys + 0.02, ys + 0.12, D.WALL_Z, D.WALL_Z + 0.50)
    # Round panels in the spandrels, plain for now
    for sx in (-1, 1):
        lathe_disc(sx * 5.25, D.ARCH_CROWN_Y + 0.05, 0.92)


def lathe_disc(x, y, r, n=40):
    z = D.WALL_Z
    prof = [(r, 0.0), (r, 0.16), (r - 0.05, 0.22), (r - 0.16, 0.22), (r - 0.20, 0.10), (0.0, 0.10)]
    a = np.linspace(0, TAU, n, endpoint=False)
    rows = [[(x + rr * math.cos(t), y + rr * math.sin(t), z + dz) for t in a] for rr, dz in prof]
    grid("ext_stone", rows, closed_u=True)


def arch_infill():
    half = D.ARCH_W / 2
    ys = D.ARCH_CROWN_Y - half
    z = D.DOOR_Z
    transom = 12.8
    # Wall under the window, with the doors at the bottom
    box("ext_ashlar", -half, half, 6.0, transom - 0.75, z - 0.2, z + 0.05, skip=("d", "u", "n"))
    box("ext_ashlar", -half, -D.DOOR_W / 2 - 0.3, 0, 6.0, z - 0.2, z + 0.05, skip=("d", "u", "n"))
    box("ext_ashlar", D.DOOR_W / 2 + 0.3, half, 0, 6.0, z - 0.2, z + 0.05, skip=("d", "u", "n"))
    # Heavy transom carrying the window
    for dy0, dy1, dz in ((-0.75, -0.42, 0.20), (-0.42, -0.30, 0.34), (-0.30, -0.12, 0.42), (-0.12, 0.0, 0.34)):
        box("ext_stone", -half, half, transom + dy0, transom + dy1, z, z + dz)
    # Door lintel, and a simple frame; the doors themselves come with the central front
    box("ext_stone", -2.75, 2.75, 3.9, 4.5, z, z + 0.44)
    box("ext_stone", -2.95, 2.95, 4.5, 4.72, z, z + 0.62)
    box("ext_stone", -2.75, 2.75, 4.72, 5.9, z, z + 0.16)
    box("ext_stone", -2.95, 2.95, 5.9, 6.1, z, z + 0.40)
    for sx in (-1, 1):
        for dx in (1.85, 2.45):
            lathe("ext_stone", sx * dx, z + 0.30, [(0.0, 0.27), (0.22, 0.27), (0.30, 0.21), (3.5, 0.18), (3.62, 0.22), (3.9, 0.25)], 16)
    box("ext_bronze", -D.DOOR_W / 2, D.DOOR_W / 2, 0, 3.9, z - 0.08, z - 0.02)
    # Stone mullions dividing the window into three lights, with small caps
    for sx in (-1, 1):
        x = sx * 1.18
        box("ext_stone", x - 0.24, x + 0.24, transom, D.ARCH_CROWN_Y - 0.5, z, z + 0.32)
        box("ext_stone", x - 0.31, x + 0.31, ys + 1.15, ys + 1.42, z, z + 0.42)
    lattice(transom, ys, half, z + 0.10)


def lattice(y0, ys, half, z):
    """The dark star-pattern grille of the real windows, as thin bronze bars over faintly lit glass."""
    # Glass: one fan across the lunette
    pts = [(half - 0.02, y0)] + [(half * 0.995 * math.cos(a), ys + half * 0.995 * math.sin(a)) for a in np.linspace(0, math.pi, 32)] + [(-half + 0.02, y0)]
    v = [(x, y, z - 0.03) for x, y in pts]
    parts["ext_glass"].add(v, [tuple(range(len(v)))[::-1]])
    pitch = 1.06
    t = 0.035
    d = 0.05

    def inside(x, y):
        return y >= y0 and (y <= ys or x * x + (y - ys) ** 2 < (half - 0.02) ** 2) and abs(x) < half

    def bar(a, b):
        ax, ay = a
        bx, by = b
        # clip by stepping along the bar, then one box-like strip for each run inside the window
        steps = 10
        run = []
        for i in range(steps + 1):
            s = i / steps
            p = (ax + (bx - ax) * s, ay + (by - ay) * s)
            if inside(*p):
                run.append(p)
        if len(run) >= 2:
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
            cx, cy = i * pitch, y0 + j * pitch
            h = pitch / 2
            bar((cx - h, cy), (cx + h, cy))
            bar((cx, cy - h), (cx, cy + h))
            bar((cx - h, cy - h), (cx + h, cy + h))
            bar((cx - h, cy + h), (cx + h, cy - h))


def pilasters():
    """The flat fluted partners on the wall behind each column."""
    for px in (-7.0, 7.0):
        for sx in (-1, 1):
            x = px + sx * D.PAIR_GAP
            w = 0.72
            z = D.WALL_Z
            y0, y1 = D.PED_Y, CAP_Y - 0.13
            # 5 flutes across the face
            us = np.linspace(-w, w, 41)
            prof = []
            for u in us:
                t = (u + w) / (2 * w) * 5
                ph = t % 1.0
                dd = 0.035 * math.sin(math.pi * min(max((ph - 0.14) / 0.72, 0), 1)) if 0.04 < t < 4.96 else 0.0
                prof.append((x + u, z + 0.30 - dd))
            prof = [(x - w, z)] + prof + [(x + w, z)]
            rows = [[(a, y, b) for a, b in prof] for y in (y0 + 0.8, y1)]
            grid("ext_shaft", rows)
            box("ext_stone", x - w - 0.14, x + w + 0.14, y0, y0 + 0.3, z, z + 0.46)
            box("ext_stone", x - w - 0.08, x + w + 0.08, y0 + 0.3, y0 + 0.8, z, z + 0.38)


# --- Entablature -------------------------------------------------------------------------------
def plan_path():
    w = W_BREAK
    return [(-SPAN_X, ZF), (-7 - w, ZF), (-7 - w, ZB), (-7 + w, ZB), (-7 + w, ZF), (7 - w, ZF), (7 - w, ZB), (7 + w, ZB), (7 + w, ZF), (SPAN_X, ZF)]


def entablature():
    y = D.COL_TOP_Y
    path = plan_path()
    # out, height: from the architrave to the top of the cornice, all measured from the frieze face
    prof = [(-1.2, y), (-0.16, y), (-0.16, y + 0.31), (-0.13, y + 0.34), (-0.09, y + 0.37), (-0.09, y + 0.69), (-0.06, y + 0.72), (-0.03, y + 0.75),
            (-0.03, y + 1.03), (0.02, y + 1.06), (0.12, y + 1.13), (0.16, y + 1.20), (0.16, y + 1.27), (0.02, y + 1.30),
            (0.02, y + 2.22), (0.06, y + 2.25), (0.10, y + 2.30), (0.10, y + 2.36),
            (0.20, y + 2.36), (0.20, y + 2.66), (0.27, y + 2.70), (0.40, y + 2.83), (0.46, y + 2.86), (0.46, y + 3.12),
            (1.46, y + 3.12), (1.46, y + 3.16), (1.52, y + 3.16), (1.52, y + 3.48), (1.58, y + 3.52), (1.66, y + 3.56), (1.72, y + 3.66), (1.82, y + 3.80), (1.90, y + 3.84), (1.92, y + 3.90), (0.6, y + 3.90)]
    # egg-and-dart over the architrave and under the dentil zone, a bead below it, leaves on the top moulding
    sweep("ext_stone", path, prof, bands=[(8, 11, "egg"), (14, 17, "bead"), (19, 22, "egg"), (28, 33, "leaf")])
    # The blocks of entablature over the columns are solid: close their undersides back to the wall
    for px in (-7.0, 7.0):
        box("ext_stone", px - W_BREAK + 0.17, px + W_BREAK - 0.17, y - 0.002, y, 9.9, ZB - 1.0, skip=("w", "e", "u", "n", "s"))
    dentils(path)
    modillions(path)
    soffit_panels(path)


def on_path(path, pitch, margin):
    """Evenly spaced points along each straight run of the path, with the run's outward direction."""
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
            p = a + d * (off + i * pitch)
            yield p, d, nor


def oriented_box(mat, p, d, nor, along, o0, o1, y0, y1):
    """A block sitting on the path: along is half its length, o0 to o1 its reach outwards."""
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


ORN = pathlib.Path(argv[1])


def load_game(tag, u0, v0, size):
    z = np.load(ORN / f"{tag}_game.npz")
    return z["verts"], z["tris"], z["uvs"] * size + np.array([u0, v0], dtype=np.float32)


BRACKET = load_game("modillion", 0.0, 0.75, 0.25)
KEY = load_game("keystone", 0.25, 0.75, 0.25)


def add_tris(mat, world, tris, uvs, flip):
    """Unindexed triangles keep each corner's UV; welding afterwards joins what can be joined."""
    pts, faces, tuv = [], [], []
    for i, (a, b, c) in enumerate(tris):
        k = len(pts)
        pts += [world[a], world[b], world[c]]
        tuv += list(uvs[i])
        faces.append((k, k + 2, k + 1) if flip else (k, k + 1, k + 2))
    parts[mat].add(pts, faces, tuv)


def modillions(path):
    """Carved brackets under the cornice, with their big scroll against the wall."""
    y1 = D.COL_TOP_Y + 3.12
    v, tris, uvs = BRACKET
    for p, d, nor in on_path(path, 1.06, 0.40):
        o = 0.46
        world = [((p + d * q[0] + nor * (o + q[1]))[0], y1 + q[2], (p + d * q[0] + nor * (o + q[1]))[1]) for q in v]
        add_tris("ext_carved", world, tris, uvs, flip=True)


def soffit_panels(path):
    """Rosette coffers in the soffit, between the brackets."""
    y = D.COL_TOP_Y + 3.118
    for p, d, nor in on_path(path, 1.06, 0.40):
        c = p + d * 0.53
        a, b = 0.30, 0.42
        o0, o1 = 0.52, 1.36

        def pt(s, o):
            q = c + d * s + nor * o
            return (q[0], y, q[1])

        v = [pt(-a, o0), pt(a, o0), pt(a, o1), pt(-a, o1)]
        # one rosette cell of the strip: a third of its width, the bottom 30 percent of its height
        parts["ext_trim"].add(v, [(0, 1, 2, 3)], [(0.0, 0.0), (1 / 3, 0.0), (1 / 3, 0.3), (0.0, 0.3)])


def place_keystone(x, y, z):
    v, tris, uvs = KEY
    world = [(q[0] + x, q[1] + y, q[2] + z) for q in v]
    add_tris("ext_carved", world, tris, uvs, flip=False)


def attic():
    y0, y1 = D.ENT_TOP_Y, D.ATTIC_TOP_Y
    z = D.WALL_Z - 0.4
    box("ext_ashlar", -SPAN_X, SPAN_X, y0, y1 - 0.5, 0.0, z, skip=("w", "e", "d", "u", "n"))
    box("ext_stone", -SPAN_X, SPAN_X, y0, y0 + 0.5, z, z + 0.24, skip=("w", "e", "n"))
    prof = [(0.0, y1 - 0.62), (0.06, y1 - 0.56), (0.16, y1 - 0.46), (0.30, y1 - 0.34), (0.42, y1 - 0.28), (0.44, y1 - 0.12), (0.52, y1 - 0.06), (0.56, y1), (0.0, y1)]
    sweep("ext_stone", [(-SPAN_X, z), (SPAN_X, z)], prof)
    n = 19
    for i in range(n):
        x = -SPAN_X + 0.7 + i * (2 * SPAN_X - 1.4) / (n - 1)
        bevel_box("ext_stone", x - 0.34, x + 0.34, y1, D.CREST_Y, z - 0.3, z + 0.02, 0.05)


def stacked_blocks(px):
    """The great unfinished blocks above each column pair: courses of rough stone, stepping in."""
    tiers = [(D.ENT_TOP_Y, 3, 3.75, 3.0, 4), (D.ENT_TOP_Y + 1.15, 3, 3.55, 2.8, 3), (D.ENT_TOP_Y + 2.3, 3, 3.2, 2.5, 3), (D.ENT_TOP_Y + 3.35, 3, 2.75, 2.1, 2), (D.ENT_TOP_Y + 4.3, 2, 2.2, 1.6, 2)]
    zc = D.COL_Z - 0.55
    for y0, nx, hw, hd, _ in tiers:
        h = 1.13 if y0 < D.ENT_TOP_Y + 3 else 1.0
        if y0 + h > D.BLOCK_TOP_Y + 0.2:
            h = D.BLOCK_TOP_Y + 0.2 - y0
        n = max(int(2 * hw / 1.7), 2)
        for i in range(n):
            x0 = px - hw + i * 2 * hw / n
            x1 = x0 + 2 * hw / n
            jit = rng.uniform(-0.05, 0.05, 3)
            top = y0 + h + 0.0
            bevel_box("ext_rough", x0 + 0.012, x1 - 0.012, y0, top, zc - hd + jit[0] * 0.5, zc + hd + jit[1], 0.05 + abs(jit[2]) * 0.6)


# --- Stairs and terrace ------------------------------------------------------------------------
def stairs():
    run = (D.STAIR_Z_BOT - D.STAIR_Z_TOP) / D.STAIR_STEPS
    rise = (D.TERRACE_Y - D.PLAZA_Y) / D.STAIR_STEPS
    xs = np.linspace(-D.STAIR_X, D.STAIR_X, 33)

    def dip(x):
        # A century of feet: a shallow hollow down the middle, a little wandering from step to step
        return 0.028 * math.exp(-(x / 6.5) ** 2)

    for i in range(D.STAIR_STEPS):
        y = D.TERRACE_Y - i * rise
        z0 = D.STAIR_Z_TOP + i * run
        z1 = z0 + run
        wob = rng.uniform(-0.2, 0.2)
        nos = 0.022
        under = 0.035                      # each step's front is set back under its nose
        back = z0 - under if i else z0
        tread = [(back, y, 0.8), (z0 + run * 0.55, y, 1.0), (z1 - nos, y, 1.0), (z1, y - nos, 1.0)]
        riser = [(z1, y - nos, 1.0), (z1, y - 0.05, 0.95), (z1 - under, y - 0.065, 0.9), (z1 - under, y - rise, 0.8)]
        grid("ext_granite", [[(float(x), yy - dip(x - wob) * k, zz) for x in xs] for zz, yy, k in tread], flip=True)
        grid("ext_riser", [[(float(x), yy - dip(x - wob) * k, zz) for x in xs] for zz, yy, k in riser], flip=True)
    # Terrace paving, doors to top step
    box("ext_paving", -D.PAV_X + 0.0, D.PAV_X - 0.0, D.TERRACE_Y - 0.5, D.TERRACE_Y, D.DOOR_Z - 0.1, D.STAIR_Z_TOP, skip=("w", "e", "d", "n", "s"))
    # Low side walls with a sloped stone coping, and the front of the top landing
    for sx in (-1, 1):
        x0, x1 = sorted((sx * D.STAIR_X, sx * (D.STAIR_X + D.CHEEK_W)))
        v = [(x0, D.PLAZA_Y, D.STAIR_Z_TOP), (x0, D.CHEEK_H, D.STAIR_Z_TOP), (x0, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_BOT), (x0, D.PLAZA_Y, D.STAIR_Z_BOT),
             (x1, D.PLAZA_Y, D.STAIR_Z_TOP), (x1, D.CHEEK_H, D.STAIR_Z_TOP), (x1, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_BOT), (x1, D.PLAZA_Y, D.STAIR_Z_BOT)]
        parts["ext_ashlar"].add(v, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6)])
    handrails()


def handrails():
    """Two bronze rails down the stairs, a real touch of the building, and good for scale."""
    for x in (-6.0, 6.0):
        z0, z1 = D.STAIR_Z_TOP - 0.2, D.STAIR_Z_BOT + 0.25
        h = 0.92
        def yy(z):
            return D.TERRACE_Y - (min(max(z, D.STAIR_Z_TOP), D.STAIR_Z_BOT) - D.STAIR_Z_TOP) / (D.STAIR_Z_BOT - D.STAIR_Z_TOP) * 4.5
        zs = [z0, D.STAIR_Z_TOP + 0.05, D.STAIR_Z_BOT - 0.05, z1]
        path = np.array([(x, yy(z) + h, z) for z in zs])
        tube(path, 0.03)
        for i in range(5):
            z = D.STAIR_Z_TOP + 0.4 + i * 2.2
            tube(np.array([(x, yy(z) - 0.01, z), (x, yy(z) + h, z)]), 0.018)


def tube(path, r, n=8):
    path = np.asarray(path, dtype=np.float64)
    a = np.linspace(0, TAU, n, endpoint=False)
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    ref = np.array([1.0, 0.0, 0.0]) if abs(tang[0, 0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    rows = []
    for p, t in zip(path, tang):
        s = np.cross(t, ref)
        s /= np.linalg.norm(s)
        u = np.cross(s, t)
        rows.append([tuple(p + r * (s * math.cos(q) + u * math.sin(q))) for q in a])
    grid("ext_bronze", rows, closed_u=True, flip=True)


# --- Output ------------------------------------------------------------------------------------
def build_all():
    for px in (-7.0, 7.0):
        pedestal(px)
        for sx in (-1, 1):
            shaft(px + sx * D.PAIR_GAP, D.COL_Z)
            base(px + sx * D.PAIR_GAP, D.COL_Z)
        stacked_blocks(px)
    arch()
    arch_infill()
    pilasters()
    entablature()
    attic()
    stairs()


def export():
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    tris_total = 0
    objs = []
    for name, part in parts.items():
        if not part.f:
            continue
        me = bpy.data.meshes.new("Section_" + name)
        me.from_pydata(part.v, [], part.f)
        me.update()
        layer = me.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", np.array([part.uv[i] for f in part.f for i in f], dtype=np.float32).ravel())
        bm = bmesh.new()
        bm.from_mesh(me)
        if name not in ("ext_trim", "ext_carved"):
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0004)
        seen = set()
        for start in bm.faces:
            if start.index in seen:
                continue
            bm.faces.ensure_lookup_table()
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
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        me.materials.append(m)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(38))
        ob = bpy.data.objects.new(me.name, me)
        scene.collection.objects.link(ob)
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        tris_total += tris
        print("PART", name, tris, flush=True)
        objs.append(ob)
    print("SECTION_TRIS", tris_total, flush=True)
    for ob in scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / "section.glb"), export_format="GLB", use_selection=True, export_yup=True,
                              export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT", export_tangents=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "section.blend"), compress=True)


build_all()
export()
print("DONE", flush=True)
