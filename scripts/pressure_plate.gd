class_name PressurePlate
extends Area3D
## An empty statue plinth with a weight sensor in it, "pressed" while at least one player stands on it.
## Only the host decides; a MultiplayerSynchronizer copies `is_pressed` to the client,
## and the setter updates the visuals on both peers.

signal pressed_changed(pressed: bool)

const IDLE_COLOR := Color(0.85, 0.2, 0.2)
const PRESSED_COLOR := Color(0.2, 0.85, 0.3)
const SINK := 0.03

## The brass label on the front, naming the statue that's away being cleaned.
@export var label: Texture2D

@export var is_pressed := false:
	set(value):
		if value == is_pressed:
			return
		is_pressed = value
		_update_visual()
		pressed_changed.emit(is_pressed)

@onready var cap: Node3D = find_child("PlinthCap", true, false)
@onready var gem: MeshInstance3D = $Gem
@onready var plaque: MeshInstance3D = $Plaque

var _occupants := 0  # host only
var _gem_material: StandardMaterial3D
var _cap_height := 0.0


func _ready() -> void:
	_cap_height = cap.position.y
	_gem_material = gem.get_active_material(0).duplicate() as StandardMaterial3D
	gem.set_surface_override_material(0, _gem_material)
	var plaque_material := plaque.get_active_material(0).duplicate() as StandardMaterial3D
	plaque_material.albedo_texture = label
	plaque_material.emission_texture = label  # so it can be read in the shade
	plaque.set_surface_override_material(0, plaque_material)
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
	var colour := PRESSED_COLOR if is_pressed else IDLE_COLOR
	_gem_material.albedo_color = colour
	_gem_material.emission = colour
	cap.position.y = _cap_height - (SINK if is_pressed else 0.0)  # sinks slightly when pressed
