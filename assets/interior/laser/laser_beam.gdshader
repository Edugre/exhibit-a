// A laser beam (asset plan P2.1): light added on top of whatever is behind it, brightest where the beam
// faces you and fading at its edges, with a slight flicker. Used twice per beam: a thin hot core and a
// wider soft glow. laser_grid.gd sets `intensity` for the alarm flare and the jammed sputter.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec4 color : source_color = vec4(1.0, 0.06, 0.05, 1.0);
uniform float intensity = 1.0;
// How hard the edges fall off: high for the core, low for the glow.
uniform float edge = 2.0;
uniform float flicker = 0.08;

float hash(float n) {
	return fract(sin(n) * 43758.5453);
}

void fragment() {
	float facing = clamp(abs(dot(normalize(NORMAL), normalize(VIEW))), 0.0, 1.0);
	float shape = pow(facing, edge);
	float flick = 1.0 - flicker * hash(floor(TIME * 24.0));
	float shimmer = 0.92 + 0.08 * sin(TIME * 30.0 + UV.y * 40.0);
	ALBEDO = color.rgb * intensity * shape * flick * shimmer;
}
