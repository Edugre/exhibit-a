extends Node
## Autoload "NoiseSystem": anything that makes a noise reports it here.
## Guards within the radius get told where it happened. Host only.


func emit_noise(at: Vector3, radius: float) -> void:
	if not multiplayer.is_server():
		return
	
	for guard:Guard in get_tree().get_nodes_in_group("guards"):
		if guard.global_position.distance_to(at) <= radius:
			guard.hear_noise(at)
		
		
