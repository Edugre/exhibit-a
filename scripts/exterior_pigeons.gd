extends MultiMeshInstance3D
## Pigeons on the museum's ledges. They peck and shuffle, and burst into the air when somebody runs
## past, then settle again on another ledge. The host runs the flock: it decides when a bird takes off,
## where it flies and which ledge it comes back to, and tells the client, so both players watch the same
## birds. The client only animates what it's told. `startled` fires on the host, for the pigeon noise rule.

signal startled(where: Vector3)

const SPOOK_RANGE := 5.5
const SPOOK_SPEED := 5.6       # a walk is 5 m/s, so only a run scares them
const CALM_RANGE := 1.6        # walk right up to one and it goes anyway
const SPEED_WINDOW := 0.25     # bodies only move on physics steps, so speed is measured over a span
const FLY_SPEED := 9.0
const SETTLE_TIME := Vector2(9.0, 22.0)
const CROWNED_BIRD := 14       # wears a gold circlet, and won't say why

## Ledges a bird can stand on, world positions.
@export var perches: Array[Vector3] = []
## The burst of wings when a flock goes up, and the odd coo from a ledge.
@export var flap_sound: NodePath
@export var coo_sound: NodePath

var _birds: Array[Dictionary] = []
var _last_pos: Dictionary = {}
var _speeds: Dictionary = {}
var _window: float = 0.0
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
			"landing": false,
		})
	multiplayer.peer_connected.connect(_on_peer_connected)


func _process(delta: float) -> void:
	_flap_wait = maxf(_flap_wait - delta, 0.0)
	_coo_wait -= delta
	if _coo_wait <= 0.0:
		_coo_wait = randf_range(7.0, 19.0)
		_play(coo_sound, _birds.pick_random().pos)
	var host := multiplayer.is_server()
	var runners := _runners(delta) if host else []
	for i in _birds.size():
		var b: Dictionary = _birds[i]
		match b.state:
			"perched":
				_perch(i, b, delta, runners)
			"flying":
				_fly(b, delta)
			"away":
				if host:
					b.wait -= delta
					if b.wait <= 0.0:
						_send_back(i)
		_write(i, b)


## Every bird at once, for the alarm. Nobody scared them, so nothing here counts as a noise.
func scatter_all() -> void:
	if not multiplayer.is_server():
		return    # the host scatters its flock and tells the client
	_flap_wait = 0.0
	for i in _birds.size():
		var b: Dictionary = _birds[i]
		if b.state == "perched":
			var from: Vector3 = b.pos + Vector3(randf_range(-3.0, 3.0), 0.0, randf_range(-3.0, 3.0))
			_launch(i, from, false)


## Everyone who could scare a bird, with how fast they are moving. Host only.
func _runners(delta: float) -> Array:
	_window += delta
	var measuring := _window >= SPEED_WINDOW
	var list: Array = []
	for p: Node3D in get_tree().get_nodes_in_group("players"):
		if measuring:
			var last: Vector3 = _last_pos.get(p, p.global_position)
			_speeds[p] = Vector2(p.global_position.x - last.x, p.global_position.z - last.z).length() / _window
			_last_pos[p] = p.global_position
		list.append([p.global_position, _speeds.get(p, 0.0)])
	if measuring:
		_window = 0.0
	return list


func _perch(i: int, b: Dictionary, delta: float, runners: Array) -> void:
	for r in runners:
		var distance: float = (r[0] as Vector3).distance_to(b.pos)
		if distance < CALM_RANGE or (distance < SPOOK_RANGE and r[1] > SPOOK_SPEED):
			_launch(i, r[0], true)
			return
	# Shuffling round on the ledge is each screen's own business
	b.wait -= delta
	if b.wait <= 0.0:
		b.wait = randf_range(1.5, 6.0)
		b.yaw += randf_range(-1.6, 1.6)


## Host: send a bird up, away from whatever scared it.
func _launch(i: int, from_where: Vector3, heard: bool) -> void:
	var b: Dictionary = _birds[i]
	var away := (b.pos as Vector3) - from_where
	away.y = 0.0
	away = away.normalized() if away.length() > 0.01 else Vector3.FORWARD
	var to: Vector3 = (b.pos as Vector3) + away * 22.0 + Vector3(randf_range(-7.0, 7.0), randf_range(14.0, 22.0), randf_range(-3.0, 3.0))
	_take_off.rpc(i, to, atan2(away.x, away.z))
	if heard:
		startled.emit(b.pos)


@rpc("authority", "call_local", "reliable")
func _take_off(i: int, to: Vector3, yaw: float) -> void:
	var b: Dictionary = _birds[i]
	b.state = "flying"
	b.landing = false
	b.t = 0.0
	b.from = b.pos
	b.to = to
	b.yaw = yaw
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
		if b.landing:
			b.landing = false
			b.state = "perched"
			b.wait = randf_range(1.5, 5.0)
		else:
			b.state = "away"
			b.wait = randf_range(SETTLE_TIME.x, SETTLE_TIME.y)


## Host: after a while the bird comes back to a free ledge.
func _send_back(i: int) -> void:
	var taken: Array[int] = []
	for other in _birds:
		taken.append(other.perch)
	var choices: Array[int] = []
	for p in perches.size():
		if not taken.has(p):
			choices.append(p)
	var perch: int = choices.pick_random() if not choices.is_empty() else int(_birds[i].perch)
	_come_back.rpc(i, perch)


@rpc("authority", "call_local", "reliable")
func _come_back(i: int, perch: int) -> void:
	var b: Dictionary = _birds[i]
	b.perch = perch
	b.from = b.pos
	b.to = perches[perch]
	b.t = 0.0
	b.state = "flying"
	b.landing = true
	var heading: Vector3 = (b.to as Vector3) - (b.from as Vector3)
	b.yaw = atan2(heading.x, heading.z)


## Host: a partner who just joined gets the flock as it is right now.
func _on_peer_connected(peer_id: int) -> void:
	if not multiplayer.is_server():
		return
	var snapshot: Array = []
	for b in _birds:
		snapshot.append([b.state, b.pos, b.from, b.to, b.t, b.perch, b.landing, b.yaw])
	_sync_flock.rpc_id(peer_id, snapshot)


@rpc("authority", "call_remote", "reliable")
func _sync_flock(snapshot: Array) -> void:
	for i in mini(snapshot.size(), _birds.size()):
		var row: Array = snapshot[i]
		var b: Dictionary = _birds[i]
		b.state = row[0]
		b.pos = row[1]
		b.from = row[2]
		b.to = row[3]
		b.t = row[4]
		b.perch = row[5]
		b.landing = row[6]
		b.yaw = row[7]


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
	multimesh.set_instance_custom_data(i, Color(flap, b.phase, 1.0 if i == CROWNED_BIRD else 0.0, 0.0))
