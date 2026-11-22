// Fifth Avenue's surface. Asphalt with stone speckle and old patches, a little smoother and darker
// along the lanes where the tyres run. With paint on, it is the road markings, worn through in places.
shader_type spatial;

#include "res://assets/exterior/ext_weather.gdshaderinc"

uniform vec3 asphalt : source_color = vec3(0.37, 0.37, 0.395);
uniform vec3 paint : source_color = vec3(0.74, 0.73, 0.69);
uniform bool painted = false;
uniform float lane_width = 3.66;
uniform float curb_z = 35.0;

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

float cloud(vec2 p) {
	return value_noise(p) * 0.55 + value_noise(p * 2.1 + 7.3) * 0.3 + value_noise(p * 4.3 + 2.1) * 0.15;
}

void fragment() {
	vec2 p = world_position.xz;
	float speckle = value_noise(p * 11.0) * 0.5 + value_noise(p * 29.0) * 0.5;
	float patches = smoothstep(0.42, 0.62, cloud(p * vec2(0.09, 0.22)));
	float k = fract((p.y - curb_z) / lane_width);
	float left_wheel = (k - 0.28) / 0.1;
	float right_wheel = (k - 0.72) / 0.1;
	float tracks = exp(-left_wheel * left_wheel) + exp(-right_wheel * right_wheel);
	vec3 road = asphalt * (0.78 + 0.44 * speckle) * mix(1.0, 0.8, patches) * (1.0 - 0.14 * tracks);
	float rough = mix(0.82, 0.58, tracks * 0.8) - patches * 0.05;
	vec3 up = vec3(0.0, 1.0, 0.0);
	float specular = 0.42;
	if (painted) {
		float worn = cloud(p * vec2(0.9, 2.1)) * 0.7 + value_noise(p * 7.0) * 0.2 + speckle * 0.3;
		float left = smoothstep(0.26, 0.6, worn);
		road = mix(road, paint * (0.85 + 0.3 * speckle), left * 0.92);
		rough = mix(rough, 0.7, left);
	}
	// Traffic keeps the wheel tracks clear of snow, so the road goes to dirty slush between them
	apply_weather(world_position, up, 0.86 * (1.0 - min(tracks, 1.0) * 0.75), road, rough, specular);
	ALBEDO = road;
	ROUGHNESS = rough;
	SPECULAR = specular;
	NORMAL = normalize((VIEW_MATRIX * vec4(weather_ripple(world_position, up, TIME), 0.0)).xyz);
}
