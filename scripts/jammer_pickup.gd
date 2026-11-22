class_name JammerPickup
extends Carryable
## The Signal Jammer as a thing in the museum: one per heist, waiting on the lobby's ticket desk.
## Either player picks it up (interact) into their hotbar. Stowed, it clips onto their belt; picked in
## the hotbar, it's in their hand, raised in their own view. The drop key puts it down again for the
## other player. Its charges belong to it, so they go wherever it goes, and a fresh one with full
## charges comes with every new run.
## The host decides everything; the MultiplayerSynchronizer copies holder_id, slot, charges and where it lies.
## GadgetJammer (on each player) uses it while that player is the holder.

const MAX_CHARGES := 2
const FALL_LIMIT := -10.0
const BLINK_EVERY := 1.6  # seconds between LED blinks while it's lying around, so it catches the eye

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
		var holder := find_holder()
		if holder == null:
			holder_id = 0  # the holder left the game: it drops where they were
			freeze = false
		else:
			global_position = holder.global_position + Vector3(0.0, 0.9, 0.0)  # rides along, hidden
	elif global_position.y < FALL_LIMIT:
		_return_to_start()


# --- Host only -----------------------------------------------------------------

## Called by the player's interact request, once the host has checked who and how far.
## Into the first free hotbar slot.
func interact(peer_id: int) -> void:
	take(peer_id)


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


func _holder_changed() -> void:
	_apply()


## Lying around it can be seen and picked up; carried, it's shown on the holder's belt or in their hand instead.
func _apply() -> void:
	if not is_node_ready():
		return
	model.visible = holder_id == 0
	shape.set_deferred("disabled", holder_id != 0)
