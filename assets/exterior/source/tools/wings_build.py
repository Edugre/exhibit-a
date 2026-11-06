"""Background Blender job: the rest of the building, in a simpler form of the centre's language, after
reference photos of the real wings. A banded base with barred windows, a run of three pedimented windows
beside the centre, then great arched windows between pilasters, a cornice, and an attic of sunk panels
with a line of carved cresting. Walls are written in wall space: u along the face, y up, w out of it,
so one set of tools serves every wall.
usage: blender -b --factory-startup --python wings_build.py -- <out dir> <ornament dir>"""
import importlib
import math
import pathlib
import sys
import numpy as np

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import front_build as F

importlib.reload(F)
D = F.D
WALL, TRIM = "ext_wing_wall", "ext_wing_trim"
GLASS = "ext_wing_glass"
F.MATS += [WALL, TRIM, GLASS]
TAU = 2 * math.pi
FACE = 0.35             # the facade stands this far in front of the plain body behind it
SECTIONS = {}


def fresh():
    F.parts = {m: F.Part() for m in F.MATS}
    return F.parts


class Wall:
    """One straight face. Viewed from outside, u runs to the right."""

    def __init__(self, a, b):
        self.a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        self.length = float(np.linalg.norm(b - a))
        self.d = (b - a) / self.length
        self.n = np.array([-self.d[1], self.d[0]])

    def T(self, u, y, w):
        p = self.a + self.d * u + self.n * w
        return (float(p[0]), float(y), float(p[1]))

    def grid(self, mat, rows, **k):
        F.grid(mat, [[self.T(*q) for q in r] for r in rows], **k)

    def quad(self, mat, u0, u1, y0, y1, w=0.0):
        self.grid(mat, [[(u0, y0, w), (u1, y0, w)], [(u0, y1, w), (u1, y1, w)]])

    def box(self, mat, u0, u1, y0, y1, w0, w1, skip=("n",)):
        v = [self.T(u, y, w) for u in (u0, u1) for y in (y0, y1) for w in (w0, w1)]
        faces = {"w": (0, 1, 3, 2), "e": (4, 6, 7, 5), "d": (0, 4, 5, 1), "u": (2, 3, 7, 6), "n": (0, 2, 6, 4), "s": (1, 5, 7, 3)}
        F.parts[mat].add(v, [q for k, q in faces.items() if k not in skip])

    def slab(self, mat, p0, p1, thick, w0, w1):
        """A bar between two points on the face, for sloped cornices."""
        u0, y0 = p0
        u1, y1 = p1
        v = []
        for u, y in ((u0, y0), (u1, y1), (u1, y1 + thick), (u0, y0 + thick)):
            v += [self.T(u, y, w0), self.T(u, y, w1)]
        F.parts[mat].add(v, [(1, 3, 5, 7), (7, 5, 4, 6), (0, 1, 7, 6), (2, 4, 5, 3), (1, 0, 2, 3)])

    def opening(self, mat, u0, u1, y0, y1, cu, half, ys, wb, n=16):
        """A wall panel with a round-headed opening through it, as deep as wb."""
        angs = sorted({math.pi * i / n for i in range(n + 1)} | {math.atan2(y1 - ys, u1 - cu), math.atan2(y1 - ys, u0 - cu)})
        inner = [(cu + half, y0)] + [(cu + half * math.cos(a), ys + half * math.sin(a)) for a in angs] + [(cu - half, y0)]
        outer = [(u1, y0)] + [F.ray_rect(cu, ys, a, u0, u1, y1) for a in angs] + [(u0, y0)]
        m = len(inner)
        v = [self.T(u, y, 0.0) for u, y in inner] + [self.T(u, y, 0.0) for u, y in outer] + [self.T(u, y, wb) for u, y in inner]
        f = []
        for i in range(m - 1):
            f.append((i, i + m, i + 1 + m, i + 1))
            f.append((i, i + 1, i + 1 + 2 * m, i + 2 * m))
        F.parts[mat].add(v, f)
        return inner

    def glass(self, outline, w):
        pts = [self.T(u, y, w) for u, y in outline]
        F.parts[GLASS].add(pts, [tuple(range(len(pts)))])


def moulded(rows, s, bands):
    """A profile run, with named spans carrying the carved strip."""
    start = 0
    for i0, i1, row in sorted(bands):
        if i0 > start:
            F.grid(TRIM, rows[start:i0 + 1], flip=True)
        F.grid("ext_trim", rows[i0:i1 + 1], uvs=F.band_uv(row, i1 - i0 + 1, s), flip=True)
        start = i1
    if start < len(rows) - 1:
        F.grid(TRIM, rows[start:], flip=True)


def keystone(W, cu, y, h=0.86, w0=0.0, top=0.5, bottom=0.34):
    """A wedge of stone at the crown of an arch, with a carved bracket on its face."""
    pts = [(cu - bottom, y), (cu + bottom, y), (cu + top, y + h), (cu - top, y + h)]
    v = [W.T(u, q, w0 + 0.24) for u, q in pts] + [W.T(u, q, w0) for u, q in pts]
    F.parts[TRIM].add(v, [(0, 1, 2, 3), (4, 5, 1, 0), (5, 6, 2, 1), (3, 2, 6, 7), (4, 0, 3, 7)])
    F.place("ext_carved", F.BRACKET, lambda q: W.T(q[0] * 0.9 + cu, -q[2] * 0.0 + q[1] * 0.9 + y + h * 0.5, q[2] * 0.9 + w0 + 0.2), flip=False)


def arched_window(W, cu, half, sill, ys, u0, u1, top):
    """The great window: a real opening, its moulded surround running up, over and down."""
    wb = -FACE + 0.02
    inner = W.opening(WALL, u0, u1, sill, top, cu, half, ys, wb)
    W.glass(inner, wb + 0.01)
    # Bronze frame: uprights, rails, and a fan in the arched head
    z0, z1 = wb + 0.015, wb + 0.09
    W.box("ext_bronze", cu - half, cu + half, sill, sill + 0.09, z0, z1)
    W.box("ext_bronze", cu - half, cu + half, ys - 0.05, ys + 0.05, z0, z1)
    y = sill + 1.45
    while y < ys - 0.5:
        W.box("ext_bronze", cu - half, cu + half, y - 0.03, y + 0.03, z0, z1)
        y += 1.45
    for du in (-half * 0.36, half * 0.36):
        W.box("ext_bronze", cu + du - 0.04, cu + du + 0.04, sill, ys + math.sqrt(half * half - du * du), z0, z1)
    for a in (35, 90, 145):
        r = math.radians(a)
        F.tube([W.T(cu + 0.42 * math.cos(r), ys + 0.42 * math.sin(r), z1 - 0.03), W.T(cu + half * math.cos(r), ys + half * math.sin(r), z1 - 0.03)], 0.03, 4)
    F.tube([W.T(cu + 0.42 * math.cos(a), ys + 0.42 * math.sin(a), z1 - 0.03) for a in np.linspace(0, math.pi, 7)], 0.03, 4, ref=(W.n[0], 0.0, W.n[1]))
    # Surround
    prof = [(half - 0.02, -0.07), (half + 0.03, 0.09), (half + 0.26, 0.09), (half + 0.29, 0.13), (half + 0.44, 0.13), (half + 0.50, 0.09), (half + 0.54, 0.0)]
    angs = np.linspace(0, math.pi, 17)
    rows = [[W.T(cu + r * math.cos(a), ys + r * math.sin(a), w) for a in angs] for r, w in prof]
    bands = [(3, 4, "bead")]
    moulded(rows, angs * (half + 0.36), bands)
    for sign, ys_ in ((1, (sill, ys)), (-1, (ys, sill))):
        rows = [[W.T(cu + sign * r, y, w) for y in ys_] for r, w in prof]
        moulded(rows, np.array(ys_), bands)
    keystone(W, cu, ys + half - 0.06)
    # A deep sill on two small blocks
    W.box(TRIM, cu - half - 0.68, cu + half + 0.68, sill - 0.2, sill, 0.0, 0.24)
    W.box(TRIM, cu - half - 0.60, cu + half + 0.60, sill - 0.36, sill - 0.2, 0.0, 0.1)


def pedimented_window(W, cu, half, sill, top, u0, u1, y0, y1):
    """Square-headed, in an architrave, under a pediment on two carved brackets."""
    wb = -FACE + 0.02
    W.quad(WALL, u0, cu - half, y0, y1)
    W.quad(WALL, cu + half, u1, y0, y1)
    W.quad(WALL, cu - half, cu + half, y0, sill)
    W.quad(WALL, cu - half, cu + half, top, y1)
    W.grid(WALL, [[(cu - half, sill, wb), (cu - half, sill, 0.0)], [(cu - half, top, wb), (cu - half, top, 0.0)]])
    W.grid(WALL, [[(cu + half, sill, 0.0), (cu + half, sill, wb)], [(cu + half, top, 0.0), (cu + half, top, wb)]])
    W.grid(WALL, [[(cu - half, top, 0.0), (cu + half, top, 0.0)], [(cu - half, top, wb), (cu + half, top, wb)]])
    W.grid(WALL, [[(cu - half, sill, wb), (cu + half, sill, wb)], [(cu - half, sill, 0.0), (cu + half, sill, 0.0)]])
    W.glass([(cu - half, sill), (cu + half, sill), (cu + half, top), (cu - half, top)], wb + 0.01)
    z0, z1 = wb + 0.015, wb + 0.09
    W.box("ext_bronze", cu - 0.035, cu + 0.035, sill, top, z0, z1)
    y = sill + 1.1
    while y < top - 0.3:
        W.box("ext_bronze", cu - half, cu + half, y - 0.03, y + 0.03, z0, z1)
        y += 1.1
    # Architrave
    t = 0.36
    W.box(TRIM, cu - half - t, cu - half, sill, top + t, 0.0, 0.13)
    W.box(TRIM, cu + half, cu + half + t, sill, top + t, 0.0, 0.13)
    W.box(TRIM, cu - half, cu + half, top, top + t, 0.0, 0.13)
    W.box(TRIM, cu - half - 0.55, cu + half + 0.55, sill - 0.18, sill, 0.0, 0.26)
    # Brackets, frieze and pediment
    for sign in (-1, 1):
        q = cu + sign * (half + t + 0.1)
        F.place("ext_carved", F.BRACKET, lambda p, q=q: W.T(p[0] * 0.75 + q, p[1] * 1.1 + top + 0.36, p[2] * 0.7 + 0.14), flip=False)
    y = top + t + 0.05
    span = half + t + 0.42
    W.box(TRIM, cu - span, cu + span, y, y + 0.2, 0.0, 0.38)
    rise = 0.86
    W.slab(TRIM, (cu - span - 0.1, y + 0.18), (cu, y + 0.18 + rise), 0.24, 0.0, 0.40)
    W.slab(TRIM, (cu, y + 0.18 + rise), (cu + span + 0.1, y + 0.18), 0.24, 0.0, 0.40)
    v = [W.T(cu - span, y + 0.2, 0.08), W.T(cu + span, y + 0.2, 0.08), W.T(cu, y + 0.2 + rise, 0.08)]
    F.parts[TRIM].add(v, [(0, 1, 2)])


def pilaster(W, u, y0=0.0, y1=11.4, half=0.5):
    """A plain strip between bays, on a block and under a moulded head."""
    W.box(TRIM, u - half, u + half, y0, y1, 0.0, 0.17)
    W.box(TRIM, u - half - 0.1, u + half + 0.1, y0, y0 + 0.74, 0.0, 0.26)
    W.box(TRIM, u - half - 0.1, u + half + 0.1, y1 - 0.5, y1 - 0.34, 0.0, 0.26)
    W.box(TRIM, u - half - 0.14, u + half + 0.14, y1 - 0.34, y1, 0.0, 0.3)


def basement_window(W, cu, half=1.0):
    y0, y1 = -3.2, -1.5
    w = 0.47
    W.box(GLASS, cu - half, cu + half, y0, y1, w - 0.02, w + 0.01)
    t = 0.2
    W.box(TRIM, cu - half - t, cu - half, y0 - t, y1 + t, w - 0.03, w + 0.09)
    W.box(TRIM, cu + half, cu + half + t, y0 - t, y1 + t, w - 0.03, w + 0.09)
    W.box(TRIM, cu - half, cu + half, y1, y1 + t, w - 0.03, w + 0.09)
    W.box(TRIM, cu - half, cu + half, y0 - t, y0, w - 0.03, w + 0.12)
    u = cu - half + 0.22
    while u < cu + half:
        F.tube([W.T(u, y0, w + 0.04), W.T(u, y1, w + 0.04)], 0.016, 4)
        u += 0.26
    for y in (y0 + 0.55, y1 - 0.55):
        W.box("ext_bronze", cu - half, cu + half, y - 0.018, y + 0.018, w + 0.02, w + 0.06)


def rusticated(W, u0, u1, y0=-3.86, y1=-0.78, w=0.41):
    """Deep horizontal channels across the base, as on the centre's end bays."""
    pitch = 0.77
    rows = []
    n = int((y1 - y0) / pitch)
    for i in range(n):
        y = y0 + i * pitch
        for dy, dw in ((0.0, -0.075), (0.05, -0.075), (0.09, 0.0), (pitch - 0.04, 0.0), (pitch, -0.05)):
            rows.append((y + dy, w + dw))
    rows.append((y1, w))
    W.grid(TRIM, [[(u0, y, q), (u1, y, q)] for y, q in rows])


def sunk_panel(W, u0, u1, y0, y1, w=0.0):
    """The long sunk panels of the attic: a recessed field in a thin moulded frame."""
    W.quad(WALL, u0, u1, y0, y1, w - 0.09)
    t = 0.14
    W.box(TRIM, u0, u1, y0, y0 + t, w - 0.09, w)
    W.box(TRIM, u0, u1, y1 - t, y1, w - 0.09, w)
    W.box(TRIM, u0, u0 + t, y0 + t, y1 - t, w - 0.09, w)
    W.box(TRIM, u1 - t, u1, y0 + t, y1 - t, w - 0.09, w)


def cresting(W, u0, u1, y, pitch=1.5, h=0.74):
    """The carved line along the skyline: a row of palmettes standing on the cornice."""
    u = u0 + pitch / 2
    while u < u1:
        pts = []
        for i in range(11):
            a = math.pi * i / 10
            r = h * (1.0 if i % 2 == 0 else 0.68) * (0.72 + 0.28 * math.sin(a))
            pts.append((u + r * 0.62 * math.cos(a), y + 0.1 + r * math.sin(a)))
        n = len(pts)
        v = [W.T(a, b, 0.02) for a, b in pts] + [W.T(a, b, -0.09) for a, b in pts]
        f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i + n, i + n + 1, i + 1, i) for i in range(n - 1)]
        F.parts[TRIM].add(v, f)
        W.box(TRIM, u - 0.4, u + 0.4, y, y + 0.14, -0.1, 0.03)
        u += pitch


def main_cornice_profile(y):
    return [(-0.05, y - 1.45), (0.02, y - 1.45), (0.02, y - 1.0), (0.05, y - 0.97), (0.05, y - 0.62), (0.03, y - 0.6), (0.03, y - 0.1), (0.1, y - 0.04),
            (0.2, y + 0.06), (0.24, y + 0.1), (0.24, y + 0.26), (0.32, y + 0.3), (0.62, y + 0.34), (0.68, y + 0.4), (0.74, y + 0.52), (0.82, y + 0.68), (0.86, y + 0.8), (-0.2, y + 0.8)]


def top_cornice_profile(y):
    return [(-0.05, y - 0.62), (0.03, y - 0.62), (0.03, y - 0.4), (0.12, y - 0.34), (0.3, y - 0.2), (0.34, y - 0.12), (0.46, y - 0.06), (0.5, y), (-0.3, y)]


BASE_PROFILE = [(0.82, D.PLAZA_Y), (0.82, -4.06), (0.70, -3.96), (0.46, -3.90), (0.30, -3.86), (0.30, -0.78), (0.46, -0.72), (0.58, -0.62), (0.58, -0.52),
                (0.70, -0.42), (0.74, -0.30), (0.74, -0.08), (0.66, 0.0), (0.0, 0.0)]


def bays(W, edges, kind, sill=1.7, ys=8.2, half=1.75, top=11.4):
    """Arched bays between the given pilaster lines."""
    for a, b in zip(edges[:-1], edges[1:]):
        cu = (a + b) / 2
        W.quad(WALL, a, b, 0.0, sill)
        arched_window(W, cu, half, sill, ys, a, b, top)
        for u0, u1 in ((a + 0.5, cu - half - 0.54), (cu + half + 0.54, b - 0.5)):
            W.box(TRIM, u0, u1, ys - 0.2, ys + 0.06, 0.0, 0.06)     # the string that ties the imposts together
        if kind == "base":
            basement_window(W, cu)
    for u in edges:
        pilaster(W, u)


def attic(W, edges, y0, y1):
    W.quad(WALL, edges[0], edges[-1], y0, y0 + 0.4)
    W.quad(WALL, edges[0], edges[-1], y1 - 0.5, y1)
    for a, b in zip(edges[:-1], edges[1:]):
        sunk_panel(W, a + 0.72, b - 0.72, y0 + 0.4, y1 - 0.5)
        W.quad(WALL, a, a + 0.72, y0 + 0.4, y1 - 0.5)
        W.quad(WALL, b - 0.72, b, y0 + 0.4, y1 - 0.5)
    for u in edges:
        W.box(TRIM, u - 0.5, u + 0.5, y0, y1 - 0.5, 0.0, 0.12)


def mid_wing(a, b, near_centre_at_start):
    """The long wall between the centre and an end wing."""
    W = Wall(a, b)
    L = W.length
    if near_centre_at_start:
        trio = (0.0, 15.6)
        run = np.linspace(15.6, L, 6)
    else:
        trio = (L - 15.6, L)
        run = np.linspace(0.0, L - 15.6, 6)
    # The three pedimented windows next to the centre
    s0, s1 = trio
    edges = [s0, s0 + 5.2, s0 + 10.4, s1]
    for i in range(3):
        pedimented_window(W, (edges[i] + edges[i + 1]) / 2, 1.0, 1.5, 6.9, edges[i], edges[i + 1], 0.0, 11.4)
        basement_window(W, (edges[i] + edges[i + 1]) / 2, 0.75)
    bays(W, list(run), "base")
    rusticated(W, 0.0, L)
    edges_up = [s0 + 0.05, (s0 + s1) / 2, s1] if near_centre_at_start else [s0, (s0 + s1) / 2, s1 - 0.05]
    attic(W, [q for q in sorted(set(list(run) + edges_up))], D.CORNICE_Y + 0.8, D.WING_TOP_Y - 0.62)
    cresting(W, 0.0, L, D.WING_TOP_Y)
    return W


def end_front(a, b, top):
    W = Wall(a, b)
    edges = list(np.linspace(0.0, W.length, 6))
    W.quad(WALL, 0.0, W.length, 0.0, 0.01)
    bays(W, edges, "base", half=1.95, ys=8.0)
    rusticated(W, 0.0, W.length)
    attic(W, edges, D.CORNICE_Y + 0.8, top - 0.62)
    cresting(W, 0.0, W.length, top)
    return W


def side(a, b, top, pitch):
    W = Wall(a, b)
    n = max(int(round(W.length / pitch)), 1)
    edges = list(np.linspace(0.0, W.length, n + 1))
    bays(W, edges, "base", half=1.7, ys=8.0)
    rusticated(W, 0.0, W.length)
    attic(W, edges, D.CORNICE_Y + 0.8, top - 0.62)
    cresting(W, 0.0, W.length, top)
    return W


def offset(path, by):
    """Move a plan path out by a distance, keeping corners mitred."""
    p = np.asarray(path, dtype=float)
    seg = np.diff(p, axis=0)
    seg /= np.linalg.norm(seg, axis=1, keepdims=True)
    nor = np.stack([-seg[:, 1], seg[:, 0]], -1)
    out = []
    for i in range(len(p)):
        a = nor[max(i - 1, 0)]
        b = nor[min(i, len(nor) - 1)]
        out.append(tuple(p[i] + (a + b) / (1 + a @ b) * by))
    return out


def front_section(sx):
    """One half of the front: middle wing, the return of the end wing, end wing and first stretch of its side."""
    P, M, Z, Y, X, S = D.PAV_X, D.MID_X, D.MID_Z, D.END_Z, D.END_X, -14.0
    if sx > 0:
        plan = [(P, Z), (M, Z), (M, Y), (X, Y), (X, S)]
    else:
        plan = [(-X, S), (-X, Y), (-M, Y), (-M, Z), (-P, Z)]
    face = offset(plan, FACE)
    fresh()
    if sx > 0:
        mid_wing(face[0], face[1], True)
        side(face[1], face[2], D.END_TOP_Y, 11.8)
        end_front(face[2], face[3], D.END_TOP_Y)
        side(face[3], face[4], D.END_TOP_Y, 11.0)
        low, high = face[:2], face[1:]
    else:
        side(face[0], face[1], D.END_TOP_Y, 11.0)
        end_front(face[1], face[2], D.END_TOP_Y)
        side(face[2], face[3], D.END_TOP_Y, 11.8)
        mid_wing(face[3], face[4], False)
        low, high = face[3:], face[:4]
    F.sweep(TRIM, face, BASE_PROFILE)
    for run, y_top in ((low, D.WING_TOP_Y), (high, D.END_TOP_Y)):
        F.sweep(TRIM, run, main_cornice_profile(D.CORNICE_Y), bands=[(6, 8, "egg"), (9, 10, "bead"), (13, 15, "leaf")])
        F.sweep(TRIM, run, top_cornice_profile(y_top))
        for p, d, nor in F.on_path(run, 0.42, 0.3):
            F.oriented_box(TRIM, p, d, nor, 0.1, 0.24, 0.4, D.CORNICE_Y + 0.02, D.CORNICE_Y + 0.26)
    # A plain block closes the end of the facade where it stops along the side wall
    W = Wall(face[3], face[4]) if sx > 0 else Wall(face[0], face[1])
    u = W.length if sx > 0 else 0.0
    a, b = (u - 0.04, u + 0.04)
    W.box(TRIM, a, b, D.PLAZA_Y, 0.02, -FACE, 0.86, skip=())
    W.box(TRIM, a, b, 0.02, D.END_TOP_Y, -FACE, 0.54, skip=())
    SECTIONS["WingE" if sx > 0 else "WingW"] = F.parts


def back_section():
    """Everything else keeps its plain walls, tied in with the same base and cornice lines."""
    fresh()
    # Start where the east front's side stops, run round the back, and stop where the west one starts
    ordered = [(152.3, 18.6), (152.3, -93.7), (141.0, -93.7), (141.0, -152.0), (87.8, -152.0), (87.8, -129.4), (17.0, -129.4), (16.0, -130.6), (16.0, -134.2), (18.6, -137.0), (28.6, -137.0),
               (28.6, -147.5), (5.5, -170.9), (-5.5, -170.9), (-28.6, -147.5), (-28.6, -137.0), (-18.6, -137.0), (-16.0, -134.2), (-16.0, -130.6), (-17.0, -129.4), (-87.8, -129.4), (-87.8, -151.5),
               (-141.0, -151.5), (-141.0, -96.0), (-152.3, -96.0), (-152.3, 18.6)]
    ordered[0] = (152.3, -14.0)
    ordered[-1] = (-152.3, -14.0)
    F.sweep(TRIM, ordered, [(0.34, D.PLAZA_Y), (0.34, -3.9), (0.17, -3.7), (0.17, -0.1), (0.26, 0.0), (0.0, 0.1)])
    F.sweep(TRIM, ordered, [(0.0, D.CORNICE_Y - 0.5), (0.06, D.CORNICE_Y - 0.5), (0.06, D.CORNICE_Y), (0.3, D.CORNICE_Y + 0.2), (0.5, D.CORNICE_Y + 0.3), (0.0, D.CORNICE_Y + 0.3)])
    F.sweep(TRIM, ordered, [(0.0, D.WING_TOP_Y - 0.5), (0.05, D.WING_TOP_Y - 0.5), (0.2, D.WING_TOP_Y - 0.25), (0.4, D.WING_TOP_Y - 0.1), (0.4, D.WING_TOP_Y + 0.05), (-0.3, D.WING_TOP_Y + 0.05)])
    # Plain arched windows along the long side walls
    for a, b in (((141.0, -96.0), (141.0, -150.0)), ((-141.0, -150.0), (-141.0, -98.0)), ((-152.3, -96.0), (-152.3, -30.0)), ((28.6, -147.5), (5.5, -170.9)), ((-5.5, -170.9), (-28.6, -147.5))):
        W = Wall(a, b)
        n = int(W.length / 11.0)
        for i in range(n):
            cu = (i + 0.5) * W.length / n
            half, sill, ys = 1.6, 1.7, 8.0
            ang = np.linspace(0, math.pi, 13)
            outline = [(cu + half, sill)] + [(cu + half * math.cos(q), ys + half * math.sin(q)) for q in ang] + [(cu - half, sill)]
            W.glass(outline, 0.04)
            rows = [[W.T(cu + r * math.cos(q), ys + r * math.sin(q), w) for q in ang] for r, w in ((half, 0.03), (half + 0.04, 0.09), (half + 0.34, 0.09), (half + 0.38, 0.0))]
            F.grid(TRIM, rows, flip=True)
            W.box(TRIM, cu - half - 0.5, cu + half + 0.5, sill - 0.24, sill, 0.0, 0.2)
            for sign in (-1, 1):
                W.box(TRIM, cu + sign * (half + 0.19) - 0.19, cu + sign * (half + 0.19) + 0.19, sill, ys, 0.0, 0.09)
    SECTIONS["BackAndSides"] = F.parts


front_section(1)
front_section(-1)
back_section()
F.export(SECTIONS, "wings")
print("DONE", flush=True)
