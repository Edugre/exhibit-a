// Leaf clumps on the plaza trees. Each clump stirs on its own in the night air, gusts travel across the
// plaza, and thin leaves let lamplight through from behind. UV.x is how far out on the tree a clump
// sits and UV.y is its random seed.
shader_type spatial;
render_mode cull_disabled;

uniform vec3 leaf_dark : source_color = vec3(0.13, 0.22, 0.15);
uniform vec3 leaf_light : source_color = vec3(0.27, 0.36, 0.19);

void vertex() {
	vec3 world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float reach = UV.x;
	float seed = UV.y;
	float gust = sin(TIME * 0.9 + world.x * 0.07 + world.z * 0.05) * 0.5 + 0.5;
	float amount = 0.07 * (0.3 + reach) * (0.4 + gust);
	VERTEX.x += sin(TIME * 1.7 + seed * 6.283 + world.z * 0.3) * amount;
	VERTEX.z += cos(TIME * 1.3 + seed * 6.283) * amount;
	VERTEX.y += sin(TIME * 2.1 + seed * 6.283) * amount * 0.5;
}

void fragment() {
	ALBEDO = mix(leaf_dark, leaf_light, UV.y);
	ROUGHNESS = 0.82;
	SPECULAR = 0.16;
	BACKLIGHT = ALBEDO * 0.7;
}
