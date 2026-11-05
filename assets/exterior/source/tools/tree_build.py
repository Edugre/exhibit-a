"""Background Blender job: three plaza trees, chunky low-poly but properly tree-shaped. A trunk that forks
into real limbs, carrying many separate clumps of leaves, so the crown has gaps and an edge against the
sky instead of being one lump. UV.x stores how far out a leaf is, for the wind in the shader.
usage: blender -b --factory-startup --python tree_build.py -- <out glb>"""
import math
import random
import sys
import bmesh
import bpy

OUT = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.context.scene.objects):
    bpy.data.objects.remove(ob)


def limb(V, F, a, b, r0, r1, sides=5):
    """A tapering branch from a to b, in Blender's z-up axes."""
    ax = [b[i] - a[i] for i in range(3)]
    ln = math.sqrt(sum(q * q for q in ax)) or 1.0
    ax = [q / ln for q in ax]
    ref = (1.0, 0.0, 0.0) if abs(ax[0]) < 0.8 else (0.0, 1.0, 0.0)
    s = (ax[1] * ref[2] - ax[2] * ref[1], ax[2] * ref[0] - ax[0] * ref[2], ax[0] * ref[1] - ax[1] * ref[0])
    sl = math.sqrt(sum(q * q for q in s))
    s = tuple(q / sl for q in s)
    u = (ax[1] * s[2] - ax[2] * s[1], ax[2] * s[0] - ax[0] * s[2], ax[0] * s[1] - ax[1] * s[0])
    base = len(V)
    for p, r in ((a, r0), (b, r1)):
        for i in range(sides):
            t = math.tau * i / sides
            V.append(tuple(p[k] + r * (math.cos(t) * s[k] + math.sin(t) * u[k]) for k in range(3)))
    for i in range(sides):
        j = (i + 1) % sides
        F.append((base + i, base + j, base + sides + j, base + sides + i))


def clump(Vl, Fl, Ul, c, r, squash, rng, reach):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, -0.45), plane_no=(0, 0, 1), clear_inner=True)
    base = len(Vl)
    bm.verts.ensure_lookup_table()
    index = {v: i for i, v in enumerate(bm.verts)}
    for v in bm.verts:
        q = 1.0 + rng.uniform(-0.17, 0.17)
        Vl.append((c[0] + v.co.x * r * q, c[1] + v.co.y * r * q, c[2] + v.co.z * r * squash * q))
        Ul.append((reach, rng.random()))
    for f in bm.faces:
        Fl.append(tuple(base + index[v] for v in f.verts))
    bm.free()


def tree(seed, height, spread):
    rng = random.Random(seed)
    Vb, Fb, Vl, Fl, Ul = [], [], [], [], []
    fork = (0.0, 0.0, height * 0.32)
    limb(Vb, Fb, (0.0, 0.0, -0.1), fork, 0.27, 0.2, 7)
    tips = []
    for i in range(5):
        a = math.tau * i / 5 + rng.uniform(-0.3, 0.3)
        r = spread * rng.uniform(0.42, 0.62)
        mid = (math.cos(a) * r, math.sin(a) * r, height * rng.uniform(0.52, 0.62))
        limb(Vb, Fb, fork, mid, 0.17, 0.09)
        for j in range(3):
            b = a + rng.uniform(-0.8, 0.8)
            q = spread * rng.uniform(0.62, 0.92)
            tip = (math.cos(b) * q, math.sin(b) * q, height * rng.uniform(0.66, 0.9))
            limb(Vb, Fb, mid, tip, 0.08, 0.035, 4)
            tips.append(tip)
    for tip in tips:
        for k in range(2):
            c = tuple(tip[i] + rng.uniform(-0.8, 0.8) for i in range(3))
            clump(Vl, Fl, Ul, c, rng.uniform(1.25, 1.95), 0.72, rng, math.hypot(c[0], c[1]) / spread)
    for k in range(10):
        a = rng.uniform(0, math.tau)
        q = spread * rng.uniform(0.1, 0.55)
        c = (math.cos(a) * q, math.sin(a) * q, height * rng.uniform(0.82, 1.0))
        clump(Vl, Fl, Ul, c, rng.uniform(1.5, 2.2), 0.68, rng, q / spread)
    return Vb, Fb, Vl, Fl, Ul


mat_bark = bpy.data.materials.new("ext_bark")
mat_leaf = bpy.data.materials.new("ext_leaf")
scene = bpy.context.scene
total = 0
for i, (seed, height, spread) in enumerate(((3, 11.0, 4.6), (11, 12.5, 5.2), (23, 10.0, 4.2))):
    Vb, Fb, Vl, Fl, Ul = tree(seed, height, spread)
    for name, V, F, mat, U in ((f"Tree{i}_Bark", Vb, Fb, mat_bark, None), (f"Tree{i}_Leaves", Vl, Fl, mat_leaf, Ul)):
        me = bpy.data.meshes.new(name)
        me.from_pydata(V, [], F)
        me.update()
        layer = me.uv_layers.new(name="UVMap")
        if U:
            for poly in me.polygons:
                for li in poly.loop_indices:
                    layer.data[li].uv = U[me.loops[li].vertex_index]
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        scene.collection.objects.link(ob)
        ob.select_set(True)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        total += sum(len(p.vertices) - 2 for p in me.polygons)
print("TREE_TRIS", total, flush=True)
bpy.context.view_layer.objects.active = scene.objects[0]
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_materials="EXPORT", export_cameras=False, export_lights=False, export_animations=False)
