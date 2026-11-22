"""The Sculpture Hall's three statues (asset item P3.1), carved in plain numpy.

Each statue is a signed distance field (negative inside the stone): a smooth union of round cones and
ellipsoids for the body, small blobs for curls, displaced masses for drapery, then chips and breaks cut
out of it. Surface nets turn the field into a dense mesh, which sculpture_build.py thins and bakes in
Blender. Pure numpy, so make_sculpture_art.py can read the breaks and chips too.

Statue space is Blender's: z up, metres, the origin on the floor under the statue's own base slab, the
statue looking along -y (the game's +z). The museum plinth is added under it by the build script."""
import math

import numpy as np

TAU = 2 * math.pi


# --- Frames ---------------------------------------------------------------------------------------------

def rot(rx=0.0, ry=0.0, rz=0.0):
    """Rotation about x, then y, then z, in degrees."""
    ax, ay, az = (math.radians(a) for a in (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return z @ y @ x


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def frame(forward, up=(0, 0, 1)):
    """Columns right, forward, up (local x, y, z) for something looking along `forward`."""
    f = unit(forward)
    r = unit(np.cross(f, up))
    return np.stack([r, f, np.cross(r, f)], 1)


def frame_ru(right, up):
    """A body frame from its right direction and a rough up."""
    r = unit(right)
    u = unit(np.asarray(up, float) - r * np.dot(up, r))
    return np.stack([r, np.cross(u, r), u], 1)


class Frame:
    """A local space: p(local) gives the world point, R the orientation."""

    def __init__(self, origin, R, scale=1.0):
        self.o = np.asarray(origin, float)
        self.R = np.asarray(R, float)
        self.s = scale

    def p(self, local):
        return self.o + self.R @ (np.asarray(local, float) * self.s)

    def d(self, local):
        return self.R @ unit(local)


# --- Shapes ----------------------------------------------------------------------------------------------

def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


class Shape:
    def local(self, P):
        return (P - self.c) @ self.R


class Ellipsoid(Shape):
    def __init__(self, c, r, R=None):
        self.c, self.r = np.asarray(c, float), np.asarray(r, float)
        self.R = np.eye(3) if R is None else np.asarray(R, float)

    def bounds(self):
        e = np.abs(self.R) @ self.r
        return self.c - e, self.c + e

    def sdf(self, P):
        q = self.local(P) / self.r
        k0 = np.linalg.norm(q, axis=-1)
        k1 = np.linalg.norm(q / self.r, axis=-1)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def Sphere(c, r):
    return Ellipsoid(c, (r, r, r))


class RoundCone(Shape):
    """A capsule whose radius runs from ra at a to rb at b."""

    def __init__(self, a, b, ra, rb):
        self.a, self.b, self.ra, self.rb = np.asarray(a, float), np.asarray(b, float), float(ra), float(rb)

    def bounds(self):
        r = max(self.ra, self.rb)
        return np.minimum(self.a, self.b) - r, np.maximum(self.a, self.b) + r

    def sdf(self, P):
        ba = self.b - self.a
        l2 = float(ba @ ba)
        rr = self.ra - self.rb
        a2 = l2 - rr * rr
        il2 = 1.0 / l2
        pa = P - self.a
        y = pa @ ba
        z = y - l2
        xv = pa * l2 - y[..., None] * ba
        x2 = np.sum(xv * xv, -1)
        y2, z2 = y * y * l2, z * z * l2
        k = math.copysign(1.0, rr) * rr * rr * x2 if rr != 0 else np.zeros_like(x2)
        d1 = np.sqrt(x2 + z2) * il2 - self.rb
        d2 = np.sqrt(x2 + y2) * il2 - self.ra
        d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0.0)) + y * rr) * il2 - self.ra
        return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))


class RoundBox(Shape):
    def __init__(self, c, half, r=0.0, R=None):
        self.c, self.h, self.rr = np.asarray(c, float), np.asarray(half, float), float(r)
        self.R = np.eye(3) if R is None else np.asarray(R, float)

    def bounds(self):
        e = np.abs(self.R) @ self.h
        return self.c - e, self.c + e

    def sdf(self, P):
        q = np.abs(self.local(P)) - self.h + self.rr
        return np.linalg.norm(np.maximum(q, 0.0), axis=-1) + np.minimum(q.max(-1), 0.0) - self.rr


class Cylinder(Shape):
    """Along the local z axis, height h, edges rounded by `round`."""

    def __init__(self, c, r, h, round_=0.0, R=None):
        self.c, self.r, self.hh, self.rr = np.asarray(c, float), float(r), float(h) / 2, float(round_)
        self.R = np.eye(3) if R is None else np.asarray(R, float)

    def bounds(self):
        e = np.abs(self.R) @ np.array([self.r, self.r, self.hh])
        return self.c - e, self.c + e

    def sdf(self, P):
        q = self.local(P)
        dx = np.hypot(q[..., 0], q[..., 1]) - self.r + self.rr
        dz = np.abs(q[..., 2]) - self.hh + self.rr
        return np.minimum(np.maximum(dx, dz), 0.0) + np.hypot(np.maximum(dx, 0.0), np.maximum(dz, 0.0)) - self.rr


class Ring(Shape):
    """A tube of radius r round an ellipse with semi-axes (a, b) in the local xy plane."""

    def __init__(self, c, a, b, r, R=None):
        self.c, self.a, self.b, self.r = np.asarray(c, float), float(a), float(b), float(r)
        self.R = np.eye(3) if R is None else np.asarray(R, float)

    def bounds(self):
        e = np.abs(self.R) @ np.array([self.a + self.r, self.b + self.r, self.r])
        return self.c - e, self.c + e

    def sdf(self, P):
        q = self.local(P)
        e = np.sqrt((q[..., 0] / self.a) ** 2 + (q[..., 1] / self.b) ** 2) + 1e-9
        flat = np.hypot(q[..., 0], q[..., 1]) * (1 - 1 / e)
        return np.hypot(flat, q[..., 2]) - self.r


class Custom(Shape):
    """Any distance function over a known box."""

    def __init__(self, lo, hi, fn):
        self.lo, self.hi, self.fn = np.asarray(lo, float), np.asarray(hi, float), fn

    def bounds(self):
        return self.lo, self.hi

    def sdf(self, P):
        return self.fn(P)


# --- Noise -------------------------------------------------------------------------------------------------

_TABLES = {}


def noise3(P, freq, seed):
    """Smooth value noise in -1..1, from a repeating table of random numbers."""
    if seed not in _TABLES:
        _TABLES[seed] = np.random.default_rng(seed).random((64, 64, 64)).astype(np.float32)
    table = _TABLES[seed]
    q = np.asarray(P, np.float64) * freq
    i = np.floor(q).astype(np.int64)
    f = (q - i).astype(np.float32)
    u = f * f * (3 - 2 * f)
    i %= 64
    j = (i + 1) % 64
    out = np.zeros(q.shape[:-1], np.float32)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                ix = j[..., 0] if dx else i[..., 0]
                iy = j[..., 1] if dy else i[..., 1]
                iz = j[..., 2] if dz else i[..., 2]
                w = (u[..., 0] if dx else 1 - u[..., 0]) * (u[..., 1] if dy else 1 - u[..., 1]) * (u[..., 2] if dz else 1 - u[..., 2])
                out += table[ix, iy, iz] * w
    return out * 2 - 1


def fbm(P, freq, seed, octaves=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total = total + noise3(P, freq * 2 ** o, seed + o) * amp
        norm += amp
        amp *= 0.5
    return total / norm


# --- The field ------------------------------------------------------------------------------------------

class Field:
    """A distance field sampled every h metres over a box."""

    def __init__(self, lo, hi, h):
        self.lo = np.asarray(lo, float)
        self.h = float(h)
        self.n = np.ceil((np.asarray(hi, float) - self.lo) / h).astype(int) + 1
        self.d = np.full(tuple(self.n), 1.0, np.float32)

    def window(self, lo, hi):
        i0 = np.clip(np.floor((np.asarray(lo) - self.lo) / self.h).astype(int), 0, self.n)
        i1 = np.clip(np.ceil((np.asarray(hi) - self.lo) / self.h).astype(int) + 1, 0, self.n)
        if np.any(i1 <= i0):
            return None, None
        sl = tuple(slice(a, b) for a, b in zip(i0, i1))
        axes = [(self.lo[k] + self.h * np.arange(i0[k], i1[k])).astype(np.float32) for k in range(3)]
        return sl, np.stack(np.meshgrid(*axes, indexing="ij"), -1)

    def _apply(self, shape, k, fn):
        lo, hi = shape.bounds()
        pad = k + 3 * self.h
        sl, P = self.window(lo - pad, hi + pad)
        if sl is not None:
            self.d[sl] = fn(self.d[sl], shape.sdf(P).astype(np.float32))

    def add(self, shape, k=0.0):
        self._apply(shape, k, lambda a, b: smin(a, b, k))

    def cut(self, shape, k=0.0):
        self._apply(shape, k, lambda a, b: smax(a, -b, k))

    def displace(self, lo, hi, fn):
        """Adds fn(P) to the field over a box: positive pushes the surface in."""
        sl, P = self.window(lo, hi)
        if sl is not None:
            self.d[sl] += fn(P).astype(np.float32)

    def mesh(self):
        return surface_nets(self.d, self.lo, self.h)


def surface_nets(F, lo, h):
    """One vertex per cell the surface crosses, at the mean of its edge crossings; one quad per grid edge
    it crosses. Returns (vertices, quads) with outward winding. The surface must stay inside the box."""
    inside = F < 0
    nx, ny, nz = F.shape
    corners = [(i, j, k) for k in (0, 1) for j in (0, 1) for i in (0, 1)]
    count = sum(inside[i:nx - 1 + i, j:ny - 1 + j, k:nz - 1 + k].astype(np.uint8) for i, j, k in corners)
    active = (count > 0) & (count < 8)
    cells = np.argwhere(active)
    index = np.full(active.shape, -1, np.int64)
    index[active] = np.arange(len(cells))
    edges = [((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0)), ((0, 0, 1), (1, 0, 1)), ((0, 1, 1), (1, 1, 1)),
             ((0, 0, 0), (0, 1, 0)), ((1, 0, 0), (1, 1, 0)), ((0, 0, 1), (0, 1, 1)), ((1, 0, 1), (1, 1, 1)),
             ((0, 0, 0), (0, 0, 1)), ((1, 0, 0), (1, 0, 1)), ((0, 1, 0), (0, 1, 1)), ((1, 1, 0), (1, 1, 1))]
    acc = np.zeros((len(cells), 3))
    num = np.zeros(len(cells))
    ci, cj, ck = cells[:, 0], cells[:, 1], cells[:, 2]
    for a, b in edges:
        fa = F[ci + a[0], cj + a[1], ck + a[2]].astype(np.float64)
        fb = F[ci + b[0], cj + b[1], ck + b[2]].astype(np.float64)
        crossing = (fa < 0) != (fb < 0)
        t = np.where(crossing, fa / np.where(crossing, fa - fb, 1.0), 0.0)
        p = np.asarray(a, float) + t[:, None] * (np.asarray(b, float) - np.asarray(a, float))
        acc[crossing] += p[crossing]
        num[crossing] += 1
    verts = np.asarray(lo, float) + h * (cells + acc / num[:, None])

    quads = []
    ex = inside[:-1, :, :] != inside[1:, :, :]
    ex[:, 0, :] = ex[:, -1, :] = False
    ex[:, :, 0] = ex[:, :, -1] = False
    i, j, k = np.nonzero(ex)
    q = np.stack([index[i, j - 1, k - 1], index[i, j, k - 1], index[i, j, k], index[i, j - 1, k]], 1)
    flip = ~inside[i, j, k]
    q[flip] = q[flip][:, ::-1]
    quads.append(q)
    ey = inside[:, :-1, :] != inside[:, 1:, :]
    ey[0, :, :] = ey[-1, :, :] = False
    ey[:, :, 0] = ey[:, :, -1] = False
    i, j, k = np.nonzero(ey)
    q = np.stack([index[i - 1, j, k - 1], index[i - 1, j, k], index[i, j, k], index[i, j, k - 1]], 1)
    flip = ~inside[i, j, k]
    q[flip] = q[flip][:, ::-1]
    quads.append(q)
    ez = inside[:, :, :-1] != inside[:, :, 1:]
    ez[0, :, :] = ez[-1, :, :] = False
    ez[:, 0, :] = ez[:, -1, :] = False
    i, j, k = np.nonzero(ez)
    q = np.stack([index[i - 1, j - 1, k], index[i, j - 1, k], index[i, j, k], index[i - 1, j, k]], 1)
    flip = ~inside[i, j, k]
    q[flip] = q[flip][:, ::-1]
    quads.append(q)
    quads = np.concatenate(quads)
    assert (quads >= 0).all(), "the surface touches the edge of the field"
    return verts, quads


# --- Anatomy -------------------------------------------------------------------------------------------

def seg_frame(a, b, front):
    """A limb segment's frame: x across, y towards `front`, z along the bone from a to b."""
    z = unit(np.asarray(b, float) - a)
    y = unit(np.asarray(front, float) - z * np.dot(front, z))
    return np.stack([np.cross(y, z), y, z], 1)


def muscle(f, a, b, front, t, offset, radii, k):
    """An ellipsoid partway (t) along a limb, pushed `offset` metres along its (x, y) and lying along the bone."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    R = seg_frame(a, b, front)
    c = a + (b - a) * t + R[:, 0] * offset[0] + R[:, 1] * offset[1]
    f.add(Ellipsoid(c, radii, R), k)


def leg(f, hip, knee, ankle, toe, front, s=1.0, knee_front=None):
    """Thigh, knee, shin and calf, then the foot from the ankle to the ball of the toes."""
    f.add(RoundCone(hip, knee, 0.082 * s, 0.052 * s), 0.03)
    muscle(f, hip, knee, front, 0.42, (0, 0.022 * s), (0.062 * s, 0.058 * s, 0.19 * s), 0.035)       # quadriceps
    muscle(f, hip, knee, front, 0.5, (0, -0.018 * s), (0.058 * s, 0.05 * s, 0.17 * s), 0.035)        # hamstrings
    side = 1 if np.cross(unit(np.asarray(knee) - hip), front)[0] >= 0 else -1
    muscle(f, hip, knee, front, 0.2, (0.02 * s * side, 0.0), (0.05 * s, 0.05 * s, 0.12 * s), 0.03)  # adductor
    f.add(Sphere(np.asarray(knee) + unit(knee_front if knee_front is not None else front) * 0.026 * s, 0.033 * s), 0.02)
    f.add(RoundCone(knee, ankle, 0.05 * s, 0.031 * s), 0.025)
    muscle(f, knee, ankle, front, 0.28, (0, -0.026 * s), (0.046 * s, 0.045 * s, 0.11 * s), 0.03)     # calf
    foot(f, ankle, toe, front, s)


def foot(f, ankle, toe, front, s=1.0):
    ankle, toe = np.asarray(ankle, float), np.asarray(toe, float)
    along = unit(toe - ankle)
    R = seg_frame(ankle, toe, front)
    mid = ankle + (toe - ankle) * 0.55
    f.add(Sphere(ankle - along * 0.035 * s - R[:, 1] * 0.0, 0.034 * s), 0.02)                         # heel
    f.add(Ellipsoid(mid, (0.042 * s, 0.024 * s, np.linalg.norm(toe - ankle) * 0.62), R), 0.03)       # arch and instep
    f.add(Ellipsoid(toe, (0.044 * s, 0.017 * s, 0.03 * s), R), 0.015)                                 # the row of toes


def arm(f, shoulder, elbow, wrist, front, s=1.0):
    f.add(RoundCone(shoulder, elbow, 0.044 * s, 0.034 * s), 0.025)
    muscle(f, shoulder, elbow, front, 0.52, (0, 0.014 * s), (0.036 * s, 0.038 * s, 0.1 * s), 0.025)  # biceps
    muscle(f, shoulder, elbow, front, 0.45, (0, -0.016 * s), (0.04 * s, 0.036 * s, 0.11 * s), 0.025)  # triceps
    f.add(RoundCone(elbow, wrist, 0.037 * s, 0.022 * s), 0.02)
    muscle(f, elbow, wrist, front, 0.25, (0.008 * s, 0.004 * s), (0.04 * s, 0.032 * s, 0.085 * s), 0.025)  # forearm


def hand(f, wrist, tip, palm_normal, thumb_side, curl=0.4, s=1.0):
    """A hand from the wrist towards the fingertips: palm, four fingers in one curled mass, and a thumb."""
    wrist, tip = np.asarray(wrist, float), np.asarray(tip, float)
    along = unit(tip - wrist)
    n = unit(np.asarray(palm_normal, float) - along * np.dot(palm_normal, along))
    side = unit(np.cross(n, along)) * thumb_side
    knuckles = wrist + along * 0.085 * s
    f.add(Ellipsoid(wrist + along * 0.045 * s, (0.042 * s, 0.017 * s, 0.05 * s), np.stack([side, n, along], 1)), 0.012)
    bend = unit(along - n * curl)
    for k in range(4):
        base = knuckles + side * (0.027 - k * 0.018) * s
        length = (0.072, 0.08, 0.076, 0.062)[k] * s
        mid = base + along * length * 0.5
        end = mid + bend * length * 0.5
        f.add(RoundCone(base, mid, 0.0095 * s, 0.0085 * s), 0.006)
        f.add(RoundCone(mid, end, 0.0085 * s, 0.0072 * s), 0.004)
    t0 = wrist + along * 0.03 * s + side * 0.03 * s - n * 0.008 * s
    t1 = t0 + unit(along + side * 0.7 - n * 0.5) * 0.05 * s
    t2 = t1 + unit(along + side * 0.1 - n * 0.6) * 0.04 * s
    f.add(RoundCone(t0, t1, 0.014 * s, 0.011 * s), 0.01)
    f.add(RoundCone(t1, t2, 0.011 * s, 0.0085 * s), 0.005)


def torso(f, pelvis, hips, waist, chest, shoulders, neck, female, s=1.0):
    """hips and shoulders are (right, left) pairs. The pelvis and chest take their tilt from them."""
    rh, lh = (np.asarray(p, float) for p in hips)
    rs, ls = (np.asarray(p, float) for p in shoulders)
    pelvis, waist, chest, neck = (np.asarray(p, float) for p in (pelvis, waist, chest, neck))
    P = Frame(pelvis, frame_ru(rh - lh, waist - pelvis), s)
    C = Frame(chest, frame_ru(rs - ls, neck - waist), s)
    wide = 1.12 if female else 1.0
    f.add(Ellipsoid(P.p((0, 0, 0)), np.array((0.155 * wide, 0.11, 0.11)) * s, P.R), 0.04)               # pelvis
    for side in (-1, 1):
        f.add(Ellipsoid(P.p((0.068 * side * wide, -0.05, -0.045)), np.array((0.072, 0.052, 0.078)) * s * wide, P.R), 0.05)  # glutes
        f.add(Ellipsoid(P.p((0.12 * side * wide, 0.0, 0.1)), np.array((0.06, 0.085, 0.11)) * s, P.R), 0.05)  # flanks
    f.add(RoundCone(pelvis, chest, 0.12 * s * (1.04 if female else 1.0), 0.13 * s), 0.06)                   # the core
    f.add(RoundCone(chest, chest + (neck - chest) * 0.75, 0.13 * s, 0.075 * s), 0.06)
    f.add(Ellipsoid(C.p((0, 0.005, 0.085)), np.array((0.15, 0.085, 0.085)) * s, C.R), 0.05)              # upper chest
    f.add(Ellipsoid(C.p((0, 0, -0.07)), np.array((0.155, 0.11, 0.17)) * s * (0.94 if female else 1.0), C.R), 0.05)  # ribcage
    f.add(Ellipsoid(C.p((0, 0.05, -0.27)), np.array((0.105, 0.062, 0.14)) * s, C.R), 0.05)                  # belly
    for side in (-1, 1):
        f.add(Ellipsoid(C.p((0.125 * side, -0.025, -0.13)), np.array((0.06, 0.08, 0.13)) * s, C.R), 0.05)    # lats
        f.add(RoundCone(neck, (rs if side < 0 else ls), 0.058 * s, 0.045 * s), 0.05)                         # trapezius
        sh = rs if side < 0 else ls
        f.add(Ellipsoid(sh + C.R @ np.array((0.012 * side, 0.0, -0.01)) * s, np.array((0.058, 0.062, 0.07)) * s, C.R), 0.03)  # deltoid
    if female:
        for side in (-1, 1):
            f.add(Ellipsoid(C.p((0.08 * side, 0.088, -0.04)), np.array((0.06, 0.056, 0.056)) * s, C.R), 0.045)
    else:
        for side in (-1, 1):
            f.add(Ellipsoid(C.p((0.07 * side, 0.072, -0.012)), np.array((0.08, 0.032, 0.056)) * s, C.R @ rot(0, 0, -10 * side)), 0.04)  # pecs
        f.cut(Ellipsoid(C.p((0, 0.118, -0.25)), np.array((0.01, 0.014, 0.1)) * s, C.R), 0.035)               # a lean athlete's belly line
    f.cut(Ellipsoid(C.p((0, -0.108, -0.12)), np.array((0.012, 0.01, 0.12)) * s, C.R), 0.04)                 # the spine's groove
    f.add(Ellipsoid(P.p((0, -0.065, 0.03)), np.array((0.065, 0.04, 0.075)) * s, P.R), 0.05)                 # sacrum
    f.add(Ellipsoid(C.p((0, 0.095, 0.07)), np.array((0.11, 0.03, 0.025)) * s, C.R), 0.03)                   # collarbones
    f.cut(Ellipsoid(C.p((0, 0.13, 0.1)), np.array((0.025, 0.02, 0.02)) * s, C.R), 0.02)                     # the notch between them
    f.cut(Sphere(P.p((0, 0.105, 0.14)), 0.009 * s), 0.008)                                                   # navel
    return P, C


# --- Heads -----------------------------------------------------------------------------------------------
# Head units: the head is 1 tall from chin (z -0.5) to crown (z 0.5), eyes at z 0, y forward, x to its right.

def head(f, centre, forward, up, height, style):
    H = Frame(centre, frame(forward, up), height)
    e = lambda c, r, R=None: Ellipsoid(H.p(c), np.asarray(r) * height, H.R if R is None else H.R @ R)
    k = lambda u: u * height                                                # blends, in head units
    f.add(e((0, -0.06, 0.08), (0.33, 0.43, 0.42)), k(0.03))                 # cranium
    f.add(e((0, 0.22, 0.13), (0.24, 0.17, 0.2)), k(0.08))                   # forehead
    f.add(e((0, 0.12, -0.16), (0.255, 0.27, 0.34)), k(0.08))                # face
    f.add(e((0, 0.1, -0.32), (0.225, 0.25, 0.17)), k(0.08))                 # jaw
    f.add(e((0, 0.29, -0.415), (0.09, 0.075, 0.08)), k(0.05))               # chin
    for x in (-1, 1):
        f.add(e((0.18 * x, 0.22, -0.08), (0.08, 0.07, 0.07)), k(0.06))      # cheekbones
        f.add(e((0.325 * x, -0.03, -0.03), (0.04, 0.09, 0.14), rot(0, 0, 12 * x)), k(0.02))   # ears
    f.add(e((0, 0.305, 0.06), (0.24, 0.07, 0.05)), k(0.05))                 # brow
    f.add(RoundCone(H.p((0, 0.37, 0.05)), H.p((0, 0.458, -0.19)), 0.03 * height, 0.04 * height), k(0.03))  # nose
    for x in (-1, 1):
        f.add(e((0.044 * x, 0.405, -0.205), (0.034, 0.03, 0.026)), k(0.015))  # nostril wings
    f.cut(e((0, 0.45, -0.232), (0.012, 0.02, 0.012)), k(0.01))              # under the tip
    lid = 0.35 if style == "blind" else 0.0
    for x in (-1, 1):
        f.cut(e((0.13 * x, 0.39, 0.0), (0.072, 0.05, 0.044)), k(0.035))     # eye sockets
        f.add(e((0.13 * x, 0.33, -0.004), (0.062, 0.05, 0.04)), k(0.012))   # the blank eyes
        f.add(e((0.13 * x, 0.345, 0.02 - lid * 0.03), (0.066, 0.042, 0.016 + lid * 0.03)), k(0.012))  # upper lids
        f.add(e((0.13 * x, 0.345, -0.034), (0.058, 0.035, 0.01)), k(0.012))   # lower lids
    f.add(e((0, 0.385, -0.278), (0.078, 0.032, 0.024)), k(0.02))             # upper lip
    f.add(e((0, 0.375, -0.318), (0.066, 0.036, 0.026)), k(0.02))             # lower lip
    f.cut(e((0, 0.418, -0.298), (0.05 if style == "blind" else 0.07, 0.036, 0.0035 if style == "blind" else 0.0045)), k(0.008))  # between them
    for x in (-1, 1):
        f.cut(Sphere(H.p((0.074 * x, 0.37, -0.3)), 0.012 * height), k(0.012))
    f.cut(e((0, 0.4, -0.37), (0.06, 0.03, 0.02)), k(0.04))                  # under the lower lip
    if style == "blind":                                                     # an old man's brow
        f.cut(e((0, 0.36, 0.2), (0.15, 0.04, 0.009)), k(0.035))
    return H


def hair_curls(f, H, height, seed, n=90, r=0.055, hairline=0.16, back=-0.5, keep=0.36):
    """Short tight curls over the cranium, kept off the face."""
    rng = np.random.default_rng(seed)
    f.add(Ellipsoid(H.p((0, -0.08, 0.1)), np.array((0.34, 0.44, 0.415)) * height, H.R), 0.01)
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n * 3):
        z = 1 - 2 * (i + 0.5) / (n * 3)
        rad = math.sqrt(1 - z * z)
        a = golden * i
        d = np.array((math.cos(a) * rad, math.sin(a) * rad, z))
        p = np.array((0.345, 0.45, 0.425)) * d + np.array((0, -0.08, 0.1))
        if p[2] < hairline - 0.6 * max(0.0, p[1]) or (p[1] > 0.1 and p[2] < hairline + 0.12) or p[2] < back * 0.2 - 0.08 - abs(p[0]) * 0.0:
            continue
        if p[2] < 0.02 and abs(p[0]) > 0.24 and p[1] > -0.12:
            continue                                                         # leave the ears free
        if rng.random() > keep:
            continue
        rr = r * rng.uniform(0.8, 1.2) * height
        f.add(Sphere(H.p(p * 1.02), rr), 0.008 * height / 0.235)


def hair_waves(f, H, height, bun=True, fillet=True, beard=False, seed=0, hair=True):
    """Hair parted at the front and swept back in waves, with a ribbon round it and a knot behind."""
    face = Ellipsoid(H.p((0, 0.38, -0.2)), np.array((0.27, 0.3, 0.38)) * height, H.R)
    shell = Ellipsoid(H.p((0, -0.08, 0.1)), np.array((0.355, 0.465, 0.435)) * height, H.R)
    o, R, s = H.o, H.R, height

    def waves(P):
        q = ((P - o) @ R) / s
        d = smax(shell.sdf(P), -face.sdf(P), 0.02 * s)
        ang = np.arctan2(np.abs(q[..., 0]), q[..., 2] + 0.12)
        phase = ang * 18 + np.sin(q[..., 1] * 9 + q[..., 2] * 4) * 1.3 + noise3(P, 14, seed) * 0.8
        groove = 1 - np.abs(np.sin(phase))
        return d + groove * 0.012 * s + noise3(P, 70, seed + 1) * 0.002 * s

    lo, hi = shell.bounds()
    if hair:
        f.add(Custom(lo, hi, waves), 0.01 * s)
    if bun:
        c = H.p((0, -0.47, 0.03))
        knot = Ellipsoid(c, np.array((0.17, 0.13, 0.15)) * s, H.R)

        def twisted(P):
            q = ((P - c) @ R) / s
            ang = np.arctan2(q[..., 2], q[..., 0])
            rad = np.hypot(q[..., 0], q[..., 2])
            return knot.sdf(P) + (0.5 - 0.5 * np.cos(ang * 5 + rad * 40)) * 0.02 * s

        lo, hi = knot.bounds()
        f.add(Custom(lo, hi, twisted), 0.02 * s)
    if fillet:
        band = Ellipsoid(H.p((0, -0.08, 0.1)), np.array((0.365, 0.476, 0.446)) * s, H.R)
        n = H.R @ unit((0, 0.35, 0.94))
        p0 = H.p((0, -0.06, 0.24))
        lo, hi = band.bounds()
        f.add(Custom(lo, hi, lambda P: smax(np.abs(band.sdf(P)) - 0.013 * s, np.abs((P - p0) @ n) - 0.024 * s, 0.004 * s)), 0.005 * s)
    if beard:
        rng = np.random.default_rng(seed + 7)
        f.add(Ellipsoid(H.p((0, 0.18, -0.5)), np.array((0.3, 0.26, 0.27)) * s, H.R), 0.03 * s)
        for i in range(170):
            a = rng.uniform(-1.45, 1.45)
            z = rng.uniform(-0.82, -0.3)
            rr = 0.3 * math.cos(a * 0.75) * (1.0 - max(0.0, -0.62 - z) * 1.5)
            if rr <= 0.05:
                continue
            p = np.array((math.sin(a) * rr, 0.2 + math.cos(a) * rr * 0.92, z))
            if p[2] > -0.36 and abs(p[0]) < 0.12:
                continue                                                     # keep the lips clear
            top = p + np.array((0, 0.0, 0.05))
            low = p + np.array((math.sin(a) * 0.02, 0.01, -0.07))
            f.add(RoundCone(H.p(top), H.p(low), 0.038 * s, 0.022 * s), 0.012 * s)
        for x in (-1, 1):                                                    # moustache
            a = H.p((0.0 * x, 0.43, -0.245))
            b = H.p((0.1 * x, 0.42, -0.29))
            c = H.p((0.16 * x, 0.36, -0.38))
            f.add(RoundCone(a, b, 0.03 * s, 0.03 * s), 0.01 * s)
            f.add(RoundCone(b, c, 0.03 * s, 0.018 * s), 0.01 * s)


# --- Breaks, chips and the base slabs ----------------------------------------------------------------

def break_off(f, point, normal, reach, seed, rough=0.012):
    """Snaps the stone beyond a plane off, within `reach` of the point, leaving a rough fracture."""
    point, normal = np.asarray(point, float), unit(normal)
    ball = Sphere(point + normal * reach * 0.5, reach)

    def region(P):
        plane = -((P - point) @ normal) + fbm(P, 30, seed, 3) * rough
        return smax(plane, ball.sdf(P), 0.0)

    lo, hi = ball.bounds()
    f.cut(Custom(lo, hi, region), 0.0)


def chip(f, c, r, seed):
    """A small flake of stone knocked out: a lumpy blob cut away."""
    ball = Sphere(c, r)
    f.cut(Custom(*ball.bounds(), lambda P: ball.sdf(P) + noise3(P, 2.2 / r, seed) * r * 0.35), r * 0.15)


def slab(f, centre, half, seed, chips=()):
    """A roughly squared base slab: rounded, with a hand-dressed wobble to its faces."""
    box = RoundBox(centre, half, 0.012)
    lo, hi = box.bounds()
    f.add(Custom(lo - 0.01, hi + 0.01, lambda P: box.sdf(P) + fbm(P, 9, seed, 3) * 0.006 + noise3(P, 60, seed + 5) * 0.0015), 0.0)
    for c, r in chips:
        chip(f, c, r, seed + int(r * 1000))


# --- The statues --------------------------------------------------------------------------------------

SLAB_H = 0.07       # every statue stands on its own slab of this height, on the museum plinth
DETAIL = {}         # per statue: (centre, radius) of the parts that keep the most triangles when thinned


def venus(h):
    """Venus with her arms long gone: weight on her right leg, the left knee forward under the drapery
    that has slipped to her hips, her head turned a little to her left."""
    f = Field((-0.42, -0.46, -0.02), (0.42, 0.4, 1.99), h)
    z0 = SLAB_H
    J = {k: np.asarray(v) + (0, 0, z0) for k, v in {
        "r_ankle": (-0.075, 0.03, 0.075), "r_toe": (-0.09, -0.12, 0.02), "r_knee": (-0.075, -0.005, 0.5),
        "r_hip": (-0.095, 0.0, 0.935), "l_ankle": (0.1, -0.11, 0.135), "l_toe": (0.12, -0.25, 0.075),
        "l_knee": (0.095, -0.165, 0.53), "l_hip": (0.09, 0.0, 0.905), "pelvis": (0.0, 0.0, 0.94),
        "waist": (0.005, 0.015, 1.1), "chest": (0.0, 0.01, 1.3), "r_sh": (-0.172, 0.03, 1.462),
        "l_sh": (0.172, 0.03, 1.492), "neck": (0.005, 0.03, 1.535), "head": (0.014, -0.02, 1.785)}.items()}
    slab(f, (0, -0.02, z0 / 2), (0.31, 0.25, z0 / 2), 501,
         chips=[((0.3, -0.26, z0), 0.035), ((-0.29, 0.21, z0 * 0.6), 0.03), ((-0.1, -0.27, z0 * 0.9), 0.02)])
    f.add(RoundBox(J["l_ankle"] + (0.0, -0.035, -0.095), (0.085, 0.12, 0.04), 0.01), 0.005)    # the step under her left foot
    s = 0.97
    front = (0, -1, 0)
    torso(f, J["pelvis"], (J["r_hip"], J["l_hip"]), J["waist"], J["chest"], (J["r_sh"], J["l_sh"]), J["neck"], True, s)
    leg(f, J["r_hip"], J["r_knee"], J["r_ankle"], J["r_toe"], front, s * 1.05)
    leg(f, J["l_hip"], J["l_knee"], J["l_ankle"], J["l_toe"], (0, -0.4, 0.9), s * 1.05)
    f.add(RoundCone(J["neck"] - (0, 0.0, 0.02), J["head"] + (0, 0.01, -0.09), 0.056, 0.05), 0.03)  # neck
    # Her arms: only the stumps are left, the right broken above the elbow and the left at the shoulder
    for side, (point, normal, reach, seed) in BREAKS["venus"].items():
        sh = J["r_sh"] if side == "right_arm" else J["l_sh"]
        end = point + unit(normal) * 0.035
        f.add(RoundCone(sh, end, 0.046 * s, 0.041 * s), 0.025)
        muscle(f, sh, end, front, 0.5, (0, 0.006), (0.04, 0.042, 0.06), 0.025)
        break_off(f, point, normal, reach, seed)

    H = head(f, *VENUS_HEAD, "calm")
    DETAIL["venus"] = [(np.asarray(VENUS_HEAD[0]) + (0, -0.03, -0.02), 0.17)]
    hair_waves(f, H, 0.235, bun=True, fillet=False, seed=530)

    drapery(f, J, z0)
    for c, r, seed in CHIPS["venus"]:
        chip(f, c, r, seed)
    return f


def drapery(f, J, z0):
    """The cloth slipping off her hips: a twisted roll round them, then a heavy bell of cloth to the slab,
    pulled into diagonal folds by the left knee and pooling round her right foot."""
    lk = J["l_knee"] - (0, 0, z0)
    knee = Ellipsoid(lk + (0.0, -0.01, z0), (0.1, 0.11, 0.12))
    shin = RoundCone(lk + (0.0, -0.03, z0 - 0.05), (0.11, -0.2, z0 + 0.04), 0.1, 0.13)
    lo = np.array((-0.42, -0.46, z0 - 0.005))
    hi = np.array((0.42, 0.4, 0.99 + z0))

    def cloth(P):
        x, y, z = P[..., 0], P[..., 1], P[..., 2] - z0
        t = np.clip(z / 0.9, 0, 1)
        # A bell: an ellipse 0.2 x 0.15 at the hips, spreading to 0.28 x 0.24 on the slab, flared at the hem
        ax = 0.25 - 0.055 * t ** 0.9 + 0.04 * np.clip(1 - z / 0.12, 0, 1) ** 2
        ay = 0.215 - 0.065 * t ** 0.9 + 0.03 * np.clip(1 - z / 0.12, 0, 1) ** 2
        cy = -0.015 - 0.03 * (1 - t)
        e = np.sqrt((x / ax) ** 2 + ((y - cy) / ay) ** 2)
        d = (e - 1) * np.minimum(ax, ay)
        d = smin(d, knee.sdf(P), 0.1)
        d = smin(d, shin.sdf(P), 0.08)
        ang = np.arctan2(x, -(y - cy))
        down = np.clip((0.88 - z) / 0.88, 0, 1)
        wander = fbm(P * np.array((1.0, 1.0, 0.35)), 4, 610, 3) * 2.2 + np.sin(z * 3.0) * 0.4
        long_folds = np.abs(np.sin(ang * 4.5 + wander))
        fine = np.abs(np.sin(ang * 13 + wander * 1.7 + fbm(P, 9, 613, 2) * 1.5))
        # Diagonal folds from the left knee sweeping down to her right, strongest in front of the shins
        u = (x - lk[0]) * 0.8 + (z - lk[2]) * 0.6
        v = (x - lk[0]) * -0.6 + (z - lk[2]) * 0.8
        front = np.clip((-(y - cy) - 0.02) / 0.15, 0, 1)
        sweep = np.exp(-(u * u) / 0.06 - np.maximum(v, 0) ** 2 / 0.02) * front * (z < lk[2] + 0.1)
        diag = np.abs(np.sin(v * 38 + fbm(P, 7, 611, 2) * 1.8))
        amp = 0.006 + 0.03 * down
        d = d - amp * long_folds * (1 - 0.6 * sweep) - 0.008 * down * fine - 0.022 * sweep * diag
        d = d + fbm(P, 30, 612, 2) * 0.0025
        top = z - (0.9 + 0.055 * np.clip(x / 0.2, -1, 1) + 0.015 * np.sin(ang * 3))    # higher on her left
        return smax(d, top, 0.02)

    f.add(Custom(lo, hi, cloth), 0.025)
    Rr = rot(0, 9, 0)
    c = np.array((0.005, -0.005, 0.895 + z0))

    def twisted(P):
        q = (P - c) @ Rr
        a = np.arctan2(q[..., 1], q[..., 0])
        e = np.sqrt((q[..., 0] / 0.195) ** 2 + (q[..., 1] / 0.158) ** 2) + 1e-9
        flat = np.hypot(q[..., 0], q[..., 1]) * (1 - 1 / e)
        b = np.arctan2(q[..., 2], flat)
        tube = 0.03 + 0.012 * np.sin(a * 2 + 1) + 0.008 * fbm(P, 8, 614, 2)
        return np.hypot(flat, q[..., 2]) - tube - 0.008 * np.abs(np.sin(a * 4 + b * 0.8 + fbm(P, 10, 615, 2)))

    f.add(Custom(c - 0.27, c + 0.27, twisted), 0.03)
    f.add(Ellipsoid(c + (0.1, -0.135, 0.0), (0.06, 0.045, 0.05), rot(0, 0, 30)), 0.03)        # the knot at the front
    f.add(Ellipsoid(c + (0.14, -0.17, -0.12), (0.05, 0.03, 0.12), rot(0, -12, 30)), 0.04)       # its fall


def discus_thrower(h):
    """The athlete wound up to throw: bent over his right knee, the left foot dragging on its toes, the
    discus swung back high in his right hand and his head turned down. Moves towards -x."""
    f = Field((-0.58, -0.36, -0.02), (0.82, 0.36, 1.74), h)
    z0 = SLAB_H
    J = {k: np.asarray(v) + (0, 0, z0) for k, v in {
        "r_ankle": (-0.21, 0.07, 0.085), "r_toe": (-0.35, 0.06, 0.02), "r_knee": (-0.31, 0.04, 0.5),
        "r_hip": (-0.02, 0.08, 0.8), "l_hip": (0.03, -0.08, 0.81), "l_knee": (0.28, -0.1, 0.42),
        "l_ankle": (0.6, -0.08, 0.15), "l_toe": (0.5, -0.08, 0.025), "pelvis": (0.005, 0.0, 0.81),
        "waist": (-0.07, -0.005, 0.95), "chest": (-0.2, -0.02, 1.08), "neck": (-0.3, -0.03, 1.2)}.items()}
    slab(f, (0.12, 0.0, z0 / 2), (0.52, 0.21, z0 / 2), 502,
         chips=[((0.64, 0.2, z0), 0.03), ((-0.4, -0.21, z0 * 0.7), 0.035), ((0.3, 0.21, z0 * 0.8), 0.02)])
    # A Roman copy needs a prop: a tree stump against the standing leg, tied to the calf by a strut
    stump = RoundCone((-0.2, 0.17, z0), (-0.21, 0.15, z0 + 0.42), 0.065, 0.05)
    f.add(Custom(*[b + d for b, d in zip(stump.bounds(), (-0.02, 0.02))],
                 lambda P: stump.sdf(P) + (0.5 - 0.5 * np.cos(np.arctan2(P[..., 1] - 0.16, P[..., 0] + 0.2) * 9 + P[..., 2] * 6)) * 0.008
                 + fbm(P, 18, 520, 2) * 0.004), 0.015)
    f.add(RoundCone((-0.21, 0.15, z0 + 0.36), J["r_knee"] + (0.04, 0.03, -0.12), 0.022, 0.02), 0.01)
    lean = unit(J["neck"] - J["waist"])
    face_dir = unit((-0.5, -0.866, 0))
    right = unit(np.cross(face_dir, lean))
    up = unit(np.cross(right, face_dir))
    J["r_sh"] = J["chest"] + right * 0.175 + lean * 0.1
    J["l_sh"] = J["chest"] - right * 0.175 + lean * 0.1
    s = 1.0
    torso(f, J["pelvis"], (J["r_hip"], J["l_hip"]), J["waist"], J["chest"], (J["r_sh"], J["l_sh"]), J["neck"], False, s * 1.06)
    leg(f, J["r_hip"], J["r_knee"], J["r_ankle"], J["r_toe"], (-1, -0.1, 0.0), s * 1.12)
    leg(f, J["l_hip"], J["l_knee"], J["l_ankle"], J["l_toe"], (-1, 0.0, -0.3), s * 1.12, knee_front=(-0.6, 0, -0.8))
    # The discus arm swings up behind his back; the other hangs across to the right knee
    r_elbow = J["r_sh"] + unit((0.75, 0.35, 0.56)) * 0.3
    r_wrist = r_elbow + unit((0.85, 0.05, 0.52)) * 0.27
    arm(f, J["r_sh"], r_elbow, r_wrist, (0, -1, 0.2), s * 1.1)
    disc_c = r_wrist + unit((0.85, 0.05, 0.52)) * 0.06 + np.array((0.0, -0.035, 0.03))
    hand(f, r_wrist, r_wrist + unit((0.8, -0.2, 0.55)) * 0.17, (0, 1, 0), -1, 0.7, s)
    disc_R = frame_ru(unit((0.85, 0.05, 0.52)), (0, 1, 0))
    disc_R = np.stack([disc_R[:, 0], disc_R[:, 2], disc_R[:, 1]], 1)
    f.add(Cylinder(disc_c, 0.105, 0.022, 0.009, disc_R), 0.004)
    f.add(Cylinder(disc_c, 0.04, 0.036, 0.012, disc_R), 0.01)
    l_elbow = J["l_sh"] + np.array((-0.07, -0.08, -0.25))
    l_wrist = l_elbow + np.array((-0.09, 0.05, -0.24))
    arm(f, J["l_sh"], l_elbow, l_wrist, (-1, -0.3, 0.2), s * 1.1)
    hand(f, l_wrist, l_wrist + np.array((-0.03, 0.03, -0.17)), (1, 0.6, 0.2), 1, 0.35, s)
    head_c = J["neck"] + lean * 0.06 + unit((-0.35, -0.5, -0.1)) * 0.11
    f.add(RoundCone(J["neck"] - lean * 0.03, head_c + unit((0.3, 0.4, -0.85)) * 0.09, 0.062, 0.054), 0.03)
    H = head(f, head_c, (-0.42, -0.62, -0.66), (-0.62, -0.1, 0.78), 0.218, "calm")
    DETAIL["discus_thrower"] = [(head_c, 0.16), (r_wrist + unit((0.8, -0.2, 0.55)) * 0.08, 0.13), (l_wrist + (-0.015, 0.015, -0.08), 0.1)]
    hair_curls(f, H, 0.218, 540)
    for c, r, seed in CHIPS["discus_thrower"]:
        chip(f, c, r, seed)
    return f


def bust_homer(h):
    """Homer: head and shoulders on a turned socle, bearded, his blind eyes half shut, a ribbon in his
    hair and a fold of cloak over his left shoulder. The tip of his nose went long ago."""
    f = Field((-0.26, -0.24, -0.02), (0.26, 0.22, 0.7), h)
    f.add(Ellipsoid((0, 0.012, 0.262), (0.185, 0.105, 0.105)), 0.04)                # chest
    for x in (-1, 1):
        f.add(RoundCone((0.04 * x, 0.015, 0.31), (0.165 * x, 0.02, 0.275), 0.06, 0.058), 0.05)   # shoulders
        f.add(Ellipsoid((0.07 * x, -0.065, 0.262), (0.075, 0.035, 0.05)), 0.04)  # pecs
    f.add(Ellipsoid((0, -0.07, 0.318), (0.1, 0.03, 0.02)), 0.03)                   # collarbones
    f.add(RoundCone((0, 0.0, 0.29), (0.0, -0.01, 0.42), 0.064, 0.056), 0.035)      # neck
    # The classic truncation: a U curve under the chest, and a short stem down to the socle
    f.cut(Custom((-0.3, -0.25, 0.0), (0.3, 0.25, 0.4), lambda P: P[..., 2] - (0.19 + 3.2 * P[..., 0] ** 2 + 0.6 * P[..., 1] ** 2)), 0.012)
    f.add(RoundCone((0, 0.0, 0.112), (0, 0.0, 0.205), 0.052, 0.06), 0.025)
    f.add(Cylinder((0, 0, 0.022), 0.105, 0.044, 0.008), 0.0)                       # socle foot
    f.add(Ring((0, 0, 0.05), 0.088, 0.088, 0.016), 0.006)
    f.add(Cylinder((0, 0, 0.075), 0.06, 0.06, 0.006), 0.012)                       # its waist
    f.add(Cylinder((0, 0, 0.108), 0.085, 0.022, 0.006), 0.006)                     # top disc
    # The cloak: a heavy fold over the left shoulder and down across the chest
    cloak = [RoundCone((0.19, 0.03, 0.29), (0.05, -0.1, 0.16), 0.045, 0.04),
             RoundCone((0.2, 0.04, 0.3), (0.18, 0.1, 0.16), 0.05, 0.045),
             Ellipsoid((0.17, 0.0, 0.29), (0.08, 0.1, 0.05))]

    def folds(P):
        d = cloak[0].sdf(P)
        for g in cloak[1:]:
            d = smin(d, g.sdf(P), 0.04)
        along = P[..., 0] * 0.6 - P[..., 2]
        return d + (0.5 - 0.5 * np.cos(along * 70 + fbm(P, 12, 560, 2) * 2)) * 0.008

    f.add(Custom((0.0, -0.17, 0.1), (0.27, 0.17, 0.36), lambda P: smax(folds(P), 0.2 + 3.2 * P[..., 0] ** 2 - P[..., 2], 0.01)), 0.02)
    H = head(f, *HOMER_HEAD, "blind")
    DETAIL["bust_homer"] = [(np.asarray(HOMER_HEAD[0]) + (0, -0.02, -0.04), 0.2)]
    hair_curls(f, H, 0.245, 571, n=160, r=0.05, hairline=0.17, keep=0.75)
    hair_waves(f, H, 0.245, bun=False, fillet=True, beard=True, seed=570, hair=False)
    for c, r, seed in CHIPS["bust_homer"]:
        chip(f, c, r, seed)
    return f


# Where the heads sit (centre at eye level, looking along, up, height chin to crown), so the chips on
# their faces can be found from outside too.
VENUS_HEAD = ((0.014, -0.02, 1.785 + SLAB_H), (0.26, -1, -0.12), (0.06, 0.05, 1), 0.235)
HOMER_HEAD = ((0.0, -0.035, 0.53), (0.08, -1, -0.08), (0.0, 0.05, 1), 0.245)


def head_point(spec, local):
    c, fwd, up, height = spec
    return Frame(c, frame(fwd, up), height).p(local)


# The breaks and chips, where make_sculpture_art.py can find them too: the fresh stone is paler.
BREAKS = {
    "venus": {
        "right_arm": (np.array((-0.19, 0.012, 1.37 + SLAB_H)), np.array((-0.19, -0.19, -0.96)), 0.07, 591),
        "left_arm": (np.array((0.205, 0.022, 1.455 + SLAB_H)), np.array((0.62, -0.15, -0.77)), 0.07, 592),
    },
    "discus_thrower": {},
    "bust_homer": {},
}
CHIPS = {
    "venus": [(head_point(VENUS_HEAD, (0.015, 0.5, -0.2)), 0.006, 593),
              (np.array((0.21, -0.2, 0.08 + SLAB_H)), 0.03, 594), (np.array((-0.24, -0.12, 0.05 + SLAB_H)), 0.025, 595)],
    "discus_thrower": [(np.array((-0.29, -0.145, 0.62)), 0.016, 596), (np.array((0.62, -0.1, 0.06)), 0.02, 597)],
    "bust_homer": [(head_point(HOMER_HEAD, (0.0, 0.5, -0.195)), 0.016, 598), (np.array((0.08, -0.08, 0.03)), 0.02, 599)],
}

STATUES = {"venus": venus, "discus_thrower": discus_thrower, "bust_homer": bust_homer}
