extends Camera3D
## The opening shot behind the menu. It starts on the moon and comes down over Fifth Avenue to the
## curb, in front of the museum, then rests there breathing until a player's own camera takes over.

const MOON_DIRECTION := Vector3(-0.35, 0.72, -0.6)    # same as ext_night_sky.gdshader
const SHOT_TIME := 13.0
const START_AT := Vector3(24.0, 30.0, 50.0)    # high over the avenue, clear of the far side's towers
const HALFWAY_AT := Vector3(28.0, 13.0, 50.0)
const END_AT := Vector3(7.0, -2.9, 33.8)        # on the sidewalk, at the curb, out of the traffic
const END_LOOK := Vector3(-9.0, 10.0, 10.0)
const START_FOV := 26.0
const END_FOV := 66.0
const MENU_FADE_START := 2.0
const MENU_FADE_TIME := 2.2
const REST_SWAY := Vector3(0.22, 0.09, 0.0)

@export var menu_path: NodePath
@export var shade_path: NodePath

var _clock: float = 0.0
var _start_turn: Quaternion
var _end_turn: Quaternion


func _ready() -> void:
	_start_turn = Basis.looking_at(MOON_DIRECTION.normalized()).get_rotation_quaternion()
	_end_turn = Basis.looking_at((END_LOOK - END_AT).normalized()).get_rotation_quaternion()
	_pose(0.0)
	make_current()
	var menu := get_node_or_null(menu_path) as Control
	var shade := get_node_or_null(shade_path) as Control
	if menu != null and shade != null:
		menu.visibility_changed.connect(func() -> void: shade.visible = menu.visible)
		menu.modulate.a = 0.0
		shade.modulate.a = 0.0
		var fade := create_tween().set_parallel()
		fade.tween_property(menu, "modulate:a", 1.0, MENU_FADE_TIME).set_delay(MENU_FADE_START)
		fade.tween_property(shade, "modulate:a", 1.0, MENU_FADE_TIME).set_delay(MENU_FADE_START)


func _process(delta: float) -> void:
	if not current:
		set_process(false)    # a player's camera took over, and this one's work is done
		return
	_clock += delta
	if _clock < SHOT_TIME:
		_pose(_clock / SHOT_TIME)
	else:
		var rest := _clock - SHOT_TIME
		var drift := minf(rest / 4.0, 1.0)
		position = END_AT + Vector3(sin(rest * 0.23) * REST_SWAY.x, sin(rest * 0.31) * REST_SWAY.y, 0.0) * drift


## One point along the shot, from 0 at the moon to 1 at the curb. The camera holds on the moon for a
## moment, then tips down faster than it descends, so the museum comes up over the skyline.
func _pose(progress: float) -> void:
	var travel := smoothstep(0.0, 1.0, progress)
	var turn := smoothstep(0.12, 0.74, progress)
	var a := START_AT.lerp(HALFWAY_AT, travel)
	var b := HALFWAY_AT.lerp(END_AT, travel)
	position = a.lerp(b, travel)
	quaternion = _start_turn.slerp(_end_turn, turn)
	fov = lerpf(START_FOV, END_FOV, smoothstep(0.1, 0.9, progress))
