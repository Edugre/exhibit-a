"""Shared numbers for the museum exterior blockout. Godot coordinates, metres:
+x east, +y up, +z south (towards the street). Interior floor and terrace are y = 0.
The plan's site plan is 3.5 px per metre, with today's gallery south wall (z = 6) at y_px = 386.
Blender and the collision generator both read this file, so shapes and collision can't drift."""

# Levels
TERRACE_Y = 0.0
PLAZA_Y = -4.5
ROAD_Y = -4.65

# Site, from the plan
BLD_X = 75.0            # building half width (150 m)
BLD_Z_BACK = -71.0      # building is 80 m deep
BLD_Z_FRONT = 8.9       # wing wall line
ROOMS_X = 50.0          # reserved interior, 100 m by 60 m
ROOMS_Z = (-54.0, 6.0)
ROOMS_ROOF_Y = 13.0
STAIR_X = 12.0          # stairs 24 m wide
STAIR_Z_TOP = 14.9
STAIR_Z_BOT = 24.6      # 9.7 m run: 30 steps of 15 cm by 32 cm
STAIR_STEPS = 30
PLAZA_Z_END = 46.6
SIDEWALK_Z_END = 50.6
ROAD_Z_END = 62.6
FAR_WALK_Z_END = 67.0
PARK_Z_END = -77.0
PARK_Z_FAR = -115.0
RING_X = 79.0
BOUND_X = 92.0
BOUND_Z_S = 64.5
BOUND_Z_N = -108.0
FOUNTAIN_X = 48.0
FOUNTAIN_Z = 35.5
FOUNTAIN_R = 7.4
TREE_X = (64.0, 70.0)
TREE_Z = (28.9, 35.7, 42.6)

# Central front, proportions measured from reference photos
BAY = 14.0              # pair centre to pair centre
PAIRS_X = (-21.0, -7.0, 7.0, 21.0)
PAIR_GAP = 1.55         # column centre offset from the pair's centre (1.9 diameters apart, as in the photos)
COL_Z = 12.0
COL_R = 0.82            # 1.64 m diameter at the base
COL_R_TOP = 0.70
PED_Y = 3.2             # pedestal height
PED_W = 5.2
PED_Z = (10.0, 13.5)
COL_TOP_Y = 19.0        # top of capital
ENT_TOP_Y = 22.9        # top of entablature
ATTIC_TOP_Y = 27.6
CREST_Y = 28.9
BLOCK_TOP_Y = 29.2
WALL_Z = 10.0           # pavilion wall face
DOOR_Z = 8.8            # glazing and doors, set back in the arch
ARCH_W = 7.6
ARCH_CROWN_Y = 18.5
PAV_X = 29.0            # three-arch front is 46 m; banded end bays take it to 58 m
TERRACE_Z_FRONT = STAIR_Z_TOP
DOOR_W = 3.0
DOOR_H = 3.8
WING_TOP_Y = 18.2
CHEEK_W = 0.8           # low side walls of the stairs
CHEEK_H = 0.55          # height above the line of the steps
