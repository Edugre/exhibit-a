"""Builds the Security Office set (asset item P3.4) in a background Blender:
  blender -b --factory-startup --python office_build.py -- <assets/interior/office folder> <scenes/props folder>
Writes security_desk, monitor_wall, lockers, office_chair and key_board: each a .glb, its import settings
and a prop scene. Run make_office_art.py for the texture and materials.

Blender is z up and the game is y up: a prop's front, the game's +z, is Blender's -y."""
import math
import pathlib
import sys

import bmesh
import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import office_layout as L  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/office/"
N = L.ATLAS
BODY, SCREEN = 0, 1
MATERIALS = ("int_office", "int_screens")


def region_uv(name, fu, fv):
    x, y, w, h = L.REGIONS[name]
    return ((x + 1 + fu * (w - 2)) / N, 1 - (y + 1 + fv * (h - 2)) / N)


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")

    def quad(self, corners, texture, slot=BODY):
        face = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        face.material_index = slot
        for loop, (fu, fv) in zip(face.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[self.layer].uv = region_uv(texture, fu, fv)

    def box(self, lo, hi, texture, faces=None, slot=BODY):
        """A box; `faces` overrides the region on chosen sides, e.g. {"front": "door_0"}."""
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
            tex = (faces or {}).get(side, texture)
            if tex:
                self.quad(corners, tex, slot)

    def screen(self, x0, x1, z0, z1, y, texture):
        """A glowing picture just in front of a face at depth y."""
        self.quad([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], texture, SCREEN)

    def cylinder(self, centre, radius, height, texture, segments=12):
        cx, cy, cz = centre
        ring = lambda z: [(cx + radius * math.cos(a), cy + radius * math.sin(a), z) for a in (i / segments * math.tau for i in range(segments))]
        bot, top = ring(cz), ring(cz + height)
        for i in range(segments):
            j = (i + 1) % segments
            face = self.bm.faces.new([self.bm.verts.new(bot[i]), self.bm.verts.new(bot[j]), self.bm.verts.new(top[j]), self.bm.verts.new(top[i])])
            face.smooth = True
            for loop, (fu, fv) in zip(face.loops, ((i / segments, 1), ((i + 1) / segments, 1), ((i + 1) / segments, 0), (i / segments, 0))):
                loop[self.layer].uv = region_uv(texture, fu, fv)
        cap = self.bm.faces.new([self.bm.verts.new(c) for c in top])
        for loop in cap.loops:
            loop[self.layer].uv = region_uv("dark", 0.5, 0.5)

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


def monitor(b, cx, cy, base_z, w, h, d, feed):
    """A chunky old monitor: a box, a stand, and the picture on its front."""
    b.box((cx - 0.05, cy - 0.06, base_z), (cx + 0.05, cy + 0.06, base_z + 0.06), "dark")
    z0 = base_z + 0.06
    b.box((cx - w / 2, cy - d / 2, z0), (cx + w / 2, cy + d / 2, z0 + h), "dark")
    b.screen(cx - w / 2 + 0.025, cx + w / 2 - 0.025, z0 + 0.025, z0 + h - 0.025, cy - d / 2 - 0.002, feed)


def build_desk():
    b = Builder()
    w, d, h = L.DESK
    hw, hd = w / 2, d / 2
    b.box((-hw, -hd, h - 0.04), (hw, hd, h), "laminate")                    # top
    b.box((hw - 0.42, -hd + 0.03, 0), (hw - 0.03, hd - 0.03, h - 0.04), "steel")   # drawer pedestal
    b.box((-hw + 0.03, -hd + 0.05, 0), (-hw + 0.07, -hd + 0.09, h - 0.04), "dark")  # legs
    b.box((-hw + 0.03, hd - 0.09, 0), (-hw + 0.07, hd - 0.05, h - 0.04), "dark")
    b.box((-hw + 0.07, hd - 0.05, 0.25), (hw - 0.42, hd - 0.03, h - 0.04), "steel")  # modesty panel
    monitor(b, -0.38, 0.1, h, 0.44, 0.34, 0.36, "desk_feed")
    monitor(b, 0.22, 0.12, h, 0.44, 0.34, 0.36, "desk_log")
    b.box((-0.32, -0.32, h), (0.12, -0.16, h + 0.02), "dark", faces={"top": "keyboard"})
    b.cylinder((0.42, -0.2, h), 0.045, 0.1, "mug")
    b.box((-0.72, -0.3, h), (-0.5, -0.02, h + 0.035), "logbook")
    return b.finish("security_desk")


def build_monitor_wall():
    b = Builder()
    w, d, h = L.MONITOR_WALL
    hw = w / 2
    y_back = d / 2
    b.box((-hw, -d / 2, 0), (hw, y_back, 0.9), "steel")                      # console
    b.box((-hw, -d / 2 - 0.04, 0.88), (hw, y_back, 0.92), "laminate")        # its ledge
    b.box((-hw, y_back - 0.25, 0.92), (hw, y_back, h), "steel")              # the screen rack
    cols, rows = 3, 2
    cw, rh = (w - 0.2) / cols, (h - 1.02) / rows
    for r in range(rows):
        for c in range(cols):
            x0 = -hw + 0.1 + c * cw + 0.04
            z0 = 1.0 + (rows - 1 - r) * rh + 0.04
            b.box((x0, y_back - 0.33, z0), (x0 + cw - 0.08, y_back - 0.25, z0 + rh - 0.08), "dark")
            b.screen(x0 + 0.03, x0 + cw - 0.11, z0 + 0.03, z0 + rh - 0.11, y_back - 0.332, L.FEEDS[r * cols + c])
    b.box((-hw + 0.25, -d / 2 - 0.02, 0.92), (-hw + 0.75, -d / 2 + 0.16, 0.95), "dark", faces={"top": "keyboard"})
    return b.finish("monitor_wall")


def build_lockers():
    b = Builder()
    w, d, h = L.LOCKER
    for i in range(3):
        x0 = -1.5 * w + i * w
        b.box((x0 + 0.005, -d / 2, 0.0), (x0 + w - 0.005, d / 2, h), "steel", faces={"front": "door_%d" % i})
    b.box((-1.5 * w, -d / 2 - 0.01, h), (1.5 * w, d / 2, h + 0.03), "steel")
    return b.finish("lockers")


def build_chair():
    b = Builder()
    s = L.CHAIR_SEAT
    b.cylinder((0, 0, 0.06), 0.03, s - 0.1, "dark", segments=8)
    for k in range(5):                       # the star base
        a = k / 5 * math.tau
        x, y = math.cos(a) * 0.26, math.sin(a) * 0.26
        b.box((min(0, x) - 0.02, min(0, y) - 0.02, 0.02), (max(0, x) + 0.02, max(0, y) + 0.02, 0.06), "dark")
    b.box((-0.24, -0.24, s - 0.05), (0.24, 0.24, s + 0.03), "fabric")
    b.box((-0.22, 0.2, s + 0.03), (0.22, 0.26, s + 0.55), "fabric")
    # Her cardigan, hung over the back with the sleeves dangling
    b.box((-0.24, 0.18, s + 0.42), (0.24, 0.29, s + 0.6), "knit")
    b.box((-0.25, 0.27, s + 0.15), (0.23, 0.31, s + 0.6), "knit")
    b.box((-0.29, 0.18, s + 0.05), (-0.22, 0.25, s + 0.5), "knit")
    b.box((0.21, 0.19, s + 0.1), (0.28, 0.26, s + 0.52), "knit")
    return b.finish("office_chair")


def build_key_board():
    b = Builder()
    b.box((-0.32, -0.03, 1.3), (0.32, 0.0, 1.75), "laminate", faces={"front": "keyboard_board"})
    return b.finish("key_board")


GLB_IMPORT = (TOOLS / "cases_build.py").read_text(encoding="utf8").split('GLB_IMPORT_HEAD = """')[1].split('"""')[0]
MAT_ENTRY = (TOOLS / "cases_build.py").read_text(encoding="utf8").split('MAT_ENTRY = """')[1].split('"""')[0]


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
        target.write_text(GLB_IMPORT.format(res=RES, name=obj.name, materials=mats), encoding="utf8", newline="\n")
    print("exported", obj.name, len(obj.data.polygons), "faces")


def prop_scene(name, box, note, light=None):
    """box is (size, centre) in the game's axes, or None for no collision. light adds a glow for the screens."""
    parts = ['[gd_scene format=3]\n\n[ext_resource type="PackedScene" path="%s%s.glb" id="1_mesh"]\n' % (RES, name)]
    if box:
        (sx, sy, sz), _ = box
        parts.append('\n[sub_resource type="BoxShape3D" id="BoxShape3D_body"]\nsize = Vector3(%.3f, %.3f, %.3f)\n' % (sx, sy, sz))
    title = "".join(p.title() for p in name.split("_"))
    parts.append('\n[node name="%s" type="Node3D"]\neditor_description = "%s"\n\n[node name="Mesh" parent="." instance=ExtResource("1_mesh")]\n' % (title, note))
    if box:
        _, (cx, cy, cz) = box
        parts.append('\n[node name="Body" type="StaticBody3D" parent="."]\n\n[node name="Shape" type="CollisionShape3D" parent="Body"]\n'
                     'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %.3f, %.3f, %.3f)\nshape = SubResource("BoxShape3D_body")\n' % (cx, cy, cz))
    if light:
        (lx, ly, lz), energy = light
        parts.append('\n[node name="ScreenGlow" type="OmniLight3D" parent="."]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %.3f, %.3f, %.3f)\n'
                     'light_color = Color(0.6, 1, 0.75, 1)\nlight_energy = %.2f\nomni_range = 3.0\nomni_attenuation = 1.6\n' % (lx, ly, lz, energy))
    (PROPS / (name + ".tscn")).write_text("".join(parts), encoding="utf8", newline="\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
w, d, h = L.DESK
export(build_desk())
prop_scene("security_desk", ((w, h, d), (0, h / 2, 0)), "The night guard's desk: two old monitors (the vault feed, and the log: DAY 2,071, BOOK STILL OVERDUE), a keyboard, a mug and the night log. 0.76 m: not cover.",
           light=((0, 1.2, 0.5), 0.35))
w, d, h = L.MONITOR_WALL
export(build_monitor_wall())
prop_scene("monitor_wall", ((w, h, d), (0, h / 2, 0)), "Six CCTV screens over a console, for standing against a wall. 2.35 m tall. The feeds show the museum's rooms, the curb and one camera that's out.",
           light=((0, 1.6, 0.9), 0.6))
w, d, h = L.LOCKER
export(build_lockers())
prop_scene("lockers", ((3 * w, h + 0.03, d), (0, (h + 0.03) / 2, 0)), "A row of three steel lockers, 1.9 m: cover. The third is hers: L. KEEP OUT, with a SHH sticker.")
export(build_chair())
prop_scene("office_chair", ((0.5, 1.05, 0.55), (0, 0.52, 0.02)), "The guard's chair, with the librarian's cardigan over the back.")
export(build_key_board())
prop_scene("key_board", None, "Wall-mounted key board, origin on the floor below it, back against the wall. Two keys are missing.")
print("office built")
