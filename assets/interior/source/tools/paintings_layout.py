"""Shared by paintings_build.py (Blender) and make_paintings_art.py (numpy): the paintings' sizes, titles
and where each part sits in the set's one texture (asset item P1.3 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024
GLOW = 512              # the picture lights' glow is soft, so its texture is half size

# Three frame sizes: (outer width, outer height, moulding width, depth off the wall); turn one for portraits
FRAMES = {
    "large": (1.6, 1.0, 0.12, 0.07),
    "medium": (1.0, 0.8, 0.09, 0.055),
    "small": (0.6, 0.75, 0.07, 0.045),
}
LABEL = (0.3, 0.056)    # the brass title label on the wall under each painting
LABEL_GAP = 0.07

# name: (frame, portrait?, title, the line under it)
PAINTINGS = {
    "small_splash": ("large", False, "Landscape with a Small Splash", "School of Daedalus · Oil on canvas"),
    "achilles": ("large", True, "Achilles, Full-Length Portrait", "Feet cropped at the sitter's request"),
    "sisyphus": ("medium", False, "Sisyphus, Almost There", "One of a series · Oil on canvas"),
    "narcissus": ("medium", True, "Narcissus, Self-Portrait #47", "Narcissus (attributed) · Oil on canvas"),
    "disputed_apple": ("small", True, "Still Life with Disputed Apple", "Paris School · Oil on panel"),
    "medusa": ("small", True, "Portrait of Medusa (Rear View)", "Hung this way for visitors' safety"),
}


def outer(name):
    """A painting's frame outside size (width, height) as hung."""
    frame, portrait, _, _ = PAINTINGS[name]
    w, h, _, _ = FRAMES[frame]
    if frame != "small" and portrait:
        w, h = h, w
    return w, h


def canvas(name):
    w, h = outer(name)
    m = FRAMES[PAINTINGS[name][0]][2]
    return w - 2 * m, h - 2 * m


REGIONS = {
    "small_splash": (0, 0, 496, 277),
    "achilles": (504, 0, 256, 458),
    "narcissus": (768, 0, 242, 320),
    "sisyphus": (0, 285, 320, 242),
    "disputed_apple": (768, 328, 184, 244),
    "medusa": (0, 535, 184, 244),
    "gilt": (328, 285, 64, 512),       # the frame's carved face, outer edge to inner, along its length
    "gilt_plain": (400, 285, 96, 96),  # its sides
    "brass": (192, 535, 128, 32),
    "lamp": (192, 575, 64, 16),
}
for k, name in enumerate(PAINTINGS):
    REGIONS["label_" + name] = (504, 466 + k * 52, 256, 48)
for name in PAINTINGS:   # each canvas's picture should keep the canvas's shape
    w, h = canvas(name)
    rw, rh = REGIONS[name][2:]
    assert abs(rw / rh - w / h) < 0.02, (name, rw / rh, w / h)
