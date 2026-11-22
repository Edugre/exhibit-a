@tool
extends Node3D
## Two brass posts with a velvet rope between them (asset plan P1.4). The posts block you, the
## rope doesn't. Set `span` in the editor to stretch it; for a longer line, put barriers end to end.

## Post to post, in metres. The rope was built for 2 m and stretches to fit.
@export_range(0.8, 3.5, 0.05) var span := 2.0:
	set(value):
		span = value
		_apply()

const BUILT_SPAN := 2.0


func _ready() -> void:
	_apply()


func _apply() -> void:
	if not is_node_ready():
		return
	$PostB.position.x = span
	$Rope.scale.x = span / BUILT_SPAN
