"""Shared by archives_build.py (Blender) and make_archives_art.py (numpy): the Twin Archives set's sizes
and where each part sits in its one texture (asset item P3.2 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024
WOOD_TILE = 1.0          # metres of wood one copy of the grain covers before it would stretch

CATALOGUE = (1.2, 0.5, 1.3)          # width, depth, height: a card catalogue, drawers on the front
CATALOGUE_DRAWERS = (6, 8)           # columns, rows
RACK = (1.0, 0.4, 1.8)               # a scroll rack, pigeonholes on the front
RACK_CELLS = (5, 7)
TABLE = (2.0, 0.9, 0.76)             # the reading table
CHAIR_SEAT = 0.46
LADDER = (0.5, 2.75, 14.0)           # width, rail length, lean from upright (degrees)
LAMP = (0.32, 0.4)                   # a banker's lamp: shade length, height

assert TABLE[2] < D.COVER_MIN_H and CATALOGUE[2] < D.COVER_MIN_H   # furniture, not cover (the room has no guard)

REGIONS = {
    "oak": (0, 0, 256, 256),
    "oak_dark": (264, 0, 256, 256),
    "drawers": (528, 0, 384, 368),
    "cubbies": (0, 264, 256, 410),
    "pages": (264, 264, 256, 160),
    "pages_2": (264, 432, 256, 160),
    "leather": (528, 376, 128, 128),
    "brass": (664, 376, 128, 32),
    "glass": (664, 416, 128, 64),
    "glow": (800, 376, 64, 32),
    "sign": (664, 488, 160, 64),
    "chair_back": (528, 512, 128, 128),
}
