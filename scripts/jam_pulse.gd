extends Node3D
## The Signal Jammer's pulse (asset item P2.4), played on every screen when a charge is spent: a shell of
## light that sweeps out to the jammer's range, a ring along the floor, a flash and a burst of radio static.
## Cosmetic only: each peer plays its own copy where the host says, and it frees itself.

const SWEEP_TIME := 0.45
const LIFE := 1.2

## How far the pulse reaches, in metres. GadgetJammer sets it to its range.
var radius := 6.0

@onready var shell: MeshInstance3D = $Shell
@onready var ring: MeshInstance3D = $Ring
@onready var flash: OmniLight3D = $Flash
@onready var sound: AudioStreamPlayer3D = $Sound


func _ready() -> void:
	var shell_material := shell.mesh.surface_get_material(0).duplicate() as StandardMaterial3D
	shell.material_override = shell_material
	var ring_material := ring.mesh.surface_get_material(0).duplicate() as StandardMaterial3D
	ring.material_override = ring_material
	shell.scale = Vector3.ONE * 0.1
	ring.scale = Vector3.ONE * 0.1
	sound.play()

	var tween := create_tween().set_parallel().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(shell, "scale", Vector3.ONE * radius, SWEEP_TIME)
	tween.tween_property(ring, "scale", Vector3(radius, 1.0, radius), SWEEP_TIME)
	tween.tween_property(shell_material, "albedo_color:a", 0.0, SWEEP_TIME)
	tween.tween_property(ring_material, "albedo_color:a", 0.0, SWEEP_TIME * 1.4)
	tween.tween_property(flash, "light_energy", 0.0, SWEEP_TIME)
	await get_tree().create_timer(LIFE).timeout
	queue_free()
