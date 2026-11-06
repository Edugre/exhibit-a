"""The museum's library card for the end of a heist, and the rubber stamps that land on it.
usage: python make_card.py <ui dir>"""
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = pathlib.Path(sys.argv[1])
BOLD = "C:/Windows/Fonts/palab.ttf"
ITAL = "C:/Windows/Fonts/palai.ttf"
BLOCK = "C:/Windows/Fonts/arialbd.ttf"
W, H = 1520, 940
RULE_TOP, RULE_STEP = 216, 76        # twice what the card shows on screen, for sharp text
rng = np.random.default_rng(47)


def blur_noise(w, h, radius):
    img = Image.fromarray((rng.random((h, w)) * 255).astype(np.uint8))
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
    return (a - a.mean()) / max(a.std(), 1e-4)


# Buff card stock, aged darker towards the edges, with fibres in it
paper = np.ones((H, W, 3), np.float32) * np.array([0.90, 0.84, 0.70], np.float32)
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
edge = np.minimum(np.minimum(x, W - x) / 260, np.minimum(y, H - y) / 200).clip(0, 1)
paper *= (0.84 + 0.16 * edge ** 0.6)[..., None]
paper *= (1 + 0.018 * blur_noise(W, H, 40) + 0.022 * blur_noise(W, H, 3) + 0.012 * blur_noise(W, H, 0.7))[..., None]
img = Image.fromarray((paper.clip(0, 1) * 255).astype(np.uint8))
d = ImageDraw.Draw(img)

# Ruled lines, a red margin, and the printed heading
INK = (58, 42, 34)
RED = (150, 44, 36)
BLUE = (110, 128, 158)
for i in range(7):
    yy = RULE_TOP + RULE_STEP * i
    d.line([(44, yy), (W - 44, yy)], fill=BLUE, width=2)
d.line([(330, 150), (330, RULE_TOP + RULE_STEP * 6 + 26)], fill=RED, width=3)
d.line([(338, 150), (338, RULE_TOP + RULE_STEP * 6 + 26)], fill=RED, width=1)
d.line([(44, 148), (W - 44, 148)], fill=RED, width=5)
d.text((W / 2 + 40, 58), "MVSEVM ALEXANDRINVM", font=ImageFont.truetype(BOLD, 58), fill=INK, anchor="mm")
d.text((W / 2 + 40, 112), "Circulation Record. Please do not lose this card. She will know.", font=ImageFont.truetype(ITAL, 34), fill=INK, anchor="mm")

# The owl from the museum's flag, small, in the corner of the heading
cx, cy = 104, 80
d.ellipse([cx - 44, cy - 50, cx + 44, cy + 46], outline=INK, width=5)
for sx in (-1, 1):
    d.ellipse([cx + sx * 20 - 13, cy - 24, cx + sx * 20 + 13, cy + 2], outline=INK, width=4)
    d.line([(cx + sx * 6, cy - 34), (cx + sx * 34, cy - 46)], fill=INK, width=5)
    d.ellipse([cx + sx * 20 - 4, cy - 15, cx + sx * 20 + 4, cy - 7], fill=INK)
d.polygon([(cx - 7, cy + 2), (cx + 7, cy + 2), (cx, cy + 18)], fill=INK)

# A coffee ring from some long-dead librarian
ring = Image.new("L", (W, H), 0)
rd = ImageDraw.Draw(ring)
rd.ellipse([1150, 560, 1490, 900], outline=70, width=14)
ring = ring.filter(ImageFilter.GaussianBlur(3))
broken = (np.asarray(ring, dtype=np.float32) / 255) * (0.65 + 0.35 * blur_noise(W, H, 14).clip(-1, 1))
a = np.asarray(img, dtype=np.float32)
a *= 1 - (broken[..., None] * np.array([0.5, 0.75, 1.0], np.float32))

# Rounded corners, a punched hole at the foot
alpha = Image.new("L", (W, H), 0)
ad = ImageDraw.Draw(alpha)
ad.rounded_rectangle([0, 0, W - 1, H - 1], 26, fill=255)
ad.ellipse([W / 2 - 34, H - 72, W / 2 + 34, H - 4], fill=0)
out = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
out.putalpha(alpha.filter(ImageFilter.GaussianBlur(1)))
out.save(OUT / "library_card.png", optimize=True)


def stamp(name, top, bottom):
    sw, sh = 760, 300
    im = Image.new("L", (sw, sh), 0)
    s = ImageDraw.Draw(im)
    s.rounded_rectangle([10, 10, sw - 11, sh - 11], 22, outline=255, width=12)
    s.rounded_rectangle([28, 28, sw - 29, sh - 29], 14, outline=255, width=4)
    if bottom:
        s.text((sw / 2, 112), top, font=ImageFont.truetype(BLOCK, 92), fill=255, anchor="mm")
        s.text((sw / 2, 210), bottom, font=ImageFont.truetype(BLOCK, 76), fill=255, anchor="mm")
    else:
        s.text((sw / 2, sh / 2), top, font=ImageFont.truetype(BLOCK, 112), fill=255, anchor="mm")
    ink = np.asarray(im, dtype=np.float32) / 255
    # A real stamp never inks evenly: patches run dry and the grain of the card shows through
    dry = blur_noise(sw, sh, 30) * 0.5 + blur_noise(sw, sh, 2.0) * 0.6
    ink *= ((dry + 1.25) / 0.7).clip(0, 1)
    rgba = np.zeros((sh, sw, 4), np.uint8)
    rgba[..., :3] = (168, 26, 22)
    rgba[..., 3] = (ink.clip(0, 1) * 235).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT / f"stamp_{name}.png", optimize=True)


stamp("withdrawn", "WITHDRAWN", "")
stamp("revoked", "PRIVILEGES", "REVOKED")
stamp("closed", "LIBRARY", "CLOSED")
print("card written")
