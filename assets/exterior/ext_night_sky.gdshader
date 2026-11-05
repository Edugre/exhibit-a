// A clear blue night, drawn entirely in code: gradient, stars, moon, and the warm glow of the city
// low on the horizon behind the street.
shader_type sky;

uniform vec3 zenith_color : source_color = vec3(0.075, 0.125, 0.30);
uniform vec3 horizon_color : source_color = vec3(0.20, 0.30, 0.52);
uniform vec3 city_glow : source_color = vec3(0.34, 0.17, 0.085);
uniform vec3 moon_direction = vec3(-0.35, 0.72, -0.6);
uniform float star_density = 0.0016;
uniform float star_energy = 1.3;

float hash31(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.zyx + 31.32);
	return fract((p.x + p.y) * p.z);
}

void sky() {
	vec3 d = normalize(EYEDIR);
	float h = max(d.y, 0.0);
	vec3 c = mix(horizon_color, zenith_color, pow(h, 0.55));
	// The city lies to the south, behind the street
	float south = 0.5 + 0.5 * dot(normalize(d.xz + vec2(0.0001)), vec2(0.0, 1.0));
	c += city_glow * exp(-h * 11.0) * (0.35 + 0.65 * south);
	if (AT_CUBEMAP_PASS) {
		COLOR = c;
	} else {
		// Stars: a jittered point in each cell of a fine grid on the sphere
		vec3 cell = floor(d * 420.0);
		float r = hash31(cell);
		if (r < star_density && d.y > 0.02) {
			vec3 spot = (cell + vec3(hash31(cell + 1.0), hash31(cell + 2.0), hash31(cell + 3.0))) / 420.0;
			float near = 1.0 - smoothstep(0.0, 0.0016, distance(normalize(spot), d));
			float bright = pow(hash31(cell + 4.0), 5.0) * 2.6 + 0.2;
			c += vec3(0.85, 0.92, 1.0) * near * bright * star_energy * smoothstep(0.02, 0.22, d.y);
		}
		vec3 m = normalize(moon_direction);
		float a = dot(d, m);
		c += vec3(1.0, 0.97, 0.9) * smoothstep(0.99993, 0.99996, a) * 1.9;
		c += vec3(0.5, 0.6, 0.85) * pow(max(a, 0.0), 1400.0) * 0.08;
		COLOR = c;
	}
}
