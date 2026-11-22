extends Node
## The two bronze lanterns by the main doors burn a little unevenly, like real flames behind old glass.
## Purely cosmetic: each peer runs its own and nothing here touches shared game state.

@export var lanterns: Array[NodePath] = []

var _lights: Array[OmniLight3D] = []
var _base: Array[float] = []
var _time: float = 0.0


func _ready() -> void:
	for path in lanterns:
		var light := get_node(path) as OmniLight3D
		_lights.append(light)
		_base.append(light.light_energy)


func _process(delta: float) -> void:
	_time += delta
	for i in _lights.size():
		var slow := sin(_time * 7.3 + i) * sin(_time * 2.1 + i * 2.0)
		var quick := sin(_time * 23.0 + i * 5.0)
		_lights[i].light_energy = _base[i] * (0.93 + 0.05 * slow + 0.02 * quick)
