// A grey city pigeon. The script hands each bird its flap speed through the instance's custom data, so
// the wings are moved here and a whole flock costs one draw call. UV.x is how far out along a wing a
// point sits, and the folded wing is simply that same wing pulled in along the back.
shader_type spatial;

uniform vec3 back_colour : source_color = vec3(0.30, 0.32, 0.36);
uniform vec3 neck_colour : source_color = vec3(0.13, 0.25, 0.26);

varying float along_body;
varying float height;
varying float crowned;

void vertex() {
	along_body = VERTEX.z;
	height = VERTEX.y;
	crowned = INSTANCE_CUSTOM.z;
	float flap = INSTANCE_CUSTOM.x;
	float phase = INSTANCE_CUSTOM.y;
	float wing = UV.x;
	if (flap > 0.01) {
		VERTEX.y += wing * 0.20 * sin(TIME * 34.0 + phase) * flap;
	} else {
		VERTEX.x *= 1.0 - wing * 0.82;
		VERTEX.z -= wing * 0.12;
	}
}

void fragment() {
	float neck = smoothstep(0.05, 0.11, along_body);
	ALBEDO = mix(back_colour, neck_colour, neck) * (0.85 + 0.25 * UV.x);
	ROUGHNESS = 0.8;
	SPECULAR = 0.2;
	// One bird in the flock knows who it is
	if (crowned > 0.5 && along_body > 0.08 && height > 0.268 && height < 0.288) {
		ALBEDO = vec3(0.86, 0.62, 0.16);
		EMISSION = vec3(0.42, 0.29, 0.06);
		METALLIC = 1.0;
		ROUGHNESS = 0.3;
	}
}
