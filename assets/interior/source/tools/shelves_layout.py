"""Shared by shelves_build.py (Blender) and make_shelves_art.py (numpy): the archive bookcases' sizes and
where each part sits in the set's one texture (asset item P2.3 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024
UNIT_W = 1.2            # every bookcase is this wide, so a row of them makes a straight wall
HEIGHT = 2.7            # 2.5 m and up, as Twin Archives needs: nobody sees over it, even jumping
DEPTH_DOUBLE = 0.62     # books on both faces, for a wall standing out in the room
DEPTH_WALL = 0.4        # books on the front only, for standing against a wall
PANEL = 0.03            # side panels, shelves and back
KICK = 0.1
CROWN = 0.12            # the moulded top
SHELVES = 6             # compartments, bottom to top
SPINE_PX_PER_M = 400    # 1024 pixels of spines cover 2.56 m of books
assert HEIGHT < D.WALL_H

REGIONS = {
    "spines_tall": (0, 0, 1024, 128),
    "spines_mid": (0, 136, 1024, 128),
    "spines_short": (0, 272, 1024, 128),
    "wood": (0, 408, 384, 384),
    "pages": (392, 408, 256, 64),
    "cover": (392, 480, 128, 128),
    "label_0": (656, 408, 96, 40),
    "label_1": (760, 408, 96, 40),
    "label_2": (864, 408, 96, 40),
    "label_3": (656, 456, 96, 40),
}
ROWS = ("spines_short", "spines_mid", "spines_tall")    # by book height
LABELS = ("label_0", "label_1", "label_2", "label_3")
