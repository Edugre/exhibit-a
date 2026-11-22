"""A century of weather on the front: one map, laid across the whole pavilion like a stencil, so no two
columns or bays age alike. Dark soot gathers where rain can't reach; pale streaks run where it does.
In the four niches, clean silhouettes show where statues stood until they were taken away.
Stored at two thirds of the true value, so it can brighten as well as darken.
usage: python make_stain.py <out dir>"""
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ext_dims as D

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
X0, Y0, MW, MH = -32.0, -5.0, 64.0, 36.0
W, H = 2048, 1152
PPM = W / MW
rng = np.random.default_rng(11)


def col(x):
    return int((x - X0) * PPM)


def row(y):
    return int((Y0 + MH - y) * PPM)


def noise1d(n, scale):
    """Smooth noise along a line, 0 to 1."""
    k = max(int(n / scale), 4)
    v = rng.random(k + 2)
    return np.interp(np.arange(n) / n * k, np.arange(k + 2), v)


def noise2d(sigma):
    a = rng.random((H, W), dtype=np.float32)
    a = gaussian_filter(a, sigma, mode="wrap")
    return (a - a.min()) / (a.max() - a.min())


S = np.ones((H, W), dtype=np.float32)
ys = np.arange(H)
y_world = Y0 + MH - (ys + 0.5) / PPM


def ledge(x0, x1, y, dark, reach, wash=0.0):
    """Soot under a ledge, thinning downwards, broken into runs where the rain drips off it."""
    a, b = max(col(x0), 0), min(col(x1), W)
    if b <= a:
        return
    n = b - a
    drip = noise1d(n, 11) * 0.55 + noise1d(n, 3.5) * 0.45
    drip = np.clip((drip - 0.25) / 0.6, 0, 1)
    below = np.maximum(y - y_world, 0)
    above = y_world <= y
    for i in range(n):
        length = reach * (0.35 + 2.1 * drip[i] ** 2)
        fall = np.exp(-below / length) * above
        S[:, a + i] *= 1 - dark * (0.45 + 0.55 * drip[i]) * fall
        if wash:
            # a clean pale line where the run of water is strongest
            S[:, a + i] *= 1 + wash * max(drip[i] - 0.72, 0) * 3 * np.exp(-below / (length * 1.5)) * above


# The great overhangs throw a band of soot on everything under them
ledge(-30.4, 30.4, D.ATTIC_TOP_Y - 0.6, 0.30, 0.9, 0.10)
ledge(-30.4, 30.4, D.COL_TOP_Y + 3.1, 0.44, 0.7, 0.08)
ledge(-30.4, 30.4, D.COL_TOP_Y + 1.25, 0.20, 0.9, 0.10)
ledge(-30.4, 30.4, D.COL_TOP_Y, 0.46, 2.4, 0.14)
for cx in D.ARCHES_X:
    half = D.ARCH_W / 2
    ledge(cx - half - 0.9, cx + half + 0.9, D.ARCH_SPRING_Y + 0.1, 0.30, 1.6, 0.10)
    ledge(cx - half, cx + half, D.TRANSOM_Y - 0.7, 0.34, 1.5, 0.12)
    ledge(cx - 3.0, cx + 3.0, 4.5, 0.26, 1.0)
for px in D.PAIRS_X:
    ledge(px - 2.9, px + 2.9, D.PED_Y - 0.2, 0.30, 1.0, 0.12)
ledge(-30.4, 30.4, -0.7, 0.30, 1.2, 0.10)

# Rising damp and splash at the foot of every wall, and the great floods of the street below
S *= 1 - 0.26 * np.exp(-np.maximum(y_world - 0.0, 0) / 0.9)[:, None] * (y_world > 0)[:, None]
S *= 1 - 0.34 * np.exp(-np.maximum(y_world + 4.5, 0) / 0.8)[:, None]

# Slow patches over the whole surface, like old repairs and differences in the stone
S *= 0.93 + 0.14 * noise2d(40)
S *= 0.97 + 0.06 * noise2d(9)

# The top of the attic and the blocks catch the rain and stay washed
S *= 1 + 0.10 * np.clip((y_world - 24.5) / 4, 0, 1)[:, None]

# Niches: dirty hollows with a clean ghost in each one
ghost = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(ghost)


def figure(cx, y0, h, pose):
    """A standing draped figure in outline. Unit coordinates: x across, y up."""
    def q(pts):
        return [(col(cx + x * h), row(y0 + y * h)) for x, y in pts]

    body = [(-0.09, 0.0), (0.09, 0.0), (0.10, 0.22), (0.07, 0.42), (0.11, 0.62), (0.10, 0.74), (0.045, 0.80), (0.05, 0.86), (0.035, 0.93), (-0.035, 0.93), (-0.05, 0.86), (-0.045, 0.80),
            (-0.10, 0.74), (-0.11, 0.62), (-0.07, 0.42), (-0.10, 0.22)]
    d.polygon(q(body), fill=255)
    if pose == "spear":
        d.polygon(q([(0.14, 0.0), (0.155, 0.0), (0.155, 0.98), (0.17, 0.92), (0.147, 1.02), (0.125, 0.92), (0.14, 0.98)]), fill=255)
        d.polygon(q([(0.10, 0.72), (0.15, 0.62), (0.16, 0.66), (0.11, 0.76)]), fill=255)
        d.ellipse([col(cx - 0.20 * h), row(y0 + 0.58 * h), col(cx - 0.02 * h), row(y0 + 0.40 * h)], fill=255)   # shield
    elif pose == "staff":
        d.polygon(q([(-0.15, 0.0), (-0.135, 0.0), (-0.135, 0.86), (-0.15, 0.86)]), fill=255)
        d.polygon(q([(-0.10, 0.72), (-0.15, 0.60), (-0.135, 0.58), (-0.08, 0.68)]), fill=255)
    elif pose == "book":
        d.polygon(q([(-0.10, 0.70), (-0.13, 0.52), (0.13, 0.52), (0.10, 0.70)]), fill=255)
        d.polygon(q([(-0.13, 0.58), (0.13, 0.58), (0.13, 0.50), (-0.13, 0.50)]), fill=255)
    else:
        d.polygon(q([(0.10, 0.72), (0.20, 0.82), (0.18, 0.85), (0.08, 0.76)]), fill=255)


for x, y0, y1, half, h, pose in ((-27.2, 2.5, 13.0, 0.95, 6.6, "staff"), (-21.0, 4.4, 10.3, 0.68, 4.2, "spear"), (21.0, 4.4, 10.3, 0.68, 4.2, "raised"), (27.2, 2.5, 13.0, 0.95, 6.6, "book")):
    a, b = col(x - half), col(x + half)
    t, u = row(y1), row(y0)
    S[t:u, a:b] *= 0.72
    figure(x, y0, h, pose)
g = np.asarray(ghost.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(1.2)), dtype=np.float32) / 255
S = S * (1 - g) + np.minimum(S * 1.62, 1.30) * g

Image.fromarray((np.clip(S / 1.5, 0, 1) * 255).astype(np.uint8)).save(OUT / "ext_stain.png", optimize=True)
print("stain written", round(float(S.min()), 2), round(float(S.max()), 2))
