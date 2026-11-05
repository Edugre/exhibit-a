"""Writes the style test into the repo: textures, import settings, shared materials and the scene.
usage: python gen_section.py <capital bake dir> <section dir>"""
import json
import pathlib
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ext_dims as D

WT = pathlib.Path(r"C:\Users\waism\Downloads\exhibit-a\.claude\worktrees\agitated-benz-0e18d0")
A = WT / "assets" / "exterior"
CAP = pathlib.Path(sys.argv[1])
SEC = pathlib.Path(sys.argv[2])
RES = "res://assets/exterior/"

# --- Textures ---------------------------------------------------------------------------------
ORN = pathlib.Path(sys.argv[3])
TRIM = pathlib.Path(sys.argv[4])


def atlas(capital, modillion, keystone, fill):
    """Capital in the lower three quarters; bracket and keystone side by side above it."""
    a = Image.new("RGB", (2048, 2048), fill)
    a.paste(Image.open(capital).convert("RGB").resize((2048, 1536), Image.LANCZOS), (0, 512))
    a.paste(Image.open(modillion).convert("RGB").resize((512, 512), Image.LANCZOS), (0, 0))
    a.paste(Image.open(keystone).convert("RGB").resize((512, 512), Image.LANCZOS), (512, 0))
    return a


atlas(CAP / "cap_normal.png", ORN / "modillion_normal.png", ORN / "keystone_normal.png", (128, 128, 255)).save(A / "ext_carved_normal.png", optimize=True)
wide = atlas(CAP / "cap_ao_wide.png", ORN / "modillion_ao_wide.png", ORN / "keystone_ao_wide.png", (255, 255, 255)).convert("L")
tight = atlas(CAP / "cap_ao_tight.png", ORN / "modillion_ao_tight.png", ORN / "keystone_ao_tight.png", (255, 255, 255)).convert("L")
Image.merge("RGB", (wide, tight, Image.new("L", (2048, 2048), 0))).save(A / "ext_carved_ao.png", optimize=True)
shutil.copy(TRIM / "ext_trim_normal.png", A / "ext_trim_normal.png")
shutil.copy(TRIM / "ext_trim_ao.png", A / "ext_trim_ao.png")


def tex_import(name, normal=False):
    (A / f"{name}.png.import").write_text(f"""[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="{RES}{name}.png"

[params]

compress/mode=2
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
                ("ext_trim_normal", True), ("ext_trim_ao", False)):
    tex_import(n, is_n)

# --- Models -----------------------------------------------------------------------------------
shutil.copy(CAP / "capital.glb", A / "capital.glb")
shutil.copy(SEC / "section.glb", A / "section.glb")
MATS = ["ext_shaft", "ext_ashlar", "ext_stone", "ext_granite", "ext_rough", "ext_trim", "ext_bronze", "ext_glass", "ext_paving", "ext_carved", "ext_riser"]


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
glb_import("section", MATS)
glb_import("exterior_context", {"BO_Stone": "ext_context", "BO_StoneDark": "ext_context_dark", "BO_Steps": "ext_granite", "BO_Paving": "ext_paving", "BO_City": "ext_context_dark"})


# --- Materials --------------------------------------------------------------------------------
def stone_mat(name, **params):
    tex = {"stone_albedo": "ext_stone_albedo.png", "stone_normal": "ext_stone_normal.png", "stone_rough": "ext_stone_rough.png"}
    lines = ['[gd_resource type="ShaderMaterial" format=3]\n', f'[ext_resource type="Shader" path="{RES}ext_stone.gdshader" id="s"]']
    for i, (k, v) in enumerate(tex.items()):
        lines.append(f'[ext_resource type="Texture2D" path="{RES}{v}" id="t{i}"]')
    lines.append("\n[resource]\nshader = ExtResource(\"s\")")
    for i, k in enumerate(tex):
        lines.append(f'shader_parameter/{k} = ExtResource("t{i}")')
    for k, v in params.items():
        lines.append(f"shader_parameter/{k} = {v}")
    (A / f"{name}.tres").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


stone_mat("ext_stone", tint="Vector3(1, 1, 1)")
stone_mat("ext_shaft", joints="true", course_height=2.37, block_length=400.0, joint_width=0.007, block_tone=0.06)
stone_mat("ext_ashlar", joints="true", course_height=0.74, block_length=2.46, joint_width=0.010, block_tone=0.05, grime=0.32, grime_top=19.0, grime_length=10.0)
stone_mat("ext_rough", tint="Vector3(0.86, 0.84, 0.8)", normal_strength=3.0, metres_per_tile=2.6, roughness_add=0.05)
stone_mat("ext_granite", tint="Vector3(0.42, 0.415, 0.41)", metres_per_tile=1.4, normal_strength=0.7, roughness_add=-0.10)
stone_mat("ext_riser", tint="Vector3(0.36, 0.355, 0.35)", metres_per_tile=1.4, normal_strength=0.7, roughness_add=-0.05)
stone_mat("ext_paving", tint="Vector3(0.62, 0.61, 0.6)", metres_per_tile=3.2, roughness_add=-0.08)
stone_mat("ext_context", tint="Vector3(0.72, 0.71, 0.69)")
stone_mat("ext_context_dark", tint="Vector3(0.5, 0.5, 0.5)")


def carved_mat(name, normal, ao):
    (A / f"{name}.tres").write_text(f"""[gd_resource type="ShaderMaterial" format=3]

[ext_resource type="Shader" path="{RES}ext_carved.gdshader" id="s"]
[ext_resource type="Texture2D" path="{RES}ext_stone_albedo.png" id="t0"]
[ext_resource type="Texture2D" path="{RES}ext_stone_rough.png" id="t1"]
[ext_resource type="Texture2D" path="{RES}{normal}" id="t2"]
[ext_resource type="Texture2D" path="{RES}{ao}" id="t3"]

[resource]
shader = ExtResource("s")
shader_parameter/stone_albedo = ExtResource("t0")
shader_parameter/stone_rough = ExtResource("t1")
shader_parameter/carved_normal = ExtResource("t2")
shader_parameter/carved_ao = ExtResource("t3")
""", encoding="utf-8", newline="\n")


carved_mat("ext_carved", "ext_carved_normal.png", "ext_carved_ao.png")
carved_mat("ext_trim", "ext_trim_normal.png", "ext_trim_ao.png")

(A / "ext_bronze.tres").write_text("""[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.30, 0.21, 0.115, 1)
metallic = 0.35
roughness = 0.46
""", encoding="utf-8", newline="\n")
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


# --- Scene ------------------------------------------------------------------------------------
def T(x, y, z):
    return f"Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x:g}, {y:g}, {z:g})"


def spot(name, pos, target, energy, angle, rng, color, shadow=True):
    return dict(name=name, pos=pos, target=target, energy=energy, angle=angle, rng=rng, color=color, shadow=shadow)


CAP_Y = D.COL_TOP_Y - 1.92
nodes = []
nodes.append('[node name="ExteriorSection" type="Node3D"]\n')
nodes.append('[node name="Environment" type="WorldEnvironment" parent="."]\nenvironment = SubResource("env")\n')
nodes.append('[node name="Moon" type="DirectionalLight3D" parent="."]\n'
             'transform = Transform3D(0.853, 0.4275, -0.2996, 0, 0.5738, 0.819, 0.522, -0.6986, 0.4894, 0, 40, 0)\n'
             'light_color = Color(0.66, 0.74, 0.95, 1)\nlight_energy = 0.12\nlight_specular = 0.0\nshadow_enabled = true\ndirectional_shadow_max_distance = 120.0\n')
nodes.append('[node name="Context" parent="." instance=ExtResource("context")]\n')
nodes.append('[node name="Section" parent="." instance=ExtResource("section")]\n')
nodes.append('[node name="Capitals" type="Node3D" parent="."]\n')
k = 0
for px in (-7.0, 7.0):
    for sx in (-1, 1):
        x = px + sx * D.PAIR_GAP
        nodes.append(f'[node name="Capital{k}" parent="Capitals" instance=ExtResource("capital")]\ntransform = {T(x, CAP_Y, D.COL_Z)}\n')
        k += 1
        nodes.append(f'[node name="Capital{k}" parent="Capitals" instance=ExtResource("capital")]\ntransform = {T(x, CAP_Y, D.WALL_Z + 0.34)}\n')
        k += 1
nodes.append('[node name="Lights" type="Node3D" parent="."]\n')
LIGHTS = json.loads((pathlib.Path(__file__).parent / "lights.json").read_text())
for i, l in enumerate(LIGHTS):
    px, py, pz = l["pos"]
    tx, ty, tz = l["target"]
    f = np.array([tx - px, ty - py, tz - pz], dtype=float)
    f /= np.linalg.norm(f)
    z = -f
    up = np.array([0.0, 1.0, 0.0]) if abs(f[1]) < 0.99 else np.array([0.0, 0.0, 1.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    basis = f"{x[0]:.5f}, {y[0]:.5f}, {z[0]:.5f}, {x[1]:.5f}, {y[1]:.5f}, {z[1]:.5f}, {x[2]:.5f}, {y[2]:.5f}, {z[2]:.5f}"
    c = l["color"]
    if l.get("omni"):
        nodes.append(f'[node name="{l["name"]}" type="OmniLight3D" parent="Lights"]\ntransform = {T(px, py, pz)}\n'
                     f'light_color = Color({c[0]}, {c[1]}, {c[2]}, 1)\nlight_energy = {l["energy"]}\nomni_range = {l["range"]}\nomni_attenuation = 1.2\n'
                     f'shadow_enabled = {"true" if l.get("shadow") else "false"}\nlight_specular = 0.2\n')
    else:
        nodes.append(f'[node name="{l["name"]}" type="SpotLight3D" parent="Lights"]\ntransform = Transform3D({basis}, {px:g}, {py:g}, {pz:g})\n'
                     f'light_color = Color({c[0]}, {c[1]}, {c[2]}, 1)\nlight_energy = {l["energy"]}\nspot_range = {l["range"]}\nspot_angle = {l["angle"]}\n'
                     f'spot_angle_attenuation = {l.get("soft", 0.7)}\nspot_attenuation = {l.get("atten", 0.9)}\nshadow_enabled = {"true" if l.get("shadow", True) else "false"}\n'
                     f'shadow_blur = 1.2\nlight_specular = 0.25\n')

head = f"""[gd_scene format=3]

[ext_resource type="PackedScene" path="{RES}section.glb" id="section"]
[ext_resource type="PackedScene" path="{RES}capital.glb" id="capital"]
[ext_resource type="PackedScene" path="{RES}exterior_context.glb" id="context"]
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
ambient_light_energy = 0.12
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
fog_density = 0.0024
fog_sky_affect = 0.0
"""
(WT / "scenes" / "exterior_section.tscn").write_text(head + "\n" + "\n".join(nodes), encoding="utf-8", newline="\n")
print("section scene written", len(LIGHTS), "lights")
