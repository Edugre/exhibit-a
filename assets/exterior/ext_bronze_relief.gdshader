// Cast bronze that has stood outdoors for a century. The body of the metal is dark; green verdigris
// gathers in the hollows and runs down in rain streaks; the high points are rubbed back to warm metal
// by passing hands. All of it comes from the height stored in the relief atlas plus cheap noise.
shader_type spatial;

uniform sampler2D relief_normal : hint_normal, filter_linear_mipmap_anisotropic;
uniform sampler2D relief_ao : hint_default_white, filter_linear_mipmap_anisotropic;
uniform vec3 hollow_bronze : source_color = vec3(0.060, 0.047, 0.036);
uniform vec3 body_bronze : source_color = vec3(0.205, 0.145, 0.088);
uniform vec3 rubbed_bronze : source_color = vec3(0.60, 0.50, 0.36);
uniform vec3 verdigris : source_color = vec3(0.20, 0.31, 0.26);
uniform float normal_depth = 1.3;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

float cloud(vec2 p) {
	return value_noise(p) * 0.55 + value_noise(p * 2.1 + 7.3) * 0.3 + value_noise(p * 4.3 + 2.1) * 0.15;
}

void fragment() {
	vec3 maps = texture(relief_ao, UV).rgb;
	float height = maps.b;
	float hollow = 1.0 - maps.g;
	float mottle = cloud(UV * 34.0);
	float rain = cloud(UV * vec2(120.0, 11.0));
	float green = smoothstep(0.46, 0.8, rain * 0.46 + mottle * 0.3 + (1.0 - height) * 0.36 + hollow * 0.45);
	float rubbed = smoothstep(0.42, 0.74, height + (mottle - 0.5) * 0.2);
	vec3 colour = mix(hollow_bronze, body_bronze, smoothstep(0.08, 0.5, height) * (0.7 + mottle * 0.5));
	colour = mix(colour, verdigris, green * (1.0 - rubbed) * 0.78);
	colour = mix(colour, rubbed_bronze, rubbed * 0.85);
	ALBEDO = colour * mix(0.5, 1.0, maps.g);
	METALLIC = mix(0.3, 0.82, rubbed) * (1.0 - green * 0.6);
	ROUGHNESS = mix(0.68, 0.36, rubbed) + (mottle - 0.5) * 0.14;
	NORMAL_MAP = texture(relief_normal, UV).rgb;
	NORMAL_MAP_DEPTH = normal_depth;
	AO = maps.r;
	AO_LIGHT_AFFECT = 0.45;
}
