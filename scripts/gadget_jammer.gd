class_name GadgetJammer
extends Node
## Signal Jammer, the HW #4 gadget: one player's side of it. A child of each player.
## There's one jammer per heist, a JammerPickup lying in the museum (on the lobby's ticket desk). Whoever
## picks it up has it in their hotbar (see Hotbar). With it in hand they fire it with the throw button, or
## from anywhere in the bar with use_gadget (Q), which also brings it to hand; the hotbar's drop key puts it
## down for their partner.
## The owner asks the host; the host checks the phase, who's holding it, its charges and the range, spends a
## charge, and jams every "jammable" object close enough. The charges belong to the jammer, not the player.
##
## Jammable targets: in group "jammable", with a host-only method jam(seconds: float) -> void.
## They can also have show_jammed(seconds: float) -> void, which every peer calls for the look.
##
## The look (asset item P2.4): stowed, the jammer rides on its holder's belt. In hand it stays up in the
## holder's own view (and in their hand for everyone else), kicks when fired, and a spent charge plays a
## pulse on every screen.

const JAM_SECONDS := 6.0
const JAM_RANGE := 6.0  # metres from the player to the target
const NO_CHARGES_TEXT := "Jammer empty"
const NO_TARGET_TEXT := "Nothing to jam in range"
const NO_JAMMER_TEXT := "You don't have the jammer"

const MODEL := preload("res://scenes/signal_jammer_model.tscn")
const PULSE := preload("res://scenes/jam_pulse.tscn")
const DUD_SOUND := preload("res://assets/gadget/jam_dud.wav")
## On the front of the belt, right of the buckle, relative to the player's model (its label facing forward).
## The coat reaches z -0.29 at that height, and the arms hang past the hips, so the front is where it shows.
const BELT := Transform3D(Basis(Vector3.UP, PI), Vector3(0.16, 0.84, -0.32))
## In your own view, relative to the camera: tucked out of sight, held while it's in hand, and thrust up to fire.
var _view_down := Transform3D(Basis.from_euler(Vector3(-0.6, 0.35, 0.2)), Vector3(0.3, -0.7, -0.4))
var _view_held := Transform3D(Basis.from_euler(Vector3(0.0, 0.35, 0.12)), Vector3(0.24, -0.27, -0.4))
var _view_up := Transform3D(Basis.from_euler(Vector3(0.1, 0.35, 0.12)), Vector3(0.2, -0.2, -0.38))
## In a teammate's hand, as everyone else sees it: relative to their head, like a held throwable.
var _hand_pose := Transform3D(Basis.from_euler(Vector3(0.0, 0.35, 0.12)), Vector3(0.32, -0.38, -0.5))

@onready var player: CharacterBody3D = get_parent()
@onready var hud: GadgetHud = $GadgetHud

var _belt_model: Node3D
var _hand_model: Node3D  # everyone but the owner
var _view_model: Node3D  # owner only
var _view_tween: Tween
var _view_shown := false
var _dud_player: AudioStreamPlayer


func _enter_tree() -> void:
	# The player hands its authority to all its children. The jammer's rules belong to the host, so take it back.
	set_multiplayer_authority(1)


func _ready() -> void:
	hud.visible = player.is_multiplayer_authority()
	hud.charges_label.visible = false
	# The player's own nodes aren't ready yet (children are ready first), so find them by path.
	_belt_model = MODEL.instantiate()
	_belt_model.transform = BELT
	_belt_model.visible = false
	player.get_node(^"Model").add_child(_belt_model)  # the owner's model is hidden, and this with it
	if player.is_multiplayer_authority():
		_view_model = MODEL.instantiate()
		_view_model.transform = _view_down
		_view_model.visible = false
		player.get_node(^"Head/Camera3D").add_child(_view_model)
		_dud_player = AudioStreamPlayer.new()
		_dud_player.stream = DUD_SOUND
		add_child(_dud_player)
	else:
		_hand_model = MODEL.instantiate()
		_hand_model.transform = _hand_pose
		_hand_model.visible = false
		player.get_node(^"Head").add_child(_hand_model)


## Every peer works out from the jammer's synced holder, slot and the holder's picked slot where it shows:
## on the belt when stowed, in the hand when picked.
func _process(_delta: float) -> void:
	var pickup := jammer()
	var mine := holding()
	var in_hand := mine and pickup.in_hand()
	_belt_model.visible = mine and not in_hand
	if _hand_model:
		_hand_model.visible = in_hand
	if player.is_multiplayer_authority():
		hud.charges_label.visible = false  # the hotbar shows the charges
		_show_in_view(in_hand)


func _unhandled_input(event: InputEvent) -> void:
	if not player.is_multiplayer_authority() or Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return
	if event.is_action_pressed("use_gadget"):
		request_use()


## Owner: fire the jammer. From anywhere in the hotbar: it's brought to hand first.
func request_use() -> void:
	if player.get("holding"):
		return  # both hands on the book
	if holding():
		player.selected_slot = jammer().slot
		_kick_in_view()  # straight away, so the key feels answered before the host replies
	_request_use.rpc_id(1)


## The jammer for this run, wherever it is. null between a restart's free and spawn.
func jammer() -> JammerPickup:
	for pickup: JammerPickup in get_tree().get_nodes_in_group("jammer_pickup"):
		if not pickup.is_queued_for_deletion():
			return pickup
	return null


func holding() -> bool:
	var pickup := jammer()
	return pickup != null and pickup.is_held_by(player.name.to_int())


# --- Host only ---------------------------------------------------------------

@rpc("any_peer", "call_local", "reliable")
func _request_use() -> void:
	if not multiplayer.is_server():
		return
	var sender_id := multiplayer.get_remote_sender_id()
	if sender_id != player.name.to_int():
		return  # each player asks through their own GadgetJammer
	if GameState.phase != GameState.Phase.PLAYING:
		return
	if GameState.artifact_state == GameState.ArtifactState.CARRIED and GameState.artifact_holder == sender_id:
		return  # both hands on the book

	var pickup := jammer()
	if pickup == null or not pickup.is_held_by(sender_id):
		_show_message.rpc_id(sender_id, NO_JAMMER_TEXT)
		_play_dud.rpc_id(sender_id)
		return
	if pickup.charges <= 0:
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
	pickup.spend()
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


# --- Replication -------------------------------------------------------------

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
	if _hand_model:
		_hand_model.blink()
	if _view_model:
		_view_model.blink()
	for path in jammed:
		var target := get_node_or_null(path)
		if target and target.has_method("show_jammed"):
			target.show_jammed(JAM_SECONDS)


## Owner only: the jammer did nothing (not holding it, nothing in range, or no charge left).
@rpc("authority", "call_local", "reliable")
func _play_dud() -> void:
	if _dud_player:
		_dud_player.play()
	if _view_model and holding():
		_view_model.blink_twice()


# --- Owner's view ---------------------------------------------------------------

## Slides it up into view when it comes to hand, and back down out of sight when it goes.
func _show_in_view(shown: bool) -> void:
	if _view_model == null or shown == _view_shown:
		return
	_view_shown = shown
	if _view_tween:
		_view_tween.kill()
	_view_model.visible = true
	_view_tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	if shown:
		_view_tween.tween_property(_view_model, "transform", _view_held, 0.18)
	else:
		_view_tween.tween_property(_view_model, "transform", _view_down, 0.15)
		_view_tween.tween_callback(_view_model.hide)


## Fired: a quick thrust forward, then back to where it's held.
func _kick_in_view() -> void:
	if _view_model == null:
		return
	if _view_tween:
		_view_tween.kill()
	_view_shown = true
	_view_model.visible = true
	_view_tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_view_tween.tween_property(_view_model, "transform", _view_up, 0.12)
	_view_tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
	_view_tween.tween_property(_view_model, "transform", _view_held, 0.3)
