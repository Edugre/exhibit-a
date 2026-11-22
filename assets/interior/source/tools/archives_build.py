"""Builds the Twin Archives set (asset item P3.2) in a background Blender:
  blender -b --factory-startup --python archives_build.py -- <assets/interior/archives folder> <scenes/props folder>
Writes card_catalogue, scroll_rack, reading_table (with its books and sign), library_chair,
rolling_ladder and reading_lamp: each a .glb, its import settings and a prop scene. Run
make_archives_art.py for the texture and materials.

Every prop stands on its origin on the floor (the lamp on whatever it sits on) and faces +z. Shapes are
written in the game's axes (y up) and turned into Blender's (z up) when a vertex is made."""
import math
import pathlib
import random
import sys

import bmesh
import bpy

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import archives_layout as L  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/archives/"
N = L.ATLAS
BODY, GLASS, GLOW = 0, 1, 2
MATERIALS = ("int_archives", "int_archives_glass", "int_archives_glow")
WINDOWED = ("oak", "oak_dark", "leather")   # textures a face takes a piece of, sized to it, instead of stretching

X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)


def bl(p):
    x, y, z = p
    return (x, -z, y)


def region_uv(name, fu, fv):
    x, y, w, h = L.REGIONS[name]
    fu, fv = min(max(fu, 0.0), 1.0), min(max(fv, 0.0), 1.0)
    return ((x + 1 + fu * (w - 2)) / N, 1 - (y + 1 + fv * (h - 2)) / N)


def newell(pts):
    n = [0.0, 0.0, 0.0]
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    return n


def add(*vs):
    return tuple(sum(v[i] for v in vs) for i in range(3))


def mul(v, k):
    return (v[0] * k, v[1] * k, v[2] * k)


def yaw(deg):
    """The x and z axes of something turned `deg` degrees about y."""
    a = math.radians(deg)
    return (math.cos(a), 0.0, -math.sin(a)), (math.sin(a), 0.0, math.cos(a))


class Builder:
    def __init__(self, seed):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")
        self.rng = random.Random(seed)

    def face(self, pts, uvs, texture, normal, slot=BODY):
        n = newell(pts)
        if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
            pts, uvs = pts[::-1], uvs[::-1]
        f = self.bm.faces.new([self.bm.verts.new(bl(p)) for p in pts])
        f.material_index = slot
        for loop, (fu, fv) in zip(f.loops, uvs):
            loop[self.layer].uv = region_uv(texture, fu, fv)

    def obox(self, centre, axes, half, textures, slot=BODY):
        """A box with its own axes (ax, ay, az) and half sizes. textures maps sides (+x -x +y -y +z -z,
        in the box's axes) to regions; sides left out aren't made. Wood takes a piece of its texture the
        size of the face, at a different spot each time, so boards don't repeat or stretch."""
        ax, ay, az = axes
        hx, hy, hz = half

        def c(sx, sy, sz):
            return add(centre, mul(ax, sx * hx), mul(ay, sy * hy), mul(az, sz * hz))
        sides = {
            "+z": ([c(-1, -1, 1), c(1, -1, 1), c(1, 1, 1), c(-1, 1, 1)], (2 * hx, 2 * hy), az),
            "-z": ([c(1, -1, -1), c(-1, -1, -1), c(-1, 1, -1), c(1, 1, -1)], (2 * hx, 2 * hy), mul(az, -1)),
            "+x": ([c(1, -1, 1), c(1, -1, -1), c(1, 1, -1), c(1, 1, 1)], (2 * hz, 2 * hy), ax),
            "-x": ([c(-1, -1, -1), c(-1, -1, 1), c(-1, 1, 1), c(-1, 1, -1)], (2 * hz, 2 * hy), mul(ax, -1)),
            "+y": ([c(-1, 1, 1), c(1, 1, 1), c(1, 1, -1), c(-1, 1, -1)], (2 * hx, 2 * hz), ay),
            "-y": ([c(-1, -1, -1), c(1, -1, -1), c(1, -1, 1), c(-1, -1, 1)], (2 * hx, 2 * hz), mul(ay, -1)),
        }
        for side, texture in textures.items():
            pts, (w, h), normal = sides[side]
            u0, v0, us, vs = 0.0, 0.0, 1.0, 1.0
            if texture in WINDOWED:
                us, vs = min(1.0, w / L.WOOD_TILE), min(1.0, h / L.WOOD_TILE)
                u0, v0 = self.rng.uniform(0, 1 - us), self.rng.uniform(0, 1 - vs)
            uvs = [(u0, v0 + vs), (u0 + us, v0 + vs), (u0 + us, v0), (u0, v0)]
            self.face(pts, uvs, texture, normal, slot)

    def box(self, lo, hi, textures, slot=BODY, turn=0.0):
        """An upright box from corner lo to corner hi, optionally turned about its own centre."""
        centre = mul(add(lo, hi), 0.5)
        half = tuple(abs(hi[i] - lo[i]) / 2 for i in range(3))
        ax, az = yaw(turn)
        self.obox(centre, (ax, Y, az), half, textures, slot)

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


ALL = ("+x", "-x", "+y", "-y", "+z", "-z")


def sides(tex, front=None, top=None, skip=()):
    t = {s: tex for s in ALL if s not in skip}
    if front:
        t["+z"] = front
    if top:
        t["+y"] = top
    return t


def build_catalogue():
    """A card catalogue: forty-eight drawers on a dark plinth, under an overhanging top."""
    b = Builder(3501)
    w, d, h = L.CATALOGUE
    b.box((-w / 2 + 0.02, 0.0, -d / 2), (w / 2 - 0.02, 0.08, d / 2 - 0.03), sides("oak_dark", skip=("-y", "+y")))
    b.box((-w / 2, 0.08, -d / 2), (w / 2, h - 0.04, d / 2), sides("oak", front="drawers", skip=("-y",)))
    b.box((-w / 2 - 0.02, h - 0.04, -d / 2 - 0.02), (w / 2 + 0.02, h, d / 2 + 0.02), sides("oak", skip=("-y",)))
    b.box((-w / 2 - 0.02, h - 0.04 - 0.012, d / 2), (w / 2 + 0.02, h - 0.04, d / 2 + 0.02), {"-y": "oak_dark", "+z": "oak_dark"})
    return b.finish("card_catalogue")


def build_rack():
    """A scroll rack: pigeonholes built as a real grid, so they read from the side, with the scrolls
    showing end on at the back of each hole."""
    b = Builder(3502)
    w, d, h = L.RACK
    cols, rows = L.RACK_CELLS
    base, crown, frame, depth = 0.12, 0.12, 0.03, 0.14
    b.box((-w / 2, 0.0, -d / 2), (w / 2, base, d / 2), sides("oak_dark", skip=("-y",)))
    b.box((-w / 2 - 0.02, h - crown, -d / 2 - 0.02), (w / 2 + 0.02, h, d / 2 + 0.02), sides("oak_dark", skip=()))
    b.box((-w / 2, base, -d / 2), (w / 2, h - crown, d / 2 - depth), sides("oak_dark", front="cubbies", skip=("+y", "-y")))
    y0, y1 = base, h - crown
    for k in range(cols + 1):                                    # the uprights between the holes, and the two sides
        x = -w / 2 + k * w / cols
        x0, x1 = x - frame / 2, x + frame / 2
        if k == 0:
            x0, x1 = -w / 2, -w / 2 + frame
        elif k == cols:
            x0, x1 = w / 2 - frame, w / 2
        b.box((x0, y0, d / 2 - depth), (x1, y1, d / 2), sides("oak_dark", skip=("+y", "-y")))
    for r in range(1, rows):                                     # and the shelves
        y = y0 + r * (y1 - y0) / rows
        b.box((-w / 2, y - frame / 2, d / 2 - depth), (w / 2, y + frame / 2, d / 2), sides("oak_dark", skip=("+x", "-x")))
    return b.finish("scroll_rack")


def book(b, centre, size, turn, cover="leather", top=None):
    x, y, z = centre
    w, d, t = size
    b.box((x - w / 2, y, z - d / 2), (x + w / 2, y + t, z + d / 2), sides(cover, top=top, skip=("-y",)), turn=turn)


def build_table():
    """The reading table, long and plain, with two open books, a small stack and a brass sign asking for
    quiet. The lamps are separate, so they can sit anywhere."""
    b = Builder(3503)
    w, d, h = L.TABLE
    top = 0.05
    b.box((-w / 2, h - top, -d / 2), (w / 2, h, d / 2), sides("oak"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (w / 2 - 0.1), sz * (d / 2 - 0.09)
            b.box((x - 0.035, 0.0, z - 0.035), (x + 0.035, h - top, z + 0.035), sides("oak_dark", skip=("+y", "-y")))
    for sz in (-1, 1):
        z = sz * (d / 2 - 0.09)
        b.box((-w / 2 + 0.1, h - top - 0.11, z - 0.015), (w / 2 - 0.1, h - top, z + 0.015), sides("oak_dark", skip=("+y",)))
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.1)
        b.box((x - 0.015, h - top - 0.11, -d / 2 + 0.1), (x + 0.015, h - top, d / 2 - 0.1), sides("oak_dark", skip=("+y",)))
    # two open books, a little crooked, their covers showing round the pages
    for (x, z, turn, pages) in ((-0.5, 0.08, 7.0, "pages"), (0.32, -0.12, -12.0, "pages_2")):
        book(b, (x, h, z), (0.5, 0.34, 0.012), turn)
        book(b, (x, h + 0.012, z), (0.47, 0.31, 0.02), turn, cover="pages", top=pages)
    y = h                                                        # and a small stack, none of it square
    for dx, dz, turn, size in ((0.0, 0.0, 4, (0.26, 0.19, 0.05)), (0.01, -0.01, -9, (0.24, 0.18, 0.04)), (-0.01, 0.01, 15, (0.22, 0.16, 0.045))):
        book(b, (0.78 + dx, y, 0.22 + dz), size, turn)
        y += size[2]
    b.box((-0.08, h, -0.33), (0.08, h + 0.07, -0.28), {"+z": "sign", "-z": "oak_dark", "+x": "oak_dark", "-x": "oak_dark", "+y": "oak_dark"}, turn=180.0)
    return b.finish("reading_table")


def build_chair():
    """A library chair: oak frame and a buttoned green leather back."""
    b = Builder(3504)
    s = L.CHAIR_SEAT
    hw = 0.23
    b.box((-hw, s - 0.05, -hw), (hw, s, hw), sides("oak"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (hw - 0.03), sz * (hw - 0.03)
            top = s + 0.5 if sz < 0 else s - 0.05
            b.box((x - 0.022, 0.0, z - 0.022), (x + 0.022, top, z + 0.022), sides("oak_dark", skip=("-y",)))
    b.box((-hw + 0.03, s + 0.12, -hw - 0.005), (hw - 0.03, s + 0.44, -hw + 0.035), {"+z": "chair_back", "-z": "oak_dark", "+y": "oak_dark"})
    b.box((-hw, s + 0.44, -hw - 0.01), (hw, s + 0.5, -hw + 0.04), sides("oak_dark"))
    return b.finish("library_chair")


def build_ladder():
    """A rolling library ladder, leaning back against a bookcase: two rails, rungs, brass hooks at the
    top that would hang it on a rail, and little wheels at the feet."""
    b = Builder(3505)
    w, length, lean = L.LADDER
    a = math.radians(lean)
    up = (0.0, math.cos(a), -math.sin(a))
    out = (0.0, math.sin(a), math.cos(a))                      # the ladder's own "front"
    for sx in (-1, 1):
        foot = (sx * (w / 2 - 0.025), 0.03, 0.0)
        b.obox(add(foot, mul(up, length / 2)), (X, up, out), (0.025, length / 2, 0.035), sides("oak_dark"))
        b.obox(add(foot, (0, -0.005, 0)), (X, Y, Z), (0.03, 0.03, 0.045), sides("brass"))
        top = add(foot, mul(up, length))
        b.obox(add(top, (0, -0.02, -0.05)), (X, Y, Z), (0.012, 0.035, 0.07), sides("brass"))
    rungs = int((length - 0.35) / 0.28)
    for k in range(rungs):
        centre = add((0.0, 0.03, 0.0), mul(up, 0.3 + k * 0.28))
        b.obox(centre, (X, up, out), (w / 2 - 0.05, 0.02, 0.06), sides("oak", skip=("+x", "-x")))
    return b.finish("rolling_ladder")


def build_lamp():
    """A banker's lamp: a brass base and stem under a long green glass shade, lit underneath."""
    b = Builder(3506)
    sl, h = L.LAMP
    b.box((-0.12, 0.0, -0.07), (0.12, 0.025, 0.07), sides("brass", skip=("-y",)))
    b.box((-0.012, 0.025, -0.045), (0.012, h - 0.06, -0.021), sides("brass", skip=("-y", "+y")))
    b.box((-0.06, h - 0.07, -0.04), (0.06, h - 0.055, -0.02), sides("brass"))
    y0, y1 = h - 0.08, h
    zb0, zb1, zt0, zt1 = -0.08, 0.075, -0.035, 0.03          # wide at the bottom, narrow on top
    hw = sl / 2
    b.face([(-hw, y0, zb1), (hw, y0, zb1), (hw, y1, zt1), (-hw, y1, zt1)], [(0, 1), (1, 1), (1, 0), (0, 0)], "glass", (0, 0.5, 1), GLASS)
    b.face([(hw, y0, zb0), (-hw, y0, zb0), (-hw, y1, zt0), (hw, y1, zt0)], [(0, 1), (1, 1), (1, 0), (0, 0)], "glass", (0, 0.5, -1), GLASS)
    b.face([(-hw, y1, zt1), (hw, y1, zt1), (hw, y1, zt0), (-hw, y1, zt0)], [(0, 0.4), (1, 0.4), (1, 0.3), (0, 0.3)], "glass", (0, 1, 0), GLASS)
    for sx in (-1, 1):
        b.face([(sx * hw, y0, zb0), (sx * hw, y0, zb1), (sx * hw, y1, zt1), (sx * hw, y1, zt0)], [(0, 1), (1, 1), (0.7, 0), (0.3, 0)], "glass", (sx, 0, 0), GLASS)
    b.face([(-hw + 0.01, y0 + 0.002, zb0 + 0.01), (hw - 0.01, y0 + 0.002, zb0 + 0.01), (hw - 0.01, y0 + 0.002, zb1 - 0.01), (-hw + 0.01, y0 + 0.002, zb1 - 0.01)],
           [(0, 1), (1, 1), (1, 0), (0, 0)], "glow", (0, -1, 0), GLOW)
    return b.finish("reading_lamp")


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
    """box is (size, centre) in the game's axes, or None. light is (position, energy) for a warm glow."""
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
        parts.append('\n[node name="Glow" type="OmniLight3D" parent="."]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %.3f, %.3f, %.3f)\n'
                     'light_color = Color(1, 0.85, 0.62, 1)\nlight_energy = %.2f\nomni_range = 1.8\nomni_attenuation = 1.5\n' % (lx, ly, lz, energy))
    (PROPS / (name + ".tscn")).write_text("".join(parts), encoding="utf8", newline="\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
w, d, h = L.CATALOGUE
export(build_catalogue())
prop_scene("card_catalogue", ((w, h, d), (0, h / 2, 0)), "A card catalogue: 48 drawers, typed labels, brass pulls. %.1f m tall: furniture, not cover." % h)
w, d, h = L.RACK
export(build_rack())
prop_scene("scroll_rack", ((w, h, d), (0, h / 2, 0)), "A scroll rack: pigeonholes full of scrolls. 1.8 m tall, back against a wall.")
w, d, h = L.TABLE
export(build_table())
prop_scene("reading_table", ((w, h, d), (0, h / 2, 0)), "The reading table, with two open books (OVERDUE; Fines, Vol. VII), a stack, and a sign: SILENCE, she can hear you. Put reading_lamp scenes on it.")
export(build_chair())
prop_scene("library_chair", ((0.48, 1.0, 0.48), (0, 0.5, 0)), "A library chair with a buttoned green leather back, facing +z.")
w, length, lean = L.LADDER
export(build_ladder())
reach = length * math.sin(math.radians(lean))
prop_scene("rolling_ladder", ((w + 0.06, 1.6, 0.3), (0, 0.8, -0.15)),
           "A rolling library ladder leaning back %.0f degrees; its top hooks sit %.2f m behind its feet, so stand its feet that far out from a bookcase." % (lean, reach))
export(build_lamp())
prop_scene("reading_lamp", None, "A green banker's lamp, lit. Origin under its base: set it on a table or cabinet top. Its small warm light has no shadows.",
           light=((0.0, L.LAMP[1] - 0.12, 0.05), 0.55))
print("archives built")
