"""Background Blender job (stretch goal: scoring): six small valuables to pocket, and the crowbar that opens
the display cases. Run loot_art.py first.
usage: blender -b --factory-startup --python loot_build.py -- <out dir>
Each sits with its origin at the bottom of its middle, on the surface it lies on; front faces -Y (Godot +Z).
They're drawn a little larger than life, so they read from a few metres away at night."""
import importlib
import math
import pathlib
import sys
from mathutils import Matrix

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import int_mesh as M
importlib.reload(M)

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1]).resolve()
M.reset()
atlas = M.Atlas(HERE / "loot_atlas.json", OUT / "int_loot.png")
METAL = M.material("metal", atlas.image, metallic=1.0, roughness=0.22)
STONE = M.material("stone", atlas.image, roughness=0.15)
SOFT = M.material("soft", atlas.image, roughness=0.85)
MATS = [METAL, STONE, SOFT]
UV = atlas.uv


def ring_points(radius, z, n=20, tilt=0.0):
    return [(radius * math.cos(a), radius * math.sin(a) * math.cos(tilt), z + radius * math.sin(a) * math.sin(tilt))
            for a in (i / n * math.tau for i in range(n + 1))]


def gold_ring():
    """The Ring of Gyges, standing on its band, with a ruby."""
    b = M.Builder()
    r = 0.045
    pts = [(r * math.cos(a), 0.0, r + r * math.sin(a)) for a in (i / 22 * math.tau for i in range(23))]
    b.tube(pts, 0.008, 0, UV("gold"), segments=8)
    b.box(0.03, 0.022, 0.016, 0, UV("gold"), M.at(z=2 * r + 0.004), bevel=0.003)
    b.sphere(0.014, 1, UV("ruby"), M.at(z=2 * r + 0.016), squash=0.8, segments=10, rings=6)
    return b.object("GoldRing", MATS)


def scarab():
    """A lapis scarab on a little gold plinth."""
    b = M.Builder()
    b.cylinder(0.06, 0.065, 0.02, 0, UV("gold"), M.at(z=0.01), segments=16)
    b.sphere(0.055, 1, UV("lapis"), M.at(z=0.02, y=0.01) @ Matrix.Diagonal((0.85, 1.15, 0.6, 1.0)), segments=14, rings=8)
    b.sphere(0.024, 1, UV("lapis"), M.at(y=-0.058, z=0.035), squash=0.7, segments=10, rings=6)
    b.box(0.004, 0.11, 0.006, 0, UV("gold"), M.at(y=0.01, z=0.054))       # the line between its wing cases
    for side in (-1, 1):
        for k, y in enumerate((-0.03, 0.0, 0.03)):
            b.tube([(side * 0.04, y, 0.03), (side * 0.07, y + (k - 1) * 0.01, 0.022)], 0.004, 0, UV("gold"), segments=5)
    return b.object("Scarab", MATS)


def laurel():
    """A gilt laurel wreath, lying flat."""
    b = M.Builder()
    r = 0.11
    b.tube(ring_points(r, 0.008, 24), 0.005, 0, UV("gold"), segments=6)
    for k in range(26):
        a = k / 26 * math.tau
        if abs(a - math.pi * 1.5) < 0.35:
            continue  # the gap at the back where it ties
        for side in (-1, 1):
            out = r + side * 0.018
            leaf = M.at(x=out * math.cos(a), y=out * math.sin(a), z=0.01, rz=math.degrees(a) + 90 + side * 30, rx=side * 15)
            b.sphere(0.02, 0, UV("laurel"), leaf @ Matrix.Diagonal((1.0, 0.38, 0.12, 1.0)), segments=6, rings=3)
    return b.object("Laurel", MATS)


def purse():
    """Charon's purse: a leather pouch tied at the neck, with a few coins spilling out."""
    b = M.Builder()
    b.sphere(0.075, 2, UV("leather"), M.at(z=0.065) @ Matrix.Diagonal((1.0, 0.95, 0.85, 1.0)), segments=14, rings=8)
    b.cylinder(0.03, 0.045, 0.05, 2, UV("leather"), M.at(z=0.145), segments=12)
    b.cylinder(0.034, 0.034, 0.012, 2, UV("dark"), M.at(z=0.135), segments=12)
    for x, y, tilt in ((0.09, -0.03, 8), (0.12, 0.02, -5), (0.06, -0.08, 12)):
        b.cylinder(0.022, 0.022, 0.005, 0, UV("gold"), M.at(x=x, y=y, z=0.004, rx=tilt), segments=14)
    return b.object("Purse", MATS)


def owl():
    """The Owl of Athena: a silver statuette on a bronze base."""
    b = M.Builder()
    b.cylinder(0.06, 0.065, 0.03, 0, UV("bronze"), M.at(z=0.015), segments=16)
    b.sphere(0.055, 0, UV("silver"), M.at(z=0.09) @ Matrix.Diagonal((0.9, 0.85, 1.15, 1.0)), segments=14, rings=8)
    b.sphere(0.045, 0, UV("silver"), M.at(z=0.17), segments=14, rings=8)
    for side in (-1, 1):
        b.sphere(0.014, 1, UV("emerald"), M.at(x=side * 0.018, y=-0.04, z=0.18), segments=8, rings=5)
        b.cylinder(0.012, 0.0, 0.03, 0, UV("silver"), M.at(x=side * 0.028, z=0.215, ry=side * 18), segments=6)
    b.cylinder(0.008, 0.0, 0.02, 0, UV("gold"), M.at(y=-0.048, z=0.165, rx=100), segments=6)  # beak
    return b.object("Owl", MATS)


def dagger():
    """A jewelled dagger lying on its side."""
    b = M.Builder()
    flat = Matrix.Diagonal((1.0, 0.22, 1.0, 1.0))
    b.cylinder(0.025, 0.002, 0.2, 0, UV("silver"), M.at(x=0.1, z=0.008, ry=90) @ flat, segments=4)   # blade
    b.box(0.018, 0.08, 0.016, 0, UV("gold"), M.at(z=0.008), bevel=0.004)                               # guard
    b.cylinder(0.011, 0.011, 0.08, 2, UV("leather"), M.at(x=-0.05, z=0.011, ry=90), segments=10)       # grip
    b.sphere(0.018, 0, UV("gold"), M.at(x=-0.095, z=0.012), segments=10, rings=6)                      # pommel
    for y in (-0.028, 0.028):
        b.sphere(0.008, 1, UV("ruby"), M.at(y=y, z=0.017), segments=8, rings=5)
    return b.object("Dagger", MATS)


def crowbar():
    """A red crowbar: a straight hex bar with a curled claw at one end and a flat chisel at the other.
    Lies along X; held, the claw points forward."""
    b = M.Builder()
    length = 0.62
    pts = [(-length / 2, 0.0, 0.0), (length / 2 - 0.06, 0.0, 0.0)]
    for k in range(1, 8):                                       # the claw curls up and back
        a = k / 7 * math.pi * 0.95
        pts.append((length / 2 - 0.06 + 0.05 * math.sin(a), 0.0, 0.05 - 0.05 * math.cos(a)))
    b.tube(pts, 0.012, 0, UV("iron"), segments=6)
    b.tube(pts[:2], 0.0125, 2, UV("paint"), segments=6)          # red paint on the shaft
    b.box(0.05, 0.03, 0.008, 0, UV("iron"), M.at(x=-length / 2 - 0.02, z=-0.004, ry=-12))   # chisel end
    b.box(0.02, 0.016, 0.03, 0, UV("iron"), M.at(x=length / 2 - 0.06 + 0.05, z=0.1))       # the split claw tip
    return b.object("Crowbar", MATS)


for make, name in ((gold_ring, "gold_ring"), (scarab, "scarab"), (laurel, "laurel"), (purse, "purse"),
                   (owl, "owl"), (dagger, "dagger"), (crowbar, "crowbar")):
    obj = make()
    print(name, len(obj.data.polygons), "faces")
    M.export(obj, OUT / f"{name}.gltf")
