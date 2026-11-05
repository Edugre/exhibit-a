extends Node3D
## Fifth Avenue's night traffic. Cars run one way down four lanes, keep their distance, stop at the
## crossing's signal, and brake and honk for anyone standing in the road. Purely cosmetic: each peer runs
## its own traffic, the cars have no collision, and nothing here touches shared game state.

const LANES: Array[float] = [40.49, 44.15, 47.81, 51.47]
const WRAP_X := 268.0
const STOP_X := 8.4            # nose at the stop line, seen from a car's centre
const CRUISE := Vector2(10.0, 13.5)
const GAP := 9.0
const LOOK_AHEAD := 20.0
const GREEN_TIME := 32.0
const RED_TIME := 15.0

## One MultiMeshInstance3D per car model, and how many of each to run.
@export var models: Array[NodePath] = []
@export var counts: Array[int] = []
@export var beams: NodePath
@export var red_lamps: Array[NodePath] = []
@export var green_lamps: Array[NodePath] = []
@export var hand_signs: Array[NodePath] = []
@export var walk_signs: Array[NodePath] = []
@export var horn: NodePath
@export var engine: NodePath

var _cars: Array[Dictionary] = []
var _clock: float = 0.0
var _green: bool = true
var _horn_wait: float = 0.0
var _beams: MultiMeshInstance3D


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var total := 0
	for i in models.size():
		var batch := get_node(models[i]) as MultiMeshInstance3D
		batch.multimesh = batch.multimesh.duplicate()
		batch.multimesh.instance_count = counts[i]
		for k in counts[i]:
			_cars.append({
				"batch": batch.multimesh,
				"slot": k,
				"lane": rng.randi() % LANES.size(),
				"x": rng.randf_range(-WRAP_X, WRAP_X),
				"cruise": rng.randf_range(CRUISE.x, CRUISE.y),
				"speed": 8.0,
			})
			total += 1
	_beams = get_node(beams) as MultiMeshInstance3D
	_beams.multimesh = _beams.multimesh.duplicate()
	_beams.multimesh.instance_count = total
	_set_signal(true)


func _process(delta: float) -> void:
	_clock += delta
	var green_now: bool = fmod(_clock, GREEN_TIME + RED_TIME) < GREEN_TIME
	if green_now != _green:
		_set_signal(green_now)
	_horn_wait = maxf(_horn_wait - delta, 0.0)
	var walkers: Array[Vector3] = []
	for p: Node3D in get_tree().get_nodes_in_group("players"):
		walkers.append(p.global_position)
	var nearest: Vector3 = Vector3.INF
	var nearest_distance: float = INF
	var camera: Camera3D = get_viewport().get_camera_3d()
	for i in _cars.size():
		var car: Dictionary = _cars[i]
		var want: float = car.cruise
		var x: float = car.x
		var z: float = LANES[car.lane]
		if not _green and x > STOP_X and x < STOP_X + 42.0:
			want = minf(want, (x - STOP_X) * 0.9)
		for other in _cars:
			if other != car and other.lane == car.lane and float(other.x) < x and x - float(other.x) < GAP + 12.0:
				want = minf(want, maxf((x - float(other.x) - GAP) * 0.9, 0.0))
		for w in walkers:
			if absf(w.z - z) < 2.0 and w.x < x and x - w.x < LOOK_AHEAD:
				want = minf(want, maxf((x - w.x - 6.0) * 0.8, 0.0))
				if x - w.x < 12.0 and _horn_wait <= 0.0:
					_honk(Vector3(x, 0.6, z))
		var rate: float = 7.0 if want < float(car.speed) else 3.0
		car.speed = move_toward(float(car.speed), want, rate * delta)
		x -= float(car.speed) * delta
		if x < -WRAP_X:
			x = WRAP_X
			car.lane = randi() % LANES.size()
		car.x = x
		var at := Vector3(x, 0.0, z)
		(car.batch as MultiMesh).set_instance_transform(car.slot, Transform3D(Basis.IDENTITY, at))
		_beams.multimesh.set_instance_transform(i, Transform3D(Basis.IDENTITY, at))
		if camera != null:
			var d: float = (to_global(at)).distance_squared_to(camera.global_position)
			if d < nearest_distance and float(car.speed) > 1.0:
				nearest_distance = d
				nearest = at
	if nearest != Vector3.INF and not engine.is_empty():
		(get_node(engine) as Node3D).position = nearest


func _set_signal(green: bool) -> void:
	_green = green
	for p in red_lamps:
		(get_node(p) as Node3D).visible = not green
	for p in green_lamps:
		(get_node(p) as Node3D).visible = green
	for p in hand_signs:
		(get_node(p) as Node3D).visible = green
	for p in walk_signs:
		(get_node(p) as Node3D).visible = not green


func _honk(where: Vector3) -> void:
	_horn_wait = 4.0
	if horn.is_empty():
		return
	var player := get_node(horn) as AudioStreamPlayer3D
	player.position = where
	player.play()
