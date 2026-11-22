"""The night staff's hand bell (docs/boss_and_staff.md): three quick strikes of a small brass bell, each a
few inharmonic partials dying away, with a little clapper noise on the strike. Made here, like every other
sound in the project; a fixed seed, so it comes out the same every time.
usage: python make_staff_bell.py <assets/characters folder>"""
import pathlib
import sys
import wave

import numpy as np

OUT = pathlib.Path(sys.argv[1])
RATE = 22050
rng = np.random.default_rng(1871)

length = 1.6
t = np.arange(int(RATE * length)) / RATE
x = np.zeros_like(t)
for k, start in enumerate((0.0, 0.17, 0.36)):
    f = 1320.0 * (1.0 + 0.004 * k)                         # each swing strikes a hair differently
    s = np.clip(t - start, 0.0, None)
    on = (t >= start).astype(float)
    tone = sum(a * np.sin(2 * np.pi * f * m * s + rng.uniform(0, 6.28)) * np.exp(-s * d)
               for m, a, d in ((1.0, 1.0, 3.2), (2.76, 0.45, 6.0), (5.4, 0.22, 10.0), (8.93, 0.1, 16.0)))
    click = rng.normal(0, 1, len(t)) * np.exp(-s * 160.0) * 0.25
    x += on * (tone + click) * (0.9 ** k)
x *= np.minimum(1.0, (length - t) / 0.25)                   # fade the tail to silence
x = x / np.abs(x).max() * 0.8
data = (x * 32767).astype("<i2").tobytes()
with wave.open(str(OUT / "staff_bell.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(data)
print("wrote", OUT / "staff_bell.wav")
