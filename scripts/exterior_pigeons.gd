extends MultiMeshInstance3D
## Pigeons on the museum's ledges. They peck and shuffle, and burst into the air when somebody runs
## past, then settle again on another ledge. Purely cosmetic: each peer runs its own flock and nothing
## here touches shared game state. `startled` is there if the team wants to treat a scattering flock
## as noise for the guard.

signal startled(where: Vector3)

const SPOOK_RANGE := 5.5
const SPOOK_SPEED := 5.6       # a walk is 5 m/s, so only a run scares them
const CALM_RANGE := 1.6        # walk right up to one and it goes anyway
const FLY_SPEED := 9.0
const SETTLE_TIME := Vector2(9.0, 22.0)

## Ledges a bird can stand on, world positions.
@export var perches: Array[Vector3] = []
## The burst of wings when a flock goes up, and the odd coo from a ledge.
@export var flap_sound: NodePath
@export var coo_sound: NodePath

var _birds: Array[Dictionary] = []
var _last_pos: Dictionary = {}
var _flap_wait: float = 0.0
var _coo_wait: float = 6.0


func _ready() -> void:
	add_to_group("pigeons")
	multimesh = multimesh.duplicate()
	multimesh.instance_count = perches.size()
	for i in perches.size():
		_birds.append({
			"pos": perches[i],
			"perch": i,
			"yaw": randf() * TAU,
			"state": "perched",
			"t": 0.0,
			"from": perches[i],
			"to": perches[i],
			"wait": randf() * 4.0,
			"phase": randf() * TAU,
		})


func _process(delta: float) -> void:
	_flap_wait = maxf(_flap_wait - delta, 0.0)
	_coo_wait -= delta
	if _coo_wait <= 0.0:
		_coo_wait = randf_range(7.0, 19.0)
		_play(coo_sound, _birds.pick_random().pos)
	var runners := _runners(delta)
	for i in _birds.size():
		var b: Dictionary = _birds[i]
		match b.state:
			"perched":
				_perch(b, delta, runners)
			"flying":
				_fly(b, delta)
			"away":
				b.wait -= delta
				if b.wait <= 0.0:
					_return(b)
		_write(i, b)


## Every bird at once, for the alarm. Nobody scared them, so nothing here counts as a noise.
func scatter_all() -> void:
	_flap_wait = 0.0
	for b: Dictionary in _birds:
		if b.state == "perched":
			var from: Vector3 = b.pos + Vector3(randf_range(-3.0, 3.0), 0.0, randf_range(-3.0, 3.0))
			_take_off(b, from, false)


## Everyone who could scare a bird, with how fast they are moving.
func _runners(delta: float) -> Array:
	var list: Array = []
	for p: Node3D in get_tree().get_nodes_in_group("players"):
		var last: Vector3 = _last_pos.get(p, p.global_position)
		var speed: float = Vector2(p.global_position.x - last.x, p.global_position.z - last.z).length() / maxf(delta, 0.001)
		_last_pos[p] = p.global_position
		list.append([p.global_position, speed])
	return list


func _perch(b: Dictionary, delta: float, runners: Array) -> void:
	for r in runners:
		var distance: float = (r[0] as Vector3).distance_to(b.pos)
		if distance < CALM_RANGE or (distance < SPOOK_RANGE and r[1] > SPOOK_SPEED):
			_take_off(b, r[0])
			return
	b.wait -= delta
	if b.wait <= 0.0:
		b.wait = randf_range(1.5, 6.0)
		b.yaw += randf_range(-1.6, 1.6)


func _take_off(b: Dictionary, from_where: Vector3, heard: bool = true) -> void:
	var away := (b.pos as Vector3) - from_where
	away.y = 0.0
	away = away.normalized() if away.length() > 0.01 else Vector3.FORWARD
	b.state = "flying"
	b.t = 0.0
	b.from = b.pos
	b.to = (b.pos as Vector3) + away * 22.0 + Vector3(randf_range(-7.0, 7.0), randf_range(14.0, 22.0), randf_range(-3.0, 3.0))
	b.yaw = atan2(away.x, away.z)
	if heard:
		startled.emit(b.pos)
	if _flap_wait <= 0.0:
		_flap_wait = 1.5
		_play(flap_sound, b.pos)


func _fly(b: Dictionary, delta: float) -> void:
	var length: float = maxf((b.to as Vector3).distance_to(b.from), 0.1)
	b.t = minf(float(b.t) + delta * FLY_SPEED / length, 1.0)
	# Up and out on a curve, eased into the landing
	var s := float(b.t)
	var at: Vector3 = (b.from as Vector3).lerp(b.to, s)
	at.y += sin(s * PI) * 2.2
	b.pos = at
	if b.t >= 1.0:
		if b.get("landing", false):
			b.landing = false
			b.state = "perched"
			b.wait = randf_range(1.5, 5.0)
		else:
			b.state = "away"
			b.wait = randf_range(SETTLE_TIME.x, SETTLE_TIME.y)


## After a while the bird comes back to a free ledge, gliding down from the air.
func _return(b: Dictionary) -> void:
	var taken: Array[int] = []
	for other in _birds:
		taken.append(other.perch)
	var choices: Array[int] = []
	for i in perches.size():
		if not taken.has(i):
			choices.append(i)
	if not choices.is_empty():
		b.perch = choices.pick_random()
	b.from = b.pos
	b.to = perches[b.perch]
	b.t = 0.0
	b.state = "flying"
	b.landing = true
	var heading: Vector3 = (b.to as Vector3) - (b.from as Vector3)
	b.yaw = atan2(heading.x, heading.z)


func _play(sound: NodePath, where: Vector3) -> void:
	if sound.is_empty():
		return
	var player := get_node(sound) as AudioStreamPlayer3D
	player.global_position = where
	player.play()


func _write(i: int, b: Dictionary) -> void:
	var flap := 1.0 if b.state == "flying" else 0.0
	var hide_it: bool = b.state == "away"
	var basis := Basis(Vector3.UP, b.yaw).scaled(Vector3.ONE * (0.0001 if hide_it else 1.0))
	multimesh.set_instance_transform(i, Transform3D(basis, b.pos))
	multimesh.set_instance_custom_data(i, Color(flap, b.phase, 0.0, 0.0))
