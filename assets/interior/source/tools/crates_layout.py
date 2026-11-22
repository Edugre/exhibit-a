"""Shared by crates_build.py (Blender) and make_crates_art.py (numpy): the conservation crates' sizes
and where each face sits in the set's one texture (asset item P1.1 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner."""
import int_dims as D

ATLAS = 1024
PX_PER_M = 200          # texture detail on the crates: 5 mm a pixel
PAD = 6                 # spare pixels round every cell, so mipmaps don't bleed one cell into the next

BATTEN_W = 0.08         # the pine battens framing every face
BATTEN_T = 0.022        # how far they stand proud of the plywood
SKID_H = 0.05           # two runners underneath, so a forklift could get in

# name: (width along x, depth along z, height), in metres. Heights stack in CRATE_H steps.
CRATES = {
    "crate_small": (1.0, 0.7, D.CRATE_H[0]),
    "crate_cover": (1.2, 1.0, D.CRATE_H[1]),
    "crate_painting": (1.6, 0.5, D.CRATE_H[2]),
}


def _cells():
    """Every rectangle the texture needs, before packing: (name, width px, height px)."""
    out = []
    for name, (w, d, h) in CRATES.items():
        out.append((name + ".front", round(w * PX_PER_M), round(h * PX_PER_M)))
        out.append((name + ".side", round(d * PX_PER_M), round(h * PX_PER_M)))
        out.append((name + ".top", round(w * PX_PER_M), round(d * PX_PER_M)))
    out.append(("cloth", 448, 448))
    out.append(("tag", 96, 64))
    return out


def _pack():
    """Shelf packing, tallest first, with the batten strip across the bottom."""
    cells = sorted(_cells(), key=lambda c: -c[2])
    rects, x, y, shelf = {}, PAD, PAD, 0
    for name, w, h in cells:
        if x + w + PAD > ATLAS:
            x, y, shelf = PAD, y + shelf + 2 * PAD, 0
        rects[name] = (x, y, w, h)
        x += w + 2 * PAD
        shelf = max(shelf, h)
    y += shelf + 2 * PAD
    rects["batten"] = (PAD, y, ATLAS - 2 * PAD, 48)
    assert y + 48 + PAD <= ATLAS, "the crate texture is full"
    return rects


RECTS = _pack()
