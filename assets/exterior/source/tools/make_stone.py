"""Tiling limestone: colour, normal and roughness. Plain numpy, every layer repeats across the tile.
usage: python make_stone.py <out dir> [size]"""
import pathlib
import sys
import numpy as np
from PIL import Image

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
TILE_METRES = 4.0


def fft_noise(beta, seed, lo=0.0, hi=1e9, aspect=(1.0, 1.0)):
    """Repeating noise whose energy falls off with frequency; beta sets how smooth it is."""
    rng = np.random.default_rng(seed)
    fx = np.fft.fftfreq(N)[None, :] * N / aspect[0]
    fy = np.fft.fftfreq(N)[:, None] * N / aspect[1]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[(f < lo) | (f > hi)] = 0
    amp[0, 0] = 0
    spec = amp * np.exp(2j * np.pi * rng.random((N, N)))
    out = np.fft.ifft2(spec).real
    return ((out - out.mean()) / out.std()).astype(np.float32)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# Big cloudy mottling, and medium patches
cloud = fft_noise(3.0, 1, hi=24)
patch = fft_noise(2.2, 2, lo=8, hi=120)
# Faint horizontal bedding of sawn limestone
bed = fft_noise(2.4, 3, hi=400, aspect=(14.0, 1.0))
# Fine grain and fossil pits
grain = fft_noise(0.8, 4, lo=120)
pits_src = fft_noise(1.2, 5, lo=60, hi=500)
pits = sstep(1.5, 2.6, pits_src)
fines = sstep(2.0, 3.0, fft_noise(0.2, 6, lo=300))

height = 0.34 * cloud + 0.30 * patch + 0.20 * bed + 0.20 * grain - 2.2 * pits - 1.0 * fines
tone = 0.012 * cloud + 0.012 * patch + 0.016 * bed + 0.012 * grain - 0.15 * pits - 0.05 * fines

base = np.array([0.655, 0.610, 0.545], dtype=np.float32)      # warm limestone, in sRGB values
warm = np.array([0.045, 0.012, -0.030], dtype=np.float32)
col = base[None, None, :] + tone[..., None] + warm[None, None, :] * (0.22 * cloud + 0.16 * bed)[..., None]
Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / "ext_stone_albedo.png", optimize=True)

# Normal, from a height in metres (the tile covers 4 m), +Y up as Godot expects
px = TILE_METRES / N
relief = 0.0016 * height
dx = (np.roll(relief, -1, 1) - np.roll(relief, 1, 1)) / (2 * px)
dy = (np.roll(relief, -1, 0) - np.roll(relief, 1, 0)) / (2 * px)
nz = np.ones_like(dx)
ln = np.sqrt(dx * dx + dy * dy + nz * nz)
nrm = np.stack([-dx / ln, dy / ln, nz / ln], -1)
Image.fromarray(((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).save(OUT / "ext_stone_normal.png", optimize=True)

rough = np.clip(0.86 + 0.05 * patch - 0.03 * cloud + 0.08 * pits, 0.6, 1.0)
Image.fromarray((rough * 255 + 0.5).astype(np.uint8)).save(OUT / "ext_stone_rough.png", optimize=True)
print("stone written", N, {k: round(float(v), 3) for k, v in dict(tone_min=tone.min(), tone_max=tone.max()).items()})
