"""Builds the Sculpture Hall set (asset item P3.1) in a background Blender:
  blender -b --factory-startup --python sculpture_build.py -- <assets/interior/sculpture folder> <scenes/props folder>
Carves the three statues (sculpture_figures.py), thins each to its game mesh, bakes how much light reaches
every part of the fine carving into assets/interior/source/sculpture_<statue>_ao.png, and builds Homer's
pier and Icarus's wings. Writes each prop's .glb, its import settings and its scene in scenes/props, and
the "away for cleaning" plinth. Run make_sculpture_art.py afterwards for the texture and materials.

Blender is z up and the game is y up: a prop's front, the game's +z, is Blender's -y. The statues wear
assets/plates/statue_marble.tres, the marble the players turn into when they pose on a plinth, with the
set's grime laid over it."""
import math
import pathlib
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import int_dims as D  # noqa: E402
import sculpture_figures as S  # noqa: E402
import sculpture_layout as L  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
PROPS.mkdir(parents=True, exist_ok=True)
BAKES = TOOLS.parent
RES = "res://assets/interior/sculpture/"
MARBLE = "res://assets/plates/statue_marble.tres"
N = L.ATLAS
T0 = time.time()


def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m


def activate(ob):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def apply_mod(ob, kind, **kw):
    activate(ob)
    m = ob.modifiers.new("m", kind)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.ops.object.modifier_apply(modifier=m.name)


def region_uv(name, fu, fv):
    """A point in a region, fu across and fv down from its top-left, in Blender's UV space (v up)."""
    x, y, w, h = L.REGIONS[name]
    return ((x + 1 + fu * (w - 2)) / N, 1 - (y + 1 + fv * (h - 2)) / N)


# --- The statues ------------------------------------------------------------------------------------

def from_field(name, field):
    v, q = field.mesh()
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v))
    me.vertices.foreach_set("co", v.astype(np.float32).ravel())
    me.loops.add(q.size)
    me.polygons.add(len(q))
    me.polygons.foreach_set("loop_start", np.arange(len(q), dtype=np.int32) * 4)
    me.loops.foreach_set("vertex_index", q.astype(np.int32).ravel())
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.ones(len(q), bool))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def game_mesh(hp, name):
    """A copy of the carving thinned to the statue's budget, unwrapped into 0..1."""
    lp = bpy.data.objects.new(name, hp.data.copy())
    bpy.context.scene.collection.objects.link(lp)
    apply_mod(lp, "TRIANGULATE")
    # Faces and hands keep their triangles; plain drapery, backs and the slab give theirs up first
    co = np.empty(len(lp.data.vertices) * 3, np.float32)
    lp.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    # (Blender's collapse never touches a weight of 0 and spends least on low weights, so detail gets 0.1, the rest 1.)
    keep = np.zeros(len(co))
    for centre, radius in S.DETAIL[name]:
        d = np.linalg.norm(co - np.asarray(centre), axis=1)
        keep = np.maximum(keep, np.clip((radius - d) / (radius * 0.4), 0, 1))
    weight = np.round(1.0 - 0.9 * keep, 2)
    group = lp.vertex_groups.new(name="detail")
    for w in np.unique(weight):
        group.add(np.nonzero(weight == w)[0].tolist(), float(w), "REPLACE")
    apply_mod(lp, "DECIMATE", decimate_type="COLLAPSE", ratio=L.TRIS[name] / len(lp.data.polygons),
              vertex_group="detail", vertex_group_factor=12.0)
    lp.vertex_groups.clear()
    lp.data.polygons.foreach_set("use_smooth", np.ones(len(lp.data.polygons), bool))
    activate(lp)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(78), island_margin=0.01, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    log(name, "game mesh", len(lp.data.polygons), "tris")
    return lp


def ao_material(distance):
    m = bpy.data.materials.new("bake_ao_%g" % distance)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 16
    ao.only_local = True
    ao.inputs["Distance"].default_value = distance
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(ao.outputs["AO"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def bake_ao(name, lp, hp):
    """Two bakes of the fine carving onto the game mesh: R the crevices (3 cm), G the broad shadow (30 cm)."""
    w = L.REGIONS[name][2]
    target = material("bake_target")
    target.use_nodes = True
    node = target.node_tree.nodes.new("ShaderNodeTexImage")
    target.node_tree.nodes.active = node
    lp.data.materials.clear()
    lp.data.materials.append(target)
    channels = []
    for distance in (0.03, 0.3):
        hp.data.materials.clear()
        hp.data.materials.append(ao_material(distance))
        img = bpy.data.images.new("ao_%s_%g" % (name, distance), w, w, alpha=False, float_buffer=False)
        img.colorspace_settings.name = "Non-Color"
        node.image = img
        for o in bpy.context.scene.objects:
            o.select_set(False)
        hp.select_set(True)
        lp.select_set(True)
        bpy.context.view_layer.objects.active = lp
        bpy.ops.object.bake(type="EMIT", use_selected_to_active=True, cage_extrusion=0.025, max_ray_distance=0.05,
                            margin=6, margin_type="EXTEND", use_clear=True, target="IMAGE_TEXTURES")
        px = np.empty(w * w * 4, np.float32)
        img.pixels.foreach_get(px)
        channels.append(px.reshape(w, w, 4)[..., 0])
        bpy.data.images.remove(img)
    out = bpy.data.images.new("sculpture_%s_ao" % name, w, w, alpha=False, float_buffer=False)
    out.colorspace_settings.name = "Non-Color"
    rgba = np.ones((w, w, 4), np.float32)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = channels[0], channels[1], 0.0
    out.pixels.foreach_set(rgba.ravel())
    out.filepath_raw = str(BAKES / ("sculpture_%s_ao.png" % name))
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    lp.data.materials.clear()
    log(name, "baked")


def place_in_atlas(ob, name):
    x, y, w, h = L.REGIONS[name]
    for d in ob.data.uv_layers.active.data:
        u, v = d.uv
        d.uv = ((x + u * w) / N, 1 - (y + (1 - v) * h) / N)


def statue(name, lift):
    field = S.STATUES[name](L.CARVE[name])
    hp = from_field("carving_" + name, field)
    apply_mod(hp, "SMOOTH", factor=0.5, iterations=2)
    log(name, "carved", len(hp.data.polygons), "faces")
    lp = game_mesh(hp, name)
    bake_ao(name, lp, hp)
    bpy.data.objects.remove(hp)
    place_in_atlas(lp, name)
    lp.data.transform(Matrix.Translation((0, 0, lift)))
    lp.data.materials.append(material("statue_marble"))
    lp.data.validate()
    return lp


# --- Hand-built parts: boxes and quads with their own place in the atlas -----------------------------

class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")

    def quad(self, corners, region, uvs=((0, 1), (1, 1), (1, 0), (0, 0)), slot=0, smooth=False):
        face = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        face.material_index = slot
        face.smooth = smooth
        for loop, (fu, fv) in zip(face.loops, uvs):
            loop[self.layer].uv = region_uv(region, fu, fv)
        return face

    def box(self, lo, hi, region, taper=0.0):
        """A box, its top pulled in by `taper` on every side; each face shows the whole region."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        t = taper
        b = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
        u = [(x0 + t, y0 + t, z1), (x1 - t, y0 + t, z1), (x1 - t, y1 - t, z1), (x0 + t, y1 - t, z1)]
        for i in range(4):
            j = (i + 1) % 4
            self.quad([b[i], b[j], u[j], u[i]], region)
        self.quad(u, region)
        self.quad(b[::-1], region)

    def tube(self, points, radii, region, sides=6, slot=0):
        """A tube through the points: its length runs across the region, its girth down it."""
        rings = []
        total = sum((Vector(points[i + 1]) - Vector(points[i])).length for i in range(len(points) - 1))
        run = 0.0
        for i, p in enumerate(points):
            a = Vector(points[max(i - 1, 0)])
            b = Vector(points[min(i + 1, len(points) - 1)])
            t = (b - a).normalized()
            side = t.cross(Vector((0, 0, 1)))
            if side.length < 1e-4:
                side = t.cross(Vector((0, 1, 0)))
            side.normalize()
            up = side.cross(t).normalized()
            if i:
                run += (Vector(p) - Vector(points[i - 1])).length
            rings.append([(Vector(p) + radii[i] * (math.cos(k / sides * math.tau) * side + math.sin(k / sides * math.tau) * up),
                           run / total) for k in range(sides + 1)])
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(sides):
                self.quad([r0[k][0], r0[k + 1][0], r1[k + 1][0], r1[k][0]], region,
                          uvs=[(r0[k][1], k / sides), (r0[k][1], (k + 1) / sides), (r1[k][1], (k + 1) / sides), (r1[k][1], k / sides)],
                          slot=slot, smooth=True)

    def blob(self, centre, radii, region, seed, slot=0, rot_z=0.0, segments=7, rings=4):
        """A lumpy low-poly lump: a squashed sphere with its points jittered. Built point by point, because
        Blender's own sphere hands its faces back in a different order every run."""
        rng = np.random.default_rng(seed)
        R = Matrix.Rotation(rot_z, 3, "Z")
        c = Vector(centre)

        def point(x, y, z):
            j = 1 + rng.uniform(-0.18, 0.18)
            return self.bm.verts.new(c + R @ Vector((x * radii[0] * j, y * radii[1] * j, z * radii[2] * j)))

        top = point(0, 0, 1)
        rows = []
        for r in range(1, rings):
            a = math.pi * r / rings
            rows.append([point(math.sin(a) * math.cos(k / segments * math.tau), math.sin(a) * math.sin(k / segments * math.tau), math.cos(a))
                         for k in range(segments)])
        bottom = point(0, 0, -1)
        uv = lambda v: (0.5 + (v.co - c).x / (radii[0] * 2.4), 0.5 - (v.co - c).z / (radii[2] * 2.4))
        faces = [[top, rows[0][(k + 1) % segments], rows[0][k]] for k in range(segments)]
        for r0, r1 in zip(rows, rows[1:]):
            faces += [[r0[k], r0[(k + 1) % segments], r1[(k + 1) % segments], r1[k]] for k in range(segments)]
        faces += [[bottom, rows[-1][k], rows[-1][(k + 1) % segments]] for k in range(segments)]
        for corners in faces:
            face = self.bm.faces.new(corners)
            face.material_index = slot
            face.smooth = True
            for loop, v in zip(face.loops, corners):
                loop[self.layer].uv = region_uv(region, *uv(v))

    def finish(self, name, materials):
        mesh = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in materials:
            mesh.materials.append(material(m))
        mesh.validate()
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def pedestal():
    """Homer's pier: a square base with a step, a slightly tapering shaft and a capital, all in green marble."""
    b = Builder()
    bw, bh = L.PED_BASE
    sw, sh = L.PED_SHAFT
    cw, ch = L.PED_CAP
    h = lambda w: w / 2
    b.box((-h(bw), -h(bw), 0.0), (h(bw), h(bw), bh * 0.7), "ped_base")
    b.box((-h(bw) + 0.02, -h(bw) + 0.02, bh * 0.7), (h(bw) - 0.02, h(bw) - 0.02, bh), "ped_base", taper=0.02)
    b.box((-h(sw), -h(sw), bh), (h(sw), h(sw), bh + sh), "ped_shaft", taper=0.01)
    b.box((-h(sw) + 0.01, -h(sw) + 0.01, bh + sh), (h(sw) - 0.01, h(sw) - 0.01, bh + sh + ch * 0.35), "ped_cap", taper=-0.02)
    b.box((-h(cw), -h(cw), bh + sh + ch * 0.35), (h(cw), h(cw), L.PED_H), "ped_cap")
    ob = b.finish("pedestal", ["int_sculpture"])
    # The top shows the whole of its own cell
    for poly in ob.data.polygons:
        if poly.normal.z > 0.9 and poly.center.z > L.PED_H - 0.001:
            for li in poly.loop_indices:
                co = ob.data.vertices[ob.data.loops[li].vertex_index].co
                ob.data.uv_layers.active.data[li].uv = region_uv("ped_top", co.x / cw + 0.5, 0.5 - co.y / cw)
    apply_mod(ob, "BEVEL", width=0.005, segments=1, limit_method="ANGLE", angle_limit=math.radians(40))
    if hasattr(ob.data, "set_sharp_from_angle"):
        ob.data.set_sharp_from_angle(angle=math.radians(40))
    return ob


# --- Icarus's wings ---------------------------------------------------------------------------------

FEATHERS, FRAME = 1, 0
TILT = Matrix.Rotation(math.radians(-L.WING_TILT), 3, "X")


def feather(b, base, direction, length, width, droop, region, twist=0.0):
    """One feather card: narrow at the quill, widest past the middle, bending down along its length."""
    d = Vector(direction).normalized()
    n = Vector((0, 0, 1))
    w = d.cross(n).normalized()
    n = w.cross(d).normalized()
    w = (w * math.cos(twist) + n * math.sin(twist)).normalized()
    base = Vector(base)
    pts = []
    for t, half in ((0.0, 0.18), (0.45, 0.5), (1.0, 0.36)):
        c = base + d * length * t - n * droop * t * t
        pts.append((c - w * width * half, c + w * width * half, t))
    for (a0, a1, t0), (b0, b1, t1) in zip(pts, pts[1:]):
        b.quad([a0, a1, b1, b0], region, uvs=[(0.5 - 0.5 * _h(t0), 1 - t0), (0.5 + 0.5 * _h(t0), 1 - t0),
                                              (0.5 + 0.5 * _h(t1), 1 - t1), (0.5 - 0.5 * _h(t1), 1 - t1)], slot=FEATHERS)


def _h(t):
    """The card's half-width as a share of the feather cell, matching the shape drawn in the texture."""
    return {0.0: 0.36, 0.45: 1.0, 1.0: 0.72}[t]


def bar_point(path, t):
    """A point t (0..1) along a polyline."""
    seg = [(Vector(path[i + 1]) - Vector(path[i])).length for i in range(len(path) - 1)]
    goal = t * sum(seg)
    for i, s in enumerate(seg):
        if goal <= s or i == len(seg) - 1:
            return Vector(path[i]).lerp(Vector(path[i + 1]), min(goal / s, 1.0))
        goal -= s


def colour(rng, kind, t):
    """Daedalus took feathers where he found them: mostly goose white, some eagle brown, a few scorched."""
    r = rng.random()
    k = 1 if r < 0.22 else (2 if r < 0.22 + 0.3 * t else 0)
    return "%s_%d" % (kind, k if kind != "covert" else k + 3 * int(rng.random() < 0.5))


def wing(b, side, rng):
    """One wing, x > 0, mirrored by `side`. The leading edge faces -y, the prop's front."""
    path = [(0.1, 0.0, 0.0), (0.45, -0.04, 0.05), (0.86, -0.06, 0.07), (1.3, 0.02, 0.045), (L.WING_SPAN / 2 - 0.05, 0.13, 0.0)]
    m = lambda p: Vector((p[0] * side, p[1], p[2]))
    b.tube([m(p) for p in path], [0.02, 0.017, 0.014, 0.011, 0.007], "wood", sides=6, slot=FRAME)
    # Primaries fan from the wrist to the tip; a melted one hangs loose
    for i in range(11):
        t = i / 10
        base = bar_point(path, 0.48 + 0.5 * t)
        ang = math.radians(12 + 64 * t)
        d = (math.sin(ang), math.cos(ang), -0.05)
        loose = i == 4
        feather(b, m(base + Vector((0, 0, 0.004 * i))), m(d) if not loose else m((d[0], d[1], -0.28)),
                0.54 + 0.12 * math.sin(t * math.pi * 0.9) + rng.uniform(-0.02, 0.02), 0.17, 0.05 if not loose else 0.08,
                colour(rng, "primary", t), twist=0.12 * side)
    # Secondaries along the arm, two lost near the root where the wax ran
    for i in range(18):
        if i in (4, 9):
            continue
        t = i / 17
        base = bar_point(path, 0.02 + 0.47 * t)
        d = (0.06 + 0.14 * t, 1.0, -0.06)
        feather(b, m(base + Vector((0, 0.01, 0.003 * i))), m(d), 0.44 + 0.08 * t + rng.uniform(-0.015, 0.015), 0.18, 0.035,
                colour(rng, "secondary", 0.5 * t), twist=0.08 * side)
    # Two rows of coverts over the quills, the upper row shorter
    for row, (count, length, lift, reach, width) in enumerate(((18, 0.28, 0.02, 0.9, 0.13), (21, 0.16, 0.034, 0.98, 0.09))):
        for i in range(count):
            if row == 0 and i == 4:
                continue
            t = i / (count - 1)
            base = bar_point(path, 0.02 + reach * t)
            ang = math.radians(6 + (55 if row == 0 else 60) * max(0.0, t - 0.55) / 0.45)
            d = (math.sin(ang), math.cos(ang), -0.12)
            feather(b, m(base + Vector((0, -0.01, lift + 0.002 * i))), m(d), length * rng.uniform(0.9, 1.1), width,
                    0.015, colour(rng, "covert", 0.0), twist=0.05 * side)
    # Wax over the quills, thickest near the root (nearest the lamp), with drips hanging from it
    for i in range(9):
        t = (i / 8) ** 1.4 * 0.75
        c = bar_point(path, t)
        b.blob(m(c + Vector((0, 0.012, 0.012))), (0.05 - 0.025 * t, 0.034, 0.02), "wax", 700 + i + (0 if side > 0 else 50), rot_z=0.3 * side)
    for i in range(5):
        c = bar_point(path, 0.04 + 0.12 * i) + Vector((0, 0.02, -0.01))
        length = 0.05 + 0.03 * ((i * 7) % 3)
        b.tube([m(c), m(c + Vector((0, 0.004, -length * 0.6))), m(c + Vector((0, 0.006, -length)))], [0.008, 0.006, 0.003], "wax", sides=5, slot=FRAME)
    # A leather loop for the forearm
    c = bar_point(path, 0.3)
    ring = [m(c + Vector((0.02 * math.sin(a), 0.015, -0.035 + 0.035 * math.cos(a)))) for a in np.linspace(0, math.tau, 9)]
    b.tube(ring, [0.006] * 9, "leather", sides=4, slot=FRAME)


def wings():
    rng = np.random.default_rng(710)
    b = Builder()
    for side in (1, -1):
        wing(b, side, rng)
    # The harness between them: a leather band and a buckle plate
    b.tube([(-0.12, 0.0, 0.0), (-0.05, 0.03, -0.02), (0.05, 0.03, -0.02), (0.12, 0.0, 0.0)], [0.014] * 4, "leather", sides=4, slot=FRAME)
    b.box((-0.03, 0.015, -0.035), (0.03, 0.045, -0.005), "steel")
    ob = b.finish("icarus_wings", ["int_sculpture", "int_sculpture_feathers"])
    # Tips raised, then the whole spread tipped up so the room sees the tops of the feathers, as if soaring away
    for v in ob.data.vertices:
        reach = max(abs(v.co.x) - 0.1, 0.0)
        v.co.z += reach * math.tan(math.radians(L.WING_DIHEDRAL))
    ob.data.transform(TILT.to_4x4())
    lowest = min(v.co.z for v in ob.data.vertices)
    assert L.WING_HANG_Y + lowest >= L.WING_MIN_Y, lowest
    # Three wires to the ceiling: from each wrist and from the harness
    w = Builder()
    top = D.WALL_H - L.WING_HANG_Y
    lift = (0.86 - 0.1) * math.tan(math.radians(L.WING_DIHEDRAL))
    for p in ((0.86, -0.06, 0.07 + lift), (-0.86, -0.06, 0.07 + lift), (0.0, 0.03, 0.0)):
        a = TILT @ Vector(p)
        w.tube([a, Vector((a.x, a.y, top - 0.02))], [0.0035, 0.0035], "steel", sides=4)
        w.box((a.x - 0.03, a.y - 0.03, top - 0.02), (a.x + 0.03, a.y + 0.03, top), "steel")
    wires = w.finish("wires", ["int_sculpture"])
    log("wings", len(ob.data.polygons), "faces,", "lowest point", round(L.WING_HANG_Y + lowest, 2), "m")
    return ob, wires


# --- Export, import settings and prop scenes --------------------------------------------------------

GLB_IMPORT = (TOOLS / "cases_build.py").read_text(encoding="utf8").split('GLB_IMPORT_HEAD = """')[1].split('"""')[0]
MAT_ENTRY = (TOOLS / "cases_build.py").read_text(encoding="utf8").split('MAT_ENTRY = """')[1].split('"""')[0]


def export(name, objects):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT / (name + ".glb")), export_format="GLB", use_selection=True,
                              use_active_scene=True, export_yup=True, export_materials="EXPORT",
                              export_cameras=False, export_lights=False, export_animations=False)
    target = OUT / (name + ".glb.import")
    if not target.exists():
        mats = sorted({m.name for o in objects for m in o.data.materials})
        entries = []
        for m in mats:
            entry = MAT_ENTRY.format(mat=m, res=RES)
            if m == "statue_marble":
                entry = entry.replace(RES + "statue_marble.tres", MARBLE)
            entries.append(entry)
        target.write_text(GLB_IMPORT.format(res=RES, name=name, materials=",\n".join(entries)), encoding="utf8", newline="\n")
    log("exported", name, sum(len(o.data.polygons) for o in objects), "faces")


def game_box(lo, hi):
    """A box from Blender corners to the game's (size, centre)."""
    lo, hi = Vector(lo), Vector(hi)
    return (hi.x - lo.x, hi.z - lo.z, hi.y - lo.y), ((lo.x + hi.x) / 2, (lo.z + hi.z) / 2, -(lo.y + hi.y) / 2)


def scene_text(title, note, parts, subs, nodes, editable=None):
    out = ["[gd_scene format=3]\n"]
    out += ['[ext_resource type="%s" path="%s" id="%s"]' % p for p in parts]
    out.append("")
    for sid, kind, body in subs:
        out.append('[sub_resource type="%s" id="%s"]\n%s\n' % (kind, sid, body))
    out.append('[node name="%s" type="Node3D"]\neditor_description = "%s"\n' % (title, note))
    out += nodes
    if editable:
        out.append('[editable path="%s"]\n' % editable)
    return "\n".join(out)


def box_nodes(boxes):
    subs, nodes = [], ['[node name="Body" type="StaticBody3D" parent="."]\n']
    for name, (size, centre) in boxes:
        subs.append(("BoxShape3D_%s" % name.lower(), "BoxShape3D", "size = Vector3(%.3f, %.3f, %.3f)" % size))
        nodes.append('[node name="%s" type="CollisionShape3D" parent="Body"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %.3f, %.3f, %.3f)\n'
                     'shape = SubResource("BoxShape3D_%s")\n' % ((name,) + centre + (name.lower(),)))
    return subs, nodes


def plaque(label, size, at):
    sub = ("QuadMesh_label", "QuadMesh", 'material = ExtResource("4_label")\nsize = Vector2(%.3f, %.3f)' % size)
    node = '[node name="Plaque" type="MeshInstance3D" parent="."]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %.3f, %.3f, %.3f)\nmesh = SubResource("QuadMesh_label")\n' % at
    return sub, node, ("Material", RES + "int_label_%s.tres" % label, "4_label")


def statue_scene(name, ob, figure_box, note):
    title = "Statue" + "".join(p.title() for p in name.split("_"))
    sub_label, node_label, res_label = plaque(name, L.PLAQUE, L.PLAQUE_AT)
    subs, body = box_nodes([("Plinth", ((L.PLINTH_W, D.PLINTH_H, L.PLINTH_W), (0.0, D.PLINTH_H / 2, 0.0))), ("Figure", figure_box)])
    parts = [("PackedScene", "res://assets/plates/plinth.glb", "1_plinth"), ("PackedScene", RES + name + ".glb", "2_mesh"),
             ("Material", RES + "int_statue_grime.tres", "3_grime"), res_label]
    nodes = ['[node name="Plinth" parent="." instance=ExtResource("1_plinth")]\n',
             '[node name="Mesh" parent="." instance=ExtResource("2_mesh")]\n',
             '[node name="%s" parent="Mesh"]\nmaterial_overlay = ExtResource("3_grime")\n' % ob.name, node_label] + body
    (PROPS / ("statue_%s.tscn" % name)).write_text(scene_text(title, note, parts, subs + [sub_label], nodes, "Mesh"), encoding="utf8", newline="\n")


def bust_scene(ob, ped):
    shaft_half = L.PED_SHAFT[0] / 2 - 0.01 * (L.BUST_PLAQUE_Y - L.PED_BASE[1]) / L.PED_SHAFT[1]
    sub_label, node_label, res_label = plaque("bust_homer", L.BUST_PLAQUE, (0.0, L.BUST_PLAQUE_Y, shaft_half + 0.002))
    lo = [min(v.co[i] for v in ob.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in ob.data.vertices) for i in range(3)]
    bw = L.PED_BASE[0]
    subs, body = box_nodes([("Pier", ((bw, L.PED_H, bw), (0.0, L.PED_H / 2, 0.0))),
                            ("Bust", game_box((lo[0] + 0.03, lo[1] + 0.03, L.PED_H), (hi[0] - 0.03, hi[1] - 0.02, hi[2])))])
    parts = [("PackedScene", RES + "bust_homer.glb", "2_mesh"), ("Material", RES + "int_statue_grime.tres", "3_grime"), res_label]
    nodes = ['[node name="Mesh" parent="." instance=ExtResource("2_mesh")]\n',
             '[node name="%s" parent="Mesh"]\nmaterial_overlay = ExtResource("3_grime")\n' % ob.name, node_label] + body
    note = ("Homer: a bearded marble bust, the tip of his nose long gone, on a green marble pier (asset P3.1). %.2f m to the top: "
            "as tall as cover, but too narrow to hide behind. Origin on the floor; the label faces +z." % hi[2])
    (PROPS / "statue_bust_homer.tscn").write_text(scene_text("StatueBustHomer", note, parts, subs + [sub_label], nodes, "Mesh"), encoding="utf8", newline="\n")


def wings_scene():
    parts = [("PackedScene", RES + "icarus_wings.glb", "1_mesh")]
    nodes = ['[node name="Mesh" parent="." instance=ExtResource("1_mesh")]\n',
             '[node name="wires" parent="Mesh"]\ncast_shadow = 0\n']
    note = ("Icarus's wings: feathers bound to a reed frame with leather and wax, the wax melted and a few feathers lost (asset P3.1). "
            "%.1f m across, hung on three wires; the origin is the harness, to be placed %.1f m up so the wires reach a 4 m ceiling. "
            "Art only: no collision. Their lowest feather stays above %.1f m." % (L.WING_SPAN, L.WING_HANG_Y, L.WING_MIN_Y))
    (PROPS / "icarus_wings.tscn").write_text(scene_text("IcarusWings", note, parts, [], nodes, "Mesh"), encoding="utf8", newline="\n")


def cleaning_scene():
    """The empty plinth whose statue is away for cleaning: the posing plinth with a different label."""
    (PROPS / "plinth_away_for_cleaning.tscn").write_text("""[gd_scene format=3]

[ext_resource type="PackedScene" path="res://scenes/statue_plinth.tscn" id="1_plinth"]
[ext_resource type="Material" path="%sint_label_galatea.tres" id="2_label"]

[sub_resource type="QuadMesh" id="QuadMesh_label"]
material = ExtResource("2_label")
size = Vector2(%.3f, %.3f)

[node name="PlinthAwayForCleaning" instance=ExtResource("1_plinth")]
editor_description = "An empty plinth: Galatea is away for cleaning (asset P3.1). It is scenes/statue_plinth.tscn with its own label, so a player standing on it empty-handed still passes for a statue."

[node name="Plaque" parent="."]
mesh = SubResource("QuadMesh_label")
""" % (RES, L.PLAQUE[0], L.PLAQUE[1]), encoding="utf8", newline="\n")


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.seed = 0
    scene.cycles.use_denoising = False


setup()
venus = statue("venus", D.PLINTH_H)
export("venus", [venus])
statue_scene("venus", venus, game_box((-0.25, -0.24, D.PLINTH_H + S.SLAB_H), (0.25, 0.22, D.PLINTH_H + 1.97)),
             "Venus, her arms long gone, on a museum plinth (asset P3.1). 2.6 m to the top of her head. The label says her arms "
             "were handed in to Lost Property. Origin on the floor; she and her label face +z.")
discus = statue("discus_thrower", D.PLINTH_H)
export("discus_thrower", [discus])
statue_scene("discus_thrower", discus, game_box((-0.42, -0.2, D.PLINTH_H + S.SLAB_H), (0.3, 0.2, D.PLINTH_H + 1.3)),
             "The Discus Thrower, wound up to throw, on a museum plinth (asset P3.1). He moves towards -x with the discus swung back "
             "high towards +x. Origin on the floor; the label faces +z.")
bust = statue("bust_homer", L.PED_H)
ped = pedestal()
export("bust_homer", [bust, ped])
bust_scene(bust, ped)
wing_mesh, wires = wings()
export("icarus_wings", [wing_mesh, wires])
wings_scene()
cleaning_scene()
log("sculpture built")
