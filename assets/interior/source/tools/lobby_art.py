"""The lobby set's one texture (asset plan P3.5): wood, marble, brass and coat wool for the furniture,
and the printed signs, map and banners.
usage: python lobby_art.py <out dir>     (writes int_lobby.png there)"""
import pathlib
import sys
import numpy as np
from PIL import ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
S = 1024
rng = np.random.default_rng(3501)

RECTS = {
    # Materials
    "wood": (0, 0, 256, 256),
    "marble": (256, 0, 512, 256),
    "brass": (512, 0, 640, 128),
    "wool_a": (640, 0, 768, 128),
    "wool_b": (768, 0, 896, 128),
    "dark": (896, 0, 1024, 128),
    "paper": (512, 128, 640, 256),
    "shade": (640, 128, 768, 256),
    "glass": (768, 128, 896, 256),
    # Prints, each the shape of the face it goes on
    "sign_tickets": (0, 256, 512, 384),      # 0.60 x 0.15 m
    "sign_coats": (512, 256, 1024, 384),     # 1.20 x 0.30 m
    "sign_donate": (0, 384, 384, 640),       # 0.36 x 0.24 m
    "map": (384, 384, 1024, 832),            # 1.00 x 0.70 m
    "banner_book": (0, 640, 192, 1024),      # 1.20 x 2.40 m
    "banner_gift": (192, 640, 384, 1024),
}
INK = (24, 20, 18)
GOLD = (232, 196, 110)
CREAM = (238, 228, 204)

img = np.zeros((S, S, 3), np.float32)


def region(name):
    x0, y0, x1, y1 = RECTS[name]
    return x0, y0, x1, y1, x1 - x0, y1 - y0


def fill(name, rgb, vary=0.03, grain=2.0):
    x0, y0, x1, y1, w, h = region(name)
    img[y0:y1, x0:x1] = np.array(rgb, np.float32) * (1 + vary * A.blur_noise(rng, w, h, grain))[..., None]


# --- Materials -------------------------------------------------------------
x0, y0, x1, y1, w, h = region("wood")
yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
rings = 0.5 + 0.5 * np.sin((yy + 10 * A.blur_noise(rng, w, h, 28)) * 2 * np.pi / 18)
img[y0:y1, x0:x1] = np.array([0.36, 0.20, 0.11], np.float32) * (0.8 + 0.25 * rings + 0.05 * A.streaks(rng, w, h, 40, axis=1))[..., None]
x0, y0, x1, y1, w, h = region("marble")
vein = np.abs(A.blur_noise(rng, w, h, 14) + 0.5 * A.blur_noise(rng, w, h, 5))  # thin veins where the noise crosses zero
img[y0:y1, x0:x1] = np.array([0.90, 0.87, 0.82], np.float32) * (1 - 0.22 * np.exp(-(vein / 0.07) ** 2) + 0.02 * A.blur_noise(rng, w, h, 30))[..., None]
x0, y0, x1, y1, w, h = region("brass")
img[y0:y1, x0:x1] = np.array([0.80, 0.62, 0.30], np.float32) * (1 + 0.07 * A.streaks(rng, w, h, 30))[..., None]
fill("wool_a", (0.20, 0.17, 0.22), 0.08, 0.8)
fill("wool_b", (0.42, 0.30, 0.18), 0.08, 0.8)
fill("dark", (0.07, 0.07, 0.07), 0.05)
fill("paper", (0.93, 0.91, 0.86), 0.02)
fill("shade", (0.10, 0.42, 0.24), 0.04)
fill("glass", (0.82, 0.90, 0.94), 0.01)
fill("sign_tickets", (0.14, 0.11, 0.08), 0.03)
fill("sign_coats", (0.14, 0.11, 0.08), 0.03)
fill("sign_donate", CREAM and (0.92, 0.88, 0.78), 0.02)
fill("map", (0.92, 0.89, 0.80), 0.02)
fill("banner_book", (0.42, 0.06, 0.07), 0.05, 1.5)
fill("banner_gift", (0.08, 0.24, 0.17), 0.05, 1.5)

pic = A.to_image(img)
d = ImageDraw.Draw(pic)


def centred(name, y, text, path, size, fill_colour, pad=24):
    x0, y0, x1, y1, w, h = region(name)
    font = A.fit_font(d, text, path, size, w - 2 * pad)
    d.text(((x0 + x1) / 2, y0 + y), text, font=font, fill=fill_colour, anchor="mm")


def frame(name, colour, inset=8, width=3):
    x0, y0, x1, y1, w, h = region(name)
    d.rectangle((x0 + inset, y0 + inset, x1 - inset, y1 - inset), outline=colour, width=width)


# --- Signs ---------------------------------------------------------------------
frame("sign_tickets", GOLD)
centred("sign_tickets", 46, "TICKETS", A.SERIF_BOLD, 54, GOLD)
centred("sign_tickets", 96, "Admission free. Leaving costs extra.", A.SERIF_ITAL, 34, CREAM)

frame("sign_coats", GOLD)
centred("sign_coats", 48, "COAT CHECK", A.SERIF_BOLD, 58, GOLD)
centred("sign_coats", 98, "Golden fleeces left at owner's risk", A.SERIF_ITAL, 34, CREAM)

frame("sign_donate", (90, 70, 40), 10, 3)
centred("sign_donate", 52, "PLEASE GIVE", A.SERIF, 30, INK)
centred("sign_donate", 104, "Help us rebuild the", A.SERIF, 30, INK)
centred("sign_donate", 146, "LIBRARY OF", A.SERIF_BOLD, 40, INK)
centred("sign_donate", 188, "ALEXANDRIA", A.SERIF_BOLD, 40, INK)
centred("sign_donate", 228, "Fireproof edition coming soon", A.SERIF_ITAL, 24, INK)

# --- The map: the lobby, three unknown rooms, the gallery and the vault ----------------
x0, y0, x1, y1, w, h = region("map")
frame("map", (70, 55, 35), 10, 4)
centred("map", 44, "MUSEUM MAP", A.SERIF_BOLD, 44, INK)
cx = (x0 + x1) / 2
plan_top, plan_bottom = y0 + 78, y1 - 78
rows = [("VAULT", "staff only"), ("GALLERY", ""), ("?", ""), ("?", ""), ("?", ""), ("LOBBY", "")]
row_h = (plan_bottom - plan_top) / len(rows)
for i, (label, note) in enumerate(rows):
    top = plan_top + i * row_h + 4
    half = 92 if label in ("?",) else (70 if label == "VAULT" else 130)
    box = (cx - half, top, cx + half, top + row_h - 8)
    d.rectangle(box, outline=INK, width=3, fill=(214, 204, 178) if label == "?" else None)
    font = A.fit_font(d, label, A.SERIF_BOLD if label != "?" else A.SANS_BOLD, 26, 2 * half - 16)
    d.text((cx, (box[1] + box[3]) / 2), label, font=font, fill=INK, anchor="mm")
    if note:
        d.text((box[2] + 14, (box[1] + box[3]) / 2), note, font=A.fit_font(d, note, A.SERIF_ITAL, 22, 160), fill=INK, anchor="lm")
# You are here, in the lobby
lobby_mid_y = plan_top + 5 * row_h + row_h / 2
d.ellipse((cx - 112 - 9, lobby_mid_y - 9, cx - 112 + 9, lobby_mid_y + 9), fill=(190, 30, 30))
d.text((cx - 130, lobby_mid_y), "You are here", font=A.fit_font(d, "You are here", A.SERIF_ITAL, 24, 130), fill=(160, 24, 24), anchor="rm")
centred("map", h - 42, "Rooms are rearranged every night. Please do not ask.", A.SERIF_ITAL, 26, INK)

# --- Banners ----------------------------------------------------------------------
x0, y0, x1, y1, w, h = region("banner_book")
frame("banner_book", GOLD, 8, 2)
centred("banner_book", 46, "TONIGHT ONLY", A.SANS_BOLD, 22, GOLD, 30)
for i, word in enumerate(["THE", "LAST", "BOOK", "OF", "ALEX-", "ANDRIA"]):
    centred("banner_book", 104 + i * 40, word, A.SERIF_BOLD, 40, CREAM, 22)
centred("banner_book", 356, "one copy · no returns", A.SERIF_ITAL, 18, GOLD, 22)

x0, y0, x1, y1, w, h = region("banner_gift")
frame("banner_gift", GOLD, 8, 2)
centred("banner_gift", 50, "GIFT", A.SERIF_BOLD, 46, CREAM, 22)
centred("banner_gift", 96, "SHOP", A.SERIF_BOLD, 46, CREAM, 22)
# A little wooden horse on wheels
hx, hy = (x0 + x1) / 2, y0 + 196
d.rectangle((hx - 38, hy - 18, hx + 30, hy + 12), fill=GOLD)                 # body
d.rectangle((hx + 18, hy - 52, hx + 34, hy - 10), fill=GOLD)                 # neck
d.rectangle((hx + 20, hy - 62, hx + 52, hy - 44), fill=GOLD)                 # head
for lx in (hx - 30, hx - 10, hx + 6, hx + 22):
    d.rectangle((lx, hy + 12, lx + 7, hy + 34), fill=GOLD)                   # legs
d.rectangle((hx - 46, hy + 34, hx + 40, hy + 40), fill=GOLD)                 # plank
for wx in (hx - 34, hx + 28):
    d.ellipse((wx - 9, hy + 36, wx + 9, hy + 54), outline=GOLD, width=3)     # wheels
centred("banner_gift", 290, "Beware of Greeks", A.SERIF_ITAL, 22, CREAM, 18)
centred("banner_gift", 318, "bearing gifts", A.SERIF_ITAL, 22, CREAM, 18)
centred("banner_gift", 356, "this way, please", A.SERIF, 18, GOLD, 22)

pic.save(OUT / "int_lobby.png")
A.write_layout(HERE / "lobby_atlas.json", [S, S], RECTS)
print("wrote", OUT / "int_lobby.png")
