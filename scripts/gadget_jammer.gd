class_name GadgetJammer
extends Node
## Signal Jammer, the HW #4 gadget. A child of each player.
## The owner presses use_gadget and asks the host. The host checks the phase, the charges and the range,
## spends a charge, and jams every "jammable" object close enough. Charges live on the host
## and are sent to every peer; they reset at the start of every heist.
##
## Jammable targets: in group "jammable", with a host-only method jam(seconds: float) -> void.
## They can also have show_jammed(seconds: float) -> void, which every peer calls for the look.
##
## The look (asset item P2.4): the jammer rides on every player's belt, comes up into the owner's view
## when they press the key, and a spent charge plays a pulse on every screen.

const MAX_CHARGES := 2
const JAM_SECONDS := 6.0
const JAM_RANGE := 6.0  # metres from the player to the target
const NO_CHARGES_TEXT := "Jammer empty"
const NO_TARGET_TEXT := "Nothing to jam in range"

const MODEL := preload("res://scenes/signal_jammer_model.tscn")
const PULSE := preload("res://scenes/jam_pulse.tscn")
const DUD_SOUND := preload("res://assets/gadget/jam_dud.wav")
## On the front of the belt, right of the buckle, relative to the player's model (its label facing forward).
## The coat reaches z -0.29 at that height, and the arms hang past the hips, so the front is where it shows.
const BELT := Transform3D(Basis(Vector3.UP, PI), Vector3(0.16, 0.84, -0.32))
## In your own view, relative to the camera: tucked out of sight, and raised to use.
var _view_down := Transform3D(Basis.from_euler(Vector3(-0.6, 0.35, 0.2)), Vector3(0.3, -0.7, -0.4))
var _view_up := Transform3D(Basis.from_euler(Vector3(0.1, 0.35, 0.12)), Vector3(0.2, -0.2, -0.38))
const VIEW_HOLD := 0.7  # seconds it stays up

## How many charges this player has left. Set only by the host, shown by every peer.
var charges: int = MAX_CHARGES

@onready var player: CharacterBody3D = get_parent()
@onready var hud: GadgetHud = $GadgetHud

var _belt_model: Node3D
var _view_model: Node3D  # owner only
var _view_tween: Tween
var _dud_player: AudioStreamPlayer


func _enter_tree() -> void:
	# The player hands its authority to all its children. The charges belong to the host, so take it back.
	set_multiplayer_authority(1)


func _ready() -> void:
	hud.visible = player.is_multiplayer_authority()
	hud.show_charges(charges, MAX_CHARGES)
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host
	# The player's own nodes aren't ready yet (children are ready first), so find them by path.
	_belt_model = MODEL.instantiate()
	_belt_model.transform = BELT
	player.get_node(^"Model").add_child(_belt_model)  # the owner's model is hidden, and this with it
	if player.is_multiplayer_authority():
		_view_model = MODEL.instantiate()
		_view_model.transform = _view_down
		_view_model.visible = false
		player.get_node(^"Head/Camera3D").add_child(_view_model)
		_dud_player = AudioStreamPlayer.new()
		_dud_player.stream = DUD_SOUND
		add_child(_dud_player)


func _unhandled_input(event: InputEvent) -> void:
	if not player.is_multiplayer_authority():
		return
	if event.is_action_pressed("use_gadget") and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_raise_into_view()  # straight away, so the key feels answered before the host replies
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
		_play_dud.rpc_id(sender_id)
		return

	var targets := _targets_in_range()
	if targets.is_empty():
		# A charge is only spent when something gets jammed, so a miss costs nothing.
		_show_message.rpc_id(sender_id, NO_TARGET_TEXT)
		_play_dud.rpc_id(sender_id)
		return

	var jammed: Array[NodePath] = []
	for target: Node in targets:
		target.jam(JAM_SECONDS)
		jammed.append(target.get_path())
	_set_charges.rpc(charges - 1)
	_play_pulse.rpc(player.global_position, jammed)
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


## Every peer: a charge was spent here. The pulse, the LED, and each jammed thing's own look.
@rpc("authority", "call_local", "reliable")
func _play_pulse(at: Vector3, jammed: Array) -> void:  # untyped: typed arrays don't survive an RPC
	var pulse := PULSE.instantiate()
	pulse.radius = JAM_RANGE
	player.get_parent().get_parent().add_child(pulse)  # the world, not the player, so it stays put
	pulse.global_position = at
	_belt_model.blink()
	if _view_model:
		_view_model.blink()
	for path in jammed:
		var target := get_node_or_null(path)
		if target and target.has_method("show_jammed"):
			target.show_jammed(JAM_SECONDS)


## Owner only: the jammer did nothing (nothing in range, or no charge left).
@rpc("authority", "call_local", "reliable")
func _play_dud() -> void:
	if _dud_player:
		_dud_player.play()
	if _view_model:
		_view_model.blink_twice()


# --- Owner's view ---------------------------------------------------------------

func _raise_into_view() -> void:
	if _view_model == null:
		return
	if _view_tween:
		_view_tween.kill()
	_view_model.visible = true
	_view_tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_view_tween.tween_property(_view_model, "transform", _view_up, 0.15)
	_view_tween.tween_interval(VIEW_HOLD)
	_view_tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_view_tween.tween_property(_view_model, "transform", _view_down, 0.2)
	_view_tween.tween_callback(_view_model.hide)
