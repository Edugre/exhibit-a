"""Builds the archive bookcases (asset item P2.3) in a background Blender:
  blender -b --factory-startup --python shelves_build.py -- <assets/interior/shelves folder> <scenes/props folder>
Writes bookcase_double.glb (books on both faces) and bookcase_wall.glb (books on the front only), their
import settings and their prop scenes. Run make_shelves_art.py for the texture and material.

Each shelf is filled with runs of books: a box per run, its front showing a stretch of one spine strip
picked by its height, so no two runs look alike. Blender is z up and the game is y up: a prop's
front, the game's +z, is Blender's -y."""
import math
import pathlib
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import shelves_layout as L  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/shelves/"
N = L.ATLAS


def uv_px(px, py):
    return (px / N, 1 - py / N)


def region_uv(name, fu, fv):
    x, y, w, h = L.REGIONS[name]
    return uv_px(x + 1 + fu * (w - 2), y + 1 + fv * (h - 2))


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")

    def quad(self, corners, uvs):
        face = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        for loop, coord in zip(face.loops, uvs):
            loop[self.layer].uv = coord
        return face

    def box(self, lo, hi, textures, transform=None):
        """textures maps a side (front, back, left, right, top, bottom) to a region name, or to a
        function giving that side's four texture positions. Sides left out aren't built."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        sides = {
            "front": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "back": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            "right": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            "left": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            "top": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            "bottom": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        }
        for side, corners in sides.items():
            tex = textures.get(side)
            if tex is None:
                continue
            if transform is not None:
                corners = [transform @ Vector(c) for c in corners]
            uvs = tex() if callable(tex) else [region_uv(tex, *f) for f in ((0, 1), (1, 1), (1, 0), (0, 0))]
            self.quad(corners, uvs)

    def finish(self, name):
        mesh = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        mesh.materials.append(bpy.data.materials.get("int_shelves") or bpy.data.materials.new("int_shelves"))
        mesh.validate()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def spine_strip(row, width_m, rng):
    """Texture positions for a run of books: a stretch of the row's strip as wide as the run."""
    x, y, w, h = L.REGIONS[row]
    span = width_m * L.SPINE_PX_PER_M
    start = rng.uniform(0, w - span - 2)
    u0, u1 = x + start, x + start + span
    return lambda: [uv_px(u0, y + h - 1), uv_px(u1, y + h - 1), uv_px(u1, y + 1), uv_px(u0, y + 1)]


def fill_shelf(b, x0, x1, z, clear, front_y, back_y, facing, rng):
    """Runs of books along one shelf, facing -y (facing=1) or +y (facing=-1)."""
    x = x0 + 0.01
    while x < x1 - 0.06:
        if rng.random() < 0.1:                    # a gap, sometimes with one book leaning into it
            gap = rng.uniform(0.06, 0.14)
            if rng.random() < 0.6 and x + gap < x1:
                lean = math.radians(rng.uniform(12, 22))
                bh = clear * rng.uniform(0.7, 0.85)
                depth = rng.uniform(0.17, 0.22)
                pivot = Vector((x + gap - 0.035, 0, z))
                t = Matrix.Translation(pivot) @ Matrix.Rotation(lean, 4, "Y") @ Matrix.Translation(-pivot)
                y_front = front_y + facing * (abs(back_y - front_y) - depth)
                lo = (x + gap - 0.065, min(y_front, back_y), z)
                hi = (x + gap - 0.035, max(y_front, back_y), z + bh)
                row = L.ROWS[min(int((bh / clear - 0.55) / 0.15), 2)]
                b.box(lo, hi, {("front" if facing > 0 else "back"): spine_strip(row, 0.03, rng), "top": "pages",
                               "left": "cover", "right": "cover"}, transform=t)
            x += gap
            continue
        run = min(rng.uniform(0.09, 0.3), x1 - 0.01 - x)
        frac = rng.uniform(0.6, 0.94)
        bh = clear * frac
        row = L.ROWS[0 if frac < 0.72 else (1 if frac < 0.84 else 2)]
        depth = rng.uniform(0.17, 0.24)
        y_front = front_y + facing * (abs(back_y - front_y) - depth) * rng.uniform(0.0, 0.25)
        lo = (x, min(y_front, back_y), z)
        hi = (x + run, max(y_front, back_y), z + bh)
        face = "front" if facing > 0 else "back"
        b.box(lo, hi, {face: spine_strip(row, run, rng), "top": "pages", "left": "cover", "right": "cover"})
        x += run + rng.uniform(0.0, 0.006)


def build(name, depth, double, seed):
    rng = random.Random(seed)
    b = Builder()
    w = L.UNIT_W / 2
    p = L.PANEL
    h = L.HEIGHT
    y_front, y_back = -depth / 2, depth / 2
    wood_all = {s: "wood" for s in ("front", "back", "left", "right", "top", "bottom")}
    # Carcass: two sides, a kick, the moulded top, and a back (or a centre panel for the double)
    b.box((-w, y_front, 0), (-w + p, y_back, h - L.CROWN), wood_all)
    b.box((w - p, y_front, 0), (w, y_back, h - L.CROWN), wood_all)
    b.box((-w + p, y_front + 0.03, 0), (w - p, y_back - 0.03, L.KICK), {k: "wood" for k in ("front", "back", "top")})
    b.box((-w - 0.02, y_front - 0.025, h - L.CROWN), (w + 0.02, y_back + 0.025, h), wood_all)
    b.box((-w - 0.01, y_front - 0.012, h - L.CROWN - 0.03), (w + 0.01, y_back + 0.012, h - L.CROWN), wood_all)
    if double:
        b.box((-w + p, -p / 2, L.KICK), (w - p, p / 2, h - L.CROWN), {"front": "wood", "back": "wood"})
    else:
        b.box((-w + p, y_back - p, L.KICK), (w - p, y_back, h - L.CROWN), {"front": "wood", "back": "wood"})
    pitch = (h - L.CROWN - L.KICK) / L.SHELVES
    faces = [(y_front, -p / 2 if double else y_back - p, 1)]
    if double:
        faces.append((y_back, p / 2, -1))
    for i in range(L.SHELVES):
        z = L.KICK + i * pitch
        b.box((-w + p, y_front, z), (w - p, y_back, z + p), {"front": "wood", "back": "wood", "top": "wood", "bottom": "wood"})
        for front, back, facing in faces:
            fill_shelf(b, -w + p, w - p, z + p, pitch - p - 0.012, front, back, facing, rng)
            if i in (1, 4):                       # a shelf mark on a few shelves
                lab = L.LABELS[(i + (facing < 0) * 2) % 4]
                ly = front - facing * 0.004
                b.box((-0.06, min(ly, front), z - 0.002), (0.06, max(ly, front), z + p + 0.012),
                      {("front" if facing > 0 else "back"): lab})
    return b.finish(name)


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
"int_shelves": {{
"use_external/enabled": true,
"use_external/fallback_path": "{res}int_shelves.tres",
"use_external/path": "{res}int_shelves.tres"
}}
}}
}}
gltf/naming_version=2
gltf/embedded_image_handling=1
"""


def export(obj):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(OUT / (obj.name + ".glb")), export_format="GLB", use_selection=True,
                              use_active_scene=True, export_yup=True, export_materials="EXPORT",
                              export_cameras=False, export_lights=False, export_animations=False)
    target = OUT / (obj.name + ".glb.import")
    if not target.exists():
        target.write_text(GLB_IMPORT.format(res=RES, name=obj.name), encoding="utf8", newline="\n")
    print("exported", obj.name, len(obj.data.polygons), "faces")


def prop_scene(name, depth, note):
    w, h = L.UNIT_W + 0.04, L.HEIGHT
    (PROPS / (name + ".tscn")).write_text("""[gd_scene format=3]

[ext_resource type="PackedScene" path="{res}{name}.glb" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_body"]
size = Vector3({w:.3f}, {h:.3f}, {d:.3f})

[node name="{title}" type="Node3D"]
editor_description = "{note}"

[node name="Mesh" parent="." instance=ExtResource("1_mesh")]

[node name="Body" type="StaticBody3D" parent="."]

[node name="Shape" type="CollisionShape3D" parent="Body"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, {cy:.3f}, 0)
shape = SubResource("BoxShape3D_body")
""".format(res=RES, name=name, title="".join(p.title() for p in name.split("_")), note=note, w=w, h=h, d=depth + 0.05, cy=h / 2),
        encoding="utf8", newline="\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
export(build("bookcase_double", L.DEPTH_DOUBLE, True, 6201))
export(build("bookcase_wall", L.DEPTH_WALL, False, 6202))
prop_scene("bookcase_double", L.DEPTH_DOUBLE, "Double-sided archive bookcase, 1.2 m wide and 2.7 m tall, books on both faces. Line several up to wall off Twin Archives' two alcoves: nobody sees over or through it.")
prop_scene("bookcase_wall", L.DEPTH_WALL, "Archive bookcase for standing against a wall, 1.2 m wide and 2.7 m tall, books on the front only.")
print("shelves built")
