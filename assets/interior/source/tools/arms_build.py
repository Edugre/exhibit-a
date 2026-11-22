"""Background Blender job (asset plan P3.3): the Hall of Arms. Three suits of Greek bronze armour on
stands (Ajax, Patroclus, Odysseus), a rack of Myrmidon spears with one gone, and the Shield of Achilles in a
glass case. Run arms_art.py first.
usage: blender -b --factory-startup --python arms_build.py -- <out dir>
Every prop faces -Y here (+Z in Godot) with its origin on the floor, in the middle."""
import importlib
import math
import pathlib
import sys
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import int_dims as D
import int_mesh as M
importlib.reload(D)
importlib.reload(M)

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1]).resolve()
M.reset()
atlas = M.Atlas(HERE / "arms_atlas.json", OUT / "int_arms.png")
BRONZE = M.material("bronze", atlas.image, metallic=0.9, roughness=0.35)
WOOD = M.material("wood", atlas.image, roughness=0.55)
CLOTH = M.material("cloth", atlas.image, roughness=0.95)
GLASS = M.material("glass", atlas.image, roughness=0.05, alpha=0.22)
UV = atlas.uv
FRONT = Vector((0, -1, 0))
RIGHT = Vector((1, 0, 0))
UP = Vector((0, 0, 1))
B, W, C, G = 0, 1, 2, 3  # material slots
MATS = [BRONZE, WOOD, CLOTH, GLASS]

PLINTH = (0.62, 0.52, 0.18)
LABEL = (0.40, 0.10)


def label_plate(b, rect, place):
    """A brass plate with a printed label on its front."""
    faces = b.box(LABEL[0], 0.01, LABEL[1], B, UV(rect), place)
    rot = place.to_3x3()
    b.print_face(faces, rot @ FRONT, rot @ RIGHT, rot @ UP, UV(rect))


def painted_disc(b, radius, thick, slot, rect, place, segments=32):
    """A round shield: the rim and back in bronze, its face printed."""
    faces = b.cylinder(radius, radius, thick, slot, UV("bronze_dark"), place, segments=segments)
    rot = place.to_3x3()
    toward = rot @ Vector((0, 0, 1))
    u = rot @ Vector((1, 0, 0))
    b.print_face(faces, toward, u, toward.cross(u), UV(rect))
    return faces


def armour(name, crest, label, hoplon=None, spear=False):
    """A bronze panoply on a wooden stand: greaves, a linen skirt, a muscled cuirass, shoulder guards and
    a crested Corinthian helmet."""
    b = M.Builder()
    pw, pd, ph = PLINTH
    b.box(pw, pd, ph, W, UV("wood"), M.at(z=ph / 2), bevel=0.01)
    label_plate(b, label, M.at(y=-pd / 2 - 0.004, z=ph / 2))
    b.cylinder(0.025, 0.025, 1.4, W, UV("wood"), M.at(z=ph + 0.7))                 # the stand's pole
    for x in (-0.1, 0.1):                                                           # legs: an iron rod in each greave
        b.cylinder(0.014, 0.014, 0.66, B, UV("iron"), M.at(x=x, z=ph + 0.33))
        b.cylinder(0.05, 0.068, 0.42, B, UV("bronze"), M.at(x=x, y=-0.01, z=ph + 0.24), segments=14)
        b.sphere(0.05, B, UV("bronze"), M.at(x=x, y=-0.03, z=ph + 0.48), squash=0.8, segments=10, rings=6)
    waist, chest = 1.0, 1.42
    for k in range(12):                                                             # the linen skirt, in strips
        a = k / 12 * math.tau
        r = 0.175
        b.box(0.085, 0.02, 0.24, C, UV("linen" if k % 2 else "leather"),
              M.at(x=r * math.cos(a), y=r * math.sin(a) * 0.75, z=waist - 0.1, rz=math.degrees(a) + 90))
    flat = Matrix.Diagonal((1.0, 0.68, 1.0, 1.0))
    b.cylinder(0.19, 0.245, chest - waist, B, UV("bronze"), M.at(z=(waist + chest) / 2) @ flat, segments=20)
    b.cylinder(0.245, 0.12, 0.08, B, UV("bronze"), M.at(z=chest + 0.04) @ flat, segments=20)
    b.cylinder(0.2, 0.2, 0.03, B, UV("bronze_dark"), M.at(z=waist) @ flat, segments=20)  # the belt
    for x in (-0.09, 0.09):                                                         # the muscles on the chest
        b.sphere(0.1, B, UV("bronze"), M.at(x=x, y=-0.12, z=chest - 0.1) @ Matrix.Diagonal((1.0, 0.45, 0.7, 1.0)), segments=12, rings=7)
    for side in (-1, 1):                                                            # shoulder guards
        b.sphere(0.11, C, UV("leather"), M.at(x=side * 0.22, z=chest + 0.04) @ Matrix.Diagonal((1.0, 0.95, 0.45, 1.0)), segments=12, rings=6)
    b.cylinder(0.05, 0.05, 0.1, B, UV("iron"), M.at(z=chest + 0.12))                # neck
    hz = chest + 0.27
    b.sphere(0.135, B, UV("bronze"), M.at(z=hz) @ Matrix.Diagonal((0.95, 1.1, 1.15, 1.0)), segments=16, rings=10)
    for x in (-0.065, 0.065):                                                       # cheek guards and eye holes
        b.box(0.06, 0.03, 0.13, B, UV("bronze"), M.at(x=x, y=-0.125, z=hz - 0.1, rz=-x * 120))
        b.box(0.055, 0.012, 0.026, C, UV("crest_black"), M.at(x=x * 0.8, y=-0.146, z=hz - 0.005))
    b.box(0.024, 0.025, 0.1, B, UV("bronze"), M.at(y=-0.15, z=hz - 0.04))          # nose guard
    b.box(0.02, 0.16, 0.04, B, UV("bronze_dark"), M.at(z=hz + 0.165))              # crest holder
    for k in range(11):                                                             # the horsehair crest, front to back
        a = math.radians(-50 + k * 16)
        r = 0.2
        b.box(0.04, 0.075, 0.12, C, UV(crest), M.at(y=-r * math.sin(a) * -1, z=hz + r * math.cos(a), rx=-math.degrees(a)))
    if spear:                                                                       # a spear in the right hand
        x = 0.33
        b.cylinder(0.016, 0.016, 2.2, W, UV("wood"), M.at(x=x, y=-0.06, z=ph + 1.1))
        b.cylinder(0.034, 0.0, 0.22, B, UV("bronze"), M.at(x=x, y=-0.06, z=ph + 2.31), segments=8)
        b.cylinder(0.012, 0.012, 0.3, B, UV("iron"), M.at(x=(x + 0.12) / 2, y=-0.06, z=chest - 0.1, ry=90))  # the stand's arm
    if hoplon:                                                                      # a shield leaning on the plinth
        place = M.at(x=-0.45, y=-0.08, z=0.45, rx=80, rz=-28)
        painted_disc(b, 0.45, 0.04, B, hoplon, place)
    return b.object(name, MATS)


def spear_rack():
    """A wall rack for five spears, and four in it. Its back goes against the wall (+Y)."""
    b = M.Builder()
    w = 1.3
    b.box(w, 0.36, 0.14, W, UV("wood"), M.at(z=0.07), bevel=0.01)               # the trough
    b.box(w, 0.05, 2.0, W, UV("wood"), M.at(y=0.16, z=1.0))                      # back board
    b.box(w + 0.06, 0.2, 0.06, W, UV("wood"), M.at(y=0.07, z=1.72), bevel=0.008) # top rail
    b.box(w, 0.2, 0.05, W, UV("wood"), M.at(y=0.07, z=0.9))                      # middle rail
    label_plate(b, "label_spears", M.at(y=-0.185, z=0.07))
    xs = [-0.5, -0.25, 0.0, 0.25, 0.5]
    for i, x in enumerate(xs):
        b.cylinder(0.03, 0.03, 0.02, B, UV("bronze_dark"), M.at(x=x, y=0.02, z=0.145))  # the sockets
        if i == 3:
            continue  # the missing one
        lean = 2.0 * (i - 2)
        b.cylinder(0.016, 0.016, 2.3, W, UV("wood"), M.at(x=x, y=0.02, z=1.29, ry=lean * 0.3))
        b.cylinder(0.036, 0.0, 0.26, B, UV("bronze"), M.at(x=x + lean * 0.004, y=0.02, z=2.57), segments=8)
        b.cylinder(0.012, 0.0, 0.1, B, UV("bronze_dark"), M.at(x=x, y=0.02, z=0.17, rx=180), segments=8)
    return b.object("SpearRack", MATS)


CASE = (0.9, 0.8, 1.3)  # the shield case: footprint, cabinet height, glass height (like the tall case)


def shield_case():
    """The Shield of Achilles on a stand, under glass, on a wooden cabinet with its label."""
    b = M.Builder()
    s, cab, glass = CASE
    b.box(s, s, cab, W, UV("wood"), M.at(z=cab / 2), bevel=0.01)
    label_plate(b, "label_shield", M.at(y=-s / 2 - 0.004, z=cab - 0.18))
    top = cab + glass
    b.box(s - 0.02, s - 0.02, glass, G, UV("glass"), M.at(z=cab + glass / 2))
    for x in (-1, 1):                                                               # brass corner posts
        for y in (-1, 1):
            b.box(0.03, 0.03, glass, B, UV("bronze"), M.at(x=x * (s / 2 - 0.015), y=y * (s / 2 - 0.015), z=cab + glass / 2))
    b.box(s + 0.04, s + 0.04, 0.06, W, UV("wood"), M.at(z=top + 0.03), bevel=0.01)
    # The stand: a slanted back and a ledge, and the shield on it
    b.box(0.08, 0.05, 0.6, W, UV("wood"), M.at(y=0.16, z=cab + 0.3, rx=12))
    b.box(0.5, 0.08, 0.04, W, UV("wood"), M.at(y=-0.06, z=cab + 0.04))
    place = M.at(y=0.02, z=cab + 0.42, rx=78)
    painted_disc(b, 0.36, 0.035, B, "shield_achilles", place, segments=40)
    b.sphere(0.05, B, UV("bronze"), place @ Matrix.Translation((0, 0, 0.02)), squash=0.5, segments=12, rings=6)
    return b.object("ShieldCase", MATS)


for obj, name in ((armour("ArmourAjax", "crest_red", "label_ajax", hoplon="hoplon_a"), "armour_ajax"),
                  (armour("ArmourPatroclus", "crest_white", "label_patroclus", hoplon="hoplon_b"), "armour_patroclus"),
                  (armour("ArmourOdysseus", "crest_black", "label_odysseus", spear=True), "armour_odysseus"),
                  (spear_rack(), "spear_rack"),
                  (shield_case(), "shield_case")):
    print(name, len(obj.data.polygons), "faces")
    M.export(obj, OUT / f"{name}.gltf")
