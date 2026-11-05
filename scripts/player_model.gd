extends Node3D
## The visible player character: one body for everyone, tinted by an accent colour.
## Cosmetic only. Every variant shares the same mesh, silhouette and size, and this
## script holds no game state, so a colour can never give a player an advantage.

const BLEND_TIME := 0.25

## Metres one loop of the walk clip covers. Playback follows speed so planted feet don't slide.
const WALK_STRIDE := 1.6
## Two thresholds, so a speed hovering near one value can't flicker between idle and walk.
const WALK_START_SPEED := 0.6
const WALK_STOP_SPEED := 0.3
const SPEED_SMOOTHING := 12.0
## Nobody covers this far on foot in one tick, so a jump this big is a respawn, not a step.
const TELEPORT_DISTANCE := 1.0

## All eight share the same perceived lightness, so no colour is easier to spot than another.
## The host hands these out in order, so neighbours in this list should look the most
## different: the first two players get the red and blue beanies.
const ACCENT_COLORS: Array[Color] = [
	Color(0.777, 0.399, 0.355),  # brick
	Color(0.224, 0.551, 0.800),  # slate
	Color(0.632, 0.513, 0.032),  # mustard
	Color(0.549, 0.460, 0.788),  # violet
	Color(0.002, 0.605, 0.582),  # teal
	Color(0.748, 0.437, 0.199),  # rust
	Color(0.392, 0.590, 0.272),  # moss
	Color(0.741, 0.393, 0.567),  # rose
]

## Index into ACCENT_COLORS.
@export_range(0, 7) var variant: int = 0:
	set(value):
		variant = posmod(value, ACCENT_COLORS.size())
		_apply_variant()

## Holds the arms up, standing or walking. The carried object belongs on the carry_socket bone.
@export var carrying: bool = false:
	set(value):
		carrying = value
		_apply_pose()

var _accent_material: BaseMaterial3D
var _animation_player: AnimationPlayer
var _last_position: Vector3
var _speed: float = 0.0
var _walking: bool = false


func _ready() -> void:
	var accent_mesh := find_child("PlayerAccent", true, false) as MeshInstance3D
	_accent_material = accent_mesh.get_active_material(0).duplicate() as BaseMaterial3D
	accent_mesh.set_surface_override_material(0, _accent_material)

	_animation_player = find_child("AnimationPlayer", true, false) as AnimationPlayer
	for clip: StringName in [&"idle", &"walk", &"carry", &"carry_walk"]:
		_animation_player.get_animation(clip).loop_mode = Animation.LOOP_LINEAR

	_last_position = global_position
	_apply_variant()
	_apply_pose()


func _physics_process(delta: float) -> void:
	if not is_visible_in_tree():
		return

	# Speed comes from the position every peer already receives, so a teammate
	# animates correctly with no extra network traffic.
	var moved := global_position - _last_position
	_last_position = global_position
	moved.y = 0.0
	var step := moved.length() if moved.length() < TELEPORT_DISTANCE else 0.0
	_speed = lerpf(_speed, step / delta, 1.0 - exp(-SPEED_SMOOTHING * delta))

	var walking := _speed > (WALK_STOP_SPEED if _walking else WALK_START_SPEED)
	if walking != _walking:
		_walking = walking
		_apply_pose()
	_animation_player.speed_scale = _speed / WALK_STRIDE if _walking else 1.0


func _apply_variant() -> void:
	if _accent_material:
		_accent_material.albedo_color = ACCENT_COLORS[variant]


func _apply_pose() -> void:
	if not _animation_player:
		return
	if carrying:
		_animation_player.play(&"carry_walk" if _walking else &"carry", BLEND_TIME)
	else:
		_animation_player.play(&"walk" if _walking else &"idle", BLEND_TIME)
