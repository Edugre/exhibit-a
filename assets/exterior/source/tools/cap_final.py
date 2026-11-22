"""Background Blender job: final capital. Sculpt, wear, game mesh, UVs, bakes, export.
usage: blender -b --factory-startup --python cap_final.py -- <out dir> <grid res> <voxel> <wedge tris> <tex size>"""
import importlib, math, pathlib, sys, time
import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import cap_gen
importlib.reload(cap_gen)

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(argv[0])
RES, VOX = float(argv[1]), float(argv[2])
WEDGE_TRIS = int(argv[3])
TEX = int(argv[4])
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
    ob.hide_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def apply_mod(ob, kind, **kw):
    activate(ob)
    m = ob.modifiers.new("m", kind)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.ops.object.modifier_apply(modifier=m.name)


# --- wear ---------------------------------------------------------------------------------------
def value_noise(p, freq, seed):
    """Smooth 3D noise, from a repeating table of random numbers, sampled with numpy."""
    rng = np.random.default_rng(seed)
    n = 64
    table = rng.random((n, n, n), dtype=np.float32)
    q = p * freq
    i = np.floor(q).astype(np.int64)
    f = q - i
    u = f * f * (3 - 2 * f)
    i %= n
    j = (i + 1) % n
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                ix, iy, iz = (j[:, 0] if dx else i[:, 0]), (j[:, 1] if dy else i[:, 1]), (j[:, 2] if dz else i[:, 2])
                wx = u[:, 0] if dx else 1 - u[:, 0]
                wy = u[:, 1] if dy else 1 - u[:, 1]
                wz = u[:, 2] if dz else 1 - u[:, 2]
                out = out + table[ix, iy, iz] * wx * wy * wz
    return out * 2 - 1


def add_wear(ob):
    """Gentle hand-cut unevenness and pitting, so the stone is not machine smooth."""
    me = ob.data
    n = len(me.vertices)
    co = np.zeros(n * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    nor = np.zeros(n * 3, dtype=np.float32)
    me.vertex_normals.foreach_get("vector", nor)
    nor = nor.reshape(-1, 3)
    d = (value_noise(co, 9.0, 1) * 0.0035 + value_noise(co, 31.0, 2) * 0.0016 + value_noise(co, 110.0, 3) * 0.0008)
    pits = np.clip(value_noise(co, 70.0, 4) - 0.55, 0, 1) * 0.012
    co = co + nor * (d - pits)[:, None]
    me.vertices.foreach_set("co", co.ravel())
    me.update()


# --- game mesh ----------------------------------------------------------------------------------
def build_game_mesh(hp):
    me = hp.data.copy()
    ob = bpy.data.objects.new("LP_Wedge", me)
    bpy.context.scene.collection.objects.link(ob)
    apply_mod(ob, "REMESH", mode="VOXEL", voxel_size=0.012, use_smooth_shade=False)
    apply_mod(ob, "SMOOTH", factor=0.5, iterations=4)
    log("mid mesh", len(ob.data.polygons))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # keep the wedge from the front axis (x = 0) to the corner diagonal (x + y = 0)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 1, 0), clear_outer=True)
    # Faces buried in the shaft or under the entablature are never seen
    dead = [f for f in bm.faces if f.calc_center_median().z > cap_gen.H - 0.004 or f.calc_center_median().z < -0.125]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    log("wedge", len(ob.data.polygons))
    apply_mod(ob, "TRIANGULATE")
    ratio = WEDGE_TRIS / max(len(ob.data.polygons), 1)
    apply_mod(ob, "DECIMATE", decimate_type="COLLAPSE", ratio=ratio)
    log("decimated", len(ob.data.polygons), "tris")
    # Put the cut edges exactly back on their mirror planes, so the copies meet with no gap
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for v in bm.verts:
        if not v.is_boundary:
            continue
        x, y = v.co.x, v.co.y
        if abs(x) < 0.03:
            v.co.x = 0.0
        elif abs(x + y) < 0.03:
            m = (x - y) / 2
            v.co.x, v.co.y = m, -m
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def unwrap(ob):
    activate(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=0.006, area_weight=0.0, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("unwrapped")


def mirror_round(ob):
    """Copy the wedge round the square's eight positions, sharing UVs, and weld it."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    src = list(bm.faces)
    raw = [([tuple(l.vert.co) for l in f.loops], [tuple(l[uv].uv) for l in f.loops]) for f in src]
    bm.free()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for q in range(4):
        a = q * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        for mirror in (False, True):
            for pts, uvs in raw:
                seq = list(zip(pts, uvs))
                if mirror:
                    seq = seq[::-1]
                vs = []
                for (x, y, z), _ in seq:
                    x2 = -x if mirror else x
                    vs.append(bm.verts.new((c * x2 - s * y, s * x2 + c * y, z)))
                f = bm.faces.new(vs)
                for l, (_, t) in zip(f.loops, seq):
                    l[uv].uv = t
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0015)
    me = bpy.data.meshes.new("Capital")
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), dtype=bool))
    me.update()
    full = bpy.data.objects.new("Capital", me)
    bpy.context.scene.collection.objects.link(full)
    log("full game mesh", len(me.polygons), "tris", len(me.vertices), "verts")
    return full


# --- bakes --------------------------------------------------------------------------------------
def image(name, colorspace, fmt="PNG"):
    img = bpy.data.images.new(name, TEX, TEX, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img


def bake(lp, hp, img, kind, **kw):
    mat = lp.data.materials[0]
    nt = mat.node_tree
    n = next((x for x in nt.nodes if x.name == "BAKE_TARGET"), None) or nt.nodes.new("ShaderNodeTexImage")
    n.name = "BAKE_TARGET"
    n.image = img
    nt.nodes.active = n
    for o in bpy.context.scene.objects:
        o.select_set(False)
    hp.select_set(True)
    lp.select_set(True)
    bpy.context.view_layer.objects.active = lp
    bpy.ops.object.bake(type=kind, use_selected_to_active=True, **kw)
    img.filepath_raw = str(OUT / f"{img.name}.png")
    img.file_format = "PNG"
    img.save()
    log("baked", img.name)


def ao_material(distance):
    m = bpy.data.materials.get("HP_AO") or bpy.data.materials.new("HP_AO")
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

    v, f = cap_gen.build(RES)
    log("generated", len(f), "tris")
    hp = to_mesh("HP_Capital", v, f)
    apply_mod(hp, "REMESH", mode="VOXEL", voxel_size=VOX, use_smooth_shade=True)
    apply_mod(hp, "SMOOTH", factor=0.5, iterations=2)
    log("fused", len(hp.data.polygons))
    add_wear(hp)
    log("wear added")

    lp = build_game_mesh(hp)
    unwrap(lp)
    full = mirror_round(lp)
    bpy.data.objects.remove(lp)
    mat = bpy.data.materials.new("ext_carved")
    mat.use_nodes = True
    full.data.materials.append(mat)
    hp.data.materials.append(ao_material(0.4))

    b = scene.render.bake
    b.margin = 12
    b.margin_type = "EXTEND"
    b.use_clear = True
    b.target = "IMAGE_TEXTURES"
    b.cage_extrusion = 0.035
    b.max_ray_distance = 0.11
    scene.cycles.samples = 16
    bake(full, hp, image("cap_normal", "Non-Color"), "NORMAL", normal_space="TANGENT")
    scene.cycles.samples = 128
    bake(full, hp, image("cap_ao_wide", "Non-Color"), "EMIT")
    ao_tight = ao_material(0.05)
    bake(full, hp, image("cap_ao_tight", "Non-Color"), "EMIT")

    # The atlas keeps its top quarter for the bracket and keystone
    for loop_uv in full.data.uv_layers.active.data:
        loop_uv.uv = (loop_uv.uv[0], loop_uv.uv[1] * 0.75)
    activate(full)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "capital.glb"), export_format="GLB", use_selection=True, export_tangents=True,
                              export_yup=True, export_cameras=False, export_lights=False, export_animations=False, export_materials="EXPORT")
    log("exported capital.glb")
    tris = sum(len(p.vertices) - 2 for p in full.data.polygons)
    print("GAME_TRIS", tris, flush=True)
    bpy.data.objects.remove(hp)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "capital_game.blend"), compress=True)
    log("done")


main()
