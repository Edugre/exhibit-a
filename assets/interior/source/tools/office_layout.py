"""Shared by office_build.py (Blender) and make_office_art.py (numpy): the Security Office set's sizes and
where each part sits in its one texture (asset item P3.4 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024

DESK = (1.6, 0.8, 0.76)          # width, depth, height
MONITOR_WALL = (2.4, 0.5, 2.35)  # a console with six screens above it, for standing against a wall
LOCKER = (0.5, 0.5, 1.9)         # one locker; the prop is a row of three. Taller than COVER_MIN_H
CHAIR_SEAT = 0.48
assert LOCKER[2] >= D.COVER_MIN_H

# The six feeds on the wall and the two on the desk, in the order the build script places them
FEEDS = ["cam1", "cam2", "cam3", "cam4", "cam5", "cam6"]
DESK_SCREENS = ["desk_feed", "desk_log"]

REGIONS = {
    "steel": (0, 0, 256, 256),
    "door_0": (264, 0, 96, 256),
    "door_1": (368, 0, 96, 256),
    "door_2": (472, 0, 96, 256),
    "laminate": (576, 0, 256, 128),
    "dark": (840, 0, 128, 128),
    "knit": (576, 136, 128, 128),
    "fabric": (712, 136, 128, 128),
    "mug": (848, 136, 96, 64),
    "logbook": (848, 208, 96, 56),
    "keyboard": (576, 272, 160, 48),
    "keyboard_board": (744, 272, 160, 112),
    "cam1": (0, 264, 160, 120),
    "cam2": (168, 264, 160, 120),
    "cam3": (336, 264, 160, 120),
    "cam4": (0, 392, 160, 120),
    "cam5": (168, 392, 160, 120),
    "cam6": (336, 392, 160, 120),
    "desk_feed": (504, 392, 160, 120),
    "desk_log": (672, 392, 160, 120),
}
