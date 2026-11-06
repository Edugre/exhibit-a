"""The three great hanging banners, printed in numpy and PIL: one texture, three designs side by side.
usage: python make_banners.py <out dir>"""
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
W, H = 4096, 1024
COL = W // 3
BOLD = "C:/Windows/Fonts/palab.ttf"
REG = "C:/Windows/Fonts/pala.ttf"
ITAL = "C:/Windows/Fonts/palai.ttf"
GOLD = (222, 186, 118)
PALE = (232, 218, 190)


def font(path, size):
    return ImageFont.truetype(path, size)


def spaced(d, cx, y, text, f, fill, gap):
    widths = [d.textlength(c, font=f) for c in text]
    x = cx - (sum(widths) + gap * (len(text) - 1)) / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill, anchor="lm")
        x += w + gap


def border(d, x0, x1, colour):
    d.rectangle([x0 + 34, 34, x1 - 34, H - 34], outline=colour, width=6)
    d.rectangle([x0 + 50, 50, x1 - 50, H - 50], outline=colour, width=2)


def tome(d, cx, cy, s):
    """The Last Book, with its burning edge."""
    glow = [(cx - 1.2 * s, cy - 0.78 * s), (cx + 1.2 * s, cy - 0.78 * s), (cx + 1.2 * s, cy + 0.78 * s), (cx - 1.2 * s, cy + 0.78 * s)]
    d.polygon(glow, fill=(255, 136, 44))
    d.polygon([(cx - 1.12 * s, cy - 0.70 * s), (cx + 1.12 * s, cy - 0.70 * s), (cx + 1.12 * s, cy + 0.70 * s), (cx - 1.12 * s, cy + 0.70 * s)], fill=(38, 20, 15))
    d.line([(cx, cy - 0.70 * s), (cx, cy + 0.70 * s)], fill=GOLD, width=8)
    for sx in (-1, 1):
        d.rectangle([cx + sx * 0.14 * s if sx > 0 else cx - 1.02 * s, cy - 0.60 * s, cx + 1.02 * s if sx > 0 else cx - 0.14 * s, cy + 0.60 * s], outline=GOLD, width=4)
    # the wheeled horse on the cover
    q = lambda x, y: (cx + 0.58 * s + x * 0.62 * s, cy + y * 0.62 * s)
    d.polygon([q(-0.7, -0.05), q(-0.6, -0.2), q(0.1, -0.2), q(0.35, -0.65), q(0.62, -0.5), q(0.42, -0.35), q(0.34, 0.1), q(-0.6, 0.1)], fill=GOLD)
    for x in (-0.55, -0.3, 0.05, 0.28):
        d.rectangle([q(x - 0.05, 0.1), q(x + 0.05, 0.5)], fill=GOLD)
    d.rectangle([q(-0.72, 0.5), q(0.5, 0.58)], fill=GOLD)
    for x in (-0.5, 0.25):
        p = q(x, 0.68)
        d.ellipse([p[0] - 16, p[1] - 16, p[0] + 16, p[1] + 16], fill=GOLD)
    for i in range(5):
        y = cy - 0.42 * s + i * 0.21 * s
        d.line([(cx - 0.9 * s, y), (cx - 0.28 * s, y)], fill=(150, 118, 76), width=4)


def heel(d, cx, cy, s, col):
    """A broken marble foot with an arrow through its heel."""
    d.polygon([(cx - 0.9 * s, cy - 0.55 * s), (cx - 0.25 * s, cy - 0.62 * s), (cx - 0.10 * s, cy - 0.05 * s), (cx + 0.55 * s, cy + 0.12 * s), (cx + 1.0 * s, cy + 0.30 * s), (cx + 1.02 * s, cy + 0.52 * s),
               (cx - 0.72 * s, cy + 0.54 * s), (cx - 0.96 * s, cy + 0.2 * s)], fill=col)
    for i in range(5):
        x = cx + (0.62 + i * 0.1) * s
        d.ellipse([x - 22, cy + 0.26 * s + i * 2, x + 22, cy + 0.26 * s + i * 2 + 42], fill=(246, 234, 208))
    d.line([(cx - 1.5 * s, cy + 0.15 * s), (cx - 0.6 * s, cy + 0.34 * s)], fill=(70, 34, 26), width=15)
    d.polygon([(cx - 0.72 * s, cy + 0.25 * s), (cx - 0.46 * s, cy + 0.38 * s), (cx - 0.76 * s, cy + 0.44 * s)], fill=(70, 34, 26))
    for i in range(3):
        d.line([(cx - (1.5 - i * 0.1) * s, cy + 0.15 * s), (cx - (1.62 - i * 0.1) * s, cy + (0.0 + 0.03 * i) * s)], fill=(70, 34, 26), width=8)


FEMALE = [(0.61, 0.23), (0.65, 0.29), (0.66, 0.345), (0.648, 0.375), (0.675, 0.43), (0.70, 0.47), (0.69, 0.49), (0.655, 0.50), (0.665, 0.522), (0.648, 0.54),
          (0.66, 0.56), (0.645, 0.585), (0.645, 0.62), (0.625, 0.65), (0.565, 0.655), (0.545, 0.78), (0.60, 0.90), (0.30, 0.90), (0.37, 0.74), (0.34, 0.60), (0.31, 0.46),
          (0.33, 0.31), (0.42, 0.20), (0.52, 0.17)]


def profile(d, cx, cy, s, col, hair):
    q = lambda x, y: (cx + (x - 0.5) * s, cy + (y - 0.5) * s)
    d.polygon([q(x, y) for x, y in FEMALE], fill=col)
    p = q(0.32, 0.30)
    r = 0.13 * s
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=hair)
    d.polygon([q(x, y) for x, y in ((0.62, 0.22), (0.54, 0.14), (0.40, 0.15), (0.31, 0.26), (0.30, 0.44), (0.36, 0.60), (0.46, 0.52), (0.50, 0.36), (0.58, 0.29))], fill=hair)


def ships(d, x0, x1, y, col):
    for i in range(9):
        x = x0 + (x1 - x0) * (i + 0.5) / 9
        s = 15
        d.polygon([(x - 2.2 * s, y), (x + 2.2 * s, y), (x + 1.4 * s, y + 1.0 * s), (x - 1.4 * s, y + 1.0 * s)], fill=col)
        d.polygon([(x, y - 2.6 * s), (x, y - 0.1 * s), (x + 1.6 * s, y - 0.5 * s)], fill=col)


im = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(im)

# Achilles, on bronze-dark blue
x0, x1 = 0, COL
d.rectangle([x0, 0, x1, H], fill=(24, 38, 58))
border(d, x0, x1, GOLD)
cx = (x0 + x1) // 2
spaced(d, cx, 196, "ACHILLES", font(BOLD, 190), GOLD, 22)
heel(d, cx, 500, 190, (214, 204, 186))
d.text((cx, 770), "A Retrospective", font=font(ITAL, 92), fill=PALE, anchor="mm")
d.text((cx, 884), "Heel not included.", font=font(REG, 60), fill=GOLD, anchor="mm")

# The Last Book, on oxblood
def book_panel(d, x0, x1, bg, headline, footnote):
    d.rectangle([x0, 0, x1, H], fill=bg)
    border(d, x0, x1, GOLD)
    cx = (x0 + x1) // 2
    spaced(d, cx, 136, "THE LAST BOOK", font(BOLD, 120), GOLD, 14)
    spaced(d, cx, 262, "OF ALEXANDRIA", font(BOLD, 120), GOLD, 14)
    tome(d, cx, 508, 150)
    spaced(d, cx, 758, headline, font(BOLD, 134), PALE, 14)
    d.text((cx, 888), footnote, font=font(ITAL, 60), fill=GOLD, anchor="mm")


book_panel(d, COL, 2 * COL, (84, 19, 18), "NOW OVERDUE", "Please do not touch. She will know.")
# The same banner once the Book has gone, its colour gone from oxblood to alarm
stolen = Image.new("RGB", (W, H), (0, 0, 0))
book_panel(ImageDraw.Draw(stolen), COL, 2 * COL, (132, 16, 14), "NOW STOLEN", "She knows.")

# Helen, on deep teal
x0, x1 = 2 * COL, 3 * COL
d.rectangle([x0, 0, x1, H], fill=(18, 58, 60))
border(d, x0, x1, GOLD)
cx = (x0 + x1) // 2
spaced(d, cx, 158, "HELEN OF TROY", font(BOLD, 132), GOLD, 12)
profile(d, cx, 462, 500, (224, 206, 176), GOLD)
ships(d, x0 + 90, x1 - 90, 716, GOLD)
d.text((cx, 800), "The Face That Launched a Thousand Ships", font=font(ITAL, 62), fill=PALE, anchor="mm")
d.text((cx, 888), "Ships sold separately.", font=font(REG, 56), fill=GOLD, anchor="mm")

# Woven cloth: fine weave, soft sun fading, and the long folds of heavy fabric
a = np.asarray(im, dtype=np.float32) / 255
rng = np.random.default_rng(5)
weave = 0.965 + 0.035 * np.sin(np.arange(H)[:, None] * 2.4) * np.sin(np.arange(W)[None, :] * 2.4)
noise = np.asarray(Image.fromarray((rng.random((H // 8, W // 8)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255
folds = 0.90 + 0.10 * np.sin(np.arange(W)[None, :] / W * 3.0 * 2 * np.pi * 5.0 + 1.3)
a *= (weave * (0.93 + 0.14 * noise) * folds)[..., None]
Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(OUT / "ext_banners.png", optimize=True)
b = np.asarray(stolen, dtype=np.float32) / 255
b *= (weave * (0.93 + 0.14 * noise) * folds)[..., None]
Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8)).crop((COL, 0, 2 * COL, H)).save(OUT / "ext_banner_stolen.png", optimize=True)
print("banners written")
