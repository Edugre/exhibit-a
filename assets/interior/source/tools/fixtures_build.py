"""Builds the ceiling and wall fixtures (asset item P1.5) in a background Blender:
  blender -b --factory-startup --python fixtures_build.py -- <assets/interior/fixtures folder> <scenes/props folder>
Writes pendant_lamp, light_panel, exit_sign and wall_vent: each a .glb, its import settings and a prop
scene. Run make_fixtures_art.py for the texture and materials. None has collision: they're all out of reach.

Where each one's origin is:
  pendant_lamp  the bottom of its glass bowl. Hang it PENDANT_LIFT above a room light, so the light shines
                down freely and the lamp only leaves a soft patch of shadow on the ceiling. Its rod runs up
                0.7 m, into the ceiling slab.
  light_panel   the centre of its face, on the ceiling (y = int_dims.WALL_H), facing down.
  exit_sign     the centre of its back, on the wall, facing +z; the arrow points right as you face it (+x),
                so hang it to the left of the door as you look at it.
  wall_vent     the centre of its back, on the wall, facing +z, with its brass plate underneath.
Shapes are written in the game's axes (y up) and turned into Blender's (z up) when a vertex is made."""
import math
import pathlib
import sys

import bmesh
import bpy

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import fixtures_layout as L  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/fixtures/"
N = L.ATLAS
METAL, GLOW = 0, 1
MATERIALS = ("int_fixtures", "int_fixtures_glow")
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


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")

    def face(self, pts, uvs, texture, normal, slot=METAL):
        n = newell(pts)
        if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
            pts, uvs = pts[::-1], uvs[::-1]
        f = self.bm.faces.new([self.bm.verts.new(bl(p)) for p in pts])
        f.material_index = slot
        f.smooth = False
        for loop, (fu, fv) in zip(f.loops, uvs):
            loop[self.layer].uv = region_uv(texture, fu, fv)

    def obox(self, centre, axes, half, textures, slot=METAL):
        ax, ay, az = axes
        hx, hy, hz = half

        def c(sx, sy, sz):
            return add(centre, mul(ax, sx * hx), mul(ay, sy * hy), mul(az, sz * hz))
        sides = {
            "+z": ([c(-1, -1, 1), c(1, -1, 1), c(1, 1, 1), c(-1, 1, 1)], az),
            "-z": ([c(1, -1, -1), c(-1, -1, -1), c(-1, 1, -1), c(1, 1, -1)], mul(az, -1)),
            "+x": ([c(1, -1, 1), c(1, -1, -1), c(1, 1, -1), c(1, 1, 1)], ax),
            "-x": ([c(-1, -1, -1), c(-1, -1, 1), c(-1, 1, 1), c(-1, 1, -1)], mul(ax, -1)),
            "+y": ([c(-1, 1, 1), c(1, 1, 1), c(1, 1, -1), c(-1, 1, -1)], ay),
            "-y": ([c(-1, -1, -1), c(1, -1, -1), c(1, -1, 1), c(-1, -1, 1)], mul(ay, -1)),
        }
        for side, spec in textures.items():
            texture, face_slot = spec if isinstance(spec, tuple) else (spec, slot)
            pts, normal = sides[side]
            self.face(pts, [(0, 1), (1, 1), (1, 0), (0, 0)], texture, normal, face_slot)

    def box(self, lo, hi, textures, slot=METAL):
        centre = mul(add(lo, hi), 0.5)
        self.obox(centre, (X, Y, Z), tuple(abs(hi[i] - lo[i]) / 2 for i in range(3)), textures, slot)

    def frustum(self, y0, r0, y1, r1, texture, slot=METAL, outward=True, segments=14):
        """A ring of faces from radius r0 at height y0 to r1 at y1, facing out (or in)."""
        for i in range(segments):
            a0, a1 = i / segments * math.tau, (i + 1) / segments * math.tau
            p = [(r0 * math.cos(a0), y0, r0 * math.sin(a0)), (r0 * math.cos(a1), y0, r0 * math.sin(a1)),
                 (r1 * math.cos(a1), y1, r1 * math.sin(a1)), (r1 * math.cos(a0), y1, r1 * math.sin(a0))]
            mid = (a0 + a1) / 2
            normal = (math.cos(mid), (r0 - r1) / max(abs(y1 - y0), 1e-6) * (1 if y1 > y0 else -1), math.sin(mid))
            if not outward:
                normal = mul(normal, -1)
            self.face(p, [(i / segments, 1), ((i + 1) / segments, 1), ((i + 1) / segments, 0), (i / segments, 0)], texture, normal, slot)

    def disc(self, y, r, texture, normal_y, slot=METAL, segments=14):
        pts = [(r * math.cos(i / segments * math.tau), y, r * math.sin(i / segments * math.tau)) for i in range(segments)]
        uvs = [(0.5 + 0.5 * math.cos(i / segments * math.tau), 0.5 + 0.5 * math.sin(i / segments * math.tau)) for i in range(segments)]
        self.face(pts, uvs, texture, (0, normal_y, 0), slot)

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


def build_pendant():
    """A gallery pendant: a brass rod, a brass bell shade, and a glowing opal glass bowl under it."""
    b = Builder()
    rim, tall = L.PENDANT_SHADE
    bowl = L.PENDANT_BOWL
    rim_y = bowl                         # the bowl's bottom is the origin; the shade's rim sits on the bowl
    top_y = rim_y + tall
    b.box((-0.008, top_y, -0.008), (0.008, top_y + 0.7, 0.008), {s: "brass" for s in ("+x", "-x", "+z", "-z")})
    b.frustum(rim_y, rim, top_y, 0.05, "brass")                       # the shade, outside
    b.frustum(rim_y, rim * 0.97, top_y - 0.01, 0.045, "brass", outward=False)   # and inside
    b.disc(top_y, 0.05, "brass", 1)
    b.frustum(0.0, 0.1, rim_y, rim * 0.93, "opal", GLOW)            # the glass bowl
    b.disc(0.0, 0.1, "opal", -1, GLOW)
    return b.finish("pendant_lamp")


def build_panel():
    """An office light panel set into the ceiling: a painted steel frame round a prismatic lens."""
    b = Builder()
    w, d = L.PANEL
    b.box((-w / 2 - 0.03, -0.02, -d / 2 - 0.03), (w / 2 + 0.03, 0.0, d / 2 + 0.03), {s: "steel" for s in ("+x", "-x", "+z", "-z", "-y")})
    b.face([(-w / 2, -0.021, -d / 2), (w / 2, -0.021, -d / 2), (w / 2, -0.021, d / 2), (-w / 2, -0.021, d / 2)],
           [(0, 0), (1, 0), (1, 1), (0, 1)], "panel", (0, -1, 0), GLOW)
    return b.finish("light_panel")


def build_exit():
    """A lit EXIT sign in a white box, for the wall beside a door."""
    b = Builder()
    w, h, d = L.EXIT
    b.box((-w / 2, -h / 2, 0.0), (w / 2, h / 2, d), {"+z": ("exit", GLOW), "+x": "exit_side", "-x": "exit_side", "+y": "exit_side", "-y": "exit_side"})
    return b.finish("exit_sign")


def build_vent():
    """A wall vent: a painted frame, louvres angled down, the dark behind them, and the brass plate."""
    b = Builder()
    w, h = L.VENT
    f = 0.03
    b.face([(-w / 2, -h / 2, 0.003), (w / 2, -h / 2, 0.003), (w / 2, h / 2, 0.003), (-w / 2, h / 2, 0.003)], [(0, 1), (1, 1), (1, 0), (0, 0)], "vent_back", (0, 0, 1))
    for lo, hi in (((-w / 2, h / 2 - f, 0.0), (w / 2, h / 2, 0.03)), ((-w / 2, -h / 2, 0.0), (w / 2, -h / 2 + f, 0.03)),
                   ((-w / 2, -h / 2 + f, 0.0), (-w / 2 + f, h / 2 - f, 0.03)), ((w / 2 - f, -h / 2 + f, 0.0), (w / 2, h / 2 - f, 0.03))):
        b.box(lo, hi, {s: "steel" for s in ("+x", "-x", "+y", "-y", "+z")})
    slats = 6
    tilt = math.radians(35)
    up = (0.0, math.cos(tilt), math.sin(tilt))
    out = (0.0, -math.sin(tilt), math.cos(tilt))
    inner = h - 2 * f
    for k in range(slats):
        y = -h / 2 + f + (k + 0.5) * inner / slats
        b.obox((0.0, y, 0.016), (X, up, out), (w / 2 - f, inner / slats * 0.42, 0.003), {"+z": "steel", "-y": "steel", "+y": "steel"})
    pw, ph = 0.26, 0.055
    py = -h / 2 - 0.05 - ph / 2
    b.box((-pw / 2, py - ph / 2, 0.0), (pw / 2, py + ph / 2, 0.005), {"+z": "vent_plate", "+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"})
    return b.finish("wall_vent")


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


def prop_scene(name, note):
    title = "".join(p.title() for p in name.split("_"))
    (PROPS / (name + ".tscn")).write_text(
        '[gd_scene format=3]\n\n[ext_resource type="PackedScene" path="%s%s.glb" id="1_mesh"]\n\n'
        '[node name="%s" type="Node3D"]\neditor_description = "%s"\n\n[node name="Mesh" parent="." instance=ExtResource("1_mesh")]\n'
        % (RES, name, title, note), encoding="utf8", newline="\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
export(build_pendant())
prop_scene("pendant_lamp", "A brass pendant with a glowing opal bowl (asset P1.5). Origin: the bowl's bottom; hang it %.2f m above a room light, so the light shines down freely and the lamp only leaves a small shadow on the ceiling. Its rod runs up into the ceiling. No collision." % L.PENDANT_LIFT)
export(build_panel())
prop_scene("light_panel", "An office light panel, flush with the ceiling (asset P1.5). Origin: the centre of its face at ceiling height, facing down. No collision.")
export(build_exit())
prop_scene("exit_sign", "A lit green EXIT sign (asset P1.5). Origin: the centre of its back, on the wall, facing +z. The arrow points to its right as you face it, so hang it to the left of the way out. No collision.")
export(build_vent())
prop_scene("wall_vent", "A wall vent with louvres, and a brass plate under it: NOT AN ESCAPE ROUTE. We checked. (asset P1.5). Origin: the centre of its back, on the wall, facing +z. No collision.")
print("fixtures built")
