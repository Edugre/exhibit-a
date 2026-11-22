"""The loot set's one small texture and its sounds (stretch goal: scoring): gold, silver, bronze, lapis, ruby,
emerald, leather, laurel, iron and red paint for six small valuables and the crowbar; a coin chink for
pocketing something, glass breaking for a display case, and the crowbar's creak as it bites.
It lives in assets/loot (the valuables move between rooms, like the gadget).
usage: python loot_art.py <out dir>     (writes int_loot.png and the .wav files there)"""
import math
import pathlib
import sys
import wave
import numpy as np
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
S = 512
rng = np.random.default_rng(7001)

RECTS = {
    "gold": (0, 0, 128, 128),
    "silver": (128, 0, 256, 128),
    "bronze": (256, 0, 384, 128),
    "lapis": (384, 0, 512, 128),
    "ruby": (0, 128, 128, 256),
    "emerald": (128, 128, 256, 256),
    "leather": (256, 128, 384, 256),
    "laurel": (384, 128, 512, 256),
    "iron": (0, 256, 256, 384),
    "paint": (256, 256, 512, 384),
    "dark": (0, 384, 128, 512),
}

img = np.zeros((S, S, 3), np.float32)


def region(name):
    x0, y0, x1, y1 = RECTS[name]
    return x0, y0, x1, y1, x1 - x0, y1 - y0


def fill(name, rgb, vary=0.04, grain=1.5, streak=0.0):
    x0, y0, x1, y1, w, h = region(name)
    tone = 1 + vary * A.blur_noise(rng, w, h, grain)
    if streak:
        tone = tone + streak * A.streaks(rng, w, h, 30)
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * tone[..., None]


fill("gold", (0.95, 0.72, 0.28), 0.05, 3)
fill("silver", (0.82, 0.83, 0.85), 0.04, 3)
fill("bronze", (0.62, 0.42, 0.2), 0.08, 3)
x0, y0, x1, y1, w, h = region("lapis")  # deep blue with gold flecks
img[y0:y1, x0:x1] = np.array([0.1, 0.16, 0.55], np.float32) * (1 + 0.15 * A.blur_noise(rng, w, h, 4))[..., None]
flecks = rng.random((h, w)) < 0.01
img[y0:y1, x0:x1][flecks] = np.array([0.95, 0.78, 0.35], np.float32)
fill("ruby", (0.75, 0.04, 0.08), 0.1, 2)
fill("emerald", (0.05, 0.55, 0.25), 0.1, 2)
fill("leather", (0.38, 0.22, 0.12), 0.14, 0.8)
fill("laurel", (0.86, 0.68, 0.25), 0.1, 1)   # a gilt laurel
fill("iron", (0.22, 0.22, 0.24), 0.06, 2, streak=0.06)
fill("paint", (0.62, 0.08, 0.06), 0.05, 2)
fill("dark", (0.05, 0.05, 0.05), 0.05)

A.to_image(img).save(OUT / "int_loot.png")
A.write_layout(HERE / "loot_atlas.json", [S, S], RECTS)
print("wrote", OUT / "int_loot.png")

# --- Sounds -------------------------------------------------------------------------
SR = 22050


def write(name, x):
    x = np.asarray(x, np.float64)
    x = x / max(np.abs(x).max(), 1e-6) * 0.86
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("wrote", OUT / f"{name}.wav")


def smooth(x, n):
    return np.convolve(x, np.ones(n) / n, mode="same")


def ping(t, freq, decay):
    """A struck bit of metal or glass: a few inharmonic partials, each dying away."""
    out = np.zeros_like(t)
    for k, (ratio, amp) in enumerate(((1.0, 1.0), (2.76, 0.5), (5.4, 0.25), (8.9, 0.12))):
        out += amp * np.sin(2 * math.pi * freq * ratio * t) * np.exp(-t * decay * (1 + 0.6 * k))
    return out


# The chink: a coin dropped into a full purse, twice
r = np.random.default_rng(7002)
t = np.arange(int(0.45 * SR)) / SR
chink = np.zeros(t.size)
for start, freq in ((0.0, 3150.0), (0.09, 3620.0)):
    i = int(start * SR)
    chink[i:] += ping(t[: t.size - i], freq * r.uniform(0.98, 1.02), 18)
write("chink", chink)

# Glass breaking: a sharp crack, then a shower of tinkling shards over a hiss
r = np.random.default_rng(7003)
t = np.arange(int(1.4 * SR)) / SR
crack = r.standard_normal(t.size) * np.exp(-t * 40)
crack = crack - smooth(crack, 4)
shards = np.zeros(t.size)
for _ in range(60):
    start = r.exponential(0.25)
    if start > 1.2:
        continue
    i = int(start * SR)
    shards[i:] += r.uniform(0.2, 0.7) * ping(t[: t.size - i], r.uniform(2500, 7500), r.uniform(25, 60))
hiss = r.standard_normal(t.size)
hiss = (hiss - smooth(hiss, 3)) * 0.15 * np.exp(-t * 3)
write("glass_break", crack * 1.4 + shards * 0.5 + hiss)

# The crowbar biting: a dry creak of wood and metal, a strained squeal, then a pop
r = np.random.default_rng(7004)
t = np.arange(int(0.8 * SR)) / SR
grain = (r.random(t.size) < 0.02 + 0.03 * t) * r.standard_normal(t.size)
creak = smooth(grain, 12) * 6 * np.clip(t / 0.1, 0, 1)
squeal = np.sin(2 * math.pi * np.cumsum(620 + 240 * t + 30 * np.sin(t * 40)) / SR) * 0.25 * np.exp(-((t - 0.45) / 0.18) ** 2)
pop = np.zeros(t.size)
i = int(0.66 * SR)
pop[i:] = r.standard_normal(t.size - i) * np.exp(-np.arange(t.size - i) / (0.01 * SR))
write("crowbar_pry", creak + squeal + pop * 0.8)
