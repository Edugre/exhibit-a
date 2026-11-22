class_name GadgetJammer
extends Node
## Signal Jammer, the HW #4 gadget. A child of each player.
## The owner presses use_gadget and asks the host. The host checks the phase, the charges and the range,
## spends a charge, and jams every "jammable" object close enough. Charges live on the host
## and are sent to every peer; they reset at the start of every heist.
##
## Jammable targets: in group "jammable", with a host-only method jam(seconds: float) -> void.

const MAX_CHARGES := 2
const JAM_SECONDS := 6.0
const JAM_RANGE := 6.0  # metres from the player to the target
const NO_CHARGES_TEXT := "Jammer empty"
const NO_TARGET_TEXT := "Nothing to jam in range"

## How many charges this player has left. Set only by the host, shown by every peer.
var charges: int = MAX_CHARGES

@onready var player: CharacterBody3D = get_parent()
@onready var hud: GadgetHud = $GadgetHud


func _enter_tree() -> void:
	# The player hands its authority to all its children. The charges belong to the host, so take it back.
	set_multiplayer_authority(1)


func _ready() -> void:
	hud.visible = player.is_multiplayer_authority()
	hud.show_charges(charges, MAX_CHARGES)
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _unhandled_input(event: InputEvent) -> void:
	if not player.is_multiplayer_authority():
		return
	if event.is_action_pressed("use_gadget") and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_request_use.rpc_id(1)


# --- Host only ---------------------------------------------------------------

@rpc("any_peer", "call_local", "reliable")
func _request_use() -> void:
	if not multiplayer.is_server():
		return
	var sender_id := multiplayer.get_remote_sender_id()
	if sender_id != player.name.to_int():
		return  # only the owner may use their own jammer
	if GameState.phase != GameState.Phase.PLAYING:
		return

	if charges <= 0:
		_show_message.rpc_id(sender_id, NO_CHARGES_TEXT)
		return

	var targets := _targets_in_range()
	if targets.is_empty():
		# A charge is only spent when something gets jammed, so a miss costs nothing.
		_show_message.rpc_id(sender_id, NO_TARGET_TEXT)
		return

	for target: Node in targets:
		target.jam(JAM_SECONDS)
	_set_charges.rpc(charges - 1)
	_show_message.rpc_id(sender_id, "Jammed %d for %d s" % [targets.size(), int(JAM_SECONDS)])


func _targets_in_range() -> Array[Node]:
	var found: Array[Node] = []
	for target: Node in get_tree().get_nodes_in_group("jammable"):
		if not (target is Node3D) or not target.has_method("jam"):
			continue
		if player.global_position.distance_to((target as Node3D).global_position) <= JAM_RANGE:
			found.append(target)
	return found


func _on_heist_reset(_respawn_players: bool) -> void:
	_set_charges.rpc(MAX_CHARGES)


# --- Replication -------------------------------------------------------------

@rpc("authority", "call_local", "reliable")
func _set_charges(value: int) -> void:
	charges = clampi(value, 0, MAX_CHARGES)
	hud.show_charges(charges, MAX_CHARGES)


@rpc("authority", "call_local", "reliable")
func _show_message(text: String) -> void:
	hud.flash(text)
