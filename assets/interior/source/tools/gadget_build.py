"""Background Blender job (asset plan P2.4): the Signal Jammer, a hand-sized radio with an antenna, a dial,
a red LED and a belt clip. Run gadget_art.py first.
usage: blender -b --factory-startup --python gadget_build.py -- <out dir>"""
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
atlas = M.Atlas(HERE / "gadget_atlas.json", OUT / "int_gadget.png")
PLASTIC = M.material("plastic", atlas.image, roughness=0.55)
METAL = M.material("metal", atlas.image, metallic=1.0, roughness=0.35)
RUBBER = M.material("rubber", atlas.image, roughness=0.9)
LED = M.material("led", atlas.image, roughness=0.2, emission=4.0)
UV = atlas.uv

# Sizes in metres. The front faces -Y (Godot +Z); the origin is the middle of the body.
W, D, H = 0.07, 0.035, 0.13


def jammer():
    b = M.Builder()
    body = b.box(W, D, H, 0, UV("plastic"), M.at(), bevel=0.008)
    b.print_face(body, Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), UV("face"))
    b.print_face(body, Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1)), UV("back"))
    b.box(W + 0.006, D + 0.006, 0.03, 2, UV("rubber"), M.at(z=-H / 2 + 0.012), bevel=0.004)   # rubber boot
    # Antenna with a ball on the end, off to one side
    b.cylinder(0.006, 0.006, 0.02, 2, UV("rubber"), M.at(x=-0.022, z=H / 2 + 0.01))
    b.cylinder(0.0025, 0.0018, 0.12, 1, UV("metal"), M.at(x=-0.022, z=H / 2 + 0.08))
    b.sphere(0.005, 1, UV("metal"), M.at(x=-0.022, z=H / 2 + 0.142), segments=8, rings=5)
    # Dial and the LED on top
    b.cylinder(0.009, 0.009, 0.01, 1, UV("metal"), M.at(x=0.016, z=H / 2 + 0.005), segments=12)
    b.sphere(0.0045, 3, UV("led"), M.at(x=0.0, y=-0.006, z=H / 2 + 0.002), segments=8, rings=5)
    # Belt clip on the back, above the sticker
    b.box(0.022, 0.004, 0.04, 1, UV("metal"), M.at(y=D / 2 + 0.006, z=0.03))
    return b.object("SignalJammer", [PLASTIC, METAL, RUBBER, LED])


M.export(jammer(), OUT / "signal_jammer.gltf")
