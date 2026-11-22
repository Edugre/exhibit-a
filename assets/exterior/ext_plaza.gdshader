// The plaza floor: granite pavers in long running courses, drawn in world space so a floor over 300 m
// long has no seams to unwrap. Near the fountains the stone is wet, dark and glossy.
shader_type spatial;

global uniform float exterior_alarm;

#include "res://assets/exterior/ext_weather.gdshaderinc"

uniform sampler2D stone_albedo : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform vec3 tint = vec3(0.60, 0.59, 0.58);
uniform float course_width = 0.6;
uniform float paver_length = 1.5;
uniform float band_every = 12.0;
uniform float fountain_x = 38.5;
uniform float fountain_z = 22.05;
uniform float fountain_half = 6.95;
uniform bool low_detail = false;
uniform sampler2D star_map : hint_default_black, filter_linear_mipmap;
uniform float star_strength = 0.0;

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
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

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

void fragment() {
	vec2 p = world_position.xz;
	float row = floor(p.y / course_width);
	float shift = mod(row, 2.0) * 0.5 * paver_length;
	float column = floor((p.x + shift) / paver_length);
	vec2 f = vec2(fract((p.x + shift) / paver_length) * paver_length, fract(p.y / course_width) * course_width);
	float edge = min(min(f.x, paver_length - f.x), min(f.y, course_width - f.y));
	// Joints are drawn with their real width on screen, and thin away with distance instead of crawling
	float pixel = max(length(fwidth(p)), 0.0004);
	float joint = (1.0 - smoothstep(0.011 - pixel, 0.011 + pixel, edge)) * clamp(0.018 / pixel, 0.0, 1.0);
	float tone = (hash(vec2(column, row)) - 0.5) * clamp(1.5 - pixel * 16.0, 0.0, 1.0);
	// Long darker bands tie the floor to the rhythm of the building
	float band = 1.0 - smoothstep(0.55, 0.62, abs(mod(p.x, band_every) - band_every * 0.5));
	vec3 colour = texture(stone_albedo, p / 2.4).rgb * tint;
	colour *= (1.0 + tone * 0.17) * mix(1.0, 0.72, band) * (1.0 - 0.45 * joint);
	// Wet near the pools, with the edge of the wet patch wandering
	vec2 d = abs(vec2(abs(p.x) - fountain_x, p.y - fountain_z)) - vec2(fountain_half);
	float outside = length(max(d, vec2(0.0)));
	float wander = value_noise(p * 0.55) * 2.4;
	float wet = 1.0 - smoothstep(0.6 + wander * 0.6, 1.4 + wander * 1.1, outside);
	vec3 surface = colour * mix(1.0, 0.45, wet);
	float rough = mix(0.74 + tone * 0.12, 0.16, wet);
	float specular = mix(0.14, 0.62, wet);
	apply_weather(world_position, vec3(0.0, 1.0, 0.0), 1.0, surface, rough, specular);
	ALBEDO = surface;
	ROUGHNESS = rough;
	SPECULAR = specular;
	if (!low_detail) {
		NORMAL = normalize((VIEW_MATRIX * vec4(weather_ripple(world_position, vec3(0.0, 1.0, 0.0), TIME), 0.0)).xyz);
	}
	if (low_detail && star_strength > 0.0) {
		vec3 warning = vec3(1.25, 0.14, 0.09) * (0.72 + 0.28 * sin(TIME * 3.4));
		EMISSION = ALBEDO * star_light(world_position, star_map, star_strength) * mix(vec3(1.0), warning, exterior_alarm);
	}
}
