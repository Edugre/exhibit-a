extends CanvasLayer
## Heads-up display: time, artifact, alert, waiting message, and the end screen.
## Only reads GameState; the one thing it asks for is a restart.

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


func _ready() -> void:
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
	alert_label.text = "ALERT!" if GameState.guard_alerted else "Quiet"
	alert_label.modulate = Color(1.0, 0.3, 0.3) if GameState.guard_alerted else Color.WHITE


func _on_phase_changed(phase: GameState.Phase) -> void:
	var ended := phase == GameState.Phase.WON or phase == GameState.Phase.LOST
	end_panel.visible = false
	end_panel.clear()
	if ended:
		result_label.text = "HEIST COMPLETE!" if phase == GameState.Phase.WON else "BUSTED"
		reason_label.text = GameState.end_reason
		var taken := GameState.HEIST_DURATION - GameState.time_left
		var had_book := GameState.artifact_state == GameState.ArtifactState.CARRIED or GameState.artifact_state == GameState.ArtifactState.DROPPED
		var out_of_time := GameState.end_reason == GameState.TIME_UP_REASON
		var reason := GameState.end_reason
		if phase == GameState.Phase.WON:
			await _watch_getaway()
			if GameState.phase != phase:
				return  # the host left while the van was driving off
		end_panel.visible = true
		end_panel.stamp_card(phase == GameState.Phase.WON, reason, taken, had_book, out_of_time)
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE  # so the Restart button can be clicked
	elif phase == GameState.Phase.PLAYING and _last_phase != GameState.Phase.LOBBY:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED  # coming back from a restart
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
