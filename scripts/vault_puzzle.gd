extends Node
## Puzzle rule: both pressure plates must be held at the same time to open the door.

signal solved

@export var plate_a: PressurePlate
@export var plate_b: PressurePlate
@export var door: VaultDoor

var is_solved := false


func _ready() -> void:
	plate_a.pressed_changed.connect(_on_plate_changed)
	plate_b.pressed_changed.connect(_on_plate_changed)
	GameState.heist_reset.connect(_on_heist_reset)


func _on_plate_changed(_pressed: bool) -> void:
	if not multiplayer.is_server():
		return
	elif is_solved:
		return 
	
	if plate_a.is_pressed  && plate_b.is_pressed:
		is_solved = true
		door.is_open = true
		solved.emit()

func _on_heist_reset(_respawn_players: bool) -> void:
	is_solved = false
	door.is_open = false
	
