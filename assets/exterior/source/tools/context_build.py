"""Background Blender job: everything around the finished pavilion, at true size and still simple.
The wings, sides and back follow the real footprint; plaza trees and benches stand at their real
positions; Cleopatra's Needle stands where it really does, behind the museum.
usage: blender -b --factory-startup --python context_build.py -- <out glb> [save blend]"""
import importlib, json, math, pathlib, sys
import bmesh
import bpy

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import ext_dims as D
importlib.reload(D)

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
SITE = json.load(open(HERE / "site.json"))
MATS = {"BO_Stone": (0.56, 0.55, 0.53), "BO_StoneDark": (0.42, 0.41, 0.40), "BO_Glass": (0.05, 0.06, 0.08), "BO_Paving": (0.34, 0.335, 0.33),
        "BO_Road": (0.135, 0.135, 0.15), "BO_Line": (0.60, 0.59, 0.55), "BO_Grass": (0.16, 0.20, 0.15), "BO_Tree": (0.15, 0.20, 0.15), "BO_City": (0.33, 0.34, 0.37), "BO_Metal": (0.13, 0.13, 0.14),
        "BO_Granite": (0.30, 0.16, 0.13), "BO_Water": (0.02, 0.04, 0.06), "BO_Rim": (0.24, 0.24, 0.25), "BO_Wet": (0.05, 0.05, 0.055), "BO_Lamp": (1.0, 0.78, 0.5), "BO_CityTrim": (0.2, 0.19, 0.2), "BO_Tank": (0.14, 0.1, 0.075), "BO_Hedge": (0.05, 0.085, 0.055)}


class Part:
    def __init__(self):
        self.v, self.f, self.s = [], [], []

    def add(self, verts, faces, smooth=False):
        b = len(self.v)
        self.v += [(x, -z, y) for x, y, z in verts]
        for f in faces:
            self.f.append([i + b for i in f])
            self.s.append(smooth)


parts = {k: Part() for k in MATS}


def box(mat, x0, x1, y0, y1, z0, z1):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    parts[mat].add(v, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])


def loft(mat, x, z, rings, segs=12):
    v = []
    for y, r in rings:
        for i in range(segs):
            a = -2 * math.pi * i / segs
            v.append((x + r * math.cos(a), y, z + r * math.sin(a)))
    f = []
    for j in range(len(rings) - 1):
        for i in range(segs):
            a, b = j * segs + i, j * segs + (i + 1) % segs
            f.append((a, b, b + segs, a + segs))
    f.append(tuple(range(len(v) - segs, len(v))))
    parts[mat].add(v, f, True)


def extrude(mat, outline, y0, y1, walls=True, cap=True):
    """A wall ring and roof from a footprint. The wall behind the centre arch keeps a way in for the doors."""
    n = len(outline)
    v = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
    f = []
    if walls:
        for i in range(n):
            j = (i + 1) % n
            a, b = outline[i], outline[j]
            if a[1] == b[1] == 5.9 and min(a[0], b[0]) < 0 < max(a[0], b[0]):
                k = 1.8 if a[0] > 0 else -1.8
                for x0, x1, q0, q1 in ((a[0], k, y0, y1), (k, -k, 3.9, y1), (-k, b[0], y0, y1)):
                    parts[mat].add([(x0, q0, 5.9), (x1, q0, 5.9), (x1, q1, 5.9), (x0, q1, 5.9)], [(0, 1, 2, 3)])
                continue
            f.append((i, j, j + n, i + n))
    if cap:
        f.append(tuple(range(n, 2 * n)))
    parts[mat].add(v, f)


def arched_panel(mat, x, z, y0, ys, half, facing, n=12):
    """A dark window on a front wall. facing is +1 for the front, and it may sit on a side wall too."""
    pts = [(half, y0)] + [(half * math.cos(math.pi * i / n), ys + half * math.sin(math.pi * i / n)) for i in range(n + 1)] + [(-half, y0)]
    verts = [(x + a, b, z + 0.03 * facing) for a, b in pts]
    parts[mat].add(verts, [tuple(range(len(verts)))])


def windows_front(x0, x1, pitch, z, y0, ys, half):
    n = int(abs(x1 - x0) / pitch)
    sx = 1 if x1 > x0 else -1
    pad = (abs(x1 - x0) - (n - 1) * pitch) / 2
    for i in range(n):
        x = x0 + sx * (pad + i * pitch)
        arched_panel("BO_Glass", x, z, y0, ys, half, 1)
        box("BO_Stone", x - half - 0.45, x + half + 0.45, y0 - 0.45, y0, z, z + 0.32)        # sill
        box("BO_Glass", x - 1.0, x + 1.0, -3.0, -1.2, z, z + 0.03)                            # barred basement window
        box("BO_Stone", x - 2.0, x + 2.0, D.CORNICE_Y + 1.1, D.WING_TOP_Y - 1.5, z, z + 0.12)  # upper panel


def building():
    F = [(x, 5.9) if abs(x) < 31 and z == 10.0 else (x, z) for x, z in D.FOOTPRINT]
    # Whole body. The pavilion's own walls are replaced by the finished front, so the notch for it is cut out of the loop.
    extrude("BO_Stone", F, D.PLAZA_Y, D.WING_TOP_Y)
    for sx in (-1, 1):
        # The end wing's taller body; its finished front comes from the wing builder
        xa, xb = sorted((sx * D.MID_X, sx * D.END_X))
        box("BO_Stone", xa, xb, D.WING_TOP_Y, D.END_TOP_Y, -10.0, D.END_Z)
    # The glass wall on the park side of the south-east wing, where the real Temple of Dendur sits
    dz = SITE["dendur"][1]
    box("BO_Glass", D.END_X, D.END_X + 0.1, -3.5, 13.5, -92.0, -28.0)
    for i in range(16):
        z = -92.0 + i * 4.2
        box("BO_Metal", D.END_X, D.END_X + 0.25, -3.5, 13.5, z, z + 0.16)
    # Back: the long glass wall facing the park
    box("BO_Glass", -80.0, 80.0, -3.5, 12.0, -129.5, -129.4)
    for i in range(38):
        x = -80.0 + i * 4.3
        if abs(x) > 15:
            box("BO_Metal", x, x + 0.18, -3.5, 12.0, -129.7, -129.4)
    # Loading dock on the west side
    box("BO_StoneDark", -D.END_X - 4.0, -D.END_X, D.PLAZA_Y, -3.2, -24.6, -16.0)
    box("BO_Glass", -D.END_X - 0.05, -D.END_X, D.PLAZA_Y, 0.2, -24.2, -16.4)
    box("BO_StoneDark", -D.END_X - 5.0, -D.END_X, 0.2, 0.6, -25.0, -15.6)


def tree(x, z, h=11.0, r=4.2):
    y = D.PLAZA_Y
    loft("BO_Metal", x, z, [(y, 0.30), (y + h * 0.5, 0.2)], 8)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    v = [(x + q.co.x * r, y + h * 0.68 + q.co.z * r * 0.95, z + q.co.y * r) for q in bm.verts]
    f = [[q.index for q in g.verts] for g in bm.faces]
    bm.free()
    parts["BO_Tree"].add(v, f)


def site():
    P = D.PLAZA_Y
    W = 240.0
    # Paving everywhere the public walks, the avenue, the far sidewalk, and the park beyond the path
    box("BO_Paving", -D.RING_X - 8, D.RING_X + 8, P - 0.5, P, D.PARK_Z, D.CURB_Z)
    box("BO_Road", -W, W, P - 0.5, D.ROAD_Y, D.CURB_Z, D.ROAD_Z_END)
    box("BO_Paving", -W, W, P - 0.5, P, D.ROAD_Z_END, D.FAR_WALK_Z_END + 42.0)
    box("BO_Grass", -W, W, P - 0.45, P + 0.01, -300.0, D.PARK_Z)
    for sx in (-1, 1):
        a, b = sorted((sx * (D.RING_X + 8), sx * W))
        box("BO_Grass", a, b, P - 0.45, P + 0.01, D.PARK_Z, D.CURB_Z - 12)
    # Fountains: square pools, the real size and place
    h = D.FOUNTAIN_SIZE / 2
    for sx in (-1, 1):
        x = sx * D.FOUNTAIN_X
        z = D.FOUNTAIN_Z
        rim = 0.62
        # Polished granite coping, stepped down to a dark wet floor
        box("BO_Rim", x - h, x + h, P, P + 0.3, z - h, z - h + rim)
        box("BO_Rim", x - h, x + h, P, P + 0.3, z + h - rim, z + h)
        box("BO_Rim", x - h, x - h + rim, P, P + 0.3, z - h + rim, z + h - rim)
        box("BO_Rim", x + h - rim, x + h, P, P + 0.3, z - h + rim, z + h - rim)
        box("BO_Rim", x - h - 0.1, x + h + 0.1, P, P + 0.1, z - h - 0.1, z - h)
        box("BO_Rim", x - h - 0.1, x + h + 0.1, P, P + 0.1, z + h, z + h + 0.1)
        box("BO_Rim", x - h - 0.1, x - h, P, P + 0.1, z - h, z + h)
        box("BO_Rim", x + h, x + h + 0.1, P, P + 0.1, z - h, z + h)
        box("BO_Wet", x - h + rim, x + h - rim, P, P + 0.08, z - h + rim, z + h - rim)
        box("BO_Water", x - h + rim, x + h - rim, P + 0.08, P + 0.2, z - h + rim, z + h - rim)
        # Bronze nozzles standing just proud of the water
        edge = h - 0.95
        for i in range(9):
            t = (i + 0.5) / 9 * 2 - 1
            for ax, az in ((t * edge, -edge), (t * edge, edge), (-edge, t * edge), (edge, t * edge)):
                box("BO_Metal", x + ax - 0.05, x + ax + 0.05, P + 0.2, P + 0.25, z + az - 0.05, z + az + 0.05)
        loft("BO_Metal", x, z, [(P + 0.2, 0.55), (P + 0.34, 0.5), (P + 0.38, 0.3)], 12)
    # Lamp standards along the curb: a cast base, a fluted post and a lantern
    for x, z in [(x, D.LAMP_Z) for x in D.LAMPS_X] + [(x, D.FAR_LAMP_Z) for x in D.FAR_LAMPS_X] + D.PATH_LAMPS:
        y = P
        loft("BO_Metal", x, z, [(y, 0.30), (y + 0.5, 0.26), (y + 0.7, 0.16), (y + 3.0, 0.10), (y + 8.5, 0.07), (y + 8.7, 0.13)], 10)
        loft("BO_Lamp", x, z, [(D.LAMP_TOP_Y - 0.45, 0.14), (D.LAMP_TOP_Y + 0.25, 0.27)], 8)
        loft("BO_Metal", x, z, [(D.LAMP_TOP_Y + 0.25, 0.31), (D.LAMP_TOP_Y + 0.45, 0.14), (D.LAMP_TOP_Y + 0.6, 0.03)], 8)
    # Fifth Avenue runs one way in five lanes, with a zebra crossing where 82nd Street meets the steps
    y = D.ROAD_Y + 0.012
    lane = (D.ROAD_Z_END - D.CURB_Z) / 5
    for i in range(1, 5):
        z = D.CURB_Z + i * lane
        x = -172.0
        while x < 172:
            if abs(x + 1.5) > 7.5:
                box("BO_Line", x, x + 3.0, D.ROAD_Y, y, z - 0.07, z + 0.07)
            x += 12.0
    for i in range(15):
        z = D.CURB_Z + 0.95 + i * 1.18
        box("BO_Line", -2.4, 2.4, D.ROAD_Y, y, z - 0.31, z + 0.31)
    box("BO_Line", 5.2, 5.65, D.ROAD_Y, y, D.CURB_Z + 0.3, D.ROAD_Z_END - 0.3)
    # Tree pits at the real trees; the trees themselves are drawn in instanced batches
    for x, z in SITE["trees"]:
        if abs(x) <= 160 and 10 < z < 36:
            box("BO_Metal", x - 1.15, x + 1.15, P, P + 0.02, z - 1.15, z + 1.15)
            box("BO_Wet", x - 1.0, x + 1.0, P, P + 0.025, z - 1.0, z + 1.0)
    for x, z in SITE["benches"]:
        if z > 0:
            box("BO_StoneDark", x - 1.1, x + 1.1, P, P + 0.48, z - 0.35, z + 0.35)
    # The park's edge: a clipped hedge along the limit of the walkable ground
    h = 2.6
    box("BO_Hedge", -D.BOUND_X - 1.4, -D.BOUND_X, P, P + h, D.BOUND_Z_N, 18.0)
    box("BO_Hedge", D.BOUND_X, D.BOUND_X + 1.4, P, P + h, D.BOUND_Z_N, 18.0)
    box("BO_Hedge", -D.BOUND_X - 1.4, D.BOUND_X + 1.4, P, P + h, D.BOUND_Z_N - 1.4, D.BOUND_Z_N)
    # The West Side skyline, far beyond the park
    far_z = -760.0
    x, i = -900.0, 0
    tall = [62, 96, 74, 150, 158, 80, 66, 118, 124, 70, 88, 170, 176, 92, 64, 104, 84, 140, 72, 98]
    while x < 900:
        w = 34 + (i * 13) % 37
        box("BO_City", x, x + w, P, P + tall[i % len(tall)], far_z, far_z + 30)
        x += w + 7
        i += 1
    # Cleopatra's Needle: 21 m of Egyptian granite that once stood in Alexandria
    nx, nz = SITE["needle"]
    box("BO_StoneDark", nx - 3.2, nx + 3.2, P, P + 0.9, nz - 3.2, nz + 3.2)
    box("BO_StoneDark", nx - 2.1, nx + 2.1, P + 0.9, P + 2.4, nz - 2.1, nz + 2.1)
    top = P + 2.4 + 21.0
    w0, w1 = 1.25, 0.8
    v = [(nx + sx * w0, P + 2.4, nz + sz * w0) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    v += [(nx + sx * w1, top - 1.6, nz + sz * w1) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    v.append((nx, top, nz))
    parts["BO_Granite"].add(v, [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0), (4, 8, 5), (5, 8, 6), (6, 8, 7), (7, 8, 4)])
    # Fifth Avenue's far side: real heights from the map, 18 to 70 m, as plain masses for now
    x = -240.0
    heights = [27, 21, 53, 18, 49, 24, 72, 20, 37, 62, 19, 23, 51, 26, 74, 18, 31, 48, 22, 44]
    i = 0
    while x < 240:
        w = 22 + (i * 7) % 19
        for a, b in ((x, min(x + w - 1.5, -D.STREET82_X)), (max(x, D.STREET82_X), x + w - 1.5)):
            if b - a > 3.0:
                top = P + heights[i % len(heights)]
                front = D.FAR_WALK_Z_END + 0.5
                box("BO_City", a, b, P, top, front, front + 33.5)
                # A heavy cornice, a line of stone above the shops, and for some a water tank on the roof
                box("BO_CityTrim", a - 0.3, b + 0.3, top - 0.4, top, front - 0.45, front + 34)
                box("BO_CityTrim", a, b, P + 4.2, P + 4.7, front - 0.25, front)
                if i % 3 == 0 and b - a > 10:
                    wx, wz = a + (b - a) * 0.3, front + 15
                    for dx, dz in ((-1.5, -1.5), (1.5, -1.5), (1.5, 1.5), (-1.5, 1.5)):
                        box("BO_Metal", wx + dx - 0.1, wx + dx + 0.1, top, top + 3.2, wz + dz - 0.1, wz + dz + 0.1)
                    loft("BO_Tank", wx, wz, [(top + 3.2, 2.1), (top + 7.2, 2.1), (top + 7.3, 2.25), (top + 8.8, 0.15)], 12)
        x += w
        i += 1
    for x0, x1, h, z0 in ((-300, -170, 110, 170), (-160, -60, 145, 190), (-50, 60, 120, 175), (70, 190, 160, 185), (200, 320, 118, 170)):
        box("BO_City", x0, x1, P, P + h, z0, z0 + 60)


def build():
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    building()
    site()
    total = 0
    for name, part in parts.items():
        if not part.f:
            continue
        me = bpy.data.meshes.new(name.replace("BO_", "Context_"))
        me.from_pydata(part.v, [], part.f)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        # Cut out what the finished pavilion replaces
        if name in ("BO_Stone",):
            pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f, s in zip(bm.faces, part.s):
            f.smooth = s
        bm.to_mesh(me)
        bm.free()
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        n = next(q for q in m.node_tree.nodes if q.type == "BSDF_PRINCIPLED")
        n.inputs["Base Color"].default_value = (*MATS[name], 1)
        n.inputs["Roughness"].default_value = 0.9
        me.materials.append(m)
        ob = bpy.data.objects.new(me.name, me)
        scene.collection.objects.link(ob)
        total += sum(len(p.vertices) - 2 for p in me.polygons)
    print("CONTEXT_TRIS", total, flush=True)
    for ob in scene.objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = next(iter(scene.objects))
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_cameras=False, export_lights=False, export_animations=False)
    if len(argv) > 1:
        bpy.ops.wm.save_as_mainfile(filepath=argv[1], compress=True)


build()
