# Read into gen_front.py. Writes the street's scene text: cars, signal lamps, flags, steam and sound.
STREET_RES, STREET_SUBS, STREET_NODES = "", "", []
PROPS_ART = json.load(open(pathlib.Path(__file__).parent / "props_layout.json"))
CAR_MODELS = [("taxi", 5), ("sedan", 4), ("maroon", 3), ("van", 2)]
for name, count in CAR_MODELS:
    STREET_RES += f'[ext_resource type="ArrayMesh" path="res://assets/exterior/meshes/car_{name}.res" id="car_{name}"]\n'
    STREET_SUBS += f'[sub_resource type="MultiMesh" id="traffic_{name}"]\ntransform_format = 1\nmesh = ExtResource("car_{name}")\n\n'
for name in SOUNDS:
    STREET_RES += f'[ext_resource type="AudioStream" path="{RES}{name}.wav" id="snd_{name}"]\n'

STREET_SUBS += """[sub_resource type="QuadMesh" id="beam_quad"]
size = Vector2(4.2, 9.0)
orientation = 1
center_offset = Vector3(-6.4, 0.03, 0)

[sub_resource type="ShaderMaterial" id="beam_look"]
shader = ExtResource("beam_shader")

[sub_resource type="MultiMesh" id="traffic_beams"]
transform_format = 1
mesh = SubResource("beam_quad")

[sub_resource type="SphereMesh" id="lamp_ball"]
radius = 0.13
height = 0.26
radial_segments = 8
rings = 4

[sub_resource type="StandardMaterial3D" id="lamp_red"]
shading_mode = 0
albedo_color = Color(1, 0.12, 0.08, 1)
disable_receive_shadows = true

[sub_resource type="StandardMaterial3D" id="lamp_green"]
shading_mode = 0
albedo_color = Color(0.2, 1, 0.65, 1)
disable_receive_shadows = true

"""
for tag, key in (("hand", "hand"), ("walk", "walker")):
    u0, v0, u1, v1 = PROPS_ART["signs"][key]
    STREET_SUBS += f"""[sub_resource type="StandardMaterial3D" id="sign_{tag}"]
shading_mode = 0
albedo_texture = ExtResource("props_tex")
uv1_scale = Vector3({u1 - u0:.5f}, {v1 - v0:.5f}, 1)
uv1_offset = Vector3({u0:.5f}, {1 - v1:.5f}, 0)

"""
STREET_SUBS += """[sub_resource type="QuadMesh" id="sign_quad"]
size = Vector2(0.3, 0.3)

"""
u0, v0, u1, v1 = PROPS_ART["signs"]["flag"]
STREET_SUBS += f"""[sub_resource type="PlaneMesh" id="flag_cloth"]
size = Vector2(3.4, 2.04)
subdivide_width = 28
subdivide_depth = 10
orientation = 2

[sub_resource type="ShaderMaterial" id="flag_look"]
shader = ExtResource("flag_shader")
shader_parameter/print_map = ExtResource("props_tex")
shader_parameter/print_rect = Vector4({u0:.5f}, {1 - v1:.5f}, {u1:.5f}, {1 - v0:.5f})

[sub_resource type="QuadMesh" id="steam_puff"]
size = Vector2(1.5, 1.5)

[sub_resource type="ShaderMaterial" id="steam_look"]
shader = ExtResource("steam_shader")

[sub_resource type="ParticleProcessMaterial" id="steam_motion"]
emission_shape = 1
emission_sphere_radius = 0.25
direction = Vector3(0.1, 1, 0)
spread = 9.0
gravity = Vector3(0.25, 0.25, 0)
initial_velocity_min = 0.7
initial_velocity_max = 1.3
damping_min = 0.15
damping_max = 0.3
scale_min = 0.5
scale_max = 1.5

[sub_resource type="ParticleProcessMaterial" id="cart_motion"]
direction = Vector3(0, 1, 0)
spread = 6.0
gravity = Vector3(0.1, 0.1, 0)
initial_velocity_min = 0.25
initial_velocity_max = 0.45
scale_min = 0.12
scale_max = 0.3

"""

lane_paths = []
n = STREET_NODES
n.append(f'[node name="Traffic" type="Node3D" parent="."]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, {D.ROAD_Y}, 0)\nscript = ExtResource("traffic")\n'
         + "models = Array[NodePath]([" + ", ".join(f'NodePath("{name}")' for name, _ in CAR_MODELS) + "])\n"
         + "counts = Array[int]([" + ", ".join(str(c) for _, c in CAR_MODELS) + "])\n"
         + 'beams = NodePath("Beams")\nhorn = NodePath("Horn")\nengine = NodePath("Engine")\n'
         + 'red_lamps = Array[NodePath]([NodePath("RedNear"), NodePath("RedFar")])\ngreen_lamps = Array[NodePath]([NodePath("GreenNear"), NodePath("GreenFar")])\n'
         + 'hand_signs = Array[NodePath]([NodePath("HandNear"), NodePath("HandFar")])\nwalk_signs = Array[NodePath]([NodePath("WalkNear"), NodePath("WalkFar")])\n')
for name, _ in CAR_MODELS:
    n.append(f'[node name="{name}" type="MultiMeshInstance3D" parent="Traffic"]\nmaterial_override = ExtResource("props_mat")\ncast_shadow = 0\nmultimesh = SubResource("traffic_{name}")\n')
n.append('[node name="Beams" type="MultiMeshInstance3D" parent="Traffic"]\nmaterial_override = SubResource("beam_look")\ncast_shadow = 0\nmultimesh = SubResource("traffic_beams")\n')
n.append('[node name="Horn" type="AudioStreamPlayer3D" parent="Traffic"]\nstream = ExtResource("snd_car_horn")\nunit_size = 18.0\nmax_distance = 140.0\n')
n.append('[node name="Engine" type="AudioStreamPlayer3D" parent="Traffic"]\nstream = ExtResource("snd_car_engine")\nvolume_db = -7.0\nunit_size = 7.0\nmax_distance = 70.0\nautoplay = true\n')
n.append(f'[node name="ParkedTaxi" type="MeshInstance3D" parent="Traffic"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -20, 0, 36.4)\nmesh = ExtResource("car_taxi")\nmaterial_override = ExtResource("props_mat")\n')
# Signal heads: arm tips of the two masts, and the walkers' boxes on them, as world positions
HEADS = {"Near": (-6.33, 41.8), "Far": (-6.33, 46.5)}
for tag, (x, z) in HEADS.items():
    y = D.PLAZA_Y - D.ROAD_Y
    n.append(f'[node name="Red{tag}" type="MeshInstance3D" parent="Traffic"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x}, {y + 5.65}, {z})\nmesh = SubResource("lamp_ball")\nsurface_material_override/0 = SubResource("lamp_red")\ncast_shadow = 0\n')
    n.append(f'[node name="Green{tag}" type="MeshInstance3D" parent="Traffic"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x}, {y + 4.91}, {z})\nmesh = SubResource("lamp_ball")\nsurface_material_override/0 = SubResource("lamp_green")\ncast_shadow = 0\n')
for tag, z, turn, oz in (("Near", 34.2, "Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1,", 0.19), ("Far", 54.1, "Transform3D(-1, 0, 0, 0, 1, 0, 0, 0, -1,", -0.19)):
    y = D.PLAZA_Y - D.ROAD_Y
    for sign_name, mat in (("Hand", "sign_hand"), ("Walk", "sign_walk")):
        n.append(f'[node name="{sign_name}{tag}" type="MeshInstance3D" parent="Traffic"]\ntransform = {turn} -6.5, {y + 2.9}, {z + oz})\nmesh = SubResource("sign_quad")\nsurface_material_override/0 = SubResource("{mat}")\ncast_shadow = 0\n')

# The centre doors, on their hinges
STREET_RES += '[ext_resource type="Script" path="res://scripts/exterior_doors.gd" id="doors"]\n'
n.append(f'[node name="FrontDoors" type="Node3D" parent="."]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, {D.DOOR_Z})\nscript = ExtResource("doors")\nleft_hinge = NodePath("HingeL")\nright_hinge = NodePath("HingeR")\ngroan = NodePath("Groan")\n')
n.append(f'[node name="Groan" type="AudioStreamPlayer3D" parent="FrontDoors"]\nstream = ExtResource("snd_door_groan")\nvolume_db = -4.0\nunit_size = 7.0\nmax_distance = 60.0\n')
for tag, sx in (("L", -1), ("R", 1)):
    hx = sx * (D.DOOR_W / 2 + 0.1)
    n.append(f'[node name="Hinge{tag}" type="Node3D" parent="FrontDoors"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {hx}, 0, -0.1)\n')
    for part in ("door", "bronze"):
        STREET_RES += f'[ext_resource type="ArrayMesh" path="res://assets/exterior/meshes/door{tag.lower()}_ext_{part}.res" id="leaf_{tag}_{part}"]\n'
        n.append(f'[node name="{part}" type="MeshInstance3D" parent="FrontDoors/Hinge{tag}"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {-hx}, 0, {-D.DOOR_Z + 0.1})\nmesh = ExtResource("leaf_{tag}_{part}")\n')

# She will know: the owls' eyes, the librarian on her hinge, and the alarm's sounds
CREST = json.load(open(pathlib.Path(__file__).parent / "crest_spot.json"))
STREET_RES += '[ext_resource type="Script" path="res://scripts/exterior_alarm.gd" id="alarm"]\n'
STREET_RES += '[ext_resource type="ArrayMesh" path="res://assets/exterior/meshes/librarian_ext_carved.res" id="librarian"]\n'
STREET_SUBS += """[sub_resource type="SphereMesh" id="eye_ball"]
radius = 0.075
height = 0.15
radial_segments = 14
rings = 7

[sub_resource type="StandardMaterial3D" id="eye_glow"]
shading_mode = 0
albedo_color = Color(1, 0.3, 0.12, 1)
disable_receive_shadows = true

"""
n.append('[node name="Alarm" type="Node3D" parent="."]\nscript = ExtResource("alarm")\n')
n.append('[node name="OwlEyes" type="Node3D" parent="Alarm"]\n')
eye_y = D.ARCH_CROWN_Y + 0.10 + 0.90
for i, cx in enumerate(D.ARCHES_X):
    for tag, sx in (("L", -1), ("R", 1)):
        n.append(f'[node name="Eye{i}{tag}" type="MeshInstance3D" parent="Alarm/OwlEyes"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {cx + sx * 0.175}, {eye_y}, {D.WALL_Z + 1.02})\nmesh = SubResource("eye_ball")\nsurface_material_override/0 = SubResource("eye_glow")\ncast_shadow = 0\n')
n.append(f'[node name="Librarian" type="Node3D" parent="Alarm"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {CREST["x"]}, {CREST["y"]}, {CREST["z"]})\n')
n.append('[node name="Head" type="MeshInstance3D" parent="Alarm/Librarian"]\nmesh = ExtResource("librarian")\n')
for tag, sx in (("L", -1), ("R", 1)):
    n.append(f'[node name="Eye{tag}" type="MeshInstance3D" parent="Alarm/Librarian"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx * 0.125}, 1.04, 0.66)\nmesh = SubResource("eye_ball")\nsurface_material_override/0 = SubResource("eye_glow")\ncast_shadow = 0\n')
n.append('[node name="Whisper" type="AudioStreamPlayer" parent="Alarm"]\nstream = ExtResource("snd_she_knows")\nvolume_db = -2.0\n')
n.append('[node name="Bell" type="AudioStreamPlayer3D" parent="Alarm"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 6, 10)\nstream = ExtResource("snd_alarm_bell")\nvolume_db = -9.0\nunit_size = 20.0\nmax_distance = 220.0\n')
n.append('[node name="Siren" type="AudioStreamPlayer3D" parent="Alarm"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 150, 8, 48)\nstream = ExtResource("snd_siren_far")\nvolume_db = -6.0\nunit_size = 60.0\nmax_distance = 420.0\n')

# Flags on the two tall poles
n.append('[node name="Flags" type="Node3D" parent="."]\n')
for sx, tag in ((-1, "West"), (1, "East")):
    x = sx * 27.0 + 1.72
    n.append(f'[node name="{tag}" type="MeshInstance3D" parent="Flags"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x}, 14.3, 19)\nmesh = SubResource("flag_cloth")\nmaterial_override = SubResource("flag_look")\ncast_shadow = 0\n')

# Steam from two manholes and from the cart's grill
n.append('[node name="Steam" type="Node3D" parent="Life"]\n')
for tag, (x, y, z) in (("HoleA", (-48.0, D.ROAD_Y + 0.05, 42.2)), ("HoleB", (66.0, D.ROAD_Y + 0.05, 49.6))):
    n.append(f'[node name="{tag}" type="GPUParticles3D" parent="Life/Steam"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x}, {y}, {z})\namount = 24\nlifetime = 5.0\npreprocess = 5.0\nvisibility_aabb = AABB(-6, 0, -6, 12, 14, 12)\nprocess_material = SubResource("steam_motion")\ndraw_pass_1 = SubResource("steam_puff")\nmaterial_override = SubResource("steam_look")\ncast_shadow = 0\n')
n.append(f'[node name="Cart" type="GPUParticles3D" parent="Life/Steam"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 18.55, {D.PLAZA_Y + 1.5}, 32.6)\namount = 10\nlifetime = 2.5\npreprocess = 2.5\nvisibility_aabb = AABB(-2, 0, -2, 4, 4, 4)\nprocess_material = SubResource("cart_motion")\ndraw_pass_1 = SubResource("steam_puff")\nmaterial_override = SubResource("steam_look")\ncast_shadow = 0\n')

# The soundscape
n.append('[node name="Sound" type="Node3D" parent="Life"]\n')
n.append('[node name="City" type="AudioStreamPlayer" parent="Life/Sound"]\nstream = ExtResource("snd_amb_city")\nvolume_db = -9.0\nautoplay = true\n')
for sx, tag in ((-1, "West"), (1, "East")):
    n.append(f'[node name="Fountain{tag}" type="AudioStreamPlayer3D" parent="Life/Sound"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {sx * D.FOUNTAIN_X}, {D.PLAZA_Y + 1}, {D.FOUNTAIN_Z})\nstream = ExtResource("snd_amb_fountain")\nvolume_db = -3.0\nunit_size = 9.0\nmax_distance = 85.0\nautoplay = true\n')
n.append(f'[node name="Crickets" type="AudioStreamPlayer3D" parent="Life/Sound"]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, {D.PLAZA_Y + 1}, -210)\nstream = ExtResource("snd_amb_crickets")\nvolume_db = -6.0\nunit_size = 60.0\nmax_distance = 190.0\nautoplay = true\n')
n.append('[node name="PigeonFlap" type="AudioStreamPlayer3D" parent="Life/Sound"]\nstream = ExtResource("snd_pigeons_flap")\nunit_size = 10.0\nmax_distance = 80.0\n')
n.append('[node name="PigeonCoo" type="AudioStreamPlayer3D" parent="Life/Sound"]\nstream = ExtResource("snd_pigeon_coo")\nvolume_db = -6.0\nunit_size = 5.0\nmax_distance = 34.0\n')
