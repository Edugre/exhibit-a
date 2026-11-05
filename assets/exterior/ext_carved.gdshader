// Carved pieces: the same limestone as the walls, with sculpted detail from a baked atlas.
// The atlas holds the normal map, and occlusion in two sizes that darken the stone in its recesses.
shader_type spatial;

uniform sampler2D stone_albedo : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D stone_rough : hint_default_white, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D carved_normal : hint_normal, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D carved_ao : hint_default_white, repeat_enable, filter_linear_mipmap_anisotropic;
uniform vec3 tint = vec3(1.0);
uniform float metres_per_tile = 4.0;
uniform float soot_wide = 0.55;
uniform float soot_tight = 0.8;
uniform float normal_depth = 1.0;

varying vec3 world_pos;
varying vec3 world_nor;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(world_nor);
	vec3 blend = pow(abs(n), vec3(6.0));
	blend /= blend.x + blend.y + blend.z;
	vec3 p = world_pos / metres_per_tile;
	vec3 albedo = texture(stone_albedo, p.zy).rgb * blend.x
			+ texture(stone_albedo, p.xz).rgb * blend.y
			+ texture(stone_albedo, p.xy).rgb * blend.z;
	float rough = texture(stone_rough, p.zy).r * blend.x
			+ texture(stone_rough, p.xz).r * blend.y
			+ texture(stone_rough, p.xy).r * blend.z;
	vec2 ao = texture(carved_ao, UV).rg;
	// City dirt settles where the rain can't wash it: recesses go darker and a little cooler
	albedo *= mix(1.0, ao.g, soot_tight) * mix(1.0, ao.r, soot_wide);
	ALBEDO = albedo * tint;
	ROUGHNESS = rough;
	SPECULAR = 0.3;
	NORMAL_MAP = texture(carved_normal, UV).rgb;
	NORMAL_MAP_DEPTH = normal_depth;
	AO = ao.r;
	AO_LIGHT_AFFECT = 0.35;
}
