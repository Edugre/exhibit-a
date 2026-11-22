class_name JammerPickup
extends RigidBody3D
## The Signal Jammer as a thing in the museum: one per heist, waiting on the lobby's ticket desk.
## Either player picks it up (interact) and it clips onto their belt; with nothing else in hand, the
## throw button puts it down again for the other player. Its charges belong to it, so they go
## wherever it goes, and a fresh one with full charges comes with every new run.
## The host decides everything; the MultiplayerSynchronizer copies holder_id, charges and where it lies.
## GadgetJammer (on each player) uses it while that player is the holder.

const MAX_CHARGES := 2
const DROP_REACH := 0.7     # how far in front of you it lands
const FALL_LIMIT := -10.0
const BLINK_EVERY := 1.6  # seconds between LED blinks while it's lying around, so it catches the eye

## Peer id of the player carrying it, 0 if it's lying somewhere. Replicated.
@export var holder_id := 0:
	set(value):
		holder_id = value
		_apply()

## Charges left for this heist. Replicated.
@export var charges := MAX_CHARGES

var _start_transform: Transform3D
var _blink_left := 0.0

@onready var shape: CollisionShape3D = $CollisionShape3D
@onready var model: Node3D = $Model


func _ready() -> void:
	add_to_group("interactable")
	add_to_group("jammer_pickup")
	_start_transform = global_transform
	freeze = true  # it rests on the desk until someone drops it somewhere
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host
	_apply()


func _process(delta: float) -> void:
	if holder_id != 0:
		return
	_blink_left -= delta
	if _blink_left <= 0.0:
		_blink_left = BLINK_EVERY
		model.blink()


func _physics_process(_delta: float) -> void:
	if not multiplayer.is_server():
		return
	if holder_id != 0:
		var holder := _find_holder()
		if holder == null:
			holder_id = 0  # the holder left the game: it drops where they were
			freeze = false
		else:
			global_position = holder.global_position + Vector3(0.0, 0.9, 0.0)  # rides along, hidden
	elif global_position.y < FALL_LIMIT:
		_return_to_start()


# --- Host only -----------------------------------------------------------------

## Called by the player's interact request, once the host has checked who and how far.
func interact(peer_id: int) -> void:
	if not multiplayer.is_server() or holder_id != 0:
		return
	holder_id = peer_id
	freeze = true


## Puts it down in front of the holder.
func drop_from(player: Node3D) -> void:
	if not multiplayer.is_server() or holder_id != player.name.to_int():
		return
	var forward := -player.global_basis.z
	global_position = player.global_position + forward * DROP_REACH + Vector3(0.0, 0.4, 0.0)
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	holder_id = 0
	freeze = false


func spend() -> void:
	if multiplayer.is_server():
		charges = maxi(charges - 1, 0)


func _on_heist_reset(_respawn_players: bool) -> void:
	holder_id = 0
	charges = MAX_CHARGES
	_return_to_start()


func _return_to_start() -> void:
	global_transform = _start_transform
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	freeze = true


# --- Every peer -------------------------------------------------------------------

func is_held_by(peer_id: int) -> bool:
	return holder_id != 0 and holder_id == peer_id


## Lying around it can be seen and picked up; carried, it's shown on the holder's belt instead.
func _apply() -> void:
	if not is_node_ready():
		return
	model.visible = holder_id == 0
	shape.set_deferred("disabled", holder_id != 0)


func _find_holder() -> Node3D:
	for player in get_tree().get_nodes_in_group("players"):
		if player.name == str(holder_id):
			return player as Node3D
	return null
