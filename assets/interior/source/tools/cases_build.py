"""Builds the glass display cases (asset item P1.2) in a background Blender:
  blender -b --factory-startup --python cases_build.py -- <assets/interior/cases folder> <scenes/props folder>
Writes each case as three meshes, so it can be broken into (stretch goal: scoring): the case itself
(case_tall.glb, case_low.glb), its glass panes (*_glass.glb) and the prize inside (*_prize.glb), with their
import settings (which hand each part its material), and the prop scenes, where scripts/display_case.gd
breaks the glass and the prize is a Loot to pocket. Run make_cases_art.py for the texture and materials.

The glass blocks players and the guard's feet, but it's in the "see_through" group so her eyes can
pass through it. Blender is z up and the game is y up: a prop's front, the game's +z, is Blender's -y."""
import math
import pathlib
import sys

import bmesh
import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import cases_layout as L  # noqa: E402
import int_dims as D  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/cases/"
N = L.ATLAS
WOOD, BRASS, GLASS = 0, 1, 2      # material slots
MATERIALS = ("int_cases", "int_brass", "int_glass")


def uv(px, py):
    return (px / N, 1 - py / N)


def region_uv(name, fu, fv):
    x, y, w, h = L.REGIONS[name]
    return uv(x + 2 + fu * (w - 4), y + 2 + fv * (h - 4))


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")

    def quad(self, corners, texture, slot, uvs=((0, 1), (1, 1), (1, 0), (0, 0))):
        face = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        face.material_index = slot
        for loop, (fu, fv) in zip(face.loops, uvs):
            loop[self.layer].uv = region_uv(texture, fu, fv)
        return face

    def box(self, lo, hi, texture, slot, skip=()):
        """A box, each side showing the whole region, read the right way up from outside."""
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
            if side not in skip:
                self.quad(corners, texture, slot)

    def lathe(self, profile, centre, texture, slot, segments=20):
        """A pot turned from a profile of (radius, height) points, foot first. The texture's rows run
        from the lip at the top of the region down to the foot, round the whole circumference."""
        lengths = [0.0]
        for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
            lengths.append(lengths[-1] + math.hypot(r1 - r0, z1 - z0))
        total = lengths[-1]
        cx, cy, cz = centre
        rings = []
        for (r, z), _ in zip(profile, lengths):
            rings.append([self.bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), cz + z))
                          for a in (i / segments * math.tau for i in range(segments))])
        for k in range(len(profile) - 1):
            v0, v1 = 1 - lengths[k] / total, 1 - lengths[k + 1] / total
            for i in range(segments):
                j = (i + 1) % segments
                face = self.bm.faces.new([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]])
                face.material_index = slot
                face.smooth = True
                for loop, (fu, fv) in zip(face.loops, [(i / segments, v0), ((i + 1) / segments, v0), ((i + 1) / segments, v1), (i / segments, v1)]):
                    loop[self.layer].uv = region_uv(texture, fu, fv)
        # A dark disc just inside the mouth, so nobody sees through the pot
        r, z = profile[-1]
        mouth = [self.bm.verts.new((cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a), cz + z - 0.02)) for a in (i / segments * math.tau for i in range(segments))]
        face = self.bm.faces.new(mouth)
        face.material_index = slot
        for loop in face.loops:
            loop[self.layer].uv = region_uv("mouth", 0.5, 0.5)

    def handle(self, start, end, bulge, texture, slot, thick=0.012, steps=6):
        """A strap handle: a bent bar from start to end, bowed outwards by bulge."""
        pts = []
        for i in range(steps + 1):
            t = i / steps
            p = Vector(start).lerp(Vector(end), t) + Vector(bulge) * math.sin(t * math.pi)
            pts.append(p)
        for a, b in zip(pts, pts[1:]):
            d = (b - a).normalized()
            side = d.cross(Vector((0, 0, 1))).normalized() * thick if abs(d.z) < 0.95 else Vector((thick, 0, 0))
            up = d.cross(side).normalized() * thick
            ring_a = [a + side + up, a - side + up, a - side - up, a + side - up]
            ring_b = [b + side + up, b - side + up, b - side - up, b + side - up]
            for k in range(4):
                self.quad([ring_a[k], ring_a[(k + 1) % 4], ring_b[(k + 1) % 4], ring_b[k]], texture, slot,
                          uvs=((0.5, 0.12), (0.52, 0.12), (0.52, 0.14), (0.5, 0.14)))

    def coin(self, centre, radius, face_texture, segments=12, thick=0.004):
        cx, cy, cz = centre
        top = [self.bm.verts.new((cx + radius * math.cos(a), cy + radius * math.sin(a), cz + thick)) for a in (i / segments * math.tau for i in range(segments))]
        bot = [self.bm.verts.new((cx + radius * math.cos(a), cy + radius * math.sin(a), cz)) for a in (i / segments * math.tau for i in range(segments))]
        face = self.bm.faces.new(top)
        face.material_index = BRASS
        for loop, i in zip(face.loops, range(segments)):
            a = i / segments * math.tau
            loop[self.layer].uv = region_uv(face_texture, 0.5 + 0.5 * math.cos(a), 0.5 - 0.5 * math.sin(a))
        for i in range(segments):
            j = (i + 1) % segments
            self.quad([bot[i].co.copy(), bot[j].co.copy(), top[j].co.copy(), top[i].co.copy()], "brass", BRASS)

    def finish(self, name):
        mesh = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in MATERIALS:
            mesh.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
        mesh.validate()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def frame(b, x0, y0, x1, y1, z0, z1):
    """Brass strips up the four corners of the glass and round its top and bottom edges."""
    f = L.FRAME
    for x in (x0, x1):
        for y in (y0, y1):
            b.box((x - f / 2, y - f / 2, z0), (x + f / 2, y + f / 2, z1), "brass", BRASS)
    for z in (z0, z1 - f):
        b.box((x0 - f / 2, y0 - f / 2, z), (x1 + f / 2, y0 + f / 2, z + f), "brass", BRASS)
        b.box((x0 - f / 2, y1 - f / 2, z), (x1 + f / 2, y1 + f / 2, z + f), "brass", BRASS)
        b.box((x0 - f / 2, y0 + f / 2, z), (x0 + f / 2, y1 - f / 2, z + f), "brass", BRASS)
        b.box((x1 - f / 2, y0 + f / 2, z), (x1 + f / 2, y1 - f / 2, z + f), "brass", BRASS)


def glass_box(b, lo, hi, top=True):
    """Only the outside faces: the panes are seen from outside the case."""
    b.box(lo, hi, "glass", GLASS, skip=("bottom",) if top else ("bottom", "top"))


def card(b, centre, texture, width=0.17, height=0.085, tilt=35):
    cx, cy, cz = centre
    t = math.radians(tilt)
    dy, dz = math.sin(t) * height, math.cos(t) * height
    b.quad([(cx - width / 2, cy, cz), (cx + width / 2, cy, cz), (cx + width / 2, cy + dy, cz + dz), (cx - width / 2, cy + dy, cz + dz)], texture, WOOD)


AMPHORA = [(0.0, 0.0), (0.055, 0.0), (0.06, 0.02), (0.045, 0.045), (0.09, 0.09), (0.15, 0.19), (0.17, 0.28),
           (0.16, 0.36), (0.12, 0.43), (0.065, 0.47), (0.05, 0.52), (0.055, 0.56), (0.075, 0.585), (0.07, 0.6)]
BOWL = [(0.0, 0.0), (0.045, 0.0), (0.05, 0.015), (0.04, 0.022), (0.1, 0.05), (0.135, 0.09), (0.14, 0.105), (0.132, 0.11)]


def build_tall():
    """The case, its glass, and the prize: the amphora and the bowl on the shelf."""
    b, glass, prize = Builder(), Builder(), Builder()
    w = L.TALL_W / 2
    g = w - 0.02
    b.box((-w, -w, L.KICK_H), (w, w, L.TALL_BASE_H), "wood", WOOD)
    b.box((-w + 0.03, -w + 0.03, 0), (w - 0.03, w - 0.03, L.KICK_H), "wood", WOOD)
    b.box((-0.13, -w - 0.008, L.TALL_BASE_H - 0.2), (0.13, -w, L.TALL_BASE_H - 0.15), "plate", BRASS, skip=("back",))
    glass_box(glass, (-g, -g, L.TALL_BASE_H), (g, g, L.TALL_GLASS_TOP), top=False)
    frame(b, -g, -g, g, g, L.TALL_BASE_H, L.TALL_GLASS_TOP)
    b.box((-w - 0.01, -w - 0.01, L.TALL_GLASS_TOP), (w + 0.01, w + 0.01, D.CASE_TALL_H), "wood", WOOD)
    b.box((-g + 0.03, -g + 0.03, L.TALL_SHELF_Z), (g - 0.03, g - 0.03, L.TALL_SHELF_Z + 0.01), "glass", GLASS)
    prize.lathe(AMPHORA, (0.0, 0.06, L.TALL_BASE_H), "pottery", WOOD)
    z = L.TALL_BASE_H
    prize.handle((0.12, 0.06, z + 0.43), (0.055, 0.06, z + 0.53), (0.07, 0, 0.0), "pottery", WOOD)
    prize.handle((-0.12, 0.06, z + 0.43), (-0.055, 0.06, z + 0.53), (-0.07, 0, 0.0), "pottery", WOOD)
    prize.lathe(BOWL, (0.06, 0.02, L.TALL_SHELF_Z + 0.01), "pottery", WOOD)
    card(b, (0.24, -g + 0.08, L.TALL_BASE_H + 0.003), "card_tall", width=0.15, height=0.075)
    return b.finish("case_tall"), glass.finish("case_tall_glass"), prize.finish("case_tall_prize")


def build_low():
    """The case, its glass, and the prize: the coins and the scroll on the velvet."""
    b, glass, prize = Builder(), Builder(), Builder()
    w, d = L.LOW_W / 2, L.LOW_D / 2
    gw, gd = w - 0.02, d - 0.02
    top = D.CASE_LOW_H
    b.box((-w, -d, L.KICK_H), (w, d, L.LOW_BASE_H), "wood", WOOD)
    b.box((-w + 0.03, -d + 0.03, 0), (w - 0.03, d - 0.03, L.KICK_H), "wood", WOOD)
    b.box((-gw + 0.01, -gd + 0.01, L.LOW_BASE_H), (gw - 0.01, gd - 0.01, L.LOW_BASE_H + 0.01), "velvet", WOOD, skip=("bottom",))
    glass_box(glass, (-gw, -gd, L.LOW_BASE_H), (gw, gd, top))
    frame(b, -gw, -gd, gw, gd, L.LOW_BASE_H, top)
    bed = L.LOW_BASE_H + 0.01
    for row in range(3):          # three rows of coins on the velvet, gold and silver in turn
        for col in range(5):
            x = -0.52 + col * 0.085 + (row % 2) * 0.03
            y = -0.13 + row * 0.11
            radius = 0.022 if (row + col) % 3 else 0.028
            prize.coin((x, y, bed), radius, "coin_gold" if (row + col) % 2 else "coin_silver")
    # The scroll: a roll at the back, its free end lying open towards the front
    rx0, rx1, ry, rr = 0.12, 0.5, 0.15, 0.03
    seg = 10
    ring = lambda x: [(x, ry + rr * math.cos(a), bed + rr + rr * math.sin(a)) for a in (i / seg * math.tau for i in range(seg))]
    left, right = ring(rx0), ring(rx1)
    for i in range(seg):
        j = (i + 1) % seg
        prize.quad([left[i], left[j], right[j], right[i]], "parchment", WOOD, uvs=((0, 0), (0, 0.1), (1, 0.1), (1, 0)))
    for k in range(6):            # the open sheet, sagging gently onto the velvet
        y0, y1 = ry - 0.02 - k * 0.04, ry - 0.02 - (k + 1) * 0.04
        z0 = bed + 0.004 + 0.03 * (1 - k / 6) ** 2
        z1 = bed + 0.004 + 0.03 * (1 - (k + 1) / 6) ** 2
        prize.quad([(rx0, y1, z1), (rx1, y1, z1), (rx1, y0, z0), (rx0, y0, z0)], "parchment", WOOD,
               uvs=((0, (k + 1) / 6), (1, (k + 1) / 6), (1, k / 6), (0, k / 6)))
    card(b, (0.0, -gd + 0.06, bed), "card_low", width=0.17, height=0.085, tilt=60)
    return b.finish("case_low"), glass.finish("case_low_glass"), prize.finish("case_low_prize")


GLB_IMPORT_HEAD = """[remap]

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
{materials}
}}
}}
gltf/naming_version=2
gltf/embedded_image_handling=1
"""
MAT_ENTRY = """"{mat}": {{
"use_external/enabled": true,
"use_external/fallback_path": "{res}{mat}.tres",
"use_external/path": "{res}{mat}.tres"
}}"""


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
        mats = ",\n".join(MAT_ENTRY.format(mat=m, res=RES) for m in MATERIALS)
        target.write_text(GLB_IMPORT_HEAD.format(res=RES, name=obj.name, materials=mats), encoding="utf8", newline="\n")
    print("exported", obj.name, len(obj.data.polygons), "faces")


CASE_SCENE = """[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/display_case.gd" id="1_case"]
[ext_resource type="PackedScene" path="{res}{name}.glb" id="2_mesh"]
[ext_resource type="PackedScene" path="{res}{name}_glass.glb" id="3_glass"]
[ext_resource type="PackedScene" path="{res}{name}_prize.glb" id="4_prize"]
[ext_resource type="Script" path="res://scripts/loot.gd" id="5_loot"]

[sub_resource type="BoxShape3D" id="BoxShape3D_base"]
size = Vector3({bs[0]:.3f}, {bs[1]:.3f}, {bs[2]:.3f})

[sub_resource type="BoxShape3D" id="BoxShape3D_glass"]
size = Vector3({gs[0]:.3f}, {gs[1]:.3f}, {gs[2]:.3f})

[sub_resource type="BoxShape3D" id="BoxShape3D_prize"]
size = Vector3({ps[0]:.3f}, {ps[1]:.3f}, {ps[2]:.3f})

[sub_resource type="SceneReplicationConfig" id="Sync_case"]
properties/0/path = NodePath(".:broken")
properties/0/spawn = true
properties/0/replication_mode = 2

[sub_resource type="SceneReplicationConfig" id="Sync_prize"]
properties/0/path = NodePath(".:taken")
properties/0/spawn = true
properties/0/replication_mode = 2

[node name="{title_node}" type="Node3D"]
editor_description = "{note}"
script = ExtResource("1_case")

[node name="Mesh" parent="." instance=ExtResource("2_mesh")]

[node name="GlassMesh" parent="." instance=ExtResource("3_glass")]

[node name="Body" type="StaticBody3D" parent="."]

[node name="Shape" type="CollisionShape3D" parent="Body"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {bc[0]:.3f}, {bc[1]:.3f}, {bc[2]:.3f})
shape = SubResource("BoxShape3D_base")

[node name="Glass" type="StaticBody3D" parent="." groups=["see_through"]]

[node name="Shape" type="CollisionShape3D" parent="Glass"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {gc[0]:.3f}, {gc[1]:.3f}, {gc[2]:.3f})
shape = SubResource("BoxShape3D_glass")

[node name="Prize" type="StaticBody3D" parent="."]
script = ExtResource("5_loot")
display_name = "{title}"
value = {dollars}
note = "{prize_note}"

[node name="Model" parent="Prize" instance=ExtResource("4_prize")]

[node name="Shape" type="CollisionShape3D" parent="Prize"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {pc[0]:.3f}, {pc[1]:.3f}, {pc[2]:.3f})
shape = SubResource("BoxShape3D_prize")

[node name="MultiplayerSynchronizer" type="MultiplayerSynchronizer" parent="Prize"]
replication_config = SubResource("Sync_prize")

[node name="MultiplayerSynchronizer" type="MultiplayerSynchronizer" parent="."]
replication_config = SubResource("Sync_case")
"""


def prop_scene(name, base, glass, prize, note):
    """base and glass are (size, centre) boxes in the game's axes (x, up, z); prize is
    (title, dollars, note, (size, centre)) for the Loot inside, which shows once the glass is broken."""
    (bs, bc), (gs, gc) = base, glass
    title, dollars, prize_note, (ps, pc) = prize
    (PROPS / (name + ".tscn")).write_text(CASE_SCENE.format(
        res=RES, name=name, title_node="".join(p.title() for p in name.split("_")), note=note, bs=bs, bc=bc, gs=gs, gc=gc,
        title=title, dollars=dollars, prize_note=prize_note, ps=ps, pc=pc), encoding="utf8", newline="\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
for part in build_tall() + build_low():
    export(part)
tw = L.TALL_W
prop_scene("case_tall", ((tw, L.TALL_BASE_H, tw), (0, L.TALL_BASE_H / 2, 0)),
           ((tw, D.CASE_TALL_H - L.TALL_BASE_H, tw), (0, (D.CASE_TALL_H + L.TALL_BASE_H) / 2, 0)),
           ("Amphora with a wooden horse", 2500, "A gift from the Greeks. Check inside.", ((0.36, 0.62, 0.36), (0, L.TALL_BASE_H + 0.31, -0.06))),
           "Tall glass case, 2.1 m: an amphora with a familiar wooden horse on it. Not cover: the guard sees through the glass (group see_through), and the cabinet is only 0.8 m. A crowbar breaks the glass (loud); then the amphora is loot.")
prop_scene("case_low", ((L.LOW_W, L.LOW_BASE_H, L.LOW_D), (0, L.LOW_BASE_H / 2, 0)),
           ((L.LOW_W, D.CASE_LOW_H - L.LOW_BASE_H, L.LOW_D), (0, (D.CASE_LOW_H + L.LOW_BASE_H) / 2, 0)),
           ("Coins of Troy", 1500, "And one overdue scroll.", ((1.2, 0.08, 0.5), (0, L.LOW_BASE_H + 0.04, 0))),
           "Low glass case, 1.05 m: coins of Troy and an overdue scroll on velvet. Not cover. The glass is in group see_through. A crowbar breaks the glass (loud); then the coins are loot.")
print("cases built")
