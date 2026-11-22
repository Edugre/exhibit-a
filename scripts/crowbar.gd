class_name Crowbar
extends Carryable
## The crowbar (stretch goal: scoring): one per heist, behind the lobby's coat check. It goes in the hotbar
## like the jammer; with it in hand, the throw button pries open the display case you're looking at (see
## Hotbar._request_pry and DisplayCase). The drop key puts it down for your partner.
## The host decides who holds it; the MultiplayerSynchronizer copies holder, slot and where it lies.
## It's drawn in front of its holder only while it's in their hand, and swings when they pry.

## Held like a first-person crowbar: gripped low on the right, near the chisel end, with the bar rising
## up and away towards the middle of the view and the claw at the top, curling outwards.
const GRIP := Vector3(0.34, -0.5, -0.46)  # where the hand would be: right, down and forward from the head
const BAR_UP := Vector3(-0.52, 0.8, -0.3)   # from the grip towards the claw, in the head's space
const CURL := Vector3(1.0, 0.25, 0.2)        # roughly the way the claw curls (the bar's +y)
const GRIP_TO_MIDDLE := 0.26               # the model's origin is the middle of the bar
const HELD_SCALE := 1.3                    # drawn a little bigger in hand, so it reads as a heavy bar
const FALL_LIMIT := -10.0

var _start_transform: Transform3D
var _swing := 0.0  # 1 when it has just bitten, easing back to 0
var _hold := _hold_transform()


## From the grip to the bar as it's held: its x along BAR_UP, its claw curling towards CURL.
static func _hold_transform() -> Transform3D:
	var along := BAR_UP.normalized()
	var curl := (CURL - along * along.dot(CURL)).normalized()
	return Transform3D(Basis(along, curl, along.cross(curl)), along * GRIP_TO_MIDDLE)


func _ready() -> void:
	add_to_group("interactable")
	_start_transform = global_transform
	freeze = true  # it waits where it was put until someone takes it
	if multiplayer.has_multiplayer_peer() and not multiplayer.is_server():
		freeze = true
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _physics_process(_delta: float) -> void:
	if not multiplayer.is_server():
		return
	if holder_id != 0 and find_holder() == null:
		holder_id = 0  # the holder left the game: it drops where they were
		freeze = false
	elif holder_id == 0 and global_position.y < FALL_LIMIT:
		_return_to_start()


func _process(delta: float) -> void:
	if holder_id == 0:
		visible = true
		($Model as Node3D).scale = Vector3.ONE
		return
	var holder := find_holder()
	if holder == null:
		return
	visible = in_hand()
	($Model as Node3D).scale = Vector3.ONE * HELD_SCALE
	_swing = move_toward(_swing, 0.0, delta * 2.2)
	var head: Node3D = holder.get_node("Head")
	# A bite: the bar chops forward and down about the hand, and the hand pushes in a little
	var bite := Transform3D(Basis(Vector3.RIGHT, -1.0 * _swing), Vector3(0.0, 0.0, -0.12 * _swing))
	global_transform = head.global_transform * Transform3D(Basis(), GRIP) * bite * _hold


## Host only: called by the player's interact request. Into the first free hotbar slot.
func interact(peer_id: int) -> void:
	take(peer_id)


## A quick jab forward. The owner calls it on a swing at nothing; the host sends swung() to everyone
## when it bites into a case.
func swing() -> void:
	_swing = 1.0


@rpc("authority", "call_local", "reliable")
func swung() -> void:
	swing()


func _holder_changed() -> void:
	if not is_node_ready():
		return
	for shape: CollisionShape3D in find_children("*", "CollisionShape3D", false, false):
		shape.set_deferred("disabled", holder_id != 0)


func _on_heist_reset(_respawn_players: bool) -> void:
	holder_id = 0
	_return_to_start()


func _return_to_start() -> void:
	global_transform = _start_transform
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	freeze = true
