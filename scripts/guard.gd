class_name Guard
extends CharacterBody3D
## Museum guard. Every decision runs on the host; the MultiplayerSynchronizer
## copies position, rotation, `alerted` and `model_state` to the client.
##
## PATROL      walk the GuardWaypoints loop, pausing at each one
## INVESTIGATE walk to a point (a noise, or where a player was last seen), look around
## CHASE       a player was seen long enough: follow them; catching one ends the heist
## CAUGHT      she tackled a player; nothing more happens until the next heist

enum State { PATROL, INVESTIGATE, CHASE, CAUGHT }

const GuardModel := preload("res://scripts/guard_model.gd")

const PATROL_SPEED := 2.0
const INVESTIGATE_SPEED := 3.0
const CHASE_SPEED := 4.5          # slower than walking (5), faster than sneaking (2.5)
const TURN_SPEED := 6.0
## She moves on physics steps. Her model glides between them, so she doesn't stutter on a fast screen.
const GLIDE_SPEED := 22.0
const SNAP_DISTANCE := 3.0

# Spotting uses the beam players can see, so those numbers live with the beam.
const VIEW_DISTANCE := GuardModel.BEAM_RANGE
const VIEW_HALF_ANGLE := GuardModel.BEAM_ANGLE
# No beam shows during a chase, so she can keep track of a player beyond it.
const CHASE_VIEW_DISTANCE := 12.0
const CHASE_VIEW_HALF_ANGLE := 35.0
const DETECT_TIME := 0.6          # seconds of continuous sight before a chase starts
const LOSE_SIGHT_TIME := 2.0      # seconds out of sight before the guard gives up
const CATCH_DISTANCE := 1.2
const PATROL_PAUSE := 1.0
const LOOK_AROUND_TIME := 3.0
const LOOK_AROUND_SPEED := 1.5    # radians per second while searching

const CALM_LIGHT := Color(1.0, 0.93, 0.74)
const ALERT_LIGHT := Color(1.0, 0.2, 0.2)

@export var waypoints_path: NodePath = ^"../Museum/GuardWaypoints"

## Replicated to the client so its flashlight turns red during a chase.
@export var alerted := false:
	set(value):
		alerted = value
		if is_node_ready():
			flashlight.light_color = ALERT_LIGHT if alerted else CALM_LIGHT

## The clip she shows. The host picks it from what she's doing; every peer plays it.
@export var model_state: GuardModel.State = GuardModel.State.IDLE:
	set(value):
		if value == model_state:
			return  # replaying a clip that holds its last frame would restart it
		model_state = value
		if is_node_ready():
			model.state = value

@onready var agent: NavigationAgent3D = $NavigationAgent3D
@onready var eyes: Node3D = $Eyes
@onready var model: GuardModel = $Model
@onready var flashlight: SpotLight3D = model.flashlight

var state := State.PATROL
var _model_at := Vector3.ZERO
var _waypoints: Array[Vector3] = []
var _waypoint_index := 0
var _wait_timer := 0.0
var _suspicion := 0.0
var _target: Node3D = null
var _last_seen := Vector3.ZERO
var _lost_sight_timer := 0.0
var _start_transform: Transform3D


func _ready() -> void:
	add_to_group("guards")
	_start_transform = global_transform
	for marker in get_node(waypoints_path).get_children():
		_waypoints.append((marker as Node3D).global_position)
	flashlight.light_color = CALM_LIGHT
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _process(delta: float) -> void:
	_model_at = _model_at.lerp(global_position, 1.0 - exp(-GLIDE_SPEED * delta))
	if _model_at.distance_to(global_position) > SNAP_DISTANCE:
		_model_at = global_position
	model.global_position = _model_at


func _physics_process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	if GameState.phase != GameState.Phase.PLAYING:
		if state != State.CAUGHT:
			model_state = GuardModel.State.IDLE  # the tackle holds; anything else stands still
		return

	var seen := _find_visible_player()

	# Seeing a player builds suspicion; a full meter starts a chase.
	if state != State.CHASE:
		if seen:
			_suspicion += delta / DETECT_TIME
			if _suspicion >= 1.0:
				_start_chase(seen)
		else:
			_suspicion = maxf(_suspicion - delta / DETECT_TIME, 0.0)

	if _suspicion > 0.0:
		_stop(delta)  # she stops to look until she's sure, or has lost them
	else:
		match state:
			State.PATROL:
				_patrol(delta)
			State.INVESTIGATE:
				_investigate(delta)
			State.CHASE:
				_chase(delta, seen)

	_update_model_state()


# --- Public (host): Phase 7's noise system calls this ---------------------

func hear_noise(at: Vector3) -> void:
	if not multiplayer.is_server() or state == State.CHASE or state == State.CAUGHT:
		return
	_investigate_at(at)


# --- States ----------------------------------------------------------------

func _patrol(delta: float) -> void:
	if _waypoints.is_empty():
		return
	if agent.is_navigation_finished():
		_stop(delta)
		_wait_timer += delta
		if _wait_timer >= PATROL_PAUSE:
			_wait_timer = 0.0
			_waypoint_index = (_waypoint_index + 1) % _waypoints.size()
			agent.target_position = _waypoints[_waypoint_index]
		return
	_move_along_path(PATROL_SPEED, delta)


func _investigate(delta: float) -> void:
	if not agent.is_navigation_finished():
		_move_along_path(INVESTIGATE_SPEED, delta)
		return
	_stop(delta)
	rotate_y(LOOK_AROUND_SPEED * delta)
	_wait_timer += delta
	if _wait_timer >= LOOK_AROUND_TIME:
		_return_to_patrol()


func _chase(delta: float, seen: Node3D) -> void:
	if seen:
		_target = seen
		_last_seen = seen.global_position
		_lost_sight_timer = 0.0
	else:
		_lost_sight_timer += delta
		if _lost_sight_timer >= LOSE_SIGHT_TIME:
			_investigate_at(_last_seen)  # go check where they were last seen
			return

	if is_instance_valid(_target) and global_position.distance_to(_target.global_position) <= CATCH_DISTANCE:
		_stop(delta)
		state = State.CAUGHT
		GameState.end_heist(false, "Caught by the guard!")
		return

	agent.target_position = _last_seen
	_move_along_path(CHASE_SPEED, delta)


# --- Transitions -------------------------------------------------------------

func _start_chase(player: Node3D) -> void:
	state = State.CHASE
	_target = player
	_last_seen = player.global_position
	_lost_sight_timer = 0.0
	_suspicion = 0.0
	alerted = true
	GameState.set_alert(true)


func _investigate_at(at: Vector3) -> void:
	state = State.INVESTIGATE
	_wait_timer = 0.0
	agent.target_position = at
	alerted = false
	GameState.set_alert(false)


func _return_to_patrol() -> void:
	state = State.PATROL
	_wait_timer = 0.0
	if not _waypoints.is_empty():
		agent.target_position = _waypoints[_waypoint_index]
	alerted = false
	GameState.set_alert(false)


func _on_heist_reset(_respawn_players: bool) -> void:
	global_transform = _start_transform
	velocity = Vector3.ZERO
	_suspicion = 0.0
	_target = null
	_wait_timer = 0.0
	_waypoint_index = 0
	state = State.PATROL
	alerted = false
	model_state = GuardModel.State.IDLE
	if not _waypoints.is_empty():
		agent.target_position = _waypoints[0]


# --- Model -----------------------------------------------------------------

func _update_model_state() -> void:
	var moving := Vector2(velocity.x, velocity.z).length() > 0.1
	match state:
		State.CAUGHT:
			model_state = GuardModel.State.TACKLE
		State.CHASE:
			model_state = GuardModel.State.CHASE if moving else GuardModel.State.ALERT
		_:
			if _suspicion > 0.0:
				model_state = GuardModel.State.ALERT
			else:
				model_state = GuardModel.State.PATROL if moving else GuardModel.State.IDLE


# --- Vision ----------------------------------------------------------------

func _find_visible_player() -> Node3D:
	var forward := -global_basis.z
	var eye := eyes.global_position
	var chasing := state == State.CHASE
	var view_distance := CHASE_VIEW_DISTANCE if chasing else VIEW_DISTANCE
	var view_half_angle := CHASE_VIEW_HALF_ANGLE if chasing else VIEW_HALF_ANGLE
	var best: Node3D = null
	var best_distance := INF

	for player: Node3D in get_tree().get_nodes_in_group("players"):
		if not chasing and player.is_posing_as_statue():
			continue  # one more statue, unless she already saw them climb up there
		var chest := player.global_position + Vector3.UP * 1.2
		var to_player := chest - eye
		var distance := to_player.length()
		if distance > view_distance or distance >= best_distance:
			continue
		var flat := Vector3(to_player.x, 0.0, to_player.z)
		if flat.length() > 0.01 and rad_to_deg(forward.angle_to(flat.normalized())) > view_half_angle:
			continue  # outside the vision cone
		if not _has_line_of_sight(eye, chest, player):
			continue  # a wall or the door is in the way
		best = player
		best_distance = distance
	return best


func _has_line_of_sight(from: Vector3, to: Vector3, player: Node3D) -> bool:
	var query := PhysicsRayQueryParameters3D.create(from, to)
	query.exclude = [get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.get("collider") == player


# --- Movement ----------------------------------------------------------------

func _move_along_path(speed: float, delta: float) -> void:
	var direction := agent.get_next_path_position() - global_position
	direction.y = 0.0
	if direction.length() < 0.05:
		_stop(delta)
		return
	direction = direction.normalized()
	velocity.x = direction.x * speed
	velocity.z = direction.z * speed
	_apply_gravity(delta)
	move_and_slide()
	rotation.y = lerp_angle(rotation.y, atan2(-direction.x, -direction.z), TURN_SPEED * delta)


func _stop(delta: float) -> void:
	velocity.x = 0.0
	velocity.z = 0.0
	_apply_gravity(delta)
	move_and_slide()


func _apply_gravity(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
