// Heavy cloth moving in the night air. The wind lives entirely in the vertex shader, so three big
// banners cost almost nothing, and every peer sees them move without any network traffic.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D print : source_color, filter_linear_mipmap_anisotropic;
// The Book's banner when the Book has gone: it unrolls from the rod over the old one
uniform sampler2D print_stolen : source_color, filter_linear_mipmap_anisotropic;
global uniform float exterior_alarm;
uniform float sway = 0.11;
uniform float speed = 0.8;

// LOW graphics: no floodlights reach the cloth, so it carries its own light
uniform bool low_detail = false;

void vertex() {
	// UV.y runs from the rod at the top (0) to the free hem at the bottom (1)
	float free_cloth = UV.y * UV.y;
	float x = (MODEL_MATRIX * vec4(VERTEX, 1.0)).x;
	float t = TIME * speed;
	float wave = sin(t + x * 0.9) * 0.6 + sin(t * 1.7 + x * 2.3 + UV.y * 3.0) * 0.3 + sin(t * 0.37) * 0.5;
	VERTEX.z += wave * sway * free_cloth;
	VERTEX.x += sin(t * 0.8 + UV.y * 2.0) * sway * 0.25 * free_cloth;
}

void fragment() {
	ALBEDO = texture(print, UV).rgb;
	if (UV.x > 0.3334 && UV.x < 0.6666 && UV.y < exterior_alarm * 1.03) {
		ALBEDO = texture(print_stolen, vec2((UV.x - 0.33333) * 3.0, UV.y)).rgb;
	}
	ROUGHNESS = 0.88;
	SPECULAR = 0.2;
	// A little light passes through the cloth, so it glows softly when lit from behind
	BACKLIGHT = ALBEDO * 0.4;
	if (low_detail) {
		EMISSION = ALBEDO * 0.42;
	}
}
