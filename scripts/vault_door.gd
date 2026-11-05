class_name VaultDoor
extends Node3D
## The way into the vault: a section of wall with her portrait on it, armoured on the back.
## It folds out flat against the gallery wall, steel side showing, clear of the guard's patrol.
## The host sets `is_open`; a MultiplayerSynchronizer copies it to the client, and the setter swings
## the door on both peers. Each plate switches on one picture lamp, on every peer, from the
## `is_pressed` that plates already replicate, so the lamps need no network traffic of their own.

const LAMP_ENERGY := 5.0
const BULB_GLOW := 7.0
const LAMP_TIME := 0.3

@export var open_degrees := 180.0
@export var open_time := 2.2
@export var plate_left: PressurePlate
@export var plate_right: PressurePlate

@export var is_open := false:
	set(value):
		if value == is_open:
			return
		is_open = value
		_apply(true)

var _swing: Tween

@onready var shape: CollisionShape3D = $Leaf/Body/CollisionShape3D
@onready var lamp_left: SpotLight3D = $Leaf/LampLeft
@onready var lamp_right: SpotLight3D = $Leaf/LampRight


func _ready() -> void:
	_apply(false)
	_wire_lamp(plate_left, lamp_left, "LampLeftGlow", $Leaf/GemLeft)
	_wire_lamp(plate_right, lamp_right, "LampRightGlow", $Leaf/GemRight)


func _apply(animate: bool) -> void:
	if not is_node_ready():
		return
	var target_y := -open_degrees if is_open else 0.0
	if not animate:
		rotation_degrees.y = target_y
		return
	# It sweeps across the guard's patrol, so it's only solid once it has stopped moving.
	shape.set_deferred("disabled", true)
	if _swing:
		_swing.kill()
	_swing = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_swing.tween_property(self, "rotation_degrees:y", target_y, open_time)
	_swing.tween_callback(shape.set_deferred.bind("disabled", false))


## Each lamp has a bulb under its hood and a little gem that matches its plate's colour.
func _wire_lamp(plate: PressurePlate, spot: SpotLight3D, bulb_name: String, gem: MeshInstance3D) -> void:
	var bulb := find_child(bulb_name, true, false) as MeshInstance3D
	var bulb_material := bulb.get_active_material(0).duplicate() as StandardMaterial3D
	bulb.set_surface_override_material(0, bulb_material)
	var gem_material := gem.get_active_material(0).duplicate() as StandardMaterial3D
	gem.set_surface_override_material(0, gem_material)

	var show_lamp := func(pressed: bool) -> void:
		var fade := create_tween().set_parallel()
		fade.tween_property(spot, "light_energy", LAMP_ENERGY if pressed else 0.0, LAMP_TIME)
		fade.tween_property(bulb_material, "emission_energy_multiplier", BULB_GLOW if pressed else 0.0, LAMP_TIME)
		var colour := PressurePlate.PRESSED_COLOR if pressed else PressurePlate.IDLE_COLOR
		gem_material.albedo_color = colour
		gem_material.emission = colour

	plate.pressed_changed.connect(show_lamp)
	show_lamp.call(plate.is_pressed)
