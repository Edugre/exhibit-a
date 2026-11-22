"""Shared by doorway_build.py (Blender) and make_doorway_art.py (numpy): the doorway set's sizes, the room
plaques, and where each part sits in its one texture (asset item K1 in docs/hw4_assets_plan.md).
Pixel rectangles are (x, y, width, height) from the texture's top-left corner.

Two rooms meet back to back, each owning half the doorway's depth (int_dims.WALL_T). Each room frames
the half it owns:
  - its entrance with the portal: a stone arch, its name plaque facing the room you come from;
  - its exit with the jambs: carved sides only, full height, so the next room's plaque shows through
    and the sliding RoomGate still has its slot."""
import math

import int_dims as D

ATLAS = 1024

# The arch over a room's entrance: segmental, springing from the jambs and peaking at DOOR_H
HALF = D.DOOR_W / 2
SPRING_Y = 2.6
RISE = D.DOOR_H - SPRING_Y
RADIUS = (HALF * HALF + RISE * RISE) / (2 * RISE)
CENTRE_Y = D.DOOR_H - RADIUS
HALF_ANGLE = math.asin(HALF / RADIUS)
RING = 0.24             # depth of the arch stones, face to face across the ring
RING_PROUD_IN = 0.05    # how far the ring stands out from the wall, on the room side
RING_PROUD_OUT = 0.04   # and on the side facing the previous room
VOUSSOIRS = 5           # arch stones each side of the keystone

PILASTER_W = 0.24       # the carved strips up the sides of a doorway
PILASTER_T = 0.07
PLINTH_H = 0.32         # the blocks they stand on, which cover the skirting's ends
PLINTH_T = 0.09
IMPOST_H = 0.10         # the cap the arch springs from
CONSOLE_H = 0.34        # the bracket that ends an exit jamb under the cornice

PLAQUE_W, PLAQUE_H = 1.4, 0.32
PLAQUE_Y = 3.48         # bottom edge: clear of the ring's outer edge (about 3.44) and under the 4 m ceiling
assert PLAQUE_Y > CENTRE_Y + RADIUS + RING
assert SPRING_Y - IMPOST_H > PLINTH_H and D.CORNICE_Y0 - CONSOLE_H > D.DOOR_H

# Every room's plaque, so the other tracks can drop theirs in: (scene name, title, the line under it)
PLAQUES = [
    ("sculpture_hall", "SCULPTURE HALL", "Antiquities in Marble and Bronze"),
    ("twin_archives", "THE TWIN ARCHIVES", "Castor & Pollux Reading Rooms"),
    ("security_office", "SECURITY OFFICE", "Staff Only"),
    ("hall_of_arms", "HALL OF ARMS", "Arms & Armour of the Heroic Age"),
    ("vault", "THE VAULT", "Special Collections · Strictly No Lending"),
]

REGIONS = {
    "stone": (512, 0, 256, 256),
    "casing": (768, 0, 128, 512),
    "plinth": (896, 0, 128, 128),
    "impost": (896, 128, 128, 64),
    "keystone": (896, 192, 128, 192),
    "console": (896, 384, 128, 128),
    "brass": (512, 256, 256, 64),
    "lamp": (512, 328, 64, 32),
}
for k in range(8):      # eight dressed stones, so neighbouring arch stones never look alike
    REGIONS["block_%d" % k] = (128 * (k % 4), 128 * (k // 4), 128, 128)
for i, (name, _, _) in enumerate(PLAQUES):
    REGIONS["plaque_" + name] = (0, 264 + i * 128, 512, 117)
