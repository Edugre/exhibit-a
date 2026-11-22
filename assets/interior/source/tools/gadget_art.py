"""The Signal Jammer's texture and sounds (asset plan P2.4). Plain Python: numpy and Pillow only.
usage: python gadget_art.py <out dir>     (writes int_gadget.png, jam_pulse.wav and jam_dud.wav there)"""
import math
import pathlib
import sys
import wave
import numpy as np
from PIL import ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
S = 512

RECTS = {
    "plastic": (0, 0, 128, 128),
    "metal": (128, 0, 256, 128),
    "rubber": (256, 0, 384, 128),
    "led": (384, 0, 512, 128),
    "face": (0, 128, 256, 512),     # the front, 0.07 x 0.13 m: grille, dial ring and label
    "back": (256, 128, 512, 512),   # the back, with the belt clip's warning sticker
}
rng = np.random.default_rng(2401)
img = np.zeros((S, S, 3), np.float32)


def fill(name, rgb, vary=0.04, grain=1.2):
    x0, y0, x1, y1 = RECTS[name]
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (1 + vary * A.blur_noise(rng, x1 - x0, y1 - y0, grain))[..., None]


fill("plastic", (0.10, 0.11, 0.12))
fill("metal", (0.62, 0.63, 0.66), 0.06, 0.6)
fill("rubber", (0.05, 0.05, 0.05), 0.08)
fill("led", (1.0, 0.12, 0.08), 0.0)
fill("face", (0.10, 0.11, 0.12))
fill("back", (0.10, 0.11, 0.12))

pic = A.to_image(img)
d = ImageDraw.Draw(pic)
INK = (225, 220, 205)
GOLD = (214, 170, 80)

# Front: a speaker grille, a gold winged-sandal badge and the label
x0, y0, x1, y1 = RECTS["face"]
cx = (x0 + x1) / 2
for row in range(6):
    for col in range(6):
        px, py = x0 + 54 + col * 30, y0 + 36 + row * 17
        d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=(18, 18, 20))
d.rounded_rectangle((x0 + 30, y0 + 20, x1 - 30, y0 + 140), radius=14, outline=(60, 62, 66), width=4)
d.text((cx, y0 + 172), "HERMES", font=A.fit_font(d, "HERMES", A.SANS_BOLD, 48, x1 - x0 - 60), fill=GOLD, anchor="mm")
d.text((cx, y0 + 210), "SIGNAL JAMMER", font=A.fit_font(d, "SIGNAL JAMMER", A.SANS_BOLD, 30, x1 - x0 - 50), fill=INK, anchor="mm")
# A little winged sandal
sx, sy = cx, y0 + 262
d.polygon([(sx - 40, sy + 10), (sx + 30, sy + 10), (sx + 40, sy), (sx - 30, sy - 6)], fill=GOLD)
d.polygon([(sx - 26, sy - 6), (sx - 50, sy - 30), (sx - 18, sy - 22), (sx - 44, sy - 42), (sx - 6, sy - 26)], fill=GOLD)
d.text((cx, y0 + 296), "Messenger of the gods.", font=A.fit_font(d, "Messenger of the gods.", A.SERIF_ITAL, 22, x1 - x0 - 30), fill=INK, anchor="mm")

# Back: the sticker
x0, y0, x1, y1 = RECTS["back"]
cx = (x0 + x1) / 2
d.rectangle((x0 + 40, y0 + 172, x1 - 40, y0 + 292), fill=(230, 196, 40))
for i, line in enumerate(["DO NOT POINT", "AT OLYMPUS", "2 uses per night"]):
    font = A.fit_font(d, line, A.SANS_BOLD if i < 2 else A.SERIF_ITAL, 24, x1 - x0 - 100)
    d.text((cx, y0 + 198 + i * 34), line, font=font, fill=(24, 20, 18), anchor="mm")

pic.save(OUT / "int_gadget.png")
A.write_layout(HERE / "gadget_atlas.json", [S, S], RECTS)
print("wrote", OUT / "int_gadget.png")

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
    k = np.ones(n) / n
    return np.convolve(x, k, mode="same")


# The pulse: a falling radio whoop, then a burst of crackling static that fades out
r = np.random.default_rng(2402)
t = np.arange(int(0.9 * SR)) / SR
freq = 1400 * np.exp(-t * 7) + 180
whoop = np.sin(2 * math.pi * np.cumsum(freq) / SR) * np.exp(-t * 9)
hiss = r.standard_normal(t.size)
hiss = hiss - smooth(hiss, 6)                                  # thin it to a radio hiss
crackle = (r.random(t.size) < 0.012) * r.standard_normal(t.size) * 4
static = (hiss * 0.35 + crackle) * np.clip(t / 0.03, 0, 1) * np.exp(-t * 4.2)
write("jam_pulse", whoop * 0.8 + static)

# The dud: two short dry clicks, when there's nothing in range or no charge left
r = np.random.default_rng(2403)
t = np.arange(int(0.25 * SR)) / SR
dud = np.zeros(t.size)
for start in (0.0, 0.11):
    n = int(0.03 * SR)
    i = int(start * SR)
    burst = r.standard_normal(n) * np.exp(-np.arange(n) / (0.004 * SR))
    dud[i:i + n] += burst - smooth(burst, 3)
write("jam_dud", dud)
