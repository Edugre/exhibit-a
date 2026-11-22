// Street furniture and the cars: one painted atlas with a glow map, under whatever the night is doing,
// so taxis and carts pick up snow on their roofs and go dark and glossy in the rain.
shader_type spatial;

#include "res://assets/exterior/ext_weather.gdshaderinc"

uniform sampler2D paint : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D glow : source_color, hint_default_black, filter_linear_mipmap;
uniform float glow_strength = 1.7;

varying vec3 world_pos;
varying vec3 world_nor;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 colour = texture(paint, UV).rgb;
	float rough = 0.62;
	float specular = 0.35;
	apply_weather(world_pos, normalize(world_nor), 1.0, colour, rough, specular);
	ALBEDO = colour;
	ROUGHNESS = rough;
	SPECULAR = specular;
	EMISSION = texture(glow, UV).rgb * glow_strength;
}
