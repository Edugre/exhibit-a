"""The floor wear decals (asset plan P6.1): textures with alpha, projected by Decal nodes onto the floors.
  floor_wear.png        a soft oval of dulled, greyed floor where visitors stop in front of an exhibit
  threshold_scuff.png   a band of grime and black heel marks across a doorway
usage: python make_wear_art.py <out dir>     (writes both, and their import settings, there)"""
import pathlib
import sys
import numpy as np
from PIL import Image, ImageDraw
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
TOOLS = pathlib.Path(__file__).parent
RES = "res://assets/interior/wear/"


def save(name, rgb, alpha):
    rgba = np.dstack([np.clip(rgb, 0, 1), np.clip(alpha, 0, 1)])
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(OUT / name, optimize=True)


# --- A worn patch in front of an exhibit -------------------------------------------
rng = np.random.default_rng(6101)
n = 512
yy, xx = (np.mgrid[0:n, 0:n] + 0.5) / n * 2 - 1
oval = np.clip(1 - np.sqrt((xx / 0.95) ** 2 + (yy / 0.8) ** 2), 0, 1) ** 0.9
blotch = 0.65 + 0.35 * A.blur_noise(rng, n, n, 24)
grit = 0.85 + 0.15 * A.blur_noise(rng, n, n, 1.5)
alpha = oval * blotch * grit * 0.55
dull = np.array([0.42, 0.37, 0.31], np.float32)  # varnish worn off: a grey-brown, flatter than the floor
save("floor_wear.png", dull * (0.95 + 0.1 * A.blur_noise(rng, n, n, 3))[..., None] * np.ones((n, n, 1)), alpha)

# --- A scuffed doorway threshold ---------------------------------------------------
rng = np.random.default_rng(6102)
w, h = 1024, 256
yy, xx = (np.mgrid[0:h, 0:w] + 0.5)
v = yy / h * 2 - 1
band = np.clip(1 - np.abs(v) ** 2.2, 0, 1) * np.clip(1 - (np.abs(xx / w * 2 - 1) / 0.98) ** 6, 0, 1)
grime = band * (0.5 + 0.5 * A.blur_noise(rng, w, h, 18)) * 0.45
rgb = np.ones((h, w, 3), np.float32) * np.array([0.16, 0.13, 0.10], np.float32)
marks = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(marks)
for _ in range(70):  # heel marks: short dark arcs, mostly along the way through (v)
    cx, cy = rng.uniform(40, w - 40), rng.uniform(30, h - 30)
    length, ang = rng.uniform(14, 46), rng.normal(np.pi / 2, 0.5)
    dx, dy = np.cos(ang) * length / 2, np.sin(ang) * length / 2
    d.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=int(rng.uniform(90, 200)), width=int(rng.integers(2, 5)))
marks = np.asarray(marks, np.float32) / 255 * band
alpha = np.maximum(grime, marks * 0.8)
rgb = rgb * (1 - marks[..., None] * 0.7)
save("threshold_scuff.png", rgb, alpha)

IMPORT = (TOOLS / "make_kit.py").read_text(encoding="utf8").split('IMPORT = """')[1].split('"""')[0]
for png in sorted(OUT.glob("*.png")):
    target = png.with_suffix(".png.import")
    if not target.exists():
        target.write_text(IMPORT.format(path=RES + png.name, normal=0, hq="false"), encoding="utf8", newline="\n")
print("wrote the wear decals to", OUT)
