"""Every sound inside the museum's rooms (asset plan P4), generated from noise and maths, so nothing is
borrowed. Plain Python with numpy only. 16-bit mono WAV at 22050 Hz. Each sound draws from its own seed,
so adding or changing one never changes the others. Loops fold their tail over their head so they
repeat without a click; their import settings loop them (edit/loop_mode=2).
usage: python make_room_sounds.py <out dir>      (assets/interior/sounds)"""
import math
import pathlib
import sys
import wave
import numpy as np

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
SR = 22050
LOOPS = []  # names of the sounds that loop, for the import step


def secs(t):
    return np.arange(int(t * SR)) / SR


def lowpass(x, hz):
    """One-pole low-pass, in a plain loop (no scipy here)."""
    a = 1.0 - math.exp(-2.0 * math.pi * hz / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def band(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)


def seam(x, fade):
    """Fold the tail back over the head, so the loop has no click."""
    n = int(fade * SR)
    t = np.linspace(0, 1, n)
    x = x.copy()
    x[:n] = x[:n] * t + x[-n:] * (1 - t)
    return x[:-n]


def write(name, x, loop=False):
    x = np.asarray(x, np.float64)
    x = x / max(np.abs(x).max(), 1e-6) * 0.86
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    if loop:
        LOOPS.append(name)
    print("wrote", OUT / f"{name}.wav", "(loop)" if loop else "")


# P4.1 HVAC hum: rumbling air and a low mains drone. One loop; each room plays it at its own pitch.
r = np.random.default_rng(4101)
t = secs(6.5)
air = lowpass(lowpass(r.standard_normal(t.size), 260), 400)
drone = np.sin(2 * math.pi * 55 * t) + 0.35 * np.sin(2 * math.pi * 110 * t) + 0.12 * np.sin(2 * math.pi * 165 * t)
wobble = 1 + 0.08 * np.sin(2 * math.pi * 0.31 * t)
write("amb_hvac", seam((air * 2.2 + drone * 0.25) * wobble, 0.5), loop=True)

# P4.2 Ticking clock: four beats a loop, tick and tock a little apart in pitch, with a wooden body.
r = np.random.default_rng(4201)
t = secs(4.0)
clock = np.zeros(t.size)
for beat in range(4):
    start = int((beat + 0.25) * SR)  # a quarter beat in, so the loop starts in silence
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    pitch = 2300 if beat % 2 == 0 else 1750
    click = np.sin(2 * math.pi * pitch * tt) * np.exp(-tt * 140)
    knock = np.sin(2 * math.pi * 420 * tt) * np.exp(-tt * 60) * 0.5
    grit = band(r.standard_normal(n), 1500, 6000) * np.exp(-tt * 300) * 0.6
    clock[start:start + n] += click + knock + grit
write("amb_clock", clock, loop=True)

# P4.3 Fluorescent buzz: a 120 Hz hum rich in harmonics, a thin hiss, and a flutter that repeats every loop.
r = np.random.default_rng(4301)
t = secs(3.25)  # 3 s to keep, plus 0.25 s to fold over the start; 3 s is a whole number of hum cycles
buzz = sum((0.6 ** k) * np.sign(np.sin(2 * math.pi * 120 * (k + 1) * t)) for k in range(4))
buzz = lowpass(buzz, 1800)
hiss = band(r.standard_normal(t.size), 5000, 9000) * 0.15
flutter = 1 - 0.25 * np.clip(np.sin(2 * math.pi * (1 / 3.0) * t * 3) ** 40, 0, 1)
write("amb_fluorescent", seam((buzz * 0.5 + hiss) * flutter, 0.25), loop=True)

# P4.4 Radio chatter: a squelch, then voice-shaped bursts of band-limited noise (no words), then a squelch.
for k, (seed, length) in enumerate(((4401, 2.2), (4402, 1.6), (4403, 2.8)), start=1):
    r = np.random.default_rng(seed)
    t = secs(length)
    voice = band(r.standard_normal(t.size), 350, 2600)
    env = np.zeros(t.size)
    pos = 0.12
    while pos < length - 0.25:
        syl = r.uniform(0.07, 0.2)
        a, b = int(pos * SR), int((pos + syl) * SR)
        env[a:b] = np.sin(np.linspace(0, math.pi, b - a)) * r.uniform(0.5, 1.0)
        pos += syl + r.uniform(0.02, 0.12) + (0.25 if r.random() < 0.15 else 0.0)
    pitchy = 1 + 0.4 * np.sin(2 * math.pi * r.uniform(90, 160) * t)  # a buzzy, throaty edge
    squelch = np.zeros(t.size)
    for at in (0.0, length - 0.08):
        a = int(at * SR)
        n = int(0.07 * SR)
        squelch[a:a + n] += band(r.standard_normal(n), 800, 7000) * np.linspace(1, 0.2, n)
    write(f"sfx_radio_chatter_{k}", lowpass(voice * env * pitchy, 3000) + squelch * 0.6)

# P4.6 Floorboard creaks: a rubbing, wavering tone with grit in it.
for k, (seed, length, lo, hi) in enumerate(((4601, 0.9, 170, 320), (4602, 0.7, 240, 420)), start=1):
    r = np.random.default_rng(seed)
    t = secs(length)
    freq = lo + (hi - lo) * (0.5 + 0.5 * np.sin(2 * math.pi * r.uniform(0.7, 1.4) * t + r.uniform(0, 6)))
    freq += 25 * lowpass(r.standard_normal(t.size), 30)
    phase = 2 * math.pi * np.cumsum(freq) / SR
    tone = np.sign(np.sin(phase)) * 0.4 + np.sin(phase * 2) * 0.3
    grit = 0.6 + 0.4 * (lowpass(r.random(t.size), 400) > 0.5)
    env = np.sin(np.linspace(0, math.pi, t.size)) ** 0.7
    write(f"sfx_floor_creak_{k}", lowpass(tone * grit * env, 1600))

# P4.6 Page rustles: a few crinkly bursts of bright noise, like a page being turned.
for k, (seed, length) in enumerate(((4611, 0.7), (4612, 0.5)), start=1):
    r = np.random.default_rng(seed)
    t = secs(length)
    noise = band(r.standard_normal(t.size), 1800, 9000)
    crinkle = (r.random(t.size) < 0.02) * r.standard_normal(t.size) * 3
    env = np.zeros(t.size)
    for _ in range(r.integers(3, 6)):
        c = r.uniform(0.05, length - 0.1)
        env += np.exp(-((t - c) / r.uniform(0.02, 0.06)) ** 2)
    write(f"sfx_page_rustle_{k}", (noise + crinkle) * env)

# P4.5 Laser hum: a steady electric drone with a thin whine on top, while the grid is on.
r = np.random.default_rng(4501)
t = secs(2.0)
hum = np.sin(2 * math.pi * 60 * t) + 0.5 * np.sin(2 * math.pi * 180 * t) + 0.25 * np.sin(2 * math.pi * 300 * t)
whine = 0.08 * np.sin(2 * math.pi * 3150 * t) * (1 + 0.3 * np.sin(2 * math.pi * 3 * t))
fizz = band(r.standard_normal(t.size), 3000, 8000) * 0.05
write("amb_laser_hum", seam(hum * 0.5 + whine + fizz, 0.2), loop=True)

# P4.5 Laser zap: what you hear when you walk into the beams, before the alarm noise sends a guard.
r = np.random.default_rng(4502)
t = secs(0.45)
freq = 2200 * np.exp(-t * 9) + 260
zap = np.sign(np.sin(2 * math.pi * np.cumsum(freq) / SR)) * np.exp(-t * 7)
crackle = (r.random(t.size) < 0.05) * r.standard_normal(t.size) * np.exp(-t * 10)
write("sfx_laser_zap", lowpass(zap * 0.6 + crackle, 5000))

(OUT / "loops.txt").write_text("\n".join(LOOPS) + "\n", newline="\n")
