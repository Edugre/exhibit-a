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
## Sounds (asset item P4.5): a hum while the beams are on, and a zap when someone walks into them.
const HUM := preload("res://assets/interior/sounds/amb_laser_hum.wav")
const ZAP := preload("res://assets/interior/sounds/sfx_laser_zap.wav")
## The look (asset item P2.1): emitter posts, built for a 2.4 m grid and stretched to fit, and the beam shader.
const POST := preload("res://assets/interior/laser/laser_post.gltf")
const POST_BUILT_HEIGHT := 2.4
const BEAM_SHADER := preload("res://assets/interior/laser/laser_beam.gdshader")

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
var _core_material := ShaderMaterial.new()
var _glow_material := ShaderMaterial.new()
var _lens_material := StandardMaterial3D.new()
var _sputter_left := 0.0  # every peer: how long the jammed look lasts
var _hum: AudioStreamPlayer3D
var _zap: AudioStreamPlayer3D


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

## The Signal Jammer hit this grid (asset item P2.4). Cosmetic, on every peer: sparks fly off both
## posts and the beams sputter until it comes back, so a jammed grid doesn't look like one that a
## switch turned off.
func show_jammed(seconds: float) -> void:
	_sputter_left = seconds
	for side: float in [-1.0, 1.0]:
		_spark(Vector3(side * (width / 2.0 + POST_SIZE / 2.0), height * 0.6, 0.0))


func _process(delta: float) -> void:
	if _sputter_left <= 0.0:
		return
	_sputter_left -= delta
	if is_active or _sputter_left <= 0.0:
		_sputter_left = 0.0
		_set_beam_intensity(1.0)
		_show_active()
		return
	# Off, but now and then a beam stutters back for a frame, dimmer than it should be
	_set_beam_intensity(0.35)
	beams_root.visible = randf() < 0.07


func _spark(at: Vector3) -> void:
	var process := ParticleProcessMaterial.new()
	process.direction = Vector3.UP
	process.spread = 75.0
	process.initial_velocity_min = 1.5
	process.initial_velocity_max = 3.5
	process.gravity = Vector3(0.0, -9.8, 0.0)
	var spark_material := StandardMaterial3D.new()
	spark_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark_material.albedo_color = Color(1.0, 0.75, 0.35)
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE * 0.015
	mesh.material = spark_material
	var sparks := GPUParticles3D.new()
	sparks.amount = 24
	sparks.lifetime = 0.5
	sparks.one_shot = true
	sparks.explosiveness = 0.9
	sparks.process_material = process
	sparks.draw_pass_1 = mesh
	sparks.position = at
	add_child(sparks)
	sparks.emitting = true
	get_tree().create_timer(1.2).timeout.connect(sparks.queue_free)

## A short flare on every screen when someone sets it off.
@rpc("authority", "call_local", "reliable")
func _flash() -> void:
	_set_beam_intensity(3.0)
	_zap.play()
	create_tween().tween_method(_set_beam_intensity, 3.0, 1.0, 0.4)


## 1 is normal. The core and the glow share it, so every beam flares and fades together.
func _set_beam_intensity(value: float) -> void:
	_core_material.set_shader_parameter("intensity", 2.5 * value)
	_glow_material.set_shader_parameter("intensity", 0.6 * value)


func _show_active() -> void:
	beams_root.visible = is_active
	_lens_material.emission_energy_multiplier = 3.0 if is_active else 0.15
	if _hum:
		if is_active and not _hum.playing:
			_hum.play(randf() * HUM.get_length())
		elif not is_active:
			_hum.stop()


## Two emitter posts with a lens at every beam, and the beams between them (asset item P2.1).
## Only the look; the trigger and the rules are above.
func _build() -> void:
	_hum = AudioStreamPlayer3D.new()
	_hum.stream = HUM
	_hum.volume_db = -16.0
	_hum.unit_size = 2.0
	_hum.max_distance = 9.0
	_hum.position.y = height / 2.0
	add_child(_hum)
	_zap = AudioStreamPlayer3D.new()
	_zap.stream = ZAP
	_zap.volume_db = -6.0
	_zap.unit_size = 4.0
	_zap.max_distance = 25.0
	_zap.position.y = height / 2.0
	add_child(_zap)

	var box := BoxShape3D.new()
	box.size = Vector3(width, height, DEPTH)
	trigger_shape.shape = box
	trigger_shape.position = Vector3(0.0, height / 2.0, 0.0)

	# Each beam is a thin hot core inside a wider soft glow, both lying along x
	for material: ShaderMaterial in [_core_material, _glow_material]:
		material.shader = BEAM_SHADER
		material.set_shader_parameter("color", BEAM_COLOR)
	_core_material.set_shader_parameter("edge", 1.0)
	_glow_material.set_shader_parameter("edge", 3.0)
	_set_beam_intensity(1.0)
	var core_mesh := _beam_mesh(BEAM_THICKNESS * 0.35, _core_material)
	var glow_mesh := _beam_mesh(BEAM_THICKNESS * 1.8, _glow_material)

	_lens_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_lens_material.albedo_color = BEAM_COLOR
	_lens_material.emission_enabled = true
	_lens_material.emission = BEAM_COLOR
	var lens_mesh := CylinderMesh.new()
	lens_mesh.top_radius = 0.022
	lens_mesh.bottom_radius = 0.022
	lens_mesh.height = 0.02
	lens_mesh.radial_segments = 12
	lens_mesh.material = _lens_material

	for i in beam_count:
		var y := height * float(i + 1) / float(beam_count + 1)
		for mesh: Mesh in [core_mesh, glow_mesh]:
			var beam := MeshInstance3D.new()
			beam.mesh = mesh
			beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			beam.rotation.z = PI / 2.0
			beam.position.y = y
			beams_root.add_child(beam)
		for side: float in [-1.0, 1.0]:
			var lens := MeshInstance3D.new()
			lens.mesh = lens_mesh
			lens.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			lens.rotation.z = PI / 2.0
			lens.position = Vector3(side * (width / 2.0 + 0.005), y, 0.0)
			add_child(lens)

	for side: float in [-1.0, 1.0]:
		var post: Node3D = POST.instantiate()
		post.position = Vector3(side * (width / 2.0 + POST_SIZE / 2.0), 0.0, 0.0)
		post.scale.y = height / POST_BUILT_HEIGHT
		add_child(post)


func _beam_mesh(thickness: float, material: ShaderMaterial) -> CylinderMesh:
	var mesh := CylinderMesh.new()
	mesh.top_radius = thickness
	mesh.bottom_radius = thickness
	mesh.height = width
	mesh.radial_segments = 8
	mesh.rings = 1
	mesh.cap_top = false
	mesh.cap_bottom = false
	mesh.material = material
	return mesh
