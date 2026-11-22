// Interior surfaces laid on in world space, so CSG rooms need no UVs: floors, painted walls, ceilings and
// skirting all share this. Optional slabs with grout for marble floors, and a soft shade where walls
// meet the floor and ceiling, which the room lights alone don't give at night.
shader_type spatial;

uniform sampler2D albedo_map : source_color, hint_default_white, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D normal_map : hint_normal, repeat_enable, filter_linear_mipmap_anisotropic;
uniform bool use_normal_map = true;
uniform vec3 tint : source_color = vec3(1.0);
uniform float metres_per_tile = 2.0;
uniform float normal_strength = 1.0;
uniform float roughness = 0.6;
// Darker texels a little rougher, so gaps and grain read as matte against a satin finish
uniform float roughness_from_dark = 0.0;
uniform float specular = 0.4;
// Slabs: a grid in world space, each slab a slightly different tone and a different patch of the
// texture, so the veins don't run in lines across the room
uniform float tile_size = 0.0;
uniform float grout_width = 0.004;
uniform vec3 grout_color : source_color = vec3(0.42, 0.40, 0.37);
uniform float tile_tone = 0.05;
// Walls go a little darker towards the floor and the ceiling (room heights from int_dims.py)
uniform float corner_shade = 0.0;
uniform float wall_height = 4.0;
// Wear, from one map on its own repeat so it never lines up with the surface under it.
// R: dirt and grime. G: scratches (positive lightens, for wood and stone; negative darkens, for scuffs on paint).
// B: patches worn dull, which lose their shine.
uniform sampler2D wear_map : hint_default_black, repeat_enable, filter_linear_mipmap_anisotropic;
uniform float wear_tile = 3.1;
uniform float dirt = 0.0;
uniform float scratches = 0.0;
uniform float dullness = 0.0;
// Walls: scuffs and grime gather below this height, where feet, bags and trolleys hit. 0 = all over.
uniform float scuff_height = 0.0;

varying vec3 world_pos;
varying vec3 world_nor;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(world_nor);
	vec3 blend = pow(abs(n), vec3(6.0));
	blend /= blend.x + blend.y + blend.z;
	vec3 p = world_pos / metres_per_tile;

	// Slabs only on floors and ceilings: shift each slab's patch of texture and its tone
	vec2 shift = vec2(0.0);
	float tone = 0.0;
	float grout = 0.0;
	vec2 slab_edge = vec2(0.0);
	bool flat_face = abs(n.y) > 0.7;
	if (tile_size > 0.0 && flat_face) {
		vec2 c = world_pos.xz / tile_size;
		vec2 id = floor(c);
		shift = vec2(hash(id), hash(id + 17.0)) * 7.0;
		tone = hash(id + 3.0) - 0.5;
		vec2 f = fract(c) * tile_size;
		vec2 d = min(f, tile_size - f);
		float fine = 1.0 - smoothstep(0.004, 0.02, length(fwidth(world_pos.xz)));
		grout = (1.0 - smoothstep(grout_width, grout_width * 2.0, min(d.x, d.y))) * fine;
		slab_edge = (1.0 - smoothstep(grout_width, grout_width * 5.0, d)) * sign(f - tile_size * 0.5) * fine;
	}

	vec3 albedo = texture(albedo_map, p.zy).rgb * blend.x
			+ texture(albedo_map, p.xz + shift).rgb * blend.y
			+ texture(albedo_map, p.xy).rgb * blend.z;
	albedo *= tint * (1.0 + tone * tile_tone * 2.0);

	// Wear: one projection is enough, from the side the face mostly looks along
	vec3 a = abs(n);
	vec2 wear_uv = (a.y > a.x && a.y > a.z ? world_pos.xz : (a.x > a.z ? world_pos.zy : world_pos.xy)) / wear_tile;
	vec3 worn = texture(wear_map, wear_uv).rgb;
	float low = scuff_height > 0.0 && !flat_face ? 1.0 - smoothstep(0.0, scuff_height, world_pos.y) : 1.0;
	albedo *= 1.0 - dirt * worn.r * (scuff_height > 0.0 && !flat_face ? 0.35 + 0.65 * low : 1.0);
	if (scratches > 0.0) {
		albedo = mix(albedo, albedo * 1.35 + 0.04, scratches * worn.g);
	} else {
		albedo *= 1.0 + scratches * worn.g * low;
	}
	albedo = mix(albedo, grout_color * mix(1.0, 0.65, worn.r), grout);

	vec3 wn = n;
	if (use_normal_map) {
		// Whiteout blend of the three projected normal maps, in world space.
		// Normal maps are stored as two channels, so the third is rebuilt here.
		vec3 tx = vec3(texture(normal_map, p.zy).xy * 2.0 - 1.0, 0.0);
		vec3 ty = vec3(texture(normal_map, p.xz + shift).xy * 2.0 - 1.0, 0.0);
		vec3 tz = vec3(texture(normal_map, p.xy).xy * 2.0 - 1.0, 0.0);
		tx.z = sqrt(max(1.0 - dot(tx.xy, tx.xy), 0.0));
		ty.z = sqrt(max(1.0 - dot(ty.xy, ty.xy), 0.0));
		tz.z = sqrt(max(1.0 - dot(tz.xy, tz.xy), 0.0));
		tx.xy *= normal_strength;
		ty.xy *= normal_strength;
		tz.xy *= normal_strength;
		vec3 wx = vec3(tx.xy + n.zy, abs(tx.z) * n.x);
		vec3 wy = vec3(ty.xy + n.xz, abs(ty.z) * n.y);
		vec3 wz = vec3(tz.xy + n.xy, abs(tz.z) * n.z);
		wn = normalize(wx.zyx * blend.x + wy.xzy * blend.y + wz.xyz * blend.z);
	}
	// Each slab's edge rolls off a touch into the grout and catches the light
	wn = normalize(wn + vec3(slab_edge.x, 0.0, slab_edge.y) * 0.35 * sign(n.y));

	if (corner_shade > 0.0 && !flat_face) {
		float y = world_pos.y;
		float low = 1.0 - smoothstep(0.0, 0.9, y);
		float high = smoothstep(wall_height - 0.7, wall_height, y);
		albedo *= 1.0 - corner_shade * max(low, high * 0.7);
	}

	float lum = dot(albedo, vec3(0.3, 0.59, 0.11));
	ALBEDO = albedo;
	ROUGHNESS = clamp(roughness + roughness_from_dark * (0.5 - lum) + grout * 0.5 + dullness * worn.b + worn.g * abs(scratches) * 0.2, 0.0, 1.0);
	SPECULAR = specular;
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
}
