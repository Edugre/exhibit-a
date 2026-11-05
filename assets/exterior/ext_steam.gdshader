// A soft puff of steam, always facing the camera. It fades in, thins as it rises, and takes on whatever
// light is around it, so a manhole's plume glows under a street lamp and is barely there in the dark.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform float density = 0.26;

varying float age;

void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	float size = length(MODEL_MATRIX[0].xyz);
	age = clamp(INSTANCE_CUSTOM.y, 0.0, 1.0);
	float grow = (0.7 + age * 2.0) * size;
	VERTEX *= grow;
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}

void fragment() {
	vec2 q = UV * 2.0 - 1.0;
	float puff = 1.0 - smoothstep(0.1, 1.0, length(q));
	ALBEDO = vec3(0.75, 0.77, 0.8);
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
	ALPHA = puff * density * smoothstep(0.0, 0.12, age) * (1.0 - age);
}
