"""Background Blender job: the grey blockout with the finished bay cut out of it.
usage: blender -b <exterior_blockout.blend> --python context_build.py -- <out glb>"""
import sys
import bmesh
import bpy

out = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene
print("scene", scene.name, [o.name for o in scene.objects if o.type == "MESH"], flush=True)
total = 0
for ob in list(scene.objects):
    if ob.type != "MESH":
        bpy.data.objects.remove(ob)
        continue
    if ob.name.startswith("Blockout_Steps"):
        bpy.data.objects.remove(ob)
        continue
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for x in (-14.0, -10.2, 10.2, 14.0):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 19.0), plane_no=(0, 0, 1))
    dead = []
    for f in bm.faces:
        c = f.calc_center_median()
        x, y, z = c.x, c.z, -c.y   # to Godot
        bay = abs(x) < 10.2 and y > -0.01 and z > 6.0
        upper = abs(x) < 14.0 and y > 18.99 and z > -5.0
        cheek = abs(x) < 13.0 and 14.8 < z < 25 and y > -4.6
        terrace = ob.name.startswith("Blockout_Paving") and 5.9 < z < 15.0
        if bay or upper or cheek or terrace:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    total += sum(len(p.vertices) - 2 for p in ob.data.polygons)
for ob in scene.objects:
    ob.select_set(True)
bpy.context.view_layer.objects.active = next(iter(scene.objects))
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_yup=True, export_cameras=False, export_lights=False, export_animations=False)
print("CONTEXT_TRIS", total, flush=True)
