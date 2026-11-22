class_name TwinPlateGate
extends Node
## Gate rule for Twin Archives (task B1): two plates sit in alcoves split by a wall. Pressing one starts
## a two-second window, and a fresh press on the other plate inside that window opens the gate.
## Unlike the vault, nobody has to keep standing on a plate. What counts is pressing together without
## seeing each other, so the players have to count it out between them.
## Only the host decides. The gate's own sync shows the result to the other player.

signal solved

## How close together the two presses must be, in seconds.
const WINDOW := 2.0
## A room is built (and rebuilt on every restart) while the players are still standing wherever they
## were, so plates can appear under them. The rule waits this long before it listens, so that
## doesn't count as two presses. Someone already on a plate steps off and on again to press it.
const SETTLE := 0.75

@export var plate_a: PressurePlate
@export var plate_b: PressurePlate
## What opens: anything with open() and close(), like the RoomGate from task A0, or anything with an
## `is_open` property, like the vault door, so the rule can be tried out before A0 lands.
@export var gate: Node

var is_solved := false

var _last_press := {}  # host only: PressurePlate -> time of its latest press, in seconds
var _listening_from := 0.0


func _ready() -> void:
	plate_a.pressed_changed.connect(_on_pressed_changed.bind(plate_a))
	plate_b.pressed_changed.connect(_on_pressed_changed.bind(plate_b))
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host
	_listening_from = _now() + SETTLE


func _on_pressed_changed(pressed: bool, plate: PressurePlate) -> void:
	if not is_inside_tree():
		return  # a room on its way out: its plates let go as it leaves
	if not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
		return
	if is_solved or not pressed:
		return  # only the moment a plate goes down counts, not stepping off it
	var now := _now()
	if now < _listening_from:
		return
	_last_press[plate] = now
	var other := plate_b if plate == plate_a else plate_a
	if _last_press.has(other) and now - float(_last_press[other]) <= WINDOW:
		_solve()


func _solve() -> void:
	is_solved = true
	_set_gate(true)
	solved.emit()


func _on_heist_reset(_respawn_players: bool) -> void:
	is_solved = false
	_last_press.clear()
	_listening_from = _now() + SETTLE
	_set_gate(false)


func _set_gate(open: bool) -> void:
	if gate == null:
		return
	if open and gate.has_method("open"):
		gate.open()
	elif not open and gate.has_method("close"):
		gate.close()
	elif "is_open" in gate:
		gate.is_open = open


func _now() -> float:
	return Time.get_ticks_msec() / 1000.0
