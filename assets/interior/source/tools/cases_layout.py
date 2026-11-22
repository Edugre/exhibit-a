"""Shared by cases_build.py (Blender) and make_cases_art.py (numpy): the glass display cases' sizes and
where each part sits in the set's one texture (asset item P1.2 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024

# Tall case: a wooden cabinet, a glass box with one glass shelf, and a wooden cap
TALL_W = 0.9
TALL_BASE_H = 0.8
TALL_GLASS_TOP = D.CASE_TALL_H - 0.08
TALL_SHELF_Z = 1.42
# Low case: a table cabinet with a shallow glass lid over a velvet bed
LOW_W, LOW_D = 1.4, 0.7
LOW_BASE_H = D.CASE_LOW_H - 0.2
KICK_H = 0.06          # the dark recessed foot under each cabinet
FRAME = 0.022          # the brass strips along the glass edges

REGIONS = {
    "wood": (0, 0, 384, 384),
    "pottery": (384, 0, 512, 256),
    "glass": (896, 0, 128, 128),
    "brass": (896, 128, 128, 64),
    "coin_gold": (896, 192, 64, 64),
    "coin_silver": (960, 192, 64, 64),
    "velvet": (384, 256, 256, 128),
    "parchment": (640, 256, 256, 128),
    "card_tall": (0, 384, 256, 128),
    "card_low": (256, 384, 256, 128),
    "plate": (512, 384, 256, 48),
    "mouth": (896, 256, 32, 32),
}
