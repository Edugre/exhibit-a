extends Node3D
## The Signal Jammer's look (asset item P2.4): the model, and an LED that blinks when it's used.
## Cosmetic only. GadgetJammer puts one on each player's belt and, for the owner, one that comes up into view.

const LED_IDLE := 1.0
const LED_FLASH := 14.0

var _led: StandardMaterial3D


func _ready() -> void:
	# Give this copy its own LED material, so one jammer blinking doesn't light up the other.
	for mesh: MeshInstance3D in find_children("*", "MeshInstance3D", true, false):
		for i in mesh.get_surface_override_material_count():
			var material := mesh.get_active_material(i)
			if material and material.resource_name == "led":
				_led = material.duplicate() as StandardMaterial3D
				mesh.set_surface_override_material(i, _led)
	if _led:
		_led.emission_energy_multiplier = LED_IDLE


## A bright flash that fades, once per use.
func blink() -> void:
	if _led == null:
		return
	_led.emission_energy_multiplier = LED_FLASH
	create_tween().tween_property(_led, "emission_energy_multiplier", LED_IDLE, 0.5)


## Two short blinks, for a use that did nothing.
func blink_twice() -> void:
	if _led == null:
		return
	var tween := create_tween()
	for i in 2:
		tween.tween_property(_led, "emission_energy_multiplier", LED_FLASH * 0.5, 0.04)
		tween.tween_property(_led, "emission_energy_multiplier", LED_IDLE, 0.08)
