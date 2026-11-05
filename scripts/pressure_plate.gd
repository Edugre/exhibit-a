class_name PressurePlate
extends Area3D
## A floor plate that is "pressed" while at least one player stands on it.
## Only the host decides; a MultiplayerSynchronizer copies `is_pressed` to the client,
## and the setter updates the visuals on both peers.

signal pressed_changed(pressed: bool)

const IDLE_COLOR := Color(0.85, 0.2, 0.2)
const PRESSED_COLOR := Color(0.2, 0.85, 0.3)

@export var is_pressed := false:
	set(value):
		if value == is_pressed:
			return
		is_pressed = value
		_update_visual()
		pressed_changed.emit(is_pressed)

@onready var visual: CSGBox3D = $Visual

var _occupants := 0  # host only
var _material := StandardMaterial3D.new()


func _ready() -> void:
	visual.material = _material
	_update_visual()
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)


func _on_body_entered(body: Node3D) -> void:
	if not multiplayer.is_server() or not body.is_in_group("players"):
		return
	_occupants += 1
	is_pressed = _occupants > 0


func _on_body_exited(body: Node3D) -> void:
	if not multiplayer.is_server() or not body.is_in_group("players"):
		return
	_occupants = maxi(_occupants - 1, 0)
	is_pressed = _occupants > 0


func _update_visual() -> void:
	if not is_node_ready():
		return
	_material.albedo_color = PRESSED_COLOR if is_pressed else IDLE_COLOR
	visual.position.y = -0.04 if is_pressed else 0.0  # sinks slightly when pressed
