extends Node
## A tube on its way out (asset P5.3): every so often the light stutters, a few quick dips, then catches
## again. The ceiling panel's glass dips with it. Purely cosmetic: each peer flickers in its own time and
## nothing here touches game state. It never drops below `lowest`, so the guards' flashlight beams (their
## own lights) always read, as the asset plan asks.

@export var light: Light3D
## The light panel whose glowing glass flickers along with the light.
@export var panel: Node3D
@export var rest_seconds := Vector2(4.0, 11.0)
@export var lowest := 0.35

var _rng := RandomNumberGenerator.new()
var _base_energy := 1.0
var _glass: StandardMaterial3D
var _base_glow := 1.0
var _wait := 0.0
var _dips_left := 0
var _dim := false


func _ready() -> void:
	_rng.randomize()
	_base_energy = light.light_energy
	# The panel's glass shares its material with every fixture, so this one gets a copy of its own
	for mesh: MeshInstance3D in panel.find_children("*", "MeshInstance3D", true, false):
		for i in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(i) as StandardMaterial3D
			if material != null and material.emission_enabled:
				_glass = material.duplicate() as StandardMaterial3D
				_base_glow = _glass.emission_energy_multiplier
				mesh.set_surface_override_material(i, _glass)
	_wait = _rng.randf_range(rest_seconds.x, rest_seconds.y)


func _process(delta: float) -> void:
	_wait -= delta
	if _wait > 0.0:
		return
	if _dim:
		_set_level(1.0)
		_dim = false
		_wait = _rng.randf_range(0.04, 0.2) if _dips_left > 0 else _rng.randf_range(rest_seconds.x, rest_seconds.y)
		return
	if _dips_left == 0:
		_dips_left = _rng.randi_range(2, 6)
	_set_level(_rng.randf_range(lowest, lowest + 0.25))
	_dim = true
	_dips_left -= 1
	_wait = _rng.randf_range(0.03, 0.11)


func _set_level(level: float) -> void:
	light.light_energy = _base_energy * level
	if _glass != null:
		_glass.emission_energy_multiplier = _base_glow * level
