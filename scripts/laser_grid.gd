class_name LaserGrid
extends Node3D
## A laser grid across a doorway (task C2). It doesn't stop anyone physically. Walking through it
## while it's active sets off an alarm: a loud noise at the grid that sends every guard in range to look.
##
## It's on when it has power and isn't jammed. The host decides both:
## - power: set_powered(), for a room's own switch (the Laser Corridor's fallback in C3)
## - jammed: jam(seconds), from the Signal Jammer (it's in the "jammable" group)
## `is_active` is copied to the client by the MultiplayerSynchronizer, so late joiners see it too.

signal tripped(by_peer: int)

## How far guards hear the alarm. Big on purpose: the beams are wired to the whole wing.
@export var alarm_radius := 20.0
## While someone stays in the beams, the alarm goes off again this often.
@export var retrigger_seconds := 1.5
## Size of the grid, matching the room contract's 3 m doorway by default.
@export var width := 3.0
@export var height := 2.4
@export var beam_count := 5

const BEAM_COLOR := Color(1.0, 0.05, 0.05)
const BEAM_THICKNESS := 0.02
const DEPTH := 0.3  # how thick the trigger zone is, so a fast step can't skip it
const POST_SIZE := 0.12

## Synced. True while the beams are on. Only the host sets it.
@export var is_active := true:
	set(value):
		is_active = value
		if is_node_ready():
			_show_active()

@onready var trigger: Area3D = $Trigger
@onready var trigger_shape: CollisionShape3D = $Trigger/CollisionShape3D
@onready var beams_root: Node3D = $Beams

var _powered := true
var _jam_left := 0.0
var _next_alarm: Dictionary[int, float] = {}  # peer id -> time (s) the alarm may go off again for them
var _beam_material := StandardMaterial3D.new()


func _ready() -> void:
	add_to_group(Room.JAMMABLE_GROUP)
	add_to_group("laser_grids")
	_build()
	_show_active()
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _physics_process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	if _jam_left > 0.0:
		_jam_left -= delta
		if _jam_left <= 0.0:
			_update_active()
	if is_active and GameState.phase == GameState.Phase.PLAYING:
		_check_players()


# --- Host only ---------------------------------------------------------------

## Called by GadgetJammer. A second jam restarts the countdown, it doesn't add to it.
func jam(seconds: float) -> void:
	if not multiplayer.is_server():
		return
	_jam_left = maxf(seconds, 0.0)
	_update_active()


## For a room's switch: false drops the grid until power comes back.
func set_powered(on: bool) -> void:
	if not multiplayer.is_server():
		return
	_powered = on
	_update_active()


func is_jammed() -> bool:
	return _jam_left > 0.0


func _update_active() -> void:
	var should_be := _powered and not is_jammed()
	if should_be == is_active:
		return
	is_active = should_be
	if is_active:
		# Anyone standing in the beams when they come back on is caught at once.
		_next_alarm.clear()


func _check_players() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	for body: Node3D in trigger.get_overlapping_bodies():
		if not body.is_in_group("players"):
			continue
		var peer_id := body.name.to_int()
		if now < _next_alarm.get(peer_id, 0.0):
			continue
		_next_alarm[peer_id] = now + retrigger_seconds
		NoiseSystem.emit_noise(body.global_position, alarm_radius)
		tripped.emit(peer_id)
		_flash.rpc()


func _on_heist_reset(_respawn_players: bool) -> void:
	_powered = true
	_jam_left = 0.0
	_next_alarm.clear()
	is_active = true


# --- Every peer --------------------------------------------------------------

## A short flare on every screen when someone sets it off.
@rpc("authority", "call_local", "reliable")
func _flash() -> void:
	_beam_material.emission_energy_multiplier = 6.0
	var tween := create_tween()
	tween.tween_property(_beam_material, "emission_energy_multiplier", 2.0, 0.4)


func _show_active() -> void:
	beams_root.visible = is_active


## Placeholder look: two posts and evenly spaced beams. The art (asset item P2.1) can replace
## the meshes later; the trigger and the rules stay here.
func _build() -> void:
	var box := BoxShape3D.new()
	box.size = Vector3(width, height, DEPTH)
	trigger_shape.shape = box
	trigger_shape.position = Vector3(0.0, height / 2.0, 0.0)

	_beam_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_beam_material.albedo_color = BEAM_COLOR
	_beam_material.emission_enabled = true
	_beam_material.emission = BEAM_COLOR
	_beam_material.emission_energy_multiplier = 2.0

	var beam_mesh := BoxMesh.new()
	beam_mesh.size = Vector3(width, BEAM_THICKNESS, BEAM_THICKNESS)
	beam_mesh.material = _beam_material
	for i in beam_count:
		var beam := MeshInstance3D.new()
		beam.mesh = beam_mesh
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		beam.position.y = height * float(i + 1) / float(beam_count + 1)
		beams_root.add_child(beam)

	var post_mesh := BoxMesh.new()
	post_mesh.size = Vector3(POST_SIZE, height, POST_SIZE)
	for side: float in [-1.0, 1.0]:
		var post := MeshInstance3D.new()
		post.mesh = post_mesh
		post.position = Vector3(side * (width / 2.0 + POST_SIZE / 2.0), height / 2.0, 0.0)
		add_child(post)
