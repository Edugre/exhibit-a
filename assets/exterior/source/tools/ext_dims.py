"""Every size of the museum exterior, 1:1 with the real Fifth Avenue site wherever it could be measured.
Godot coordinates, metres: x along the avenue (north end positive), y up, z out towards the street.
The interior floor and the terrace are y = 0; the street is 4.5 m below them.

Plan shapes come from the OpenStreetMap outline of the building, street and plaza. Heights are not on
the map, so they come from reference photos, scaled by the people in them."""

# Levels
TERRACE_Y = 0.0
PLAZA_Y = -4.5
ROAD_Y = -4.65

# The real footprint, cleaned of survey noise: front corner round the back and home again
FOOTPRINT = [
    (152.3, 18.6), (88.1, 18.6), (88.1, 6.8), (30.4, 6.8), (30.4, 10.0), (-30.4, 10.0), (-30.4, 6.8), (-88.1, 6.8), (-88.1, 18.6),
    (-152.3, 18.6), (-152.3, -96.0), (-141.0, -96.0), (-141.0, -151.5), (-87.8, -151.5), (-87.8, -129.4), (-17.0, -129.4), (-16.0, -130.6),
    (-16.0, -134.2), (-18.6, -137.0), (-28.6, -137.0), (-28.6, -147.5), (-5.5, -170.9), (5.5, -170.9), (28.6, -147.5), (28.6, -137.0),
    (18.6, -137.0), (16.0, -134.2), (16.0, -130.6), (17.0, -129.4), (87.8, -129.4), (87.8, -152.0), (141.0, -152.0), (141.0, -93.7), (152.3, -93.7),
]

# Front of the building
PAV_X = 30.4            # the three-arch pavilion is 61 m wide
MID_X = 88.1            # the middle wings end here, 58 m long
END_X = 152.3           # the end wings end here, 64 m long
WALL_Z = 10.0           # pavilion wall
MID_Z = 6.8             # middle wings, 3.2 m behind the pavilion
END_Z = 18.6            # end wings, 11.8 m forward of the middle wings

# Plaza and street
CURB_Z = 35.0           # the outer tree row stands just inside this kerb; the plaza's area agrees
ROAD_Z_END = 53.3       # Fifth Avenue is 18.3 m kerb to kerb
FAR_WALK_Z_END = 59.0
STAIR_X = 15.0          # stairs 30 m wide
STAIR_Z_TOP = 14.9
STAIR_Z_BOT = 24.6      # 9.7 m run: 30 steps of 15 cm by 32 cm
STAIR_STEPS = 30
FOUNTAIN_X = 38.5
FOUNTAIN_Z = 22.05
FOUNTAIN_SIZE = 13.7    # the real fountains are square pools
TERRACE_Z_FRONT = STAIR_Z_TOP

# Walkable edge of the site
RING_X = 165.0
BOUND_X = 172.0
BOUND_Z_S = 58.5
BOUND_Z_N = -246.0
PARK_Z = -180.0

# Reserved interior, unchanged: the rooms keep their floor at 0 and sit behind the doors
ROOMS_X = 50.0
ROOMS_Z = (-54.0, 6.0)
ROOMS_ROOF_Y = 13.0

# Central front, proportions from reference photos
BAY = 14.0              # pair centre to pair centre
PAIRS_X = (-21.0, -7.0, 7.0, 21.0)
ARCHES_X = (-14.0, 0.0, 14.0)
PAIR_GAP = 1.55         # column centre offset from the pair's centre
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
DOOR_Z = 8.8            # glazing and doors, set back in the arch
ARCH_W = 7.6
ARCH_CROWN_Y = 17.6
ARCH_SPRING_Y = ARCH_CROWN_Y - ARCH_W / 2
TRANSOM_Y = 11.9
END_BAY_X = 24.0        # the banded end bays run from here to the pavilion's corner
DOOR_W = 3.0
DOOR_H = 3.8

# Wings
WING_TOP_Y = 18.2
END_TOP_Y = 19.6
CORNICE_Y = 13.0

# Lamp standards along both curbs, clear of the view of the pavilion
LAMPS_X = (-124.0, -96.0, -72.0, -50.0, -33.0, 33.0, 50.0, 72.0, 96.0, 124.0)
LAMP_Z = 33.2
FAR_LAMPS_X = (-120.0, -75.0, -30.0, 30.0, 75.0, 120.0)
FAR_LAMP_Z = 54.4
LAMP_TOP_Y = 4.6
# Park lamps along the path round the block
PATH_LAMPS = [(sx * 159.0, z) for sx in (-1, 1) for z in (-30.0, -78.0, -126.0, -172.0)] + [(sx * x, -178.0) for sx in (-1, 1) for x in (112.0, 66.0, 22.0)] + [(sx * 112.0, -128.0) for sx in (-1, 1)]
STREET82_X = 9.0        # East 82nd Street meets the avenue square on to the steps

CHEEK_W = 0.8           # low side walls of the stairs
CHEEK_H = 0.55          # height above the line of the steps
