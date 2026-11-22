class_name RoomTone
extends Node3D
## A room's background sound (asset plan P4): a quiet loop that never stops, and now and then a one-shot
## picked from a list and played a little way off. Put one or more in a room scene, outside the
## NavigationRegion3D. Cosmetic and local: each peer plays its own, and nothing here is synced or
## affects the game. The sounds come from assets/interior/source/tools/make_room_sounds.py.

## The loop (its import settings loop it). Leave empty for a node that only plays one-shots.
@export var loop: AudioStream
@export var loop_volume_db := -22.0
## Played faster or slower, so one hum can sound different in every room.
@export var pitch := 1.0
## Beyond this many metres it can't be heard, so a room's tone stays mostly in that room.
@export var reach := 10.0

## One of these plays every so often, picked at random.
@export var one_shots: Array[AudioStream] = []
@export var one_shot_volume_db := -16.0
## The wait between one-shots, in seconds, picked between x and y each time.
@export var one_shot_every := Vector2(8.0, 18.0)
## How far from this node a one-shot can come from, along each axis.
@export var spread := Vector3.ZERO

var _loop_player: AudioStreamPlayer3D
var _shot_player: AudioStreamPlayer3D
var _next_shot := 0.0


func _ready() -> void:
	if loop:
		_loop_player = _player(loop, loop_volume_db)
		_loop_player.pitch_scale = pitch
		_loop_player.play(randf() * loop.get_length())  # start somewhere along it, so two rooms don't pulse together
	if not one_shots.is_empty():
		_shot_player = _player(null, one_shot_volume_db)
		_next_shot = randf_range(one_shot_every.x * 0.3, one_shot_every.y)


func _process(delta: float) -> void:
	if _shot_player == null:
		return
	_next_shot -= delta
	if _next_shot > 0.0:
		return
	_next_shot = randf_range(one_shot_every.x, one_shot_every.y)
	_shot_player.stream = one_shots.pick_random()
	_shot_player.position = Vector3(randf_range(-spread.x, spread.x), randf_range(-spread.y, spread.y), randf_range(-spread.z, spread.z))
	_shot_player.pitch_scale = randf_range(0.92, 1.08)
	_shot_player.play()


func _player(stream: AudioStream, volume: float) -> AudioStreamPlayer3D:
	var player := AudioStreamPlayer3D.new()
	player.stream = stream
	player.volume_db = volume
	player.unit_size = 3.0
	player.max_distance = reach
	add_child(player)
	return player
