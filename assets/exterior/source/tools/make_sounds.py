"""Every sound of the street, generated from noise and maths, so nothing is borrowed. 16-bit WAV.
usage: python make_sounds.py <out dir>"""
import pathlib
import sys
import wave
import numpy as np
from scipy.signal import butter, sosfilt

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
SR = 22050
rng = np.random.default_rng(82)


def band(x, lo, hi):
    return sosfilt(butter(2, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos"), x)


def low(x, hi):
    return sosfilt(butter(2, hi / (SR / 2), btype="low", output="sos"), x)


def seam(x, fade):
    """Fold the tail back over the head, so the loop has no click."""
    n = int(fade * SR)
    t = np.linspace(0, 1, n)
    x = x.copy()
    x[:n] = x[:n] * t + x[-n:] * (1 - t)
    return x[:-n]


def write(name, x):
    x = np.asarray(x, dtype=np.float64)
    x = x / max(np.abs(x).max(), 1e-6) * 0.86
    pcm = (x * 32767).astype(np.int16)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1 if pcm.ndim == 1 else 2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(name, round(len(pcm) / SR, 1), "s", flush=True)


def swell(n, period, sharp):
    """A slow random envelope, for the rise and fall of distant traffic."""
    k = max(int(n / SR / period), 4)
    keys = rng.random(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), keys) ** sharp


# The city at night: a low rumble, far traffic rising and falling, one far siren, one far horn
T = 44
n = T * SR
rumble = low(rng.standard_normal(n), 130) * 1.2
far = band(rng.standard_normal(n), 180, 900) * (0.25 + swell(n, 5.0, 1.6))
hiss = band(rng.standard_normal(n), 1200, 5000) * 0.04 * (0.4 + swell(n, 3.0, 1.0))
city = rumble + far * 0.8 + hiss
t = np.arange(n) / SR
siren = np.sin(2 * np.pi * np.cumsum(620 + 170 * np.sin(2 * np.pi * 0.28 * t)) / SR)
env = np.exp(-((t - 17) / 5.5) ** 2)
city += low(siren, 1500) * env * 0.05
horn_at = 31.0
h = np.exp(-((t - horn_at) / 0.22) ** 8) * (np.sin(2 * np.pi * 340 * t) + np.sin(2 * np.pi * 428 * t))
city += low(h, 1200) * 0.05
left = city + band(rng.standard_normal(n), 200, 700) * 0.1 * swell(n, 4.0, 1.5)
right = city + band(rng.standard_normal(n), 200, 700) * 0.1 * swell(n, 4.0, 1.5)
write("amb_city", np.stack([seam(left, 3.0), seam(right, 3.0)], -1))

# The fountain: broad falling water with its own slow pulse
n = 14 * SR
w = rng.standard_normal(n)
water = band(w, 500, 2600) + band(w, 2600, 7000) * 0.6 + band(w, 150, 500) * 0.4
drops = (rng.random(n) > 0.9992) * rng.random(n)
water += band(np.convolve(drops, np.exp(-np.arange(600) / 90.0), "same"), 900, 4000) * 3.0
write("amb_fountain", seam(water * (0.72 + 0.28 * swell(n, 2.0, 1.0)), 1.5))

# Crickets in the park
n = 16 * SR
t = np.arange(n) / SR
chirp = np.zeros(n)
for f, rate, phase in ((4300, 2.1, 0.0), (4620, 1.7, 0.4), (3980, 2.6, 0.7)):
    pulses = (np.sin(2 * np.pi * rate * t + phase) > 0.2) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t) ** 2)
    chirp += np.sin(2 * np.pi * f * t) * low(pulses.astype(float), 90)
write("amb_crickets", seam(chirp, 1.0))

# A flock taking off: a burst of wing claps, thinning out
n = int(2.1 * SR)
x = np.zeros(n)
for i in range(46):
    at = int(rng.random() ** 1.7 * (n - 3000))
    m = int(rng.uniform(500, 1100))
    clap = band(rng.standard_normal(m), 350, 2600) * np.exp(-np.arange(m) / (m * 0.25))
    x[at:at + m] += clap * rng.uniform(0.4, 1.0)
write("pigeons_flap", x)

# The cooing of a pigeon on a ledge
n = int(1.3 * SR)
t = np.arange(n) / SR
pitch = 320 + 70 * np.sin(2 * np.pi * 1.6 * t + 0.6) + 20 * np.sin(2 * np.pi * 9 * t)
coo = np.sin(2 * np.pi * np.cumsum(pitch) / SR) + 0.35 * np.sin(4 * np.pi * np.cumsum(pitch) / SR)
envelope = np.clip(np.sin(np.pi * t / 1.3), 0, 1) ** 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.3 * t) ** 2)
write("pigeon_coo", low(coo * envelope, 1400))

# The bronze doors: a low grinding swing that settles with a soft thud
n = int(1.5 * SR)
t = np.arange(n) / SR
grind = band(rng.standard_normal(n), 60, 420) * np.clip(np.sin(np.pi * t / 1.25), 0, 1) ** 0.7
creak = np.sin(2 * np.pi * np.cumsum(118 + 34 * np.sin(2 * np.pi * 2.1 * t) + 40 * t) / SR) * np.clip(np.sin(np.pi * t / 1.25), 0, 1)
thud = low(rng.standard_normal(n), 160) * np.exp(-np.maximum(t - 1.22, 0) * 22) * (t > 1.22)
write("door_groan", grind + 0.42 * low(creak, 900) + thud * 1.8)

# A cab's horn, and an engine going by
n = int(0.7 * SR)
t = np.arange(n) / SR
horn = np.sign(np.sin(2 * np.pi * 415 * t)) * 0.6 + np.sign(np.sin(2 * np.pi * 523 * t)) * 0.6
write("car_horn", low(horn, 2400) * np.clip(t / 0.02, 0, 1) * np.clip((0.7 - t) / 0.05, 0, 1))
n = 8 * SR
t = np.arange(n) / SR
engine = low(rng.standard_normal(n), 240) + 0.5 * band(rng.standard_normal(n), 300, 1400)
write("car_engine", seam(engine + 0.3 * np.sin(2 * np.pi * 58 * t), 1.0))

# She knows: one long breath of a whisper, close to the ear
n = int(1.9 * SR)
t = np.arange(n) / SR
breath = band(rng.standard_normal(n), 2400, 8200) + 0.4 * band(rng.standard_normal(n), 900, 2400)
shape = np.clip(t / 0.18, 0, 1) ** 1.5 * np.clip((1.9 - t) / 1.0, 0, 1) ** 2
write("she_knows", breath * shape * (0.82 + 0.18 * np.sin(2 * np.pi * 5.5 * t)))

# An old electric alarm bell, somewhere in the building
n = 3 * SR
t = np.arange(n) / SR
strike = (np.sin(2 * np.pi * 24 * t) > 0).astype(float)
ring = sum(np.sin(2 * np.pi * f * t) * g for f, g in ((1180, 1.0), (2370, 0.5), (3720, 0.25), (5310, 0.12)))
write("alarm_bell", seam(ring * (0.55 + 0.45 * low(strike, 200)), 0.3))

# A police siren a long way uptown, rising and falling
n = 12 * SR
t = np.arange(n) / SR
wail = 760 + 340 * np.sin(2 * np.pi * 0.17 * t)
tone = np.sin(2 * np.pi * np.cumsum(wail) / SR)
tone += 0.4 * np.sin(4 * np.pi * np.cumsum(wail) / SR)
write("siren_far", seam(band(tone, 300, 2400) * (0.75 + 0.25 * swell(n, 2.0, 1.0)), 1.5))

# Rain on stone: a steady hiss, a heavier patter under it, and the odd fat drop
n = 16 * SR
sides = []
for side in range(2):
    wet = band(rng.standard_normal(n), 1400, 7800) + 0.6 * band(rng.standard_normal(n), 320, 1400)
    fat = (rng.random(n) > 0.9994) * rng.random(n)
    wet += band(np.convolve(fat, np.exp(-np.arange(500) / 70.0), "same"), 600, 3000) * 5.0
    sides.append(seam(wet * (0.82 + 0.18 * swell(n, 3.0, 1.0)), 2.0))
write("amb_rain", np.stack(sides, -1))

# Wind round the columns on a snowy night: low and hollow, rising and dropping
n = 18 * SR
sides = []
for side in range(2):
    gust = band(rng.standard_normal(n), 160, 620) * (0.3 + 0.7 * swell(n, 2.8, 1.8))
    sides.append(seam(gust + 0.18 * low(rng.standard_normal(n), 120), 2.5))
write("amb_wind", np.stack(sides, -1))

# Far thunder: one crack softened by distance, then a long roll
n = 6 * SR
t = np.arange(n) / SR
roll = low(rng.standard_normal(n), 190) * np.exp(-t * 0.9) * (0.5 + 0.5 * swell(n, 0.5, 1.4))
crack = band(rng.standard_normal(n), 200, 1400) * np.exp(-t * 11.0)
write("thunder", roll + 0.45 * crack)
