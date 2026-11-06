extends Node
## Graphics levels, so the game runs on a weak laptop and still looks its best on a strong PC.
## Each machine picks its own level the first time, from its kind of GPU, and steps down by itself if
## the frame rate stays low. A choice made in the menu is saved and wins from then on.
## Only how things are drawn changes here. No level touches game state, so peers can differ.

enum Level { LOW, MEDIUM, HIGH }

const SETTINGS_PATH := "user://graphics.cfg"
const AUTO := -1
const MATERIAL_FOLDER := "res://assets/exterior/"
const CHEAP_MATERIALS: Array[String] = ["ext_stone", "ext_shaft", "ext_ashlar", "ext_rough", "ext_granite", "ext_riser", "ext_paving", "ext_context", "ext_context_dark", "ext_wing_wall", "ext_wing_trim", "ext_carved", "ext_trim", "ext_relief", "ext_plaza", "ext_banner", "ext_door"]
## Lights replaced by the baked light on the front at LOW.
const BAKED_LIGHTS: Array[String] = ["Flood", "Graze", "ArchGraze", "EndBay", "Crest"]
## The only lights that keep their shadows at MEDIUM.
const SHADOW_LIGHTS_MEDIUM: Array[String] = ["Flood", "WindowStar"]
## LOW draws the 3D at about this many lines whatever the screen, and scales up, so a 1080p laptop isn't punished.
const LOW_RENDER_LINES := 620.0
## Automatic stepping down: ignore the slow first moments, then how slow, for how long.
const SETTLE_TIME := 3.0
const SLOW_FRAME_MS := 30.0
const SLOW_TIME := 3.0
## Windows calls many built-in GPUs "discrete", so the first guess goes by name. Strong names are checked first.
const STRONG_GPU_WORDS: Array[String] = ["rtx", "gtx", "radeon rx", "radeon pro", "arc(tm)"]
const WEAK_GPU_WORDS: Array[String] = ["intel", "radeon(tm) graphics", "radeon graphics", "vega", " mx", "microsoft", "llvmpipe", "swiftshader", "parsec"]

@export var environment_node: NodePath = ^"../Environment"
@export var moon_node: NodePath = ^"../Moon"
@export var lights_node: NodePath = ^"../Exterior/Lights"
@export var life_node: NodePath = ^"../Exterior/Life"

var level: Level = Level.HIGH
var choice: int = AUTO

var _shadowed: Array[Light3D] = []
var _settling: float = SETTLE_TIME
var _slow_time: float = 0.0
var _frames: int = 0
var _frame_total: float = 0.0


func _ready() -> void:
	add_to_group("graphics_quality")
	for light: Light3D in _all_lights():
		if light.shadow_enabled:
			_shadowed.append(light)
	var saved := ConfigFile.new()
	if saved.load(SETTINGS_PATH) == OK:
		choice = saved.get_value("graphics", "choice", AUTO)
	apply(choice if choice != AUTO else _best_guess())


func _process(delta: float) -> void:
	if choice != AUTO or level == Level.LOW:
		return
	if _settling > 0.0:
		_settling -= delta
		return
	_frames += 1
	_frame_total += delta
	if _frame_total < 1.0:
		return
	var average_ms := _frame_total / _frames * 1000.0
	_slow_time = _slow_time + _frame_total if average_ms > SLOW_FRAME_MS else 0.0
	_frames = 0
	_frame_total = 0.0
	if _slow_time >= SLOW_TIME:
		_slow_time = 0.0
		_settling = SETTLE_TIME
		apply(level - 1)


## From the menu: a level, or AUTO to let the game decide again. Saved for next time.
func choose(new_choice: int) -> void:
	choice = new_choice
	var saved := ConfigFile.new()
	saved.set_value("graphics", "choice", choice)
	saved.save(SETTINGS_PATH)
	apply(choice if choice != AUTO else _best_guess())


func apply(new_level: int) -> void:
	level = new_level as Level
	var view := get_viewport()
	var environment: Environment = (get_node(environment_node) as WorldEnvironment).environment
	var moon := get_node(moon_node) as DirectionalLight3D
	var low := level == Level.LOW
	var high := level == Level.HIGH
	view.msaa_3d = Viewport.MSAA_4X if high else (Viewport.MSAA_2X if not low else Viewport.MSAA_DISABLED)
	view.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if low else Viewport.SCREEN_SPACE_AA_DISABLED
	view.use_debanding = true
	view.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if low else Viewport.SCALING_3D_MODE_BILINEAR
	var lines := float(DisplayServer.window_get_size().y)
	view.scaling_3d_scale = clampf(LOW_RENDER_LINES / lines, 0.5, 0.9) if low else (0.88 if not high else 1.0)
	view.positional_shadow_atlas_size = 1024 if low else (2048 if not high else 4096)
	environment.ssao_enabled = high
	moon.shadow_enabled = not low
	moon.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL if not high else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	moon.directional_shadow_max_distance = 120.0 if not high else 260.0
	RenderingServer.directional_shadow_atlas_set_size(1024 if not high else 4096, true)
	for light in _shadowed:
		light.shadow_enabled = high or (level == Level.MEDIUM and _named(light, SHADOW_LIGHTS_MEDIUM))
	for light: Light3D in _all_lights():
		light.visible = not (low and (_named(light, BAKED_LIGHTS) or light.name.begins_with("WindowStar")))
	for path in CHEAP_MATERIALS:
		var material := load(MATERIAL_FOLDER + path + ".tres") as ShaderMaterial
		material.set_shader_parameter("low_detail", low)
	var life := get_node_or_null(life_node)
	if life != null:
		for child in life.get_children():
			if child is GPUParticles3D:
				child.amount_ratio = 0.35 if low else 1.0
		var steam := life.get_node_or_null("Steam")
		if steam != null:
			steam.visible = not low


func _named(light: Light3D, groups: Array[String]) -> bool:
	for group in groups:
		if light.name.begins_with(group):
			return true
	return false


func _all_lights() -> Array[Node]:
	var lights := get_node_or_null(lights_node)
	return lights.get_children() if lights != null else []


## A first guess from the GPU's name. Stepping down afterwards corrects a wrong one.
func _best_guess() -> int:
	var gpu := RenderingServer.get_video_adapter_name().to_lower()
	for word in STRONG_GPU_WORDS:
		if gpu.contains(word):
			return Level.HIGH
	for word in WEAK_GPU_WORDS:
		if gpu.contains(word):
			return Level.LOW
	return Level.MEDIUM
