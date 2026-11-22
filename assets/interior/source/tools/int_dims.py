"""Every shared size inside the museum, in one place (asset item K0 in docs/hw4_assets_plan.md).
Godot coordinates, metres: y up, rooms run along -z, and every room's floor is y = 0, the same as the
exterior's terrace. Read sizes from here; never hard-code them in a build script or a room.
Frozen once K0 merges: a change here needs a heads-up to the whole team."""

# Rooms (these must match the room contract in docs/hw4_rooms_plan.md)
FLOOR_Y = 0.0
WALL_H = 4.0            # floor to ceiling
WALL_T = 0.5
DOOR_W = 3.0            # every doorway between rooms
DOOR_H = 3.2            # top of the opening; K1's carved frame sits around it
CEILING_T = 0.25

# Bands every wall carries, measured up from the floor
SKIRTING_H = 0.18
SKIRTING_T = 0.03       # how far it stands proud of the wall
CORNICE_H = 0.36        # the carved band right under the ceiling
CORNICE_T = 0.06
CORNICE_Y0 = WALL_H - CORNICE_H
CORNICE_Y1 = WALL_H

# Who looks over what. The guard's eyes are 1.6 m up and she aims at a player's chest, 1.2 m up
# (scenes/guard.tscn Eyes, scripts/guard.gd). Cover at least this tall hides you from her whenever
# you're nearer to it than she is.
GUARD_EYE_Y = 1.6
PLAYER_CHEST_Y = 1.2
PLAYER_H = 2.0          # scenes/player.tscn capsule
PLAYER_R = 0.5
JUMP_REACH = 1.0        # a jump clears about this, so anything lower can be climbed
COVER_MIN_H = 1.4

# Heights of the furniture every room shares
PLINTH_H = 0.6          # the statue plinths (scenes/pressure_plate.tscn)
BENCH_H = 0.45
ROPE_POST_H = 0.95
CASE_LOW_H = 1.05       # top of the glass on a low display case
CASE_TALL_H = 2.1
CRATE_H = (0.7, 1.4, 2.1)   # small, cover, tall; they stack in 0.7 m steps
PICTURE_Y = 1.6         # centre of a hung painting
LIGHT_Y = 3.5           # room lights, as in scenes/museum.tscn

# Wall paint, one per room mood (sRGB). The plaster texture is pale grey; these tint it.
WALL_PAINT = {
    "cream": (0.89, 0.85, 0.77),    # lobby, Sculpture Hall, the gallery
    "red": (0.50, 0.27, 0.24),      # Pompeian red for picture rooms
    "green": (0.30, 0.42, 0.35),    # library green for the archives
}
CEILING_TINT = (0.80, 0.78, 0.74)
MOULDING_TINT = (0.93, 0.90, 0.84)
SKIRTING_TINT = (0.16, 0.18, 0.17)  # the marble, darkened to a green-black

# How much floor or wall one copy of each texture covers, in metres
PARQUET_TILE = 2.0      # 4 x 4 blocks of 0.5 m, four slats each
MARBLE_TILE = 1.6
MARBLE_SLAB = 0.8       # floor slabs, with grout between
PLASTER_TILE = 2.5
TRIM_REPEAT = 1.2       # the exterior's carved strip (assets/exterior/source/tools/make_trim.py)
CORNICE_ROWS = 0.70     # the cornice shows the strip's top three rows: egg-and-dart, beads and leaves
WEAR_TILE = 3.1         # dirt, scratches and dull patches, on a different repeat from every surface under them
SCUFF_H = 1.0           # walls collect scuffs and grime below this height, where feet, bags and trolleys hit

# P1.4 rope barriers and bench (the post and bench heights are the shared ones above)
POST_BASE_R = 0.16
POST_SHAFT_R = 0.024
ROPE_HOOK_Y = ROPE_POST_H - 0.1   # where the rope's end caps clip on
ROPE_SPAN = 2.0         # post to post, as built; scripts/props/rope_barrier.gd stretches it
ROPE_SAG = 0.16
ROPE_R = 0.019
BENCH_L = 1.8
BENCH_D = 0.5

# P1.6 signs
WETFLOOR_H = 0.64
WETFLOOR_W = 0.3
WETFLOOR_SPLAY = 0.30   # distance between the two feet, front to back
PLACARD_POST_H = 0.98
PLACARD_W = 0.36
PLACARD_H = 0.26
