class_name Guard
extends CharacterBody3D
## Museum guard. Every decision runs on the host; the MultiplayerSynchronizer
## copies position, rotation and `alerted` to the client.
##
## PATROL      walk the GuardWaypoints loop, pausing at each one
## INVESTIGATE walk to a point (a noise, or where a player was last seen), look around
## CHASE       a player was seen long enough: follow them; catching one ends the heist

enum State { PATROL, INVESTIGATE, CHASE }

const PATROL_SPEED := 2.0
const INVESTIGATE_SPEED := 3.0
const CHASE_SPEED := 4.5          # slower than walking (5), faster than sneaking (2.5)
const TURN_SPEED := 6.0

const VIEW_DISTANCE := 12.0
const VIEW_HALF_ANGLE := 35.0     # degrees; keep equal to the flashlight's Spot Angle
const DETECT_TIME := 0.6          # seconds of continuous sight before a chase starts
const LOSE_SIGHT_TIME := 2.0      # seconds out of sight before the guard gives up
const CATCH_DISTANCE := 1.2
const PATROL_PAUSE := 1.0
const LOOK_AROUND_TIME := 3.0
const LOOK_AROUND_SPEED := 1.5    # radians per second while searching

const CALM_LIGHT := Color(1.0, 0.95, 0.8)
const ALERT_LIGHT := Color(1.0, 0.2, 0.2)

@export var waypoints_path: NodePath = ^"../Museum/GuardWaypoints"

## Replicated to the client so its flashlight turns red during a chase.
@export var alerted := false:
	set(value):
		alerted = value
		if is_node_ready():
			flashlight.light_color = ALERT_LIGHT if alerted else CALM_LIGHT

@onready var agent: NavigationAgent3D = $NavigationAgent3D
@onready var eyes: Node3D = $Eyes
@onready var flashlight: SpotLight3D = $Eyes/Flashlight

var state := State.PATROL
var _waypoints: Array[Vector3] = []
var _waypoint_index := 0
var _wait_timer := 0.0
var _suspicion := 0.0
var _target: Node3D = null
var _last_seen := Vector3.ZERO
var _lost_sight_timer := 0.0
var _start_transform: Transform3D


func _ready() -> void:
	_start_transform = global_transform
	for marker in get_node(waypoints_path).get_children():
		_waypoints.append((marker as Node3D).global_position)
	flashlight.light_color = CALM_LIGHT
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _physics_process(delta: float) -> void:			
	if not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
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

	match state:
		State.PATROL:
			_patrol(delta)
		State.INVESTIGATE:
			_investigate(delta)
		State.CHASE:
			_chase(delta, seen)


# --- Public (host): Phase 7's noise system calls this ---------------------

func hear_noise(at: Vector3) -> void:
	if not multiplayer.is_server() or state == State.CHASE:
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
	if not _waypoints.is_empty():
		agent.target_position = _waypoints[0]


# --- Vision ----------------------------------------------------------------

func _find_visible_player() -> Node3D:
	var forward := -global_basis.z
	var eye := eyes.global_position
	var best: Node3D = null
	var best_distance := INF

	for player: Node3D in get_tree().get_nodes_in_group("players"):
		var chest := player.global_position + Vector3.UP * 1.2
		var to_player := chest - eye
		var distance := to_player.length()
		if distance > VIEW_DISTANCE or distance >= best_distance:
			continue
		var flat := Vector3(to_player.x, 0.0, to_player.z)
		if flat.length() > 0.01 and rad_to_deg(forward.angle_to(flat.normalized())) > VIEW_HALF_ANGLE:
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


# --- Debug (host): press 4 to make a noise at the host's position. Remove in Phase 7.

func _unhandled_input(event: InputEvent) -> void:
	if not OS.is_debug_build() or not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_4:
		var host_player := get_node_or_null("../Players/1") as Node3D
		if host_player:
			hear_noise(host_player.global_position)
