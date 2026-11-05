// The plaza floor: granite pavers in long running courses, drawn in world space so a floor over 300 m
// long has no seams to unwrap. Near the fountains the stone is wet, dark and glossy.
shader_type spatial;

uniform sampler2D stone_albedo : source_color, repeat_enable, filter_linear_mipmap_anisotropic;
uniform vec3 tint = vec3(0.60, 0.59, 0.58);
uniform float course_width = 0.6;
uniform float paver_length = 1.5;
uniform float band_every = 12.0;
uniform float fountain_x = 38.5;
uniform float fountain_z = 22.05;
uniform float fountain_half = 6.95;

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
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
	float fine = 1.0 - smoothstep(0.01, 0.04, length(fwidth(p)));
	float joint = (1.0 - smoothstep(0.006, 0.016, edge)) * fine;
	float tone = hash(vec2(column, row)) - 0.5;
	// Long darker bands tie the floor to the rhythm of the building
	float band = 1.0 - smoothstep(0.55, 0.62, abs(mod(p.x, band_every) - band_every * 0.5));
	vec3 colour = texture(stone_albedo, p / 2.4).rgb * tint;
	colour *= (1.0 + tone * 0.17) * mix(1.0, 0.72, band) * (1.0 - 0.45 * joint);
	// Wet near the pools, with the edge of the wet patch wandering
	vec2 d = abs(vec2(abs(p.x) - fountain_x, p.y - fountain_z)) - vec2(fountain_half);
	float outside = length(max(d, vec2(0.0)));
	float wander = value_noise(p * 0.55) * 2.4;
	float wet = 1.0 - smoothstep(0.6 + wander * 0.6, 1.4 + wander * 1.1, outside);
	ALBEDO = colour * mix(1.0, 0.45, wet);
	ROUGHNESS = mix(0.74 + tone * 0.12, 0.16, wet);
	SPECULAR = mix(0.14, 0.62, wet);
}
