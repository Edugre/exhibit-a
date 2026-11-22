"""Builds the doorway set (asset item K1) in a background Blender:
  blender -b --factory-startup --python doorway_build.py -- <assets/interior/doorways folder> <scenes/props folder>
Writes doorway_portal (a room's entrance: a stone arch), doorway_jambs (a room's exit: carved sides, open
to the ceiling for the sliding gate) and one brass plaque per room (room_plaque_<room>): each a .glb, its
import settings and a prop scene. Run make_doorway_art.py for the texture and materials.

Every piece's origin is the doorway's centre on the floor, on the line where the two rooms meet: put it on
the room's Entry or Exit marker without turning it. Shapes here are written in the game's axes (y up, the
room running along -z from its Entry) and turned into Blender's (z up) only when a vertex is made."""
import math
import pathlib
import sys

import bmesh
import bpy

sys.dont_write_bytecode = True
TOOLS = pathlib.Path(__file__).parent
sys.path.insert(0, str(TOOLS))
import doorway_layout as L  # noqa: E402
import int_dims as D  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = pathlib.Path(ARGS[0])
PROPS = pathlib.Path(ARGS[1])
OUT.mkdir(parents=True, exist_ok=True)
RES = "res://assets/interior/doorways/"
KIT = "res://assets/interior/kit/"
N = L.ATLAS
STONE, BRASS, LAMP, MOULD = 0, 1, 2, 3
MATERIALS = (("int_doorway", RES), ("int_plaque", RES), ("int_plaque_lamp", RES), ("int_moulding", KIT))

T = D.WALL_T
HALF = L.HALF
R1, R2 = L.RADIUS, L.RADIUS + L.RING
CY = L.CENTRE_Y


def bl(p):
    x, y, z = p
    return (x, -z, y)


def region_uv(name, fu, fv):
    x, y, w, h = L.REGIONS[name]
    fu, fv = min(max(fu, 0.0), 1.0), min(max(fv, 0.0), 1.0)
    return ((x + 1 + fu * (w - 2)) / N, 1 - (y + 1 + fv * (h - 2)) / N)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


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

    def face(self, pts, uvs, texture, normal, slot=STONE):
        """A polygon in game axes, wound to face `normal`; uvs are (across, down) within the texture's region."""
        n = newell(pts)
        if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
            pts, uvs = pts[::-1], uvs[::-1]
        f = self.bm.faces.new([self.bm.verts.new(bl(p)) for p in pts])
        f.material_index = slot
        for loop, (fu, fv) in zip(f.loops, uvs):
            loop[self.layer].uv = region_uv(texture, fu, fv)

    def box(self, lo, hi, textures, slot=STONE, uv=None):
        """A box in game axes. textures maps sides (+x -x +y -y +z -z) to regions; sides left out aren't made.
        uv(side, point) can replace the plain 0..1 stretch on a side."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        sides = {
            "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),
            "-z": ([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], (0, 0, -1)),
            "+x": ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], (1, 0, 0)),
            "-x": ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
            "+y": ([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], (0, 1, 0)),
            "-y": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
        }
        for side, texture in textures.items():
            pts, normal = sides[side]
            uvs = [uv(side, p) for p in pts] if uv else [(0, 1), (1, 1), (1, 0), (0, 0)]
            self.face(pts, uvs, texture, normal, slot)

    def finish(self, name):
        mesh = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m, _ in MATERIALS:
            mesh.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
        mesh.validate()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def intrados(phi):
    return (R1 * math.sin(phi), CY + R1 * math.cos(phi))


def extrados(phi):
    return (R2 * math.sin(phi), CY + R2 * math.cos(phi))


def side_strip_uv(top, bottom, outward=True):
    """For the carved strips up a doorway's sides: across runs from the opening's edge outwards, on either side."""
    def uv(side, p):
        return ((abs(p[0]) - HALF) / L.PILASTER_W if outward else 0.5, (top - p[1]) / (top - bottom))
    return uv


def jamb_parts(b, face_z, sign, top, crown):
    """The plinth and the carved strip up one side of a doorway. face_z is the wall face, sign the way
    into the room (-1 for an entrance, whose room lies along -z; +1 for an exit). crown tops the strip."""
    front = "+z" if sign > 0 else "-z"
    for sx in (1, -1):
        def span(a, c):
            return (min(sx * a, sx * c), max(sx * a, sx * c))
        xa, xb = span(HALF, HALF + L.PILASTER_W + 0.05)
        za, zb = sorted((face_z, face_z + sign * L.PLINTH_T))
        b.box((xa, 0.0, za), (xb, L.PLINTH_H, zb), {front: "plinth", "+x": "plinth", "-x": "plinth", "+y": "stone"})
        xa, xb = span(HALF, HALF + L.PILASTER_W)
        za, zb = sorted((face_z, face_z + sign * L.PILASTER_T))
        b.box((xa, L.PLINTH_H, za), (xb, top, zb), {front: "casing", "+x": "stone", "-x": "stone"},
              uv=lambda side, p, s=front: side_strip_uv(top, L.PLINTH_H)(side, p) if side == s else ((p[2] - za) / (zb - za), (top - p[1]) / (top - L.PLINTH_H)))
        crown(b, sx, front, sign)


def build_portal():
    """A room's entrance: a segmental arch of dressed stones with an owl on the keystone, carved jambs
    on the room side, and a stretch of the room's cornice across the top. The far face, towards the room
    you come from, is plain stone: the plaque goes there."""
    b = Builder()
    z_in, z_out = -T - L.RING_PROUD_IN, L.RING_PROUD_OUT
    key = 0.11 / R1
    th0 = L.HALF_ANGLE
    edges = [key + (th0 - key) * j / L.VOUSSOIRS for j in range(L.VOUSSOIRS + 1)]
    blocks = [(-edges[j + 1], -edges[j]) for j in reversed(range(L.VOUSSOIRS))] + [(-key, key)] + [(edges[j], edges[j + 1]) for j in range(L.VOUSSOIRS)]
    for k, (a, c) in enumerate(blocks):
        tex = "block_%d" % ((k * 3) % 8)
        pa, pc, qa, qc = intrados(a), intrados(c), extrados(a), extrados(c)
        for z, normal in ((z_in, (0, 0, -1)), (z_out, (0, 0, 1))):
            b.face([(pa[0], pa[1], z), (pc[0], pc[1], z), (qc[0], qc[1], z), (qa[0], qa[1], z)], [(0, 1), (1, 1), (1, 0), (0, 0)], tex, normal)
        m = (a + c) / 2
        up = (math.sin(m), math.cos(m), 0)
        for z0, z1 in ((-T, z_in), (0.0, z_out)):   # the ring's edge where it stands proud of each face
            b.face([(qa[0], qa[1], z0), (qc[0], qc[1], z0), (qc[0], qc[1], z1), (qa[0], qa[1], z1)], [(0, 0.1), (1, 0.1), (1, 0), (0, 0)], tex, up)
        b.face([(pa[0], pa[1], z_out), (pc[0], pc[1], z_out), (pc[0], pc[1], z_in), (pa[0], pa[1], z_in)], [(0, 0), (1, 0), (1, 1), (0, 1)], tex, (-up[0], -up[1], 0))
    for phi, sx in ((th0, 1), (-th0, -1)):          # the springers' beds, where they stand proud
        p, q = intrados(phi), extrados(phi)
        normal = (sx * math.cos(th0), -math.sin(th0), 0)
        for z0, z1 in ((-T, z_in), (0.0, z_out)):
            b.face([(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)], [(0, 1), (1, 1), (1, 0), (0, 0)], "stone", normal)

    # The keystone, on the room side: deeper than the ring, hanging a little below it, with the owl
    yb, yt = CY + R1 - 0.07, D.CORNICE_Y0 - 0.04
    zk, zb = -T - 0.11, -T + 0.02
    bot, top = (0.1, yb), (0.15, yt)
    b.face([(-bot[0], yb, zk), (bot[0], yb, zk), (top[0], yt, zk), (-top[0], yt, zk)], [(0, 1), (1, 1), (1, 0), (0, 0)], "keystone", (0, 0, -1))
    for sx in (1, -1):
        b.face([(sx * bot[0], yb, zk), (sx * bot[0], yb, zb), (sx * top[0], yt, zb), (sx * top[0], yt, zk)], [(0, 1), (1, 1), (1, 0), (0, 0)], "stone", (sx, 0, 0))
    b.face([(-top[0], yt, zk), (top[0], yt, zk), (top[0], yt, zb), (-top[0], yt, zb)], [(0, 1), (1, 1), (1, 0), (0, 0)], "stone", (0, 1, 0))
    b.face([(-bot[0], yb, zb), (bot[0], yb, zb), (bot[0], yb, zk), (-bot[0], yb, zk)], [(0, 1), (1, 1), (1, 0), (0, 0)], "stone", (0, -1, 0))

    # The stone filling the doorway above the arch, on both faces
    phx = math.asin(HALF / R2)
    steps = 16
    y_low = CY + R2 * math.cos(phx)
    for i in range(steps):
        a, c = -phx + 2 * phx * i / steps, -phx + 2 * phx * (i + 1) / steps
        qa, qc = extrados(a), extrados(c)
        uv = lambda p: ((p[0] + HALF) / (2 * HALF), (D.WALL_H - p[1]) / (D.WALL_H - y_low))
        for z, normal in ((-T, (0, 0, -1)), (0.0, (0, 0, 1))):
            pts = [(qa[0], qa[1], z), (qc[0], qc[1], z), (qc[0], D.WALL_H, z), (qa[0], D.WALL_H, z)]
            b.face(pts, [uv(p) for p in pts], "stone", normal)

    # Stone linings on the opening's sides, up to the arch
    for sx in (1, -1):
        x = sx * (HALF - 0.01)
        pts = [(x, 0.0, z_out), (x, 0.0, z_in), (x, L.SPRING_Y, z_in), (x, L.SPRING_Y, z_out)]
        b.face(pts, [((z_out - p[2]) / (z_out - z_in), 1 - p[1] / L.SPRING_Y) for p in pts], "stone", (-sx, 0, 0))

    def impost(b, sx, front, sign):
        xa, xb = sorted((sx * HALF, sx * (HALF + L.PILASTER_W + 0.06)))
        y0 = L.SPRING_Y - L.IMPOST_H
        b.box((xa, y0, -T - 0.1), (xb, L.SPRING_Y, -T), {"-z": "impost", "+x": "impost", "-x": "impost", "+y": "stone", "-y": "stone"},
              uv=lambda side, p: ((p[0] - xa) / (xb - xa) if side in ("-z", "+y", "-y") else (p[2] + T + 0.1) / 0.1, (L.SPRING_Y - p[1]) / L.IMPOST_H))
    jamb_parts(b, -T, -1, L.SPRING_Y - L.IMPOST_H, impost)

    # The room's cornice, carried across over the doorway (the kit's carved band, laid on by height)
    b.box((-HALF, D.CORNICE_Y0, -T - D.CORNICE_T), (HALF, D.WALL_H, -T), {"-z": "stone", "-y": "stone"}, slot=MOULD)
    return b.finish("doorway_portal")


def build_jambs():
    """A room's exit: carved strips up both sides on the room side, each ending in a scroll bracket under
    the cornice. Open to the ceiling between them, so the next room's arch and plaque show through and
    the RoomGate can slide up."""
    b = Builder()
    top = D.CORNICE_Y0 - L.CONSOLE_H
    split = top + L.CONSOLE_H * 0.45

    def console(b, sx, front, sign):
        xa, xb = sorted((sx * HALF, sx * (HALF + L.PILASTER_W + 0.04)))
        for (y0, y1, depth, v0, v1) in ((top, split, 0.09, 0.5, 1.0), (split, D.CORNICE_Y0, 0.14, 0.0, 0.5)):
            b.box((xa, y0, T), (xb, y1, T + depth), {"+z": "console", "+x": "stone", "-x": "stone", "-y": "stone"},
                  uv=lambda side, p, y0=y0, y1=y1, v0=v0, v1=v1, d=depth: ((p[0] - xa) / (xb - xa) if side == "+z" else (p[2] - T) / d,
                                                                         v0 + (v1 - v0) * (y1 - p[1]) / (y1 - y0)))
    jamb_parts(b, T, 1, top, console)
    return b.finish("doorway_jambs")


def build_plaque(name):
    """A brass plaque on the far face of a room's entrance, over the arch, with a little lamp above it."""
    b = Builder()
    w, h, y = L.PLAQUE_W, L.PLAQUE_H, L.PLAQUE_Y
    b.box((-w / 2 - 0.025, y - 0.025, 0.0), (w / 2 + 0.025, y + h + 0.025, 0.012), {"+z": "brass", "+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"}, slot=BRASS)
    b.box((-w / 2, y, 0.012), (w / 2, y + h, 0.024), {"+z": "plaque_" + name, "+x": "brass", "-x": "brass", "+y": "brass", "-y": "brass"}, slot=BRASS)
    ly = y + h + 0.06
    b.box((-0.42, ly, 0.0), (0.42, ly + 0.035, 0.11), {"+z": "brass", "+x": "brass", "-x": "brass", "+y": "brass"}, slot=BRASS)
    b.face([(-0.4, ly - 0.001, 0.005), (0.4, ly - 0.001, 0.005), (0.4, ly - 0.001, 0.1), (-0.4, ly - 0.001, 0.1)], [(0, 1), (1, 1), (1, 0), (0, 0)], "lamp", (0, -1, 0), LAMP)
    for sx in (1, -1):    # the lamp's two arms
        b.box((sx * 0.3 - 0.012, ly + 0.035, 0.0), (sx * 0.3 + 0.012, ly + 0.06, 0.03), {"+z": "brass", "+x": "brass", "-x": "brass", "+y": "brass"}, slot=BRASS)
    return b.finish("room_plaque_" + name)


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
        mats = ",\n".join(MAT_ENTRY.format(mat=m, res=res) for m, res in MATERIALS)
        target.write_text(GLB_IMPORT.format(res=RES, name=obj.name, materials=mats), encoding="utf8", newline="\n")
    print("exported", obj.name, len(obj.data.polygons), "faces")


def prop_scene(name, box, note):
    """box is (size, centre) in the game's axes, or None for no collision."""
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
    (PROPS / (name + ".tscn")).write_text("".join(parts), encoding="utf8", newline="\n")


PLACE = "Put it on the room's %s marker, unturned, outside the NavigationRegion3D like the Trim."
bpy.ops.wm.read_factory_settings(use_empty=True)
export(build_portal())
head = D.WALL_H - D.DOOR_H
prop_scene("doorway_portal", ((D.DOOR_W, head, T), (0, D.DOOR_H + head / 2, -T / 2)),
           "A room's entrance (asset K1): a stone arch in the half of the doorway the room owns, with an owl on the keystone. "
           "The opening stays 3 m wide and 3.2 m high. Pair it with the room's plaque. " + PLACE % "Entry")
export(build_jambs())
prop_scene("doorway_jambs", None,
           "A room's exit (asset K1): carved sides, open to the ceiling, so the next room's arch and plaque show through and the RoomGate can slide up. " + PLACE % "Exit")
for name, title, _ in L.PLAQUES:
    export(build_plaque(name))
    prop_scene("room_plaque_" + name, None,
               "The %s plaque (asset K1), over the arch on the side facing the room you come from, with a small lamp. %s" % (title.title(), PLACE % "Entry"))
print("doorways built")
