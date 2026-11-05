class_name Throwable
extends RigidBody3D
## An object players can pick up and throw. The host runs its physics;
## the MultiplayerSynchronizer copies its position and holder to the client.

const HOLD_OFFSET := Vector3(0.4, -0.3, -0.8)  # right, down and forward from the head
const FALL_LIMIT := -10.0  # below this, the box has left the map
const THROW_SPEED := 12.0
const NOISE_RADIUS := 8.0

## Peer id of the player holding this, 0 if nobody. Replicated to the client.
@export var holder_id := 0:
	set(value):
		holder_id = value
		if is_node_ready():
			collision_shape.set_deferred("disabled", holder_id != 0)

@onready var collision_shape: CollisionShape3D = $CollisionShape3D

var _start_transform: Transform3D
var _thrown := false


func _ready() -> void:
	add_to_group("interactable")
	add_to_group("throwables")
	NetworkManager.connected_to_host.connect(_on_connected_to_host)
	_start_transform = global_transform
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host
	body_entered.connect(_on_body_entered)


func _physics_process(_delta: float) -> void:
	if not multiplayer.is_server():
		return

	if global_position.y < FALL_LIMIT:
		_return_to_start()
		return

	if holder_id != 0 and _find_holder() == null:
		_release()  # the holder left the game


func _process(_delta: float) -> void:
	if holder_id == 0:
		return

	var holder := _find_holder()
	if holder == null:
		return

	var head: Node3D = holder.get_node("Head")
	global_position = head.global_transform * HOLD_OFFSET
	global_rotation = head.global_rotation


func _find_holder() -> Node3D:
	return get_node_or_null("../../Players/%d" % holder_id) as Node3D


## Host only: called by the player's interact request.
func interact(peer_id: int) -> void:
	if holder_id != 0:
		return
	holder_id = peer_id
	freeze = true

## Host only: called by the player's throw request.
func throw(direction: Vector3) -> void:
	_release()
	linear_velocity = direction * THROW_SPEED
	_thrown = true


func _release() -> void:
	holder_id = 0
	freeze = false


func _on_connected_to_host() -> void:
	freeze = true  # the client only shows where the host says it is
	
func _on_heist_reset(_respawn_players: bool) -> void:
	_release()
	_return_to_start()


func _return_to_start() -> void:
	global_transform = _start_transform
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	_thrown = false
	
func _on_body_entered(_body: Node) -> void:
	if not multiplayer.is_server():
		return
	if _thrown:
		_thrown = false
		NoiseSystem.emit_noise(global_position, NOISE_RADIUS)
		
	
