"""Background Blender job: the water of the two plaza fountains, modelled on reference photos. Rows of
thin arcs rise from the edges of the basin and lean inward; a tall plume stands in the middle. Each jet
is a pair of crossed ribbons. UV.x runs along the jet, UV.y is that jet's own random seed, and the
moving water is entirely in the shader. usage: blender -b --factory-startup --python fountain_build.py -- <out glb>"""
import importlib
import math
import pathlib
import random
import sys
import bpy

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import ext_dims as D
importlib.reload(D)

OUT = sys.argv[sys.argv.index("--") + 1]
rng = random.Random(7)
V, UV, F = [], [], []


def arc(start, end, peak, width, seed, segs=10):
    """One jet, from start to end with its top peak metres above the line between them."""
    dx, dz = end[0] - start[0], end[2] - start[2]
    ln = math.hypot(dx, dz) or 1.0
    sx, sz = -dz / ln, dx / ln
    for side, (ax, ay, az) in enumerate(((sx, 0.0, sz), (0.0, 1.0, 0.0))):
        base = len(V)
        for i in range(segs + 1):
            t = i / segs
            x = start[0] + dx * t
            z = start[2] + dz * t
            y = start[1] + (end[1] - start[1]) * t + 4.0 * peak * t * (1.0 - t)
            w = width * (1.0 + 1.4 * t)
            V.append((x - ax * w, y - ay * w, z - az * w))
            V.append((x + ax * w, y + ay * w, z + az * w))
            UV.append((t, seed))
            UV.append((t, seed))
        for i in range(segs):
            a = base + i * 2
            F.append((a, a + 1, a + 3, a + 2))


for sx in (-1, 1):
    cx, cz = sx * D.FOUNTAIN_X, D.FOUNTAIN_Z
    y0 = D.PLAZA_Y + 0.2
    edge = D.FOUNTAIN_SIZE / 2 - 0.95
    # Four rows of arcs along the edges, leaning in
    for i in range(9):
        t = (i + 0.5) / 9 * 2 - 1
        for ax, az in ((t * edge, -edge), (t * edge, edge), (-edge, t * edge), (edge, t * edge)):
            start = (cx + ax, y0, cz + az)
            reach = rng.uniform(0.34, 0.5)
            end = (cx + ax * reach, y0, cz + az * reach)
            arc(start, end, rng.uniform(2.3, 3.5), 0.016, rng.random())
    # A second, lower ring inside them
    for i in range(14):
        a = math.tau * i / 14
        r = 3.3
        start = (cx + r * math.cos(a), y0, cz + r * math.sin(a))
        end = (cx + r * 0.42 * math.cos(a + 0.4), y0, cz + r * 0.42 * math.sin(a + 0.4))
        arc(start, end, rng.uniform(1.3, 2.0), 0.014, rng.random(), 8)
    # The central plume, a sheaf of jets going nearly straight up
    for i in range(30):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.02, 0.32)
        out = rng.uniform(0.25, 1.5)
        start = (cx + r * math.cos(a), y0, cz + r * math.sin(a))
        end = (cx + (r + out) * math.cos(a), y0, cz + (r + out) * math.sin(a))
        arc(start, end, rng.uniform(3.7, 6.2), 0.03, rng.random())

me = bpy.data.meshes.new("FountainJets")
me.from_pydata(V, [], F)
me.update()
layer = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    for li in poly.loop_indices:
        layer.data[li].uv = UV[me.loops[li].vertex_index]
m = bpy.data.materials.new("ext_jet")
me.materials.append(m)
for ob in list(bpy.context.scene.objects):
    bpy.data.objects.remove(ob)
ob = bpy.data.objects.new("FountainJets", me)
bpy.context.scene.collection.objects.link(ob)
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
# Blender is z up: the exporter turns (x, y, z) into (x, z, -y), so hand it the inverse
for v in me.vertices:
    x, y, z = v.co
    v.co = (x, -z, y)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_materials="EXPORT", export_cameras=False, export_lights=False, export_animations=False)
print("JET_TRIS", len(F) * 2, flush=True)
