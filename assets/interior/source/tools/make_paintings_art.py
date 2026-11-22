"""The paintings' one texture (asset item P1.3): six old oil paintings of myths, each laid out from simple
shapes and then repainted stroke by stroke along the forms, so they read as brushwork rather than clip
art. Then aged: canvas weave, yellowed varnish darker at the edges, and a fine network of cracks. Also the
gilt frame moulding (rubbed through to the red clay under the gold on the high points), the brass title
labels and the picture lights. Writes the texture, a normal map, the lights' glow map, their import
settings and three materials (canvas, gilt and brass, and the lamps).
usage: python make_paintings_art.py <assets/interior/paintings folder>"""
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, map_coordinates, sobel
from scipy.spatial import cKDTree

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import paintings_layout as L  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/paintings/"
N = L.ATLAS
SERIF_BOLD = "C:/Windows/Fonts/palab.ttf"
SERIF_ITAL = "C:/Windows/Fonts/palai.ttf"
GOLD = np.array([0.72, 0.55, 0.24])
BOLE = np.array([0.5, 0.22, 0.12])
BRASS = np.array([0.8, 0.62, 0.3])
PATINA = np.array([0.11, 0.085, 0.05])

rgb = np.zeros((N, N, 3))
height = np.zeros((N, N))


def noise(shape, sigma, seed):
    n = gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-9)


def region(name):
    x, y, w, h = L.REGIONS[name]
    return (slice(y, y + h), slice(x, x + w)), w, h


def drawn(w, h, fn, ss=3):
    img = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(img), ss)
    return np.asarray(img.resize((w, h), Image.BOX), dtype=float) / 255


def c8(c):
    return tuple(int(max(0, min(255, v * 255))) for v in c)


# --- Laying out a scene ------------------------------------------------------------------------------

class Scene:
    """A picture laid out at twice its final size, from fractions of its width and height."""

    def __init__(self, w, h, seed):
        self.W, self.H = w * 2, h * 2
        self.img = Image.new("RGB", (self.W, self.H))
        self.d = ImageDraw.Draw(self.img)
        self.rng = np.random.default_rng(seed)

    def p(self, x, y):
        return (x * self.W, y * self.H)

    def gradient(self, stops, y0=0.0, y1=1.0):
        a = np.asarray(self.img, dtype=float) / 255
        t = np.linspace(0, 1, self.H)
        rows = np.stack([np.interp(t, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)], -1)
        band = (t >= y0) & (t <= y1)
        a[band] = rows[band][:, None, :]
        self.set(a)

    def glow(self, x, y, radius, colour, strength=1.0, y_max=1.0):
        a = np.asarray(self.img, dtype=float) / 255
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        r2 = ((xx - x * self.W) ** 2 + (yy - y * self.H) ** 2) / (radius * self.W) ** 2
        k = (np.exp(-r2) * strength * (yy <= y_max * self.H))[..., None]
        self.set(a * (1 - k) + np.array(colour) * k)

    def poly(self, pts, colour):
        self.d.polygon([self.p(*q) for q in pts], fill=c8(colour))

    def ellipse(self, x, y, rx, ry, colour):
        self.d.ellipse([*self.p(x - rx, y - ry), *self.p(x + rx, y + ry)], fill=c8(colour))

    def line(self, pts, colour, width):
        self.d.line([self.p(*q) for q in pts], fill=c8(colour), width=max(1, int(width * self.W)), joint="curve")

    def shade(self, pts, colour, alpha, blur=6):
        """A soft-edged tint over part of the picture: shadows, light, haze."""
        m = Image.new("L", (self.W, self.H), 0)
        ImageDraw.Draw(m).polygon([self.p(*q) for q in pts], fill=255)
        k = gaussian_filter(np.asarray(m, dtype=float) / 255, blur)[..., None] * alpha
        a = np.asarray(self.img, dtype=float) / 255
        self.set(a * (1 - k) + np.array(colour) * k)

    def texture(self, amount, sigma, seed, y0=0.0, y1=1.0):
        a = np.asarray(self.img, dtype=float) / 255
        n = noise((self.H, self.W), sigma, seed)[..., None] - 0.5
        band = np.zeros((self.H, 1, 1))
        band[int(y0 * self.H):int(y1 * self.H)] = 1
        self.set(a * (1 + amount * n * band))

    def set(self, a):
        self.img = Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))
        self.d = ImageDraw.Draw(self.img)

    def array(self):
        return np.asarray(self.img, dtype=float) / 255


def small_splash(s):
    s.gradient([(0, (0.38, 0.5, 0.64)), (0.25, (0.62, 0.7, 0.76)), (0.42, (0.95, 0.86, 0.66))], 0, 0.42)
    s.gradient([(0.42, (0.6, 0.66, 0.62)), (0.6, (0.22, 0.36, 0.4)), (1.0, (0.08, 0.16, 0.2))], 0.42, 1)
    s.glow(0.78, 0.2, 0.09, (1.0, 0.94, 0.74), 0.9, y_max=0.42)
    s.ellipse(0.78, 0.2, 0.025, 0.045, (1.0, 0.97, 0.85))
    for k in range(200):     # the sun's glitter on the sea, and ripples everywhere else
        x = 0.78 + s.rng.normal(0, 0.035) if k < 120 else s.rng.uniform(0.3, 1.0)
        y = s.rng.uniform(0.43, 0.65) if k < 120 else s.rng.uniform(0.43, 1.0)
        c = (1.0, 0.92, 0.7) if k < 120 else (0.33, 0.46, 0.5)
        s.line([(x - 0.012, y), (x + 0.012, y)], c, 0.003)
    s.poly([(0.5, 0.42), (0.58, 0.39), (0.66, 0.405), (0.76, 0.385), (0.88, 0.4), (1.0, 0.38), (1.0, 0.425), (0.5, 0.425)], (0.5, 0.55, 0.6))
    s.poly([(0.6, 0.5), (0.71, 0.5), (0.69, 0.53), (0.615, 0.53)], (0.24, 0.15, 0.09))       # the ship
    s.line([(0.652, 0.36), (0.652, 0.5)], (0.2, 0.13, 0.08), 0.003)
    s.poly([(0.656, 0.37), (0.7, 0.4), (0.656, 0.49)], (0.92, 0.87, 0.74))
    s.poly([(0.648, 0.38), (0.615, 0.48), (0.648, 0.48)], (0.82, 0.78, 0.66))
    s.poly([(0, 0.55), (0.1, 0.52), (0.2, 0.555), (0.3, 0.64), (0.37, 0.78), (0.41, 0.93), (0.43, 1.0), (0, 1.0)], (0.3, 0.3, 0.16))
    s.shade([(0, 0.55), (0.1, 0.52), (0.2, 0.555), (0.24, 0.6), (0, 0.62)], (0.42, 0.48, 0.2), 0.7)
    s.shade([(0.25, 0.62), (0.37, 0.78), (0.41, 0.93), (0.43, 1.0), (0.3, 1.0)], (0.12, 0.1, 0.06), 0.6)
    s.texture(0.35, 2, 1101, 0.52, 1.0)
    s.ellipse(0.155, 0.505, 0.008, 0.03, (0.14, 0.11, 0.09))                                   # a shepherd, looking the other way
    s.ellipse(0.153, 0.47, 0.006, 0.011, (0.18, 0.13, 0.1))
    s.line([(0.142, 0.45), (0.138, 0.54)], (0.2, 0.14, 0.08), 0.0025)
    for x, y in ((0.19, 0.54), (0.215, 0.548), (0.235, 0.56), (0.205, 0.565)):
        s.ellipse(x, y, 0.011, 0.012, (0.86, 0.84, 0.76))
    s.ellipse(0.47, 0.705, 0.032, 0.014, (0.8, 0.86, 0.85))                                    # the splash, and a pair of legs
    s.ellipse(0.47, 0.705, 0.022, 0.009, (0.16, 0.28, 0.32))
    s.line([(0.466, 0.705), (0.452, 0.645)], (0.86, 0.66, 0.52), 0.006)
    s.line([(0.474, 0.705), (0.49, 0.65)], (0.86, 0.66, 0.52), 0.006)
    for k in range(9):
        x, y = s.rng.uniform(0.41, 0.55), s.rng.uniform(0.62, 0.74)
        a = s.rng.uniform(0, math.pi)
        s.line([(x, y), (x + 0.01 * math.cos(a), y + 0.016 * math.sin(a))], (0.95, 0.94, 0.9), 0.003)
    for k in range(14):
        x, y = 0.47 + s.rng.normal(0, 0.012), 0.69 - abs(s.rng.normal(0, 0.02))
        s.ellipse(x, y, 0.002, 0.004, (0.92, 0.96, 0.95))


def achilles(s):
    s.gradient([(0, (0.17, 0.13, 0.09)), (1, (0.07, 0.05, 0.04))])
    s.glow(0.55, 0.25, 0.45, (0.33, 0.25, 0.16), 0.8)
    s.poly([(0.02, 0), (0.19, 0), (0.19, 1), (0.02, 1)], (0.42, 0.38, 0.31))                  # a column
    s.shade([(0.13, 0), (0.19, 0), (0.19, 1), (0.13, 1)], (0.15, 0.12, 0.1), 0.6, 3)
    s.poly([(0.0, 0.0), (0.22, 0.0), (0.22, 0.05), (0.0, 0.05)], (0.5, 0.45, 0.36))
    s.poly([(0.62, 0), (1, 0), (1, 0.55), (0.88, 0.38), (0.76, 0.14)], (0.42, 0.07, 0.06))     # a drape
    s.shade([(0.8, 0.0), (0.9, 0.0), (0.97, 0.4), (0.9, 0.33)], (0.6, 0.12, 0.1), 0.7, 4)
    s.poly([(0.33, 0.27), (0.68, 0.27), (0.86, 1.0), (0.22, 1.0)], (0.55, 0.1, 0.08))          # his cloak
    s.shade([(0.6, 0.3), (0.68, 0.27), (0.86, 1.0), (0.7, 1.0)], (0.25, 0.04, 0.04), 0.6)
    s.line([(0.255, 0.04), (0.255, 1.0)], (0.33, 0.23, 0.13), 0.012)                           # spear
    s.poly([(0.255, 0.0), (0.27, 0.05), (0.255, 0.075), (0.24, 0.05)], (0.75, 0.56, 0.26))
    for a, b in (((0.41, 0.68), (0.48, 1.0)), ((0.52, 0.68), (0.59, 1.0))):                   # legs, and greaves
        s.poly([(a[0], a[1]), (a[0] + 0.07, a[1]), (b[0], b[1]), (b[0] - 0.07, b[1])], (0.76, 0.55, 0.41))
        s.poly([(a[0] + 0.002, 0.82), (a[0] + 0.074, 0.82), (b[0] + 0.004, 1.0), (b[0] - 0.072, 1.0)], (0.6, 0.43, 0.2))
        s.shade([(a[0] + 0.03, 0.83), (a[0] + 0.05, 0.83), (b[0] - 0.02, 1.0), (b[0] - 0.04, 1.0)], (0.92, 0.76, 0.42), 0.6, 2)
    for k in range(9):                                                                          # leather strips
        x = 0.38 + k * 0.027
        s.poly([(x, 0.555), (x + 0.024, 0.555), (x + 0.024, 0.69), (x, 0.69)], (0.36, 0.22, 0.12) if k % 2 else (0.28, 0.17, 0.09))
        s.ellipse(x + 0.012, 0.675, 0.006, 0.004, (0.78, 0.6, 0.3))
    s.poly([(0.36, 0.29), (0.31, 0.38), (0.27, 0.45), (0.3, 0.47), (0.36, 0.4), (0.4, 0.33)], (0.76, 0.55, 0.41))  # arm on the spear
    s.ellipse(0.265, 0.455, 0.022, 0.018, (0.8, 0.58, 0.44))
    s.poly([(0.36, 0.27), (0.64, 0.27), (0.665, 0.42), (0.62, 0.56), (0.38, 0.56), (0.335, 0.42)], (0.6, 0.43, 0.19))  # bronze cuirass
    s.glow(0.44, 0.35, 0.07, (0.9, 0.7, 0.36), 0.8)
    s.glow(0.56, 0.35, 0.06, (0.85, 0.64, 0.32), 0.6)
    s.shade([(0.56, 0.3), (0.64, 0.27), (0.665, 0.42), (0.62, 0.56), (0.56, 0.56)], (0.25, 0.16, 0.06), 0.5)
    s.line([(0.4, 0.45), (0.5, 0.47), (0.6, 0.45)], (0.35, 0.24, 0.1), 0.006)
    s.line([(0.5, 0.33), (0.5, 0.54)], (0.38, 0.26, 0.1), 0.005)
    s.poly([(0.64, 0.29), (0.7, 0.33), (0.71, 0.5), (0.67, 0.56), (0.64, 0.5), (0.65, 0.36)], (0.72, 0.52, 0.39))  # other arm
    s.ellipse(0.72, 0.6, 0.075, 0.05, (0.62, 0.45, 0.2))                                       # his helmet, under his arm
    s.glow(0.7, 0.585, 0.03, (0.9, 0.72, 0.4), 0.7)
    s.poly([(0.65, 0.56), (0.7, 0.53), (0.78, 0.54), (0.82, 0.58), (0.76, 0.555), (0.68, 0.565)], (0.6, 0.1, 0.07))
    s.poly([(0.46, 0.215), (0.54, 0.215), (0.545, 0.285), (0.455, 0.285)], (0.66, 0.46, 0.34))  # neck, head, hair
    s.ellipse(0.5, 0.17, 0.072, 0.085, (0.8, 0.58, 0.44))
    s.shade([(0.52, 0.09), (0.58, 0.12), (0.58, 0.24), (0.52, 0.26)], (0.5, 0.32, 0.22), 0.55, 3)
    s.poly([(0.425, 0.15), (0.44, 0.1), (0.5, 0.078), (0.56, 0.1), (0.575, 0.15), (0.56, 0.125), (0.5, 0.112), (0.44, 0.125)], (0.2, 0.12, 0.07))
    for k in range(18):
        a = s.rng.uniform(math.pi * 1.0, math.pi * 2.0)
        s.ellipse(0.5 + 0.07 * math.cos(a), 0.135 + 0.06 * math.sin(a), 0.012, 0.011, (0.2, 0.12, 0.07) if k % 3 else (0.3, 0.19, 0.1))
    s.shade([(0.44, 0.2), (0.56, 0.2), (0.55, 0.25), (0.45, 0.25)], (0.3, 0.18, 0.1), 0.6, 2)     # beard
    for x in (0.473, 0.53):
        s.shade([(x - 0.017, 0.152), (x + 0.017, 0.152), (x + 0.015, 0.172), (x - 0.015, 0.172)], (0.55, 0.36, 0.27), 0.5, 2)
        s.ellipse(x, 0.164, 0.008, 0.0045, (0.34, 0.22, 0.15))
        s.line([(x - 0.015, 0.149), (x + 0.013, 0.147)], (0.36, 0.22, 0.12), 0.003)
    s.line([(0.502, 0.168), (0.498, 0.195)], (0.58, 0.38, 0.27), 0.006)
    s.line([(0.485, 0.214), (0.515, 0.214)], (0.5, 0.28, 0.2), 0.004)
    s.shade([(0.5, 0.27), (0.665, 0.27), (0.7, 0.56), (0.6, 1.0), (0.5, 1.0)], (0.12, 0.07, 0.04), 0.35, 10)   # light from the left


def narcissus(s):
    s.gradient([(0, (0.24, 0.3, 0.36)), (0.4, (0.66, 0.64, 0.52)), (0.56, (0.78, 0.72, 0.56))])
    s.poly([(0, 0.46), (0.25, 0.44), (0.5, 0.455), (0.75, 0.435), (1, 0.45), (1, 0.52), (0, 0.52)], (0.4, 0.44, 0.48))
    for k in range(70):                                                                         # the wood
        side = k % 2
        x = s.rng.uniform(-0.05, 0.36) if side == 0 else s.rng.uniform(0.68, 1.05)
        y = s.rng.uniform(-0.05, 0.42)
        g = s.rng.uniform(0.09, 0.2)
        s.ellipse(x, y, s.rng.uniform(0.05, 0.12), s.rng.uniform(0.04, 0.09), (g * 0.8, g, g * 0.6))
    for x in (0.08, 0.22, 0.31, 0.78, 0.9):
        s.line([(x, 0.2), (x + 0.01, 0.52)], (0.1, 0.08, 0.06), 0.014)
    s.poly([(0, 0.5), (0.35, 0.535), (0.7, 0.52), (1, 0.54), (1, 0.56), (0, 0.56)], (0.15, 0.13, 0.07))
    s.poly([(0.25, 0.52), (0.42, 0.505), (0.43, 0.54), (0.27, 0.545)], (0.75, 0.56, 0.42))      # the youth, kneeling, leaning out
    s.poly([(0.36, 0.43), (0.46, 0.39), (0.56, 0.43), (0.53, 0.5), (0.4, 0.53), (0.35, 0.49)], (0.86, 0.83, 0.74))
    s.shade([(0.4, 0.47), (0.53, 0.47), (0.53, 0.5), (0.4, 0.53)], (0.45, 0.43, 0.38), 0.5, 2)
    s.line([(0.5, 0.43), (0.57, 0.48), (0.61, 0.535)], (0.78, 0.58, 0.44), 0.016)
    s.ellipse(0.575, 0.425, 0.034, 0.028, (0.8, 0.6, 0.46))
    for k in range(12):
        a = s.rng.uniform(math.pi * 0.9, math.pi * 2.0)
        s.ellipse(0.575 + 0.032 * math.cos(a), 0.418 + 0.026 * math.sin(a), 0.012, 0.01, (0.32, 0.2, 0.1))
    for k in range(7):                                                                          # narcissi on the bank
        x, y = 0.7 + k * 0.035 + s.rng.uniform(-0.01, 0.01), 0.53 + s.rng.uniform(-0.01, 0.01)
        s.line([(x, y + 0.03), (x, y)], (0.3, 0.45, 0.2), 0.004)
        for j in range(6):
            a = j / 6 * math.tau
            s.ellipse(x + 0.011 * math.cos(a), y + 0.008 * math.sin(a), 0.007, 0.006, (0.95, 0.94, 0.86))
        s.ellipse(x, y, 0.005, 0.004, (0.95, 0.75, 0.2))
    a = s.array()
    cut = int(0.56 * s.H)
    top = a[:cut]
    mirror = top[::-1][: s.H - cut]                                                            # his reflection in the pool
    yy, xx = np.mgrid[0:mirror.shape[0], 0:s.W]
    shift = 3.0 * np.sin(yy * 0.35) * (0.4 + yy / mirror.shape[0])
    mirror = np.stack([map_coordinates(mirror[..., i], [yy, np.clip(xx + shift, 0, s.W - 1)], order=1) for i in range(3)], -1)
    depth = np.linspace(0, 1, mirror.shape[0])[:, None, None]
    a[cut:] = mirror * np.array([0.5, 0.58, 0.64]) * (1 - 0.35 * depth) + np.array([0.02, 0.04, 0.05])
    s.set(a)
    for k in range(40):
        x, y = s.rng.uniform(0.0, 1.0), s.rng.uniform(0.57, 1.0)
        s.line([(x, y), (x + s.rng.uniform(0.03, 0.09), y)], (0.55, 0.6, 0.6), 0.002)


def sisyphus(s):
    s.gradient([(0, (0.24, 0.21, 0.36)), (0.45, (0.82, 0.52, 0.34)), (0.62, (0.95, 0.76, 0.46))])
    s.glow(0.12, 0.6, 0.2, (1.0, 0.82, 0.5), 0.7)
    s.poly([(0, 0.62), (0.12, 0.54), (0.25, 0.58), (0.38, 0.5), (0.5, 0.57), (0.62, 0.52), (0.75, 0.6), (0.9, 0.5), (1, 0.55), (1, 0.7), (0, 0.7)], (0.38, 0.32, 0.45))
    s.poly([(0, 1), (0, 0.95), (0.3, 0.8), (0.55, 0.55), (0.72, 0.4), (0.8, 0.33), (0.86, 0.335), (0.95, 0.42), (1, 0.46), (1, 1)], (0.36, 0.3, 0.16))
    s.shade([(0.84, 0.34), (0.95, 0.42), (1, 0.46), (1, 1), (0.8, 1), (0.7, 0.6)], (0.14, 0.11, 0.08), 0.65, 8)
    s.shade([(0, 0.95), (0.3, 0.8), (0.55, 0.55), (0.6, 0.6), (0.3, 0.9), (0, 1)], (0.6, 0.48, 0.26), 0.45, 6)
    s.texture(0.4, 1.5, 1401, 0.33, 1.0)
    s.line([(0.08, 0.98), (0.25, 0.86), (0.2, 0.8), (0.42, 0.68), (0.38, 0.63), (0.58, 0.5), (0.62, 0.45)], (0.6, 0.52, 0.36), 0.006)
    s.ellipse(0.69, 0.36, 0.062, 0.08, (0.48, 0.46, 0.43))                                    # the boulder, nearly at the top
    s.shade([(0.69, 0.29), (0.76, 0.33), (0.75, 0.43), (0.69, 0.44)], (0.2, 0.19, 0.2), 0.6, 4)
    s.glow(0.665, 0.33, 0.025, (0.85, 0.72, 0.6), 0.6)
    s.poly([(0.598, 0.475), (0.612, 0.475), (0.638, 0.39), (0.628, 0.385)], (0.12, 0.09, 0.08))  # Sisyphus, pushing
    s.line([(0.632, 0.39), (0.646, 0.38)], (0.12, 0.09, 0.08), 0.006)
    s.ellipse(0.628, 0.373, 0.009, 0.012, (0.13, 0.1, 0.08))
    s.line([(0.605, 0.475), (0.59, 0.478)], (0.12, 0.09, 0.08), 0.006)


def disputed_apple(s):
    s.gradient([(0, (0.12, 0.1, 0.08)), (1, (0.05, 0.04, 0.035))])
    s.glow(0.25, 0.2, 0.5, (0.22, 0.18, 0.13), 0.8)
    s.poly([(0, 0.64), (1, 0.62), (1, 1), (0, 1)], (0.22, 0.14, 0.08))
    s.line([(0, 0.66), (1, 0.64)], (0.4, 0.27, 0.15), 0.006)
    s.poly([(0, 0.6), (0.46, 0.63), (0.38, 1), (0, 1)], (0.84, 0.82, 0.76))                    # a tablecloth
    for k in range(4):
        s.shade([(0.05 + k * 0.08, 0.62), (0.09 + k * 0.08, 0.62), (0.06 + k * 0.07, 1), (0.02 + k * 0.07, 1)], (0.5, 0.48, 0.45), 0.5, 3)
    s.ellipse(0.56, 0.67, 0.33, 0.085, (0.5, 0.51, 0.53))                                     # pewter plate
    s.ellipse(0.56, 0.665, 0.27, 0.06, (0.38, 0.39, 0.41))
    for k in range(22):                                                                        # grapes
        x, y = 0.7 + s.rng.normal(0, 0.05), 0.58 + abs(s.rng.normal(0, 0.035))
        s.ellipse(x, y, 0.036, 0.028, (0.22, 0.1, 0.22))
        s.ellipse(x - 0.008, y - 0.007, 0.007, 0.005, (0.5, 0.36, 0.5))
    s.ellipse(0.34, 0.595, 0.09, 0.07, (0.52, 0.14, 0.1))                                     # pomegranate
    s.poly([(0.34, 0.545), (0.38, 0.545), (0.375, 0.53), (0.345, 0.53)], (0.4, 0.12, 0.08))
    s.ellipse(0.53, 0.6, 0.1, 0.077, (0.82, 0.6, 0.17))                                      # the golden apple
    s.shade([(0.55, 0.56), (0.62, 0.59), (0.6, 0.66), (0.53, 0.665)], (0.4, 0.25, 0.06), 0.55, 3)
    s.glow(0.505, 0.575, 0.02, (1.0, 0.94, 0.64), 0.9)
    s.line([(0.53, 0.54), (0.535, 0.515)], (0.3, 0.2, 0.1), 0.006)
    s.poly([(0.535, 0.52), (0.58, 0.5), (0.6, 0.515), (0.56, 0.53)], (0.25, 0.4, 0.15))
    s.poly([(0.6, 0.76), (0.94, 0.8), (0.94, 0.81), (0.6, 0.775)], (0.62, 0.63, 0.66))        # knife
    s.poly([(0.5, 0.745), (0.6, 0.76), (0.6, 0.775), (0.5, 0.765)], (0.2, 0.12, 0.07))


def medusa(s):
    s.gradient([(0, (0.2, 0.25, 0.25)), (1, (0.07, 0.1, 0.1))])
    s.glow(0.5, 0.35, 0.4, (0.28, 0.33, 0.31), 0.8)
    s.poly([(0.41, 0.55), (0.59, 0.55), (0.62, 0.74), (0.38, 0.74)], (0.76, 0.58, 0.46))      # her neck, from behind
    s.poly([(0.06, 1), (0.13, 0.79), (0.33, 0.69), (0.67, 0.69), (0.87, 0.79), (0.94, 1)], (0.82, 0.79, 0.71))
    for k in range(6):
        x = 0.2 + k * 0.12
        s.shade([(x, 0.72), (x + 0.03, 0.72), (x + 0.05, 1), (x + 0.01, 1)], (0.48, 0.46, 0.42), 0.45, 3)
    for k in range(46):                                                                        # the hair
        a = s.rng.uniform(0, math.tau)
        r = math.sqrt(s.rng.uniform(0, 1)) * 0.16
        x, y = 0.5 + r * math.cos(a), 0.37 + r * 1.15 * math.sin(a)
        heading = s.rng.uniform(0, math.tau)
        pts = [(x, y)]
        for j in range(9):
            heading += s.rng.normal(0, 0.7)
            x, y = x + 0.022 * math.cos(heading), y + 0.022 * math.sin(heading) * 0.75
            pts.append((x, y))
        g = s.rng.uniform(0.75, 1.15)
        width = s.rng.uniform(0.026, 0.04)
        s.line(pts, (0.08 * g, 0.16 * g, 0.07 * g), width * 1.35)
        s.line(pts, (0.24 * g, 0.42 * g, 0.16 * g), width)
        s.line(pts, (0.5 * g, 0.62 * g, 0.3 * g), width * 0.3)
        if math.hypot(pts[-1][0] - 0.5, pts[-1][1] - 0.37) > 0.15:
            hx, hy = pts[-1]
            s.ellipse(hx, hy, 0.016, 0.012, (0.22 * g, 0.36 * g, 0.14 * g))
            s.line([(hx, hy), (hx + 0.022 * math.cos(heading), hy + 0.016 * math.sin(heading))], (0.75, 0.12, 0.1), 0.004)
    s.line([(0.36, 0.42), (0.43, 0.445), (0.5, 0.452), (0.57, 0.445), (0.64, 0.42)], (0.82, 0.62, 0.24), 0.012)


SCENES = {"small_splash": small_splash, "achilles": achilles, "narcissus": narcissus,
          "sisyphus": sisyphus, "disputed_apple": disputed_apple, "medusa": medusa}


# --- Painting it -----------------------------------------------------------------------------------

def brushwork(base, seed):
    """Repaints a laid-out scene with strokes: broad ones first, then finer ones only where the picture
    still differs from the layout. Each stroke runs along the forms (across the brightness gradient) and
    takes its colour from under it, a little off."""
    H, W = base.shape[:2]
    rng = np.random.default_rng(seed)
    canvas = Image.fromarray(np.clip(gaussian_filter(base, (4, 4, 0)) * 255, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(canvas)
    lum = base @ np.array([0.3, 0.55, 0.15])
    scale = W / 700
    for width, length, threshold in ((16, 50, 0.0), (9, 30, 0.04), (5, 17, 0.07), (2, 7, 0.1)):
        width, length = max(1, int(width * scale)), max(2, int(length * scale))
        ref = gaussian_filter(base, (width * 0.4, width * 0.4, 0))
        sm = gaussian_filter(lum, width * 0.8)
        gy, gx = sobel(sm, 0), sobel(sm, 1)
        now = np.asarray(canvas, dtype=float) / 255
        err = np.abs(now - ref).sum(-1)
        step = max(2, int(width * 0.75))
        ys, xs = np.mgrid[step // 2:H:step, step // 2:W:step]
        ys = np.clip(ys + rng.integers(-step // 2, step // 2 + 1, ys.shape), 0, H - 1).ravel()
        xs = np.clip(xs + rng.integers(-step // 2, step // 2 + 1, xs.shape), 0, W - 1).ravel()
        order = rng.permutation(len(ys))
        for i in order:
            y, x = ys[i], xs[i]
            if err[y, x] < threshold:
                continue
            g = math.hypot(gx[y, x], gy[y, x])
            a = math.atan2(gy[y, x], gx[y, x]) + math.pi / 2 if g > 1e-3 else rng.uniform(0, math.pi)
            a += rng.normal(0, 0.18)
            c = ref[y, x] * (1 + rng.normal(0, 0.06)) + rng.normal(0, 0.02, 3)
            l = length * rng.uniform(0.7, 1.3)
            dx, dy = math.cos(a) * l / 2, math.sin(a) * l / 2
            d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=c8(c), width=width)
    return np.asarray(canvas, dtype=float) / 255


def craquelure(h, w, seed, cell):
    """Fine cracks in old paint: the edges of an irregular net of cells."""
    rng = np.random.default_rng(seed)
    pts = rng.random((int(h * w / cell ** 2), 2)) * [h, w]
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    wob = (noise((h, w), 6, seed + 1) - 0.5) * cell * 0.8
    q = np.stack([(yy + wob).ravel(), (xx - wob).ravel()], -1)
    dist, _ = cKDTree(pts).query(q, k=2)
    gap = (dist[:, 1] - dist[:, 0]).reshape(h, w)
    return np.clip(1 - gap / 0.55, 0, 1) * np.clip((noise((h, w), 12, seed + 2) - 0.35) * 3, 0, 1)


def painting(name, seed):
    s, w, h = region(name)
    sc = Scene(w, h, seed)
    SCENES[name](sc)
    base = sc.array()
    hh, ww = base.shape[:2]
    base = base * (0.92 + 0.16 * noise((hh, ww), 3, seed + 4)[..., None]) * (1 + 0.08 * (noise((hh, ww, 3), 7, seed + 5) - 0.5))
    paint = brushwork(base, seed + 1)
    img = np.asarray(Image.fromarray(np.clip(paint * 255, 0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=float) / 255
    stroke_relief = gaussian_filter(img.mean(-1), 0.6) - gaussian_filter(img.mean(-1), 2.5)
    yy, xx = np.mgrid[0:h, 0:w]
    weave = (np.sin(xx * 2.2) * np.sin(yy * 2.2)) * 0.5
    cracks = craquelure(h, w, seed + 2, cell=4.5 + w / 300)
    e = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]).astype(float) / min(w, h)
    edge = np.clip(1 - e / 0.12, 0, 1) ** 2
    varnish = np.array([1.0, 0.94, 0.8]) * (0.92 + 0.08 * noise((h, w), 20, seed + 3)[..., None])
    img = img * varnish * (1 - 0.22 * edge[..., None]) * (1 + 0.025 * weave[..., None]) * (1 - 0.11 * cracks[..., None])
    rgb[s] = np.clip(img, 0, 1)
    height[s] = stroke_relief * 0.004 + weave * 0.00015 - cracks * 0.0004


# --- The frames, labels and lamps -------------------------------------------------------------------

def gilt_profile(u):
    """Across the frame's face, outer edge to inner: a round outer bead, a cove, a broad carved swell,
    a row of beads, and the flat sight edge."""
    if u < 0.12:
        return 0.55 + 0.4 * math.sqrt(max(0.0, 1 - ((u - 0.06) / 0.06) ** 2))
    if u < 0.25:
        return 0.3 + 0.25 * (1 - math.sin(math.pi * (u - 0.12) / 0.13))
    if u < 0.72:
        return 0.45 + 0.5 * math.sin(math.pi * (u - 0.25) / 0.47)
    if u < 0.86:
        return 0.5
    return 0.32


def gilt():
    s, w, h = region("gilt")
    u = np.linspace(0, 1, w)
    prof = np.array([gilt_profile(x) for x in u])[None, :].repeat(h, 0)

    def ornament(d, ss):
        for k in range(13):                     # leaves on the swell: twelve to the strip, so lengths of it join up
            cx, cy = w * 0.485 * ss, k * h / 12 * ss
            d.ellipse([cx - 9 * ss, cy - 15 * ss, cx + 9 * ss, cy + 15 * ss], fill=170)
            d.line([cx, cy - 13 * ss, cx, cy + 13 * ss], fill=60, width=ss)
            for side in (-1, 1):
                d.ellipse([cx + side * 11 * ss - 4 * ss, cy + 12 * ss, cx + side * 11 * ss + 4 * ss, cy + 22 * ss], fill=150)
        for k in range(49):                     # beads, forty-eight to the strip
            cx, cy = w * 0.79 * ss, k * h / 48 * ss
            d.ellipse([cx - 3.6 * ss, cy - 3.6 * ss, cx + 3.6 * ss, cy + 3.6 * ss], fill=200)

    orn = gaussian_filter(drawn(w, h, ornament), 0.6)
    form = prof + 0.35 * orn * ((u > 0.25) & (u < 0.86))[None, :]
    cavity = np.clip(gaussian_filter(form, 2.0) - form, 0, 1)
    rub = np.clip((form - 0.82) * 4 + (noise((h, w), 3, 7801) - 0.55) * 1.5, 0, 1)
    c = GOLD * (0.75 + 0.35 * form[..., None]) * (0.92 + 0.12 * noise((h, w), 2, 7802)[..., None])
    c = c * (1 - rub[..., None] * 0.45) + BOLE * rub[..., None] * 0.45
    c = c * (1 - np.clip(cavity * 6, 0, 0.7)[..., None]) + np.array([0.08, 0.06, 0.03]) * np.clip(cavity * 6, 0, 0.7)[..., None]
    chips = (noise((h, w), 1.0, 7803) > 0.965)
    c = np.where(chips[..., None], np.array([0.82, 0.78, 0.68]), c)
    rgb[s] = np.clip(c, 0, 1)
    height[s] = form * 0.008 - chips * 0.0006


def gilt_plain():
    s, w, h = region("gilt_plain")
    c = GOLD * (0.7 + 0.2 * noise((h, w), 3, 7811)[..., None])
    grime = np.clip((noise((h, w), 8, 7812) - 0.4) * 1.5, 0, 1)
    rgb[s] = c * (1 - 0.4 * grime[..., None])


def brushed_brass(w, h, seed):
    streak = gaussian_filter(np.random.default_rng(seed).random((h, w)), (0.35, 30), mode="wrap")
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-9)
    tarnish = np.clip((noise((h, w), 4, seed + 1) - 0.62) * 3, 0, 1)
    c = BRASS * (0.8 + 0.3 * streak[..., None])
    return c * (1 - 0.2 * tarnish[..., None])


def label(name, title, subtitle, seed):
    s, w, h = region("label_" + name)
    c = brushed_brass(w, h, seed)

    def engrave(d, ss):
        d.rectangle([3 * ss, 3 * ss, (w - 4) * ss, (h - 4) * ss], outline=255, width=ss)
        size = 17 * ss
        font = ImageFont.truetype(SERIF_BOLD, size)
        while d.textlength(title, font=font) > (w - 16) * ss:
            size -= ss
            font = ImageFont.truetype(SERIF_BOLD, size)
        d.text((w * ss / 2, h * ss * 0.38), title, font=font, fill=255, anchor="mm")
        small = ImageFont.truetype(SERIF_ITAL, int(11 * ss))
        d.text((w * ss / 2, h * ss * 0.74), subtitle, font=small, fill=255, anchor="mm")

    cut = drawn(w, h, engrave)
    rgb[s] = c * (1 - cut[..., None]) + PATINA * cut[..., None]
    height[s] = -gaussian_filter(cut, 0.5) * 0.001


def bleed():
    filled = np.zeros((N, N), bool)
    for x, y, w, h in L.REGIONS.values():
        filled[y:y + h, x:x + w] = True
    for _ in range(6):
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            grow = np.roll(filled, step, axis) & ~filled
            rgb[grow] = np.roll(rgb, step, axis)[grow]
            filled |= grow


for k, name in enumerate(L.PAINTINGS):
    painting(name, 11000 + 100 * k)
gilt()
gilt_plain()
s, w, h = region("brass")
rgb[s] = brushed_brass(w, h, 7901)
s, w, h = region("lamp")
rgb[s] = np.array([1.0, 0.88, 0.66])
for k, (name, (_, _, title, subtitle)) in enumerate(L.PAINTINGS.items()):
    label(name, title, subtitle, 7950 + k)
bleed()
Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_paintings_albedo.png", optimize=True)
hgt = gaussian_filter(height, 0.5)
px = 0.002
dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / (2 * px)
dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / (2 * px)
ln = np.sqrt(dx * dx + dy * dy + 1)
Image.fromarray(np.clip((np.stack([-dx / ln, dy / ln, 1 / ln], -1) * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_paintings_normal.png", optimize=True)

# The picture lights: each canvas glows most at the top, under its lamp, and fades down the picture
glow = np.zeros((L.GLOW, L.GLOW, 3))
f = L.GLOW / N
for name in L.PAINTINGS:
    x, y, w, h = L.REGIONS[name]
    gx, gy, gw, gh = int(x * f), int(y * f), int(w * f), int(h * f)
    small = np.asarray(Image.fromarray(np.clip(rgb[y:y + h, x:x + w] * 255, 0, 255).astype(np.uint8)).resize((gw, gh), Image.BOX), dtype=float) / 255
    t = np.linspace(0, 1, gh)[:, None]
    u = np.linspace(-1, 1, gw)[None, :]
    light = (0.25 + 0.75 * np.exp(-2.6 * t)) * (0.7 + 0.3 * np.cos(u * math.pi / 2))
    glow[gy:gy + gh, gx:gx + gw] = small * light[..., None]
x, y, w, h = L.REGIONS["lamp"]
glow[int(y * f):int((y + h) * f), int(x * f):int((x + w) * f)] = np.array([1.0, 0.88, 0.66])
Image.fromarray(np.clip(glow * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / "int_paintings_glow.png", optimize=True)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")
MATERIALS = {
    "int_canvas": 'roughness = 0.5\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n'
                  'emission_enabled = true\nemission_texture = ExtResource("3_glow")\nemission_energy_multiplier = 0.6\n',
    "int_gilt": 'metallic = 0.75\nroughness = 0.42\nnormal_enabled = true\nnormal_texture = ExtResource("2_normal")\n',
    "int_picture_lamp": 'emission_enabled = true\nemission_texture = ExtResource("3_glow")\nemission_energy_multiplier = 3.0\n',
}
for name, extra in MATERIALS.items():
    (OUT / (name + ".tres")).write_text(
        '[gd_resource type="StandardMaterial3D" format=3]\n\n'
        '[ext_resource type="Texture2D" path="%sint_paintings_albedo.png" id="1_albedo"]\n'
        '[ext_resource type="Texture2D" path="%sint_paintings_normal.png" id="2_normal"]\n'
        '[ext_resource type="Texture2D" path="%sint_paintings_glow.png" id="3_glow"]\n\n'
        '[resource]\nalbedo_texture = ExtResource("1_albedo")\n%s' % (RES, RES, RES, extra), encoding="utf8", newline="\n")
print("painting art written to", OUT)
