"""Builds the conservation crates and the draped statue (asset item P1.1), in a background Blender:
  blender -b --factory-startup --python crates_build.py -- <assets/interior/crates folder> <scenes/props folder>
Writes one .glb per prop, their import settings (which hand each model its material), the prop scenes
with their collision, and the baked shading of the cloth's folds that make_crates_art.py lays into the
texture. Run make_crates_art.py afterwards.

Blender is z up and the game is y up: a prop's front, which faces the game's +z, is Blender's -y here."""
import math
import pathlib
import sys

import bmesh
import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import crates_layout as L  # noqa: E402
import int_dims as D  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
PROPS.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/crates/"
N = L.ATLAS


def uv(px, py):
    return (px / N, 1 - py / N)


def material(name):
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)


# --- Boxes with their texture placed per face ----------------------------------------------------------
def add_box(bm, layer, lo, hi, face_uv):
    """A box from corner lo to hi. face_uv(normal, point) gives each corner's texture position."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    v = [bm.verts.new(p) for p in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                     (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    faces = [((0, 1, 5, 4), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)), ((1, 2, 6, 5), (1, 0, 0)),
             ((3, 0, 4, 7), (-1, 0, 0)), ((4, 5, 6, 7), (0, 0, 1)), ((3, 2, 1, 0), (0, 0, -1))]
    for idx, normal in faces:
        f = bm.faces.new([v[i] for i in idx])
        for loop in f.loops:
            loop[layer].uv = face_uv(Vector(normal), loop.vert.co, lo, hi)


def cell_uv(cells):
    """Texture positions for a crate's plywood body: each side mapped onto its own cell, reading the right way round."""
    def fn(n, p, lo, hi):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        if abs(n.z) > 0.5:
            cx, cy, cw, ch = cells["top"]
            fu, fv = (p.x - x0) / (x1 - x0), 1 - (p.y - y0) / (y1 - y0)
        elif abs(n.y) > 0.5:
            cx, cy, cw, ch = cells["front"]
            fu = (p.x - x0) / (x1 - x0) if n.y < 0 else (x1 - p.x) / (x1 - x0)
            fv = 1 - (p.z - z0) / (z1 - z0)
        else:
            cx, cy, cw, ch = cells["side"]
            fu = (p.y - y0) / (y1 - y0) if n.x > 0 else (y1 - p.y) / (y1 - y0)
            fv = 1 - (p.z - z0) / (z1 - z0)
        return uv(cx + fu * cw, cy + fv * ch)
    return fn


def batten_uv(offset):
    """Pine battens: along the strip by length, across it by width, at 5 mm a pixel."""
    bx, by, bw, bh = L.RECTS["batten"]

    def fn(n, p, lo, hi):
        size = [hi[i] - lo[i] for i in range(3)]
        axes = [i for i in range(3) if abs(n[i]) < 0.5]
        a, b = sorted(axes, key=lambda i: -size[i])
        u = (p[a] - lo[a]) * L.PX_PER_M + offset
        v = (p[b] - lo[b]) * L.PX_PER_M + 6
        return uv(bx + u, by + v)
    return fn


def build_crate(name, w, d, h):
    t, b, s = L.BATTEN_T, L.BATTEN_W, L.SKID_H
    cells = {k: L.RECTS[name + "." + k] for k in ("front", "side", "top")}
    bm = bmesh.new()
    layer = bm.loops.layers.uv.new("UVMap")
    hw, hd = w / 2, d / 2
    add_box(bm, layer, (-hw + t, -hd + t, s), (hw - t, hd - t, h - t), cell_uv(cells))
    offsets = iter([17, 230, 455, 610, 81, 380, 520, 140, 300, 700, 40, 560, 260, 650, 420, 90, 330, 480, 200, 600, 30, 510])
    battens = []
    for sy in (-1, 1):      # front and back: a full-width rail top and bottom, posts between them at the ends
        y0, y1 = sorted((sy * (hd - t), sy * hd))
        battens += [((-hw, y0, s), (hw, y1, s + b)), ((-hw, y0, h - b), (hw, y1, h)),
                    ((-hw, y0, s + b), (-hw + b, y1, h - b)), ((hw - b, y0, s + b), (hw, y1, h - b))]
    for sx in (-1, 1):      # the ends: rails top and bottom, posts tucked in behind the front's
        x0, x1 = sorted((sx * (hw - t), sx * hw))
        battens += [((x0, -hd + t, s), (x1, hd - t, s + b)), ((x0, -hd + t, h - b), (x1, hd - t, h)),
                    ((x0, -hd + t, s + b), (x1, -hd + t + b, h - b)), ((x0, hd - t - b, s + b), (x1, hd - t, h - b))]
    # The lid's frame, flush with the rails, so another crate stacks on top
    battens += [((-hw + t, -hd + t, h - t), (hw - t, -hd + t + b, h)), ((-hw + t, hd - t - b, h - t), (hw - t, hd - t, h)),
                ((-hw + t, -hd + t + b, h - t), (-hw + t + b, hd - t - b, h)), ((hw - t - b, -hd + t + b, h - t), (hw - t, hd - t - b, h))]
    # Two skids underneath
    battens += [((-hw, sy * (hd - 0.12) - 0.04, 0.0), (hw, sy * (hd - 0.12) + 0.04, s)) for sy in (-1, 1)]
    for lo, hi in battens:
        add_box(bm, layer, lo, hi, batten_uv(next(offsets)))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material("int_crates"))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, (w, h, d)


# --- The draped statue: a cloth dropped over a figure on a plinth, simulated, then thinned out --------
def primitive(kind, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**kw)
    return bpy.context.active_object


def collider(obj, thickness=0.012):
    obj.modifiers.new("Collision", "COLLISION")
    obj.collision.thickness_outer = thickness
    obj.collision.cloth_friction = 8.0
    return obj


def build_statue():
    # The figure under the cloth: Medusa on her plinth, one arm raised, the snakes giving her head its lumps
    shapes = [
        primitive("cube", size=1, location=(0, 0, D.PLINTH_H / 2), scale=(0.86, 0.86, D.PLINTH_H)),
        primitive("cone", vertices=16, radius1=0.34, radius2=0.27, depth=0.82, location=(0, 0, D.PLINTH_H + 0.41)),
        primitive("cube", size=1, location=(0, 0, D.PLINTH_H + 0.86), scale=(0.74, 0.36, 0.2)),
        primitive("uv_sphere", radius=0.17, location=(0.0, -0.03, D.PLINTH_H + 1.13)),
        primitive("cylinder", vertices=10, radius=0.07, depth=0.7, location=(0.33, 0.0, D.PLINTH_H + 1.22), rotation=(0, math.radians(-10), 0)),
    ]
    for i in range(7):
        a = i / 7 * math.tau
        shapes.append(primitive("uv_sphere", radius=0.07, location=(0.16 * math.cos(a), 0.16 * math.sin(a) - 0.03, D.PLINTH_H + 1.19 + 0.03 * math.sin(a * 2))))
    floor = primitive("plane", size=6, location=(0, 0, 0))
    for s in shapes + [floor]:
        collider(s)

    # Big enough to reach the floor all round and pool a little, as a real drop cloth does
    cloth = primitive("grid", x_subdivisions=72, y_subdivisions=72, size=4.0, location=(0.05, -0.04, D.PLINTH_H + 1.62), rotation=(0, 0, math.radians(11)))
    cloth.name = "draped_statue"
    sim = cloth.modifiers.new("Cloth", "CLOTH")
    sim.settings.quality = 8
    sim.settings.mass = 0.35
    sim.settings.tension_stiffness = 12
    sim.settings.compression_stiffness = 12
    sim.settings.bending_stiffness = 0.4
    sim.settings.air_damping = 1.5
    sim.collision_settings.distance_min = 0.01
    sim.collision_settings.use_self_collision = False
    sim.point_cache.frame_start = 1
    sim.point_cache.frame_end = 110
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 110
    for f in range(1, 111):
        scene.frame_set(f)
    with bpy.context.temp_override(object=cloth, active_object=cloth, selected_objects=[cloth]):
        bpy.ops.object.modifier_apply(modifier="Cloth")
    scene.frame_set(1)
    # Bake the grid's starting place into its points, so the origin sits on the floor under the statue
    for o in scene.objects:
        o.select_set(False)
    cloth.select_set(True)
    bpy.context.view_layer.objects.active = cloth
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    dec = cloth.modifiers.new("Decimate", "DECIMATE")
    dec.ratio = 0.3
    with bpy.context.temp_override(object=cloth, active_object=cloth, selected_objects=[cloth]):
        bpy.ops.object.modifier_apply(modifier="Decimate")

    # The tag, pinned to her front at chest height, found by looking straight at the cloth
    origin = Vector((0.06, -3.0, D.PLINTH_H + 0.66))
    hit, at, normal, _ = cloth.ray_cast(cloth.matrix_world.inverted() @ origin, Vector((0, 1, 0)))
    at = cloth.matrix_world @ at if hit else Vector((0.06, -0.3, D.PLINTH_H + 0.62))
    for s in shapes + [floor]:
        bpy.data.objects.remove(s, do_unlink=True)

    bm = bmesh.new()
    bm.from_mesh(cloth.data)
    layer = bm.loops.layers.uv.verify()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(cloth.data)
    bm.free()
    bpy.context.view_layer.objects.active = cloth
    cloth.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")
    cx, cy, cw, ch = L.RECTS["cloth"]
    for loop_uv in cloth.data.uv_layers.active.data:
        u, v = loop_uv.uv
        loop_uv.uv = uv(cx + u * cw, cy + (1 - v) * ch)

    # The tag itself: a small card standing just off the cloth, tilted the way it hangs
    bm = bmesh.new()
    bm.from_mesh(cloth.data)
    layer = bm.loops.layers.uv.active
    tx, ty, tw, th = L.RECTS["tag"]
    half_w, half_h = 0.065, 0.044
    centre = at + Vector((0, -0.012, 0))
    tilt = math.radians(-8)
    right = Vector((math.cos(tilt), 0, math.sin(tilt)))
    up = Vector((-math.sin(tilt), 0, math.cos(tilt)))
    corners = [centre - right * half_w - up * half_h, centre + right * half_w - up * half_h,
               centre + right * half_w + up * half_h, centre - right * half_w + up * half_h]
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, (fu, fv) in zip(face.loops, [(0, 1), (1, 1), (1, 0), (0, 0)]):
        loop[layer].uv = uv(tx + fu * tw, ty + fv * th)
    bm.to_mesh(cloth.data)
    bm.free()
    for poly in cloth.data.polygons:
        poly.use_smooth = True
    cloth.data.validate()
    cloth.data.materials.clear()
    cloth.data.materials.append(material("int_cloth"))
    lo = [min(v.co[i] for v in cloth.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in cloth.data.vertices) for i in range(3)]
    return cloth, lo, hi


def bake_cloth_shading(cloth):
    """Bakes how much of the room each point of the cloth sees, so the folds and the hem read as shadowed."""
    scene = bpy.context.scene
    try:
        scene.render.engine = "CYCLES"
    except TypeError as error:
        print("no Cycles, cloth shading not baked:", error)
        return
    scene.cycles.samples = 48
    scene.cycles.device = "CPU"
    world = bpy.data.worlds.new("bake")
    scene.world = world
    world.light_settings.distance = 0.35
    floor = primitive("plane", size=6, location=(0, 0, 0))
    image = bpy.data.images.new("cloth_ao", N, N, alpha=False)
    mat = cloth.data.materials[0]
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = image
    mat.node_tree.nodes.active = node
    for o in scene.objects:
        o.select_set(False)
    cloth.select_set(True)
    bpy.context.view_layer.objects.active = cloth
    scene.render.bake.margin = 6
    bpy.ops.object.bake(type="AO")
    image.filepath_raw = str(TOOLS.parent / "crates_cloth_ao.png")
    image.file_format = "PNG"
    image.save()
    mat.node_tree.nodes.remove(node)
    bpy.data.objects.remove(floor, do_unlink=True)


# --- Export, import settings and prop scenes ----------------------------------------------------------
GLB_IMPORT = """[remap]

importer="scene"
importer_version=1
type="PackedScene"

[deps]

source_file="{res}{name}.glb"

[params]

nodes/root_type=""
nodes/root_name=""
nodes/apply_root_scale=true
nodes/root_scale=1.0
meshes/ensure_tangents=true
meshes/generate_lods=true
meshes/create_shadow_meshes=true
meshes/light_baking=1
meshes/lightmap_texel_size=0.2
meshes/force_disable_compression=false
animation/import=false
materials/extract=0
_subresources={{
"materials": {{
"{mat}": {{
"use_external/enabled": true,
"use_external/fallback_path": "{res}{mat}.tres",
"use_external/path": "{res}{mat}.tres"
}}
}}
}}
gltf/naming_version=2
gltf/embedded_image_handling=1
"""


def export(obj, mat):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(OUT / (obj.name + ".glb")), export_format="GLB", use_selection=True,
                              use_active_scene=True, export_yup=True, export_materials="EXPORT",
                              export_cameras=False, export_lights=False, export_animations=False)
    target = OUT / (obj.name + ".glb.import")
    if not target.exists():
        target.write_text(GLB_IMPORT.format(res=RES, name=obj.name, mat=mat), encoding="utf8", newline="\n")
    print("exported", obj.name, len(obj.data.polygons), "faces")


def prop_scene(name, size, centre, note):
    """size and centre are the collision box, in the game's axes (x, up, z)."""
    (PROPS / (name + ".tscn")).write_text("""[gd_scene format=3]

[ext_resource type="PackedScene" path="{res}{name}.glb" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_body"]
size = Vector3({sx:.3f}, {sy:.3f}, {sz:.3f})

[node name="{title}" type="Node3D"]
editor_description = "{note}"

[node name="Mesh" parent="." instance=ExtResource("1_mesh")]

[node name="Body" type="StaticBody3D" parent="."]

[node name="Shape" type="CollisionShape3D" parent="Body"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {cx:.3f}, {cy:.3f}, {cz:.3f})
shape = SubResource("BoxShape3D_body")
""".format(res=RES, name=name, title="".join(p.title() for p in name.split("_")), note=note,
           sx=size[0], sy=size[1], sz=size[2], cx=centre[0], cy=centre[1], cz=centre[2]), encoding="utf8", newline="\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
notes = {
    "crate_small": "Small conservation crate, 0.7 m. Not cover on its own: stack two, or set one on a cover crate.",
    "crate_cover": "Conservation crate at cover height, 1.4 m: hides a player from the guard. Pandora's jar, a gift from the Greeks.",
    "crate_painting": "Tall flat crate for a painting, 2.1 m. Full cover, but only 0.5 m deep.",
}
for name, (w, d, h) in L.CRATES.items():
    obj, (gw, gh, gd) = build_crate(name, w, d, h)
    export(obj, "int_crates")
    prop_scene(name, (gw, gh, gd), (0, gh / 2, 0), notes[name])
statue, lo, hi = build_statue()
bake_cloth_shading(statue)
export(statue, "int_cloth")
plinth = 0.86      # the box covers the plinth and figure, not the cloth pooled on the floor round them
prop_scene("draped_statue", (plinth, round(hi[2], 2), plinth), (0, round(hi[2], 2) / 2, 0),
           "A statue under a drop cloth, about 1.9 m tall: full cover. The tag says it's Medusa, on loan. Do not uncover.")
print("statue bounds", [round(v, 2) for v in lo], [round(v, 2) for v in hi])
print("crates built")
