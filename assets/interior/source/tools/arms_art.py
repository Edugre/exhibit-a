"""The Hall of Arms set's one texture (asset plan P3.3): bronze, iron, oak, linen and horsehair for three
suits of armour, a spear rack and a display case, plus the Shield of Achilles' face, two painted shields and
the brass labels.
usage: python arms_art.py <out dir>     (writes int_arms.png there)"""
import math
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
S = 1024
rng = np.random.default_rng(3301)

RECTS = {
    # Materials
    "bronze": (0, 0, 256, 256),
    "bronze_dark": (256, 0, 384, 128),
    "iron": (384, 0, 512, 128),
    "wood": (512, 0, 768, 256),
    "leather": (768, 0, 896, 128),
    "crest_red": (896, 0, 1024, 128),
    "crest_black": (768, 128, 896, 256),
    "crest_white": (896, 128, 1024, 256),
    "linen": (256, 128, 384, 256),
    "glass": (384, 128, 512, 256),
    # Prints, each the shape of the face it goes on
    "shield_achilles": (0, 256, 512, 768),   # a disc, 0.72 m across
    "label_ajax": (512, 256, 1024, 384),     # brass plates, 0.40 x 0.10 m
    "label_patroclus": (512, 384, 1024, 512),
    "label_odysseus": (512, 512, 1024, 640),
    "label_spears": (512, 640, 1024, 768),
    "label_shield": (512, 768, 1024, 896),
    "hoplon_a": (0, 768, 256, 1024),         # painted shields, discs 0.9 m across
    "hoplon_b": (256, 768, 512, 1024),
}
INK = (34, 24, 14)

img = np.zeros((S, S, 3), np.float32)


def region(name):
    x0, y0, x1, y1 = RECTS[name]
    return x0, y0, x1, y1, x1 - x0, y1 - y0


def fill(name, rgb, vary=0.03, grain=2.0):
    x0, y0, x1, y1, w, h = region(name)
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (1 + vary * A.blur_noise(rng, w, h, grain))[..., None]


def metal(name, rgb, patina, brushed=0.08):
    """Metal, brushed or hammered smooth, with green patina gathered in blotches."""
    x0, y0, x1, y1, w, h = region(name)
    base = np.array(rgb, np.float32) * (1 + brushed * A.streaks(rng, w, h, 30) + 0.05 * A.blur_noise(rng, w, h, 6))[..., None]
    green = np.clip(A.blur_noise(rng, w, h, 10) * 1.6 - 0.9, 0, 1)[..., None] * patina
    img[y0:y1, x0:x1] = base * (1 - green) + np.array([0.24, 0.42, 0.34], np.float32) * green


# --- Materials -------------------------------------------------------------
metal("bronze", (0.86, 0.64, 0.32), 0.3, brushed=0.015)
metal("bronze_dark", (0.52, 0.36, 0.18), 0.4, brushed=0.015)
metal("iron", (0.30, 0.30, 0.31), 0.0)
x0, y0, x1, y1, w, h = region("wood")
yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
rings = 0.5 + 0.5 * np.sin((yy + 12 * A.blur_noise(rng, w, h, 24)) * 2 * np.pi / 16)
img[y0:y1, x0:x1] = np.array([0.26, 0.15, 0.08], np.float32) * (0.8 + 0.25 * rings + 0.05 * A.streaks(rng, w, h, 40, axis=1))[..., None]
fill("leather", (0.30, 0.17, 0.09), 0.10, 1.2)
for name, rgb in (("crest_red", (0.55, 0.07, 0.06)), ("crest_black", (0.06, 0.05, 0.05)), ("crest_white", (0.86, 0.83, 0.76))):
    x0, y0, x1, y1, w, h = region(name)  # horsehair: fine streaks across the crest
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (0.85 + 0.3 * A.streaks(rng, w, h, 50, axis=1))[..., None]
fill("linen", (0.84, 0.79, 0.66), 0.06, 1.0)
fill("glass", (0.82, 0.90, 0.94), 0.01)
for name in ("label_ajax", "label_patroclus", "label_odysseus", "label_spears", "label_shield"):
    metal(name, (0.80, 0.62, 0.30), 0.0)
metal("shield_achilles", (0.70, 0.50, 0.22), 0.25)
fill("hoplon_a", (0.50, 0.08, 0.06), 0.05)
fill("hoplon_b", (0.08, 0.07, 0.06), 0.05)

pic = A.to_image(img)
d = ImageDraw.Draw(pic)


# --- Labels ------------------------------------------------------------------
def label(name, title, line):
    x0, y0, x1, y1, w, h = region(name)
    d.rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), outline=INK, width=3)
    d.text(((x0 + x1) / 2, y0 + 44), title, font=A.fit_font(d, title, A.SERIF_BOLD, 46, w - 60), fill=INK, anchor="mm")
    d.text(((x0 + x1) / 2, y0 + 94), line, font=A.fit_font(d, line, A.SERIF_ITAL, 30, w - 50), fill=INK, anchor="mm")


label("label_ajax", "AJAX THE GREATER", "Bronze panoply, c. 1200 BC. Still sulking.")
label("label_patroclus", "PATROCLUS", "Borrowed from a friend. Please return.")
label("label_odysseus", "ODYSSEUS", "Bronze panoply. Arrived ten years late.")
label("label_spears", "SPEARS OF THE MYRMIDONS", "Please count them on your way out.")
label("label_shield", "THE SHIELD OF ACHILLES", "By Hephaestus. Heel sold separately.")


# --- The Shield of Achilles: the world in rings, as the Iliad has it -----------
def shield(name):
    x0, y0, x1, y1, w, h = region(name)
    ss = 3
    big = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    g = ImageDraw.Draw(big)
    c = w * ss / 2
    gold, dark, light = (226, 182, 92, 255), (92, 58, 24, 255), (246, 214, 140, 255)

    def ring(r0, r1, colour):
        g.ellipse((c - r1 * ss, c - r1 * ss, c + r1 * ss, c + r1 * ss), fill=colour)
        g.ellipse((c - r0 * ss, c - r0 * ss, c + r0 * ss, c + r0 * ss), fill=(0, 0, 0, 0))

    ring(244, 256, light)                     # the rim
    ring(208, 244, dark)                      # Ocean, round the edge
    for k in range(40):                       # its waves
        a = k / 40 * math.tau
        px, py = c + 226 * ss * math.cos(a), c + 226 * ss * math.sin(a)
        g.arc((px - 12 * ss, py - 12 * ss, px + 12 * ss, py + 12 * ss), math.degrees(a) + 90, math.degrees(a) + 270, fill=gold, width=3 * ss)
    ring(200, 208, light)
    ring(146, 200, (120, 78, 32, 255))        # a ring of dancers, hand in hand
    for k in range(28):
        a = k / 28 * math.tau
        px, py = c + 173 * ss * math.cos(a), c + 173 * ss * math.sin(a)
        ux, uy = math.cos(a), math.sin(a)     # outwards = up for the figure
        tx, ty = -uy, ux
        head = (px + ux * 15 * ss, py + uy * 15 * ss)
        g.ellipse((head[0] - 5 * ss, head[1] - 5 * ss, head[0] + 5 * ss, head[1] + 5 * ss), fill=gold)
        g.line([(px + ux * 10 * ss, py + uy * 10 * ss), (px - ux * 6 * ss, py - uy * 6 * ss)], fill=gold, width=4 * ss)
        for side in (-1, 1):
            g.line([(px - ux * 6 * ss, py - uy * 6 * ss), (px - ux * 20 * ss + side * tx * 7 * ss, py - uy * 20 * ss + side * ty * 7 * ss)], fill=gold, width=3 * ss)
            g.line([(px + ux * 6 * ss, py + uy * 6 * ss), (px + ux * 2 * ss + side * tx * 13 * ss, py + uy * 2 * ss + side * ty * 13 * ss)], fill=gold, width=3 * ss)
    ring(138, 146, light)
    ring(68, 138, (52, 40, 30, 255))          # the heavens, with their stars
    stars = np.random.default_rng(3302)
    for _ in range(46):
        a, r = stars.uniform(0, math.tau), stars.uniform(78, 130)
        px, py, s = c + r * ss * math.cos(a), c + r * ss * math.sin(a), stars.uniform(1.6, 3.4) * ss
        g.ellipse((px - s, py - s, px + s, py + s), fill=light)
    ring(60, 68, light)
    ring(0, 60, gold)                         # the sun at the boss
    for k in range(16):
        a = k / 16 * math.tau
        g.line([(c + 18 * ss * math.cos(a), c + 18 * ss * math.sin(a)), (c + 50 * ss * math.cos(a), c + 50 * ss * math.sin(a))], fill=dark, width=4 * ss)
    g.ellipse((c - 16 * ss, c - 16 * ss, c + 16 * ss, c + 16 * ss), fill=light)
    small = big.resize((w, h), Image.LANCZOS)
    pic.paste(small, (x0, y0), small)


shield("shield_achilles")


# --- Two painted hoplons: a scorpion for Ajax, an owl-eyed ring for Patroclus ---
def hoplon(name, device):
    x0, y0, x1, y1, w, h = region(name)
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    d.ellipse((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=(210, 164, 80), width=14)
    if device == "scorpion":
        body = [(c[0], c[1] - 70 + i * 16) for i in range(9)]
        for i, (px, py) in enumerate(body):
            r = 14 - abs(i - 3) * 1.2
            d.ellipse((px - r, py - r, px + r, py + r), fill=(226, 196, 120))
        for side in (-1, 1):
            for k in range(3):
                d.line([(c[0], c[1] - 40 + k * 18), (c[0] + side * 48, c[1] - 56 + k * 22)], fill=(226, 196, 120), width=5)
            d.line([(c[0], c[1] - 70), (c[0] + side * 34, c[1] - 98), (c[0] + side * 20, c[1] - 112)], fill=(226, 196, 120), width=7)
        d.line([(c[0], c[1] + 58), (c[0] + 30, c[1] + 86), (c[0] + 14, c[1] + 98)], fill=(226, 196, 120), width=7)
    else:
        for r, colour in ((70, (226, 196, 120)), (46, (16, 14, 12)), (22, (226, 196, 120))):
            d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=colour)


hoplon("hoplon_a", "scorpion")
hoplon("hoplon_b", "rings")

pic.save(OUT / "int_arms.png")
A.write_layout(HERE / "arms_atlas.json", [S, S], RECTS)
print("wrote", OUT / "int_arms.png")
