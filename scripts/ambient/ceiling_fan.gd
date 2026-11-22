extends Node3D
## Turns a ceiling fan's blades (asset plan P5.4). Cosmetic: every peer spins its own copy, nothing
## is synced. Each fan starts at its own angle and speed, so two in one room never turn in step.

## Turns per second, roughly; each fan varies it a little.
@export_range(0.05, 2.0, 0.05) var turns_per_second := 0.55

var _speed := 0.0
var _wobble_t := 0.0


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(get_path())  # the same fan looks the same on every run and every screen
	rotation.y = rng.randf() * TAU
	_speed = turns_per_second * TAU * rng.randf_range(0.9, 1.1)
	_wobble_t = rng.randf() * TAU


func _process(delta: float) -> void:
	rotation.y = wrapf(rotation.y - _speed * delta, 0.0, TAU)
	# An old fan is never quite balanced: a slow tilt that goes round with it
	_wobble_t += delta * _speed
	rotation.x = sin(_wobble_t) * 0.006
	rotation.z = cos(_wobble_t) * 0.006
