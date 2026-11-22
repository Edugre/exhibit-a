"""Shared helpers for the interior's Blender build scripts. Shapes are made in Blender's own axes
(Z up, the front of a prop facing -Y), which become Godot's Y up and +Z front on export.
Each part is fitted into one rectangle of its set's atlas; printed faces get a rectangle of their own."""
import json
import math
import bmesh
import bpy
from mathutils import Matrix, Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


class Atlas:
    def __init__(self, layout_path, png_path):
        layout = json.load(open(layout_path))
        self.w, self.h = layout["size"]
        self.rects = layout["rects"]
        self.image = bpy.data.images.load(str(png_path))

    def uv(self, name, inset=3):
        """The rectangle as (u0, v0, u1, v1) in Blender's UV space (v up), pulled in a few pixels."""
        x0, y0, x1, y1 = self.rects[name]
        return ((x0 + inset) / self.w, 1 - (y1 - inset) / self.h, (x1 - inset) / self.w, 1 - (y0 + inset) / self.h)


def material(name, image, metallic=0.0, roughness=0.5, alpha=1.0, emission=0.0):
    """alpha below 1 makes it see-through (glass); emission above 0 makes the texture glow (lamp shades)."""
    m = bpy.data.materials.new(name)
    if hasattr(m, "use_nodes") and not m.use_nodes:
        m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None) or nodes.new("ShaderNodeOutputMaterial")
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        elif hasattr(m, "blend_method"):
            m.blend_method = "BLEND"
    if emission > 0.0:
        links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    return m


def at(x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0):
    """A placement: rotate (degrees, X then Y then Z), then move."""
    r = Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Rotation(math.radians(ry), 4, "Y") @ Matrix.Rotation(math.radians(rx), 4, "X")
    return Matrix.Translation((x, y, z)) @ r


class Builder:
    """Collects parts into one mesh. Every part is (faces, material slot, atlas rectangle)."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.verify()

    # --- parts ---------------------------------------------------------------

    def cylinder(self, r1, r2, depth, slot, rect, place, segments=24, caps=True):
        """Along Z, centred on the placement."""
        g = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=segments,
                                  radius1=r1, radius2=r2, depth=depth)
        return self._finish(g["verts"], slot, rect, place)

    def box(self, sx, sy, sz, slot, rect, place, bevel=0.0):
        g = bmesh.ops.create_cube(self.bm, size=1.0)
        bmesh.ops.scale(self.bm, vec=(sx, sy, sz), verts=g["verts"])
        verts = g["verts"]
        if bevel > 0:
            edges = list({e for v in verts for e in v.link_edges})
            res = bmesh.ops.bevel(self.bm, geom=edges, offset=bevel, segments=3, profile=0.5, affect="EDGES")
            verts = list({v for f in res["faces"] for v in f.verts} | {v for v in verts if v.is_valid})
            verts = list({v for f in self._faces(verts) for v in f.verts})
        return self._finish(verts, slot, rect, place)

    def sphere(self, radius, slot, rect, place, squash=1.0, segments=16, rings=10):
        g = bmesh.ops.create_uvsphere(self.bm, u_segments=segments, v_segments=rings, radius=radius)
        bmesh.ops.scale(self.bm, vec=(1, 1, squash), verts=g["verts"])
        return self._finish(g["verts"], slot, rect, place)

    def tube(self, points, radius, slot, rect, segments=10):
        """A round tube through the points (world positions), with closed ends."""
        rings = []
        for i, p in enumerate(points):
            a = points[max(i - 1, 0)]
            b = points[min(i + 1, len(points) - 1)]
            t = (Vector(b) - Vector(a)).normalized()
            side = t.cross(Vector((0, 0, 1)))
            if side.length < 1e-4:
                side = t.cross(Vector((0, 1, 0)))
            side.normalize()
            up = side.cross(t).normalized()
            ring = []
            for k in range(segments):
                ang = 2 * math.pi * k / segments
                ring.append(self.bm.verts.new(Vector(p) + radius * (math.cos(ang) * side + math.sin(ang) * up)))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(segments):
                self.bm.faces.new((r0[k], r0[(k + 1) % segments], r1[(k + 1) % segments], r1[k]))
        self.bm.faces.new(list(reversed(rings[0])))
        self.bm.faces.new(rings[-1])
        verts = [v for r in rings for v in r]
        return self._finish(verts, slot, rect, Matrix.Identity(4))

    # --- UVs -------------------------------------------------------------------

    def print_face(self, faces, toward, u_axis, v_axis, rect):
        """Lay a printed rectangle over the one face of `faces` that looks most along `toward`.
        u_axis points to the viewer's right, v_axis up the print."""
        self.bm.normal_update()
        face = max(faces, key=lambda f: f.normal.dot(Vector(toward)))
        u_axis, v_axis = Vector(u_axis).normalized(), Vector(v_axis).normalized()
        us = [l.vert.co.dot(u_axis) for l in face.loops]
        vs = [l.vert.co.dot(v_axis) for l in face.loops]
        u0, v0, u1, v1 = rect
        for l, u, v in zip(face.loops, us, vs):
            l[self.uv].uv = (u0 + (u - min(us)) / (max(us) - min(us)) * (u1 - u0),
                             v0 + (v - min(vs)) / (max(vs) - min(vs)) * (v1 - v0))
        return face

    def _faces(self, verts):
        return {f for v in verts if v.is_valid for f in v.link_faces}

    def _finish(self, verts, slot, rect, place):
        bmesh.ops.transform(self.bm, matrix=place, verts=verts)
        faces = self._faces(verts)
        self.bm.normal_update()
        # Box projection: each face onto the plane it faces most, the whole part fitted into the rectangle
        coords = []
        for f in faces:
            f.material_index = slot
            f.smooth = True
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            keep = [i for i in range(3) if i != ax]
            for l in f.loops:
                coords.append((l, l.vert.co[keep[0]], l.vert.co[keep[1]]))
        if coords:
            mu, mv = min(c[1] for c in coords), min(c[2] for c in coords)
            span = max(max(c[1] for c in coords) - mu, max(c[2] for c in coords) - mv, 1e-4)
            u0, v0, u1, v1 = rect
            for l, a, b in coords:
                l[self.uv].uv = (u0 + (a - mu) / span * (u1 - u0), v0 + (b - mv) / span * (v1 - v0))
        return faces

    # --- output ------------------------------------------------------------------

    def object(self, name, materials, sharp_angle=35.0):
        mesh = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in materials:
            mesh.materials.append(m)
        if hasattr(mesh, "set_sharp_from_angle"):
            mesh.set_sharp_from_angle(angle=math.radians(sharp_angle))
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def export(obj, path):
    """One prop per .gltf; the atlas stays a separate .png beside it, so a set's props share it."""
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLTF_SEPARATE", use_selection=True,
                              export_yup=True, export_apply=True)
    print("wrote", path)
