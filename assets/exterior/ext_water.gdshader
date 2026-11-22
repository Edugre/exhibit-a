// The thin water over the fountain floor: black and glassy, shivering everywhere and rippling out from
// the plume, with a low glow where the lamps are set under it. Normals are worked out here from noise.
shader_type spatial;

#include "res://assets/exterior/ext_weather.gdshaderinc"

uniform vec3 deep_colour : source_color = vec3(0.012, 0.016, 0.022);
uniform vec3 lamp_colour : source_color = vec3(1.0, 0.86, 0.68);
uniform float centre_x = 38.5;
uniform float centre_z = 22.05;

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

float surface(vec2 p, vec2 centre) {
	float d = length(p - centre);
	float rings = sin(d * 7.0 - TIME * 5.0) * exp(-d * 0.28) * 0.5;
	return value_noise(p * 2.2 + TIME * 0.55) * 0.45 + value_noise(p * 5.1 - TIME * 0.9) * 0.3 + value_noise(p * 12.0 + TIME * 1.7) * 0.14 + rings;
}

void fragment() {
	vec2 p = world_position.xz;
	vec2 centre = vec2(sign(p.x) * centre_x, centre_z);
	float e = 0.04;
	float h = surface(p, centre);
	vec3 n = normalize(vec3((h - surface(p + vec2(e, 0.0), centre)) / e * 0.045, 1.0, (h - surface(p + vec2(0.0, e), centre)) / e * 0.045));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	float d = length(p - centre);
	ALBEDO = deep_colour;
	ROUGHNESS = 0.1;
	SPECULAR = 0.7;
	if (exterior_snow > 0.5) {
		// Frozen over, with snow blown across the ice in drifts
		vec2 q = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * p;
		float blown = weather_noise(q * vec2(0.45, 0.8)) * 0.5 + weather_noise(p * 1.7 + 9.0) * 0.3 + weather_noise(q * 4.3 + 3.0) * 0.2;
		float drift = smoothstep(0.36, 0.66, blown);
		ALBEDO = mix(vec3(0.16, 0.2, 0.25), vec3(0.8, 0.83, 0.9), drift);
		ROUGHNESS = mix(0.26, 0.86, drift);
		SPECULAR = 0.4;
		NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
		EMISSION = vec3(0.0);
	} else {
	// Wishes: coins on the floor of the pool, glinting as the water moves over them
	vec2 cell = floor(p / 0.24);
	vec2 inside = fract(p / 0.24) - 0.5 + (vec2(hash(cell), hash(cell + 3.7)) - 0.5) * 0.4;
	float here = step(0.8, hash(cell + 11.3)) * (1.0 - smoothstep(0.1, 0.16, length(inside)));
	float glint = 0.4 + 0.6 * sin(TIME * 2.6 + h * 16.0 + hash(cell) * 6.283);
	vec3 metal = mix(vec3(0.85, 0.5, 0.25), vec3(0.8, 0.82, 0.85), step(0.5, hash(cell + 7.1)));
	float near = 1.0 - smoothstep(4.0, 26.0, length(CAMERA_POSITION_WORLD.xz - p));
	EMISSION = lamp_colour * (0.012 + 0.09 * exp(-d * d * 0.09)) + metal * here * max(glint, 0.0) * 0.09 * near;
	}
}
