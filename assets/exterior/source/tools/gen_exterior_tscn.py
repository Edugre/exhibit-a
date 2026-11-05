"""Writes scenes/exterior.tscn: the blockout model plus simple hand-sized collision, from ext_dims.py.
The stairs are a smooth ramp under the visible steps, because the player can't climb step edges."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ext_dims as D

OUT = pathlib.Path(r"C:\Users\waism\Downloads\exhibit-a\.claude\worktrees\agitated-benz-0e18d0\scenes\exterior.tscn")

subs, nodes = [], []


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def add_shape(kind, body, node_name, pos=(0, 0, 0)):
    sid = f"Shape_{len(subs)}"
    subs.append(f'[sub_resource type="{kind[0]}" id="{sid}"]\n{kind[1]}\n')
    nodes.append(f'[node name="{node_name}" type="CollisionShape3D" parent="{body}"]\n'
                 f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {fmt(pos[0])}, {fmt(pos[1])}, {fmt(pos[2])})\n'
                 f'shape = SubResource("{sid}")\n')


def box(body, name, x0, x1, y0, y1, z0, z1):
    size = f"size = Vector3({fmt(x1 - x0)}, {fmt(y1 - y0)}, {fmt(z1 - z0)})"
    add_shape(("BoxShape3D", size), body, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(body, name, x, z, y0, y1, r):
    add_shape(("CylinderShape3D", f"height = {fmt(y1 - y0)}\nradius = {fmt(r)}"), body, name, (x, (y0 + y1) / 2, z))


def wedge(body, name, x0, x1, y_low, y_a, y_b, z_a, z_b):
    pts = []
    for x in (x0, x1):
        pts += [x, y_low, z_a, x, y_a, z_a, x, y_b, z_b, x, y_low, z_b]
    arr = ", ".join(fmt(p) for p in pts)
    add_shape(("ConvexPolygonShape3D", f"points = PackedVector3Array({arr})"), body, name)


def markers():
    out = ['[node name="Markers" type="Node3D" parent="."]\n']
    spots = {
        "PlayerStart1": (-1.5, D.PLAZA_Y, 44.0),
        "PlayerStart2": (1.5, D.PLAZA_Y, 44.0),
        "FrontDoor": (0, D.TERRACE_Y, 8.8),
        "VanCurb": (0, D.ROAD_Y, 52.65),
        "RoomsMin": (-D.ROOMS_X, D.TERRACE_Y, D.ROOMS_Z[0]),
        "RoomsMax": (D.ROOMS_X, D.ROOMS_ROOF_Y, D.ROOMS_Z[1]),
    }
    for name, (x, y, z) in spots.items():
        out.append(f'[node name="{name}" type="Marker3D" parent="Markers"]\n'
                   f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {fmt(x)}, {fmt(y)}, {fmt(z)})\n')
    return out


G = "Collision/Ground"
B = "Collision/Building"
P = "Collision/Props"
E = "Collision/Edges"
LOW = -5.5

# Ground
box(G, "Paving", -140, 140, LOW, D.PLAZA_Y, D.BOUND_Z_N - 12, D.SIDEWALK_Z_END)
box(G, "Road", -140, 140, LOW, D.ROAD_Y, D.SIDEWALK_Z_END, D.ROAD_Z_END)
box(G, "FarWalk", -140, 140, LOW, D.PLAZA_Y, D.ROAD_Z_END, D.BOUND_Z_S + 6)
wedge(G, "CurbNear", -140, 140, D.ROAD_Y - 0.5, D.PLAZA_Y, D.ROAD_Y, D.SIDEWALK_Z_END, D.SIDEWALK_Z_END + 0.8)
wedge(G, "CurbFar", -140, 140, D.ROAD_Y - 0.5, D.ROAD_Y, D.PLAZA_Y, D.ROAD_Z_END - 0.8, D.ROAD_Z_END)

# Stairs: a smooth ramp, and the low side walls
wedge(B, "StairRamp", -D.STAIR_X, D.STAIR_X, LOW, D.TERRACE_Y, D.PLAZA_Y, D.STAIR_Z_TOP, D.STAIR_Z_BOT)
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * D.STAIR_X, sx * (D.STAIR_X + D.CHEEK_W)))
    wedge(B, "StairWall" + name, x0, x1, LOW, D.CHEEK_H, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_TOP, D.STAIR_Z_BOT)

# Terrace and the base wall under the outer terraces
box(B, "Terrace", -D.PAV_X, D.PAV_X, LOW, D.TERRACE_Y, 6.0, D.TERRACE_Z_FRONT)
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * (D.STAIR_X + D.CHEEK_W), sx * D.PAV_X))
    box(B, "BaseCourse" + name, x0, x1, LOW, -3.7, D.TERRACE_Z_FRONT, D.TERRACE_Z_FRONT + 0.5)
    box(B, "Railing" + name, x0, x1, 0, 1.12, D.TERRACE_Z_FRONT - 0.32, D.TERRACE_Z_FRONT - 0.22)

# Pedestals, and one tall box per column pair so throws can't pass through
for i, px in enumerate(D.PAIRS_X):
    w = D.PED_W / 2 + 0.2
    box(B, f"Pedestal{i}", px - w, px + w, 0, D.PED_Y, D.PED_Z[0], D.PED_Z[1] + 0.2)
    box(B, f"ColumnPair{i}", px - 2.4, px + 2.4, D.PED_Y, D.COL_TOP_Y, D.COL_Z - 0.85, D.COL_Z + 0.85)

# The arched wall: piers at full depth, the back of each arch, and the doorway through the middle bay
half = D.ARCH_W / 2
for i, cx in enumerate((-14, 0, 14)):
    if cx:
        box(B, f"ArchBack{i}", cx - half, cx + half, 0, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
    else:
        box(B, "ArchBackW", -half, -D.DOOR_W / 2, 0, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
        box(B, "ArchBackE", D.DOOR_W / 2, half, 0, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
        box(B, "OverDoor", -D.DOOR_W / 2, D.DOOR_W / 2, D.DOOR_H, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
pier_x = [(-23.8, -17.9), (-10.1, -3.9), (3.9, 10.1), (17.9, 23.8)]
for i, (x0, x1) in enumerate(pier_x):
    box(B, f"Pier{i}", x0, x1, 0, D.COL_TOP_Y, 8.5, D.WALL_Z)
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * 23.8, sx * D.PAV_X))
    box(B, "EndBay" + name, x0, x1, 0, D.COL_TOP_Y, 8.0, D.WALL_Z + 0.58)

# Vestibule from the doors to the rooms: side walls and a ceiling
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * D.DOOR_W / 2, sx * (D.DOOR_W / 2 + 0.5)))
    box(B, "Vestibule" + name, x0, x1, 0, 4.4, 6.0, 8.5)
box(B, "VestibuleCeiling", -2.0, 2.0, 4.0, 4.4, 6.0, 8.5)

# Wings, sides, back, roof over the reserved rooms, loading dock
F = D.BLD_Z_FRONT
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * D.PAV_X, sx * D.BLD_X))
    box(B, "Wing" + name, x0, x1, LOW, D.WING_TOP_Y, 6.0, F)
    box(B, "WingBase" + name, x0, x1, LOW, -3.9, F, F + 0.5)
    xa, xb = sorted((sx * (D.BLD_X - 12.5), sx * D.BLD_X))
    box(B, "EndPavilion" + name, xa, xb, LOW, D.WING_TOP_Y + 1.2, F, F + 1.6)
    side_x0, side_x1 = sorted((sx * D.ROOMS_X, sx * D.BLD_X))
    box(B, "Side" + name, side_x0, side_x1, LOW, D.WING_TOP_Y, D.BLD_Z_BACK, 6.0)
    px0, px1 = sorted((sx * D.BLD_X, sx * (D.BLD_X + 0.5)))
    box(B, "SideBase" + name, px0, px1, LOW, -3.9, D.BLD_Z_BACK, F)
box(B, "Back", -D.ROOMS_X, D.ROOMS_X, LOW, D.WING_TOP_Y, D.BLD_Z_BACK, D.ROOMS_Z[0])
box(B, "RoomsRoof", -D.ROOMS_X - 1, D.ROOMS_X + 1, D.ROOMS_ROOF_Y, D.ROOMS_ROOF_Y + 1, D.ROOMS_Z[0] - 1, 8.0)
box(B, "LoadingDock", -D.BLD_X - 4, -D.BLD_X, LOW, -3.2, -24.6, -16.0)

# Props
for sx in (-1, 1):
    tag = "W" if sx < 0 else "E"
    cyl(P, "Fountain" + tag, sx * D.FOUNTAIN_X, D.FOUNTAIN_Z, D.PLAZA_Y - 0.5, D.PLAZA_Y + 0.55, D.FOUNTAIN_R)
    n = 0
    for tx in D.TREE_X:
        for tz in D.TREE_Z:
            cyl(P, f"Tree{tag}{n}", sx * tx, tz, D.PLAZA_Y, D.PLAZA_Y + 5, 0.3)
            n += 1
    for i in range(4):
        x = sx * (19.0 + i * 5.2)
        box(P, f"Bench{tag}{i}", x - 1.1, x + 1.1, D.PLAZA_Y, D.PLAZA_Y + 0.48, 27.5, 28.2)
        box(P, f"Planter{tag}{i}", x - 1.4, x + 1.4, D.PLAZA_Y, D.PLAZA_Y + 0.9, 44.3, 45.6)
    for j, (lx, lz) in enumerate(((30.0, 29.0), (30.0, 46.0), (58.0, 46.0))):
        cyl(P, f"Lamp{tag}{j}", sx * lx, lz, D.PLAZA_Y, D.PLAZA_Y + 6.3, 0.16)
    for i in range(8):
        cyl(P, f"StreetTree{tag}{i}", sx * (D.RING_X + 8.5), -68.0 + i * 12.5, D.PLAZA_Y, D.PLAZA_Y + 5, 0.3)
box(P, "VanStandIn", -2.8, 2.8, D.ROAD_Y, D.ROAD_Y + 2.5, 51.4, 53.9)
box(P, "TaxiStandIn", 16.0, 20.5, D.ROAD_Y, D.ROAD_Y + 1.5, 51.4, 53.2)

# Invisible edges of the walkable block
box(E, "West", -D.BOUND_X - 1, -D.BOUND_X, LOW, 12, D.BOUND_Z_N, D.BOUND_Z_S)
box(E, "East", D.BOUND_X, D.BOUND_X + 1, LOW, 12, D.BOUND_Z_N, D.BOUND_Z_S)
box(E, "North", -D.BOUND_X, D.BOUND_X, LOW, 12, D.BOUND_Z_N - 1, D.BOUND_Z_N)
box(E, "South", -D.BOUND_X, D.BOUND_X, LOW, 12, D.BOUND_Z_S, D.BOUND_Z_S + 1)

head = ['[gd_scene format=3]\n',
        '[ext_resource type="PackedScene" path="res://assets/exterior/exterior_blockout.glb" id="1_blockout"]\n']
body = ['[node name="Exterior" type="Node3D"]\n',
        '[node name="Blockout" parent="." instance=ExtResource("1_blockout")]\n',
        '[node name="Collision" type="Node3D" parent="."]\n']
for n in ("Ground", "Building", "Props", "Edges"):
    body.append(f'[node name="{n}" type="StaticBody3D" parent="Collision"]\n')
text = "\n".join(head + subs + body + nodes + markers())
OUT.write_text(text, encoding="utf-8", newline="\n")
print("wrote", OUT, len(subs), "shapes", len(text), "bytes")
