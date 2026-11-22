// The night's weather on any outdoor surface. Both values come from scripts/exterior_weather.gd.
// Snow settles on whatever faces up, so every ledge and cornice gets its own white line. Rain darkens
// the stone, and pools stand on the flat ground with rings spreading where the drops land.
global uniform float exterior_snow;
global uniform float exterior_wet;

float weather_hash(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 19571.7);
}

float weather_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(weather_hash(i), weather_hash(i + vec2(1.0, 0.0)), f.x), mix(weather_hash(i + vec2(0.0, 1.0)), weather_hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

// The door passages and the rooms stay dry
bool weather_sheltered(vec3 p) {
	return p.y < 11.0 && abs(p.x) < 50.0 && p.z > -54.0 && p.z < 10.2;
}

void apply_weather(vec3 p, vec3 n, float cover_scale, inout vec3 albedo, inout float rough, inout float specular) {
	if (exterior_snow + exterior_wet <= 0.0 || weather_sheltered(p)) {
		return;
	}
	if (exterior_snow > 0.0) {
		float drift = weather_noise(p.xz * 1.3) * 0.6 + weather_noise(p.xz * 4.1) * 0.4;
		float cover = smoothstep(0.34, 0.66, n.y - (drift - 0.5) * 0.4) * exterior_snow * cover_scale;
		albedo = mix(albedo, vec3(0.8, 0.83, 0.9) * (0.92 + 0.14 * drift), cover);
		rough = mix(rough, 0.86, cover);
		specular = mix(specular, 0.22, cover);
	}
	if (exterior_wet > 0.0) {
		float flat_ground = smoothstep(0.5, 0.92, n.y);
		albedo *= mix(1.0, 0.56, exterior_wet);
		rough = mix(rough, 0.24, exterior_wet * flat_ground);
		specular = mix(specular, 0.55, exterior_wet * flat_ground);
		float pool = weather_noise(p.xz * 0.21) * 0.62 + weather_noise(p.xz * 0.93) * 0.38;
		pool = smoothstep(0.52, 0.6, pool) * smoothstep(0.97, 0.995, n.y) * exterior_wet;
		albedo = mix(albedo, albedo * 0.42, pool);
		rough = mix(rough, 0.05, pool);
		specular = mix(specular, 0.8, pool);
	}
}

// Rings from the rain, as a small tilt of the world-space normal. Left out of the Low level.
vec3 weather_ripple(vec3 p, vec3 n, float now) {
	if (exterior_wet <= 0.0 || n.y < 0.97 || weather_sheltered(p)) {
		return n;
	}
	vec2 q = p.xz * 3.0;
	vec2 cell = floor(q);
	float seed = weather_hash(cell);
	float age = fract(now * 1.3 + seed * 7.0);
	vec2 from_centre = fract(q) - 0.5 - (vec2(seed, weather_hash(cell + 3.1)) - 0.5) * 0.5;
	float l = length(from_centre) + 0.0001;
	float ring = abs(l - age * 0.5);
	float wave = sin(ring * 90.0) * (1.0 - smoothstep(0.0, 0.05, ring)) * (1.0 - age);
	return normalize(n + vec3(from_centre.x, 0.0, from_centre.y) / l * wave * 0.32 * exterior_wet);
}
