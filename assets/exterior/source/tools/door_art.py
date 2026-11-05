"""The bronze doors: eight relief panels telling how the Last Book came to the museum, drawn as height
fields at more than twice the old resolution. Read down the left leaf, then the right: the Horse, Troy
burning, Homer singing it, the Library's shelves, the Library burning, the librarian running, the Book,
and the card that says it is 2,000 years overdue.

Shapes are given in panel units: x 0 to A, y 0 to 1 downward, so a circle is a circle."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, gaussian_filter

A = 1.648               # panel width over height
M = 0.825               # metres per panel unit
W, H_ = 2048, 1243
FONT = "C:/Windows/Fonts/palab.ttf"


def U(pts):
    return [(x / A, y) for x, y in pts]


def smooth(pts, n=10):
    """A Catmull-Rom curve through the points."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        for t in np.linspace(0, 1, n, endpoint=False):
            a, b, c, d = map(np.array, (p[i - 1], p[i], p[i + 1], p[i + 2]))
            out.append(tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3)))
    out.append(tuple(pts[-1]))
    return out


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def turned(pts, cx, cy, deg):
    a = math.radians(deg)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


class Panel:
    def __init__(self, relief):
        self.f = relief
        self.f.H += 0.006

    def poly(self, pts, h=0.03, roll=0.03, level=0.004):
        self.f.mass(poly=U(pts), height=h, roll=roll, level=level)

    def circ(self, cx, cy, r, h=0.02, roll=0.012, level=0.004):
        self.ell(cx, cy, r, r, h, roll, level)

    def ell(self, cx, cy, rx, ry, h=0.02, roll=0.012, level=0.004, deg=0.0):
        t = np.linspace(0, math.tau, 40, endpoint=False)
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in t]
        self.poly(turned(pts, cx, cy, deg), h, roll, level)

    def line(self, pts, w, d, soft=0.5):
        self.f.add_line(U(pts), w, d, soft)

    def curve(self, pts, w, d, soft=0.5):
        self.line(smooth(pts), w, d, soft)

    def cut(self, pts, level=0.002, roll=0.012):
        """Sink a shape back to a level, with a soft edge: an arch, a niche, a hole."""
        m = self.f.mask(poly=U(pts)) > 0.5
        d = distance_transform_edt(m) * self.f.px
        k = 1 - np.exp(-(d / roll) ** 1.5)
        self.f.H = np.where(m, self.f.H * (1 - k) + level * k, self.f.H).astype(np.float32)

    def text(self, s, cx, cy, size, depth=0.01, deg=0.0, spacing=0.0):
        """Raised letters, turned about their centre if asked. cx, cy in panel units."""
        f = self.f
        im = Image.new("L", (f.w, f.h), 0)
        d = ImageDraw.Draw(im)
        font = ImageFont.truetype(FONT, int(size))
        widths = [d.textlength(c, font=font) for c in s]
        total = sum(widths) + spacing * (len(s) - 1)
        x = cx / A * f.w - total / 2
        y = cy * f.h
        for c, w in zip(s, widths):
            d.text((x, y), c, font=font, fill=255, anchor="lm")
            x += w + spacing
        if deg:
            im = im.rotate(-deg, resample=Image.BICUBIC, center=(cx / A * f.w, cy * f.h))
        m = np.asarray(im, dtype=np.float32) / 255
        dist = distance_transform_edt(m > 0.5) * f.px
        f.H += (depth * np.clip(dist / (abs(depth) * 0.5), 0, 1) * (m > 0.5)).astype(np.float32)

    def bricks(self, x0, y0, x1, y1, row=0.042, course=0.085):
        """Masonry joints scratched into a wall."""
        y, i = y0 + row, 0
        while y < y1 - 0.005:
            self.line([(x0, y), (x1, y)], 0.0028, -0.0028)
            x = x0 + (course / 2 if i % 2 else course)
            while x < x1 - 0.01:
                self.line([(x, y), (x, y + row)], 0.0028, -0.0028)
                x += course
            y += row
            i += 1

    def battlements(self, x0, x1, y, h=0.03, level=0.004, w=0.045, gap=0.04):
        x = x0
        while x + w <= x1 + 0.001:
            self.poly(rect(x, y - 0.04, x + w, y + 0.01), h, 0.008, level)
            x += w + gap

    def flames(self, x0, x1, base, top, n, seed, h=0.02, roll=0.05, level=0.004):
        """A wall of fire: leaning tongues of unequal height, with their own inner lines."""
        rng = np.random.default_rng(seed)
        step = (x1 - x0) / n
        tall = base - top
        pts = [(x0, base)]
        tips = []
        for i in range(n):
            x = x0 + i * step
            env = math.sin(math.pi * (i + 0.5) / n) ** 0.6
            H = tall * env * rng.uniform(0.66, 1.0)
            lean = rng.uniform(-0.25, 0.45) * step
            valley = H * rng.uniform(0.12, 0.3)
            pts += [(x + 0.02 * step, base - valley),
                    (x + 0.14 * step + lean * 0.15, base - H * 0.40),
                    (x + 0.20 * step + lean * 0.65, base - H * 0.72),
                    (x + 0.50 * step + lean, base - H),
                    (x + 0.66 * step + lean * 0.4, base - H * 0.66),
                    (x + 0.80 * step + lean * 0.2, base - H * 0.38)]
            tips.append((x + 0.5 * step, H, lean))
        pts.append((x1, base))
        self.poly(smooth(pts, 3), h, roll, level)
        for x, H, lean in tips:
            self.curve([(x + 0.1 * step, base - H * 0.10), (x - 0.06 * step + lean * 0.2, base - H * 0.42), (x + lean * 0.75, base - H * 0.82)], 0.006, 0.006)
            self.curve([(x + 0.26 * step, base - H * 0.08), (x + 0.14 * step + lean * 0.2, base - H * 0.34), (x + 0.2 * step + lean * 0.5, base - H * 0.58)], 0.005, -0.005)

    def sky(self, seed, n=9, y1=0.3):
        """A scatter of raised stars in the empty corners."""
        rng = np.random.default_rng(seed)
        for _ in range(n):
            self.circ(rng.uniform(0.12, 1.53), rng.uniform(0.1, y1), 0.0075, 0.007, 0.004)

    def finish(self, seed):
        """Border, hammered ground and the slight unevenness of a casting."""
        f = self.f
        rng = np.random.default_rng(seed)
        hammered = gaussian_filter(rng.standard_normal((f.h, f.w)), 5.0)
        hammered /= hammered.std()
        ground = np.clip(1.0 - (f.H - 0.006) / 0.012, 0.25, 1.0)
        f.H += (hammered * 0.00065 * ground).astype(np.float32)
        wave = gaussian_filter(rng.standard_normal((f.h, f.w)), 26.0)
        f.H += (wave / wave.std() * 0.0009).astype(np.float32)
        # A raised frame with a row of beads
        e, r = 0.04, 0.009
        self.poly(rect(0, 0, A, e), 0.022, 0.01, 0.0)
        self.poly(rect(0, 1 - e, A, 1), 0.022, 0.01, 0.0)
        self.poly(rect(0, 0, e, 1), 0.022, 0.01, 0.0)
        self.poly(rect(A - e, 0, A, 1), 0.022, 0.01, 0.0)
        for i in range(int(A / 0.034)):
            x = 0.062 + i * 0.0345
            if x < A - 0.05:
                self.circ(x, 0.062, r, 0.009, 0.005)
                self.circ(x, 0.938, r, 0.009, 0.005)
        for i in range(int(1 / 0.034)):
            y = 0.095 + i * 0.0345
            if y < 0.92:
                self.circ(0.062, y, r, 0.009, 0.005)
                self.circ(A - 0.062, y, r, 0.009, 0.005)


# --- The eight panels ---------------------------------------------------------------------------
def p_horse(p):
    p.sky(1, 8, 0.28)
    # Troy behind, low and far away
    p.poly(rect(0.08, 0.60, 1.57, 0.86), 0.006, 0.01)
    p.battlements(0.09, 1.55, 0.60, 0.006)
    for x0, x1 in ((0.14, 0.33), (1.32, 1.51)):
        p.poly(rect(x0, 0.40, x1, 0.86), 0.009, 0.012)
        p.battlements(x0 + 0.005, x1, 0.40, 0.009)
        p.bricks(x0, 0.42, x1, 0.86)
    # Tail, far legs, then the body
    p.poly(smooth([(0.42, 0.42), (0.35, 0.47), (0.31, 0.58), (0.30, 0.68), (0.33, 0.71), (0.355, 0.60), (0.40, 0.50)], 5), 0.026, 0.022, 0.006)
    for x in (0.56, 0.90):
        p.poly([(x, 0.55), (x + 0.058, 0.55), (x + 0.05, 0.80), (x + 0.01, 0.80)], 0.022, 0.014, 0.006)
    body = [(0.40, 0.43), (0.50, 0.375), (0.85, 0.385), (0.95, 0.335), (1.02, 0.225), (1.065, 0.135), (1.085, 0.075), (1.118, 0.125), (1.185, 0.165), (1.262, 0.235),
            (1.275, 0.272), (1.238, 0.296), (1.165, 0.272), (1.115, 0.272), (1.085, 0.365), (1.062, 0.46), (1.02, 0.545), (0.95, 0.585), (0.50, 0.585), (0.42, 0.56), (0.38, 0.49)]
    p.poly(body, 0.036, 0.055, 0.008)
    for x in (0.46, 0.98):
        p.poly([(x, 0.54), (x + 0.066, 0.54), (x + 0.056, 0.80), (x + 0.012, 0.80)], 0.03, 0.016, 0.01)
    # Planks and ribs
    for y in (0.43, 0.475, 0.525):
        p.curve([(0.41, y + 0.015), (0.62, y - 0.01), (0.85, y - 0.005), (1.03, y - 0.02)], 0.005, -0.006)
    for x in (0.50, 0.59, 0.68, 0.77, 0.86, 0.95):
        p.line([(x, 0.385), (x + 0.004, 0.58)], 0.005, -0.006)
    for t in (0.0, 0.05, 0.1):
        p.curve([(0.98 + t, 0.38 + t * 0.2), (1.02 + t, 0.28), (1.06 + t * 0.4, 0.17)], 0.004, -0.005)
    # Mane, eye, bridle
    for i in range(9):
        t = i / 8
        x, y = 1.085 - t * 0.15, 0.10 + t * 0.235
        p.poly([(x + 0.015, y - 0.02), (x - 0.045, y - 0.015), (x - 0.012, y + 0.03)], 0.012, 0.012, 0.034)
    p.circ(1.148, 0.185, 0.014, 0.007, 0.004, 0.034)
    p.circ(1.148, 0.185, 0.005, 0.005, 0.003, 0.04)
    p.curve([(1.10, 0.15), (1.17, 0.235), (1.245, 0.27)], 0.006, 0.006)
    p.line([(1.175, 0.24), (1.14, 0.27)], 0.005, 0.005)
    # The hatch, a Greek looking out of it, and the rope he has let down
    p.cut(rect(0.70, 0.47, 0.81, 0.565), 0.018, 0.006)
    p.line([(0.70, 0.47), (0.81, 0.47), (0.81, 0.565), (0.70, 0.565), (0.70, 0.47)], 0.009, 0.006)
    p.circ(0.755, 0.52, 0.026, 0.022, 0.012, 0.022)
    p.curve([(0.725, 0.50), (0.755, 0.478), (0.785, 0.50)], 0.012, 0.012)
    p.curve([(0.755, 0.495), (0.74, 0.47), (0.70, 0.455)], 0.008, 0.01)
    p.curve([(0.70, 0.56), (0.69, 0.66), (0.705, 0.78)], 0.006, 0.012)
    # Platform and wheels
    p.poly(rect(0.33, 0.785, 1.14, 0.83), 0.03, 0.01, 0.008)
    for x in (0.40, 0.50, 0.62, 0.74, 0.86, 0.98, 1.08):
        p.line([(x, 0.79), (x, 0.826)], 0.004, -0.005)
    for x in (0.44, 0.735, 1.03):
        p.circ(x, 0.865, 0.058, 0.03, 0.012, 0.008)
        p.cut([(x + 0.04 * math.cos(a), 0.865 + 0.04 * math.sin(a)) for a in np.linspace(0, math.tau, 30)], 0.022, 0.004)
        for a in np.arange(0, math.pi, math.pi / 3):
            p.line([(x - 0.044 * math.cos(a), 0.865 - 0.044 * math.sin(a)), (x + 0.044 * math.cos(a), 0.865 + 0.044 * math.sin(a))], 0.008, 0.012)
        p.circ(x, 0.865, 0.016, 0.012, 0.006, 0.03)


def p_troy(p):
    # Fire behind the walls
    p.flames(0.09, 1.56, 0.62, 0.08, 9, 4, 0.016, 0.06)
    p.sky(2, 4, 0.16)
    # The wall, two towers and the gate
    p.poly(rect(0.08, 0.46, 1.57, 0.76), 0.024, 0.01)
    p.battlements(0.09, 1.55, 0.46, 0.024)
    for x0, x1 in ((0.20, 0.47), (1.18, 1.45)):
        p.poly(rect(x0, 0.30, x1, 0.76), 0.034, 0.012, 0.006)
        p.battlements(x0 + 0.006, x1, 0.30, 0.034, 0.006)
        p.bricks(x0, 0.32, x1, 0.76)
        p.poly(rect((x0 + x1) / 2 - 0.018, 0.38, (x0 + x1) / 2 + 0.018, 0.46), 0.012, 0.006, 0.0)
        p.cut(rect((x0 + x1) / 2 - 0.016, 0.38, (x0 + x1) / 2 + 0.016, 0.46), 0.006, 0.005)
    p.bricks(0.08, 0.48, 0.20, 0.76)
    p.bricks(0.47, 0.48, 1.18, 0.76)
    p.bricks(1.45, 0.48, 1.57, 0.76)
    # The gate stands open
    gate = [(0.72, 0.76), (0.72, 0.60)] + [(0.824 + 0.104 * math.cos(a), 0.60 - 0.11 * math.sin(a)) for a in np.linspace(math.pi, 0, 18)] + [(0.928, 0.76)]
    p.cut(gate, 0.002, 0.012)
    p.curve([(0.70, 0.76), (0.70, 0.60), (0.75, 0.50), (0.824, 0.47), (0.90, 0.50), (0.948, 0.60), (0.948, 0.76)], 0.016, 0.01)
    # The sea and a thousand ships, or at least seven
    for y, off in ((0.80, 0.0), (0.905, 0.05)):
        p.curve([(0.08 + i * 0.075 + off, y + (0.012 if i % 2 else -0.012)) for i in range(20) if 0.08 + i * 0.075 + off < 1.57], 0.006, 0.008)
    for i, x in enumerate((0.20, 0.42, 0.63, 0.82, 1.02, 1.23, 1.44)):
        y = 0.865 + (0.012 if i % 2 else -0.008)
        p.poly([(x - 0.075, y - 0.018), (x + 0.075, y - 0.018), (x + 0.092, y - 0.04), (x + 0.058, y + 0.016), (x - 0.058, y + 0.016)], 0.02, 0.008, 0.008)
        p.line([(x, y - 0.018), (x, y - 0.09)], 0.005, 0.016)
        p.poly([(x - 0.04, y - 0.085), (x + 0.04, y - 0.085), (x + 0.048, y - 0.036), (x - 0.048, y - 0.036)], 0.014, 0.012, 0.012)


def p_homer(p):
    p.sky(3, 7, 0.26)
    # Drapery
    p.poly(smooth([(0.26, 0.93), (0.31, 0.82), (0.48, 0.74), (0.72, 0.78), (0.92, 0.86), (0.98, 0.93)], 5) + [(0.26, 0.93)], 0.026, 0.05, 0.006)
    for x, b in ((0.38, 0.90), (0.50, 0.92), (0.62, 0.92), (0.76, 0.92)):
        p.curve([(x + 0.04, 0.77), (x + 0.0, 0.83), (x + 0.02, b)], 0.006, -0.006)
    # Head in profile, looking up towards the lyre
    head = [(0.73, 0.15), (0.80, 0.19), (0.835, 0.25), (0.84, 0.31), (0.825, 0.345), (0.855, 0.40), (0.885, 0.445), (0.875, 0.47), (0.84, 0.48), (0.845, 0.50), (0.82, 0.53),
            (0.72, 0.60), (0.56, 0.60), (0.50, 0.50), (0.47, 0.38), (0.50, 0.25), (0.60, 0.16)]
    p.poly(head, 0.036, 0.06, 0.006)
    # The great beard
    beard = smooth([(0.835, 0.50), (0.85, 0.56), (0.83, 0.66), (0.79, 0.76), (0.71, 0.85), (0.64, 0.82), (0.60, 0.72), (0.60, 0.60), (0.66, 0.53), (0.75, 0.50)], 5)
    p.poly(beard, 0.03, 0.04, 0.016)
    for dx in (0.0, 0.035, 0.07, 0.105, 0.14, 0.175):
        p.curve([(0.81 - dx, 0.52), (0.83 - dx, 0.60), (0.79 - dx, 0.67), (0.76 - dx * 0.95, 0.76)], 0.008, 0.006)
    # Hair in tight curls, and a laurel wreath
    rng = np.random.default_rng(21)
    for i in range(30):
        a = math.radians(92 + i * 7.3 + rng.uniform(-2.5, 2.5))
        r = (0.178 if i % 2 else 0.222) + rng.uniform(-0.008, 0.008)
        p.ell(0.665 + r * math.cos(a), 0.37 - r * 0.98 * math.sin(a), 0.03, 0.022, 0.012, 0.014, 0.026, deg=float(rng.uniform(0, 180)))
    for i in range(8):
        a = math.radians(96 + i * 10)
        p.curve([(0.665 + 0.15 * math.cos(a), 0.37 - 0.14 * math.sin(a)), (0.665 + 0.10 * math.cos(a + 0.2), 0.37 - 0.10 * math.sin(a + 0.2)), (0.665 + 0.05 * math.cos(a + 0.5), 0.40 - 0.05 * math.sin(a + 0.5))], 0.005, 0.005)
    for i in range(12):
        t = i / 11
        x, y = 0.52 + t * 0.285, 0.325 - 0.11 * math.sin(t * 2.4)
        for s in (-1, 1):
            p.ell(x + 0.008, y + s * 0.014, 0.03, 0.011, 0.01, 0.007, 0.038, deg=-18 + s * 26)
    # Blind eyes: the lid closed, the brow heavy
    p.curve([(0.765, 0.335), (0.795, 0.325), (0.825, 0.335)], 0.012, 0.009)
    p.curve([(0.77, 0.37), (0.795, 0.38), (0.82, 0.368)], 0.005, -0.006)
    p.curve([(0.835, 0.455), (0.80, 0.465), (0.775, 0.455)], 0.007, 0.008)
    # He sings
    for i in range(3):
        d = 0.055 + i * 0.045
        p.curve([(0.885 + d, 0.42), (0.90 + d, 0.47), (0.885 + d, 0.53)], 0.006, 0.007)
    # The lyre
    cx = 1.28
    p.ell(cx, 0.78, 0.125, 0.09, 0.032, 0.03, 0.006)
    for s in (-1, 1):
        p.curve([(cx + s * 0.08, 0.74), (cx + s * 0.17, 0.58), (cx + s * 0.135, 0.40), (cx + s * 0.09, 0.25), (cx + s * 0.13, 0.17)], 0.03, 0.03, 0.42)
        p.circ(cx + s * 0.135, 0.165, 0.022, 0.03, 0.01, 0.006)
    p.line([(cx - 0.165, 0.30), (cx + 0.165, 0.30)], 0.024, 0.03)
    for i in range(6):
        x = cx + (i - 2.5) * 0.034
        p.line([(x, 0.30), (x * 0.98 + cx * 0.02, 0.77)], 0.005, 0.012, 0.8)
    p.line([(cx - 0.085, 0.77), (cx + 0.085, 0.77)], 0.016, 0.014)


def p_shelves(p):
    p.poly(rect(0.09, 0.09, 1.56, 0.91), 0.02, 0.01, 0.004)
    rng = np.random.default_rng(5)
    cols, rows = 7, 3
    cw, ch = 1.47 / cols, 0.82 / rows
    for r in range(rows):
        for c in range(cols):
            x0, y0 = 0.09 + c * cw + 0.012, 0.09 + r * ch + 0.012
            x1, y1 = x0 + cw - 0.024, y0 + ch - 0.024
            arch = [(x0, y1), (x0, y0 + 0.05)] + [((x0 + x1) / 2 + (x1 - x0) / 2 * math.cos(a), y0 + 0.05 - 0.05 * math.sin(a)) for a in np.linspace(math.pi, 0, 12)] + [(x1, y0 + 0.05), (x1, y1)]
            p.cut(arch, 0.0, 0.01)
            if (r, c) == (1, 4):        # a gap: the one scroll that is not here
                p.line([((x0 + x1) / 2, y0 + 0.02), ((x0 + x1) / 2, y0 + 0.10)], 0.003, 0.006)
                p.poly(rect((x0 + x1) / 2 - 0.022, y0 + 0.10, (x0 + x1) / 2 + 0.022, y0 + 0.155), 0.008, 0.005, 0.004)
                continue
            n = 0
            for row in range(3):
                for k in range(3 - row):
                    if rng.random() < 0.12:
                        continue
                    sr = rng.uniform(0.024, 0.031)
                    x = x0 + 0.04 + row * 0.03 + k * 0.058
                    y = y1 - 0.034 - row * 0.05
                    p.circ(x, y, sr, 0.02, 0.008, 0.002)
                    p.circ(x, y, sr * 0.3, 0.006, 0.003, 0.018)
                    n += 1
            if n and rng.random() < 0.5:
                x = x0 + rng.uniform(0.04, 0.12)
                p.line([(x, y1 - 0.09), (x + 0.005, y1 - 0.135)], 0.0028, 0.004)
                p.poly(rect(x - 0.01, y1 - 0.145, x + 0.02, y1 - 0.125), 0.005, 0.004, 0.014)
    # The ladder, and the librarian on it
    p.line([(1.05, 0.905), (1.22, 0.10)], 0.012, 0.03, 0.42)
    p.line([(1.16, 0.905), (1.33, 0.10)], 0.012, 0.03, 0.42)
    for i in range(9):
        t = 0.06 + i * 0.106
        p.line([(1.05 + t * 0.17, 0.905 - t * 0.805), (1.16 + t * 0.17, 0.905 - t * 0.805)], 0.009, 0.03, 0.45)
    p.poly([(1.20, 0.33), (1.28, 0.33), (1.31, 0.53), (1.30, 0.70), (1.235, 0.71), (1.20, 0.56)], 0.022, 0.03, 0.03)
    p.poly([(1.24, 0.70), (1.29, 0.70), (1.27, 0.77), (1.22, 0.77)], 0.018, 0.012, 0.03)
    p.circ(1.245, 0.265, 0.056, 0.024, 0.02, 0.03)
    p.circ(1.302, 0.225, 0.031, 0.024, 0.012, 0.032)
    p.curve([(1.21, 0.37), (1.13, 0.37), (1.07, 0.42)], 0.024, 0.022, 0.42)
    p.ell(1.03, 0.425, 0.05, 0.016, 0.018, 0.008, 0.038, deg=8)


def p_fire(p):
    p.flames(0.09, 1.56, 0.80, 0.075, 10, 7, 0.018, 0.07)
    p.flames(0.10, 0.60, 0.80, 0.34, 4, 8, 0.024, 0.04, 0.01)
    p.flames(1.05, 1.55, 0.80, 0.30, 4, 9, 0.024, 0.04, 0.01)
    # The Library: pediment, entablature, six columns and three steps
    p.poly(rect(0.28, 0.815, 1.37, 0.88), 0.026, 0.008, 0.012)
    p.poly(rect(0.32, 0.775, 1.33, 0.82), 0.03, 0.008, 0.012)
    p.poly(rect(0.36, 0.735, 1.29, 0.78), 0.034, 0.008, 0.012)
    p.cut(rect(0.42, 0.45, 1.23, 0.735), 0.008, 0.01)
    for i in range(6):
        x = 0.46 + i * 0.145
        p.poly([(x - 0.036, 0.738), (x + 0.036, 0.738), (x + 0.028, 0.46), (x - 0.028, 0.46)], 0.03, 0.016, 0.012)
        p.poly(rect(x - 0.042, 0.45, x + 0.042, 0.475), 0.032, 0.006, 0.012)
        for dx in (-0.016, 0.0, 0.016):
            p.line([(x + dx, 0.48), (x + dx * 1.25, 0.73)], 0.0035, -0.0045)
    p.poly(rect(0.38, 0.385, 1.27, 0.45), 0.034, 0.008, 0.012)
    p.poly([(0.36, 0.385), (0.824, 0.205), (1.29, 0.385)], 0.034, 0.012, 0.012)
    p.cut([(0.47, 0.37), (0.824, 0.235), (1.18, 0.37)], 0.03, 0.008)
    p.ell(0.824, 0.325, 0.06, 0.028, 0.014, 0.01, 0.03)
    for i in range(11):
        x = 0.42 + i * 0.081
        p.line([(x, 0.395), (x, 0.44)], 0.012, -0.005)
    # Burning scrolls blown from the doors, and sparks
    rng = np.random.default_rng(11)
    for x, y, d in ((0.16, 0.50, 30), (1.47, 0.45, -24), (0.27, 0.27, -14), (1.38, 0.20, 18), (0.60, 0.15, 12), (1.08, 0.13, -20)):
        p.ell(x, y, 0.052, 0.015, 0.014, 0.007, 0.03, deg=d)
        for s in (-1, 1):
            a = math.radians(d)
            p.circ(x + s * 0.052 * math.cos(a), y + s * 0.052 * math.sin(a), 0.016, 0.012, 0.006, 0.032)
    for _ in range(26):
        p.circ(rng.uniform(0.12, 1.53), rng.uniform(0.09, 0.66), rng.uniform(0.004, 0.009), 0.012, 0.004, 0.02)


def p_flight(p):
    # The city burning behind her
    p.flames(0.08, 0.72, 0.905, 0.22, 6, 12, 0.012, 0.06)
    for x, top in ((0.18, 0.46), (0.31, 0.58), (0.44, 0.40)):
        p.poly(rect(x, top, x + 0.075, 0.905), 0.016, 0.014, 0.008)
        p.cut([(x - 0.01, top - 0.02), (x + 0.09, top - 0.02), (x + 0.09, top + 0.018), (x + 0.03, top + 0.04), (x - 0.01, top + 0.01)], 0.006, 0.004)
    p.sky(6, 6, 0.26)
    # Wind and speed
    for y, x0 in ((0.30, 0.56), (0.40, 0.48), (0.56, 0.46), (0.70, 0.36)):
        p.curve([(x0, y + 0.03), (x0 + 0.10, y - 0.01), (x0 + 0.20, y + 0.015), (x0 + 0.27, y)], 0.006, 0.008)
    # Ground, and the scrolls she had to leave
    p.line([(0.08, 0.915), (1.57, 0.915)], 0.012, 0.01)
    for x in (0.62, 1.32, 1.42):
        p.ell(x, 0.893, 0.05, 0.014, 0.014, 0.007, 0.012, deg=3)
    # Back leg, robe, front leg
    p.poly([(0.70, 0.74), (0.77, 0.79), (0.68, 0.84), (0.58, 0.885), (0.52, 0.91), (0.47, 0.895), (0.50, 0.855), (0.58, 0.815)], 0.026, 0.024, 0.01)
    p.poly([(1.03, 0.68), (1.09, 0.70), (1.17, 0.845), (1.235, 0.875), (1.245, 0.91), (1.12, 0.91), (1.03, 0.77)], 0.03, 0.024, 0.01)
    robe = smooth([(0.84, 0.54), (0.98, 0.54), (1.07, 0.68), (1.115, 0.79), (1.04, 0.775), (0.95, 0.76), (0.87, 0.73), (0.76, 0.82), (0.64, 0.86), (0.52, 0.76), (0.60, 0.70), (0.72, 0.62)], 5)
    p.poly(robe, 0.03, 0.05, 0.012)
    for pts in ([(0.92, 0.56), (0.96, 0.66), (1.04, 0.76)], [(0.87, 0.57), (0.84, 0.64), (0.84, 0.72)], [(0.82, 0.58), (0.74, 0.66), (0.66, 0.82)], [(0.78, 0.60), (0.67, 0.68), (0.56, 0.76)]):
        p.curve(pts, 0.007, -0.007)
    # Body and the arm flung back
    p.poly([(0.86, 0.34), (0.895, 0.375), (0.79, 0.50), (0.71, 0.475), (0.695, 0.44), (0.77, 0.435)], 0.026, 0.024, 0.014)
    p.poly(smooth([(0.865, 0.315), (0.975, 0.315), (1.005, 0.44), (0.985, 0.56), (0.83, 0.575), (0.815, 0.44)], 5), 0.03, 0.05, 0.016)
    p.poly([(0.885, 0.28), (0.945, 0.285), (0.94, 0.335), (0.875, 0.335)], 0.03, 0.02, 0.014)
    # Head, bun, pencil, spectacles
    p.circ(0.845, 0.145, 0.05, 0.03, 0.022, 0.016)
    p.line([(0.79, 0.105), (0.90, 0.135)], 0.008, 0.016)
    p.circ(0.925, 0.215, 0.083, 0.03, 0.03, 0.016)
    p.poly([(0.998, 0.20), (1.03, 0.25), (0.997, 0.262)], 0.018, 0.012, 0.02)
    p.curve([(0.86, 0.17), (0.91, 0.135), (0.985, 0.16)], 0.016, 0.01)
    ring = [(0.968 + 0.03 * math.cos(a), 0.218 + 0.028 * math.sin(a)) for a in np.linspace(0, math.tau, 24)]
    p.line(ring, 0.0065, 0.011)
    p.line([(0.938, 0.215), (0.87, 0.205)], 0.0055, 0.011)
    p.curve([(0.965, 0.262), (0.985, 0.272), (1.002, 0.262)], 0.005, -0.006)
    # The arm and the Book held to her chest
    p.poly([(1.0, 0.36), (1.155, 0.335), (1.175, 0.525), (1.02, 0.55)], 0.022, 0.014, 0.032)
    p.line([(1.02, 0.378), (1.145, 0.357), (1.16, 0.51), (1.035, 0.53), (1.02, 0.378)], 0.006, -0.005)
    p.circ(1.09, 0.445, 0.025, 0.008, 0.008, 0.05)
    p.poly([(0.92, 0.34), (0.99, 0.33), (1.05, 0.47), (1.13, 0.47), (1.135, 0.515), (1.03, 0.53), (0.96, 0.45)], 0.022, 0.022, 0.05)


def p_book(p):
    # A glory of rays
    cx, cy = A / 2, 0.53
    for i in range(33):
        a = math.radians(-22 + i * (224 / 32))
        c, s = math.cos(a), math.sin(a)
        long_ray = i % 2 == 0
        r0x, r0y = 0.46, 0.24
        r1x, r1y = (0.70, 0.44) if long_ray else (0.60, 0.37)
        wid = 0.042 if long_ray else 0.03
        px, py = cx + c * r0x, cy - s * r0y
        p.poly([(px - s * wid, py - c * wid * 0.6), (cx + c * r1x, cy - s * r1y), (px + s * wid, py + c * wid * 0.6)], 0.014 if long_ray else 0.011, 0.014)
    # Lectern
    p.poly(rect(0.76, 0.76, 0.888, 0.88), 0.024, 0.02)
    p.poly(rect(0.64, 0.87, 1.01, 0.915), 0.028, 0.01)
    p.poly([(0.50, 0.70), (1.15, 0.70), (1.03, 0.79), (0.62, 0.79)], 0.028, 0.012, 0.006)
    for dx in (-0.028, 0.0, 0.028):
        p.line([(0.824 + dx, 0.80), (0.824 + dx, 0.87)], 0.004, -0.005)
    # The open book
    for s in (-1, 1):
        page = smooth([(cx, 0.73), (cx + s * 0.11, 0.685), (cx + s * 0.27, 0.70), (cx + s * 0.43, 0.725)], 6) + smooth([(cx + s * 0.43, 0.725), (cx + s * 0.44, 0.45), (cx + s * 0.45, 0.325)], 4) + \
            smooth([(cx + s * 0.45, 0.325), (cx + s * 0.28, 0.285), (cx + s * 0.11, 0.30), (cx, 0.38)], 6)
        p.poly(page, 0.03, 0.05, 0.012)
        for i in range(8):
            y = 0.385 + i * 0.041
            p.curve([(cx + s * 0.07, y + 0.03), (cx + s * 0.16, y - 0.006), (cx + s * 0.28, y - 0.004), (cx + s * 0.39, y + 0.012)], 0.0055, -0.0055)
        for i in range(3):
            p.curve([(cx + s * (0.445 + i * 0.008), 0.33 + i * 0.012), (cx + s * (0.435 + i * 0.008), 0.53), (cx + s * (0.425 + i * 0.008), 0.735 + i * 0.006)], 0.0035, -0.004)
    p.curve([(cx, 0.38), (cx + 0.006, 0.55), (cx, 0.73)], 0.008, -0.012)
    p.curve([(cx + 0.012, 0.72), (cx + 0.02, 0.80), (cx + 0.003, 0.865)], 0.016, 0.012)
    # NE TANGITO: do not touch
    p.text("NE", 0.36, 0.875, 76, 0.012, spacing=8)
    p.text("TANGITO", 1.28, 0.875, 76, 0.012, spacing=8)


def p_stamp(p):
    card = turned(rect(0.20, 0.11, 1.46, 0.90), 0.82, 0.5, -1.5)
    p.poly(card, 0.018, 0.008, 0.004)
    hole = [(0.824 + 0.03 * math.cos(a), 0.165 + 0.03 * math.sin(a)) for a in np.linspace(0, math.tau, 26)]
    p.cut(hole, 0.002, 0.008)
    p.text("BIBLIOTHECA ALEXANDRINA", 0.824, 0.235, 62, 0.006, deg=-1.5, spacing=5)
    for i in range(7):
        y = 0.30 + i * 0.086
        p.line(turned([(0.26, y), (1.40, y)], 0.82, 0.5, -1.5), 0.0045, -0.005)
    p.line(turned([(0.60, 0.29), (0.60, 0.88)], 0.82, 0.5, -1.5), 0.0045, -0.005)
    rng = np.random.default_rng(14)
    # Older loans, pencilled in, each returned on time
    for i in range(3):
        y = 0.345 + i * 0.086
        x = 0.30
        for _ in range(3):
            w = rng.uniform(0.05, 0.08)
            p.curve([(x, y), (x + w * 0.3, y - 0.012), (x + w * 0.6, y + 0.01), (x + w, y)], 0.005, 0.006)
            x += w + 0.018
        p.curve([(0.66, y), (0.74, y - 0.012), (0.82, y + 0.008), (0.92 + i * 0.08, y)], 0.005, 0.006)
    # The stamp, pressed on crooked and very hard
    c = (0.84, 0.60)
    p.line(turned([(0.32, 0.385), (1.36, 0.385), (1.36, 0.815), (0.32, 0.815), (0.32, 0.385)], c[0], c[1], -8), 0.016, 0.014, 0.4)
    p.line(turned([(0.345, 0.41), (1.335, 0.41), (1.335, 0.79), (0.345, 0.79), (0.345, 0.41)], c[0], c[1], -8), 0.006, 0.01, 0.4)
    p.text("OVERDVE", c[0] - 0.02, 0.535, 212, 0.016, deg=-8, spacing=6)
    p.text("48 B.C.", c[0] + 0.012, 0.70, 124, 0.013, deg=-8, spacing=4)


PANELS = (p_horse, p_troy, p_homer, p_shelves, p_fire, p_flight, p_book, p_stamp)


def build(relief_class, out):
    """Two atlases: normal, and wide occlusion, tight occlusion and height in RGB. Cells are 1024 by
    512, two across and four down. Returns each panel's cell in atlas pixels."""
    S = 2048
    normal = np.full((S, S, 3), (128, 128, 255), dtype=np.uint8)
    ao = np.full((S, S, 3), 255, dtype=np.uint8)
    rects = []
    for i, draw in enumerate(PANELS):
        r = relief_class(W, H_, M * A)
        p = Panel(r)
        draw(p)
        p.finish(i + 1)
        x0, y0 = (i % 2) * 1024, (i // 2) * 512
        rc = [x0, y0, x0 + 1024, y0 + 512]
        n, w, t, h = r.bake((1024, 512), 2.6, (0.0, 0.052))
        normal[y0:y0 + 512, x0:x0 + 1024] = n
        ao[y0:y0 + 512, x0:x0 + 1024, 0] = w
        ao[y0:y0 + 512, x0:x0 + 1024, 1] = t
        ao[y0:y0 + 512, x0:x0 + 1024, 2] = h
        rects.append(rc)
        print("door panel", i, draw.__name__, flush=True)
    Image.fromarray(normal).save(out / "ext_door_normal.png", optimize=True)
    Image.fromarray(ao).save(out / "ext_door_ao.png", optimize=True)
    L = np.array([-0.45, 0.55, 0.70])
    n = normal / 127.5 - 1
    shade = np.clip(n @ L, 0, 1) ** 1.2
    Image.fromarray(np.clip(shade * ao[..., 0] / 255 * ao[..., 1] / 255 * 255, 0, 255).astype(np.uint8)).save(out / "door_preview.png")
    return rects
