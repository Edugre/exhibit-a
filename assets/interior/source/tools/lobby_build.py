"""Background Blender job (asset plan P3.5): the lobby set. A ticket desk with a lamp and a bell, a coat
check counter with its rack and coats, a donation box, the museum map on a stand, and two wall banners.
Run lobby_art.py first.
usage: blender -b --factory-startup --python lobby_build.py -- <out dir>"""
import importlib
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
atlas = M.Atlas(HERE / "lobby_atlas.json", OUT / "int_lobby.png")
WOOD = M.material("wood", atlas.image, roughness=0.5)
MARBLE = M.material("marble", atlas.image, roughness=0.25)
BRASS = M.material("brass", atlas.image, metallic=1.0, roughness=0.3)
PRINT = M.material("print", atlas.image, roughness=0.75)
CLOTH = M.material("cloth", atlas.image, roughness=0.95)
GLASS = M.material("glass", atlas.image, roughness=0.05, alpha=0.22)
SHADE = M.material("shade", atlas.image, roughness=0.4, emission=1.6)
UV = atlas.uv
FRONT = Vector((0, -1, 0))  # props face -Y here, +Z in Godot
RIGHT = Vector((1, 0, 0))
UP = Vector((0, 0, 1))


def printed_board(b, slot, rect, w, h, place, thick=0.02):
    """A thin board with a print on its front face."""
    faces = b.box(w, thick, h, slot, UV("paper"), place)
    rot = place.to_3x3()
    b.print_face(faces, rot @ FRONT, rot @ RIGHT, rot @ UP, UV(rect))


def ticket_desk():
    """Reception desk, long side along x. Origin on the floor, in the middle."""
    b = M.Builder()
    w, d, h = D.DESK_W, D.DESK_D, D.DESK_H
    b.box(w, d, h - 0.05, 0, UV("wood"), M.at(z=(h - 0.05) / 2))
    b.box(w + 0.1, d + 0.08, 0.05, 1, UV("marble"), M.at(z=h - 0.025), bevel=0.01)
    b.box(w + 0.02, 0.02, 0.08, 2, UV("brass"), M.at(y=-d / 2 - 0.005, z=0.04))
    for x in (-0.4, 0.4):
        b.box(0.02, 0.02, 0.8, 2, UV("brass"), M.at(x=x, y=-d / 2 - 0.005, z=0.5))
    # Ticket sign, leaning back on a brass foot
    b.box(0.6, 0.06, 0.02, 2, UV("brass"), M.at(x=0.55, y=-0.18, z=h + 0.01))
    printed_board(b, 3, "sign_tickets", 0.6, 0.15, M.at(x=0.55, y=-0.17, z=h + 0.09, rx=-15))
    # Bell, brochures and a banker's lamp
    b.cylinder(0.035, 0.035, 0.012, 2, UV("brass"), M.at(x=-0.2, y=-0.15, z=h + 0.006))
    b.sphere(0.045, 2, UV("brass"), M.at(x=-0.2, y=-0.15, z=h + 0.02), squash=0.8, segments=14, rings=8)
    b.box(0.22, 0.3, 0.04, 3, UV("paper"), M.at(x=0.05, y=0.05, z=h + 0.02))
    b.cylinder(0.07, 0.07, 0.02, 2, UV("brass"), M.at(x=-0.85, y=0.1, z=h + 0.01))
    b.cylinder(0.01, 0.01, 0.34, 2, UV("brass"), M.at(x=-0.85, y=0.1, z=h + 0.18))
    b.cylinder(0.075, 0.075, 0.38, 4, UV("shade"), M.at(x=-0.85, y=0.04, z=h + 0.36, ry=90), segments=16)
    return b.object("TicketDesk", [WOOD, MARBLE, BRASS, PRINT, SHADE])


def coat_check():
    """Coat check counter, with the rack and three coats behind it (+Y). Origin on the floor, in the middle."""
    b = M.Builder()
    w, d, h = D.COAT_W, D.COAT_D, D.COAT_H
    b.box(w, d, h - 0.05, 0, UV("wood"), M.at(z=(h - 0.05) / 2))
    b.box(w + 0.06, d + 0.06, 0.05, 1, UV("marble"), M.at(z=h - 0.025), bevel=0.01)
    printed_board(b, 3, "sign_coats", 1.2, 0.3, M.at(y=-d / 2 - 0.012, z=0.62))
    # The rack
    rack_y, top = d / 2 + 0.35, D.RACK_H
    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        b.cylinder(0.02, 0.02, top, 2, UV("brass"), M.at(x=x, y=rack_y, z=top / 2))
        b.box(0.06, 0.4, 0.03, 2, UV("brass"), M.at(x=x, y=rack_y, z=0.015))
    b.cylinder(0.015, 0.015, w - 0.1, 2, UV("brass"), M.at(y=rack_y, z=top - 0.05, ry=90))
    # Three coats on hangers, a little turned
    for x, tint, turn in ((-0.5, "wool_a", 8), (0.05, "wool_b", -5), (0.55, "dark", 4)):
        b.cylinder(0.008, 0.008, 0.1, 2, UV("brass"), M.at(x=x, y=rack_y, z=top - 0.1))
        flat = Matrix.Diagonal((1.0, 0.32, 1.0, 1.0))  # a coat is wide and thin
        b.cylinder(0.27, 0.19, 0.95, 5, UV(tint), M.at(x=x, y=rack_y, z=top - 0.68, rz=turn) @ flat, segments=10)
        b.sphere(0.2, 5, UV(tint), M.at(x=x, y=rack_y, z=top - 0.22, rz=turn) @ Matrix.Diagonal((1.25, 0.4, 0.45, 1.0)), segments=12, rings=8)
        b.cylinder(0.06, 0.08, 0.08, 5, UV(tint), M.at(x=x, y=rack_y, z=top - 0.14, rz=turn) @ flat, segments=8)  # collar
    return b.object("CoatCheck", [WOOD, MARBLE, BRASS, PRINT, PRINT, CLOTH])


def donation_box():
    """A glass box of coins on a wooden pedestal. Origin on the floor, in the middle."""
    b = M.Builder()
    ped = 0.9
    b.box(0.4, 0.4, ped, 0, UV("wood"), M.at(z=ped / 2))
    printed_board(b, 3, "sign_donate", 0.36, 0.24, M.at(y=-0.207, z=0.62), thick=0.01)
    b.box(0.42, 0.42, 0.02, 2, UV("brass"), M.at(z=ped + 0.01))
    glass_h = D.DONATION_H - ped - 0.04
    b.box(0.38, 0.38, glass_h, 4, UV("glass"), M.at(z=ped + 0.02 + glass_h / 2))
    b.box(0.4, 0.4, 0.015, 2, UV("brass"), M.at(z=D.DONATION_H - 0.0075))
    b.box(0.12, 0.02, 0.004, 0, UV("dark"), M.at(z=D.DONATION_H + 0.001))  # the slot
    for i, (x, y) in enumerate(((-0.08, 0.05), (0.06, -0.04), (0.1, 0.09), (-0.03, -0.1), (0.0, 0.02), (-0.11, -0.03), (0.09, -0.11))):
        b.cylinder(0.022, 0.022, 0.006, 2, UV("brass"), M.at(x=x, y=y, z=ped + 0.025 + 0.006 * (i % 3), rx=8 * (i % 2)), segments=12)
    b.box(0.14, 0.07, 0.003, 3, UV("paper"), M.at(x=-0.02, y=0.08, z=ped + 0.045, rz=20))
    return b.object("DonationBox", [WOOD, MARBLE, BRASS, PRINT, GLASS])


def map_board():
    """The museum map on a stand, tilted back a little. Origin on the floor, in the middle."""
    b = M.Builder()
    for x in (-D.MAP_W / 2 - 0.03, D.MAP_W / 2 + 0.03):
        b.box(0.04, 0.04, D.MAP_Y + D.MAP_H + 0.05, 1, UV("dark"), M.at(x=x, y=0.02, z=(D.MAP_Y + D.MAP_H + 0.05) / 2))
        b.box(0.06, 0.4, 0.03, 1, UV("dark"), M.at(x=x, y=0.02, z=0.015))
    centre = M.at(z=D.MAP_Y + D.MAP_H / 2, rx=-10)
    b.box(D.MAP_W + 0.06, 0.03, D.MAP_H + 0.06, 0, UV("wood"), centre @ Matrix.Translation((0, 0.01, 0)))
    printed_board(b, 2, "map", D.MAP_W, D.MAP_H, centre @ Matrix.Translation((0, -0.012, 0)), thick=0.008)
    return b.object("MapBoard", [WOOD, CLOTH, PRINT])


def banner(name, rect):
    """A cloth banner between two brass rods, for hanging flat on a wall. Origin at the bottom middle."""
    b = M.Builder()
    w, h = D.BANNER_W, D.BANNER_H
    cloth = b.box(w, 0.01, h, 1, UV("wool_a"), M.at(z=h / 2))
    b.print_face(cloth, FRONT, RIGHT, UP, UV(rect))
    for z in (0.0, h):
        b.cylinder(0.016, 0.016, w + 0.12, 0, UV("brass"), M.at(z=z, ry=90))
        for x in (-(w + 0.12) / 2, (w + 0.12) / 2):
            b.sphere(0.024, 0, UV("brass"), M.at(x=x, z=z), segments=10, rings=6)
    return b.object(name, [BRASS, CLOTH])


for make, file in ((ticket_desk, "ticket_desk"), (coat_check, "coat_check"), (donation_box, "donation_box"),
                   (map_board, "map_board"), (lambda: banner("BannerBook", "banner_book"), "banner_book"),
                   (lambda: banner("BannerGift", "banner_gift"), "banner_gift")):
    M.export(make(), OUT / f"{file}.gltf")
