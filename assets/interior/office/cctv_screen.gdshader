// The Security Office's CCTV screens (asset P5.2). The feeds are pictures in the office texture, laid out
// in a grid of cells; this keeps them moving without any extra rendering:
//   - the five live cameras take turns: every so often each screen cuts to the next camera, through a
//     moment of static, each screen at its own moment;
//   - the camera that's out stays out, all static;
//   - the desk's vault feed and the night log stay put;
//   - every screen gets grain, scan lines and a slow bright band rolling down it.
// Cosmetic, local to each peer. make_office_art.py fills in where the cells are.
shader_type spatial;
render_mode specular_schlick_ggx;

uniform sampler2D feeds : source_color, filter_linear_mipmap, repeat_disable;
uniform vec2 cell_origin;            // top-left of the first feed, in UV
uniform vec2 cell_stride;            // from one feed to the next, across and down
uniform vec2 cell_size;              // one feed's picture
uniform vec2 dead_cell = vec2(2.0, 1.0);
uniform float live_cameras = 5.0;    // the first this many cells, row by row (three to a row), take turns
uniform float switch_every = 7.0;
uniform float glow = 1.6;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

vec2 cell_of(float index) {
	return vec2(mod(index, 3.0), floor(index / 3.0));
}

void fragment() {
	vec2 uv = UV;
	vec2 rel = (uv - cell_origin) / cell_stride;
	vec2 cell = floor(rel);
	vec2 inside = (rel - cell) * cell_stride;
	vec3 col = texture(feeds, uv).rgb;
	bool on_screen = cell.x >= 0.0 && cell.y >= 0.0 && cell.y < 2.0 && cell.x < 5.0
		&& inside.x < cell_size.x && inside.y < cell_size.y;
	if (on_screen) {
		vec2 pixel = floor(inside / cell_size * vec2(80.0, 60.0));
		float grain = hash(pixel + floor(TIME * 18.0));
		float noise_amount = 0.07;
		float index = cell.y * 3.0 + cell.x;
		if (cell.y < 1.5 && index < live_cameras && cell.x < 3.0) {
			float phase = hash(vec2(index, 7.0)) * switch_every;
			float turn = floor((TIME + phase) / switch_every);
			float shown = mod(index + turn, live_cameras);
			col = texture(feeds, cell_origin + cell_of(shown) * cell_stride + inside).rgb;
			float since = mod(TIME + phase, switch_every);
			noise_amount = max(noise_amount, 1.0 - smoothstep(0.0, 0.35, since));
		}
		if (abs(cell.x - dead_cell.x) < 0.5 && abs(cell.y - dead_cell.y) < 0.5) {
			noise_amount = 0.85;
		}
		float v = inside.y / cell_size.y;
		float lines = 0.86 + 0.14 * sin(v * 3.14159 * 120.0);
		float band = exp(-pow((fract(v - TIME * 0.11) - 0.5) / 0.06, 2.0));
		col = mix(col, vec3(grain * 0.9), noise_amount) * lines * (1.0 + 0.18 * band);
	}
	ALBEDO = col * 0.15;
	EMISSION = col * glow;
	ROUGHNESS = 0.15;
}
