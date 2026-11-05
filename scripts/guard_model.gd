extends Node3D
## The visible guard: a very old librarian on an NFL body.
## Cosmetic only. The host's guard logic decides what she does and sets `state`;
## this script just shows it and holds no game state of its own.

enum State { IDLE, PATROL, ALERT, CHASE, TACKLE, SHUSH }

const CLIPS := {
	State.IDLE: &"guard_idle",
	State.PATROL: &"guard_patrol",
	State.ALERT: &"guard_alert",
	State.CHASE: &"guard_chase",
	State.TACKLE: &"guard_tackle",
	State.SHUSH: &"guard_shush",
}
const BLEND_TIME := 0.2

## Metres one loop of each clip covers. Playback follows speed so planted feet don't slide.
const STRIDES := {State.PATROL: 0.9, State.CHASE: 3.2}
const SPEED_SMOOTHING := 12.0
const MOVING_SPEED := 0.2
## Nobody covers this far on foot in one tick, so a jump this big is a respawn, not a step.
const TELEPORT_DISTANCE := 1.0

## Match these in the guard's detection logic so what players see is what catches them.
const BEAM_RANGE := 9.0
const BEAM_ANGLE := 16.0

const GLARE_TIME := 0.15
const GLARE_ENERGY := 5.0

## Set by whatever drives the guard. Alert, tackle and shush play once and hold their last frame.
@export var state: State = State.IDLE:
	set(value):
		state = value
		_apply_state()

var _animation_player: AnimationPlayer
var _lens_material: BaseMaterial3D
var _lens_alpha: float = 1.0
var _glare_tween: Tween
var _beam: MeshInstance3D
var _face_light: OmniLight3D
var _last_position: Vector3
var _speed: float = 0.0


func _ready() -> void:
	_animation_player = find_child("AnimationPlayer", true, false) as AnimationPlayer
	for looping: State in [State.IDLE, State.PATROL, State.CHASE]:
		_animation_player.get_animation(CLIPS[looping]).loop_mode = Animation.LOOP_LINEAR

	var lens := find_child("GuardLens", true, false) as MeshInstance3D
	_lens_material = lens.get_active_material(0).duplicate() as BaseMaterial3D
	_lens_material.metallic_specular = 0.1  # keeps the sky out of the lenses so her eyes show
	_lens_material.emission_enabled = true
	_lens_material.emission = Color.WHITE
	_lens_material.emission_energy_multiplier = 0.0
	_lens_alpha = _lens_material.albedo_color.a
	lens.set_surface_override_material(0, _lens_material)

	_add_flashlight(find_child("Skeleton3D", true, false) as Skeleton3D)
	_last_position = global_position
	_apply_state()


func _physics_process(delta: float) -> void:
	var moved := global_position - _last_position
	_last_position = global_position
	moved.y = 0.0
	var step := moved.length() if moved.length() < TELEPORT_DISTANCE else 0.0
	_speed = lerpf(_speed, step / delta, 1.0 - exp(-SPEED_SMOOTHING * delta))

	if STRIDES.has(state) and _speed > MOVING_SPEED:
		_animation_player.speed_scale = _speed / STRIDES[state]
	else:
		_animation_player.speed_scale = 1.0


func _apply_state() -> void:
	if not _animation_player:
		return
	_animation_player.play(CLIPS[state], BLEND_TIME)

	# The beam shows only while she's calm: once her arms are pumping it would sweep across the
	# whole sky. For the shush the flashlight is held under her chin, lighting her face from below.
	_beam.visible = state == State.IDLE or state == State.PATROL
	_face_light.visible = state == State.SHUSH

	# Her glasses flash white when she stops being a sweet old lady.
	var glaring := state == State.ALERT or state == State.CHASE or state == State.TACKLE
	if _glare_tween:
		_glare_tween.kill()
	_glare_tween = create_tween()
	_glare_tween.tween_method(_set_glare, _current_glare(), 1.0 if glaring else 0.0, GLARE_TIME)


func _current_glare() -> float:
	return _lens_material.emission_energy_multiplier / GLARE_ENERGY


func _set_glare(amount: float) -> void:
	_lens_material.emission_energy_multiplier = amount * GLARE_ENERGY
	_lens_material.albedo_color.a = lerpf(_lens_alpha, 1.0, amount)


func _add_flashlight(skeleton: Skeleton3D) -> void:
	var socket := BoneAttachment3D.new()
	skeleton.add_child(socket)
	socket.bone_name = "flashlight_socket"

	var light := SpotLight3D.new()
	light.rotation_degrees.x = 90.0  # a spotlight shines along -Z, the socket points along +Y
	light.light_color = Color(1.0, 0.93, 0.74)
	light.light_energy = 4.0
	light.spot_range = BEAM_RANGE
	light.spot_angle = BEAM_ANGLE
	light.shadow_enabled = true
	socket.add_child(light)

	_face_light = OmniLight3D.new()
	_face_light.position.y = 0.04  # just past the lens, which sits under her chin
	_face_light.light_color = light.light_color
	_face_light.light_energy = 0.8
	_face_light.omni_range = 0.5
	socket.add_child(_face_light)

	# The beam fades out along its length. Cylinder sides use the top half of their UVs.
	var fade := Gradient.new()
	fade.set_color(0, Color(1.0, 1.0, 1.0, 0.0))
	fade.set_color(1, Color.WHITE)
	fade.set_offset(1, 0.5)
	var fade_texture := GradientTexture2D.new()
	fade_texture.gradient = fade
	fade_texture.fill_from = Vector2(0.0, 0.0)
	fade_texture.fill_to = Vector2(0.0, 1.0)

	var glow := StandardMaterial3D.new()
	glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glow.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glow.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	glow.cull_mode = BaseMaterial3D.CULL_DISABLED
	glow.albedo_color = Color(1.0, 0.93, 0.74, 0.1)
	glow.albedo_texture = fade_texture
	glow.texture_repeat = false

	var cone := CylinderMesh.new()
	cone.height = BEAM_RANGE
	cone.top_radius = BEAM_RANGE * tan(deg_to_rad(BEAM_ANGLE))
	cone.bottom_radius = 0.04
	cone.cap_top = false
	cone.cap_bottom = false
	cone.material = glow

	_beam = MeshInstance3D.new()
	_beam.mesh = cone
	_beam.position.y = BEAM_RANGE * 0.5
	_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	socket.add_child(_beam)
