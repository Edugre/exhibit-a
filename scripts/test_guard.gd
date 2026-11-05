extends Node3D
## TEST ONLY: walks the guard through every clip so the team can see her in the museum.
## This is not guard AI. She makes no decisions, can't see or catch anyone, has no collision
## and isn't synced: each peer plays its own copy of this loop, which starts with the heist.
## To remove her, delete this script, scenes/test_guard.tscn and the TestGuard node in main.tscn.

const GuardModel := preload("res://scripts/guard_model.gd")

const TURN_SPEED := 6.0
const PATROL_SPEED := 1.8
const CHASE_SPEED := 6.5
const PLAYER_SPAWNS := Vector3(0.0, 0.0, 7.5)
const GALLERY_CENTRE := Vector3(0.0, 0.0, -2.6)  # in sight of the spawns, through the gallery door
const DOORWAY := Vector3(0.0, 0.0, 4.6)

## Each step either walks to "to" at "speed", or waits for "wait" seconds facing "face".
var _steps: Array[Dictionary] = []
var _start: Vector3
var _step_index: int = -1
var _time_left: float = 0.0
var _running: bool = false

@onready var model: Node3D = $Model
@onready var waypoints: Node3D = $"../Museum/GuardWaypoints"


func _ready() -> void:
	var route: Array[Vector3] = []
	for marker: Node3D in waypoints.get_children():
		route.append(marker.global_position)
	_start = route[0]
	_steps = [
		{"state": GuardModel.State.PATROL, "to": route[1], "speed": PATROL_SPEED},
		{"state": GuardModel.State.PATROL, "to": GALLERY_CENTRE, "speed": PATROL_SPEED},
		{"state": GuardModel.State.IDLE, "wait": 1.0, "face": PLAYER_SPAWNS},
		{"state": GuardModel.State.SHUSH, "wait": 2.2, "face": PLAYER_SPAWNS},
		{"state": GuardModel.State.IDLE, "wait": 0.6, "face": PLAYER_SPAWNS},
		{"state": GuardModel.State.ALERT, "wait": 1.4, "face": PLAYER_SPAWNS},
		{"state": GuardModel.State.CHASE, "to": DOORWAY, "speed": CHASE_SPEED},
		{"state": GuardModel.State.TACKLE, "wait": 2.0, "face": PLAYER_SPAWNS},
		{"state": GuardModel.State.IDLE, "wait": 1.0, "face": PLAYER_SPAWNS},
		{"state": GuardModel.State.PATROL, "to": route[2], "speed": PATROL_SPEED},
		{"state": GuardModel.State.PATROL, "to": route[3], "speed": PATROL_SPEED},
		{"state": GuardModel.State.PATROL, "to": route[0], "speed": PATROL_SPEED},
	]
	position = _start
	GameState.phase_changed.connect(_on_phase_changed)
	_on_phase_changed(GameState.phase)


func _on_phase_changed(phase: GameState.Phase) -> void:
	_running = phase == GameState.Phase.PLAYING
	if _running:
		position = _start
		_step_index = -1
		_next_step()
	else:
		model.state = GuardModel.State.IDLE


func _physics_process(delta: float) -> void:
	if not _running:
		return
	var step: Dictionary = _steps[_step_index]
	if step.has("to"):
		_walk_toward(step["to"], step["speed"] * delta, delta)
	else:
		_turn_toward(step["face"], delta)
		_time_left -= delta
		if _time_left <= 0.0:
			_next_step()


func _walk_toward(target: Vector3, travel: float, delta: float) -> void:
	var offset := target - position
	if offset.length() <= travel:
		position = target
		_next_step()
		return
	position += offset.normalized() * travel
	_turn_toward(target, delta)


func _turn_toward(point: Vector3, delta: float) -> void:
	var offset := point - position
	if offset.length_squared() < 0.01:
		return
	var yaw := atan2(-offset.x, -offset.z)  # she faces -Z
	rotation.y = lerp_angle(rotation.y, yaw, 1.0 - exp(-TURN_SPEED * delta))


func _next_step() -> void:
	_step_index = (_step_index + 1) % _steps.size()
	var step: Dictionary = _steps[_step_index]
	model.state = step["state"]
	_time_left = step.get("wait", 0.0)
