"""The one texture every street prop shares: a strip of flat colours plus all the printed signs, and a
matching map of what glows at night. Writes ext_props.png, ext_props_glow.png and props_layout.json.
usage: python make_props_art.py <out dir>"""
import json
import pathlib
import sys
from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
BOLD, SERIF, SANS = "C:/Windows/Fonts/palab.ttf", "C:/Windows/Fonts/pala.ttf", "C:/Windows/Fonts/arialbd.ttf"
S = 2048
art = Image.new("RGB", (S, S), (40, 40, 44))
glow = Image.new("RGB", (S, S), (0, 0, 0))
da, dg = ImageDraw.Draw(art), ImageDraw.Draw(glow)
layout = {"colours": {}, "signs": {}}

COLOURS = {"steel": (150, 152, 156), "iron": (34, 36, 38), "black": (14, 14, 16), "white": (226, 224, 216), "taxi": (232, 176, 32), "red": (150, 36, 30), "sign_green": (20, 92, 62),
           "wood": (106, 72, 44), "rubber": (22, 22, 24), "chrome": (190, 194, 200), "awning_red": (160, 44, 38), "awning_cream": (222, 208, 176), "glass": (20, 26, 34), "granite": (96, 96, 100),
           "bronze": (92, 68, 44), "navy": (24, 34, 66), "sedan": (46, 54, 70), "maroon": (86, 28, 32), "van_white": (196, 196, 192), "concrete": (128, 126, 120), "hedge": (34, 56, 38), "pale": (176, 170, 158)}
GLOWS = {"bulb": (255, 214, 150), "headlamp": (255, 240, 214), "tail": (255, 30, 18), "signal_red": (255, 36, 20), "signal_green": (40, 255, 150), "taxi_lit": (255, 226, 120)}
x, y = 0, 0
for name, col in list(COLOURS.items()) + list(GLOWS.items()):
    r = (x, y, x + 62, y + 62)
    da.rectangle(r, fill=col)
    if name in GLOWS:
        dg.rectangle(r, fill=col)
    layout["colours"][name] = [(x + 31) / S, 1 - (y + 31) / S]
    x += 64
    if x >= S:
        x, y = 0, y + 64
top = y + 64


def font(path, size):
    return ImageFont.truetype(path, size)


def sign(name, w, h, bg, lit=False):
    global cx, cy, row
    if cx + w > S:
        cx, cy = 0, cy + row
        row = 0
    row = max(row, h + 6)
    rect = (cx, cy, cx + w, cy + h)
    layout["signs"][name] = [rect[0] / S, 1 - rect[3] / S, rect[2] / S, 1 - rect[1] / S]
    cx += w + 6
    panel = Image.new("RGB", (w, h), bg)
    return panel, rect


def put(panel, rect, lit=0.0):
    art.paste(panel, rect[:2])
    if lit:
        glow.paste(panel.point(lambda v: int(v * lit)), rect[:2])


cx, cy, row = 0, top + 8, 0


def centred(d, w, y, text, f, fill):
    d.text((w / 2, y), text, font=f, fill=fill, anchor="mm")


# The cart
p, r = sign("ambrosia_side", 768, 192, (26, 40, 84))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 757, 181), outline=(226, 190, 110), width=5)
centred(d, 768, 78, "AMBROSIA", font(BOLD, 112), (240, 208, 130))
centred(d, 768, 150, "Food of the Gods  ·  Since Before You", font(SERIF, 38), (226, 214, 190))
put(p, r, 0.5)
p, r = sign("ambrosia_menu", 512, 384, (232, 222, 196))
d = ImageDraw.Draw(p)
d.rectangle((8, 8, 503, 375), outline=(120, 40, 34), width=5)
centred(d, 512, 58, "MENU", font(BOLD, 64), (120, 40, 34))
lines = [("Hot dog", "4"), ("Pretzel", "3"), ("Nectar", "2"), ("Heel of bread", "free")]
for i, (a, b) in enumerate(lines):
    d.text((44, 136 + i * 54), a, font=font(SERIF, 42), fill=(40, 34, 30), anchor="lm")
    d.text((468, 136 + i * 54), b, font=font(BOLD, 42), fill=(40, 34, 30), anchor="rm")
centred(d, 512, 344, "No refunds. Zeus is watching.", font(SERIF, 30), (120, 40, 34))
put(p, r, 0.45)
# The plan's jokes
p, r = sign("sculptures", 768, 256, (74, 58, 38))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 757, 245), outline=(150, 118, 76), width=6)
centred(d, 768, 86, "SCULPTURES", font(BOLD, 84), (206, 170, 112))
centred(d, 768, 162, "PENDING DONATION", font(BOLD, 62), (206, 170, 112))
centred(d, 768, 216, "Please look up and imagine.", font(SERIF, 34), (176, 142, 94))
put(p, r)
p, r = sign("fountain_sign", 640, 320, (232, 228, 214))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 629, 309), outline=(40, 44, 50), width=6)
centred(d, 640, 84, "PLEASE DO NOT", font(BOLD, 62), (40, 44, 50))
centred(d, 640, 150, "TOUCH THE WATER.", font(BOLD, 62), (40, 44, 50))
centred(d, 640, 244, "She will know.", font(SERIF, 76), (140, 36, 30))
put(p, r)
p, r = sign("hours", 512, 640, (30, 32, 36))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 501, 629), outline=(180, 150, 96), width=5)
centred(d, 512, 90, "MVSEVM", font(BOLD, 74), (216, 190, 130))
centred(d, 512, 166, "ALEXANDRINVM", font(BOLD, 58), (216, 190, 130))
for i, t in enumerate(("Open daily 10 to 5", "Closed Mondays", "Closed for cleaning", "Closed since 48 B.C.")):
    centred(d, 512, 270 + i * 60, t, font(SERIF, 42), (214, 208, 196))
centred(d, 512, 548, "The Book is overdue.", font(BOLD, 38), (216, 190, 130))
centred(d, 512, 590, "Late fees apply.", font(SERIF, 34), (214, 208, 196))
put(p, r)
p, r = sign("newspaper", 384, 512, (214, 208, 190))
d = ImageDraw.Draw(p)
centred(d, 384, 62, "The Alexandria", font(BOLD, 52), (30, 30, 34))
centred(d, 384, 118, "POST", font(BOLD, 62), (30, 30, 34))
d.rectangle((24, 160, 359, 166), fill=(30, 30, 34))
centred(d, 384, 220, "LIBRARY FIRE", font(BOLD, 50), (30, 30, 34))
centred(d, 384, 274, "EXPERTS BAFFLED", font(BOLD, 38), (30, 30, 34))
for i in range(6):
    d.rectangle((30, 322 + i * 28, 354 - (i % 3) * 30, 332 + i * 28), fill=(120, 116, 104))
centred(d, 384, 486, "48 B.C.  ·  1 drachma", font(SERIF, 26), (30, 30, 34))
put(p, r)
# Street furniture
p, r = sign("street_5av", 512, 128, (20, 92, 62))
d = ImageDraw.Draw(p)
d.rectangle((6, 6, 505, 121), outline=(226, 224, 216), width=4)
centred(d, 512, 64, "5 Av", font(SANS, 84), (236, 234, 226))
put(p, r)
p, r = sign("street_82", 512, 128, (20, 92, 62))
d = ImageDraw.Draw(p)
d.rectangle((6, 6, 505, 121), outline=(226, 224, 216), width=4)
centred(d, 512, 64, "E 82 St", font(SANS, 84), (236, 234, 226))
put(p, r)
p, r = sign("hand", 128, 128, (8, 8, 8))
d = ImageDraw.Draw(p)
d.rounded_rectangle((42, 56, 92, 110), 10, fill=(255, 120, 30))
for i in range(4):
    d.rounded_rectangle((42 + i * 13, 22 + (2 - i) ** 2 * 3, 52 + i * 13, 70), 5, fill=(255, 120, 30))
d.rounded_rectangle((90, 62, 110, 74), 5, fill=(255, 120, 30))
put(p, r, 1.0)
p, r = sign("walker", 128, 128, (8, 8, 8))
d = ImageDraw.Draw(p)
d.ellipse((54, 16, 76, 38), fill=(226, 240, 240))
d.line((64, 42, 62, 78), fill=(226, 240, 240), width=14)
d.line((62, 78, 44, 112), fill=(226, 240, 240), width=11)
d.line((62, 78, 82, 112), fill=(226, 240, 240), width=11)
d.line((64, 50, 44, 68), fill=(226, 240, 240), width=9)
d.line((64, 50, 86, 66), fill=(226, 240, 240), width=9)
put(p, r, 1.0)
p, r = sign("taxi_sign", 256, 96, (240, 200, 90))
d = ImageDraw.Draw(p)
centred(d, 256, 48, "TAXI", font(SANS, 66), (24, 24, 26))
put(p, r, 0.9)
p, r = sign("taxi_door", 384, 128, (232, 176, 32))
d = ImageDraw.Draw(p)
for i in range(32):
    for j in range(2):
        if (i + j) % 2 == 0:
            d.rectangle((i * 12, 4 + j * 12, i * 12 + 11, 15 + j * 12), fill=(20, 20, 22))
centred(d, 384, 82, "TROY CAB CO.", font(SANS, 38), (20, 20, 22))
put(p, r)
p, r = sign("plate", 192, 96, (232, 228, 196))
d = ImageDraw.Draw(p)
centred(d, 192, 50, "HELEN", font(SANS, 48), (24, 30, 80))
put(p, r)
# The museum's flag: a gold owl on deep red
p, r = sign("flag", 640, 384, (112, 24, 26))
d = ImageDraw.Draw(p)
d.rectangle((14, 14, 625, 369), outline=(214, 176, 100), width=6)
gold = (222, 184, 106)
d.ellipse((230, 92, 410, 300), fill=gold)
d.polygon([(246, 118), (262, 62), (306, 100)], fill=gold)
d.polygon([(394, 118), (378, 62), (334, 100)], fill=gold)
d.ellipse((262, 124, 316, 178), fill=(112, 24, 26))
d.ellipse((324, 124, 378, 178), fill=(112, 24, 26))
d.ellipse((278, 140, 300, 162), fill=gold)
d.ellipse((340, 140, 362, 162), fill=gold)
d.polygon([(320, 170), (304, 196), (336, 196)], fill=(112, 24, 26))
for i in range(3):
    for j in range(2 + i % 2):
        d.arc((272 + j * 34 + (i % 2 == 0) * 16, 204 + i * 26, 304 + j * 34 + (i % 2 == 0) * 16, 232 + i * 26), 20, 160, fill=(112, 24, 26), width=5)
centred(d, 640, 334, "M  ·  A", font(BOLD, 40), gold)
put(p, r)
# Things to find. These sit in the free corners of the sheet, so the signs above never move.
def sign_at(name, x, y, w, h, bg):
    rect = (x, y, x + w, y + h)
    layout["signs"][name] = [rect[0] / S, 1 - rect[3] / S, rect[2] / S, 1 - rect[1] / S]
    return Image.new("RGB", (w, h), bg), rect


p, r = sign_at("needle_plaque", 396, 1244, 640, 256, (74, 58, 38))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 629, 245), outline=(150, 118, 76), width=6)
centred(d, 640, 66, "CLEOPATRA'S NEEDLE", font(BOLD, 56), (206, 170, 112))
centred(d, 640, 132, "Alexandria, 1450 B.C.", font(SERIF, 44), (176, 142, 94))
centred(d, 640, 198, "Also not returned.", font(BOLD, 54), (226, 190, 130))
put(p, r, 0.55)
p, r = sign_at("late_returns", 1042, 1244, 512, 320, (24, 34, 66))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 501, 309), outline=(226, 190, 110), width=6)
centred(d, 512, 76, "LATE RETURNS", font(BOLD, 64), (240, 208, 130))
d.rectangle((70, 126, 441, 168), fill=(8, 8, 10))
centred(d, 512, 216, "No questions asked.", font(SERIF, 44), (226, 214, 190))
centred(d, 512, 268, "She will know anyway.", font(SERIF, 38), (226, 190, 110))
put(p, r, 0.55)
p, r = sign_at("trojan_only", 1560, 1244, 448, 372, (236, 234, 226))
d = ImageDraw.Draw(p)
d.rectangle((10, 10, 437, 361), outline=(150, 36, 30), width=8)
centred(d, 448, 78, "NO PARKING", font(SANS, 58), (150, 36, 30))
centred(d, 448, 162, "TROJAN", font(SANS, 72), (24, 24, 28))
centred(d, 448, 236, "HORSES ONLY", font(SANS, 56), (24, 24, 28))
centred(d, 448, 318, "All other gifts will be towed.", font(SERIF, 30), (24, 24, 28))
put(p, r)
p, r = sign_at("poster_heel", 1236, 1630, 384, 372, (226, 218, 186))
d = ImageDraw.Draw(p)
centred(d, 384, 70, "LOST", font(SANS, 96), (150, 36, 30))
centred(d, 384, 158, "One (1) heel.", font(BOLD, 48), (30, 30, 34))
centred(d, 384, 214, "Sentimental value.", font(SERIF, 38), (30, 30, 34))
centred(d, 384, 262, "Last seen at Troy.", font(SERIF, 38), (30, 30, 34))
centred(d, 384, 326, "If found, do not aim.", font(BOLD, 36), (150, 36, 30))
put(p, r)
p, r = sign_at("poster_knowledge", 1626, 1630, 384, 372, (232, 228, 214))
d = ImageDraw.Draw(p)
centred(d, 384, 70, "MISSING", font(SANS, 76), (24, 24, 28))
centred(d, 384, 156, "All of human", font(BOLD, 48), (30, 30, 34))
centred(d, 384, 210, "knowledge.", font(BOLD, 48), (30, 30, 34))
centred(d, 384, 272, "Last seen 48 B.C.", font(SERIF, 38), (30, 30, 34))
centred(d, 384, 330, "Reward: everything.", font(BOLD, 34), (150, 36, 30))
put(p, r)
art.save(OUT / "ext_props.png", optimize=True)
glow.save(OUT / "ext_props_glow.png", optimize=True)
json.dump(layout, open(HERE / "props_layout.json", "w"), indent=1)
print("props art", cy + row, "of", S)
