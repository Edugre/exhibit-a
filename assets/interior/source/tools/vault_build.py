"""Background Blender job (asset plan P3.6): the vault room set. Two empty gilt frames with a card hung in
each (Helen's, on loan to Sparta; Hector's, removed at Achilles' request) and their wall labels, and a run of
empty steel library shelving for the vault, one run with the library's sign and a card left on it. Run vault_art.py first.
usage: blender -b --factory-startup --python vault_build.py -- <out dir>
Every prop faces -Y here (+Z in Godot)."""
import importlib
import pathlib
import sys
from mathutils import Vector

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import int_dims as D
import int_mesh as M
importlib.reload(D)
importlib.reload(M)

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1]).resolve()
M.reset()
atlas = M.Atlas(HERE / "vault_atlas.json", OUT / "int_vault.png")
GILT = M.material("gilt", atlas.image, metallic=0.85, roughness=0.35)
STEEL = M.material("steel", atlas.image, metallic=0.7, roughness=0.45)
CARD = M.material("card", atlas.image, roughness=0.8)
UV = atlas.uv
FRONT = Vector((0, -1, 0))
RIGHT = Vector((1, 0, 0))
UP = Vector((0, 0, 1))

FRAME = (1.0, 1.3, 0.12)   # outer width, height, moulding width
LABEL = (0.3, 0.056)
CARD_SIZE = (0.3, 0.2)
SHELF = (1.6, 2.4, 0.4)    # width, height, depth of one run of shelving


def printed(b, slot, rect, w, h, place, thick=0.006, base="card"):
    faces = b.box(w, thick, h, slot, UV(base), place)
    rot = place.to_3x3()
    b.print_face(faces, rot @ FRONT, rot @ RIGHT, rot @ UP, UV(rect))


def empty_frame(name, who):
    """A gilt frame with nothing in it but the wall, a card hung on a cord in the middle, and the label
    below. Origin: the frame's centre on the wall's surface; its back is flat on the wall."""
    b = M.Builder()
    w, h, m = FRAME
    depth = 0.07
    for x in (-(w - m) / 2, (w - m) / 2):                       # the stiles and rails, bevelled
        b.box(m, depth, h, 0, UV("gilt"), M.at(x=x, y=-depth / 2), bevel=0.012)
    for z in (-(h - m) / 2, (h - m) / 2):
        b.box(w - 2 * m + 0.01, depth, m, 0, UV("gilt"), M.at(y=-depth / 2, z=z), bevel=0.012)
    for x in (-(w - 2 * m) / 2, (w - 2 * m) / 2):                # a thin inner bead
        b.box(0.02, depth + 0.012, h - 2 * m, 0, UV("gilt"), M.at(x=x, y=-depth / 2))
    cw, ch = CARD_SIZE
    top = 0.18
    for x in (-0.09, 0.09):                                      # the cord from a pin at the top
        b.tube([(0.0, -0.02, h / 2 - m), (x, -0.025, top + ch / 2)], 0.003, 1, UV("brass"), segments=6)
    b.sphere(0.008, 1, UV("brass"), M.at(y=-0.02, z=h / 2 - m), segments=8, rings=5)
    printed(b, 2, f"card_{who}", cw, ch, M.at(y=-0.03, z=top, rx=-4))
    printed(b, 1, f"label_{who}", LABEL[0], LABEL[1], M.at(y=-0.004, z=-h / 2 - 0.12), thick=0.008, base="brass")
    return b.object(name, [GILT, STEEL, CARD])


def shelving(name, signed):
    """A run of steel library shelving, five shelves, all of them empty. The signed one has the library's
    brass sign on top and one card left on it. Its back goes against a wall (+Y); origin on the floor, in the middle."""
    b = M.Builder()
    w, h, d = SHELF
    for x in (-w / 2 + 0.02, w / 2 - 0.02):
        b.box(0.04, d, h, 1, UV("steel_dark"), M.at(x=x, z=h / 2))
    b.box(w, 0.02, h, 1, UV("steel_dark"), M.at(y=d / 2 - 0.01, z=h / 2))
    for k in range(6):
        z = 0.1 + k * (h - 0.2) / 5
        b.box(w - 0.06, d - 0.03, 0.025, 1, UV("steel"), M.at(y=-0.005, z=z))
        b.box(w - 0.06, 0.01, 0.05, 1, UV("steel"), M.at(y=-d / 2 + 0.005, z=z - 0.012))  # the lip
    if not signed:
        return b.object(name, [GILT, STEEL, CARD])
    printed(b, 1, "shelf_sign", 1.4, 0.26, M.at(y=-d / 2 - 0.01, z=h + 0.15), thick=0.01, base="brass")
    for x in (-0.6, 0.6):
        b.box(0.03, 0.02, 0.06, 1, UV("brass"), M.at(x=x, y=-d / 2 - 0.005, z=h + 0.01))
    # One card, propped against the back of the middle shelf
    z = 0.1 + 2 * (h - 0.2) / 5 + 0.0125
    printed(b, 2, "shelf_card", 0.15, 0.1, M.at(x=0.1, y=d / 2 - 0.06, z=z + 0.05, rx=-12))
    return b.object(name, [GILT, STEEL, CARD])


for obj, name in ((empty_frame("FrameHelen", "helen"), "frame_helen"),
                  (empty_frame("FrameHector", "hector"), "frame_hector"),
                  (shelving("EmptyShelving", False), "empty_shelving"),
                  (shelving("EmptyShelvingSigned", True), "empty_shelving_signed")):
    print(name, len(obj.data.polygons), "faces")
    M.export(obj, OUT / f"{name}.gltf")
