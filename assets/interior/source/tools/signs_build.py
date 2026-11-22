"""Background Blender job (asset plan P1.6): a yellow wet-floor A-frame and a brass "Do not touch"
stand with a tilted placard. Run signs_art.py first.
usage: blender -b --factory-startup --python signs_build.py -- <out dir>"""
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

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1])
M.reset()
atlas = M.Atlas(HERE / "signs_atlas.json", OUT / "int_signs.png")
PLASTIC = M.material("plastic", atlas.image, roughness=0.38)
RUBBER = M.material("rubber", atlas.image, roughness=0.9)
BRASS = M.material("brass", atlas.image, metallic=1.0, roughness=0.28)
CARD = M.material("card", atlas.image, roughness=0.8)


def wet_floor():
    """Two printed panels leaning together, hinged at the top. Front faces -Y (Godot +Z). Origin on the floor."""
    b = M.Builder()
    h, w, half = D.WETFLOOR_H, D.WETFLOOR_W, D.WETFLOOR_SPLAY / 2
    lean = math.degrees(math.atan2(half, h))
    length = math.hypot(half, h)
    thick = 0.012
    for side in (-1, 1):  # -1: front panel (on -Y), +1: back panel
        tilt = lean * side  # rotate about X so the panel leans in from its foot at y = side * half
        place = M.at(y=side * half, rx=tilt) @ Matrix.Translation((0, 0, length / 2))
        faces = b.box(w, thick, length, 0, atlas.uv("yellow"), place)
        out = Vector((0, side, 0))
        up = (M.at(rx=tilt).to_3x3() @ Vector((0, 0, 1)))
        right = Vector((1, 0, 0)) if side < 0 else Vector((-1, 0, 0))
        b.print_face(faces, out, right, up, atlas.uv("wetfloor"))
        b.box(w, 0.03, 0.02, 1, atlas.uv("rubber"), M.at(y=side * (half - 0.004), z=0.01))
    b.cylinder(0.012, 0.012, w + 0.02, 0, atlas.uv("yellow"), M.at(z=h - 0.004, ry=90))
    b.box(0.16, 0.035, 0.05, 0, atlas.uv("yellow"), M.at(z=h + 0.02), bevel=0.01)
    return b.object("WetFloor", [PLASTIC, RUBBER])


def do_not_touch():
    """A brass post with a placard on top, tilted back for reading. Front faces -Y. Origin on the floor."""
    b = M.Builder()
    brass = atlas.uv("brass")
    r = D.POST_BASE_R
    b.cylinder(r, r, 0.022, 0, brass, M.at(z=0.011), segments=32)
    b.cylinder(r * 0.94, 0.045, 0.05, 0, brass, M.at(z=0.047), segments=32)
    top = D.PLACARD_POST_H - 0.16
    b.cylinder(D.POST_SHAFT_R, D.POST_SHAFT_R, top - 0.072, 0, brass, M.at(z=(top + 0.072) / 2))
    b.cylinder(0.034, 0.03, 0.04, 0, brass, M.at(z=top))
    tilt = -28.0  # top leans away from the reader (+Y), so the card faces up at them
    centre = Vector((0, 0.03, D.PLACARD_POST_H - 0.03))
    frame = M.at(*centre, rx=tilt)
    b.box(D.PLACARD_W + 0.03, 0.014, D.PLACARD_H + 0.03, 0, brass, frame, bevel=0.004)
    card = frame @ Matrix.Translation((0, -0.009, 0))
    faces = b.box(D.PLACARD_W, 0.004, D.PLACARD_H, 1, atlas.uv("placard"), card)
    rot = M.at(rx=tilt).to_3x3()
    b.print_face(faces, rot @ Vector((0, -1, 0)), Vector((1, 0, 0)), rot @ Vector((0, 0, 1)), atlas.uv("placard"))
    # A bracket from the post up to the back of the frame
    b.box(0.03, 0.02, 0.1, 0, brass, M.at(y=0.04, z=top + 0.06))
    return b.object("DoNotTouch", [BRASS, CARD])


for make, name in ((wet_floor, "wet_floor"), (do_not_touch, "do_not_touch")):
    M.export(make(), OUT / f"{name}.gltf")
