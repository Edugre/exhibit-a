class_name Staff
extends Guard
## Night staff (docs/boss_and_staff.md). They patrol and see exactly as the librarian does (same cone,
## reach and suspicion, and the Heel and statue poses work on them too), but they never chase and never
## catch. When one is sure they've seen someone, they stop, turn to face them and ring a hand bell, and
## keep ringing while they can still see them. The librarian hears every bell, wherever she is.
## The host decides; `rings` is synced, so every peer hears the bell and shows the warning.

const RING_EVERY := 3.0
const TURN_TO_FACE := 6.0

## Counts this one's rings. When it goes up, every peer plays the bell and warns the players.
@export var rings := 0:
	set(value):
		var louder := value > rings
		rings = value
		if louder and is_node_ready():
			bell.play()
			get_tree().call_group("boss", "warn")

var _next_ring := 0.0

@onready var bell: AudioStreamPlayer3D = $Bell


## Where the librarian would start a chase, staff ring instead: they stay sure while the player is in
## sight (so they keep standing and watching), turn to them, and ring every RING_EVERY seconds.
func _start_chase(player: Node3D) -> void:
	_suspicion = 1.0
	var to := player.global_position - global_position
	rotation.y = lerp_angle(rotation.y, atan2(-to.x, -to.z), TURN_TO_FACE * get_physics_process_delta_time())
	var now := Time.get_ticks_msec() / 1000.0
	if now < _next_ring:
		return
	_next_ring = now + RING_EVERY
	rings += 1
	for boss in get_tree().get_nodes_in_group("boss"):
		boss.hear_bell(player.global_position)


func _on_heist_reset(respawn_players: bool) -> void:
	super(respawn_players)
	_next_ring = 0.0
