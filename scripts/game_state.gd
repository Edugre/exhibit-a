extends Node
## Autoload "GameState": heist phase, countdown, artifact/alert status, and outcome.
## The host runs these rules and broadcasts every change; clients only display them.
## Other systems report events through the host-only API below.

signal phase_changed(phase: Phase)
## Host only. Fired at the start of every heist so level objects can reset
## themselves (door closed, puzzle unsolved...). respawn_players is true on a restart.
signal heist_reset(respawn_players: bool)

enum Phase { LOBBY, PLAYING, WON, LOST }
enum ArtifactState { LOCKED, AVAILABLE, CARRIED, DROPPED, DELIVERED }

const HEIST_DURATION := 180.0  # seconds; set to ~20 temporarily to test the timeout
const TIME_SYNC_INTERVAL := 0.5

var phase: Phase = Phase.LOBBY
var time_left := HEIST_DURATION
var end_reason := ""
var artifact_state: ArtifactState = ArtifactState.LOCKED
var artifact_holder := 0  # peer id carrying the artifact, 0 if nobody
var guard_alerted := false

var _time_sync := 0.0


func _ready() -> void:
	NetworkManager.host_disconnected.connect(_reset_local)


func _process(delta: float) -> void:
	if phase != Phase.PLAYING:
		return
	time_left = maxf(time_left - delta, 0.0)  # every peer ticks, for a smooth display
	if not multiplayer.is_server():
		return
	_time_sync += delta
	if _time_sync >= TIME_SYNC_INTERVAL:
		_time_sync = 0.0
		_sync_time.rpc(time_left)  # host corrects any drift on the client
	if time_left <= 0.0:
		end_heist(false, "Time's up. The museum opened.")


# --- Host-only API: other systems report events here ----------------------

func start_heist(respawn_players := false) -> void:
	if not multiplayer.is_server():
		return
	_apply_state.rpc(Phase.PLAYING, HEIST_DURATION, "", ArtifactState.LOCKED, 0, false)
	heist_reset.emit(respawn_players)


func end_heist(won: bool, reason: String) -> void:
	if not multiplayer.is_server() or phase != Phase.PLAYING:
		return
	var result := Phase.WON if won else Phase.LOST
	_apply_state.rpc(result, time_left, reason, artifact_state, artifact_holder, guard_alerted)


func stop_heist() -> void:
	## Partner left: back to waiting.
	if not multiplayer.is_server():
		return
	_apply_state.rpc(Phase.LOBBY, HEIST_DURATION, "", ArtifactState.LOCKED, 0, false)


func set_artifact(state: ArtifactState, holder: int = 0) -> void:
	if not multiplayer.is_server():
		return
	_apply_state.rpc(phase, time_left, end_reason, state, holder, guard_alerted)


func set_alert(alerted: bool) -> void:
	if not multiplayer.is_server() or alerted == guard_alerted:
		return
	_apply_state.rpc(phase, time_left, end_reason, artifact_state, artifact_holder, alerted)


# --- Any peer ---------------------------------------------------------------

func request_restart() -> void:
	_request_restart.rpc_id(1)


@rpc("any_peer", "call_local", "reliable")
func _request_restart() -> void:
	if not multiplayer.is_server():
		return
	if phase != Phase.WON and phase != Phase.LOST:
		return
	start_heist(true)


# --- Replication ------------------------------------------------------------

@rpc("authority", "call_local", "reliable")
func _apply_state(new_phase: int, new_time: float, reason: String, new_artifact: int, holder: int, alerted: bool) -> void:
	var phase_did_change := new_phase != phase
	phase = new_phase as Phase
	time_left = new_time
	end_reason = reason
	artifact_state = new_artifact as ArtifactState
	artifact_holder = holder
	guard_alerted = alerted
	if phase_did_change:
		phase_changed.emit(phase)


@rpc("authority", "call_remote", "unreliable_ordered")
func _sync_time(host_time: float) -> void:
	time_left = host_time


func _reset_local() -> void:
	var phase_did_change := phase != Phase.LOBBY
	phase = Phase.LOBBY
	time_left = HEIST_DURATION
	end_reason = ""
	artifact_state = ArtifactState.LOCKED
	artifact_holder = 0
	guard_alerted = false
	if phase_did_change:
		phase_changed.emit(phase)


# --- Debug shortcuts (host only) until Phases 4 and 6 exist. Remove before submitting.

func _unhandled_input(event: InputEvent) -> void:
	if not OS.is_debug_build() or not multiplayer.is_server() or phase != Phase.PLAYING:
		return
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_F1:
			end_heist(true, "Debug: artifact delivered.")
		KEY_F2:
			end_heist(false, "Debug: caught by the guard.")
		KEY_F3:
			set_alert(not guard_alerted)
