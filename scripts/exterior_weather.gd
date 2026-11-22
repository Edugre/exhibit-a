extends Node3D
## What the night is doing. The host rolls the weather at the start of every heist and tells everyone,
## so both players stand in the same storm. It only changes how the street looks and sounds: the
## guard, the timer and the puzzles don't know about it. Rain and snow are drawn by
## ext_precip.gdshader, and every outdoor material reads the same two global values.

enum Kind {CLEAR, RAIN, SNOW}

const ANY := -1
const MAX_DROPS := 3200
const DROPS_BY_LEVEL: Array[int] = [1000, 2000, 3200]    # Low, Medium, High
const OVERCAST_MOON := 0.1
const RAIN_FOG := 0.0065
const SNOW_FOG := 0.0105
const RAIN_FOG_COLOR := Color(0.1, 0.12, 0.16)
const SNOW_FOG_COLOR := Color(0.27, 0.25, 0.28)
const RAIN_SKY := Color(0.075, 0.09, 0.12)
const SNOW_SKY := Color(0.26, 0.225, 0.255)
# Cloud shuts out the sky's own light, and snow throws the street's light back up at everything
const RAIN_AMBIENT := Color(0.36, 0.42, 0.52)
const SNOW_AMBIENT := Color(0.58, 0.56, 0.66)
const RAIN_AMBIENT_ENERGY := 0.34
const SNOW_AMBIENT_ENERGY := 0.46
const WEATHER_SKY_SHARE := 0.3
const THUNDER_WAIT := Vector2(24.0, 58.0)
const THUNDER_DELAY := Vector2(0.7, 2.6)
const FLASH_ENERGY := 1.6
const INDOORS_VOLUME := -14.0

@export var environment_path: NodePath = ^"../Environment"
@export var moon_path: NodePath = ^"../Moon"
@export var life_path: NodePath = ^"../Exterior/Life"
@export var sound_path: NodePath = ^"../Exterior/Life/Sound"
@export var rain_sound_path: NodePath = ^"RainSound"
@export var wind_sound_path: NodePath = ^"WindSound"
@export var thunder_sound_path: NodePath = ^"ThunderSound"
@export var precip_shader: Shader

## The host's choice from the menu. ANY rolls the dice.
var forced: int = ANY
var kind: Kind = Kind.CLEAR

var _environment: Environment
var _moon: DirectionalLight3D
var _moon_energy: float = 0.0
var _clear_fog: float = 0.0
var _clear_fog_color: Color
var _clear_ambient: float = 0.0
var _precip: MultiMeshInstance3D
var _material: ShaderMaterial
var _box: Vector3 = Vector3.ONE
var _next_thunder: float = 0.0
var _flash: Tween


func _enter_tree() -> void:
	add_to_group("exterior_weather")


func _ready() -> void:
	_environment = (get_node(environment_path) as WorldEnvironment).environment
	_moon = get_node(moon_path) as DirectionalLight3D
	_moon_energy = _moon.light_energy
	_clear_fog = _environment.fog_density
	_clear_fog_color = _environment.fog_light_color
	_clear_ambient = _environment.ambient_light_energy
	_build_precip()
	show_weather(Kind.CLEAR)
	var quality := get_tree().get_first_node_in_group("graphics_quality")
	if quality != null:
		on_graphics_changed(quality.level)
	GameState.phase_changed.connect(_on_phase_changed)


func _process(delta: float) -> void:
	if kind == Kind.CLEAR:
		return
	var inside := _camera_indoors()
	var rain := get_node(rain_sound_path) as AudioStreamPlayer
	var wind := get_node(wind_sound_path) as AudioStreamPlayer
	var level := INDOORS_VOLUME if inside else 0.0
	rain.volume_db = move_toward(rain.volume_db, level, delta * 40.0)
	wind.volume_db = move_toward(wind.volume_db, level - 3.0, delta * 40.0)
	if kind == Kind.RAIN:
		_next_thunder -= delta
		if _next_thunder <= 0.0:
			_next_thunder = randf_range(THUNDER_WAIT.x, THUNDER_WAIT.y)
			_lightning()


## From the graphics levels: fewer drops on a weak laptop, and reflections in the puddles on High.
func on_graphics_changed(level: int) -> void:
	if _precip != null:
		var drops := DROPS_BY_LEVEL[level]
		_precip.multimesh.visible_instance_count = drops
		# Fewer drops in a smaller box, so it falls just as thickly around the camera
		_material.set_shader_parameter("box", _box * pow(float(drops) / MAX_DROPS, 1.0 / 3.0))
		_environment.ssr_enabled = kind == Kind.RAIN and level == DROPS_BY_LEVEL.size() - 1


func show_weather(new_kind: Kind) -> void:
	if _flash != null:
		_flash.kill()    # a flash still running would drag the moon back down after this
	kind = new_kind
	var rain := kind == Kind.RAIN
	var snow := kind == Kind.SNOW
	var clear := kind == Kind.CLEAR
	RenderingServer.global_shader_parameter_set("exterior_wet", 1.0 if rain else 0.0)
	RenderingServer.global_shader_parameter_set("exterior_snow", 1.0 if snow else 0.0)
	_environment.fog_density = _clear_fog if clear else (RAIN_FOG if rain else SNOW_FOG)
	_environment.fog_light_color = _clear_fog_color if clear else (RAIN_FOG_COLOR if rain else SNOW_FOG_COLOR)
	_environment.ambient_light_color = RAIN_AMBIENT if rain else SNOW_AMBIENT
	_environment.ambient_light_sky_contribution = 1.0 if clear else WEATHER_SKY_SHARE
	_environment.ambient_light_energy = _clear_ambient if clear else (RAIN_AMBIENT_ENERGY if rain else SNOW_AMBIENT_ENERGY)
	var sky := _environment.sky.sky_material as ShaderMaterial
	sky.set_shader_parameter("overcast", 0.0 if clear else 1.0)
	sky.set_shader_parameter("overcast_color", RAIN_SKY if rain else SNOW_SKY)
	_moon.light_energy = _moon_energy * (1.0 if clear else OVERCAST_MOON)
	_precip.visible = not clear
	if rain:
		_shape_precip(Vector3(26.0, 16.0, 26.0), 15.0, Vector2(1.6, 0.7), 0.0, Vector2(0.02, 0.85), Color(0.62, 0.68, 0.82), 0.3, false)
		_next_thunder = randf_range(6.0, THUNDER_WAIT.x)
	elif snow:
		_shape_precip(Vector3(30.0, 18.0, 30.0), 1.5, Vector2(0.5, 0.25), 0.55, Vector2(0.07, 0.07), Color(0.95, 0.96, 1.0), 0.8, true)
	_set_playing(rain_sound_path, rain)
	_set_playing(wind_sound_path, snow)
	_set_street_life(clear, not snow)
	var quality := get_tree().get_first_node_in_group("graphics_quality")
	if quality != null:
		on_graphics_changed(quality.level)


func _on_phase_changed(phase: GameState.Phase) -> void:
	if phase == GameState.Phase.LOBBY:
		show_weather(Kind.CLEAR)
	elif phase == GameState.Phase.PLAYING and multiplayer.is_server():
		_set_weather.rpc(forced if forced != ANY else _roll())


@rpc("authority", "call_local", "reliable")
func _set_weather(new_kind: int) -> void:
	show_weather(new_kind as Kind)


func _roll() -> Kind:
	var dice := randf()
	return Kind.CLEAR if dice < 0.4 else (Kind.RAIN if dice < 0.7 else Kind.SNOW)


func _build_precip() -> void:
	var mesh := QuadMesh.new()
	var drops := MultiMesh.new()
	drops.transform_format = MultiMesh.TRANSFORM_3D
	drops.mesh = mesh
	drops.instance_count = MAX_DROPS
	var scatter := RandomNumberGenerator.new()
	scatter.seed = 31
	for i in MAX_DROPS:
		var spot := Vector3(scatter.randf(), scatter.randf(), scatter.randf()) * 60.0
		drops.set_instance_transform(i, Transform3D(Basis.IDENTITY, spot))
	_material = ShaderMaterial.new()
	_material.shader = precip_shader
	_precip = MultiMeshInstance3D.new()
	_precip.multimesh = drops
	_precip.material_override = _material
	_precip.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_precip.custom_aabb = AABB(Vector3.ONE * -4000.0, Vector3.ONE * 8000.0)    # it always surrounds the camera
	add_child(_precip)


func _shape_precip(box: Vector3, speed: float, wind: Vector2, sway: float, size: Vector2, color: Color, strength: float, flakes: bool) -> void:
	_box = box
	_material.set_shader_parameter("fall_speed", speed)
	_material.set_shader_parameter("wind", wind)
	_material.set_shader_parameter("sway", sway)
	_material.set_shader_parameter("size", size)
	_material.set_shader_parameter("colour", color)
	_material.set_shader_parameter("strength", strength)
	_material.set_shader_parameter("flakes", flakes)


func _set_playing(path: NodePath, playing: bool) -> void:
	var sound := get_node(path) as AudioStreamPlayer
	if playing and not sound.playing:
		sound.play()
	elif not playing:
		sound.stop()


## Crickets and moths only come out on a clear night, and the fountains are shut off for a freeze.
func _set_street_life(clear: bool, fountains: bool) -> void:
	var life := get_node_or_null(life_path)
	if life == null:
		return
	for child in life.get_children():
		if child.name.begins_with("Moths"):
			child.emitting = clear
	var jets := life.get_node_or_null("FountainJets")
	if jets != null:
		jets.visible = fountains
	var sounds := get_node_or_null(sound_path)
	if sounds == null:
		return
	_keep_playing(sounds.get_node_or_null("Crickets"), clear)
	_keep_playing(sounds.get_node_or_null("FountainWest"), fountains)
	_keep_playing(sounds.get_node_or_null("FountainEast"), fountains)


func _keep_playing(sound: AudioStreamPlayer3D, playing: bool) -> void:
	if sound != null and sound.playing != playing:
		sound.playing = playing


func _lightning() -> void:
	if _camera_indoors():
		return
	if _flash != null:
		_flash.kill()
	var settled := _moon_energy * OVERCAST_MOON
	_flash = create_tween()
	_flash.tween_property(_moon, "light_energy", FLASH_ENERGY, 0.05)
	_flash.tween_property(_moon, "light_energy", settled, 0.1)
	_flash.tween_property(_moon, "light_energy", FLASH_ENERGY * 0.6, 0.05)
	_flash.tween_property(_moon, "light_energy", settled, 0.3)
	await get_tree().create_timer(randf_range(THUNDER_DELAY.x, THUNDER_DELAY.y)).timeout
	if kind == Kind.RAIN:
		(get_node(thunder_sound_path) as AudioStreamPlayer).play()


func _camera_indoors() -> bool:
	var camera := get_viewport().get_camera_3d()
	if camera == null:
		return false
	var at := camera.global_position
	return at.y < 13.0 and absf(at.x) < 50.0 and at.z > -54.0 and at.z < 10.0
