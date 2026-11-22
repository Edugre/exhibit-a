"""Background Blender job (asset plan P2.1, P2.2): the laser grid's emitter post, and its switch: a floor pad
with a control post. The pad's top is its own file, because pressure_plate.gd sinks a node called
"PlinthCap" when someone stands on it. Run laser_art.py first.
usage: blender -b --factory-startup --python laser_build.py -- <out dir>"""
import importlib
import pathlib
import sys
from mathutils import Vector

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import int_mesh as M
importlib.reload(M)

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1])
M.reset()
atlas = M.Atlas(HERE / "laser_atlas.json", OUT / "int_laser.png")
STEEL = M.material("steel", atlas.image, metallic=0.8, roughness=0.45)
PAINT = M.material("paint", atlas.image, roughness=0.6)
RUBBER = M.material("rubber", atlas.image, roughness=0.95)
UV = atlas.uv
FRONT, RIGHT, UP = Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))

POST_W = 0.12        # laser_grid.gd POST_SIZE
POST_H = 2.4         # built for the grid's default height; laser_grid.gd scales it to fit


def laser_post():
    """One of the grid's two posts. Origin on the floor; the front (Godot +Z) carries the maker's plate."""
    b = M.Builder()
    b.box(0.3, 0.3, 0.04, 1, UV("dark"), M.at(z=0.02), bevel=0.006)
    b.box(POST_W + 0.006, POST_W + 0.006, 0.3, 1, UV("stripes"), M.at(z=0.04 + 0.15))
    b.box(POST_W, POST_W, POST_H - 0.42, 0, UV("steel"), M.at(z=0.34 + (POST_H - 0.42) / 2))
    b.box(0.16, 0.16, 0.06, 1, UV("dark"), M.at(z=POST_H - 0.05), bevel=0.008)
    b.sphere(0.028, 1, UV("lens"), M.at(z=POST_H - 0.01), squash=0.6, segments=10, rings=6)
    plate = b.box(0.09, 0.006, 0.27, 1, UV("maker"), M.at(y=-POST_W / 2 - 0.003, z=1.35))
    b.print_face(plate, FRONT, RIGHT, UP, UV("maker"))
    return b.object("LaserPost", [STEEL, PAINT])


def switch_base():
    """The pad's hazard-striped frame, and the control post behind it (Godot -Z) with its box.
    Origin on the floor in the middle of the pad."""
    b = M.Builder()
    # A striped frame round a low floor, so the top (0.9 m, resting 0.05 up) has room to sink 3 cm
    # without ever reaching the frame's top face
    for x, y, sx, sy in ((0, 0.5, 1.1, 0.1), (0, -0.5, 1.1, 0.1), (0.5, 0, 0.1, 0.9), (-0.5, 0, 0.1, 0.9)):
        b.box(sx, sy, 0.05, 1, UV("stripes"), M.at(x=x, y=y, z=0.025))
    b.box(0.9, 0.9, 0.015, 1, UV("dark"), M.at(z=0.0075))
    px, py = 0.42, 0.52
    b.box(0.2, 0.14, 0.02, 1, UV("dark"), M.at(x=px, y=py, z=0.06))
    b.box(0.06, 0.06, 0.95, 0, UV("steel"), M.at(x=px, y=py, z=0.07 + 0.475))
    box = b.box(0.3, 0.12, 0.22, 1, UV("dark"), M.at(x=px, y=py, z=1.0), bevel=0.01)
    b.print_face(box, FRONT, RIGHT, UP, UV("box"))
    return b.object("SwitchBase", [STEEL, PAINT])


def switch_top():
    """The pad's top, which sinks a little under someone's feet. Origin at the middle of its underside."""
    b = M.Builder()
    top = b.box(0.9, 0.9, 0.03, 0, UV("rubber"), M.at(z=0.015), bevel=0.004)
    # Read from the front: left to right is +X, and "up the print" runs away from the reader (+Y here)
    b.print_face(top, UP, RIGHT, Vector((0, 1, 0)), UV("pad"))
    return b.object("SwitchTop", [RUBBER])


for make, name in ((laser_post, "laser_post"), (switch_base, "switch_base"), (switch_top, "switch_top")):
    M.export(make(), OUT / f"{name}.gltf")
