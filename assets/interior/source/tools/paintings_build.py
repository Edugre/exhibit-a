"""Builds the framed paintings (asset item P1.3) in a background Blender:
  blender -b --factory-startup --python paintings_build.py -- <assets/interior/paintings folder> <scenes/props folder>
Writes one painting_<name> per picture: the canvas in a carved gilt frame with mitred corners, a brass
title label on the wall under it and a little picture light above it. Each is a .glb, its import settings
and a prop scene. Run make_paintings_art.py for the texture and materials.

A painting's origin is its centre, on the wall's surface; it faces +z, so turn it to face into the room.
Shapes are written in the game's axes (y up) and turned into Blender's (z up) when a vertex is made."""
import math
import pathlib
import sys

import bmesh
import bpy

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import paintings_layout as L  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/paintings/"
N = L.ATLAS
CANVAS, GILT, LAMP = 0, 1, 2
MATERIALS = ("int_canvas", "int_gilt", "int_picture_lamp")


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


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.layer = self.bm.loops.layers.uv.new("UVMap")

    def face(self, pts, uvs, texture, normal, slot=GILT):
        n = newell(pts)
        if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
            pts, uvs = pts[::-1], uvs[::-1]
        f = self.bm.faces.new([self.bm.verts.new(bl(p)) for p in pts])
        f.material_index = slot
        for loop, (fu, fv) in zip(f.loops, uvs):
            loop[self.layer].uv = region_uv(texture, fu, fv)

    def box(self, lo, hi, textures, slot=GILT):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        sides = {
            "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),
            "+x": ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], (1, 0, 0)),
            "-x": ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
            "+y": ([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], (0, 1, 0)),
            "-y": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
        }
        for side, texture in textures.items():
            pts, normal = sides[side]
            self.face(pts, [(0, 1), (1, 1), (1, 0), (0, 0)], texture, normal, slot)

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


def frame_band(b, w, h, m, inner_a, z_a, inner_b, z_b, u_a, u_b, texture, normal_tilt):
    """One band of the moulding all the way round: from a ring `inner_a` in from the outside edge at height
    z_a to a ring `inner_b` in at z_b, as four mitred pieces. The carving runs across the band from u_a to
    u_b; along it, each length of about eight moulding widths takes the strip once, so the ornament keeps
    its proportions and joins up where two lengths meet."""
    for side in ("top", "right", "bottom", "left"):
        horizontal = side in ("top", "bottom")
        length = w if horizontal else h
        pieces = max(1, round(length / (8 * m)))
        sgn = 1 if side in ("top", "right") else -1

        def point(inset, z, t):
            """t runs 0..1 along this side's outer edge; the inset ring is clipped to the mitres."""
            half_w, half_h = w / 2 - inset, h / 2 - inset
            if horizontal:
                x = -w / 2 + t * w
                return (max(-half_w, min(half_w, x)), sgn * half_h, z)
            y = -h / 2 + t * h
            return (sgn * half_w, max(-half_h, min(half_h, y)), z)

        out = (0, sgn, 0) if horizontal else (sgn, 0, 0)
        normal = (out[0] * normal_tilt, out[1] * normal_tilt, 1.0)
        for k in range(pieces):
            t0, t1 = k / pieces, (k + 1) / pieces
            pts = [point(inner_a, z_a, t0), point(inner_a, z_a, t1), point(inner_b, z_b, t1), point(inner_b, z_b, t0)]

            def v(p):
                along = (p[0] + w / 2) / w if horizontal else (p[1] + h / 2) / h
                return (along - t0) / (t1 - t0)
            uvs = [(u_a, v(pts[0])), (u_a, v(pts[1])), (u_b, v(pts[2])), (u_b, v(pts[3]))]
            b.face(pts, uvs, texture, normal)


def build_painting(name):
    frame, _, _, _ = L.PAINTINGS[name]
    _, _, m, depth = L.FRAMES[frame]
    w, h = L.outer(name)
    cw, ch = L.canvas(name)
    b = Builder()
    z_canvas, z_lip, z_crest, z_edge = depth * 0.35, depth * 0.75, depth, depth * 0.6
    b.face([(-cw / 2, -ch / 2, z_canvas), (cw / 2, -ch / 2, z_canvas), (cw / 2, ch / 2, z_canvas), (-cw / 2, ch / 2, z_canvas)],
           [(0, 1), (1, 1), (1, 0), (0, 0)], name, (0, 0, 1), CANVAS)
    frame_band(b, w, h, m, 0.0, 0.0, 0.0, z_edge, 0.0, 1.0, "gilt_plain", 8.0)        # the frame's outside edge
    frame_band(b, w, h, m, 0.0, z_edge, m * 0.45, z_crest, 0.0, 0.5, "gilt", 0.6)      # the outer slope of the carving
    frame_band(b, w, h, m, m * 0.45, z_crest, m, z_lip, 0.5, 1.0, "gilt", -0.6)        # the inner slope, down to the sight edge
    frame_band(b, w, h, m, m, z_lip, m, z_canvas, 0.0, 1.0, "gilt_plain", -8.0)       # the sight edge, down to the canvas

    lw, lh = L.LABEL                                                                    # the title label, on the wall below
    ly = -h / 2 - L.LABEL_GAP
    b.box((-lw / 2, ly - lh, 0.0), (lw / 2, ly, 0.006), {"+z": "label_" + name, "+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"})

    top = h / 2                                                                         # the picture light
    hood = min(0.5, w * 0.42)
    b.box((-0.025, top + 0.04, 0.0), (0.025, top + 0.12, 0.012), {"+z": "brass", "+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"})
    b.box((-0.009, top + 0.075, 0.012), (0.009, top + 0.093, 0.17), {"+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"})
    b.box((-hood / 2, top + 0.065, 0.14), (hood / 2, top + 0.105, 0.22), {"+z": "brass", "+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"})
    y_lamp = top + 0.064
    b.face([(-hood / 2 + 0.01, y_lamp, 0.145), (hood / 2 - 0.01, y_lamp, 0.145), (hood / 2 - 0.01, y_lamp, 0.215), (-hood / 2 + 0.01, y_lamp, 0.215)],
           [(0, 1), (1, 1), (1, 0), (0, 0)], "lamp", (0, -1, 0), LAMP)
    return b.finish("painting_" + name)


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
for name, (frame, _, title, subtitle) in L.PAINTINGS.items():
    export(build_painting(name))
    w, h = L.outer(name)
    prop_scene("painting_" + name, "%s (%s). A %s frame, %.2f x %.2f m, with its label below and a picture light above (asset P1.3). "
               "The origin is the painting's centre on the wall's surface, facing +z: turn it to face into the room. No collision, like the trim."
               % (title, subtitle.replace("'", "’"), frame, w, h))
print("paintings built")
