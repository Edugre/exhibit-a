extends Node3D
## Twin Archives (task B3): a lamp over the exit for each plate, so two players who can't see each other
## can still tell when the other one pressed. Pressing a plate lights its lamp, which fades out over
## the window the partner has to press theirs (TwinPlateGate.WINDOW). When the gate opens, both burn
## steady. Cosmetic: every peer works it out from the plates' is_pressed and the gate's is_open,
## which it already receives, so there's no network traffic of its own.

const LAMP_ENERGY := 2.2
const BULB_GLOW := 6.0
const WAITING := Color(1.0, 0.72, 0.36)
const OPEN := Color(0.45, 1.0, 0.55)

@export var plate_a: PressurePlate
@export var plate_b: PressurePlate
@export var gate: RoomGate
@export var lamp_a: OmniLight3D
@export var lamp_b: OmniLight3D
@export var bulb_a: MeshInstance3D
@export var bulb_b: MeshInstance3D

var _a_left := 0.0
var _b_left := 0.0
var _bulb_a_material: StandardMaterial3D
var _bulb_b_material: StandardMaterial3D


func _ready() -> void:
	plate_a.pressed_changed.connect(func(down: bool) -> void: if down: _a_left = TwinPlateGate.WINDOW)
	plate_b.pressed_changed.connect(func(down: bool) -> void: if down: _b_left = TwinPlateGate.WINDOW)
	_bulb_a_material = _own_material(bulb_a)
	_bulb_b_material = _own_material(bulb_b)


func _process(delta: float) -> void:
	_a_left = maxf(_a_left - delta, 0.0)
	_b_left = maxf(_b_left - delta, 0.0)
	_show(lamp_a, _bulb_a_material, _a_left)
	_show(lamp_b, _bulb_b_material, _b_left)


func _show(lamp: OmniLight3D, bulb: StandardMaterial3D, left: float) -> void:
	var level := 1.0 if gate.is_open else left / TwinPlateGate.WINDOW
	var colour := OPEN if gate.is_open else WAITING
	lamp.light_color = colour
	lamp.light_energy = LAMP_ENERGY * level
	bulb.emission = colour
	bulb.emission_energy_multiplier = BULB_GLOW * level


func _own_material(bulb: MeshInstance3D) -> StandardMaterial3D:
	var material := (bulb.mesh.surface_get_material(0) as StandardMaterial3D).duplicate() as StandardMaterial3D
	bulb.set_surface_override_material(0, material)
	return material
