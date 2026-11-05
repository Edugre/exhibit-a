// A jet of fountain water. Solid where it leaves the nozzle, breaking into beads as it travels, and
// always moving: the water is only a pattern sliding along a ribbon, so there are no particles to pay for.
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never;

uniform vec3 water_colour : source_color = vec3(0.86, 0.9, 0.96);
uniform float brightness = 0.55;

void vertex() {
	float t = UV.x;
	float seed = UV.y;
	// Each jet breathes a little, on its own slow rhythm
	VERTEX.y += 4.0 * t * (1.0 - t) * 0.28 * sin(TIME * 0.8 + seed * 6.283);
}

void fragment() {
	float t = UV.x;
	float seed = UV.y;
	float flow = t * 34.0 - TIME * 13.0 + seed * 41.0;
	float beads = smoothstep(0.1, 0.8, sin(flow) * 0.5 + 0.5) * smoothstep(0.0, 0.7, sin(flow * 0.37 + seed * 9.0) * 0.5 + 0.5);
	float solid = 1.0 - smoothstep(0.3, 0.8, t);
	float light = mix(beads, 1.0, solid) * (1.0 - smoothstep(0.92, 1.0, t) * 0.7);
	ALBEDO = water_colour;
	ALPHA = clamp(light * brightness, 0.0, 1.0);
}
