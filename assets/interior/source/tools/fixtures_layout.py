"""Shared by fixtures_build.py (Blender) and make_fixtures_art.py (numpy): the ceiling and wall fixtures'
sizes and where each part sits in the set's one texture (asset item P1.5 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 512

# A pendant lamp, hung a little above a room light (int_dims.LIGHT_Y): the light shines down freely, and
# the shade only stops light going up, leaving a soft patch of shadow on the ceiling as a real one would.
PENDANT_LIFT = 0.22                  # how far above the room light the bowl's bottom hangs
PENDANT_SHADE = (0.26, 0.2)          # radius at the rim, height
PENDANT_BOWL = 0.07                  # how far the glass bowl hangs below the rim
PANEL = (1.2, 0.6)                   # a recessed office light panel, flush with the ceiling
EXIT = (0.48, 0.204, 0.05)           # the EXIT sign: width, height, depth off the wall
VENT = (0.6, 0.32)                   # a wall vent grille

REGIONS = {
    "brass": (0, 0, 128, 32),
    "steel": (0, 40, 128, 64),
    "opal": (136, 0, 64, 64),
    "panel": (208, 0, 256, 128),
    "exit": (0, 112, 256, 109),
    "exit_side": (264, 136, 64, 32),
    "vent_back": (136, 72, 64, 32),
    "vent_plate": (264, 176, 192, 40),
}
assert abs(EXIT[0] / EXIT[1] - REGIONS["exit"][2] / REGIONS["exit"][3]) < 0.05   # the sign's face keeps its shape
assert D.LIGHT_Y + PENDANT_LIFT + PENDANT_BOWL + PENDANT_SHADE[1] < D.WALL_H
