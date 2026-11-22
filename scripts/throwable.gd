class_name Throwable
extends Carryable
## An object players can pick up into their hotbar and throw. The host runs its physics;
## the MultiplayerSynchronizer copies its position, holder and slot to the client.
## It's drawn in front of its holder only while it's in their hand; stowed in another slot, it's hidden.

const HOLD_OFFSET := Vector3(0.4, -0.3, -0.8)  # right, down and forward from the head
const FALL_LIMIT := -10.0  # below this, the heel has left the map
const THROW_SPEED := 12.0
const TUMBLE_SPEED := 7.0  # end over end, so it doesn't fly like it's on a wire

## How far the guard hears this land.
@export var noise_radius := 8.0

@onready var collision_shape: CollisionShape3D = $CollisionShape3D
@onready var thud: AudioStreamPlayer3D = $Thud

var _start_transform: Transform3D
var _thrown := false


func _ready() -> void:
	add_to_group("interactable")
	add_to_group("throwables")
	NetworkManager.connected_to_host.connect(_on_connected_to_host)
	if multiplayer.has_multiplayer_peer() and not multiplayer.is_server():
		freeze = true  # spawned inside a room after we connected: the host already runs its physics
	_start_transform = global_transform
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host
	body_entered.connect(_on_body_entered)


func _physics_process(_delta: float) -> void:
	if not multiplayer.is_server():
		return

	if global_position.y < FALL_LIMIT:
		_return_to_start()
		return

	if holder_id != 0 and find_holder() == null:
		_release()  # the holder left the game


func _process(_delta: float) -> void:
	if holder_id == 0:
		visible = true
		return

	var holder := find_holder()
	if holder == null:
		return

	# Stowed ones ride along unseen, so they're never left somewhere stale
	visible = in_hand()
	var head: Node3D = holder.get_node("Head")
	global_position = head.global_transform * HOLD_OFFSET
	global_rotation = head.global_rotation


func _holder_changed() -> void:
	if is_node_ready():
		collision_shape.set_deferred("disabled", holder_id != 0)


## Host only: called by the player's interact request. Into the first free hotbar slot.
func interact(peer_id: int) -> void:
	take(peer_id)

## Host only: called by the player's throw request.
func throw(direction: Vector3) -> void:
	_release()
	linear_velocity = direction * THROW_SPEED
	angular_velocity = direction.cross(Vector3.UP).normalized() * -TUMBLE_SPEED
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
		NoiseSystem.emit_noise(global_position, noise_radius)
		_play_thud.rpc()


## Host → everyone: the players hear what the guard just heard.
@rpc("authority", "call_local", "reliable")
func _play_thud() -> void:
	thud.play()
		
	
