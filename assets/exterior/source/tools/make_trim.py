"""The carved moulding strip: egg-and-dart, bead-and-reel, a leaf cyma and rosette panels, drawn as
height fields in numpy, then turned into normal and occlusion maps. Each row repeats sideways, so it
can run along any cornice or arch. usage: python make_trim.py <out dir> [size]"""
import pathlib
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
SS = 2                      # drawn at twice the size, then reduced, for clean edges
S = N * SS
METRES_PER_U = 1.2          # one texture width covers 1.2 m of moulding

# Rows of the strip, as fractions of the height, top down in image space
ROWS = dict(egg=(0.00, 0.25), bead=(0.25, 0.375), leaf=(0.375, 0.70), rosette=(0.70, 1.00))


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def cell(count, h):
    """u across one repeat, -1 to 1; v down the row, 0 at the top, 1 at the bottom."""
    w = S
    x = (np.arange(w) + 0.5) / w * count
    u = (x % 1.0) * 2 - 1
    v = (np.arange(h) + 0.5) / h
    return np.meshgrid(u, v)


def smax(a, b, k=0.04):
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0, 1)
    return a * h + b * (1 - h) + k * h * (1 - h)


def egg_and_dart(h):
    u, v = cell(4, h)                       # four eggs in 1.2 m
    y = v * 2 - 1
    # the egg, a dome, fatter at the top
    eu, ev = u / 0.60, (y + 0.06) / (0.80 - 0.10 * y)
    r = np.sqrt(eu * eu + ev * ev)
    egg = np.sqrt(np.maximum(1 - r * r, 0)) * 0.95
    # the shell around it, a raised rim cut away at the bottom
    su, sv = u / 0.86, (y + 0.02) / 1.02
    sr = np.sqrt(su * su + sv * sv)
    rim = np.exp(-((sr - 0.86) / 0.075) ** 2) * 0.62 * sstep(0.95, 0.25, y)
    # the dart between shells
    du = (1 - np.abs(u)) / 0.18
    dart = np.maximum(1 - du / np.maximum(1.0 - sstep(-0.9, 0.95, y) * 0.92, 0.05), 0) * 0.6 * (y > -0.85) * (y < 0.9)
    flat = 0.12 + 0.18 * (y < -0.88)
    return np.maximum.reduce([egg, rim, dart, np.full_like(u, flat) if False else flat * np.ones_like(u)])


def bead_and_reel(h):
    u, v = cell(8, h)
    y = v * 2 - 1
    # a long bead with two thin discs after it
    pos = (u + 1) / 2
    bead = np.sqrt(np.maximum(1 - ((pos - 0.36) / 0.34) ** 2 - (y / 0.82) ** 2, 0))
    disc = np.zeros_like(u)
    for c in (0.80, 0.92):
        disc = np.maximum(disc, np.sqrt(np.maximum(1 - ((pos - c) / 0.05) ** 2 - (y / 0.95) ** 2, 0)) * 0.9)
    return np.maximum.reduce([bead, disc, 0.06 * np.ones_like(u)])


def leaf_cyma(h):
    u, v = cell(5, h)
    y = v
    # a pointed water leaf, tip downwards, with a raised rib and a turned edge
    width = 0.92 * np.sqrt(np.clip(1 - y, 0, 1)) * (0.55 + 0.45 * sstep(0.0, 0.3, y))
    inside = np.abs(u) / np.maximum(width, 0.02)
    body = np.sqrt(np.maximum(1 - inside ** 2, 0)) * (y < 0.98) * sstep(0.0, 0.06, y)
    rib = np.exp(-(u / 0.06) ** 2) * (1 - y * 0.6) * 0.22
    edge = np.exp(-((inside - 0.86) / 0.07) ** 2) * 0.22 * (y < 0.9)
    groove = np.exp(-((inside - 0.5) / 0.08) ** 2) * 0.14
    leaf = body * 0.68 + rib + edge - groove * body
    # a tongue rising between the leaves
    tu = (1 - np.abs(u)) / 0.22
    tongue = np.maximum(1 - tu, 0) * sstep(0.95, 0.2, y) * 0.55
    return np.maximum(leaf, tongue) + 0.05


def rosette(h):
    u, v = cell(3, h)
    y = v * 2 - 1
    r = np.sqrt(u * u + y * y)
    th = np.arctan2(y, u)
    frame = np.maximum(np.abs(u), np.abs(y))
    # a coffer: sunk panel inside a stepped frame
    panel = 0.5 * sstep(0.97, 0.90, frame) * -1 + 0.5
    # eight heavy petals, two layers, and a boss
    p1 = (0.5 + 0.5 * np.abs(np.cos(th * 4))) ** 0.6
    petals = np.sqrt(np.maximum(1 - (r / (0.74 * (0.72 + 0.28 * p1))) ** 2, 0)) * 0.95
    p2 = (0.5 + 0.5 * np.abs(np.cos(th * 4 + np.pi / 4))) ** 0.6
    inner = np.sqrt(np.maximum(1 - (r / (0.46 * (0.75 + 0.25 * p2))) ** 2, 0)) * 1.2
    boss = np.sqrt(np.maximum(1 - (r / 0.16) ** 2, 0)) * 1.32
    veins = 0.06 * np.cos(th * 24) * sstep(0.74, 0.3, r)
    return np.maximum.reduce([panel, petals + veins, inner, boss])


hs = {k: int((b - a) * S) for k, (a, b) in ROWS.items()}
art = {"egg": egg_and_dart, "bead": bead_and_reel, "leaf": leaf_cyma, "rosette": rosette}
depth = dict(egg=0.075, bead=0.03, leaf=0.085, rosette=0.11)        # relief in metres
stack, relief = [], []
for k in ("egg", "bead", "leaf", "rosette"):
    h = art[k](hs[k])
    stack.append(h)
    relief.append(h * depth[k])
H = np.concatenate(relief, 0)[:S, :]
if H.shape[0] < S:
    H = np.concatenate([H, np.zeros((S - H.shape[0], S))], 0)
H = gaussian_filter(H, 0.8 * SS, mode=("nearest", "wrap"))

px = METRES_PER_U / S
dx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) / (2 * px)
dy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
nrm = np.stack([-dx / ln, dy / ln, 1 / ln], -1)
# occlusion: how far each point sits below what is around it, at two sizes
wide = 1 - np.clip((gaussian_filter(H, 40 * SS / 2, mode=("nearest", "wrap")) - H) / 0.02, 0, 1) * 0.75
tight = 1 - np.clip((gaussian_filter(H, 7 * SS / 2, mode=("nearest", "wrap")) - H) / 0.006, 0, 1) * 0.85


def down(a):
    return np.asarray(Image.fromarray(a).resize((N, N), Image.BOX))


n8 = down(((nrm * 0.5 + 0.5) * 255).astype(np.uint8))
Image.fromarray(n8).save(OUT / "ext_trim_normal.png", optimize=True)
ao = np.stack([down((wide * 255).astype(np.uint8)), down((tight * 255).astype(np.uint8)), np.zeros((N, N), np.uint8)], -1)
Image.fromarray(ao).save(OUT / "ext_trim_ao.png", optimize=True)
print("trim written")
