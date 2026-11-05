class_name VaultDoor
extends CSGBox3D
## The vault door. The host sets `is_open`; a MultiplayerSynchronizer copies it
## to the client, and the setter slides the door up on both peers.

@export var open_height := 3.8
@export var open_time := 0.8

@export var is_open := false:
	set(value):
		if value == is_open:
			return
		is_open = value
		_apply(true)

var _closed_y := 0.0


func _ready() -> void:
	_closed_y = position.y
	_apply(false)


func _apply(animate: bool) -> void:
	if not is_node_ready():
		return
	var target_y := _closed_y + (open_height if is_open else 0.0)
	if animate:
		create_tween().tween_property(self, "position:y", target_y, open_time)
	else:
		position.y = target_y
