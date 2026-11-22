"""The signs' one texture (asset plan P1.6): the wet-floor A-frame's print, the "Do not touch"
placard, the "Gallery closed" board, and plain yellow plastic, black rubber and brass for the rest.
usage: python signs_art.py <out dir>     (writes int_signs.png there)"""
import pathlib
import sys
import numpy as np
from PIL import ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
W, H = 1024, 1024
rng = np.random.default_rng(1601)

RECTS = {
    "wetfloor": (0, 0, 248, 512),      # the A-frame panel's face, 0.30 x 0.62 m
    "placard": (264, 0, 776, 370),     # the placard card, 0.36 x 0.26 m
    "yellow": (800, 0, 1024, 128),
    "brass": (800, 128, 1024, 256),
    "rubber": (800, 256, 1024, 384),
    "closed": (0, 528, 640, 1008),     # the "Gallery closed" board, 0.62 x 0.465 m
}
YELLOW = np.array([0.97, 0.78, 0.06], np.float32)
INK = (22, 20, 18)

img = np.zeros((H, W, 3), np.float32)


def fill(name, rgb, vary):
    x0, y0, x1, y1 = RECTS[name]
    w, h = x1 - x0, y1 - y0
    img[y0:y1, x0:x1] = rgb * (1 + vary * A.blur_noise(rng, w, h, 2))[..., None]


fill("wetfloor", YELLOW, 0.015)
fill("yellow", YELLOW, 0.015)
fill("placard", np.array([0.92, 0.88, 0.78], np.float32), 0.02)
fill("closed", np.array([0.93, 0.90, 0.82], np.float32), 0.02)
fill("rubber", np.array([0.05, 0.05, 0.05], np.float32), 0.08)
x0, y0, x1, y1 = RECTS["brass"]
img[y0:y1, x0:x1] = np.array([0.80, 0.62, 0.30], np.float32) * (1 + 0.07 * A.streaks(rng, x1 - x0, y1 - y0, 40))[..., None]

pic = A.to_image(img)
d = ImageDraw.Draw(pic)

# --- The wet-floor panel ---------------------------------------------------
x0, y0, x1, y1 = RECTS["wetfloor"]
cx, pw = (x0 + x1) / 2, x1 - x0
d.rectangle((x0, y0, x1, y0 + 66), fill=INK)
d.text((cx, y0 + 34), "CAUTION", font=A.fit_font(d, "CAUTION", A.SANS_BOLD, 46, pw - 30), fill=(247, 199, 15), anchor="mm")
# The warning triangle, and a visitor going over in it
top, base_y, half = (cx, y0 + 92), y0 + 268, 100
d.polygon([top, (cx - half, base_y), (cx + half, base_y)], outline=INK, width=11)
head = (cx + 16, y0 + 150)
d.ellipse((head[0] - 13, head[1] - 13, head[0] + 13, head[1] + 13), fill=INK)
hip = (cx - 8, y0 + 214)
d.line([(head[0] - 6, head[1] + 12), hip], fill=INK, width=10)                 # body, falling back
d.line([hip, (cx + 34, y0 + 196)], fill=INK, width=9)                          # leg kicked up
d.line([hip, (cx - 44, y0 + 236)], fill=INK, width=9)                          # other leg
d.line([(head[0] - 2, head[1] + 26), (cx - 40, y0 + 178)], fill=INK, width=8)  # arm flailing
d.line([(cx - 60, base_y - 16), (cx + 60, base_y - 16)], fill=INK, width=4)    # the puddle
d.text((cx, y0 + 318), "WET", font=A.fit_font(d, "WET", A.SANS_BOLD, 72, pw - 30), fill=INK, anchor="mm")
d.text((cx, y0 + 384), "FLOOR", font=A.fit_font(d, "FLOOR", A.SANS_BOLD, 72, pw - 24), fill=INK, anchor="mm")
joke = A.fit_font(d, "Mopped by Sisyphus.", A.SERIF_ITAL, 30, pw - 26)
d.text((cx, y0 + 446), "Mopped by Sisyphus.", font=joke, fill=INK, anchor="mm")
d.text((cx, y0 + 478), "Again.", font=joke, fill=INK, anchor="mm")

# --- The placard -------------------------------------------------------------
x0, y0, x1, y1 = RECTS["placard"]
cx, pw = (x0 + x1) / 2, x1 - x0
d.rectangle((x0 + 14, y0 + 14, x1 - 14, y1 - 14), outline=(90, 70, 40), width=3)
d.rectangle((x0 + 22, y0 + 22, x1 - 22, y1 - 22), outline=(90, 70, 40), width=1)
d.text((cx, y0 + 82), "PLEASE", font=A.fit_font(d, "PLEASE", A.SERIF, 40, pw - 80), fill=INK, anchor="mm")
d.text((cx, y0 + 152), "DO NOT TOUCH", font=A.fit_font(d, "DO NOT TOUCH", A.SERIF_BOLD, 66, pw - 70), fill=INK, anchor="mm")
d.line([(cx - 110, y0 + 208), (cx + 110, y0 + 208)], fill=(90, 70, 40), width=2)
d.text((cx, y0 + 262), "She will know.", font=A.fit_font(d, "She will know.", A.SERIF_ITAL, 50, pw - 80), fill=INK, anchor="mm")

# --- The "Gallery closed" board ------------------------------------------------
x0, y0, x1, y1 = RECTS["closed"]
cx, pw = (x0 + x1) / 2, x1 - x0
RED = (128, 24, 22)
d.rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12), outline=RED, width=10)
d.rectangle((x0 + 30, y0 + 30, x1 - 30, y1 - 30), outline=RED, width=2)
d.text((cx, y0 + 104), "GALLERY", font=A.fit_font(d, "GALLERY", A.SERIF_BOLD, 96, pw - 120), fill=RED, anchor="mm")
d.text((cx, y0 + 196), "CLOSED", font=A.fit_font(d, "CLOSED", A.SERIF_BOLD, 96, pw - 120), fill=RED, anchor="mm")
d.text((cx, y0 + 266), "for re-hanging", font=A.fit_font(d, "for re-hanging", A.SERIF_ITAL, 44, pw - 160), fill=INK, anchor="mm")
d.line([(cx - 150, y0 + 306), (cx + 150, y0 + 306)], fill=RED, width=3)
small = A.fit_font(d, "Pandora's collection is being catalogued.", A.SERIF, 34, pw - 90)
for i, line in enumerate(("Pandora's collection is being catalogued.", "Please do not open anything.")):
    d.text((cx, y0 + 350 + i * 44), line, font=small, fill=INK, anchor="mm")

pic.save(OUT / "int_signs.png")
A.write_layout(HERE / "signs_atlas.json", [W, H], RECTS)
print("wrote", OUT / "int_signs.png")
