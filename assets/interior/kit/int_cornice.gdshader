// The carved band under every ceiling: the exterior's moulding strip (egg-and-dart, beads, leaves and
// rosettes), so the inside matches the front. It's laid on by world height, so a plain CSG box placed
// between band_bottom and band_top (int_dims.py CORNICE_Y0 and CORNICE_Y1) shows the full carving with
// no UVs. Faces looking up or down get plain plaster.
shader_type spatial;

uniform sampler2D plaster_map : source_color, hint_default_white, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D carved_normal : hint_normal, repeat_enable, filter_linear_mipmap_anisotropic;
uniform sampler2D carved_ao : hint_default_white, repeat_enable, filter_linear_mipmap_anisotropic;
uniform vec3 tint : source_color = vec3(1.0);
uniform float band_bottom = 3.64;
uniform float band_top = 4.0;
// Keep the carving's proportions: metres_per_repeat = band height / v_range
uniform float metres_per_repeat = 0.514;
uniform float v_range = 0.70;
uniform float normal_depth = 1.0;
uniform float recess_shade = 0.35;

varying vec3 world_pos;
varying vec3 world_nor;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(world_nor);
	vec3 albedo = texture(plaster_map, world_pos.xz * 0.4 + world_pos.y * 0.4).rgb * tint;
	vec3 wn = n;
	float ao = 1.0;
	if (abs(n.y) < 0.5) {
		// Along the wall to the viewer's right, and down the band, so the carving reads the right way up
		vec3 along = normalize(cross(vec3(0.0, 1.0, 0.0), n));
		float u = dot(world_pos, along) / metres_per_repeat;
		float v = clamp((band_top - world_pos.y) / (band_top - band_bottom), 0.0, 1.0) * v_range;
		vec2 uv = vec2(u, v);
		vec3 t = vec3(texture(carved_normal, uv).xy * 2.0 - 1.0, 0.0);
		t.z = sqrt(max(1.0 - dot(t.xy, t.xy), 0.0));
		t.xy *= normal_depth;
		wn = normalize(along * t.x + vec3(0.0, 1.0, 0.0) * t.y + n * t.z);
		vec2 a = texture(carved_ao, uv).rg;
		ao = a.r;
		albedo *= mix(1.0, a.g, recess_shade);
	}
	ALBEDO = albedo;
	ROUGHNESS = 0.82;
	SPECULAR = 0.3;
	AO = ao;
	AO_LIGHT_AFFECT = 0.4;
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
}
