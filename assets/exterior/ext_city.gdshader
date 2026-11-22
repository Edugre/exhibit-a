// The apartment blocks across the avenue: plain boxes with windows drawn straight onto them in world
// space, a scatter of them lit. Fades to an even glow in the distance, so far towers never shimmer.
shader_type spatial;

uniform vec3 wall_colour : source_color = vec3(0.40, 0.39, 0.42);
uniform vec3 lamp_warm : source_color = vec3(1.0, 0.74, 0.46);
uniform vec3 lamp_cool : source_color = vec3(0.72, 0.8, 1.0);
uniform float street_level = -4.5;

varying vec3 world_position;
varying vec3 world_normal;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = mat3(MODEL_MATRIX) * NORMAL;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453);
}

void fragment() {
	vec3 n = abs(normalize(world_normal));
	float along = n.x > n.z ? world_position.z : world_position.x;
	vec2 cell = vec2(along / 2.7, (world_position.y - street_level) / 3.3);
	vec2 id = floor(cell);
	vec2 f = fract(cell);
	float pane = step(0.2, f.x) * step(f.x, 0.8) * step(0.22, f.y) * step(f.y, 0.78);
	pane *= (1.0 - step(0.5, n.y)) * step(1.0, id.y);
	float seed = hash(id);
	float lit = step(0.86, seed);
	float blind = 0.55 + 0.45 * step(0.45, f.y + hash(id + 3.1) * 0.3);
	vec3 lamp = mix(lamp_warm, lamp_cool, step(0.93, hash(id + 9.7)));
	// Beyond a few pixels a window, trade the pattern for its average
	float detail = clamp(1.6 - length(fwidth(cell)) * 3.0, 0.0, 1.0);
	float glass = mix(0.36, pane, detail);
	ALBEDO = wall_colour * mix(1.0, 0.45, glass);
	ROUGHNESS = 0.75;
	SPECULAR = 0.3;
	float glow = mix(0.2 * 0.36, lit * pane * blind * (0.35 + 0.65 * hash(id + 5.3)), detail);
	// The street's own light on the lower floors, and a row of shop fronts at ground level
	float height_up = world_position.y - street_level;
	float side = 1.0 - step(0.5, n.y);
	vec3 street_glow = wall_colour * lamp_warm * exp(-height_up * 0.09) * 0.16 * side;
	float bay = floor(along / 9.0);
	float slot = fract(along / 9.0);
	float shop = side * step(0.3, hash(vec2(bay, 2.0))) * step(0.5, height_up) * step(height_up, 3.2) * step(0.08, slot) * step(slot, 0.92);
	// Shop glass in tall panes, brighter at the top of the window, with a dark door in some bays
	float frames = step(0.09, fract(along / 1.5));
	float door = 1.0 - step(0.42, slot) * step(slot, 0.54) * step(0.5, hash(vec2(bay, 4.0)));
	float depth = 0.45 + 0.55 * smoothstep(0.5, 3.2, height_up);
	vec3 shop_light = mix(lamp_warm, vec3(0.92, 0.95, 1.0), step(0.75, hash(vec2(bay, 5.0))));
	EMISSION = lamp * glow * 0.26 + street_glow + shop_light * shop * frames * door * depth * 0.085 * (0.45 + hash(vec2(bay, 7.0)));
}
