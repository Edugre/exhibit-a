"""Writes the finished exterior into the repo: textures, import settings, shared materials, collision and
scenes. usage: python gen_front.py <capital dir> <front dir> <ornament dir> <trim dir> <relief dir> <art dir>"""
import json
import random
import math
import pathlib
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ext_dims as D
SOUNDS = ["amb_city", "amb_fountain", "amb_crickets", "pigeons_flap", "pigeon_coo", "car_horn", "car_engine", "door_groan", "she_knows", "alarm_bell", "siren_far"]

WT = pathlib.Path(__file__).resolve().parent
for up in (WT, *WT.parents):
    if (up / "project.godot").exists():
        WT = up
        break
else:
    WT = pathlib.Path(r"C:\Users\waism\Downloads\exhibit-a\.claude\worktrees\agitated-benz-0e18d0")
A = WT / "assets" / "exterior"
CAP, FRONT, ORN, TRIM, RELIEF, ART = (pathlib.Path(p) for p in sys.argv[1:7])
SITE = json.load(open(pathlib.Path(__file__).parent / "site.json"))
RES = "res://assets/exterior/"


# --- Textures ---------------------------------------------------------------------------------
def atlas(cap, parts, fill):
    """Capital in the lower three quarters; four ornaments side by side above it."""
    a = Image.new("RGB", (2048, 2048), fill)
    a.paste(Image.open(cap).convert("RGB").resize((2048, 1536), Image.LANCZOS), (0, 512))
    for i, p in enumerate(parts):
        a.paste(Image.open(p).convert("RGB").resize((512, 512), Image.LANCZOS), (i * 512, 0))
    return a


names = ("modillion", "keystone", "mask_athena", "mask_shush")
atlas(CAP / "cap_normal.png", [ORN / f"{n}_normal.png" for n in names], (128, 128, 255)).save(A / "ext_carved_normal.png", optimize=True)
wide = atlas(CAP / "cap_ao_wide.png", [ORN / f"{n}_ao_wide.png" for n in names], (255, 255, 255)).convert("L")
tight = atlas(CAP / "cap_ao_tight.png", [ORN / f"{n}_ao_tight.png" for n in names], (255, 255, 255)).convert("L")
Image.merge("RGB", (wide, tight, Image.new("L", (2048, 2048), 0))).save(A / "ext_carved_ao.png", optimize=True)
for src, name in ((TRIM, "ext_trim_normal"), (TRIM, "ext_trim_ao"), (RELIEF, "ext_relief_normal"), (RELIEF, "ext_relief_ao"), (RELIEF, "ext_door_normal"), (RELIEF, "ext_door_ao"), (ART, "ext_banners"), (ART, "ext_banner_stolen"), (ART, "ext_stain"), (ART, "ext_props"), (ART, "ext_props_glow")):
    shutil.copy(src / f"{name}.png", A / f"{name}.png")

# The window's star lattice as a light pattern, thrown across the terrace by a single cheap light
S = 2048
cookie = Image.new("L", (S, S), 0)
d = ImageDraw.Draw(cookie)
d.ellipse([80, 80, S - 80, S - 80], fill=255)
p = S / 6.4
for i in range(-8, 9):
    for j in range(-8, 9):
        x, y = S / 2 + i * p, S / 2 + j * p
        h = p / 2
        for a0, b0 in (((x - h, y), (x + h, y)), ((x, y - h), (x, y + h)), ((x - h, y - h), (x + h, y + h)), ((x - h, y + h), (x + h, y - h))):
            d.line([a0, b0], fill=0, width=30)
for x in (S / 2 - 248, S / 2 + 248):
    d.rectangle([x - 60, 0, x + 60, S], fill=0)
# Light through old glass has soft edges, and drawn lines need smoothing before they are this large
cookie = cookie.resize((512, 512), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
cookie.convert("RGBA").save(A / "ext_lattice_cookie.png", optimize=True)


def tex_import(name, normal=False, lossless=False):
    (A / f"{name}.png.import").write_text(f"""[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="{RES}{name}.png"

[params]

compress/mode={0 if lossless else 2}
compress/high_quality={'true' if normal else 'false'}
compress/lossy_quality=0.7
compress/normal_map={'1' if normal else '0'}
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
process/fix_alpha_border=false
process/size_limit=0
detect_3d/compress_to=0
""", encoding="utf-8", newline="\n")


for n, is_n in (("ext_stone_albedo", False), ("ext_stone_normal", True), ("ext_stone_rough", False), ("ext_carved_normal", True), ("ext_carved_ao", False),
                ("ext_trim_normal", True), ("ext_trim_ao", False), ("ext_relief_normal", True), ("ext_relief_ao", False), ("ext_banners", False), ("ext_stain", False)):
    tex_import(n, is_n)
tex_import("ext_lattice_cookie", lossless=True)
tex_import("ext_door_normal", normal=True)
tex_import("ext_door_ao")
tex_import("ext_banner_stolen")
tex_import("ext_baked_light")
tex_import("ext_props")
tex_import("ext_props_glow")
for sound in SOUNDS:
    shutil.copy(ART / f"{sound}.wav", A / f"{sound}.wav")
    loops = sound.startswith("amb_") or sound in ("car_engine", "alarm_bell", "siren_far")
    (A / f"{sound}.wav.import").write_text(f"""[remap]

importer="wav"
type="AudioStreamWAV"

[deps]

source_file="{RES}{sound}.wav"

[params]

force/8_bit=false
force/mono=false
force/max_rate=false
force/max_rate_hz=44100
edit/trim=false
edit/normalize=false
edit/loop_mode={2 if loops else 0}
edit/loop_begin=0
edit/loop_end=-1
compress/mode=2
""", encoding="utf-8", newline=chr(10))

# --- Models -----------------------------------------------------------------------------------
shutil.copy(CAP / "capital.glb", A / "capital.glb")
shutil.copy(FRONT / "front.glb", A / "front.glb")
shutil.copy(FRONT / "wings.glb", A / "wings.glb")
shutil.copy(FRONT / "doors.glb", A / "doors.glb")
MATS = ["ext_shaft", "ext_ashlar", "ext_stone", "ext_granite", "ext_riser", "ext_rough", "ext_trim", "ext_bronze", "ext_glass", "ext_paving", "ext_carved",
        "ext_relief", "ext_door", "ext_banner", "ext_lantern", "ext_rail", "ext_wing_wall", "ext_wing_trim", "ext_wing_glass"]


def glb_import(name, mats):
    if not isinstance(mats, dict):
        mats = {m: m for m in mats}
    sub = {"materials": {k: {"use_external/enabled": True, "use_external/path": f"{RES}{m}.tres"} for k, m in mats.items()}}
    (A / f"{name}.glb.import").write_text(f"""[remap]

importer="scene"
importer_version=1
type="PackedScene"

[deps]

source_file="{RES}{name}.glb"

[params]

nodes/root_type=""
nodes/root_name=""
nodes/root_script=null
meshes/ensure_tangents=true
meshes/generate_lods=true
meshes/create_shadow_meshes=true
meshes/light_baking=1
meshes/lightmap_texel_size=0.2
meshes/force_disable_compression=false
_subresources={json.dumps(sub)}
gltf/naming_version=2
gltf/embedded_image_handling=1
gltf/texture_map_mode=1
""", encoding="utf-8", newline="\n")


glb_import("capital", ["ext_carved"])
glb_import("front", MATS)
glb_import("wings", MATS)
glb_import("doors", MATS)
glb_import("exterior_context", {"BO_Stone": "ext_context", "BO_StoneDark": "ext_context_dark", "BO_Paving": "ext_plaza", "BO_City": "ext_city", "BO_Lamp": "ext_lantern", "BO_Road": "ext_road", "BO_Line": "ext_road_line", "BO_Water": "ext_water"})
shutil.copy(FRONT / "trees.glb", A / "trees.glb")
shutil.copy(FRONT / "props.glb", A / "props.glb")
shutil.copy(FRONT / "cars.glb", A / "cars.glb")
glb_import("props", {"ext_props": "ext_props"})
glb_import("cars", {"ext_props": "ext_props"})
glb_import("trees", {"ext_bark": "ext_bark", "ext_leaf": "ext_leaf"})
shutil.copy(FRONT / "pigeon.glb", A / "pigeon.glb")
shutil.copy(FRONT / "fountain_jets.glb", A / "fountain_jets.glb")
glb_import("fountain_jets", {"ext_jet": "ext_jet"})


# --- Materials --------------------------------------------------------------------------------
def stone_mat(name, stain=False, star=False, **params):
    tex = {"stone_albedo": "ext_stone_albedo.png", "stone_normal": "ext_stone_normal.png", "stone_rough": "ext_stone_rough.png"}
    if stain:
        tex["stain_map"] = "ext_stain.png"
        tex["baked_light"] = "ext_baked_light.png"
        params["stain_amount"] = 1.0
        params["baked_strength"] = 4.0
    if star:
        tex["star_map"] = "ext_lattice_cookie.png"
        params["star_strength"] = 0.5
    lines = ['[gd_resource type="ShaderMaterial" format=3]\n', f'[ext_resource type="Shader" path="{RES}ext_stone.gdshader" id="s"]']
    for i, v in enumerate(tex.values()):
        lines.append(f'[ext_resource type="Texture2D" path="{RES}{v}" id="t{i}"]')
    lines.append('\n[resource]\nshader = ExtResource("s")')
    for i, k in enumerate(tex):
        lines.append(f'shader_parameter/{k} = ExtResource("t{i}")')
    for k, v in params.items():
        lines.append(f"shader_parameter/{k} = {v}")
    (A / f"{name}.tres").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def carved_mat(name, normal, ao):
    (A / f"{name}.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_carved.gdshader" id="s"]
[ext_resource type="Texture2D" path="{RES}ext_stone_albedo.png" id="t0"]
[ext_resource type="Texture2D" path="{RES}ext_stone_rough.png" id="t1"]
[ext_resource type="Texture2D" path="{RES}{normal}" id="t2"]
[ext_resource type="Texture2D" path="{RES}{ao}" id="t3"]
[ext_resource type="Texture2D" path="{RES}ext_stain.png" id="t4"]
[ext_resource type="Texture2D" path="{RES}ext_baked_light.png" id="t5"]

[resource]
shader = ExtResource("s")
shader_parameter/stone_albedo = ExtResource("t0")
shader_parameter/stone_rough = ExtResource("t1")
shader_parameter/carved_normal = ExtResource("t2")
shader_parameter/carved_ao = ExtResource("t3")
shader_parameter/stain_map = ExtResource("t4")
shader_parameter/stain_amount = 1.0
shader_parameter/baked_light = ExtResource("t5")
shader_parameter/baked_strength = 4.0
""", encoding="utf-8", newline="\n")


stone_mat("ext_stone", stain=True)
stone_mat("ext_shaft", stain=True, joints="true", course_height=2.37, block_length=400.0, joint_width=0.007, block_tone=0.06)
stone_mat("ext_ashlar", stain=True, joints="true", course_height=0.74, block_length=2.46, joint_width=0.010, block_tone=0.05)
stone_mat("ext_rough", stain=True, tint="Vector3(0.86, 0.84, 0.8)", normal_strength=3.0, metres_per_tile=2.6, roughness_add=0.05)
stone_mat("ext_granite", star=True, tint="Vector3(0.42, 0.415, 0.41)", metres_per_tile=1.4, normal_strength=0.7, roughness_add=-0.10)
stone_mat("ext_riser", star=True, tint="Vector3(0.36, 0.355, 0.35)", metres_per_tile=1.4, normal_strength=0.7, roughness_add=-0.05)
stone_mat("ext_paving", star=True, tint="Vector3(0.62, 0.61, 0.6)", metres_per_tile=3.2, roughness_add=-0.08)
stone_mat("ext_context", tint="Vector3(0.72, 0.71, 0.69)", grime=0.3, grime_top=18.0, grime_length=14.0)
stone_mat("ext_wing_wall", joints="true", course_height=0.74, block_length=2.46, joint_width=0.010, block_tone=0.05, grime=0.34, grime_top=12.0, grime_length=9.0)
stone_mat("ext_wing_trim", grime=0.24, grime_top=19.0, grime_length=16.0)
stone_mat("ext_context_dark", tint="Vector3(0.5, 0.5, 0.5)")
carved_mat("ext_carved", "ext_carved_normal.png", "ext_carved_ao.png")
carved_mat("ext_trim", "ext_trim_normal.png", "ext_trim_ao.png")
carved_mat("ext_relief", "ext_relief_normal.png", "ext_relief_ao.png")

(A / "ext_door.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_bronze_relief.gdshader" id="s"]
[ext_resource type="Texture2D" path="{RES}ext_door_normal.png" id="t0"]
[ext_resource type="Texture2D" path="{RES}ext_door_ao.png" id="t1"]

[resource]
shader = ExtResource("s")
shader_parameter/relief_normal = ExtResource("t0")
shader_parameter/relief_ao = ExtResource("t1")
""", encoding="utf-8", newline="\n")
(A / "ext_banner.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_banner.gdshader" id="s"]
[ext_resource type="Texture2D" path="{RES}ext_banners.png" id="t0"]
[ext_resource type="Texture2D" path="{RES}ext_banner_stolen.png" id="t1"]

[resource]
shader = ExtResource("s")
shader_parameter/print = ExtResource("t0")
shader_parameter/print_stolen = ExtResource("t1")
""", encoding="utf-8", newline="\n")
for road_name, painted in (("ext_road", "false"), ("ext_road_line", "true")):
    (A / f"{road_name}.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_road.gdshader" id="s"]

[resource]
shader = ExtResource("s")
shader_parameter/painted = {painted}
""", encoding="utf-8", newline=chr(10))
(A / "ext_water.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_water.gdshader" id="s"]

[resource]
shader = ExtResource("s")
""", encoding="utf-8", newline=chr(10))
(A / "ext_jet.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_jet.gdshader" id="s"]

[resource]
shader = ExtResource("s")
""", encoding="utf-8", newline=chr(10))
(A / "ext_plaza.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_plaza.gdshader" id="s"]
[ext_resource type="Texture2D" path="{RES}ext_stone_albedo.png" id="t0"]
[ext_resource type="Texture2D" path="{RES}ext_lattice_cookie.png" id="t1"]

[resource]
shader = ExtResource("s")
shader_parameter/stone_albedo = ExtResource("t0")
shader_parameter/star_map = ExtResource("t1")
shader_parameter/star_strength = 0.5
""", encoding="utf-8", newline=chr(10))
(A / "ext_leaf.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_leaf.gdshader" id="s"]

[resource]
shader = ExtResource("s")
""", encoding="utf-8", newline=chr(10))
(A / "ext_bark.tres").write_text("""[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.135, 0.115, 0.1, 1)
roughness = 0.9
""", encoding="utf-8", newline=chr(10))
(A / "ext_city.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_city.gdshader" id="s"]

[resource]
shader = ExtResource("s")
""", encoding="utf-8", newline=chr(10))
for bronze_name in ("ext_bronze", "ext_rail"):
    (A / f"{bronze_name}.tres").write_text("""[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.22, 0.165, 0.115, 1)
metallic = 0.6
roughness = 0.44
""", encoding="utf-8", newline="\n")
(A / "ext_wing_glass.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_night_glass.gdshader" id="s"]

[resource]
shader = ExtResource("s")
""", encoding="utf-8", newline=chr(10))
(A / "ext_props.tres").write_text(f"""[gd_resource type="StandardMaterial3D" format=3]

[ext_resource type="Texture2D" path="{RES}ext_props.png" id="t0"]
[ext_resource type="Texture2D" path="{RES}ext_props_glow.png" id="t1"]

[resource]
albedo_texture = ExtResource("t0")
roughness = 0.62
metallic_specular = 0.35
emission_enabled = true
emission_energy_multiplier = 1.7
emission_texture = ExtResource("t1")
""", encoding="utf-8", newline=chr(10))
(A / "ext_glass.tres").write_text("""[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.03, 0.035, 0.05, 1)
roughness = 0.25
metallic_specular = 0.6
emission_enabled = true
emission = Color(1, 0.7, 0.42, 1)
emission_energy_multiplier = 0.11
cull_mode = 2
""", encoding="utf-8", newline="\n")
(A / "ext_lantern.tres").write_text("""[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(1, 0.78, 0.5, 1)
roughness = 0.4
emission_enabled = true
emission = Color(1, 0.72, 0.42, 1)
emission_energy_multiplier = 3.4
""", encoding="utf-8", newline="\n")

# --- Collision --------------------------------------------------------------------------------
subs, cnodes = [], []


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def add_shape(kind, body, node_name, pos=(0, 0, 0)):
    sid = f"Shape_{len(subs)}"
    subs.append(f'[sub_resource type="{kind[0]}" id="{sid}"]\n{kind[1]}\n')
    cnodes.append(f'[node name="{node_name}" type="CollisionShape3D" parent="{body}"]\n'
                  f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {fmt(pos[0])}, {fmt(pos[1])}, {fmt(pos[2])})\nshape = SubResource("{sid}")\n')


def box(body, name, x0, x1, y0, y1, z0, z1):
    add_shape(("BoxShape3D", f"size = Vector3({fmt(x1 - x0)}, {fmt(y1 - y0)}, {fmt(z1 - z0)})"), body, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(body, name, x, z, y0, y1, r):
    add_shape(("CylinderShape3D", f"height = {fmt(y1 - y0)}\nradius = {fmt(r)}"), body, name, (x, (y0 + y1) / 2, z))


def wedge(body, name, x0, x1, y_low, y_a, y_b, z_a, z_b):
    pts = []
    for x in (x0, x1):
        pts += [x, y_low, z_a, x, y_a, z_a, x, y_b, z_b, x, y_low, z_b]
    add_shape(("ConvexPolygonShape3D", "points = PackedVector3Array(" + ", ".join(fmt(p) for p in pts) + ")"), body, name)


G, B, P, E = "Collision/Ground", "Collision/Building", "Collision/Props", "Collision/Edges"
LOW = -5.5
box(G, "Paving", -260, 260, LOW, D.PLAZA_Y, D.BOUND_Z_N - 12, D.CURB_Z)
box(G, "Road", -260, 260, LOW, D.ROAD_Y, D.CURB_Z, D.ROAD_Z_END)
box(G, "FarWalk", -260, 260, LOW, D.PLAZA_Y, D.ROAD_Z_END, D.BOUND_Z_S + 6)
wedge(G, "CurbNear", -260, 260, D.ROAD_Y - 0.5, D.PLAZA_Y, D.ROAD_Y, D.CURB_Z, D.CURB_Z + 0.8)
wedge(G, "CurbFar", -260, 260, D.ROAD_Y - 0.5, D.ROAD_Y, D.PLAZA_Y, D.ROAD_Z_END - 0.8, D.ROAD_Z_END)
wedge(B, "StairRamp", -D.STAIR_X, D.STAIR_X, LOW, D.TERRACE_Y, D.PLAZA_Y, D.STAIR_Z_TOP, D.STAIR_Z_BOT)
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * D.STAIR_X, sx * (D.STAIR_X + D.CHEEK_W)))
    wedge(B, "StairWall" + name, x0, x1, LOW, D.CHEEK_H, D.PLAZA_Y + D.CHEEK_H, D.STAIR_Z_TOP, D.STAIR_Z_BOT)
box(B, "Terrace", -D.PAV_X, D.PAV_X, LOW, D.TERRACE_Y, 6.0, D.TERRACE_Z_FRONT)
# The wings' heavy base stands out from the plain walls
for sx, tag in ((-1, "W"), (1, "E")):
    a, b = sorted((sx * D.PAV_X, sx * D.MID_X))
    box(B, "WingBaseMid" + tag, a, b, LOW, 0.0, 6.0, D.MID_Z + 1.17)
    a, b = sorted((sx * (D.MID_X - 1.17), sx * D.END_X))
    box(B, "WingBaseEnd" + tag, a, b, LOW, 0.0, 6.0, D.END_Z + 1.17)
    a, b = sorted((sx * D.MID_X, sx * (D.END_X + 1.17)))
    box(B, "WingBaseSide" + tag, a, b, LOW, 0.0, -14.0, D.END_Z + 1.17)
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * (D.STAIR_X + D.CHEEK_W), sx * (D.PAV_X + 0.8)))
    box(B, "Base" + name, x0, x1, LOW, -0.0, D.TERRACE_Z_FRONT, D.TERRACE_Z_FRONT + 0.6)
    a, b = sorted((sx * D.PAV_X, sx * (D.PAV_X + 0.8)))
    box(B, "BaseSide" + name, a, b, LOW, 0.0, 6.8, D.TERRACE_Z_FRONT)
    box(B, "Railing" + name, x0, x1, 0, 1.2, D.TERRACE_Z_FRONT - 0.34, D.TERRACE_Z_FRONT - 0.22)
for i, px in enumerate(D.PAIRS_X):
    w = D.PED_W / 2 + 0.3
    box(B, f"Pedestal{i}", px - w, px + w, 0, D.PED_Y, D.PED_Z[0], D.PED_Z[1] + 0.3)
    box(B, f"ColumnPair{i}", px - 2.4, px + 2.4, D.PED_Y, D.COL_TOP_Y, D.COL_Z - 0.85, D.COL_Z + 0.85)
half = D.ARCH_W / 2
for i, cx in enumerate(D.ARCHES_X):
    if cx:
        box(B, f"ArchBack{i}", cx - half, cx + half, 0, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
    else:
        box(B, "ArchBackW", -half, -D.DOOR_W / 2, 0, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
        box(B, "ArchBackE", D.DOOR_W / 2, half, 0, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
        box(B, "OverDoor", -D.DOOR_W / 2, D.DOOR_W / 2, D.DOOR_H, D.COL_TOP_Y, 8.5, D.DOOR_Z + 0.2)
for i, (x0, x1) in enumerate(((-24.0, -17.8), (-10.2, -3.8), (3.8, 10.2), (17.8, 24.0))):
    box(B, f"Pier{i}", x0, x1, 0, D.COL_TOP_Y, 8.5, D.WALL_Z)
for sx, name in ((-1, "W"), (1, "E")):
    x0, x1 = sorted((sx * D.END_BAY_X, sx * D.PAV_X))
    box(B, "EndBay" + name, x0, x1, 0, D.COL_TOP_Y, 7.0, D.WALL_Z + 0.55)
    a, b = sorted((sx * D.DOOR_W / 2, sx * (D.DOOR_W / 2 + 0.5)))
    box(B, "Vestibule" + name, a, b, 0, 4.4, 6.0, 8.5)
box(B, "VestibuleCeiling", -2.0, 2.0, 4.0, 4.4, 6.0, 8.5)
# The real outline as one solid skin; the notch at the pavilion stays open for the doors
outline = []
for x, z in D.FOOTPRINT:
    outline.append((x, 5.9 if abs(x) < 31 and z > 6.5 and abs(abs(x) - 30.4) < 0.1 and z == 10.0 else z))
tris = []
top = D.WING_TOP_Y
for (ax, az), (bx, bz) in zip(outline, outline[1:] + outline[:1]):
    if max(abs(ax), abs(bx)) < 31 and min(az, bz) > 5.5:
        continue
    tris += [ax, LOW, az, bx, LOW, bz, bx, top, bz, ax, LOW, az, bx, top, bz, ax, top, az]
add_shape(("ConcavePolygonShape3D", "backface_collision = true\ndata = PackedVector3Array(" + ", ".join(fmt(v) for v in tris) + ")"), B, "Footprint")
for sx in (-1, 1):
    a, b = sorted((sx * D.PAV_X, sx * D.MID_X))
    box(B, "MidBase" + ("W" if sx < 0 else "E"), a, b, LOW, -3.9, D.MID_Z, D.MID_Z + 0.5)
    a, b = sorted((sx * D.MID_X, sx * D.END_X))
    box(B, "EndBase" + ("W" if sx < 0 else "E"), a, b, LOW, -3.9, D.END_Z, D.END_Z + 0.5)
box(B, "LoadingDock", -D.END_X - 4, -D.END_X, LOW, -3.2, -24.6, -16.0)
h = D.FOUNTAIN_SIZE / 2
for sx, tag in ((-1, "W"), (1, "E")):
    box(P, "Fountain" + tag, sx * D.FOUNTAIN_X - h, sx * D.FOUNTAIN_X + h, D.PLAZA_Y, D.PLAZA_Y + 0.32, D.FOUNTAIN_Z - h, D.FOUNTAIN_Z + h)
n = 0
for i, (x, z) in enumerate([(x, D.LAMP_Z) for x in D.LAMPS_X] + [(x, D.FAR_LAMP_Z) for x in D.FAR_LAMPS_X] + D.PATH_LAMPS):
    cyl(P, f"Lamp{i}", x, z, D.PLAZA_Y, D.PLAZA_Y + 4, 0.28)
for sx, tag in ((-1, "W"), (1, "E")):
    for x in (22.0, 64.0, 112.0):
        cyl(P, f"Bin{tag}{x:.0f}", sx * x, 33.9, D.PLAZA_Y, D.PLAZA_Y + 1, 0.34)
cyl(P, "HydrantW", -29.0, 34.2, D.PLAZA_Y, D.PLAZA_Y + 0.8, 0.17)
cyl(P, "HydrantE", 91.0, 34.2, D.PLAZA_Y, D.PLAZA_Y + 0.8, 0.17)
box(P, "NewsBoxes", -24.8, -23.2, D.PLAZA_Y, D.PLAZA_Y + 1.2, 33.65, 34.15)
box(P, "HoursBoard", -14.3, -13.3, D.PLAZA_Y, D.PLAZA_Y + 1.9, 25.5, 25.9)
box(P, "AmbrosiaCart", 17.9, 20.1, D.PLAZA_Y, D.PLAZA_Y + 1.6, 31.95, 33.25)
box(P, "ParkedTaxi", -22.5, -17.5, D.ROAD_Y, D.ROAD_Y + 1.5, 35.45, 37.3)
for i, (x, z) in enumerate(((-27.0, 19.0), (27.0, 19.0))):
    cyl(P, f"Flagpole{i}", x, z, D.PLAZA_Y, D.PLAZA_Y + 4, 0.5)
for i, (x, z) in enumerate(((-6.5, 34.2), (-6.5, 54.1), (7.6, 34.1), (7.6, 54.0))):
    cyl(P, f"StreetPole{i}", x, z, D.PLAZA_Y, D.PLAZA_Y + 4, 0.2)
for sx, tag in ((-1, "W"), (1, "E")):
    for x in (47.0, 86.0):
        box(P, f"Planter{tag}{x:.0f}", sx * x - 1.3, sx * x + 1.3, D.PLAZA_Y, D.PLAZA_Y + 1.0, 11.65, 12.75)
    for x in (56.0, 64.0, 72.0):
        box(P, f"Planter{tag}{x:.0f}", sx * x - 1.8, sx * x + 1.8, D.PLAZA_Y, D.PLAZA_Y + 1.0, 10.65, 11.75)
    for x in (52.0, 60.0, 68.0, 76.0, 84.0):
        box(P, f"PlazaBench{tag}{x:.0f}", sx * x - 1.2, sx * x + 1.2, D.PLAZA_Y, D.PLAZA_Y + 0.5, 24.3, 24.9)
    box(P, f"FountainSign{tag}", sx * D.FOUNTAIN_X - 0.1, sx * D.FOUNTAIN_X + 0.1, D.PLAZA_Y, D.PLAZA_Y + 2, 29.0, 29.3)
for x, z in SITE["trees"]:
    if abs(x) <= 160 and z < 36:
        cyl(P, f"Tree{n}", x, z, D.PLAZA_Y, D.PLAZA_Y + 5, 0.3)
        n += 1
for i, (x, z) in enumerate(SITE["benches"]):
    if z > 0:
        box(P, f"Bench{i}", x - 1.1, x + 1.1, D.PLAZA_Y, D.PLAZA_Y + 0.48, z - 0.35, z + 0.35)
nx_, nz_ = SITE["needle"]
box(P, "Needle", nx_ - 3.2, nx_ + 3.2, D.PLAZA_Y, D.PLAZA_Y + 24, nz_ - 3.2, nz_ + 3.2)
box(E, "West", -D.BOUND_X - 1, -D.BOUND_X, LOW, 12, D.BOUND_Z_N, D.BOUND_Z_S)
box(E, "East", D.BOUND_X, D.BOUND_X + 1, LOW, 12, D.BOUND_Z_N, D.BOUND_Z_S)
box(E, "North", -D.BOUND_X, D.BOUND_X, LOW, 12, D.BOUND_Z_N - 1, D.BOUND_Z_N)
box(E, "South", -D.BOUND_X, D.BOUND_X, LOW, 12, D.BOUND_Z_S, D.BOUND_Z_S + 1)

# --- Lights -----------------------------------------------------------------------------------
LIGHTS = []
WARM = [1.0, 0.77, 0.52]
for i, px in enumerate(D.PAIRS_X):
    LIGHTS.append(dict(name=f"Graze{i}", pos=[px, 3.35, 14.5], target=[px, 19.5, 11.7], energy=5.0, angle=36, range=28, soft=1.4, atten=0.3, color=WARM, shadow=True))
for i, cx in enumerate(D.ARCHES_X):
    LIGHTS.append(dict(name=f"ArchGraze{i}", pos=[cx, 0.25, 11.6], target=[cx, 17.0, 9.0], energy=2.6, angle=46, range=26, soft=1.8, atten=0.4, color=[1.0, 0.79, 0.55], shadow=True))
    if cx != 0:
        continue    # Godot only projects the star from a light with shadows, so the centre arch alone throws it
    LIGHTS.append(dict(name=f"WindowStar{i}", pos=[cx, 15.2, 9.75], target=[cx, 0.0, 17.5], energy=8.0 if cx == 0 else 5.0, angle=27, range=30, soft=1.0, atten=0.2, color=[1.0, 0.74, 0.46], shadow=cx == 0, projector=True))
    LIGHTS.append(dict(name=f"DoorLamp{i}", omni=True, pos=[cx, 3.5, 9.8], target=[0, 0, 0], energy=1.35, range=10, color=[1.0, 0.82, 0.64], shadow=False))
for i, (fx, tx) in enumerate(((-24.0, -21.0), (-10.0, -7.0), (10.0, 7.0), (24.0, 21.0))):
    LIGHTS.append(dict(name=f"Flood{i}", pos=[fx, 4.2, 33.0], target=[tx, 12.0, 11.0], energy=6.5, angle=30, range=60, soft=3.8, atten=0.6, color=[1.0, 0.80, 0.58], shadow=True))
for i, sx in enumerate((-1, 1)):
    LIGHTS.append(dict(name=f"EndBay{i}", pos=[sx * 27.2, 0.3, 16.2], target=[sx * 27.2, 15.0, 10.6], energy=3.4, angle=34, range=24, soft=2.0, atten=0.4, color=WARM, shadow=False))
    LIGHTS.append(dict(name=f"Crest{i}", pos=[sx * 16.0, 7.0, 57.0], target=[sx * 11.0, 27.0, 10.0], energy=11, angle=24, range=85, soft=2.6, atten=0.5, color=[1.0, 0.8, 0.58], shadow=False))
    LIGHTS.append(dict(name=f"Stairs{i}", pos=[sx * 19.0, 2.5, 33.0], target=[sx * 2.0, -3.0, 20.0], energy=4.0, angle=40, range=34, soft=1.6, atten=0.7, color=[1.0, 0.8, 0.6], shadow=False))
    LIGHTS.append(dict(name=f"Lantern{i}", omni=True, pos=[sx * 3.82, 2.4, 12.2], target=[0, 0, 0], energy=0.9, range=8, color=[1.0, 0.72, 0.42], shadow=False))
for i, (x, z) in enumerate([(x, D.LAMP_Z) for x in D.LAMPS_X] + [(x, D.FAR_LAMP_Z) for x in D.FAR_LAMPS_X] + D.PATH_LAMPS):
    LIGHTS.append(dict(name=f"Lamp{i}", pos=[x, D.LAMP_TOP_Y - 0.1, z], target=[x + 0.01, D.PLAZA_Y, z], energy=15.0, angle=70, range=24, soft=1.3, atten=1.0, color=[1.0, 0.76, 0.5], shadow=False))
# A low wash along the wings, so the length of the front can be read at night
wash = [(x, 6.8, 15.0) for x in (46.0, 67.0, 84.0)] + [(x, 18.6, 25.5) for x in (100.0, 120.0, 140.0)]
for i, (x, wall, z) in enumerate(wash):
    for sx in (-1, 1):
        LIGHTS.append(dict(name=f"WingWash{i}{'W' if sx < 0 else 'E'}", pos=[sx * x, -3.7, z], target=[sx * x, 9.0, wall], energy=3.0, angle=48, range=30, soft=2.0, atten=0.7, color=[1.0, 0.8, 0.6], shadow=False))
for sx, tag in ((-1, "W"), (1, "E")):
    LIGHTS.append(dict(name=f"FountainGlow{tag}", omni=True, pos=[sx * D.FOUNTAIN_X, D.PLAZA_Y + 1.4, D.FOUNTAIN_Z], target=[0, 0, 0], energy=1.6, range=11, color=[1.0, 0.86, 0.68], shadow=False))
LIGHTS.append(dict(name="CurbSpill", pos=[-13.0, 7.0, 25.0], target=[-13.0, D.ROAD_Y, 37.0], energy=8.0, angle=40, range=34, soft=2.0, atten=0.8, color=[1.0, 0.82, 0.62], shadow=False))
LIGHTS.append(dict(name="PassageLamp", omni=True, pos=[0.0, 3.3, 7.0], target=[0, 0, 0], energy=0.9, range=8, color=[1.0, 0.8, 0.58], shadow=False))
LIGHTS.append(dict(name="CartGlow", omni=True, pos=[19.1, D.PLAZA_Y + 2.1, 32.6], target=[0, 0, 0], energy=1.3, range=8, color=[1.0, 0.78, 0.5], shadow=False))
LIGHTS.append(dict(name="TerraceBounce", omni=True, pos=[0.0, 1.2, 13.0], target=[0, 0, 0], energy=0.5, range=15, color=[1.0, 0.76, 0.52], shadow=False))


# --- Scenes -----------------------------------------------------------------------------------
def T(x, y, z):
    return f"Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x:g}, {y:g}, {z:g})"


CAP_Y = D.COL_TOP_Y - 1.92
nodes = ['[node name="Exterior" type="Node3D"]\n', '[node name="Context" parent="." instance=ExtResource("context")]\n',
         '[node name="Front" parent="." instance=ExtResource("front")]\n',
         '[node name="Front_ext_rail" parent="Front" index="0"]\ncast_shadow = 0\n',
         '[node name="Wings" parent="." instance=ExtResource("wings")]\n',
         '[node name="Props" parent="." instance=ExtResource("props")]\n', '[node name="Capitals" type="Node3D" parent="."]\n']
k = 0
for px in D.PAIRS_X:
    for sx in (-1, 1):
        x = px + sx * D.PAIR_GAP
        nodes.append(f'[node name="Capital{k}" parent="Capitals" instance=ExtResource("capital")]\ntransform = {T(x, CAP_Y, D.COL_Z)}\n')
        nodes.append(f'[node name="Capital{k + 1}" parent="Capitals" instance=ExtResource("capital")]\ntransform = {T(x, CAP_Y, D.WALL_Z + 0.34)}\n')
        k += 2
nodes.append('[node name="Lights" type="Node3D" parent="."]\n')


def tree_spots():
    """The real trees, plus wild park trees that grow thicker beyond the path."""
    out = [(x, z) for x, z in SITE["trees"] if abs(x) <= 160 and -300 < z < 36]
    for i in range(16):
        for j in range(4):
            x = -176 + i * 23.5 + (j % 2) * 9
            z = -186 - j * 16 - (i % 3) * 3
            if math.hypot(x - SITE["needle"][0], z - SITE["needle"][1]) > 22:
                out.append((x, z))
    return out


# Trees are drawn in batches by area, so a whole batch out of view costs nothing
batches = {}
tree_rng = random.Random(4)
for x, z in tree_spots():
    area = "Park" if z < 10 else ("West" if x < 0 else "East")
    kind = tree_rng.randrange(3)
    a, scale = tree_rng.uniform(0, math.tau), tree_rng.uniform(0.92, 1.18)
    c, s = math.cos(a) * scale, math.sin(a) * scale
    batches.setdefault((area, kind), []).extend([c, 0.0, s, x, 0.0, scale, 0.0, D.PLAZA_Y, -s, 0.0, c, z])
exec(open(pathlib.Path(__file__).parent / "gen_street.py", encoding="utf-8").read())
TREE_RES, TREE_SUBS, TREE_NODES = "", "", []
for k in range(3):
    TREE_RES += f'[ext_resource type="ArrayMesh" path="res://assets/exterior/meshes/tree{k}_bark.res" id="tree{k}b"]\n'
    TREE_RES += f'[ext_resource type="ArrayMesh" path="res://assets/exterior/meshes/tree{k}_leaves.res" id="tree{k}l"]\n'
TREE_RES += '[ext_resource type="Material" path="res://assets/exterior/ext_leaf.tres" id="leaf_mat"]\n[ext_resource type="Material" path="res://assets/exterior/ext_bark.tres" id="bark_mat"]\n'
for (area, k), buf in sorted(batches.items()):
    n = len(buf) // 12
    data = ", ".join(f"{v:.4f}" for v in buf)
    for part, tag, mat in (("b", "Bark", "bark_mat"), ("l", "Leaves", "leaf_mat")):
        sid = f"trees_{area}_{k}_{part}"
        TREE_SUBS += f'[sub_resource type="MultiMesh" id="{sid}"]\ntransform_format = 1\ninstance_count = {n}\nmesh = ExtResource("tree{k}{part}")\nbuffer = PackedFloat32Array({data})\n\n'
        TREE_NODES.append(f'[node name="{area}{k}{tag}" type="MultiMeshInstance3D" parent="Trees"]\nmaterial_override = ExtResource("{mat}")\ncast_shadow = 0\nmultimesh = SubResource("{sid}")\n')
for l in LIGHTS:
    px, py, pz = l["pos"]
    tx, ty, tz = l["target"]
    c = l["color"]
    shadow = "true" if l.get("shadow") else "false"
    if l.get("omni"):
        nodes.append(f'[node name="{l["name"]}" type="OmniLight3D" parent="Lights"]\ntransform = {T(px, py, pz)}\n'
                     f'light_color = Color({c[0]}, {c[1]}, {c[2]}, 1)\nlight_energy = {l["energy"]}\nomni_range = {l["range"]}\nomni_attenuation = 1.2\nshadow_enabled = {shadow}\nlight_specular = 0.2\n')
        continue
    f = np.array([tx - px, ty - py, tz - pz], dtype=float)
    f /= np.linalg.norm(f)
    z = -f
    up = np.array([0.0, 1.0, 0.0]) if abs(f[1]) < 0.99 else np.array([0.0, 0.0, 1.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    basis = f"{x[0]:.5f}, {y[0]:.5f}, {z[0]:.5f}, {x[1]:.5f}, {y[1]:.5f}, {z[1]:.5f}, {x[2]:.5f}, {y[2]:.5f}, {z[2]:.5f}"
    extra = 'light_projector = ExtResource("cookie")\n' if l.get("projector") else ""
    nodes.append(f'[node name="{l["name"]}" type="SpotLight3D" parent="Lights"]\ntransform = Transform3D({basis}, {px:g}, {py:g}, {pz:g})\n'
                 f'light_color = Color({c[0]}, {c[1]}, {c[2]}, 1)\nlight_energy = {l["energy"]}\n{extra}spot_range = {l["range"]}\nspot_angle = {l["angle"]}\n'
                 f'spot_angle_attenuation = {l.get("soft", 0.7)}\nspot_attenuation = {l.get("atten", 0.9)}\nshadow_enabled = {shadow}\nshadow_blur = 1.2\nlight_specular = 0.25\n')
# Moths round every warm light near the doors
nodes.append('[node name="Life" type="Node3D" parent="."]\n')
for i, (x, y, z) in enumerate([(-4.45, 3.4, 12.2), (4.45, 3.4, 12.2), (-7.0, 4.0, 14.4), (7.0, 4.0, 14.4), (-21.0, 4.0, 14.4), (21.0, 4.0, 14.4)]):
    nodes.append(f'[node name="Moths{i}" type="GPUParticles3D" parent="Life"]\ntransform = {T(x, y, z)}\namount = 22\nlifetime = 6.0\npreprocess = 6.0\nrandomness = 0.5\n'
                 'visibility_aabb = AABB(-4, -4, -4, 8, 8, 8)\nprocess_material = SubResource("moth_motion")\ndraw_pass_1 = SubResource("moth_quad")\n')
PERCHES = []
for px in D.PAIRS_X:                                   # the tops of the pedestals, round the column bases
    PERCHES += [(px - 2.15, D.PED_Y, 13.2), (px + 2.2, D.PED_Y, 12.9), (px + 0.1, D.PED_Y, 13.3)]
for sx in (-1, 1):                                     # the railings and the base of the terraces
    PERCHES += [(sx * 17.6, 1.14, 14.62), (sx * 21.4, 1.14, 14.62), (sx * 26.9, 1.14, 14.62), (sx * 28.8, 0.0, 15.4)]
for x in (-13.4, -9.2, -5.1, -1.2, 2.4, 6.3, 11.8):    # the steps themselves
    PERCHES.append((x, -1.5 - (abs(x) % 3) * 0.9, 18.2 + (abs(x) % 3) * 1.92))
for sx, x in ((-1, 26.0), (1, 26.0)):                  # the great cornice, far above
    PERCHES += [(sx * x, D.ENT_TOP_Y, 12.2), (sx * (x - 12), D.ENT_TOP_Y, 12.3)]
for sx in (-1, 1):                                     # the wings' sills and a bench or two
    for x in (54.0, 62.5, 79.0):
        PERCHES.append((sx * x, 1.7, 7.45))
    PERCHES += [(sx * 52.3, D.PLAZA_Y + 0.5, 24.6), (sx * 68.4, D.PLAZA_Y + 0.92, 24.3), (sx * (D.FOUNTAIN_X + 3), D.PLAZA_Y + 0.3, D.FOUNTAIN_Z + 6.6)]
perch_text = ", ".join(f"Vector3({x:g}, {y:g}, {z:g})" for x, y, z in PERCHES)
nodes.append('[node name="Pigeons" type="MultiMeshInstance3D" parent="Life"]\n'
             'material_override = SubResource("pigeon_look")\nmultimesh = SubResource("flock")\nscript = ExtResource("pigeons")\n'
             f'perches = Array[Vector3]([{perch_text}])\nflap_sound = NodePath("../Sound/PigeonFlap")\ncoo_sound = NodePath("../Sound/PigeonCoo")\n')
nodes.append('[node name="FountainJets" parent="Life" instance=ExtResource("jets")]\n')
nodes.append('[node name="FountainJets" parent="Life/FountainJets" index="0"]\ncast_shadow = 0\n')
nodes += STREET_NODES
nodes.append('[node name="Trees" type="Node3D" parent="."]\n')
nodes += TREE_NODES
nodes.append('[node name="LanternFlicker" type="Node" parent="Life"]\nscript = ExtResource("flicker")\n'
             'lanterns = Array[NodePath]([NodePath("../../Lights/Lantern0"), NodePath("../../Lights/Lantern1")])\n')
nodes.append('[node name="Collision" type="Node3D" parent="."]\n')
for name in ("Ground", "Building", "Props", "Edges"):
    nodes.append(f'[node name="{name}" type="StaticBody3D" parent="Collision"]\n')
nodes += cnodes
nodes.append('[node name="Markers" type="Node3D" parent="."]\n')
for name, (x, y, z) in {"PlayerStart1": (-1.5, D.PLAZA_Y, 33.0), "PlayerStart2": (1.5, D.PLAZA_Y, 33.0), "FrontDoor": (0, D.TERRACE_Y, D.DOOR_Z), "VanCurb": (0, D.ROAD_Y, 37.6),
                        "RoomsMin": (-D.ROOMS_X, D.TERRACE_Y, D.ROOMS_Z[0]), "RoomsMax": (D.ROOMS_X, D.ROOMS_ROOF_Y, D.ROOMS_Z[1]), "CleopatrasNeedle": (nx_, D.PLAZA_Y, nz_)}.items():
    nodes.append(f'[node name="{name}" type="Marker3D" parent="Markers"]\ntransform = {T(x, y, z)}\n')

head = f"""[gd_scene format=3]

[ext_resource type="PackedScene" path="{RES}front.glb" id="front"]
[ext_resource type="PackedScene" path="{RES}wings.glb" id="wings"]
[ext_resource type="PackedScene" path="{RES}props.glb" id="props"]
[ext_resource type="Script" path="res://scripts/exterior_traffic.gd" id="traffic"]
[ext_resource type="Material" path="{RES}ext_props.tres" id="props_mat"]
[ext_resource type="Texture2D" path="{RES}ext_props.png" id="props_tex"]
[ext_resource type="Shader" path="{RES}ext_flag.gdshader" id="flag_shader"]
[ext_resource type="Shader" path="{RES}ext_steam.gdshader" id="steam_shader"]
[ext_resource type="Shader" path="{RES}ext_beam.gdshader" id="beam_shader"]
{STREET_RES}[ext_resource type="PackedScene" path="{RES}fountain_jets.glb" id="jets"]
[ext_resource type="PackedScene" path="{RES}capital.glb" id="capital"]
[ext_resource type="PackedScene" path="{RES}exterior_context.glb" id="context"]
[ext_resource type="Texture2D" path="{RES}ext_lattice_cookie.png" id="cookie"]
[ext_resource type="ArrayMesh" path="res://assets/exterior/meshes/pigeon.res" id="pigeon_mesh"]
{TREE_RES}[ext_resource type="Script" path="res://scripts/exterior_pigeons.gd" id="pigeons"]
[ext_resource type="Script" path="res://scripts/exterior_flicker.gd" id="flicker"]
[ext_resource type="Shader" path="{RES}ext_pigeon.gdshader" id="pigeon_shader"]

[sub_resource type="ShaderMaterial" id="pigeon_look"]
shader = ExtResource("pigeon_shader")

[sub_resource type="MultiMesh" id="flock"]
transform_format = 1
use_custom_data = true
mesh = ExtResource("pigeon_mesh")

{TREE_SUBS}{STREET_SUBS}[sub_resource type="ParticleProcessMaterial" id="moth_motion"]
emission_shape = 3
emission_box_extents = Vector3(1.4, 1.4, 1.4)
direction = Vector3(0, 1, 0)
spread = 180.0
initial_velocity_min = 0.2
initial_velocity_max = 0.7
gravity = Vector3(0, 0, 0)
turbulence_enabled = true
turbulence_noise_strength = 3.0
turbulence_noise_speed_random = 1.0
turbulence_influence_min = 0.3
turbulence_influence_max = 0.8

[sub_resource type="StandardMaterial3D" id="moth_look"]
shading_mode = 0
billboard_mode = 3
albedo_color = Color(1, 0.86, 0.66, 1)

[sub_resource type="QuadMesh" id="moth_quad"]
material = SubResource("moth_look")
size = Vector2(0.035, 0.022)
"""
text = head + "\n" + "\n".join(subs) + "\n" + "\n".join(nodes)
(WT / "scenes" / "exterior.tscn").write_text(text, encoding="utf-8", newline="\n")

night = f"""[gd_scene format=3]

[ext_resource type="PackedScene" path="res://scenes/exterior.tscn" id="exterior"]
[ext_resource type="Script" path="res://scripts/exterior_quality.gd" id="quality"]
[ext_resource type="Shader" path="{RES}ext_night_sky.gdshader" id="sky_shader"]

[sub_resource type="ShaderMaterial" id="sky_mat"]
shader = ExtResource("sky_shader")

[sub_resource type="Sky" id="sky"]
sky_material = SubResource("sky_mat")
radiance_size = 2

[sub_resource type="Environment" id="env"]
background_mode = 2
sky = SubResource("sky")
ambient_light_source = 3
ambient_light_sky_contribution = 1.0
ambient_light_energy = 0.22
reflected_light_source = 1
tonemap_mode = 3
tonemap_white = 6.0
ssao_enabled = true
ssao_radius = 1.4
ssao_intensity = 2.2
ssao_power = 1.6
ssao_detail = 0.6
glow_enabled = true
glow_intensity = 0.6
glow_strength = 0.9
glow_bloom = 0.04
glow_blend_mode = 1
glow_hdr_threshold = 1.1
fog_enabled = true
fog_light_color = Color(0.09, 0.12, 0.2, 1)
fog_density = 0.0016
fog_sky_affect = 0.0

[node name="ExteriorNight" type="Node3D"]

[node name="Environment" type="WorldEnvironment" parent="."]
environment = SubResource("env")

[node name="Moon" type="DirectionalLight3D" parent="."]
transform = Transform3D(0.853, 0.4275, -0.2996, 0, 0.5738, 0.819, 0.522, -0.6986, 0.4894, 0, 60, 0)
light_color = Color(0.66, 0.74, 0.95, 1)
light_energy = 0.12
light_specular = 0.0
shadow_enabled = true
shadow_opacity = 0.55
directional_shadow_max_distance = 260.0

[node name="Exterior" parent="." instance=ExtResource("exterior")]

[node name="Quality" type="Node" parent="."]
script = ExtResource("quality")
"""
(WT / "scenes" / "exterior_night.tscn").write_text(night, encoding="utf-8", newline="\n")
print("exterior written:", len(subs), "shapes,", len(LIGHTS), "lights,", sum(1 for l in LIGHTS if l.get("shadow")), "with shadows")
