"""Grey blockout of the whole block, built in its own scene. Runs inside Blender."""
import importlib, math, pathlib, sys
import bmesh
import bpy

HERE = pathlib.Path(r"C:\Users\waism\AppData\Local\Temp\claude\d9410d616540b704\746404c1-ba82-4f49-96dc-c53702a1de63\scratchpad\blender")
sys.path.insert(0, str(HERE))
import ext_dims as D
importlib.reload(D)

SCENE = "ExteriorBlockout"
MATS = {
    "BO_Stone": (0.56, 0.55, 0.53),
    "BO_StoneDark": (0.42, 0.41, 0.40),
    "BO_Steps": (0.36, 0.36, 0.37),
    "BO_Glass": (0.07, 0.08, 0.10),
    "BO_Paving": (0.34, 0.335, 0.33),
    "BO_Road": (0.17, 0.17, 0.18),
    "BO_Grass": (0.27, 0.31, 0.25),
    "BO_Tree": (0.24, 0.29, 0.24),
    "BO_City": (0.33, 0.34, 0.37),
    "BO_Metal": (0.13, 0.13, 0.14),
}


class Part:
    """Collects one material's geometry. Everything comes in as Godot coordinates."""

    def __init__(self):
        self.verts, self.faces, self.smooth = [], [], []

    def add(self, verts, faces, smooth=False):
        base = len(self.verts)
        self.verts += [(x, -z, y) for x, y, z in verts]  # Godot to Blender
        for f in faces:
            self.faces.append([i + base for i in f])
            self.smooth.append(smooth)


parts = {k: Part() for k in MATS}


def box(mat, x0, x1, y0, y1, z0, z1):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    parts[mat].add(v, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])


def wedge(mat, x0, x1, y_low, y_top_a, y_top_b, z_a, z_b):
    """A solid whose top slopes from y_top_a at z_a to y_top_b at z_b."""
    v = [(x0, y_low, z_a), (x0, y_top_a, z_a), (x0, y_top_b, z_b), (x0, y_low, z_b),
         (x1, y_low, z_a), (x1, y_top_a, z_a), (x1, y_top_b, z_b), (x1, y_low, z_b)]
    parts[mat].add(v, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])


def loft(mat, x, z, rings, segs=32, smooth=True):
    """Round shape from (y, radius) rings, capped at both ends."""
    v, f = [], []
    for y, r in rings:
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((x + r * math.cos(a), y, z + r * math.sin(a)))
    for j in range(len(rings) - 1):
        for i in range(segs):
            a, b = j * segs + i, j * segs + (i + 1) % segs
            f.append((a, b, b + segs, a + segs))
    parts[mat].add(v, f, smooth)
    last = (len(rings) - 1) * segs
    parts[mat].add(v[:segs], [tuple(range(segs))], False)
    parts[mat].add(v[last:], [tuple(range(segs))], False)


def ray_rect(cx, cy, ang, x0, x1, y1):
    dx, dy = math.cos(ang), math.sin(ang)
    ts = []
    if dx > 1e-9:
        ts.append((x1 - cx) / dx)
    if dx < -1e-9:
        ts.append((x0 - cx) / dx)
    if dy > 1e-9:
        ts.append((y1 - cy) / dy)
    t = min(ts)
    return cx + t * dx, cy + t * dy


def arch_wall(mat, x0, x1, y0, y1, zf, zb, cx, half, ys, door=None, n=32):
    """A wall panel with a round-headed opening through it."""
    angs = sorted({math.pi * i / n for i in range(n + 1)} |
                  {math.atan2(y1 - ys, x1 - cx), math.atan2(y1 - ys, x0 - cx)})
    inner = [(cx + half, y0)] + [(cx + half * math.cos(a), ys + half * math.sin(a)) for a in angs] + [(cx - half, y0)]
    outer = [(x1, y0)] + [ray_rect(cx, ys, a, x0, x1, y1) for a in angs] + [(x0, y0)]
    m = len(inner)
    v, f = [], []
    for z in (zf, zb):
        v += [(x, y, z) for x, y in inner] + [(x, y, z) for x, y in outer]
    for i in range(m - 1):
        a, b = i, i + 1
        f.append((a, b, b + m, a + m))                                   # front
        f.append((a + 2 * m, a + 3 * m, b + 3 * m, b + 2 * m))           # back
        f.append((a, a + 2 * m, b + 2 * m, b))                           # inside of the arch
    parts[mat].add(v, f)


def ring(mat, cx, ys, r0, r1, z0, z1, n=32):
    """A half-round moulding, an archivolt."""
    v, f = [], []
    for i in range(n + 1):
        a = math.pi * i / n
        for r in (r0, r1):
            for z in (z0, z1):
                v.append((cx + r * math.cos(a), ys + r * math.sin(a), z))
    for i in range(n):
        p, q = i * 4, (i + 1) * 4
        f += [(p + 1, q + 1, q + 3, p + 3), (p, p + 1, q + 1, q), (p + 2, q + 2, q + 3, p + 3), (p, q, q + 2, p + 2)]
    f += [(0, 2, 3, 1), (n * 4, n * 4 + 1, n * 4 + 3, n * 4 + 2)]
    parts[mat].add(v, f)


def arched_glass(mat, cx, y0, ys, half, z, n=16):
    """Dark window or doorway shape on a wall, round at the top."""
    pts = [(cx + half, y0)] + [(cx + half * math.cos(math.pi * i / n), ys + half * math.sin(math.pi * i / n)) for i in range(n + 1)] + [(cx - half, y0)]
    parts[mat].add([(x, y, z) for x, y in pts], [tuple(range(len(pts)))])


# --- Central front ---------------------------------------------------------------------------
def central_front():
    ys = D.ARCH_CROWN_Y - D.ARCH_W / 2
    edges = [-D.PAV_X + 6.0 - 0.8, -14 + 7, 14 - 7, D.PAV_X - 6.0 + 0.8]  # x where each bay's wall panel ends
    # Bay walls, each with its arch. The doorway is cut only in the middle bay.
    arch_wall("BO_Stone", edges[0], edges[1], 0, D.COL_TOP_Y, D.WALL_Z, D.DOOR_Z, -14, D.ARCH_W / 2, ys)
    arch_wall("BO_Stone", edges[1], edges[2], 0, D.COL_TOP_Y, D.WALL_Z, D.DOOR_Z, 0, D.ARCH_W / 2, ys)
    arch_wall("BO_Stone", edges[2], edges[3], 0, D.COL_TOP_Y, D.WALL_Z, D.DOOR_Z, 14, D.ARCH_W / 2, ys)

    # What fills each arch: a dark lunette above, stone wall below, doors in the middle.
    transom = ys - 0.4
    for cx in (-14, 0, 14):
        # lunette glazing and two mullions
        arched_glass("BO_Glass", cx, transom, ys, D.ARCH_W / 2, D.DOOR_Z + 0.25)
        box("BO_StoneDark", cx - 0.95, cx - 0.65, transom, D.ARCH_CROWN_Y - 0.7, D.DOOR_Z + 0.2, D.DOOR_Z + 0.42)
        box("BO_StoneDark", cx + 0.65, cx + 0.95, transom, D.ARCH_CROWN_Y - 0.7, D.DOOR_Z + 0.2, D.DOOR_Z + 0.42)
        box("BO_StoneDark", cx - D.ARCH_W / 2, cx + D.ARCH_W / 2, transom - 0.5, transom, D.DOOR_Z + 0.2, D.DOOR_Z + 0.5)
        h = D.DOOR_H
        box("BO_Stone", cx - D.ARCH_W / 2, cx + D.ARCH_W / 2, h + 1.6, transom - 0.5, D.DOOR_Z, D.DOOR_Z + 0.2)
        box("BO_StoneDark", cx - 2.6, cx + 2.6, h, h + 1.6, D.DOOR_Z - 0.1, D.DOOR_Z + 0.35)
        box("BO_Stone", cx - D.ARCH_W / 2, cx - D.DOOR_W / 2, 0, h, D.DOOR_Z, D.DOOR_Z + 0.2)
        box("BO_Stone", cx + D.DOOR_W / 2, cx + D.ARCH_W / 2, 0, h, D.DOOR_Z, D.DOOR_Z + 0.2)
        for dx in (-2.3, -1.75, 1.75, 2.3):
            loft("BO_StoneDark", cx + dx, D.DOOR_Z + 0.42, [(0, 0.2), (h, 0.17)], 12)
        if cx:
            box("BO_Glass", cx - D.DOOR_W / 2, cx + D.DOOR_W / 2, 0, h, D.DOOR_Z + 0.02, D.DOOR_Z + 0.06)
        # two archivolt bands and the impost the arch springs from
        ring("BO_Stone", cx, ys, D.ARCH_W / 2, D.ARCH_W / 2 + 0.45, D.WALL_Z, D.WALL_Z + 0.22)
        ring("BO_Stone", cx, ys, D.ARCH_W / 2 + 0.45, D.ARCH_W / 2 + 0.75, D.WALL_Z, D.WALL_Z + 0.36)
        for sx in (-1, 1):
            xa, xb = sorted((cx + sx * D.ARCH_W / 2, cx + sx * (D.ARCH_W / 2 + 0.78)))
            box("BO_Stone", xa, xb, ys - 0.55, ys, D.WALL_Z, D.WALL_Z + 0.42)         # impost
            box("BO_Stone", xa, xb, 0, ys - 0.55, D.WALL_Z, D.WALL_Z + 0.15)          # pier strip
        # keystone with a carved head, a block for now, and the round portrait carvings either side
        box("BO_StoneDark", cx - 0.55, cx + 0.55, D.ARCH_CROWN_Y + 0.0, D.ARCH_CROWN_Y + 1.5, D.WALL_Z, D.WALL_Z + 0.75)
        for sx in (-1, 1):
            loft_x = cx + sx * 5.05
            disc(loft_x, D.ARCH_CROWN_Y - 0.35, 0.95)

    # Pedestals, flat pilasters on the wall behind, and the columns
    for px in D.PAIRS_X:
        w = D.PED_W / 2
        box("BO_Stone", px - w - 0.2, px + w + 0.2, 0, 0.55, D.PED_Z[0], D.PED_Z[1] + 0.2)    # plinth
        box("BO_Stone", px - w, px + w, 0.55, D.PED_Y - 0.45, D.PED_Z[0], D.PED_Z[1])
        box("BO_Stone", px - w - 0.15, px + w + 0.15, D.PED_Y - 0.45, D.PED_Y, D.PED_Z[0], D.PED_Z[1] + 0.15)  # cap
        for sx in (-1, 1):
            x = px + sx * D.PAIR_GAP
            column(x, D.COL_Z)
            box("BO_Stone", x - 0.72, x + 0.72, D.PED_Y, D.COL_TOP_Y, D.WALL_Z, D.WALL_Z + 0.3)   # pilaster on the wall
            box("BO_Stone", x - 1.05, x + 1.05, D.COL_TOP_Y - 1.7, D.COL_TOP_Y, D.WALL_Z, D.WALL_Z + 0.5)  # its capital

    # Banded end bays beyond the outer pairs, with one tall niche each for now
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (D.PAV_X - 5.2), sx * D.PAV_X))
        box("BO_Stone", x0, x1, 0, D.COL_TOP_Y, 8.0, D.WALL_Z + 0.5)
        for i in range(20):
            y = 0.5 + i * 0.92
            box("BO_Stone", x0 - 0.02, x1 + 0.02, y, y + 0.72, D.WALL_Z + 0.5, D.WALL_Z + 0.58)
        cx = sx * (D.PAV_X - 2.6)
        arched_glass("BO_StoneDark", cx, 3.5, 12.5, 1.25, D.WALL_Z + 0.6)

    # Entablature, with a heavy break forward over each column pair
    box("BO_Stone", -D.PAV_X, D.PAV_X, D.COL_TOP_Y, D.ENT_TOP_Y - 1.2, 8.0, D.WALL_Z + 0.6)
    box("BO_Stone", -D.PAV_X - 0.7, D.PAV_X + 0.7, D.ENT_TOP_Y - 1.2, D.ENT_TOP_Y - 0.5, 7.5, D.WALL_Z + 1.2)
    box("BO_Stone", -D.PAV_X - 1.1, D.PAV_X + 1.1, D.ENT_TOP_Y - 0.5, D.ENT_TOP_Y, 7.5, D.WALL_Z + 1.7)
    for px in D.PAIRS_X:
        w = D.PED_W / 2
        box("BO_Stone", px - w, px + w, D.COL_TOP_Y, D.ENT_TOP_Y - 1.2, D.WALL_Z, D.COL_Z + 1.25)
        box("BO_Stone", px - w - 0.55, px + w + 0.55, D.ENT_TOP_Y - 1.2, D.ENT_TOP_Y - 0.5, D.WALL_Z, D.COL_Z + 1.8)
        box("BO_Stone", px - w - 1.0, px + w + 1.0, D.ENT_TOP_Y - 0.5, D.ENT_TOP_Y, D.WALL_Z, D.COL_Z + 2.25)
        # stacked stone blocks, three stepped tiers
        tiers = [(D.ENT_TOP_Y, D.ENT_TOP_Y + 2.1, 3.7, 3.0), (D.ENT_TOP_Y + 2.1, D.ENT_TOP_Y + 4.0, 3.0, 2.3),
                 (D.ENT_TOP_Y + 4.0, D.BLOCK_TOP_Y, 2.2, 1.5)]
        for y0, y1, hw, hd in tiers:
            box("BO_StoneDark", px - hw, px + hw, y0, y1, D.COL_Z - hd, D.COL_Z + hd * 0.72)

    # Attic above the entablature, its cornice and a row of crest blocks
    box("BO_Stone", -D.PAV_X, D.PAV_X, D.ENT_TOP_Y, D.ATTIC_TOP_Y - 0.5, -4.0, D.WALL_Z - 0.4)
    box("BO_Stone", -D.PAV_X - 0.4, D.PAV_X + 0.4, D.ATTIC_TOP_Y - 0.5, D.ATTIC_TOP_Y, -4.0, D.WALL_Z + 0.2)
    n = 21
    for i in range(n):
        x = -D.PAV_X + 1.0 + i * (2 * D.PAV_X - 2.0) / (n - 1)
        box("BO_Stone", x - 0.35, x + 0.35, D.ATTIC_TOP_Y, D.CREST_Y, D.WALL_Z - 0.3, D.WALL_Z)


def disc(x, y, r, n=24):
    z = D.WALL_Z
    pts = [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    v = [(px, py, z) for px, py in pts] + [(px, py, z + 0.28) for px, py in pts]
    f = [tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    parts["BO_Stone"].add(v, f)


def column(x, z):
    y0, y1 = D.PED_Y, D.COL_TOP_Y
    cap_h = 2.1
    shaft_top = y1 - cap_h
    rings = [(y0, 1.15), (y0 + 0.28, 1.15), (y0 + 0.36, 1.05), (y0 + 0.62, 1.0), (y0 + 0.72, D.COL_R + 0.06), (y0 + 0.82, D.COL_R)]
    rings += [(y0 + 0.82 + (shaft_top - y0 - 0.82) * t,
               D.COL_R - (D.COL_R - D.COL_R_TOP) * max(0.0, (t - 0.33) / 0.67) ** 1.4) for t in (0.33, 0.55, 0.75, 0.9, 1.0)]
    rings += [(shaft_top + 0.08, D.COL_R_TOP + 0.07), (shaft_top + 0.14, D.COL_R_TOP + 0.03), (shaft_top + 0.3, 0.94),
              (shaft_top + 1.0, 1.08), (y1 - 0.34, 1.27)]
    loft("BO_Stone", x, z, rings, 32)
    box("BO_Stone", x - 1.32, x + 1.32, y1 - 0.34, y1, z - 1.32, z + 1.32)


# --- Stairs, terrace and base wall -----------------------------------------------------------
def stairs_and_base():
    run = (D.STAIR_Z_BOT - D.STAIR_Z_TOP) / D.STAIR_STEPS
    rise = (D.TERRACE_Y - D.PLAZA_Y) / D.STAIR_STEPS
    for i in range(D.STAIR_STEPS):
        y1 = D.TERRACE_Y - i * rise
        box("BO_Steps", -D.STAIR_X, D.STAIR_X, D.PLAZA_Y, y1, D.STAIR_Z_TOP + i * run, D.STAIR_Z_TOP + (i + 1) * run)
    # Cheek walls climbing beside the stairs
    for sx in (-1, 1):
        x0, x1 = sorted((sx * D.STAIR_X, sx * (D.STAIR_X + D.CHEEK_W)))
        wedge("BO_Stone", x0, x1, D.PLAZA_Y, D.CHEEK_H, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_TOP, D.STAIR_Z_BOT)
    # Terrace: stone floor from the doors to the top step, across the whole pavilion
    box("BO_Paving", -D.PAV_X, D.PAV_X, D.PLAZA_Y, D.TERRACE_Y, 6.0, D.TERRACE_Z_FRONT)
    # Base wall under the outer terraces, with a heavy moulding on top and a railing above
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (D.STAIR_X + D.CHEEK_W), sx * D.PAV_X))
        box("BO_Stone", x0, x1, D.PLAZA_Y, -3.7, D.TERRACE_Z_FRONT, D.TERRACE_Z_FRONT + 0.5)
        box("BO_Stone", x0, x1, -0.55, 0.0, D.TERRACE_Z_FRONT - 0.1, D.TERRACE_Z_FRONT + 0.3)
        xr0, xr1 = sorted((sx * (D.STAIR_X + D.CHEEK_W), sx * (D.PAV_X - 0.2)))
        box("BO_Metal", xr0, xr1, 1.02, 1.12, D.TERRACE_Z_FRONT - 0.3, D.TERRACE_Z_FRONT - 0.24)
        for i in range(int((xr1 - xr0) / 1.8) + 1):
            x = xr0 + i * 1.8
            box("BO_Metal", x, x + 0.06, 0, 1.05, D.TERRACE_Z_FRONT - 0.3, D.TERRACE_Z_FRONT - 0.24)


# --- Wings, sides and back -------------------------------------------------------------------
def wing_windows(x_list, z, y0, ys, half, facing):
    """Tall round-headed windows along a wall, with a raised surround."""
    d = 0.02 * facing
    for x in x_list:
        arched_glass("BO_Glass", x, y0, ys, half, z + d * 6)
        box("BO_Stone", x - half - 0.42, x + half + 0.42, y0 - 0.5, y0, z, z + 0.3 * facing) if facing > 0 else box("BO_Stone", x - half - 0.42, x + half + 0.42, y0 - 0.5, y0, z - 0.3, z)


def wings_and_shell():
    F = D.BLD_Z_FRONT
    for sx in (-1, 1):
        x0, x1 = sorted((sx * D.PAV_X, sx * D.BLD_X))
        # solid wing masses, kept clear of the reserved rooms
        box("BO_Stone", x0, x1, D.PLAZA_Y, D.WING_TOP_Y, 6.0, F)
        box("BO_StoneDark", x0, x1, D.PLAZA_Y, -3.9, F, F + 0.5)                   # base course
        box("BO_Stone", x0, x1, -0.5, 0.0, F, F + 0.45)                            # water table
        box("BO_Stone", x0, x1, 12.6, 13.4, F, F + 0.8)                            # main cornice
        box("BO_Stone", x0 - sx * 0.0, x1, D.WING_TOP_Y - 0.6, D.WING_TOP_Y, F, F + 0.6)
        xs = [sx * (D.PAV_X + 5.0 + i * 8.6) for i in range(5)]
        wing_windows(xs, F, 1.8, 8.4, 1.6, 1)
        for x in xs:
            box("BO_Glass", x - 1.0, x + 1.0, -3.0, -1.2, F, F + 0.03)            # small barred basement window
            box("BO_Stone", x - 2.2, x + 2.2, 14.4, 17.0, F, F + 0.12)            # upper panel
            ring("BO_Stone", x, 8.4, 1.6, 2.05, F, F + 0.3)
        # end pavilions, standing a little forward
        xa, xb = sorted((sx * (D.BLD_X - 12.5), sx * D.BLD_X))
        box("BO_Stone", xa, xb, D.PLAZA_Y, D.WING_TOP_Y + 1.2, F, F + 1.6)
        box("BO_Stone", xa - 0.5, xb + 0.5, D.WING_TOP_Y + 0.5, D.WING_TOP_Y + 1.2, F, F + 2.1)
        # the side of the building
        side_x0, side_x1 = sorted((sx * D.ROOMS_X, sx * D.BLD_X))
        box("BO_Stone", side_x0, side_x1, D.PLAZA_Y, D.WING_TOP_Y, D.BLD_Z_BACK, 6.0)
        n = sx
        for i in range(8):
            z = -62.0 + i * 9.5
            arched_glass_side(sx * D.BLD_X + sx * 0.02, z, 2.0, 8.4, 1.5, sx)
        box("BO_Stone", *sorted((sx * D.BLD_X, sx * (D.BLD_X + 0.7))), 12.6, 13.4, D.BLD_Z_BACK, F)
        box("BO_StoneDark", *sorted((sx * D.BLD_X, sx * (D.BLD_X + 0.5))), D.PLAZA_Y, -3.9, D.BLD_Z_BACK, F)
    # Back wall and the glass wall facing the park
    box("BO_Stone", -D.ROOMS_X, D.ROOMS_X, D.PLAZA_Y, D.WING_TOP_Y, D.BLD_Z_BACK, D.ROOMS_Z[0])
    box("BO_Glass", -46, 46, -3.5, 12.0, D.BLD_Z_BACK - 0.05, D.BLD_Z_BACK + 0.0)
    for i in range(24):
        x = -46 + i * 4.0
        box("BO_Metal", x, x + 0.18, -3.5, 12.0, D.BLD_Z_BACK - 0.25, D.BLD_Z_BACK)
    box("BO_Metal", -46, 46, 11.8, 12.2, D.BLD_Z_BACK - 0.3, D.BLD_Z_BACK)
    # Roof over the reserved rooms; nothing else fills that space
    box("BO_StoneDark", -D.ROOMS_X - 1, D.ROOMS_X + 1, D.ROOMS_ROOF_Y, D.ROOMS_ROOF_Y + 1.0, D.ROOMS_Z[0] - 1, 8.0)
    box("BO_StoneDark", -D.ROOMS_X, D.ROOMS_X, D.ROOMS_ROOF_Y + 1.0, D.WING_TOP_Y - 3.0, -50.0, -4.0)
    # Front wall between the pavilion and the rooms, leaving the vestibule open
    # Loading dock on the west side
    box("BO_StoneDark", -D.BLD_X - 4.0, -D.BLD_X, D.PLAZA_Y, -3.2, -24.6, -16.0)
    box("BO_Glass", -D.BLD_X - 0.05, -D.BLD_X, D.PLAZA_Y, 0.2, -24.2, -16.4)
    box("BO_StoneDark", -D.BLD_X - 5.0, -D.BLD_X, 0.2, 0.6, -25.0, -15.6)


def arched_glass_side(x, zc, y0, ys, half, sx, n=12):
    pts = [(zc + half, y0)] + [(zc + half * math.cos(math.pi * i / n), ys + half * math.sin(math.pi * i / n)) for i in range(n + 1)] + [(zc - half, y0)]
    parts["BO_Glass"].add([(x, y, z) for z, y in pts], [tuple(range(len(pts)))])


# --- Plaza, street, park and city ------------------------------------------------------------
def tree(x, z, y=D.PLAZA_Y, h=9.0, r=3.4):
    loft("BO_Metal", x, z, [(y, 0.28), (y + h * 0.5, 0.2)], 10)
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=2, radius=1.0)
    verts = [(x + v.co.x * r, y + h * 0.66 + v.co.z * r * 1.1, z + v.co.y * r) for v in ico.verts]
    faces = [[v.index for v in f.verts] for f in ico.faces]
    ico.free()
    parts["BO_Tree"].add(verts, faces, False)


def lamp(x, z):
    loft("BO_Metal", x, z, [(D.PLAZA_Y, 0.16), (D.PLAZA_Y + 0.5, 0.12), (D.PLAZA_Y + 5.6, 0.07)], 10)
    box("BO_Metal", x - 0.28, x + 0.28, D.PLAZA_Y + 5.6, D.PLAZA_Y + 6.3, z - 0.28, z + 0.28)


def site():
    P = D.PLAZA_Y
    # Ground: thin slabs, one per surface
    box("BO_Paving", -D.BLD_X - 45, D.BLD_X + 45, P - 0.5, P, D.PARK_Z_END, D.STAIR_Z_BOT)   # ring around the building
    box("BO_Paving", -D.BLD_X - 45, D.BLD_X + 45, P - 0.5, P, D.STAIR_Z_BOT, D.PLAZA_Z_END)  # plaza
    box("BO_Paving", -D.BLD_X - 45, D.BLD_X + 45, P - 0.5, P + 0.0, D.PLAZA_Z_END, D.SIDEWALK_Z_END)
    box("BO_Road", -220, 220, P - 0.5, D.ROAD_Y, D.SIDEWALK_Z_END, D.ROAD_Z_END)
    box("BO_Paving", -220, 220, P - 0.5, P, D.ROAD_Z_END, D.FAR_WALK_Z_END)
    box("BO_Grass", -D.BLD_X - 45, D.BLD_X + 45, P - 0.45, P + 0.02, D.PARK_Z_FAR, D.PARK_Z_END)
    box("BO_Grass", -D.BLD_X - 45, -D.RING_X - 4, P - 0.45, P + 0.02, D.PARK_Z_END, D.PLAZA_Z_END - 10)
    box("BO_Grass", D.RING_X + 4, D.BLD_X + 45, P - 0.45, P + 0.02, D.PARK_Z_END, D.PLAZA_Z_END - 10)

    # Fountains: a low round rim for now
    for sx in (-1, 1):
        x = sx * D.FOUNTAIN_X
        loft("BO_Stone", x, D.FOUNTAIN_Z, [(P, D.FOUNTAIN_R), (P + 0.55, D.FOUNTAIN_R)], 48)
        loft("BO_Glass", x, D.FOUNTAIN_Z, [(P + 0.55, D.FOUNTAIN_R - 0.45), (P + 0.56, D.FOUNTAIN_R - 0.45)], 48)
        loft("BO_Stone", x, D.FOUNTAIN_Z, [(P + 0.55, 1.2), (P + 1.5, 0.9), (P + 1.8, 0.35)], 16)
        for tx in D.TREE_X:
            for tz in D.TREE_Z:
                tree(sx * tx, tz)
        # benches and planters
        for i in range(4):
            x2 = sx * (19.0 + i * 5.2)
            box("BO_StoneDark", *sorted((x2 - 1.1, x2 + 1.1)), P, P + 0.48, 27.5, 28.2)
            box("BO_Stone", *sorted((x2 - 1.4, x2 + 1.4)), P, P + 0.9, 44.3, 45.6)
        for lz in (29.0, 46.0):
            lamp(sx * 30.0, lz)
        lamp(sx * 58.0, 46.0)

    # Parked taxi and van stand-ins at the curb, for scale
    box("BO_StoneDark", -2.8, 2.8, D.ROAD_Y, D.ROAD_Y + 2.5, 51.4, 53.9)                 # van stand-in
    box("BO_StoneDark", 16.0, 20.5, D.ROAD_Y, D.ROAD_Y + 1.5, 51.4, 53.2)                # taxi stand-in

    # Rows of street trees on the side paths and a stand of park trees
    for sx in (-1, 1):
        for i in range(8):
            tree(sx * (D.RING_X + 8.5), -68.0 + i * 12.5, h=10.0)
    for i in range(13):
        for j in range(3):
            tree(-96 + i * 16 + (j % 2) * 6, D.PARK_Z_END - 8 - j * 11, h=12.0 - (i + j) % 3, r=4.6)

    # Lots of plain city across the street, near and far
    blocks = [(-175, -120, 62), (-115, -88, 38), (-84, -40, 48), (-36, -10, 34), (-6, 38, 54), (42, 70, 36), (74, 120, 66), (125, 180, 44)]
    for x0, x1, h in blocks:
        box("BO_City", x0, x1, D.PLAZA_Y, D.PLAZA_Y + h, D.FAR_WALK_Z_END + 0.5, D.FAR_WALK_Z_END + 40)
    far = [(-260, -180, 95), (-170, -95, 130), (-90, -10, 105), (0, 90, 150), (100, 190, 110), (200, 280, 125)]
    for x0, x1, h in far:
        box("BO_City", x0, x1, D.PLAZA_Y, D.PLAZA_Y + h, 170, 230)


def build():
    scene = bpy.data.scenes.get(SCENE) or bpy.data.scenes.new(SCENE)
    win = bpy.context.window
    win.scene = scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for name, col in MATS.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = 0.9
    central_front()
    stairs_and_base()
    wings_and_shell()
    site()
    total = 0
    for name, part in parts.items():
        if not part.faces:
            continue
        mesh_name = name.replace("BO_", "Blockout_")
        for old_me in [m for m in bpy.data.meshes if m.name.startswith(mesh_name)]:
            bpy.data.meshes.remove(old_me)
        me = bpy.data.meshes.new(mesh_name)
        me.from_pydata(part.verts, [], part.faces)
        me.update()
        me.polygons.foreach_set("use_smooth", part.smooth)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set("use_smooth", part.smooth)
        me.materials.append(bpy.data.materials[name])
        me.update()
        ob = bpy.data.objects.new(me.name, me)
        scene.collection.objects.link(ob)
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        total += tris
        print(me.name, "tris", tris)
    print("TOTAL tris", total)


build()
