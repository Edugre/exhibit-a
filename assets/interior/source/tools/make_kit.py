"""The interior kit (asset item K0): the surfaces every room is built from. Draws the parquet, marble
and plaster textures in numpy, then writes their import settings and the materials that use them.
The shaders that lay them on in world space are int_surface.gdshader and int_cornice.gdshader.
usage: python make_kit.py <assets/interior/kit folder>"""
import pathlib
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

sys.dont_write_bytecode = True    # no __pycache__ next to the scripts
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import int_dims as D  # noqa: E402

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/kit/"


def periodic_noise(rng, size, sigma):
    """Smooth noise that wraps at the edges, scaled to 0..1."""
    n = gaussian_filter(rng.random(size), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min())


def normal_from_height(h, metres_per_px):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * metres_per_px)
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * metres_per_px)
    ln = np.sqrt(dx * dx + dy * dy + 1)
    return np.stack([-dx / ln, dy / ln, 1 / ln], -1)


def down(a, n):
    """Draw big, save small: box-filter a float image down to n x n."""
    img = Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))
    return img.resize((n, n), Image.BOX)


# --- Parquet: oak blocks of four slats, laid in a checkerboard -------------------------------------
def parquet(n=1024, ss=2):
    rng = np.random.default_rng(4101)
    s = n * ss
    px = D.PARQUET_TILE / s
    block = s // 4
    slat = block // 4
    y, x = np.mgrid[0:s, 0:s]
    bx, by = x // block, y // block
    across_h = y % block            # slats run along x in "horizontal" blocks
    across_v = x % block
    horizontal = (bx + by) % 2 == 0
    across = np.where(horizontal, across_h, across_v)
    along = np.where(horizontal, x % block, y % block)
    slat_i = across // slat
    # One tone per slat: honey oak, some a touch redder, some paler, a few replaced over the years
    tones = rng.normal(0.0, 1.0, (4, 4, 4, 2))
    t = tones[by % 4, bx % 4, slat_i]
    base = np.array([0.46, 0.37, 0.28])
    colour = base[None, None, :] * (1 + 0.11 * t[..., :1]) + np.stack([0.02, 0.0, -0.014])[None, None, :] * t[..., 1:2]
    # No slat lies perfectly flat: each sits a hair higher or lower, tips a little, and cups in the middle
    lift = rng.normal(0.0, 1.0, (4, 4, 4, 2))[by % 4, bx % 4, slat_i]
    along_u = along / (block - 1) * 2 - 1
    across_u = (across % slat) / (slat - 1) * 2 - 1
    lie = lift[..., 0] * 0.00022 + lift[..., 1] * along_u * 0.00035 - (1 - across_u * across_u) * 0.00018
    # Grain runs along each slat, with the odd darker figure line
    grain_h = periodic_noise(rng, (s, s), (0.8 * ss, 28 * ss))
    grain_v = periodic_noise(rng, (s, s), (28 * ss, 0.8 * ss))
    grain = np.where(horizontal, grain_h, grain_v)
    figure_h = periodic_noise(rng, (s, s), (2.5 * ss, 60 * ss))
    figure_v = periodic_noise(rng, (s, s), (60 * ss, 2.5 * ss))
    figure = np.where(horizontal, figure_h, figure_v)
    colour = colour * (0.86 + 0.28 * grain[..., None]) * (1 - 0.12 * np.clip((figure[..., None] - 0.62) * 4, 0, 1))
    # Hairline gaps between slats and between blocks
    d_side = np.minimum(across % slat, slat - 1 - across % slat)
    d_end = np.minimum(along, block - 1 - along)
    gap = np.minimum(d_side, d_end).astype(float)
    grime = periodic_noise(rng, (s, s), 6 * ss)
    colour *= (1 - (0.45 + 0.35 * grime) * np.exp(-(gap / (1.6 * ss)) ** 2))[..., None]
    # Height: each slat rolls off at its edges, plus the way it lies and a little grain texture
    bevel = np.clip(gap / (3.0 * ss), 0, 1)
    height = (bevel * bevel * (3 - 2 * bevel)) * 0.0007 + grain * 0.00016 + lie * bevel
    height = gaussian_filter(height, 0.6 * ss, mode="wrap")
    nrm = normal_from_height(height, px)
    down(colour, n).save(OUT / "int_parquet_albedo.png", optimize=True)
    down(nrm * 0.5 + 0.5, n).save(OUT / "int_parquet_normal.png", optimize=True)


# --- Marble: cream stone with grey veins, for floors (and, darkened, for skirting) -----------------
def turbulence(rng, n, sigmas):
    """Several sizes of wrapped noise, folded at their middle, so they kink like stone does."""
    total, weight = 0.0, 0.0
    for i, s in enumerate(sigmas):
        w = 0.55 ** i
        total = total + w * np.abs(periodic_noise(rng, (n, n), s) * 2 - 1)
        weight += w
    return total / weight


def marble(n=1024):
    rng = np.random.default_rng(4102)
    y, x = np.mgrid[0:n, 0:n] / n
    # Veins: lines that run one way across the slab, bent by turbulence. Whole numbers of stripes keep it tiling.
    turb = turbulence(rng, n, (70, 34, 16, 7, 3))
    turb2 = turbulence(rng, n, (50, 22, 9, 4))
    width = 0.05 + 0.13 * periodic_noise(rng, (n, n), 60)
    wave = np.sin((x * 3 + y * 1) * np.pi + turb * 3.8)
    main = np.exp(-(wave / width) ** 2)
    halo = np.exp(-(wave / (width * 4)) ** 2)     # the stain that spreads either side of a vein
    hair = np.exp(-(np.sin((x * 2 - y * 4) * np.pi + turb2 * 6.0) / 0.035) ** 2)
    # Ghost veins: broad, soft and faint, deeper in the stone than the sharp ones
    ghost = np.exp(-(np.sin((x * 1 - y * 2) * np.pi + turb2 * 4.0) / 0.3) ** 2)
    # Clouds of warmer and greyer stone, at two sizes, so no patch looks freshly cut
    cloud = periodic_noise(rng, (n, n), 110)
    warm = periodic_noise(rng, (n, n), 45)
    grain = periodic_noise(rng, (n, n), 1.2)
    base = np.array([0.90, 0.88, 0.84]) * (0.92 + 0.12 * cloud[..., None])
    base = base * (1 + (warm[..., None] - 0.5) * np.array([0.10, 0.04, -0.06])) * (0.97 + 0.06 * grain[..., None])
    vein_colour = np.array([0.58, 0.58, 0.61])
    v = np.clip(main * 0.75 + halo * 0.16 + hair * 0.26 + ghost * 0.12, 0, 1)
    colour = base * (1 - v[..., None]) + vein_colour * v[..., None]
    down(colour, n).save(OUT / "int_marble.png", optimize=True)


# --- Wear: dirt, scratches and dull patches, laid over every surface at its own scale ---------------
def wear(n=1024, ss=2):
    """R: dirt and grime blotches. G: scratches and scuffs. B: patches worn dull. Covers WEAR_TILE metres."""
    from PIL import ImageDraw
    rng = np.random.default_rng(4104)
    s = n * ss
    dirt = periodic_noise(rng, (s, s), 70 * ss) * 0.55 + periodic_noise(rng, (s, s), 18 * ss) * 0.3 + periodic_noise(rng, (s, s), 4 * ss) * 0.15
    dirt = np.clip((dirt - 0.42) / 0.4, 0, 1)
    marks = Image.new("L", (s, s), 0)
    pen = ImageDraw.Draw(marks)
    for _ in range(1400):
        x0, y0 = rng.random(2) * s
        length = rng.choice([rng.uniform(6, 40), rng.uniform(40, 160)], p=[0.85, 0.15]) * ss
        angle = rng.uniform(0, np.pi) if rng.random() < 0.6 else rng.normal(0.4, 0.25)
        shade = int(rng.uniform(60, 255))
        x1, y1 = x0 + np.cos(angle) * length, y0 + np.sin(angle) * length
        for ox in (-s, 0, s):           # drawn three times across each edge, so it wraps
            for oy in (-s, 0, s):
                pen.line([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy)], fill=shade, width=1)
    scratches = np.asarray(marks, dtype=float) / 255
    dull = np.clip((periodic_noise(rng, (s, s), 120 * ss) - 0.4) / 0.4, 0, 1) * 0.8 + periodic_noise(rng, (s, s), 3 * ss) * 0.2
    down(np.stack([dirt, scratches, dull], -1), n).save(OUT / "int_wear.png", optimize=True)


# --- Plaster: hand-trowelled and unevenly painted ---------------------------------------------------
def plaster(n=512, ss=2):
    rng = np.random.default_rng(4103)
    s = n * ss
    px = D.PLASTER_TILE / s
    mottle = periodic_noise(rng, (s, s), 34 * ss)
    patches = periodic_noise(rng, (s, s), 10 * ss)
    stipple = periodic_noise(rng, (s, s), 0.9 * ss)
    # Trowel strokes: sweeps in two directions, each showing only where the plasterer's hand went
    sweep_a = periodic_noise(rng, (s, s), (3.0 * ss, 16.0 * ss))
    sweep_b = periodic_noise(rng, (s, s), (16.0 * ss, 3.0 * ss))
    hand = periodic_noise(rng, (s, s), 40 * ss)
    trowel = np.where(hand > 0.5, sweep_a, sweep_b)
    ridge = np.abs(trowel - np.roll(trowel, 2 * ss, 0)) + np.abs(trowel - np.roll(trowel, 2 * ss, 1))
    # No cracks drawn here: the plaster repeats every few metres, so any crack would repeat with it
    grey = 0.85 + (mottle - 0.5) * 0.11 + (patches - 0.5) * 0.06 + (stipple - 0.5) * 0.05 - ridge * 0.25
    height = stipple * 0.0007 + trowel * 0.0009
    nrm = normal_from_height(gaussian_filter(height, 0.5 * ss, mode="wrap"), px)
    down(np.repeat(grey[..., None], 3, -1), n).save(OUT / "int_plaster.png", optimize=True)
    down(nrm * 0.5 + 0.5, n).save(OUT / "int_plaster_normal.png", optimize=True)


# --- Import settings: compressed, with mipmaps, and normal maps marked as such ----------------------
IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="{path}"

[params]

compress/mode=2
compress/high_quality={hq}
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map={normal}
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=false
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=0
"""


def write_imports():
    for png in sorted(OUT.glob("*.png")):
        target = png.with_suffix(".png.import")
        if target.exists():
            continue    # keep the uid Godot gave it, so materials and scenes keep pointing at it
        normal = 1 if png.stem.endswith("_normal") else 0
        target.write_text(IMPORT.format(path=RES + png.name, normal=normal, hq="true" if normal else "false"), encoding="utf8", newline="\n")


# --- Materials -----------------------------------------------------------------------------------
def colour(c):
    return "Color(%.3f, %.3f, %.3f, 1)" % c


def material(name, shader, textures, params):
    lines = ['[gd_resource type="ShaderMaterial" format=3]', ""]
    lines.append('[ext_resource type="Shader" path="%s%s" id="s"]' % (RES, shader))
    for i, (_, path) in enumerate(textures):
        lines.append('[ext_resource type="Texture2D" path="%s" id="t%d"]' % (path, i))
    lines += ["", "[resource]", 'shader = ExtResource("s")']
    for i, (slot, _) in enumerate(textures):
        lines.append('shader_parameter/%s = ExtResource("t%d")' % (slot, i))
    for key, value in params.items():
        lines.append("shader_parameter/%s = %s" % (key, value))
    (OUT / (name + ".tres")).write_text("\n".join(lines) + "\n", encoding="utf8", newline="\n")


def write_materials():
    wear_map = ("wear_map", RES + "int_wear.png")
    plaster_maps = [("albedo_map", RES + "int_plaster.png"), ("normal_map", RES + "int_plaster_normal.png"), wear_map]
    material("int_floor_parquet", "int_surface.gdshader",
             [("albedo_map", RES + "int_parquet_albedo.png"), ("normal_map", RES + "int_parquet_normal.png"), wear_map],
             {"metres_per_tile": D.PARQUET_TILE, "roughness": 0.55, "roughness_from_dark": 0.3, "specular": 0.42,
              "wear_tile": D.WEAR_TILE, "dirt": 0.2, "scratches": 0.4, "dullness": 0.35})
    material("int_floor_marble", "int_surface.gdshader", [("albedo_map", RES + "int_marble.png"), wear_map],
             {"use_normal_map": "false", "metres_per_tile": D.MARBLE_TILE, "roughness": 0.28, "specular": 0.5,
              "tile_size": D.MARBLE_SLAB, "tile_tone": 0.06,
              "wear_tile": D.WEAR_TILE, "dirt": 0.14, "scratches": 0.3, "dullness": 0.45})
    for key, paint in D.WALL_PAINT.items():
        name = "int_wall_paint" if key == "cream" else "int_wall_paint_" + key
        material(name, "int_surface.gdshader", plaster_maps,
                 {"tint": colour(paint), "metres_per_tile": D.PLASTER_TILE, "roughness": 0.88, "specular": 0.3,
                  "normal_strength": 1.0, "corner_shade": 0.28, "wall_height": D.WALL_H,
                  "wear_tile": D.WEAR_TILE, "dirt": 0.12, "scratches": -0.5, "scuff_height": D.SCUFF_H})
    material("int_ceiling", "int_surface.gdshader", plaster_maps,
             {"tint": colour(D.CEILING_TINT), "metres_per_tile": D.PLASTER_TILE, "roughness": 0.9, "specular": 0.25,
              "normal_strength": 0.7, "wear_tile": D.WEAR_TILE, "dirt": 0.1})
    material("int_skirting", "int_surface.gdshader", [("albedo_map", RES + "int_marble.png"), wear_map],
             {"use_normal_map": "false", "tint": colour(D.SKIRTING_TINT), "metres_per_tile": 1.0, "roughness": 0.3,
              "specular": 0.5, "wear_tile": D.WEAR_TILE, "dirt": 0.1, "scratches": 0.6, "dullness": 0.4})
    material("int_moulding", "int_cornice.gdshader",
             [("plaster_map", RES + "int_plaster.png"),
              ("carved_normal", "res://assets/exterior/ext_trim_normal.png"),
              ("carved_ao", "res://assets/exterior/ext_trim_ao.png")],
             {"tint": colour(D.MOULDING_TINT), "band_bottom": D.CORNICE_Y0, "band_top": D.CORNICE_Y1,
              "metres_per_repeat": D.CORNICE_H / D.CORNICE_ROWS, "v_range": D.CORNICE_ROWS, "recess_shade": 0.35})


parquet()
marble()
plaster()
wear()
write_imports()
write_materials()
print("interior kit written to", OUT)
