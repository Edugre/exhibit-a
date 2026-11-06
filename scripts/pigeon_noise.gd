extends Node
## Gameplay rule: a flock going up gives you away. When a run or a close pass scares the pigeons, the
## guard hears it if she's near enough and comes to look. Runs on the host, on the host's own flock.
## The alarm's scatter doesn't count: that isn't anybody's doing.

const NOISE_RADIUS := 14.0
const QUIET_TIME := 4.0        # one panic at a time, or a whole flock would call her over and over

@export var pigeons_path: NodePath

var _quiet_until: float = 0.0


func _ready() -> void:
	(get_node(pigeons_path) as Node).startled.connect(_on_startled)


func _on_startled(where: Vector3) -> void:
	if not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
		return
	var now := Time.get_ticks_msec() / 1000.0
	if now < _quiet_until:
		return
	_quiet_until = now + QUIET_TIME
	NoiseSystem.emit_noise(where, NOISE_RADIUS)
