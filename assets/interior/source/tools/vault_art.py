"""The vault room set's one texture (asset plan P3.6): gilt for two empty frames and their cards and labels,
and steel, brass and a sign for the vault's empty library shelving.
usage: python vault_art.py <out dir>     (writes int_vault.png there)"""
import pathlib
import sys
import numpy as np
from PIL import ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
W, H = 1024, 512
rng = np.random.default_rng(3601)

RECTS = {
    # Materials
    "gilt": (0, 0, 256, 256),
    "steel": (256, 0, 384, 128),
    "steel_dark": (384, 0, 512, 128),
    "brass": (256, 128, 384, 256),
    "card": (384, 128, 512, 256),
    # Prints, each the shape of the face it goes on
    "card_helen": (512, 0, 768, 170),        # 0.30 x 0.20 m, hung in the empty frame
    "card_hector": (768, 0, 1024, 170),
    "label_helen": (512, 180, 1024, 276),    # 0.30 x 0.056 m, on the wall under the frame
    "label_hector": (512, 280, 1024, 376),
    "shelf_sign": (0, 256, 512, 352),        # 1.6 x 0.3 m, along the top of the shelving
    "shelf_card": (0, 360, 192, 488),        # 0.15 x 0.10 m, propped on the middle shelf
}
INK = (30, 24, 18)
BRASS_INK = (44, 30, 12)

img = np.zeros((H, W, 3), np.float32)


def region(name):
    x0, y0, x1, y1 = RECTS[name]
    return x0, y0, x1, y1, x1 - x0, y1 - y0


def fill(name, rgb, vary=0.03, grain=2.0):
    x0, y0, x1, y1, w, h = region(name)
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (1 + vary * A.blur_noise(rng, w, h, grain))[..., None]


def brushed(name, rgb, amount):
    x0, y0, x1, y1, w, h = region(name)
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (1 + amount * A.streaks(rng, w, h, 40) + 0.04 * A.blur_noise(rng, w, h, 5))[..., None]


# --- Materials -------------------------------------------------------------
x0, y0, x1, y1, w, h = region("gilt")  # gold leaf, rubbed through to red bole on the high spots
leaf = A.blur_noise(rng, w, h, 3)
bole = np.clip(A.blur_noise(rng, w, h, 14) * 1.5 - 1.0, 0, 1)[..., None]
gold = np.array([0.86, 0.66, 0.30], np.float32) * (1 + 0.08 * leaf)[..., None]
img[y0:y1, x0:x1] = gold * (1 - 0.6 * bole) + np.array([0.45, 0.16, 0.08], np.float32) * 0.6 * bole
brushed("steel", (0.55, 0.57, 0.58), 0.05)
brushed("steel_dark", (0.20, 0.21, 0.22), 0.05)
brushed("brass", (0.80, 0.62, 0.30), 0.07)
fill("card", (0.93, 0.90, 0.82), 0.02)
for name in ("card_helen", "card_hector", "shelf_card"):
    fill(name, (0.93, 0.90, 0.82), 0.02)
for name in ("label_helen", "label_hector", "shelf_sign"):
    brushed(name, (0.80, 0.62, 0.30), 0.05)

pic = A.to_image(img)
d = ImageDraw.Draw(pic)


def lines(name, rows, colour, border=None):
    """rows: (text, font path, size, y from the top)"""
    x0, y0, x1, y1, w, h = region(name)
    if border:
        d.rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), outline=border, width=3)
    for text, font, size, y in rows:
        d.text(((x0 + x1) / 2, y0 + y), text, font=A.fit_font(d, text, font, size, w - 36), fill=colour, anchor="mm")


lines("card_helen", [("ON LOAN", A.SERIF_BOLD, 46, 44), ("to Sparta.", A.SERIF_ITAL, 34, 96), ("Our apologies to Troy.", A.SERIF, 26, 138)], INK, (120, 30, 26))
lines("card_hector", [("REMOVED", A.SERIF_BOLD, 46, 44), ("at the request of", A.SERIF_ITAL, 30, 96), ("Achilles.", A.SERIF_ITAL, 34, 136)], INK, (120, 30, 26))
lines("label_helen", [("HELEN OF TROY", A.SERIF_BOLD, 38, 32), ("The face that launched a thousand ships", A.SERIF_ITAL, 26, 70)], BRASS_INK)
lines("label_hector", [("HECTOR, PRINCE OF TROY", A.SERIF_BOLD, 38, 32), ("Oil on canvas · Tamer of horses", A.SERIF_ITAL, 26, 70)], BRASS_INK)
lines("shelf_sign", [("THE LIBRARY OF ALEXANDRIA", A.SERIF_BOLD, 44, 36), ("Complete collection", A.SERIF_ITAL, 30, 74)], BRASS_INK, BRASS_INK)
lines("shelf_card", [("For the other", A.SERIF, 22, 22), ("399,999 volumes,", A.SERIF, 22, 50), ("see: Fire, 48 BC.", A.SERIF_ITAL, 22, 80), ("— The Curator", A.SERIF_ITAL, 18, 108)], INK)

pic.save(OUT / "int_vault.png")
A.write_layout(HERE / "vault_atlas.json", [W, H], RECTS)
print("wrote", OUT / "int_vault.png")
