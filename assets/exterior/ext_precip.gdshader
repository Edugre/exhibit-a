// Rain and snow. There are no particles to simulate: every drop is a quad that works out its own fall
// here, from the clock, and wraps round a box that travels with the camera. It costs a few thousand
// vertices, the same on every machine, and the sky never runs out when somebody sprints.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, shadows_disabled, depth_draw_never;

global uniform float exterior_alarm;

uniform vec3 box = vec3(28.0, 18.0, 28.0);
uniform float fall_speed = 15.0;
uniform vec2 wind = vec2(1.6, 0.7);
uniform float sway = 0.0;
uniform vec2 size = vec2(0.016, 0.9);
uniform vec3 colour : source_color = vec3(0.6, 0.66, 0.8);
uniform float strength = 0.5;
uniform bool flakes = false;

varying float fade;

bool in_rooms(vec3 p) {
	return p.y < 13.0 && abs(p.x) < 50.0 && p.z > -54.0 && p.z < 10.0;
}

void vertex() {
	vec3 seed = MODEL_MATRIX[3].xyz;
	float rate = 0.82 + 0.36 * fract(seed.x * 7.13 + seed.z * 3.71);
	vec3 p = seed;
	p.y -= fall_speed * rate * TIME;
	p.xz += wind * TIME;
	p.xz += vec2(sin(TIME * 0.9 + seed.y * 1.7), cos(TIME * 0.7 + seed.z * 1.3)) * sway;
	vec3 eye = CAMERA_POSITION_WORLD;
	vec3 rel = mod(p - eye + box * 0.5, box) - box * 0.5;
	vec3 world = eye + rel;
	vec3 along = normalize(vec3(wind.x, -fall_speed, wind.y));
	vec3 side = normalize(cross(along, normalize(rel)));
	if (flakes) {
		side = INV_VIEW_MATRIX[0].xyz;
		along = INV_VIEW_MATRIX[1].xyz;
	}
	float d = length(rel);
	fade = smoothstep(0.9, 3.2, d) * (1.0 - smoothstep(0.72, 1.0, d / (min(box.x, box.z) * 0.5)));
	if (in_rooms(world) || in_rooms(eye) || fade <= 0.0) {
		POSITION = vec4(2.0, 2.0, 2.0, 1.0);
	} else {
		POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(world + side * VERTEX.x * size.x + along * VERTEX.y * size.y, 1.0);
	}
}

void fragment() {
	float shape = flakes
			? 1.0 - smoothstep(0.12, 0.5, length(UV - 0.5))
			: (1.0 - abs(UV.y - 0.5) * 2.0) * (1.0 - abs(UV.x - 0.5) * 2.0);
	ALBEDO = mix(colour, colour * vec3(1.5, 0.42, 0.36), exterior_alarm * 0.7);
	ALPHA = shape * fade * strength;
}
