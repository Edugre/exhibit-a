"""Background Blender job: a small low-poly pigeon. UV.x carries how far each vertex sits out along a
wing, so the flap can live entirely in a shader. usage: blender -b --factory-startup --python pigeon_build.py -- <out glb>"""
import math
import sys
import bmesh
import bpy

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.context.scene.objects):
    bpy.data.objects.remove(ob)


def blob(bm, c, r, sub=1):
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in res["verts"]:
        v.co.x = v.co.x * r[0] + c[0]
        v.co.y = v.co.y * r[1] + c[1]
        v.co.z = v.co.z * r[2] + c[2]


bm = bmesh.new()
blob(bm, (0, 0, 0.17), (0.075, 0.135, 0.085), 2)      # body, y is forward-back, z up
blob(bm, (0, -0.135, 0.255), (0.05, 0.055, 0.052), 2)  # head
blob(bm, (0, -0.095, 0.205), (0.052, 0.06, 0.06), 1)   # neck
blob(bm, (0, -0.19, 0.245), (0.012, 0.03, 0.012), 1)   # beak
# tail
v = [bm.verts.new(p) for p in ((-0.04, 0.10, 0.16), (0.04, 0.10, 0.16), (0.055, 0.27, 0.115), (-0.055, 0.27, 0.115))]
bm.faces.new(v)
# legs
for sx in (-1, 1):
    v = [bm.verts.new(p) for p in ((sx * 0.03, 0.0, 0.11), (sx * 0.045, 0.0, 0.11), (sx * 0.04, 0.01, 0.0), (sx * 0.03, 0.01, 0.0))]
    bm.faces.new(v)
    # wing, folded along the body at rest; the shader spreads it in flight
    p = [(sx * 0.07, -0.08, 0.20), (sx * 0.075, 0.09, 0.20), (sx * 0.20, 0.10, 0.205), (sx * 0.31, 0.04, 0.21), (sx * 0.17, -0.09, 0.205)]
    v = [bm.verts.new(q) for q in p]
    bm.faces.new(v if sx > 0 else v[::-1])
me = bpy.data.meshes.new("Pigeon")
bm.to_mesh(me)
bm.free()
uv = me.uv_layers.new(name="UVMap")
for loop in me.loops:
    co = me.vertices[loop.vertex_index].co
    uv.data[loop.index].uv = (max(abs(co.x) - 0.07, 0.0) / 0.24, 0.0)
m = bpy.data.materials.new("ext_pigeon")
me.materials.append(m)
ob = bpy.data.objects.new("Pigeon", me)
bpy.context.scene.collection.objects.link(ob)
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.shade_flat()
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_yup=True, export_materials="EXPORT", export_cameras=False, export_lights=False, export_animations=False)
print("PIGEON_TRIS", sum(len(p.vertices) - 2 for p in me.polygons), flush=True)
