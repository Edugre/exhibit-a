// The museum's flag. Pinned at the pole, the cloth ripples harder the further it is from it. The print
// is one cell of the shared props texture.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D print_map : source_color, filter_linear_mipmap_anisotropic;
uniform vec4 print_rect = vec4(0.0, 0.0, 1.0, 1.0);
uniform float wind = 1.0;

void vertex() {
	float along = UV.x;
	float t = TIME * 3.4;
	float wave = sin(along * 9.0 - t) * 0.5 + sin(along * 17.0 - t * 1.7 + UV.y * 3.0) * 0.22;
	float droop = along * along * 0.22 * (0.7 + 0.3 * sin(TIME * 0.6));
	VERTEX.z += wave * along * 0.34 * wind;
	VERTEX.y += (wave * 0.05 - droop) * along;
	VERTEX.x -= along * along * 0.08;
	NORMAL = normalize(NORMAL + vec3(cos(along * 9.0 - t) * along * 1.1, 0.0, 0.0));
}

void fragment() {
	vec2 uv = mix(print_rect.xy, print_rect.zw, UV);
	ALBEDO = texture(print_map, uv).rgb;
	ROUGHNESS = 0.75;
	SPECULAR = 0.2;
	BACKLIGHT = ALBEDO * 0.5;
}
