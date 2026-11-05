// The wings' dark windows at night. Nothing is lit inside; each pane just catches a slightly different
// slice of sky above and street glow below, the way old glass does, so a window never reads as a black hole.
shader_type spatial;

uniform vec3 sky_colour : source_color = vec3(0.17, 0.25, 0.43);
uniform vec3 street_colour : source_color = vec3(0.52, 0.36, 0.22);
uniform float strength = 0.17;

varying vec3 world_position;
varying vec3 world_normal;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 c = abs(world_normal.z) > abs(world_normal.x) ? world_position.xy : world_position.zy;
	vec2 pane = floor(c / vec2(1.12, 1.45));
	float tone = hash(pane);
	float rise = clamp((world_position.y + 1.0) / 11.0, 0.0, 1.0);
	vec3 reflected = mix(street_colour, sky_colour, smoothstep(0.1, 0.62, rise + (tone - 0.5) * 0.3));
	float facing = 1.0 - clamp(dot(normalize(VIEW), NORMAL), 0.0, 1.0);
	ALBEDO = vec3(0.012, 0.015, 0.02);
	ROUGHNESS = 0.16;
	SPECULAR = 0.7;
	EMISSION = reflected * strength * (0.45 + 0.7 * tone) * (0.55 + facing);
}
