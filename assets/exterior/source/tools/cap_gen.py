"""High-detail geometry for the capital, in plain numpy. Blender only loads and fuses the result.
Capital space: +Z up, front face looks along -Y, origin at the top of the necking band, metres.
Symmetry is the square's: every part is made for one face, then copied round four times."""
import math
import numpy as np

H = 1.92
TAU = 2 * math.pi


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Acc:
    """Collects triangle soup."""

    def __init__(self):
        self.V, self.F, self.n = [], [], 0

    def add(self, v, f):
        v = np.asarray(v, dtype=np.float32)
        self.V.append(v)
        self.F.append(np.asarray(f, dtype=np.int32) + self.n)
        self.n += len(v)

    def add_copy(self, v, f, angle=0.0, mirror_x=False):
        v = np.asarray(v, dtype=np.float32).copy()
        f = np.asarray(f, dtype=np.int32)
        if mirror_x:
            v[:, 0] *= -1
            f = f[:, ::-1]
        if angle:
            c, s = math.cos(angle), math.sin(angle)
            x, y = v[:, 0].copy(), v[:, 1].copy()
            v[:, 0], v[:, 1] = c * x - s * y, s * x + c * y
        self.add(v, f)

    def arrays(self):
        return np.concatenate(self.V), np.concatenate(self.F)


def rings_to_tris(rows, cols, closed=True):
    """Triangles between stacked rings of cols points."""
    i, j = np.meshgrid(np.arange(rows - 1), np.arange(cols if closed else cols - 1), indexing="ij")
    a = i * cols + j
    b = i * cols + (j + 1) % cols
    c = a + cols
    d = b + cols
    return np.concatenate([np.stack([a, b, d], -1).reshape(-1, 3), np.stack([a, d, c], -1).reshape(-1, 3)])


def cap_fan(ring_index_start, cols, centre_index, flip=False):
    a = ring_index_start + np.arange(cols)
    b = ring_index_start + (np.arange(cols) + 1) % cols
    c = np.full(cols, centre_index)
    t = np.stack([a, b, c], -1)
    return t[:, ::-1] if flip else t


def lathe(profile, segs=256):
    """Solid of revolution from (r, z) points; closed at both ends."""
    p = np.asarray(profile, dtype=np.float64)
    ang = np.linspace(0, TAU, segs, endpoint=False)
    v = np.zeros((len(p) * segs, 3))
    for i, (r, z) in enumerate(p):
        v[i * segs:(i + 1) * segs, 0] = r * np.cos(ang)
        v[i * segs:(i + 1) * segs, 1] = r * np.sin(ang)
        v[i * segs:(i + 1) * segs, 2] = z
    f = rings_to_tris(len(p), segs)
    extra = np.array([[0, 0, p[0, 1]], [0, 0, p[-1, 1]]])
    n = len(v)
    f = np.concatenate([f, cap_fan(0, segs, n, flip=True), cap_fan((len(p) - 1) * segs, segs, n + 1)])
    return np.concatenate([v, extra]), f


def blob(center, radii, n=32):
    """An ellipsoid."""
    prof = [(math.sin(a), -math.cos(a)) for a in np.linspace(0.02, math.pi - 0.02, n // 2)]
    v, f = lathe(prof, n)
    return v * np.asarray(radii) + np.asarray(center), f


def sweep(path, side, up, section, scale_w, scale_t):
    """Closed section swept along a path. section is (w, t) points; side and up give their directions."""
    path, side, up = (np.asarray(a, dtype=np.float64) for a in (path, side, up))
    sec = np.asarray(section, dtype=np.float64)
    n, m = len(path), len(sec)
    sw = np.asarray(scale_w)[:, None, None]
    st = np.asarray(scale_t)[:, None, None]
    v = path[:, None, :] + side[:, None, :] * sw * sec[None, :, 0, None] + up[:, None, :] * st * sec[None, :, 1, None]
    v = v.reshape(-1, 3)
    f = rings_to_tris(n, m)
    extra = np.stack([path[0], path[-1]])
    k = len(v)
    f = np.concatenate([f, cap_fan(0, m, k, flip=True), cap_fan((n - 1) * m, m, k + 1)])
    return np.concatenate([v, extra]), f


def normalize(a):
    return a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)


# --- Acanthus ---------------------------------------------------------------------------------
def leaf_height(spec):
    """Height of a leaf above its sheet, the big carved shapes first. Lobes run up and out from the
    midrib along curved bands; each lobe is one rounded mass that splits into three pointed fingers
    at its end, with deep grooves between lobes and an almond eye where two lobes nearly touch."""
    L, W, res = spec["L"], spec["W"], spec["res"]
    na, nb = int(2 * W / res) + 1, int(L / res) + 1
    a = np.linspace(-W, W, na, dtype=np.float32)
    s = np.linspace(0, L, nb, dtype=np.float32)
    A, S = np.meshgrid(a, s)
    X, Y = np.abs(A) / W, S / L
    q = Y - (spec["rise"] * X + spec["rise2"] * X * X)
    h1, h2 = spec["h1"], spec["h2"]
    Hh = np.zeros_like(X)
    T = np.zeros_like(X)                 # how far out along its lobe each point is, 0 at the rib
    Eo = np.zeros_like(X)                # signed position across the lobe, for the shingle tilt
    mw = spec["mw"] * (1 - 0.62 * Y)     # half width of the midrib
    for q0, q1, reach in spec["lobes"]:
        band = (q >= q0) & (q < q1)
        e = 2 * (q - q0) / (q1 - q0) - 1
        p = (e + 1) / 2 * 3
        e3 = (p % 1.0) * 2 - 1
        rr = reach * (1 - 0.26 * np.abs(e) ** 3)
        R = rr * (1.0 - spec["serr"] * np.abs(e3) ** 1.3)
        t = X / np.maximum(R, 1e-3)
        keep = band & (t < 1)
        body = np.sqrt(np.maximum(1 - np.abs(e) ** 2.6, 0))
        fing = np.sqrt(np.maximum(1 - np.abs(e3) ** 2, 0))
        mix = sstep(0.34, 0.74, t)
        groove = 1.0 - spec["vgroove"] * np.exp(-(e3 / 0.20) ** 2) * sstep(0.45, 0.8, t)
        prof = (body * (1 - mix) + fing * np.sqrt(body) * mix) * groove
        rim = np.sqrt(np.clip((1 - t) / 0.2, 0, 1))
        val = h1 * prof * rim * (1.0 - 0.28 * t)
        # the almond eye between lobes
        eye = (1 - np.abs(e)) / 0.20 + ((t - 0.46) / 0.20) ** 2
        val = val * np.sqrt(np.clip((eye - 1.0) / 0.7, 0, 1))
        Hh[keep] = val[keep]
        T[keep] = t[keep]
        Eo[keep] = e[keep]
    # The tip of the leaf narrows and closes
    tipw = np.where(Y > 0.80, 0.86 * np.sqrt(np.maximum(1 - ((Y - 0.80) / 0.20) ** 2, 0)), 9.0)
    Hh = Hh * np.sqrt(np.clip((tipw - X) / 0.10, 0, 1))
    # Lobes dip into a channel beside the rib, and the rib stands proud
    Hh = Hh * (0.55 + 0.45 * sstep(0.8, 2.0, X / np.maximum(mw, 1e-3)))
    rib = h2 * np.sqrt(np.maximum(1 - (X / np.maximum(mw, 1e-3)) ** 2, 0)) * (1 - 0.35 * Y) * sstep(0.0, 0.16, Y) * (Y < 0.985)
    Hh = np.maximum(Hh, rib)
    # a low body under the lobes at the foot of the leaf, so it grows from the bell, not from a post
    foot = 0.016 * (1 - sstep(0.10, 0.40, Y)) * np.clip((0.62 - X) / 0.2, 0, 1) * sstep(0.0, 0.05, Y)
    Hh = np.maximum(Hh, foot)
    return a, s, Hh, T, Eo


def build_leaf(spec):
    """A leaf as a closed solid, standing at angle 0 (front), in capital space."""
    a, s, h, t_out, e_lobe = leaf_height(spec)
    # Seal the grid's outer edge so the solid is watertight; the fusing step needs that
    h[0, :] = h[-1, :] = 0.0
    h[:, 0] = h[:, -1] = 0.0
    L, W = spec["L"], spec["W"]
    u = s / L
    phi = np.radians(spec["phi0"] + (spec["phi1"] - spec["phi0"]) * sstep(0.2, 0.7, u)
                     + spec["curl"] * sstep(spec["curl_at"], 1.0, u) ** 1.5)
    ds = s[1] - s[0]
    rs = spec["r0"] + np.concatenate([[0], np.cumsum(np.sin(phi[:-1]))]) * ds
    zs = spec["z0"] + np.concatenate([[0], np.cumsum(np.cos(phi[:-1]))]) * ds
    nr, nz = np.cos(phi), -np.sin(phi)
    A = a[None, :]
    X = np.abs(A) / W
    flare = spec["flare"] * X ** 2 * sstep(0.10, 0.6, u)[:, None]
    # each lobe lies over the next like a shingle, which gives every lobe its own edge of shadow
    tile = spec["tile"] * e_lobe * t_out
    roll = spec["roll"] * sstep(0.5, 1.0, u)[:, None] * X ** 1.5

    def pos(dn):
        R = rs[:, None] + dn * nr[:, None]
        Z = zs[:, None] + dn * nz[:, None] - roll
        th = A / np.maximum(rs[:, None], 0.3) * spec.get("wrap", 1.0)
        return np.stack([R * np.sin(th), -R * np.cos(th), Z], -1)

    solid = np.clip(h / 0.012, 0, 1)
    thick = spec["thick"] * sstep(spec["curl_at"] - 0.06, spec["curl_at"] + 0.14, u)[:, None] * solid
    skin = spec["skin"] * solid
    top = pos(flare + tile * solid + h + skin)
    bot = pos(flare + tile * solid - 0.55 * h - thick - skin)
    inside = h > 1e-4
    used = inside.copy()
    used[1:, :] |= inside[:-1, :]
    used[:-1, :] |= inside[1:, :]
    used2 = used.copy()
    used2[:, 1:] |= used[:, :-1]
    used2[:, :-1] |= used[:, 1:]
    used = used2
    idx_top = -np.ones_like(inside, dtype=np.int64)
    count = int(used.sum())
    idx_top[used] = np.arange(count)
    idx_bot = idx_top.copy()
    n_in = int(inside.sum())
    idx_bot[inside] = count + np.arange(n_in)
    verts = np.concatenate([top[used], bot[inside]])
    cell = used[:-1, :-1] & used[1:, :-1] & used[:-1, 1:] & used[1:, 1:]
    cell &= inside[:-1, :-1] | inside[1:, :-1] | inside[:-1, 1:] | inside[1:, 1:]
    q = lambda id_: (id_[:-1, :-1][cell], id_[:-1, 1:][cell], id_[1:, 1:][cell], id_[1:, :-1][cell])
    t0, t1, t2, t3 = q(idx_top)
    b0, b1, b2, b3 = q(idx_bot)
    faces = np.concatenate([np.stack([t0, t1, t2], -1), np.stack([t0, t2, t3], -1),
                            np.stack([b0, b2, b1], -1), np.stack([b0, b3, b2], -1)])
    return verts, faces


# (q start, q end, reach across the half width) from the bottom of the leaf to the tip
LOBES_LOW = [(0.02, 0.21, 0.66), (0.21, 0.41, 1.0), (0.41, 0.60, 1.0), (0.60, 0.78, 0.92), (0.78, 1.0, 0.66)]
LOBES_HIGH = [(0.02, 0.30, 0.34), (0.30, 0.47, 0.60), (0.47, 0.63, 1.0), (0.63, 0.80, 1.0), (0.80, 1.0, 0.70)]
LOBES_SPROUT = [(0.05, 0.34, 0.64), (0.34, 0.62, 1.0), (0.62, 1.0, 0.72)]
LOBES_CALYX = [(0.05, 0.30, 0.80), (0.30, 0.58, 1.0), (0.58, 1.0, 0.6)]


def specs(res):
    common = dict(res=res, rise=0.30, rise2=0.34, serr=0.26, mw=0.085, tile=0.024, wrap=1.0, skin=0.009, vgroove=0.42)
    low = dict(common, L=0.86, W=0.335, lobes=LOBES_LOW, r0=0.715, z0=0.02, phi0=3, phi1=17, curl=128, curl_at=0.68,
               flare=0.075, roll=0.10, h1=0.056, h2=0.040, thick=0.055)
    high = dict(common, L=1.27, W=0.40, lobes=LOBES_HIGH, r0=0.70, z0=0.02, phi0=2, phi1=12, curl=128, curl_at=0.74,
                flare=0.085, roll=0.11, h1=0.062, h2=0.044, thick=0.065)
    calyx = dict(common, L=0.46, W=0.205, lobes=LOBES_CALYX, r0=0.815, z0=0.86, phi0=10, phi1=30, curl=95, curl_at=0.62,
                 flare=0.05, roll=0.015, h1=0.034, h2=0.036, thick=0.03, mw=0.12)
    sprout = dict(common, L=0.60, W=0.20, lobes=LOBES_SPROUT, r0=0.84, z0=1.03, phi0=4, phi1=14, curl=95, curl_at=0.64,
                  flare=0.05, roll=0.015, h1=0.036, h2=0.030, thick=0.03, mw=0.10)
    return low, high, calyx, sprout


# --- Scrolls ----------------------------------------------------------------------------------
RIBBON = [(-1.0, -1.0), (-1.0, 1.0), (-0.34, 1.0), (-0.26, 0.74), (0.26, 0.74), (0.34, 1.0), (1.0, 1.0), (1.0, 0.56),
          (0.74, 0.34), (0.74, -0.34), (1.0, -0.56), (1.0, -1.0)]


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + (t ** 3) * p3


def scroll(start, eye, rho0, rho1, turns, hand, depth0, depth1, band0, band1, thick0, thick1, lift=0.34, approach=0.22, n=420):
    """A ribbon that climbs from behind the leaves and rolls up into a spiral. Plane coordinates are
    (X sideways, Z up); depth is how far forward of the capital's axis the ribbon sits."""
    eye = np.asarray(eye, dtype=np.float64)
    start = np.asarray(start, dtype=np.float64)
    top = eye + np.array([0.0, rho0])
    sgn = float(hand)
    n_rise = n // 3
    rise = bezier(start, start + np.array([0.0, lift]), top - np.array([sgn * approach, 0.0]), top, n_rise)
    ang = np.linspace(0, turns * TAU, n - n_rise + 1)[1:]
    b = math.log(rho0 / rho1) / (turns * TAU)
    rho = rho0 * np.exp(-b * ang)
    spiral = np.stack([eye[0] + rho * np.sin(sgn * ang), eye[1] + rho * np.cos(ang)], -1)
    xz = np.concatenate([rise, spiral])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(xz, axis=0), axis=1))])
    u = s / s[-1]
    rise_end = s[n_rise - 1] / s[-1]
    depth = depth0 + (depth1 - depth0) * sstep(0.0, rise_end, u)
    path = np.stack([xz[:, 0], -depth, xz[:, 1]], -1)
    tang = normalize(np.gradient(path, axis=0))
    side = np.tile(np.array([0.0, -1.0, 0.0]), (len(path), 1))        # the band's width runs front to back
    up = normalize(np.cross(tang, side)) * (-sgn)                     # faces away from the eye of the spiral
    band = band0 + (band1 - band0) * sstep(0.1, 1.0, u)
    thick = thick0 + (thick1 - thick0) * sstep(0.1, 0.8, u)
    return sweep(path, side, up, RIBBON, band / 2, thick / 2)


def disc_y(x, z, depth0, depth1, radius, n=64):
    """A short solid cylinder between two depths, the mass a spiral is carved from."""
    v, f = lathe([(0.0, depth0), (radius, depth0), (radius, depth1), (0.0, depth1)], n)
    return np.stack([v[:, 0] + x, -v[:, 2], v[:, 1] + z], -1), f[:, ::-1]


D_AXIS = np.array([1.0, -1.0, 0.0]) / math.sqrt(2)      # out along the corner of the front-right quarter
N_AXIS = np.array([-1.0, -1.0, 0.0]) / math.sqrt(2)     # from the diagonal plane towards the front face
Z_AXIS = np.array([0.0, 0.0, 1.0])


def corner_scroll(start, eye_r, eye_z, off, rho0, rho1, turns, band0, band1, thick0, thick1, lift, approach, n=520):
    """A ribbon from the front face out to the corner. It turns towards the diagonal as it climbs and
    rolls up in a plane facing across the diagonal, so that the two scrolls meeting at a corner sit
    back to back, the way they do on real capitals."""
    start = np.asarray(start, dtype=np.float64)
    eye = D_AXIS * eye_r + N_AXIS * off + Z_AXIS * eye_z
    top = eye + Z_AXIS * rho0
    n_rise = n // 3
    rise = bezier(start, start + Z_AXIS * lift, top - D_AXIS * approach, top, n_rise)
    ang = np.linspace(0, turns * TAU, n - n_rise + 1)[1:]
    b = math.log(rho0 / rho1) / (turns * TAU)
    rho = rho0 * np.exp(-b * ang)
    spiral = eye + np.outer(rho * np.sin(ang), D_AXIS) + np.outer(rho * np.cos(ang), Z_AXIS)
    path = np.concatenate([rise, spiral])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    u = s / s[-1]
    rise_end = s[n_rise - 1] / s[-1]
    tang = normalize(np.gradient(path, axis=0))
    w = sstep(0.0, rise_end, u)[:, None]
    ref = normalize((1 - w) * np.array([0.0, -1.0, 0.0]) + w * N_AXIS)
    side = normalize(ref - tang * np.sum(ref * tang, axis=1, keepdims=True))
    up = -normalize(np.cross(tang, side))
    band = band0 + (band1 - band0) * sstep(0.1, 1.0, u)
    thick = thick0 + (thick1 - thick0) * sstep(0.1, 0.8, u)
    return sweep(path, side, up, RIBBON, band / 2, thick / 2)


def disc_axis(center, axis, d0, d1, radius, n=64):
    """A short solid cylinder along any axis."""
    axis = np.asarray(axis, dtype=np.float64)
    a = normalize(np.cross(axis, Z_AXIS))
    b = np.cross(axis, a)
    v, f = lathe([(0.0, d0), (radius, d0), (radius, d1), (0.0, d1)], n)
    out = np.outer(v[:, 0], a) + np.outer(v[:, 1], b) + np.outer(v[:, 2], axis) + np.asarray(center)
    return out, f


# --- Abacus -----------------------------------------------------------------------------------
def abacus_outline(offset=0.0, half=1.25, sag=0.22, chamfer=0.12, n=64):
    """Concave-sided square with cut corners, one closed loop. Offset grows the whole shape."""
    half = half + offset
    pts = []
    for q in range(4):
        side = []
        for i in range(n + 1):
            t = i / n
            x = -half + chamfer + t * (2 * half - 2 * chamfer)
            y = -half + sag * (1 - (2 * t - 1) ** 2)
            side.append((x, y))
        c, s = math.cos(q * math.pi / 2), math.sin(q * math.pi / 2)
        pts += [(c * x - s * y, s * x + c * y) for x, y in side]
    return np.array(pts)


def abacus():
    prof = [(1.645, -0.20), (1.665, -0.20), (1.675, -0.15), (1.70, -0.10), (1.74, -0.055), (1.785, -0.03), (1.80, 0.0),
            (1.845, 0.0), (1.852, 0.03), (1.89, 0.075), (1.905, 0.085), (H, 0.085)]
    loops = []
    for z, o in prof:
        p = abacus_outline(o)
        loops.append(np.concatenate([p, np.full((len(p), 1), z)], 1))
    cols = len(loops[0])
    v = np.concatenate(loops)
    f = rings_to_tris(len(loops), cols)
    extra = np.array([[0, 0, prof[0][0]], [0, 0, prof[-1][0]]])
    k = len(v)
    f = np.concatenate([f, cap_fan(0, cols, k, flip=True), cap_fan((len(loops) - 1) * cols, cols, k + 1)])
    return np.concatenate([v, extra]), f


# --- The owl in the flower --------------------------------------------------------------------
def fleuron(acc):
    """The big round flower of the real capitals, with a small owl's face looking out of it."""
    c = np.array([0.0, -1.075, 1.745])
    for ring, (rr, count, size) in enumerate(((0.165, 12, 0.062), (0.105, 9, 0.05))):
        for i in range(count):
            a = TAU * (i + 0.5 * ring) / count
            p = c + np.array([rr * math.cos(a), 0.015 * ring, rr * math.sin(a)])
            v, f = blob([0, 0, 0], (size * 0.8, size * 0.55, size * 1.25), 28)
            ca, sa = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2)
            x, z = v[:, 0].copy(), v[:, 2].copy()
            v[:, 0], v[:, 2] = ca * x - sa * z, sa * x + ca * z
            acc.add(v + p, f)
    for sx in (-1, 1):
        acc.add(*blob(c + [sx * 0.058, -0.045, 0.012], (0.062, 0.03, 0.062), 32))   # facial disc
        acc.add(*blob(c + [sx * 0.056, -0.07, 0.016], (0.024, 0.016, 0.024), 24))   # eye
        acc.add(*blob(c + [sx * 0.05, -0.058, 0.082], (0.03, 0.02, 0.05), 20))      # ear tuft
    acc.add(*blob(c + [0, -0.078, -0.022], (0.016, 0.022, 0.034), 20))              # beak
    acc.add(*blob(c + [0, -0.03, 0.0], (0.10, 0.04, 0.10), 32))                     # head behind


def scroll_of_papyrus(acc):
    """A small tied scroll tucked across the stem, the second hidden detail."""
    c = np.array([0.0, -0.93, 1.13])
    v, f = lathe([(0, -0.12), (0.036, -0.12), (0.042, -0.105), (0.036, -0.09), (0.036, 0.09), (0.042, 0.105), (0.036, 0.12), (0, 0.12)], 48)
    acc.add(np.stack([v[:, 2], v[:, 1], v[:, 0]], -1) + c, f[:, ::-1])
    v, f = lathe([(0, -0.016), (0.043, -0.016), (0.043, 0.016), (0, 0.016)], 48)
    acc.add(np.stack([v[:, 2], v[:, 1], v[:, 0]], -1) + c, f[:, ::-1])


def build(res=0.004):
    acc = Acc()
    low, high, calyx, sprout = specs(res)
    lv, lf = build_leaf(low)
    hv, hf = build_leaf(high)
    cv, cf = build_leaf(calyx)
    sv, sf = build_leaf(sprout)
    # Bell
    acc.add(*lathe([(0.0, 0.0), (0.70, 0.0), (0.70, 0.3), (0.72, 0.7), (0.76, 1.05), (0.83, 1.36), (0.90, 1.52), (0.975, 1.625),
                    (1.0, 1.655), (0.86, 1.70), (0.0, 1.70)], 256))
    # Necking band under the leaves
    acc.add(*lathe([(0.0, -0.13), (0.72, -0.13), (0.745, -0.115), (0.77, -0.085), (0.775, -0.05), (0.76, -0.015), (0.725, 0.0),
                    (0.705, 0.03), (0.0, 0.03)], 256))
    for q in range(4):
        rot = q * math.pi / 2
        acc.add_copy(lv, lf, rot)                                                       # lower leaf on the axis
        acc.add_copy(lv, lf, rot + math.pi / 4)                                         # lower leaf on the diagonal
        acc.add_copy(hv, hf, rot + math.pi / 8)                                         # upper leaves between
        acc.add_copy(hv, hf, rot - math.pi / 8)

    # One face's scrolls and flower, then copied
    face = Acc()
    for mirror in (False, True):
        side = Acc()
        sx, sz = 0.39, 0.98                                      # scrolls spring from here, behind the upper leaves
        side.add(*blob((sx, -0.80, sz), (0.10, 0.09, 0.08), 32))
        band = 0.115
        eye_r, eye_z = 1.235, 1.44
        side.add(*corner_scroll((sx + 0.03, -0.82, sz), eye_r, eye_z, band / 2 + 0.005, 0.215, 0.026, 2.35, 0.16, band, 0.125, 0.030,
                                lift=0.30, approach=0.42))
        c3 = D_AXIS * eye_r + Z_AXIS * eye_z
        side.add(*disc_axis(c3, N_AXIS, -0.01, band - 0.018, 0.205))
        side.add(*blob(c3 + N_AXIS * (band + 0.012), (0.042, 0.042, 0.042), 28))
        eye2 = (0.195, 1.465)
        side.add(*scroll((sx - 0.04, sz), eye2, 0.15, 0.022, 2.0, -1, 0.82, 0.965, 0.16, 0.11, 0.105, 0.024, lift=0.24, approach=0.06))
        side.add(*disc_y(eye2[0], eye2[1], 0.78, 0.945, 0.135))
        side.add(*blob((eye2[0], -1.01, eye2[1]), (0.03, 0.035, 0.03), 24))
        # small leaves wrapping where the two scrolls part
        cang = math.atan2(sx, 0.84)
        side.add_copy(cv, cf, cang + 0.16)
        side.add_copy(cv, cf, cang - 0.20)
        v, f = side.arrays()
        face.add_copy(v, f, 0.0, mirror)
    fleuron(face)
    scroll_of_papyrus(face)
    # a small leaf rising up the axis to carry the flower
    face.add(sv, sf)
    v, f = face.arrays()
    for q in range(4):
        acc.add_copy(v, f, q * math.pi / 2)
    acc.add(*abacus())
    return acc.arrays()
