"""Rebuild the blockout, then give it a neutral sun, sky and camera. Runs inside Blender."""
import math
import bpy
from mathutils import Vector

HERE = r"C:\Users\waism\AppData\Local\Temp\claude\d9410d616540b704\746404c1-ba82-4f49-96dc-c53702a1de63\scratchpad\blender"
exec(compile(open(HERE + r"\blockout_build.py").read(), "blockout_build.py", "exec"), {"__name__": "blockout"})

scene = bpy.context.window.scene
w = bpy.data.worlds.get("BO_World") or bpy.data.worlds.new("BO_World")
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.62, 0.72, 0.86, 1)
bg.inputs[1].default_value = 0.9
scene.world = w

sd = bpy.data.lights.get("BO_Sun") or bpy.data.lights.new("BO_Sun", "SUN")
sd.energy = 3.0
sun = bpy.data.objects.new("BO_Sun", sd)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(58), 0, math.radians(35))

cd = bpy.data.cameras.get("BO_Cam") or bpy.data.cameras.new("BO_Cam")
cam = bpy.data.objects.new("BO_Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 1280, 720


def shoot(eye, target, lens):
    """Eye and target in Godot coordinates."""
    e = Vector((eye[0], -eye[2], eye[1]))
    t = Vector((target[0], -target[2], target[1]))
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 1000


shoot(*globals().get("VIEW", ((16, -2.9, 42), (2, 11, 8), 20)))
