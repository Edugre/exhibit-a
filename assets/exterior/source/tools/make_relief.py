"""The storytelling carving, drawn as bas-relief height fields: six portrait medallions, eight door
panels, the frieze inscriptions and the niche notices. Writes normal, occlusion and height maps, and
the layout the mesh builder reads. usage: python make_relief.py <out dir>"""
import json
import math
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, gaussian_filter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import door_art

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
FONT = "C:/Windows/Fonts/palab.ttf"
FONT_THIN = "C:/Windows/Fonts/pala.ttf"
ATLAS = 2048


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Relief:
    """A height field in metres, built from carved masses and cut lines. Shapes are given in a unit
    square, y down, and drawn at full working size."""

    def __init__(self, w, h, metres_wide):
        self.w, self.h = w, h
        self.px = metres_wide / w
        self.H = np.zeros((h, w), dtype=np.float32)

    def mask(self, poly=None, line=None, width=1, circle=None):
        im = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        s = (self.w, self.h)
        if poly is not None:
            d.polygon([(x * s[0], y * s[1]) for x, y in poly], fill=255)
        if line is not None:
            pts = [(x * s[0], y * s[1]) for x, y in line]
            d.line(pts, fill=255, width=int(width), joint="curve")
            for p in pts:
                d.ellipse([p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2], fill=255)
        if circle is not None:
            cx, cy, r = circle
            d.ellipse([(cx - r) * s[0], (cy - r) * s[1], (cx + r) * s[0], (cy + r) * s[1]], fill=255)
        return np.asarray(im, dtype=np.float32) / 255

    def mass(self, poly=None, circle=None, height=0.02, roll=0.03, level=0.0, keep="max"):
        """A rounded raised shape. roll is how far in from its edge it takes to reach full height."""
        m = self.mask(poly=poly, circle=circle)
        d = distance_transform_edt(m > 0.5) * self.px
        h = level + height * np.sqrt(1 - np.exp(-(d / roll) ** 1.6))
        h = np.where(m > 0.5, h, -1e3)
        self.H = np.maximum(self.H, h.astype(np.float32))

    def add_line(self, pts, width_m, depth, soft=0.6):
        """A raised (depth > 0) or cut (depth < 0) line, soft across its width."""
        w = max(int(width_m / self.px), 1)
        m = gaussian_filter(self.mask(line=pts, width=w), w * soft)
        m = m / max(m.max(), 1e-3)
        self.H += (m * depth).astype(np.float32)

    def text(self, s, cx, cy, size, font=FONT, depth=-0.006, spacing=0.0, vcut=True):
        """Letters cut in with a V, deepest along their middle, the way a mason cuts them; or raised."""
        im = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(font, int(size))
        widths = [d.textlength(c, font=f) for c in s]
        total = sum(widths) + spacing * (len(s) - 1)
        x = cx * self.w - total / 2
        y = cy * self.h
        for c, w in zip(s, widths):
            d.text((x, y), c, font=f, fill=255, anchor="lm")
            x += w + spacing
        m = np.asarray(im, dtype=np.float32) / 255
        dist = distance_transform_edt(m > 0.5) * self.px
        cut = 1 - np.exp(-dist / (abs(depth) * 0.9))
        self.H += (cut * depth * (m > 0.5)).astype(np.float32)

    def ring_text(self, s, r, size, cx=0.5, cy=0.5, depth=0.006):
        """Raised letters round a circle, reading clockwise from the top."""
        f = ImageFont.truetype(FONT, int(size))
        probe = ImageDraw.Draw(Image.new("L", (8, 8)))
        widths = [probe.textlength(c, font=f) * 1.14 for c in s]
        R = r * self.w
        total = sum(widths) / R
        a = -math.pi / 2 - total / 2
        out = Image.new("L", (self.w, self.h), 0)
        for c, w in zip(s, widths):
            mid = a + w / R / 2
            cell = Image.new("L", (int(size * 2), int(size * 2)), 0)
            ImageDraw.Draw(cell).text((size, size), c, font=f, fill=255, anchor="mm")
            rot = cell.rotate(-math.degrees(mid + math.pi / 2), resample=Image.BICUBIC)
            px = cx * self.w + R * math.cos(mid) - size
            py = cy * self.h + R * math.sin(mid) - size
            out.paste(255, (int(px), int(py)), rot)
            a += w / R
        m = np.asarray(out, dtype=np.float32) / 255
        d = distance_transform_edt(m > 0.5) * self.px
        self.H += (depth * np.clip(d / (depth * 0.6), 0, 1) * (m > 0.5)).astype(np.float32)

    def bake(self, size, k=1.0, span=None):
        """Normal, two occlusions and height, reduced to the cell size. k scales the occlusion spreads
        for a drawing done at finer pixels."""
        H = gaussian_filter(self.H, 1.5)
        dy, dx = np.gradient(H, self.px)
        ln = np.sqrt(dx * dx + dy * dy + 1)
        n = np.stack([-dx / ln, dy / ln, 1 / ln], -1)
        wide = 1 - np.clip((gaussian_filter(H, 18 * k) - H) / 0.016, 0, 1) * 0.8
        tight = 1 - np.clip((gaussian_filter(H, 4 * k) - H) / 0.0035, 0, 1) * 0.9
        lo, hi = span if span else (float(H.min()), float(H.max()))
        hh = np.clip((H - lo) / max(hi - lo, 1e-5), 0, 1)

        def down(a):
            return np.asarray(Image.fromarray(a).resize(size, Image.LANCZOS))

        return (down(((n * 0.5 + 0.5) * 255).astype(np.uint8)), down((wide * 255).astype(np.uint8)), down((tight * 255).astype(np.uint8)), down((hh * 255).astype(np.uint8)))


# --- Shapes -------------------------------------------------------------------------------------
HEAD = [(0.62, 0.20), (0.665, 0.27), (0.675, 0.33), (0.66, 0.365), (0.695, 0.42), (0.735, 0.475), (0.72, 0.495), (0.675, 0.50), (0.685, 0.525), (0.665, 0.545),
        (0.68, 0.565), (0.66, 0.59), (0.665, 0.63), (0.645, 0.665), (0.57, 0.67), (0.55, 0.76), (0.58, 0.88), (0.28, 0.88), (0.33, 0.72), (0.30, 0.60), (0.27, 0.46),
        (0.30, 0.30), (0.40, 0.19), (0.52, 0.15)]
FEMALE = [(0.61, 0.23), (0.65, 0.29), (0.66, 0.345), (0.648, 0.375), (0.675, 0.43), (0.70, 0.47), (0.69, 0.49), (0.655, 0.50), (0.665, 0.522), (0.648, 0.54),
          (0.66, 0.56), (0.645, 0.585), (0.645, 0.62), (0.625, 0.65), (0.565, 0.655), (0.545, 0.78), (0.60, 0.90), (0.30, 0.90), (0.37, 0.74), (0.34, 0.60), (0.31, 0.46),
          (0.33, 0.31), (0.42, 0.20), (0.52, 0.17)]
HORSE_BODY = [(0.22, 0.46), (0.30, 0.40), (0.56, 0.40), (0.64, 0.30), (0.67, 0.18), (0.72, 0.14), (0.80, 0.21), (0.84, 0.28), (0.82, 0.31), (0.75, 0.29), (0.72, 0.36),
              (0.70, 0.46), (0.66, 0.56), (0.60, 0.60), (0.32, 0.60), (0.26, 0.58), (0.20, 0.70), (0.16, 0.69), (0.21, 0.54)]
TEMPLE = [(0.20, 0.42), (0.50, 0.26), (0.80, 0.42), (0.80, 0.46), (0.20, 0.46)]
FLAMES = [(0.16, 0.86), (0.20, 0.60), (0.26, 0.70), (0.30, 0.40), (0.37, 0.58), (0.44, 0.24), (0.50, 0.46), (0.57, 0.14), (0.62, 0.42), (0.70, 0.30), (0.72, 0.56), (0.80, 0.46), (0.84, 0.86)]
BOOK = [(0.24, 0.44), (0.48, 0.38), (0.50, 0.41), (0.52, 0.38), (0.76, 0.44), (0.76, 0.66), (0.52, 0.60), (0.50, 0.63), (0.48, 0.60), (0.24, 0.66)]


def medallion(name, label, draw):
    S = 1024
    r = Relief(S, S, 1.24)
    # field, lettered band and beaded rim
    r.mass(circle=(0.5, 0.5, 0.5), height=0.012, roll=0.01)
    yy, xx = np.mgrid[0:S, 0:S]
    rad = np.hypot(xx - S / 2 + 0.5, yy - S / 2 + 0.5) / (S / 2)
    r.H -= (sstep(0.72, 0.70, rad) * 0.018).astype(np.float32)
    r.H += (np.exp(-((rad - 0.885) / 0.018) ** 2) * 0.006 + np.exp(-((rad - 0.73) / 0.014) ** 2) * 0.008).astype(np.float32)
    for i in range(52):
        a = 2 * math.pi * i / 52
        cx, cy = 0.5 + 0.47 * math.cos(a), 0.5 + 0.47 * math.sin(a)
        bx = (xx / S - cx) / 0.0185
        by = (yy / S - cy) / 0.0185
        r.H += (np.sqrt(np.maximum(1 - bx * bx - by * by, 0)) * 0.011).astype(np.float32)
    r.ring_text(label, 0.405, 82, depth=0.006)
    # portrait, inside the inner field, drawn on a square that fits it
    field = Relief(S, S, 1.24)
    draw(field)
    k = 0.715
    im = Image.fromarray(field.H)
    small = int(S * k)
    q = np.asarray(im.resize((small, small), Image.BILINEAR), dtype=np.float32)
    pad = (S - small) // 2
    fig = np.zeros((S, S), dtype=np.float32)
    fig[pad:pad + small, pad:pad + small] = q
    fig *= (rad < 0.71).astype(np.float32)
    r.H = np.where(rad < 0.71, r.H + fig, r.H)
    return r


def homer(f):
    f.mass(poly=HEAD, height=0.05, roll=0.05)
    f.mass(poly=[(0.60, 0.50), (0.70, 0.55), (0.72, 0.66), (0.69, 0.78), (0.62, 0.86), (0.50, 0.88), (0.44, 0.74), (0.45, 0.58)], height=0.06, roll=0.04)
    for i in range(9):
        x = 0.47 + i * 0.03
        f.add_line([(x, 0.55 + i * 0.005), (x + 0.03, 0.66), (x - 0.01, 0.76), (x + 0.015, 0.85)], 0.012, -0.007)
    for i in range(8):
        y = 0.20 + i * 0.05
        f.add_line([(0.60 - i * 0.012, y), (0.46 - i * 0.012, y + 0.03), (0.36 - i * 0.008, y + 0.02), (0.31, y + 0.08)], 0.012, -0.006)
    f.add_line([(0.34, 0.33), (0.47, 0.24), (0.63, 0.25)], 0.02, 0.010)                # the fillet round his hair
    f.add_line([(0.595, 0.385), (0.635, 0.375), (0.66, 0.39)], 0.012, -0.010)          # closed, blind eye
    f.add_line([(0.60, 0.355), (0.64, 0.345), (0.67, 0.355)], 0.014, 0.008)            # brow
    f.add_line([(0.56, 0.41), (0.54, 0.46), (0.565, 0.49)], 0.012, -0.006)             # ear
    f.add_line([(0.30, 0.88), (0.44, 0.80), (0.60, 0.90)], 0.024, 0.012)               # cloak


def achilles(f):
    f.mass(poly=[(0.60, 0.42), (0.67, 0.36), (0.695, 0.42), (0.735, 0.475), (0.72, 0.495), (0.675, 0.50), (0.685, 0.525), (0.665, 0.545), (0.68, 0.565), (0.66, 0.59), (0.665, 0.63),
                 (0.645, 0.665), (0.57, 0.67), (0.55, 0.76), (0.58, 0.88), (0.34, 0.88), (0.42, 0.66)], height=0.05, roll=0.05)
    helmet = [(0.70, 0.36), (0.66, 0.24), (0.56, 0.15), (0.42, 0.14), (0.31, 0.22), (0.27, 0.37), (0.28, 0.52), (0.33, 0.62), (0.43, 0.64), (0.48, 0.56), (0.47, 0.45), (0.55, 0.40), (0.63, 0.39)]
    f.mass(poly=helmet, height=0.06, roll=0.04)
    crest = [(0.62, 0.20), (0.56, 0.06), (0.40, 0.01), (0.22, 0.06), (0.10, 0.22), (0.07, 0.42), (0.13, 0.60), (0.19, 0.42), (0.24, 0.28), (0.34, 0.17), (0.48, 0.13)]
    f.mass(poly=crest, height=0.05, roll=0.025)
    for i in range(13):
        a = math.pi * (0.04 + i * 0.075)
        f.add_line([(0.42 - 0.13 * math.cos(a), 0.24 - 0.11 * math.sin(a)), (0.40 - 0.34 * math.cos(a), 0.30 - 0.29 * math.sin(a))], 0.012, -0.008)
    f.add_line([(0.62, 0.39), (0.50, 0.42), (0.46, 0.54), (0.44, 0.63)], 0.022, 0.012)   # cheek guard edge
    f.add_line([(0.60, 0.415), (0.635, 0.405), (0.655, 0.42)], 0.012, -0.010)            # eye
    f.add_line([(0.34, 0.26), (0.50, 0.21), (0.66, 0.30)], 0.016, 0.008)
    f.add_line([(0.36, 0.86), (0.44, 0.78), (0.56, 0.80)], 0.02, 0.012)                  # shoulder of the cuirass


def helen(f):
    f.mass(poly=FEMALE, height=0.045, roll=0.05)
    f.mass(circle=(0.32, 0.30, 0.13), height=0.05, roll=0.03)                             # knot of hair
    f.mass(poly=[(0.62, 0.22), (0.54, 0.14), (0.40, 0.15), (0.31, 0.26), (0.30, 0.44), (0.36, 0.60), (0.46, 0.52), (0.50, 0.36), (0.58, 0.29)], height=0.052, roll=0.03)
    for i in range(7):
        y = 0.20 + i * 0.05
        f.add_line([(0.60 - i * 0.02, y + 0.03), (0.48, y + 0.02), (0.36, y + 0.06), (0.34, y + 0.13)], 0.011, -0.006)
    for i in range(3):
        y = 0.26 + i * 0.07
        f.add_line([(0.24, y), (0.32, y - 0.04), (0.40, y + 0.02)], 0.012, -0.007)
    f.add_line([(0.34, 0.22), (0.46, 0.15), (0.60, 0.19)], 0.024, 0.012)                  # diadem
    for i in range(5):
        f.mass(circle=(0.38 + i * 0.05, 0.195 - 0.022 * math.sin(i * 0.8) - 0.02, 0.012), height=0.012, roll=0.008, level=0.05)
    f.add_line([(0.585, 0.385), (0.625, 0.372), (0.648, 0.39)], 0.012, -0.009)
    f.add_line([(0.59, 0.355), (0.63, 0.345), (0.655, 0.36)], 0.011, 0.006)
    f.add_line([(0.42, 0.56), (0.44, 0.66), (0.40, 0.76), (0.43, 0.82)], 0.016, 0.010)    # a ringlet down her neck
    f.add_line([(0.30, 0.90), (0.42, 0.82), (0.60, 0.90)], 0.022, 0.012)


def wheel(f, x, y, r):
    f.mass(circle=(x, y, r), height=0.04, roll=0.02)
    f.add_line([(x - r * 0.8, y), (x + r * 0.8, y)], 0.012, -0.008)
    f.add_line([(x, y - r * 0.8), (x, y + r * 0.8)], 0.012, -0.008)


def horse(f):
    f.mass(poly=[(0.16, 0.80), (0.86, 0.80), (0.86, 0.75), (0.16, 0.75)], height=0.03, roll=0.012)      # the wheeled platform
    for x, w in ((0.30, 0.042), (0.38, 0.042), (0.56, 0.042), (0.64, 0.042)):
        f.mass(poly=[(x - w, 0.56), (x + w, 0.56), (x + w * 0.8, 0.76), (x - w * 0.8, 0.76)], height=0.036, roll=0.016)
    f.mass(poly=HORSE_BODY, height=0.055, roll=0.04)
    for i in range(6):
        y = 0.43 + i * 0.03
        f.add_line([(0.26, y), (0.66, y)], 0.008, -0.006)                                               # planks
    for x in (0.34, 0.44, 0.54):
        f.add_line([(x, 0.41), (x, 0.59)], 0.008, -0.005)
    f.add_line([(0.66, 0.24), (0.60, 0.30), (0.56, 0.38)], 0.03, 0.012)                                  # mane
    f.mass(circle=(0.745, 0.205, 0.016), height=0.014, roll=0.008, level=0.05)                           # eye
    f.add_line([(0.40, 0.44), (0.52, 0.44), (0.52, 0.53), (0.40, 0.53), (0.40, 0.44)], 0.012, -0.012)    # the hatch
    wheel(f, 0.27, 0.84, 0.06)
    wheel(f, 0.46, 0.84, 0.06)
    wheel(f, 0.68, 0.84, 0.06)


def library(f):
    tall = [(0.08, 0.86), (0.10, 0.50), (0.15, 0.62), (0.19, 0.30), (0.26, 0.44), (0.33, 0.10), (0.40, 0.25), (0.47, 0.03), (0.55, 0.22), (0.63, 0.07), (0.69, 0.30), (0.77, 0.20),
            (0.80, 0.44), (0.87, 0.34), (0.92, 0.60), (0.94, 0.86)]
    f.mass(poly=tall, height=0.032, roll=0.05)
    for x, y0 in ((0.14, 0.50), (0.24, 0.30), (0.36, 0.14), (0.48, 0.07), (0.60, 0.12), (0.71, 0.26), (0.84, 0.40)):
        f.add_line([(x + 0.03, 0.44), (x - 0.02, y0 + 0.16), (x + 0.012, y0)], 0.016, -0.012)
    f.mass(poly=TEMPLE, height=0.05, roll=0.02, level=0.03)
    f.mass(poly=[(0.20, 0.82), (0.80, 0.82), (0.84, 0.88), (0.16, 0.88)], height=0.05, roll=0.015, level=0.03)
    for x in (0.27, 0.40, 0.60, 0.73):
        f.mass(poly=[(x - 0.032, 0.46), (x + 0.032, 0.46), (x + 0.036, 0.82), (x - 0.036, 0.82)], height=0.05, roll=0.022, level=0.03)
    f.mass(poly=[(0.455, 0.60), (0.545, 0.60), (0.545, 0.82), (0.455, 0.82)], height=0.02, roll=0.01, level=0.02)
    # a scroll flying up out of the fire


def guard(f):
    f.mass(poly=FEMALE, height=0.045, roll=0.05)
    f.mass(circle=(0.36, 0.17, 0.09), height=0.055, roll=0.03)                                           # the bun
    f.mass(poly=[(0.62, 0.23), (0.54, 0.14), (0.40, 0.15), (0.31, 0.26), (0.30, 0.44), (0.35, 0.58), (0.45, 0.54), (0.50, 0.36), (0.58, 0.28)], height=0.05, roll=0.03)
    for i in range(6):
        y = 0.21 + i * 0.05
        f.add_line([(0.60 - i * 0.025, y + 0.02), (0.44, y), (0.34, y + 0.1)], 0.01, -0.006)
    # spectacles
    f.add_line([(0.585, 0.40), (0.60, 0.365), (0.645, 0.36), (0.655, 0.40), (0.625, 0.425), (0.59, 0.42), (0.585, 0.40)], 0.012, 0.010)
    f.add_line([(0.585, 0.385), (0.50, 0.37), (0.45, 0.40)], 0.010, 0.008)
    f.add_line([(0.60, 0.395), (0.625, 0.388), (0.645, 0.40)], 0.010, -0.008)
    f.add_line([(0.595, 0.345), (0.63, 0.325), (0.66, 0.345)], 0.012, 0.008)                             # a stern brow
    # the raised finger, and her hand
    f.mass(poly=[(0.70, 0.40), (0.735, 0.40), (0.745, 0.60), (0.705, 0.60)], height=0.03, roll=0.014, level=0.045)
    f.mass(poly=[(0.66, 0.58), (0.78, 0.57), (0.80, 0.70), (0.72, 0.76), (0.64, 0.72)], height=0.036, roll=0.03, level=0.04)
    f.mass(poly=[(0.66, 0.74), (0.74, 0.74), (0.62, 0.92), (0.50, 0.90)], height=0.03, roll=0.03, level=0.02)
    f.add_line([(0.30, 0.90), (0.42, 0.82), (0.60, 0.90)], 0.022, 0.012)


# --- Door panels --------------------------------------------------------------------------------
# --- Layout and output --------------------------------------------------------------------------
normal = np.full((ATLAS, ATLAS, 3), (128, 128, 255), dtype=np.uint8)
ao = np.full((ATLAS, ATLAS, 3), 255, dtype=np.uint8)
ao[..., 2] = 0
layout = {"medallions": {}, "door_panels": [], "inscriptions": {}, "banners": {}}


def put(rel, rect):
    x0, y0, x1, y1 = rect
    n, w, t, h = rel.bake((x1 - x0, y1 - y0))
    normal[y0:y1, x0:x1] = n
    ao[y0:y1, x0:x1, 0] = w
    ao[y0:y1, x0:x1, 1] = t
    ao[y0:y1, x0:x1, 2] = h


meds = [("homer", "HOMERVS", homer), ("achilles", "ACHILLES", achilles), ("helen", "HELENA", helen),
        ("horse", "EQVVS", horse), ("library", "BIBLIOTHECA", library), ("guard", "CVSTOS", guard)]
for i, (key, label, fn) in enumerate(meds):
    rect = [(i % 3) * 512, (i // 3) * 512, (i % 3) * 512 + 512, (i // 3) * 512 + 512]
    put(medallion(key, label, fn), rect)
    layout["medallions"][key] = rect
    print("medallion", key, flush=True)

layout["door_panels"] = door_art.build(Relief, OUT)

for key, text, y, w_m, size, gap in (("name", "MVSEVM  ALEXANDRINVM", 1536, 8.5, 86, 8), ("touch", "NE  TANGITO", 1671, 7.5, 92, 26), ("know", "ILLA  SCIET", 1806, 7.5, 92, 26)):
    width = 2048 if key == "name" else 1808
    r = Relief(width * 2, 135 * 2, w_m)
    r.text(text, 0.5, 0.5, size * 2, depth=-0.024, spacing=gap * 2)
    rect = [0, y, width, y + 135]
    put(r, rect)
    layout["inscriptions"][key] = rect

r = Relief(1024, 236, 1.04)
r.mass(poly=[(0.01, 0.03), (0.99, 0.03), (0.99, 0.97), (0.01, 0.97)], height=0.004, roll=0.004)
r.text("TEMPORARILY REMOVED", 0.5, 0.34, 76, font=FONT, depth=0.0035)
r.text("FOR CLEANING", 0.5, 0.70, 76, font=FONT, depth=0.0035)
layout["sign"] = [1536, 1024, 2048, 1142]
put(r, layout["sign"])

third = 1 / 3
layout["banners"] = {"achilles": [0.0, third], "book": [third, 2 * third], "helen": [2 * third, 1.0]}
Image.fromarray(normal).save(OUT / "ext_relief_normal.png", optimize=True)
Image.fromarray(ao).save(OUT / "ext_relief_ao.png", optimize=True)
json.dump(layout, open(HERE / "relief_layout.json", "w"), indent=1)
# A preview that shades the normals, so the carving can be judged by eye
L = np.array([-0.45, 0.55, 0.70])
n = normal / 127.5 - 1
shade = np.clip((n @ L), 0, 1) ** 1.2
Image.fromarray(np.clip(shade * ao[..., 0] / 255 * 255, 0, 255).astype(np.uint8)).save(OUT / "relief_preview.png")
print("relief written")
