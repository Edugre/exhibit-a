"""The laser grid's and its switch's texture (asset plan P2.1, P2.2): dark steel, hazard stripes, the
emitter post's maker's plate, the switch pad's "stand here" print, and the switch's own label (a
separate image, because pressure_plate.gd puts a whole texture on the plaque).
usage: python laser_art.py <out dir>     (writes int_laser.png and switch_label.png there)"""
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
S = 1024
rng = np.random.default_rng(2101)

RECTS = {
    "steel": (0, 0, 256, 256),
    "dark": (256, 0, 384, 128),
    "rubber": (384, 0, 512, 128),
    "lens": (256, 128, 384, 256),
    "stripes": (512, 0, 1024, 128),       # hazard stripes, for the post's foot and the pad's edge
    "maker": (384, 128, 512, 512),        # the post's maker's plate, 0.09 x 0.27 m
    "pad": (0, 512, 512, 1024),           # the switch pad's top, 0.9 x 0.9 m
    "box": (512, 128, 1024, 384),         # the control box's face around the lamp and the label
}
YELLOW = (236, 190, 28)
INK = (20, 20, 20)
img = np.zeros((S, S, 3), np.float32)


def region(name):
    x0, y0, x1, y1 = RECTS[name]
    return x0, y0, x1, y1, x1 - x0, y1 - y0


def fill(name, rgb, vary=0.04, grain=1.5):
    x0, y0, x1, y1, w, h = region(name)
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (1 + vary * A.blur_noise(rng, w, h, grain))[..., None]


x0, y0, x1, y1, w, h = region("steel")
img[y0:y1, x0:x1] = np.array([0.26, 0.27, 0.29], np.float32) * (1 + 0.06 * A.streaks(rng, w, h, 40, axis=0) + 0.03 * A.blur_noise(rng, w, h, 10))[..., None]
fill("dark", (0.08, 0.08, 0.09))
fill("rubber", (0.06, 0.06, 0.06), 0.1, 0.7)
fill("lens", (1.0, 0.1, 0.08), 0.0)
fill("maker", (0.70, 0.66, 0.58), 0.03)
fill("pad", (0.07, 0.07, 0.07), 0.08, 0.8)
fill("box", (0.20, 0.21, 0.23), 0.04)

pic = A.to_image(img)
d = ImageDraw.Draw(pic)

# Hazard stripes
x0, y0, x1, y1, w, h = region("stripes")
stripes = Image.new("RGB", (w, h), YELLOW)  # drawn apart, so the diagonals can't spill into the next swatch
sd = ImageDraw.Draw(stripes)
for k in range(-h, w, 64):
    sd.polygon([(k, h), (k + 32, h), (k + 32 + h, 0), (k + h, 0)], fill=INK)
pic.paste(stripes, (x0, y0))

# The maker's plate, read sideways down the post
x0, y0, x1, y1, w, h = region("maker")
plate = Image.new("RGB", (h, w), (178, 168, 148))
p = ImageDraw.Draw(plate)
p.rectangle((6, 6, h - 7, w - 7), outline=(60, 50, 40), width=3)
p.text((h / 2, w * 0.36), "HEPHAESTUS", font=A.fit_font(p, "HEPHAESTUS", A.SANS_BOLD, 52, h - 40), fill=(40, 34, 28), anchor="mm")
p.text((h / 2, w * 0.68), "Security Systems · Forged on Olympus", font=A.fit_font(p, "Security Systems · Forged on Olympus", A.SERIF_ITAL, 26, h - 40), fill=(40, 34, 28), anchor="mm")
pic.paste(plate.rotate(90, expand=True), (x0, y0))

# The pad's top: two footprints, STAND HERE, and a yellow border
x0, y0, x1, y1, w, h = region("pad")
d.rectangle((x0 + 14, y0 + 14, x1 - 14, y1 - 14), outline=YELLOW, width=12)
for fx, flip in ((x0 + w * 0.36, -1), (x0 + w * 0.64, 1)):
    fy = y0 + h * 0.42
    d.ellipse((fx - 38, fy - 80, fx + 38, fy + 46), fill=YELLOW)                 # sole
    d.ellipse((fx - 30, fy + 56, fx + 30, fy + 104), fill=YELLOW)                # heel
    for i, (tx, ty) in enumerate(((-28, -102), (-6, -112), (14, -108), (30, -96), (40, -80))):
        r = 13 - i
        d.ellipse((fx + flip * tx - r, fy + ty - r, fx + flip * tx + r, fy + ty + r), fill=YELLOW)
d.text(((x0 + x1) / 2, y0 + h * 0.8), "STAND HERE", font=A.fit_font(d, "STAND HERE", A.SANS_BOLD, 64, w - 80), fill=YELLOW, anchor="mm")
d.text(((x0 + x1) / 2, y0 + h * 0.89), "the grid is off while you do", font=A.fit_font(d, "the grid is off while you do", A.SANS_BOLD, 26, w - 120), fill=(200, 200, 200), anchor="mm")

# The control box's face: a recess for the lamp, and a vent
x0, y0, x1, y1, w, h = region("box")
d.rounded_rectangle((x0 + 20, y0 + 20, x1 - 20, y1 - 20), radius=18, outline=(70, 72, 76), width=6)
for i in range(6):
    d.rectangle((x0 + 60, y0 + 160 + i * 12, x0 + 200, y0 + 165 + i * 12), fill=(30, 30, 32))

pic.save(OUT / "int_laser.png")
A.write_layout(HERE / "laser_atlas.json", [S, S], RECTS)
print("wrote", OUT / "int_laser.png")

# The switch's label, for the plaque on its control box (0.26 x 0.11 m)
label = Image.new("RGB", (624, 264), (28, 28, 30))
l = ImageDraw.Draw(label)
l.rectangle((8, 8, 615, 255), outline=YELLOW, width=6)
l.text((312, 92), "LASER GRID", font=A.fit_font(l, "LASER GRID", A.SANS_BOLD, 84, 560), fill=YELLOW, anchor="mm")
l.text((312, 186), "Off while someone stands on the pad", font=A.fit_font(l, "Off while someone stands on the pad", A.SANS_BOLD, 34, 560), fill=(220, 220, 220), anchor="mm")
label.save(OUT / "switch_label.png")
print("wrote", OUT / "switch_label.png")
