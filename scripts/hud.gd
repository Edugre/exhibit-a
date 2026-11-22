extends CanvasLayer
## Heads-up display: time, artifact, the team's haul, alert, waiting message, and the end screen.
## Only reads GameState; the one thing it asks for is a restart. Loot calls toast() on whoever pockets it.

const TOAST_SECONDS := 2.2
const CARD_AT_START := 8.0  # seconds the controls card stays up when a heist begins

@onready var top_bar: Control = %TopBar
@onready var time_label: Label = %TimeLabel
@onready var artifact_label: Label = %ArtifactLabel
@onready var alert_label: Label = %AlertLabel
@onready var waiting_label: Label = %WaitingLabel
@onready var end_panel: PanelContainer = %EndPanel
@onready var result_label: Label = %ResultLabel
@onready var reason_label: Label = %ReasonLabel
@onready var restart_button: Button = %RestartButton

var _last_phase: GameState.Phase = GameState.Phase.LOBBY
var _watching_getaway: bool = false
var _loot_label: Label
var _toast: Label
var _toast_note: Label
var _toast_left := 0.0
var _card: ControlsCard
var _card_hint: Label
var _card_left := 0.0


func _ready() -> void:
	add_to_group("hud")
	_loot_label = Label.new()
	top_bar.add_child(_loot_label)
	top_bar.move_child(_loot_label, artifact_label.get_index() + 1)
	_build_toast()
	_card = ControlsCard.new()
	_card.visible = false
	add_child(_card)
	_card.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP, Control.PRESET_MODE_MINSIZE, 40)
	_card.grow_horizontal = Control.GROW_DIRECTION_BOTH  # under the top bar, clear of the hotbar
	_card_hint = Label.new()
	_card_hint.text = "Tab: controls"
	_card_hint.modulate = Color(1, 1, 1, 0.6)
	top_bar.add_child(_card_hint)
	restart_button.pressed.connect(GameState.request_restart)
	GameState.phase_changed.connect(_on_phase_changed)
	_on_phase_changed(GameState.phase)


func _process(_delta: float) -> void:
	visible = _is_connected()
	if not visible:
		return
	top_bar.visible = GameState.phase != GameState.Phase.LOBBY and not _watching_getaway
	waiting_label.visible = GameState.phase == GameState.Phase.LOBBY
	time_label.text = _format_time(GameState.time_left)
	artifact_label.text = _artifact_text()
	_loot_label.text = "Loot: $%s" % Loot.dollars(GameState.loot_total)
	if _toast_left > 0.0:
		_toast_left -= get_process_delta_time()
		_toast.modulate.a = clampf(_toast_left / 0.5, 0.0, 1.0)
		_toast.visible = _toast_left > 0.0
	alert_label.text = "ALERT!" if GameState.guard_alerted else "Quiet"
	alert_label.modulate = Color(1.0, 0.3, 0.3) if GameState.guard_alerted else Color.WHITE
	_card_left = maxf(_card_left - get_process_delta_time(), 0.0)
	var playing := GameState.phase == GameState.Phase.PLAYING and not _watching_getaway
	_card.visible = playing and (_card_left > 0.0 or Input.is_action_pressed("show_controls"))


func _on_phase_changed(phase: GameState.Phase) -> void:
	var ended := phase == GameState.Phase.WON or phase == GameState.Phase.LOST
	end_panel.visible = false
	end_panel.clear()
	if ended:
		result_label.text = "HEIST COMPLETE!" if phase == GameState.Phase.WON else "BUSTED"
		reason_label.text = GameState.end_reason
		var taken := GameState.heist_duration - GameState.time_left
		var had_book := GameState.artifact_state == GameState.ArtifactState.CARRIED or GameState.artifact_state == GameState.ArtifactState.DROPPED
		var out_of_time := GameState.end_reason == GameState.TIME_UP_REASON
		var reason := GameState.end_reason
		if phase == GameState.Phase.WON:
			await _watch_getaway()
			if GameState.phase != phase:
				return  # the host left while the van was driving off
		end_panel.visible = true
		end_panel.stamp_card(phase == GameState.Phase.WON, reason, taken, had_book, out_of_time, GameState.loot_total)
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE  # so the Restart button can be clicked
	elif phase == GameState.Phase.PLAYING:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED  # the card may have left the mouse free
		_card_left = CARD_AT_START  # every heist starts with the job and the keys on screen
	_last_phase = phase


func _watch_getaway() -> void:
	_watching_getaway = true
	await get_tree().create_timer(TrojanVan.SCENE_TIME).timeout
	_watching_getaway = false


func _is_connected() -> bool:
	var peer := multiplayer.multiplayer_peer
	if peer == null or peer is OfflineMultiplayerPeer:
		return false
	return peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED


func _format_time(seconds: float) -> String:
	var total := ceili(seconds)
	return "%d:%02d" % [total / 60, total % 60]


func _artifact_text() -> String:
	match GameState.artifact_state:
		GameState.ArtifactState.LOCKED:
			return "Artifact: locked in the vault"
		GameState.ArtifactState.AVAILABLE:
			return "Artifact: vault open!"
		GameState.ArtifactState.CARRIED:
			var who := "you" if GameState.artifact_holder == multiplayer.get_unique_id() else "your partner"
			return "Artifact: carried by %s" % who
		GameState.ArtifactState.DROPPED:
			return "Artifact: dropped!"
		GameState.ArtifactState.DELIVERED:
			return "Artifact: in the van"
	return ""


## A short "+$300  Gold ring" over the hotbar, for whoever just pocketed something.
func toast(text: String, note: String = "") -> void:
	_toast.text = text
	_toast_note.text = note
	_toast_left = TOAST_SECONDS
	_toast.modulate.a = 1.0
	_toast.visible = true


func _build_toast() -> void:
	_toast = Label.new()
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.add_theme_font_size_override("font_size", 26)
	_toast.add_theme_color_override("font_color", Color(0.98, 0.84, 0.46))
	_toast.add_theme_color_override("font_outline_color", Color(0.1, 0.06, 0.02, 0.9))
	_toast.add_theme_constant_override("outline_size", 6)
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast.visible = false
	add_child(_toast)
	_toast.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	_toast.offset_top = -250.0
	_toast.offset_bottom = -215.0
	_toast.offset_left = -300.0
	_toast.offset_right = 300.0
	_toast_note = Label.new()
	_toast_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast_note.add_theme_font_size_override("font_size", 15)
	_toast_note.add_theme_color_override("font_color", Color(0.96, 0.92, 0.84))
	_toast_note.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	_toast_note.add_theme_constant_override("outline_size", 4)
	_toast_note.position = Vector2(0.0, 36.0)
	_toast_note.size = Vector2(600.0, 22.0)
	_toast.add_child(_toast_note)
