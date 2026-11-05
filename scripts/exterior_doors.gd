extends Node3D
## The two great bronze doors of the centre arch swing open for whoever walks up to them, and close again
## behind them. Cosmetic: the doorway itself is always clear, so this never decides who can get through.
## Every peer works it out from the player and guard positions it already has.

const OPEN_ANGLE := 100.0
const OPEN_RANGE := 7.0
const SWING_TIME := 1.25

## The hinges, and the groan of the bronze.
@export var left_hinge: NodePath
@export var right_hinge: NodePath
@export var groan: NodePath

var _open: bool = false
var _swing: Tween


func _process(_delta: float) -> void:
	var near := _anyone_near("players") or _anyone_near("guards")
	if near != _open:
		_open = near
		_move(near)


func _anyone_near(group: StringName) -> bool:
	for body: Node3D in get_tree().get_nodes_in_group(group):
		if body.global_position.distance_squared_to(global_position) < OPEN_RANGE * OPEN_RANGE:
			return true
	return false


func _move(opening: bool) -> void:
	var angle := OPEN_ANGLE if opening else 0.0
	if _swing:
		_swing.kill()
	_swing = create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_swing.tween_property(get_node(left_hinge), "rotation_degrees:y", angle, SWING_TIME)
	_swing.tween_property(get_node(right_hinge), "rotation_degrees:y", -angle, SWING_TIME)
	if not groan.is_empty():
		(get_node(groan) as AudioStreamPlayer3D).play()
