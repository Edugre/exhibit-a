// The pool of light a car's headlamps throw on the road ahead. A soft quad drawn on the asphalt, so
// fourteen cars cost one draw call and no real lights.
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 lamp_colour : source_color = vec3(1.0, 0.9, 0.72);
uniform float strength = 0.13;

void fragment() {
	vec2 q = vec2(UV.x * 2.0 - 1.0, UV.y);
	float along = smoothstep(0.0, 0.22, q.y) * (1.0 - smoothstep(0.35, 1.0, q.y));
	float across = 1.0 - smoothstep(0.1, 1.0, abs(q.x) / (0.45 + q.y * 0.55));
	ALBEDO = lamp_colour;
	ALPHA = along * across * strength;
}
