"""Background Blender job: builds the capital, fuses it into one block and renders review views.
usage: blender -b --factory-startup --python cap_build.py -- <grid res m> <voxel m> <out dir> [samples]"""
import importlib, math, pathlib, sys, time
import bpy
import numpy as np
from mathutils import Vector

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import cap_gen
importlib.reload(cap_gen)

argv = sys.argv[sys.argv.index("--") + 1:]
RES, VOX = float(argv[0]), float(argv[1])
OUT = pathlib.Path(argv[2])
OUT.mkdir(parents=True, exist_ok=True)
SAMPLES = int(argv[3]) if len(argv) > 3 else 48
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


def setup_cycles(scene, samples):
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1100, 1100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else "Filmic"


def stone(ob):
    m = bpy.data.materials.new("Stone")
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (0.60, 0.555, 0.49, 1)
    p.inputs["Roughness"].default_value = 0.85
    ob.data.materials.append(m)


def lights_and_camera(scene):
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.035, 0.05, 0.09, 1)
    bg.inputs[1].default_value = 1.0
    scene.world = w
    sd = bpy.data.lights.new("Up", "SPOT")
    sd.energy = 26000
    sd.color = (1.0, 0.72, 0.42)
    sd.spot_size = math.radians(70)
    sd.shadow_soft_size = 0.2
    up = bpy.data.objects.new("Up", sd)
    scene.collection.objects.link(up)
    up.location = (1.6, -4.5, -12.0)
    up.rotation_euler = (Vector((0, 0, 1)) - up.location).to_track_quat("-Z", "Y").to_euler()
    moon = bpy.data.lights.new("Moon", "SUN")
    moon.energy = 0.5
    moon.color = (0.6, 0.72, 1.0)
    mo = bpy.data.objects.new("Moon", moon)
    scene.collection.objects.link(mo)
    mo.rotation_euler = (math.radians(55), 0, math.radians(-30))
    cd = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def shoot(scene, cam, name, eye, target, lens):
    e, t = Vector(eye), Vector(target)
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    log("rendered", name)


def main():
    scene = bpy.context.scene
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob)
    v, f = cap_gen.build(RES)
    log("generated", len(v), "verts", len(f), "tris")
    ob = to_mesh("HP_Capital", v, f)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    mod = ob.modifiers.new("fuse", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = VOX
    mod.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    log("fused", len(ob.data.vertices), "verts", len(ob.data.polygons), "faces")
    sm = ob.modifiers.new("soften", "SMOOTH")
    sm.factor = 0.5
    sm.iterations = 2
    bpy.ops.object.modifier_apply(modifier=sm.name)
    stone(ob)
    if "--save" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "capital_hp.blend"), compress=True)
    setup_cycles(scene, SAMPLES)
    cam = lights_and_camera(scene)
    shoot(scene, cam, "front", (0, -6.0, 0.95), (0, 0, 0.95), 62)
    shoot(scene, cam, "quarter", (3.6, -4.4, 0.9), (0, 0, 0.95), 62)
    shoot(scene, cam, "below", (2.2, -4.2, -2.6), (0, -0.2, 1.0), 58)
    log("done")


main()
