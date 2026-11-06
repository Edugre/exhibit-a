"""Background Blender job: the street. Benches, the Ambrosia cart, signals, signs, bins, a hydrant, a news
box, flagpoles, planters and the plan's joke signs, all in one texture, plus the cars. Props are written
at their real places, split by side of the plaza; cars go in their own file at the origin, nose towards
negative x, because they move. usage: blender -b --factory-startup --python props_build.py -- <out dir>"""
import importlib
import json
import math
import pathlib
import sys
import bmesh
import bpy

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import ext_dims as D
importlib.reload(D)

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1])
ART = json.load(open(HERE / "props_layout.json"))
SITE = json.load(open(HERE / "site.json"))
TAU = 2 * math.pi


class Mesh:
    def __init__(self):
        self.v, self.f, self.uv = [], [], []

    def add(self, pts, faces, uv):
        b = len(self.v)
        self.v += [(x, -z, y) for x, y, z in pts]
        self.uv += uv
        self.f += [tuple(i + b for i in q) for q in faces]


class Prop:
    """A thing standing somewhere, facing somewhere. Local x is its width, z its front."""

    def __init__(self, mesh, x=0.0, y=0.0, z=0.0, yaw=0.0):
        self.m, self.o = mesh, (x, y, z)
        a = math.radians(yaw)
        self.c, self.s = math.cos(a), math.sin(a)

    def T(self, p):
        x, y, z = p
        return (self.o[0] + x * self.c + z * self.s, self.o[1] + y, self.o[2] - x * self.s + z * self.c)

    def box(self, cx, cy, cz, sx, sy, sz, col):
        u = ART["colours"][col]
        v = [self.T((cx + a * sx / 2, cy + b * sy / 2, cz + c * sz / 2)) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        self.m.add(v, faces, [u] * 8)

    def lathe(self, cx, cz, rings, col, segs=10):
        """rings are (y, r), bottom to top; closed at both ends."""
        u = ART["colours"][col]
        v = []
        for y, r in rings:
            for i in range(segs):
                a = TAU * i / segs
                v.append(self.T((cx + r * math.cos(a), y, cz - r * math.sin(a))))
        f = []
        for j in range(len(rings) - 1):
            for i in range(segs):
                a, b = j * segs + i, j * segs + (i + 1) % segs
                f.append((a, b, b + segs, a + segs))
        f.append(tuple(range(segs - 1, -1, -1)))
        f.append(tuple(range((len(rings) - 1) * segs, len(rings) * segs)))
        self.m.add(v, f, [u] * len(v))

    def wheel(self, cx, cy, cz, r, w, col, axis="z", segs=12):
        u = ART["colours"][col]
        v = []
        for side in (-1, 1):
            for i in range(segs):
                a = TAU * i / segs
                p, q = r * math.cos(a), r * math.sin(a)
                v.append(self.T((cx + p, cy + q, cz + side * w / 2) if axis == "z" else (cx + side * w / 2, cy + q, cz + p)))
        f = [(i, (i + 1) % segs, segs + (i + 1) % segs, segs + i) for i in range(segs)]
        f += [tuple(range(segs - 1, -1, -1)), tuple(range(segs, 2 * segs))]
        self.m.add(v, f, [u] * len(v))

    def sign(self, cx, cy, cz, w, h, name, yaw=0.0):
        """A printed panel, facing local +z, turned about y if asked."""
        u0, v0, u1, v1 = ART["signs"][name]
        a = math.radians(yaw)
        c, s = math.cos(a), math.sin(a)
        pts = []
        for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            pts.append(self.T((cx + px * c, cy + py, cz - px * s)))
        self.m.add(pts, [(0, 1, 2, 3)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def loft(self, stations, col):
        """Cross sections along local x: each is (x, half width, y bottom, y top), with eased shoulders."""
        u = ART["colours"][col]
        v = []
        for x, w, y0, y1 in stations:
            k = min(0.12, (y1 - y0) * 0.3)
            for z, y in ((-w + k, y0), (w - k, y0), (w, y0 + k), (w, y1 - k), (w - k, y1), (-w + k, y1), (-w, y1 - k), (-w, y0 + k)):
                v.append(self.T((x, y, z)))
        n = 8
        f = []
        for j in range(len(stations) - 1):
            for i in range(n):
                a, b = j * n + i, j * n + (i + 1) % n
                f.append((a, a + n, b + n, b))
        f.append(tuple(range(n)))
        f.append(tuple(range(len(stations) * n - 1, (len(stations) - 1) * n - 1, -1)))
        self.m.add(v, f, [u] * len(v))


# --- Street furniture -------------------------------------------------------------------------------
def bench(m, x, z, yaw=0.0):
    p = Prop(m, x, D.PLAZA_Y, z, yaw)
    for dx in (-0.82, 0.82):
        p.box(dx, 0.23, 0.0, 0.34, 0.46, 0.5, "granite")
    for i in range(4):
        p.box(0, 0.47, -0.2 + i * 0.135, 2.4, 0.05, 0.11, "wood")
    for dx in (-0.82, 0.82):
        p.box(dx, 0.7, -0.27, 0.08, 0.46, 0.06, "iron")
    for i in range(3):
        p.box(0, 0.62 + i * 0.13, -0.3, 2.4, 0.09, 0.04, "wood")


def bin_(m, x, z):
    p = Prop(m, x, D.PLAZA_Y, z)
    p.lathe(0, 0, [(0.0, 0.26), (0.05, 0.3), (0.9, 0.32), (0.94, 0.34), (1.0, 0.3)], "iron", 10)


def hydrant(m, x, z):
    p = Prop(m, x, D.PLAZA_Y, z)
    p.lathe(0, 0, [(0.0, 0.17), (0.06, 0.17), (0.08, 0.11), (0.56, 0.11), (0.6, 0.15), (0.64, 0.15), (0.76, 0.09), (0.84, 0.03)], "red", 10)
    p.wheel(0.0, 0.42, 0.0, 0.055, 0.34, "red", axis="x", segs=8)
    p.wheel(0.0, 0.42, 0.0, 0.07, 0.04, "steel", axis="z", segs=8)


def news_box(m, x, z, yaw):
    p = Prop(m, x, D.PLAZA_Y, z, yaw)
    for dx in (-0.2, 0.2):
        for dz in (-0.17, 0.17):
            p.box(dx, 0.2, dz, 0.04, 0.4, 0.04, "iron")
    p.box(0, 0.74, 0, 0.5, 0.72, 0.42, "navy")
    p.box(0, 1.14, 0, 0.54, 0.08, 0.46, "navy")
    p.sign(0, 0.8, 0.235, 0.4, 0.5, "newspaper")


def flagpole(m, x, z):
    p = Prop(m, x, D.PLAZA_Y, z)
    p.lathe(0, 0, [(0.0, 0.5), (0.3, 0.5), (0.34, 0.34), (0.8, 0.3), (0.84, 0.16), (9.0, 0.1), (20.0, 0.055), (20.1, 0.12), (20.25, 0.1), (20.3, 0.02)], "iron", 10)


def planter(m, x, z, w=2.6):
    p = Prop(m, x, D.PLAZA_Y, z)
    p.box(0, 0.32, 0, w, 0.64, 1.1, "granite")
    p.box(0, 0.67, 0, w + 0.08, 0.06, 1.18, "pale")
    p.box(0, 0.74, 0, w - 0.2, 0.1, 0.9, "black")
    for i in range(int(w / 0.5)):
        dx = -w / 2 + 0.32 + i * 0.5
        p.lathe(dx, (i % 2) * 0.16 - 0.08, [(0.76, 0.22), (0.98, 0.3), (1.2, 0.18), (1.26, 0.04)], "hedge", 7)


def street_sign_pole(m, x, z, yaw):
    p = Prop(m, x, D.PLAZA_Y, z, yaw)
    p.lathe(0, 0, [(0.0, 0.1), (0.12, 0.09), (0.16, 0.05), (3.5, 0.04)], "iron", 7)
    p.box(0, 3.42, 0.0, 1.05, 0.26, 0.02, "sign_green")
    p.sign(0, 3.42, 0.03, 1.0, 0.25, "street_5av")
    p.sign(0, 3.42, -0.03, 1.0, 0.25, "street_5av", yaw=180)
    p.box(0, 3.14, 0.0, 0.02, 0.26, 1.05, "sign_green")
    p.sign(0.03, 3.14, 0, 1.0, 0.25, "street_82", yaw=90)
    p.sign(-0.03, 3.14, 0, 1.0, 0.25, "street_82", yaw=-90)


def signal_pole(m, x, z, yaw, arm):
    """A mast with a signal head for the traffic and a small box for walkers. The lamps themselves are
    separate nodes, so the traffic script can switch them."""
    p = Prop(m, x, D.PLAZA_Y, z, yaw)
    p.lathe(0, 0, [(0.0, 0.2), (0.2, 0.18), (0.3, 0.1), (6.2, 0.075)], "iron", 8)
    p.box(arm / 2, 5.9, 0, arm, 0.1, 0.1, "iron")
    p.box(arm, 5.28, 0, 0.36, 1.14, 0.3, "iron")
    for i in range(3):
        p.wheel(arm, 5.65 - i * 0.37, 0.165, 0.13, 0.03, "black", axis="z", segs=10)
    p.box(0.2 if arm < 0 else -0.2, 2.9, 0.0, 0.2, 0.34, 0.34, "iron")


def cart(m, x, z, yaw):
    """AMBROSIA: a steel cart under a striped umbrella, lit for the night shift."""
    p = Prop(m, x, D.PLAZA_Y, z, yaw)
    p.wheel(-0.7, 0.26, 0.56, 0.26, 0.09, "rubber")
    p.wheel(-0.7, 0.26, -0.56, 0.26, 0.09, "rubber")
    p.wheel(-0.7, 0.26, 0.56, 0.13, 0.11, "chrome")
    p.wheel(-0.7, 0.26, -0.56, 0.13, 0.11, "chrome")
    p.box(0.92, 0.25, 0, 0.1, 0.5, 0.1, "iron")
    p.box(0, 0.86, 0, 2.0, 0.82, 1.04, "steel")
    p.box(0, 1.3, 0, 2.08, 0.06, 1.12, "chrome")
    p.sign(0, 0.86, 0.545, 1.76, 0.44, "ambrosia_side")
    p.sign(0, 0.86, -0.545, 1.76, 0.44, "ambrosia_side", yaw=180)
    p.sign(1.025, 0.92, 0, 0.72, 0.54, "ambrosia_menu", yaw=90)
    # Grill, buns, a jar of mustard, a bottle of nectar
    p.box(-0.45, 1.36, 0, 0.8, 0.06, 0.74, "iron")
    for i in range(4):
        p.wheel(-0.62 + i * 0.12, 1.42, 0.0, 0.03, 0.44, "maroon", axis="z", segs=6)
    p.lathe(0.4, 0.2, [(1.33, 0.07), (1.5, 0.07), (1.53, 0.03), (1.6, 0.03)], "taxi", 7)
    p.lathe(0.55, -0.1, [(1.33, 0.08), (1.48, 0.08), (1.6, 0.03), (1.66, 0.03)], "chrome", 7)
    # Pole and umbrella
    p.lathe(0.86, 0, [(1.33, 0.03), (2.9, 0.03)], "chrome", 6)
    rim = 1.45
    apex = (0.0, 3.05, 0.0)
    n = 12
    for i in range(n):
        a0, a1 = TAU * i / n, TAU * (i + 1) / n
        col = "awning_red" if i % 2 == 0 else "awning_cream"
        u = ART["colours"][col]
        q0 = (0.1 + rim * math.cos(a0), 2.42, rim * math.sin(a0))
        q1 = (0.1 + rim * math.cos(a1), 2.42, rim * math.sin(a1))
        top = p.T((0.1, apex[1], 0.0))
        m.add([p.T(q0), p.T(q1), top], [(0, 2, 1)], [u] * 3)
        m.add([p.T(q0), p.T(q1), top], [(0, 1, 2)], [u] * 3)
    # String of little bulbs under the rim
    for i in range(12):
        a = TAU * i / 12
        p.lathe(0.1 + 1.36 * math.cos(a), 1.36 * math.sin(a), [(2.33, 0.012), (2.37, 0.03), (2.42, 0.012)], "bulb", 5)


# --- The cars ---------------------------------------------------------------------------------------
def car_body(m, body, kind):
    p = Prop(m)
    L, W = 2.42, 0.92
    if kind == "van":
        p.loft([(-2.5, 0.92, 0.32, 0.9), (-2.1, 0.96, 0.3, 1.16), (-1.5, 0.98, 0.3, 2.0), (2.4, 0.98, 0.3, 2.12), (2.5, 0.92, 0.34, 2.06)], body)
        p.box(-1.86, 1.5, 0, 0.5, 0.62, 1.82, "glass")
    else:
        p.loft([(-L, 0.84, 0.36, 0.72), (-L + 0.2, 0.9, 0.3, 0.84), (-1.0, 0.93, 0.28, 0.94), (1.2, 0.93, 0.28, 0.98), (L - 0.14, 0.9, 0.32, 0.98), (L, 0.84, 0.4, 0.88)], body)
        p.loft([(-1.12, 0.86, 0.92, 0.96), (-0.5, 0.8, 0.92, 1.4), (0.8, 0.79, 0.92, 1.42), (1.58, 0.84, 0.92, 0.99)], "glass")
        p.box(0.16, 1.43, 0, 1.28, 0.05, 1.52, body)
        for x in (-0.14, 0.72):
            for s in (-1, 1):
                p.box(x, 1.18, s * 0.82, 0.08, 0.5, 0.04, body)
    for x in (-1.44, 1.46):
        for s in (-1, 1):
            p.wheel(x, 0.33, s * 0.86, 0.33, 0.22, "rubber")
            p.wheel(x, 0.33, s * 0.88, 0.17, 0.23, "chrome", segs=8)
    # Bumpers and lamps: the nose is towards negative x
    p.box(-L - 0.03, 0.42, 0, 0.1, 0.14, 1.72, "chrome")
    p.box(L + 0.03, 0.46, 0, 0.1, 0.14, 1.72, "chrome")
    for s in (-1, 1):
        p.box(-L - 0.02, 0.68, s * 0.62, 0.05, 0.14, 0.32, "headlamp")
        p.box(L + 0.02, 0.76, s * 0.66, 0.05, 0.16, 0.28, "tail")
    return p


CARS = {}
taxi = Mesh()
p = car_body(taxi, "taxi", "car")
p.box(0.3, 1.55, 0, 0.3, 0.2, 0.9, "taxi_lit")
p.sign(0.3, 1.55, 0.472, 0.28, 0.14, "taxi_sign", yaw=0)
p.sign(0.3, 1.55, -0.472, 0.28, 0.14, "taxi_sign", yaw=180)
p.sign(0.1, 0.66, 0.955, 1.5, 0.3, "taxi_door", yaw=0)
p.sign(0.1, 0.66, -0.955, 1.5, 0.3, "taxi_door", yaw=180)
p.sign(2.52, 0.54, 0, 0.36, 0.14, "plate", yaw=90)
CARS["car_taxi"] = taxi
sedan = Mesh()
car_body(sedan, "sedan", "car")
CARS["car_sedan"] = sedan
maroon = Mesh()
car_body(maroon, "maroon", "car")
CARS["car_maroon"] = maroon
van = Mesh()
car_body(van, "van_white", "van")
CARS["car_van"] = van

# --- Where everything stands ------------------------------------------------------------------------
west, east, far, park = Mesh(), Mesh(), Mesh(), Mesh()
for x, z in SITE["benches"]:
    if z > 0:
        bench(west if x < 0 else east, x, z)
for sx, m in ((-1, west), (1, east)):
    for x in (52.0, 60.0, 68.0, 76.0, 84.0):
        bench(m, sx * x, 24.6)
    for x in (47.0, 86.0):
        planter(m, sx * x, 12.2)
    for x in (22.0, 64.0, 112.0):
        bin_(m, sx * x, 33.9)
    for x in (56.0, 64.0, 72.0):
        planter(m, sx * x, 11.2, 3.6)
    flagpole(m, sx * 27.0, 19.0)
hydrant(west, -29.0, 34.2)
hydrant(east, 91.0, 34.2)
cart(east, 19.0, 32.6, 0.0)
news_box(west, -24.5, 33.9, 0.0)
news_box(west, -23.5, 33.9, 0.0)
street_sign_pole(east, 7.6, 34.1, 0.0)
street_sign_pole(far, 7.6, 54.0, 180.0)
signal_pole(west, -6.5, 34.2, 90.0, -7.6)
signal_pole(far, -6.5, 54.1, 90.0, 7.6)
# Joke signs: the plan's plaque, the fountain's warning and the opening hours
for sx, m in ((-1, west), (1, east)):
    p = Prop(m, sx * 7.0, 0.0, D.PED_Z[1] + 0.31)
    p.box(0, 1.6, -0.01, 1.32, 0.46, 0.03, "bronze")
    p.sign(0, 1.6, 0.03, 1.26, 0.42, "sculptures")
    p = Prop(m, sx * 21.0, 0.0, D.PED_Z[1] + 0.31)
    p.box(0, 1.6, -0.01, 1.32, 0.46, 0.03, "bronze")
    p.sign(0, 1.6, 0.03, 1.26, 0.42, "sculptures")
    p = Prop(m, sx * (D.FOUNTAIN_X - sx * 0.0), D.PLAZA_Y, D.FOUNTAIN_Z + D.FOUNTAIN_SIZE / 2 + 0.26)
    p.box(0, 0.5, -0.05, 0.08, 1.0, 0.05, "iron")
    p.box(0, 1.0, 0, 1.04, 0.56, 0.05, "iron")
    p.sign(0, 1.0, 0.05, 0.96, 0.48, "fountain_sign")
p = Prop(west, -13.8, D.PLAZA_Y, 25.7)
p.box(0, 0.06, 0, 0.9, 0.12, 0.4, "granite")
p.box(0, 1.0, 0, 0.84, 1.8, 0.08, "iron")
p.sign(0, 1.05, 0.065, 0.74, 0.92, "hours")


# Secrets. The Needle really did come from Alexandria, and nobody took it back either.
nx, nz = SITE["needle"]
p = Prop(park, nx, D.PLAZA_Y, nz + 2.1)
p.box(0, 1.65, 0.02, 1.5, 0.64, 0.04, "bronze")
p.sign(0, 1.65, 0.05, 1.44, 0.58, "needle_plaque")
# A book return, out in the park where nobody will see who uses it
p = Prop(park, nx + 8.0, D.PLAZA_Y, nz + 7.0, -28.0)
for dx in (-0.3, 0.3):
    for dz in (-0.24, 0.24):
        p.box(dx, 0.14, dz, 0.07, 0.28, 0.07, "iron")
p.box(0, 0.74, 0, 0.8, 0.94, 0.62, "navy")
p.wheel(0, 1.21, 0, 0.4, 0.62, "navy")
p.box(0, 1.26, 0.325, 0.6, 0.04, 0.03, "bronze")
p.sign(0, 0.86, 0.315, 0.68, 0.425, "late_returns")
# Where the van pulls up
p = Prop(west, -19.2, D.PLAZA_Y, 34.3)
p.lathe(0, 0, [(0.0, 0.05), (2.8, 0.04)], "iron", 6)
p.box(0, 2.4, 0.0, 0.62, 0.52, 0.02, "iron")
p.sign(0, 2.4, 0.03, 0.6, 0.5, "trojan_only")
p.sign(0, 2.4, -0.03, 0.6, 0.5, "trojan_only", yaw=180)
# The neighbourhood's notice board
p = Prop(west, -26.7, D.PLAZA_Y, 33.95, 180.0)
for dx in (-0.82, 0.82):
    p.box(dx, 0.9, 0, 0.08, 1.8, 0.08, "wood")
p.box(0, 1.34, 0, 1.76, 0.92, 0.05, "wood")
p.box(0, 1.84, 0, 1.9, 0.07, 0.2, "wood")
p.sign(-0.42, 1.34, 0.03, 0.74, 0.72, "poster_heel")
p.sign(0.42, 1.34, 0.03, 0.74, 0.72, "poster_knowledge")


def barricade(m, x, z):
    """A blue police sawhorse, the kind a street gets closed with."""
    p = Prop(m, x, D.PLAZA_Y, z, 90.0)
    p.box(0, 0.98, 0, 2.5, 0.2, 0.05, "navy")
    p.box(0, 0.62, 0, 2.5, 0.14, 0.05, "white")
    for dx in (-1.05, 1.05):
        p.box(dx, 0.5, 0.2, 0.08, 1.0, 0.08, "wood")
        p.box(dx, 0.5, -0.2, 0.08, 1.0, 0.08, "wood")


# The block ends at side streets the game doesn't go into. Barricades say so, leaving the traffic its lanes.
for sx, m in ((-1, west), (1, east)):
    z = 33.0
    while z > 19.5:
        barricade(m, sx * 170.0, z)
        z -= 2.7
    for z in (36.2, 38.9, 56.3, 59.0):
        barricade(m, sx * 170.0, z)


def export(meshes, name):
    for ob in list(bpy.context.scene.objects):
        bpy.data.objects.remove(ob)
    mat = bpy.data.materials.get("ext_props") or bpy.data.materials.new("ext_props")
    total = 0
    objs = []
    for key, g in meshes.items():
        if not g.f:
            continue
        me = bpy.data.meshes.new(key)
        me.from_pydata(g.v, [], g.f)
        me.update()
        uv = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                uv.data[li].uv = g.uv[me.loops[li].vertex_index]
        me.materials.append(mat)
        ob = bpy.data.objects.new(key, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.select_set(True)
        objs.append(ob)
        total += sum(len(q.vertices) - 2 for q in me.polygons)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), export_format="GLB", use_selection=True, export_yup=True, export_materials="EXPORT", export_cameras=False, export_lights=False, export_animations=False)
    print("TRIS", name, total, flush=True)


export({"PropsWest": west, "PropsEast": east, "PropsFar": far, "PropsPark": park}, "props")
export(CARS, "cars")
print("DONE", flush=True)
