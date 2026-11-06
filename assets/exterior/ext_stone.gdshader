// Limestone laid on in world space, so walls, shafts and steps need no UVs and share one texture set.
// Optional coursed blocks are drawn here too: their joints, their slight differences in tone, and the
// dirt that collects below ledges.
shader_type spatial;

// Set by the alarm when the Book is taken: the baked floodlights pulse red, as the real ones do
global uniform float exterior_alarm;

uniform sampler2D stone_albedo : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D stone_normal : hint_normal, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D stone_rough : hint_default_white, repeat_enable, filter_linear_mipmap_anisotropic;
uniform vec3 tint = vec3(1.0);
uniform float metres_per_tile = 4.0;
uniform float normal_strength = 1.0;
uniform float roughness_add = 0.0;
// Coursed blocks
uniform bool joints = false;
uniform float course_height = 0.62;
uniform float block_length = 1.74;
uniform float joint_width = 0.016;
uniform float block_tone = 0.09;
// Rain marks that run down from the top of a wall, measured in world height
uniform float grime = 0.0;
uniform float grime_top = 19.0;
uniform float grime_length = 9.0;

// A century of weather, laid across the whole front like a stencil, so nothing repeats
uniform sampler2D stain_map : hint_default_white, filter_linear_mipmap;
uniform float stain_amount = 0.0;
uniform vec4 stain_rect = vec4(-32.0, -5.0, 64.0, 36.0);
// LOW graphics: one texture projection instead of three, and the floodlights read from a baked map
uniform bool low_detail = false;
uniform sampler2D baked_light : source_color, hint_default_black, filter_linear_mipmap;
uniform float baked_strength = 0.0;
uniform sampler2D star_map : hint_default_black, filter_linear_mipmap;
uniform float star_strength = 0.0;
// Only used while baking that map: every stone the same grey, so the map holds light and nothing else
uniform float capture_albedo = 0.0;

varying vec3 world_pos;
varying vec3 world_nor;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// The window's star on the floor, worked out here at LOW instead of by a shadow-casting light
vec3 star_light(vec3 point, sampler2D star, float strength) {
	vec3 from_window = point - vec3(0.0, 15.2, 9.75);
	vec3 axis = normalize(vec3(0.0, -15.2, 7.75));
	vec3 up = normalize(cross(vec3(1.0, 0.0, 0.0), axis));
	float depth = max(dot(from_window, axis), 0.1);
	vec2 q = vec2(from_window.x, dot(from_window, up)) / (depth * 0.5095);
	return texture(star, q * 0.5 + 0.5).rgb * vec3(1.0, 0.74, 0.46) * strength * (1.0 - smoothstep(0.86, 1.0, length(q)));
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

	if (low_detail) {
		vec3 a = abs(n);
		vec2 uv = a.y > a.x && a.y > a.z ? p.xz : (a.x > a.z ? p.zy : p.xy);
		ALBEDO = texture(stone_albedo, uv).rgb * tint;
		if (stain_amount > 0.0) {
			vec2 s = (world_pos.xy - stain_rect.xy) / stain_rect.zw;
			vec2 st = vec2(s.x, 1.0 - s.y);
			ALBEDO *= texture(stain_map, st).r * 1.5;
			if (baked_strength > 0.0 && s.x > 0.0 && s.x < 1.0 && s.y > 0.0 && s.y < 1.0) {
				vec3 warning = vec3(1.25, 0.14, 0.09) * (0.72 + 0.28 * sin(TIME * 3.4));
				EMISSION = ALBEDO * texture(baked_light, st).rgb * baked_strength * mix(vec3(1.0), warning, exterior_alarm);
			}
		}
		if (star_strength > 0.0) {
			EMISSION += ALBEDO * star_light(world_pos, star_map, star_strength);
		}
		ROUGHNESS = clamp(0.78 + roughness_add, 0.0, 1.0);
		SPECULAR = 0.2;
	} else {
	vec3 albedo = texture(stone_albedo, p.zy).rgb * blend.x
			+ texture(stone_albedo, p.xz).rgb * blend.y
			+ texture(stone_albedo, p.xy).rgb * blend.z;
	float rough = texture(stone_rough, p.zy).r * blend.x
			+ texture(stone_rough, p.xz).r * blend.y
			+ texture(stone_rough, p.xy).r * blend.z;

	// Whiteout blend of the three projected normal maps, in world space
	// Normal maps are stored as two channels, so the third is rebuilt here
	vec3 tx = vec3(texture(stone_normal, p.zy).xy * 2.0 - 1.0, 0.0);
	vec3 ty = vec3(texture(stone_normal, p.xz).xy * 2.0 - 1.0, 0.0);
	vec3 tz = vec3(texture(stone_normal, p.xy).xy * 2.0 - 1.0, 0.0);
	tx.z = sqrt(max(1.0 - dot(tx.xy, tx.xy), 0.0));
	ty.z = sqrt(max(1.0 - dot(ty.xy, ty.xy), 0.0));
	tz.z = sqrt(max(1.0 - dot(tz.xy, tz.xy), 0.0));
	tx.xy *= normal_strength;
	ty.xy *= normal_strength;
	tz.xy *= normal_strength;
	vec3 wx = vec3(tx.xy + n.zy, abs(tx.z) * n.x);
	vec3 wy = vec3(ty.xy + n.xz, abs(ty.z) * n.y);
	vec3 wz = vec3(tz.xy + n.xy, abs(tz.z) * n.z);
	vec3 wn = normalize(wx.zyx * blend.x + wy.xzy * blend.y + wz.xyz * blend.z);

	// Walls only: coordinates along the face and up it
	vec2 c = abs(n.z) > abs(n.x) ? world_pos.xy : world_pos.zy;
	float wall = 1.0 - smoothstep(0.5, 0.8, abs(n.y));

	if (joints && wall > 0.0) {
		float row = floor(c.y / course_height);
		float shift = mod(row, 2.0) * 0.5 * block_length;
		float column = floor((c.x + shift) / block_length);
		vec2 f = vec2(fract((c.x + shift) / block_length) * block_length, fract(c.y / course_height) * course_height);
		float dx = min(f.x, block_length - f.x);
		float dy = min(f.y, course_height - f.y);
		float d = min(dx, dy);
		// Joints narrower than a pixel are faded out, or a far wall breaks into a pattern of dots
		float fine = 1.0 - smoothstep(0.015, 0.05, length(fwidth(c)));
		float groove = (1.0 - smoothstep(joint_width, joint_width * 2.2, d)) * fine;
		float tone = hash(vec2(column, row)) - 0.5;
		albedo *= 1.0 + tone * block_tone * wall;
		albedo *= 1.0 - 0.36 * groove * wall;
		// Each block's edge rolls away a little into the joint, and catches raking light
		float edge = (1.0 - smoothstep(joint_width, joint_width * 4.0, d)) * wall * fine;
		vec3 up_axis = vec3(0.0, 1.0, 0.0);
		vec3 along = abs(n.z) > abs(n.x) ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 0.0, 1.0);
		vec3 bend = dy < dx ? up_axis * (f.y < course_height * 0.5 ? -1.0 : 1.0) : along * (f.x < block_length * 0.5 ? -1.0 : 1.0);
		wn = normalize(wn + bend * edge * 0.5);
	}

	if (grime > 0.0) {
		float streak = texture(stone_albedo, vec2(c.x * 0.31, world_pos.y * 0.018)).g;
		streak = smoothstep(0.52, 0.70, streak);
		float fall = 1.0 - clamp((grime_top - world_pos.y) / grime_length, 0.0, 1.0);
		albedo *= 1.0 - grime * fall * (0.35 + 0.65 * streak) * wall;
	}

	if (stain_amount > 0.0) {
		vec2 s = (world_pos.xy - stain_rect.xy) / stain_rect.zw;
		float weather = texture(stain_map, vec2(s.x, 1.0 - s.y)).r * 1.5;
		albedo *= mix(1.0, weather, stain_amount);
	}

	ALBEDO = albedo * tint;
	ROUGHNESS = clamp(rough + roughness_add, 0.0, 1.0);
	SPECULAR = 0.3;
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
	}
	if (capture_albedo > 0.0) {
		ALBEDO = vec3(capture_albedo);
	}
}
