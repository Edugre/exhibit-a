"""Background Blender job: the carved bracket under the cornice and the owl keystone.
Each is sculpted, fused, reduced to a game mesh, unwrapped and baked, the same way as the capital.
usage: blender -b --factory-startup --python orn_final.py -- <out dir> <voxel> <tex size>"""
import importlib, math, pathlib, sys, time
import bmesh
import bpy
import numpy as np

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import cap_gen
importlib.reload(cap_gen)
from cap_gen import Acc, blob, lathe, bezier, sweep, normalize, sstep, TAU

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(argv[0])
VOX = float(argv[1])
TEX = int(argv[2])
OUT.mkdir(parents=True, exist_ok=True)
t0 = time.time()


def log(*a):
    print("[%6.1fs]" % (time.time() - t0), *a, flush=True)


def to_mesh(name, v, f):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v))
    me.vertices.foreach_set("co", np.asarray(v, dtype=np.float32).ravel())
    me.loops.add(f.size)
    me.polygons.add(len(f))
    me.polygons.foreach_set("loop_start", np.arange(len(f), dtype=np.int32) * 3)
    me.loops.foreach_set("vertex_index", np.asarray(f, dtype=np.int32).ravel())
    me.update(calc_edges=True)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


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


def fused(name, v, f, vox):
    ob = to_mesh(name, v, f)
    apply_mod(ob, "REMESH", mode="VOXEL", voxel_size=vox, use_smooth_shade=True)
    apply_mod(ob, "SMOOTH", factor=0.5, iterations=2)
    return ob


def box_tris(x0, x1, y0, y1, z0, z1):
    v = np.array([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], dtype=np.float32)
    q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    f = []
    for a, b, c, d in q:
        f += [(a, b, c), (a, c, d)]
    return v, np.array(f)


def extrude_profile(pts, x0, x1):
    """A closed side outline (y, z) extruded across x, capped with a fan."""
    p = np.asarray(pts, dtype=np.float64)
    n = len(p)
    v = np.concatenate([np.stack([np.full(n, x0), p[:, 0], p[:, 1]], -1), np.stack([np.full(n, x1), p[:, 0], p[:, 1]], -1)])
    c = p.mean(0)
    v = np.concatenate([v, [[x0, c[0], c[1]], [x1, c[0], c[1]]]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [(i, j, n + j), (i, n + j, n + i), (i, 2 * n, j), (n + i, n + j, 2 * n + 1)]
    return v, np.array(f)


def side_spiral(eye_y, eye_z, rho0, rho1, turns, x, hand, band, thick):
    """A ribbon spiral standing on the side of a bracket."""
    ang = np.linspace(0, turns * TAU, 260)
    b = math.log(rho0 / rho1) / (turns * TAU)
    rho = rho0 * np.exp(-b * ang)
    y = eye_y + rho * np.sin(hand * ang)
    z = eye_z + rho * np.cos(ang)
    path = np.stack([np.full_like(y, x), y, z], -1)
    tang = normalize(np.gradient(path, axis=0))
    side = np.tile(np.array([1.0, 0.0, 0.0]), (len(y), 1))
    up = normalize(np.cross(tang, side)) * (-hand)
    sec = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
    return sweep(path, side, up, sec, np.full_like(y, band / 2), np.linspace(thick, thick * 0.45, len(y)) / 2)


# --- The bracket --------------------------------------------------------------------------------
def modillion():
    """Local space: x across (width 0.40), y outwards from the wall (0 to 1.0), z up, 0 at the soffit."""
    acc = Acc()
    ys = np.linspace(0, 1.0, 40)
    # the underside falls from the big scroll at the wall to the small one at the tip
    under = -0.40 + 0.20 * sstep(0.18, 0.72, ys) + 0.035 * np.sin(ys * 7.0)
    top = [(1.04, 0.02), (-0.02, 0.02)]
    outline = top + [(float(y), float(z)) for y, z in zip(ys, under)]
    acc.add(*extrude_profile(outline, -0.185, 0.185))
    for sx in (-1, 1):
        x = sx * 0.17
        acc.add(*side_spiral(0.20, -0.21, 0.17, 0.024, 2.2, x, 1, 0.075, 0.042))
        acc.add(*side_spiral(0.88, -0.115, 0.098, 0.018, 1.9, x, -1, 0.06, 0.03))
    # The big and the small scroll, as round masses
    for y, z, r in ((0.20, -0.21, 0.185), (0.88, -0.115, 0.105)):
        v, f = lathe([(0.0, -0.20), (r, -0.20), (r, 0.20), (0.0, 0.20)], 48)
        acc.add(np.stack([v[:, 2], v[:, 0] + y, v[:, 1] + z], -1), f[:, ::-1])
    # A leaf down the underside, its tip curling at the small scroll
    spec = dict(res=0.003, rise=0.30, rise2=0.34, serr=0.26, mw=0.10, tile=0.012, wrap=1.0, skin=0.006, vgroove=0.42, L=0.86, W=0.17,
                lobes=[(0.02, 0.26, 0.72), (0.26, 0.50, 1.0), (0.50, 0.74, 0.92), (0.74, 1.0, 0.62)], r0=4.0, z0=0.0, phi0=0, phi1=0, curl=70, curl_at=0.74,
                flare=0.02, roll=0.01, h1=0.030, h2=0.026, thick=0.018)
    v, f = cap_gen.build_leaf(spec)
    # stand the leaf's length along +y, with its face looking down
    out = np.stack([v[:, 0], v[:, 2] + 0.10, -(-v[:, 1] - 4.0) - 0.0], -1)
    fall = np.interp(out[:, 1], ys, under)
    out[:, 2] = fall + (-out[:, 2])
    acc.add(out, f[:, ::-1])
    return acc.arrays()


# --- The owl keystone ---------------------------------------------------------------------------
def tube_path(acc, pts, r0, r1, n=60, segs=20):
    p0, p1, p2, p3 = (np.asarray(p, dtype=np.float64) for p in pts)
    path = bezier(p0, p1, p2, p3, n)
    tang = normalize(np.gradient(path, axis=0))
    ref = np.array([0.0, 0.0, 1.0])
    side = normalize(np.cross(tang, ref))
    up = normalize(np.cross(side, tang))
    a = np.linspace(0, TAU, segs, endpoint=False)
    sec = np.stack([np.cos(a), np.sin(a)], -1)
    r = np.linspace(r0, r1, n)
    acc.add(*sweep(path, side, up, sec, r, r))


def keystone():
    """Local space: x across, y up the face (0 at the crown of the arch), z outwards. Only x >= 0
    matters; the piece is cut on x = 0 and mirrored. An owl for Athena, on a scrolled console."""
    acc = Acc()
    # Console: wider at the top, leaning forward as it rises
    ys = np.array([-0.95, 1.55])
    prof = [(-0.05, -0.95), (0.22, -0.95), (0.60, 1.40), (0.60, 1.58), (0.70, 1.62), (0.70, 1.72), (-0.05, 1.72)]
    for sign in (1,):
        acc.add(*extrude_profile([(y, z) for z, y in prof], -0.46, 0.46))
    # Scrolls at the two sides of the console, top and bottom
    for sx in (-1, 1):
        for y, r, turns in ((1.28, 0.27, 2.2), (-0.60, 0.20, 2.0)):
            x = sx * 0.46
            v, f = lathe([(0.0, -0.05), (r, -0.05), (r, 0.06), (0.0, 0.06)], 48)
            acc.add(np.stack([v[:, 2] * sx + x, v[:, 0] + y, v[:, 1] + 0.36], -1), f if sx > 0 else f[:, ::-1])
            ang = np.linspace(0, turns * TAU, 240)
            b = math.log(r / 0.03) / (turns * TAU)
            rho = r * np.exp(-b * ang)
            yy = y + rho * np.cos(ang)
            zz = 0.36 + rho * np.sin(ang)
            path = np.stack([np.full_like(yy, x + sx * 0.07), yy, zz], -1)
            tang = normalize(np.gradient(path, axis=0))
            side = np.tile(np.array([1.0, 0.0, 0.0]), (len(yy), 1))
            up = normalize(np.cross(tang, side))
            acc.add(*sweep(path, side, up, [(-1, -1), (-1, 1), (1, 1), (1, -1)], np.full_like(yy, 0.04), np.linspace(0.03, 0.012, len(yy))))
    # The owl stands against the console
    zc = 0.62
    body_y = 0.05
    acc.add(*blob((0, body_y, zc), (0.40, 0.72, 0.30), 48))                 # body
    acc.add(*blob((0, 0.86, zc + 0.03), (0.40, 0.36, 0.33), 48))            # head
    for sx in (-1, 1):
        acc.add(*blob((sx * 0.185, 0.88, zc + 0.27), (0.195, 0.205, 0.075), 40))          # facial disc
        v, f = lathe([(0.0, 0.0), (0.105, 0.0), (0.105, 0.03), (0.075, 0.05), (0.0, 0.05)], 40)
        acc.add(np.stack([v[:, 0] + sx * 0.175, v[:, 1] + 0.90, v[:, 2] + zc + 0.325], -1), f[:, ::-1])  # eye ring
        acc.add(*blob((sx * 0.175, 0.90, zc + 0.375), (0.055, 0.055, 0.035), 24))          # eye
        tube_path(acc, [(sx * 0.03, 0.97, zc + 0.36), (sx * 0.12, 1.08, zc + 0.36), (sx * 0.26, 1.12, zc + 0.30), (sx * 0.38, 1.26, zc + 0.14)], 0.045, 0.012)  # brow into ear tuft
        # folded wing
        acc.add(*blob((sx * 0.37, 0.12, zc + 0.05), (0.13, 0.62, 0.20), 40))
        for i in range(6):
            y = 0.52 - i * 0.17
            tube_path(acc, [(sx * 0.30, y, zc + 0.19), (sx * 0.40, y - 0.02, zc + 0.21), (sx * 0.47, y - 0.07, zc + 0.14), (sx * 0.50, y - 0.14, zc + 0.04)], 0.032, 0.012, 30, 12)
    acc.add(*blob((0, 0.80, zc + 0.355), (0.05, 0.085, 0.075), 28))         # beak
    # Rows of chest feathers
    for row in range(8):
        y = 0.56 - row * 0.135
        w = 0.33 - abs(row - 3) * 0.028
        count = 5 + (row % 2)
        for i in range(count):
            x = (i - (count - 1) / 2) * (2 * w / max(count - 1, 1))
            inside = max(1.0 - (x / 0.40) ** 2 - ((y - body_y) / 0.72) ** 2, 0.02)
            z = zc + 0.30 * math.sqrt(inside) + 0.004
            acc.add(*blob((x, y, z), (0.086, 0.104, 0.040), 20))
    # Talons on a small tied scroll, the way the owl guards the library
    v, f = lathe([(0.0, -0.40), (0.075, -0.40), (0.085, -0.37), (0.075, -0.34), (0.075, 0.34), (0.085, 0.37), (0.075, 0.40), (0.0, 0.40)], 40)
    acc.add(np.stack([v[:, 2], v[:, 1] - 0.62, v[:, 0] + zc + 0.20], -1), f[:, ::-1])
    v, f = lathe([(0.0, -0.03), (0.09, -0.03), (0.09, 0.03), (0.0, 0.03)], 40)
    acc.add(np.stack([v[:, 2], v[:, 1] - 0.62, v[:, 0] + zc + 0.20], -1), f[:, ::-1])
    for sx in (-1, 1):
        for i in range(3):
            x = sx * (0.12 + i * 0.075)
            tube_path(acc, [(x, -0.46, zc + 0.27), (x, -0.50, zc + 0.31), (x, -0.56, zc + 0.31), (x, -0.61, zc + 0.27)], 0.03, 0.011, 24, 10)
    return acc.arrays()


# --- Game mesh, UVs, bakes ----------------------------------------------------------------------
def game_mesh(hp, name, tris, voxel, mirror):
    me = hp.data.copy()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    apply_mod(ob, "REMESH", mode="VOXEL", voxel_size=voxel, use_smooth_shade=False)
    apply_mod(ob, "SMOOTH", factor=0.5, iterations=3)
    if mirror:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
        bm.to_mesh(ob.data)
        bm.free()
    apply_mod(ob, "TRIANGULATE")
    apply_mod(ob, "DECIMATE", decimate_type="COLLAPSE", ratio=(tris / (2 if mirror else 1)) / max(len(ob.data.polygons), 1))
    if mirror:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        for v in bm.verts:
            if v.is_boundary and abs(v.co.x) < 0.03:
                v.co.x = 0.0
        bm.to_mesh(ob.data)
        bm.free()
    activate(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.012, area_weight=0.0, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    if mirror:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        raw = [([tuple(l.vert.co) for l in f.loops], [tuple(l[uv].uv) for l in f.loops]) for f in bm.faces]
        bm.free()
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        for flip in (False, True):
            for pts, uvs in raw:
                seq = list(zip(pts, uvs))[::-1] if flip else list(zip(pts, uvs))
                vs = [bm.verts.new((-p[0] if flip else p[0], p[1], p[2])) for p, _ in seq]
                f = bm.faces.new(vs)
                for l, (_, t) in zip(f.loops, seq):
                    l[uv].uv = t
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bm.to_mesh(ob.data)
        bm.free()
    ob.data.polygons.foreach_set("use_smooth", np.ones(len(ob.data.polygons), dtype=bool))
    ob.data.update()
    log(name, "game tris", sum(len(p.vertices) - 2 for p in ob.data.polygons))
    return ob


def ao_material(distance):
    m = bpy.data.materials.new(f"AO_{distance}")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 32
    ao.inputs["Distance"].default_value = distance
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(ao.outputs["AO"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def bake_one(lp, hp, tag, wide, tight):
    scene = bpy.context.scene
    mat = bpy.data.materials.new("ext_carved")
    mat.use_nodes = True
    lp.data.materials.clear()
    lp.data.materials.append(mat)
    nt = mat.node_tree
    n = nt.nodes.new("ShaderNodeTexImage")
    nt.nodes.active = n

    def run(name, kind, colorspace, **kw):
        img = bpy.data.images.new(f"{tag}_{name}", TEX, TEX, alpha=False, float_buffer=False)
        img.colorspace_settings.name = colorspace
        n.image = img
        for o in bpy.context.scene.objects:
            o.select_set(False)
        hp.select_set(True)
        lp.select_set(True)
        bpy.context.view_layer.objects.active = lp
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, **kw)
        img.filepath_raw = str(OUT / f"{tag}_{name}.png")
        img.file_format = "PNG"
        img.save()
        log("baked", tag, name)

    b = scene.render.bake
    b.margin = 8
    b.margin_type = "EXTEND"
    b.use_clear = True
    b.target = "IMAGE_TEXTURES"
    b.cage_extrusion = 0.03
    b.max_ray_distance = 0.09
    scene.cycles.samples = 16
    run("normal", "NORMAL", "Non-Color", normal_space="TANGENT")
    scene.cycles.samples = 96
    hp.data.materials.clear()
    hp.data.materials.append(ao_material(wide))
    run("ao_wide", "EMIT", "Non-Color")
    hp.data.materials[0] = ao_material(tight)
    run("ao_tight", "EMIT", "Non-Color")
    # Save the game mesh as plain arrays; the section places copies of it
    me = lp.data
    verts = np.zeros(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", verts)
    tris = []
    uvs = []
    uv = me.uv_layers.active.data
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        tris.append(tuple(t.vertices))
        uvs.append([tuple(uv[i].uv) for i in t.loops])
    np.savez(OUT / f"{tag}_game.npz", verts=verts.reshape(-1, 3), tris=np.array(tris), uvs=np.array(uvs, dtype=np.float32))


def main():
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.cycles.use_denoising = False

    v, f = modillion()
    hp = fused("HP_Modillion", v, f, VOX)
    log("modillion sculpt", len(hp.data.polygons))
    lp = game_mesh(hp, "Modillion", 130, 0.012, mirror=False)
    bake_one(lp, hp, "modillion", 0.16, 0.03)
    bpy.data.objects.remove(hp)
    bpy.data.objects.remove(lp)

    v, f = keystone()
    hp = fused("HP_Keystone", v, f, VOX)
    log("keystone sculpt", len(hp.data.polygons))
    lp = game_mesh(hp, "Keystone", 2000, 0.010, mirror=True)
    bake_one(lp, hp, "keystone", 0.30, 0.05)
    log("done")


def preview():
    from mathutils import Vector
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.cycles.samples = 32
    scene.render.resolution_x, scene.render.resolution_y = 800, 800
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    next(n for n in w.node_tree.nodes if n.type == "BACKGROUND").inputs[0].default_value = (0.05, 0.07, 0.12, 1)
    scene.world = w
    sd = bpy.data.lights.new("U", "SPOT")
    sd.energy = 900
    sd.color = (1, 0.8, 0.6)
    sd.spot_size = 1.2
    u = bpy.data.objects.new("U", sd)
    scene.collection.objects.link(u)
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    m = bpy.data.materials.new("S")
    m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.6, 0.56, 0.5, 1)

    def shot(ob, name, eye, target, light):
        for o in scene.objects:
            if o.type == "MESH":
                o.hide_render = o is not ob
        e, t = Vector(eye), Vector(target)
        cam.location = e
        cam.rotation_euler = (t - e).to_track_quat("-Z", "Y").to_euler()
        cd.lens = 70
        u.location = light
        u.rotation_euler = (t - Vector(light)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / f"{name}.png")
        bpy.ops.render.render(write_still=True)

    v, f = keystone()
    k = fused("K", v, f, VOX)
    k.data.materials.append(m)
    # the piece's y up, z out becomes Blender's z up, -y out
    k.rotation_euler = (math.radians(90), 0, 0)
    v, f = modillion()
    b = fused("M", v, f, VOX)
    b.data.materials.append(m)
    shot(k, "keystone_front", (0.0, -6.5, 0.4), (0, 0, 0.4), (1.5, -5, -3))
    shot(k, "keystone_below", (2.0, -5.0, -3.5), (0, -0.3, 0.3), (1.5, -5, -3))
    shot(b, "modillion_below", (1.3, 1.6, -2.4), (0, 0.5, -0.2), (1, 0.5, -3.0))


if "--preview" in argv:
    preview()
else:
    main()
