"""Every shared size of the museum interior, in metres, in one place (asset plan K0).
The first block mirrors the room contract in scripts/room.gd: change both together.
Item K0 adds the surface sizes; each prop item adds its own block below."""

# Room contract (scripts/room.gd)
DOOR_WIDTH = 3.0
WALL_HEIGHT = 4.0
WALL_THICKNESS = 0.5

# P1.4 rope barriers and bench
POST_HEIGHT = 0.96          # to the top of the finial
POST_BASE_RADIUS = 0.16
POST_SHAFT_RADIUS = 0.024
ROPE_HOOK_HEIGHT = 0.86     # where the rope's end caps clip on
ROPE_SPAN = 2.0             # post to post, as built; rope_barrier.gd stretches it
ROPE_SAG = 0.16
ROPE_RADIUS = 0.019
BENCH_LENGTH = 1.8
BENCH_DEPTH = 0.5
BENCH_SEAT_HEIGHT = 0.46    # top of the cushion

# P1.6 signs
WETFLOOR_HEIGHT = 0.64
WETFLOOR_WIDTH = 0.3
WETFLOOR_SPLAY = 0.30       # distance between the two feet, front to back
PLACARD_POST_HEIGHT = 0.98
PLACARD_WIDTH = 0.36
PLACARD_HEIGHT = 0.26
