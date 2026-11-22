class_name TrojanVan
extends Node3D
## The getaway van, wearing a plywood horse. Cosmetic only: it reads the heist phase every
## peer already receives and plays the same escape on each screen, with no network traffic.
## The win belongs to GameState; this just shows it.

## How long the whole getaway plays. The HUD waits this long before showing the end screen.
const SCENE_TIME := 6.6

const SLAM_TIME := 1.0
const COUGH_TIME := 1.4
const DRIVE_TIME := 4.2
const DRIVE_DISTANCE := 80.0
const DRIVE_SPEED_SCALE := 1.5

## The bay light glows brighter while someone's carrying the artifact.
const BAY_ENERGY_CALM := 1.1
const BAY_ENERGY_CARRIED := 2.4

const CAMERA_FOLLOW_SPEED := 5.0
const CAMERA_AIM_HEIGHT := 2.0

var _start: Vector3
var _sequence: Tween
var _return_camera: Camera3D
var _aim: Vector3

@onready var animation: AnimationPlayer = find_child("AnimationPlayer", true, false)
@onready var body: StaticBody3D = $Body
@onready var shell_shape: CollisionShape3D = $Body/Shell
@onready var ramp_shape: CollisionShape3D = $Body/Ramp
@onready var exhaust: GPUParticles3D = $Exhaust
@onready var bay_light: OmniLight3D = $BayLight
@onready var win_camera: Camera3D = $"../GetawayCamera"


func _ready() -> void:
	_start = position
	for looping: StringName in [&"van_idle", &"van_drive"]:
		animation.get_animation(looping).loop_mode = Animation.LOOP_LINEAR
	GameState.phase_changed.connect(_on_phase_changed)
	_reset()


func _process(delta: float) -> void:
	bay_light.light_energy = BAY_ENERGY_CARRIED if GameState.artifact_state == GameState.ArtifactState.CARRIED else BAY_ENERGY_CALM
	if not win_camera.current:
		return
	# A little lag, so the van isn't pinned to the middle of the frame.
	var target := global_position + Vector3.UP * CAMERA_AIM_HEIGHT
	_aim = _aim.lerp(target, 1.0 - exp(-CAMERA_FOLLOW_SPEED * delta))
	win_camera.look_at(_aim)


func _on_phase_changed(phase: GameState.Phase) -> void:
	if phase == GameState.Phase.WON:
		_get_away()
	else:
		_reset()


func _get_away() -> void:
	_return_camera = get_viewport().get_camera_3d()
	_aim = global_position + Vector3.UP * CAMERA_AIM_HEIGHT
	win_camera.make_current()
	animation.play(&"van_slam", 0.05)
	_sequence = create_tween()
	_sequence.tween_interval(SLAM_TIME)
	_sequence.tween_callback(_cough)
	_sequence.tween_interval(COUGH_TIME)
	_sequence.tween_callback(_gallop)
	_sequence.tween_property(self, "position:x", _start.x + DRIVE_DISTANCE, DRIVE_TIME) \
			.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)


func _cough() -> void:
	animation.play(&"van_cough", 0.05)
	exhaust.emitting = true


func _gallop() -> void:
	animation.play(&"van_drive", 0.1)
	animation.speed_scale = DRIVE_SPEED_SCALE
	# Nobody should be able to stand in a van-shaped hole in the air.
	shell_shape.set_deferred("disabled", true)
	ramp_shape.set_deferred("disabled", true)


func _reset() -> void:
	if _sequence:
		_sequence.kill()
	position = _start
	animation.speed_scale = 1.0
	animation.play(&"van_idle", 0.1)
	exhaust.emitting = false
	shell_shape.set_deferred("disabled", false)
	ramp_shape.set_deferred("disabled", false)
	if win_camera.current and is_instance_valid(_return_camera):
		_return_camera.make_current()
