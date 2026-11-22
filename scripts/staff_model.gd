extends "res://scripts/guard_model.gd"
## A night staff member, as seen (docs/boss_and_staff.md). PLACEHOLDER LOOK until the staff get a
## character of their own: the player body, washed out to a pale grey-green so nobody mistakes them for
## a teammate, with a staff-green cap and a lantern held out in front. The lantern's beam is the
## librarian's, with the same reach and angle as their sight, so what you see is what spots you.
## Same states as hers, so the guard logic drives it unchanged. Cosmetic only.

const UNIFORM := Color(0.62, 0.68, 0.64)
const CAP := Color(0.16, 0.24, 0.19)
const LANTERN := Color(1.0, 0.78, 0.48)
## Clips from the player's rig. Ringing the bell uses the arms-up carry pose.
const STAFF_CLIPS := {
	State.IDLE: &"idle", State.PATROL: &"walk", State.ALERT: &"carry",
	State.CHASE: &"walk", State.TACKLE: &"carry", State.SHUSH: &"carry",
}
const WALK_STRIDE := 1.6


func _ready() -> void:
	_animation_player = find_child("AnimationPlayer", true, false) as AnimationPlayer
	for clip: StringName in [&"idle", &"walk", &"carry"]:
		_animation_player.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	_tint("PlayerBody", UNIFORM)
	_tint("PlayerAccent", CAP)

	var socket := Node3D.new()                 # out in front at chest height, pointing ahead (+Y forward)
	socket.position = Vector3(0.22, 1.1, -0.3)
	socket.rotation_degrees.x = -90.0
	add_child(socket)
	_add_light_to(socket)
	flashlight.light_color = LANTERN
	flashlight.light_energy = 2.5
	var bulb := MeshInstance3D.new()            # the lantern itself, a small warm glow
	var sphere := SphereMesh.new()
	sphere.radius = 0.06
	sphere.height = 0.12
	var glass := StandardMaterial3D.new()
	glass.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glass.albedo_color = LANTERN
	sphere.material = glass
	bulb.mesh = sphere
	bulb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	socket.add_child(bulb)

	_last_position = global_position
	_apply_state()


func _tint(mesh_name: String, colour: Color) -> void:
	var mesh := find_child(mesh_name, true, false) as MeshInstance3D
	var material := mesh.get_active_material(0).duplicate() as BaseMaterial3D
	material.albedo_color = colour
	mesh.set_surface_override_material(0, material)


func _physics_process(delta: float) -> void:
	var moved := global_position - _last_position
	_last_position = global_position
	moved.y = 0.0
	var step := moved.length() if moved.length() < TELEPORT_DISTANCE else 0.0
	_speed = lerpf(_speed, step / delta, 1.0 - exp(-SPEED_SMOOTHING * delta))
	_animation_player.speed_scale = _speed / WALK_STRIDE if state == State.PATROL and _speed > MOVING_SPEED else 1.0
	if _beam.visible:
		_trim_beam(delta)


func _apply_state() -> void:
	if not _animation_player:
		return
	_animation_player.play(STAFF_CLIPS[state], BLEND_TIME)
	# The beam shows while they walk their rounds; when they stop to ring, the lantern lights their face.
	_beam.visible = state == State.IDLE or state == State.PATROL
	_face_light.visible = state == State.ALERT
