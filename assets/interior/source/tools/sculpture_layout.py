"""Shared by sculpture_build.py (Blender) and make_sculpture_art.py (numpy): the Sculpture Hall set's sizes,
its labels and where each part sits in the set's one texture (asset item P3.1 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024

# The museum plinth the two standing statues share with the empty ones (scenes/statue_plinth.tscn:
# assets/plates/plinth.glb, 1.12 m square, with its brass label on the front)
PLINTH_W = 1.12
PLAQUE = (0.78, 0.335)          # the label on a plinth's front, as on the empty plinths
PLAQUE_AT = (0.0, 0.275, 0.504)

# Homer's pedestal: a dark marble pier, his bust on top
PED_BASE = (0.44, 0.12)         # square base block: width, height
PED_SHAFT = (0.34, 0.9)
PED_CAP = (0.42, 0.07)
PED_H = PED_BASE[1] + PED_SHAFT[1] + PED_CAP[1]
BUST_PLAQUE = (0.26, 0.112)     # the small label on the pier
BUST_PLAQUE_Y = 0.78

# Icarus's wings, hung from the ceiling by three wires. The lowest feather stays above this.
WING_SPAN = 3.5
WING_HANG_Y = 3.2               # the harness, where the wings meet
WING_TILT = 55                  # degrees the spread is tipped up from flat, its top towards the room
WING_DIHEDRAL = 12              # degrees each wing rises towards its tip
WING_MIN_Y = 2.6
assert WING_MIN_Y > D.PLAYER_H + 0.4 and WING_HANG_Y < D.WALL_H

# The statues' triangle budgets after thinning (a hero prop is about 3k)
TRIS = {"venus": 2900, "discus_thrower": 2900, "bust_homer": 2500}
# How finely each is carved before thinning, metres
CARVE = {"venus": 0.005, "discus_thrower": 0.005, "bust_homer": 0.003}

# name: (title, the line under it, the note, the last line in italics)
LABELS = {
    "discus_thrower": ("THE DISCUS THROWER", "Marble, Roman copy after Myron", "The bronze original is lost.",
                       "On loan from Olympia."),
    "venus": ("VENUS", "Marble, Hellenistic, 2nd century BC", "Her arms were handed in to Lost Property.",
              "Please ask at the desk."),
    "bust_homer": ("HOMER", "Marble bust, Roman copy", "Poet of the Iliad and the Odyssey.",
                   "From the Library of Alexandria."),
    "galatea": ("GALATEA", "Marble, by Pygmalion", "Away for cleaning.", "She walked there herself."),
}

REGIONS = {
    "label_discus_thrower": (0, 0, 504, 216),
    "label_venus": (512, 0, 504, 216),
    "label_bust_homer": (0, 224, 504, 216),
    "label_galatea": (512, 224, 504, 216),
    # The statues' own grime: soot in the crevices, dust on top, streaks, fresh white chips
    "venus": (0, 448, 352, 352),
    "discus_thrower": (360, 448, 352, 352),
    "bust_homer": (720, 448, 296, 296),
    # Homer's pier, in a dark green marble
    "ped_shaft": (720, 752, 96, 264),
    "ped_top": (824, 752, 104, 104),
    "ped_base": (824, 864, 192, 48),
    "ped_cap": (824, 920, 192, 32),
    "steel": (936, 752, 32, 32),
    "wax": (936, 792, 80, 64),
    "leather": (824, 960, 192, 24),
    "wood": (824, 992, 192, 24),
}
# Feathers, tip at the top of each cell: long flight feathers, the shorter ones behind them, and coverts
for k in range(3):
    REGIONS["primary_%d" % k] = (k * 68, 808, 64, 208)
    REGIONS["secondary_%d" % k] = (208 + k * 64, 808, 60, 152)
    REGIONS["covert_%d" % k] = (404 + k * 52, 808, 48, 96)
    REGIONS["covert_%d" % (k + 3)] = (404 + k * 52, 912, 48, 96)


def _check():
    cells = list(REGIONS.items())
    for i, (a, (ax, ay, aw, ah)) in enumerate(cells):
        assert ax >= 0 and ay >= 0 and ax + aw <= ATLAS and ay + ah <= ATLAS, a
        for b, (bx, by, bw, bh) in cells[i + 1:]:
            assert ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay, (a, b)
    w, h = REGIONS["label_venus"][2:]
    assert abs(w / h - PLAQUE[0] / PLAQUE[1]) < 0.01


_check()
