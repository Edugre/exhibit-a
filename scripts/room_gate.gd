class_name RoomGate
extends Node3D
## A door across a room's Exit (task A0). Closed, it blocks the way; open, it slides up into the wall.
## Only the host opens or closes it; a MultiplayerSynchronizer copies `is_open` to the client and
## the setter moves the door on both peers. A puzzle rule (like TwinPlateGate) calls open().
## Keep it outside the room's NavigationRegion3D, so the baked navmesh doesn't treat it as a wall.

const SLIDE_TIME := 1.2

## Open at the start of every heist. For rooms whose exit is always open.
@export var starts_open := false
## Once the artifact has been taken, open for good, so the way back out is about stealth,
## not doing the puzzle again.
@export var stays_open_on_return := true

@export var is_open := false:
	set(value):
		if value == is_open:
			return
		is_open = value
		_apply(true)

var _slide: Tween

@onready var leaf: Node3D = $Leaf
@onready var shape: CollisionShape3D = $Leaf/Body/CollisionShape3D


func _ready() -> void:
	is_open = starts_open
	_apply(false)
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _process(_delta: float) -> void:
	if not multiplayer.is_server() or is_open or not stays_open_on_return:
		return
	if GameState.phase != GameState.Phase.PLAYING:
		return
	var taken := GameState.artifact_state == GameState.ArtifactState.CARRIED \
		or GameState.artifact_state == GameState.ArtifactState.DROPPED
	if taken:
		open()


## Host only.
func open() -> void:
	if multiplayer.is_server():
		is_open = true


## Host only.
func close() -> void:
	if multiplayer.is_server():
		is_open = false


func _on_heist_reset(_respawn_players: bool) -> void:
	is_open = starts_open


func _apply(animate: bool) -> void:
	if not is_node_ready():
		return
	var target_y := Room.WALL_HEIGHT if is_open else 0.0
	shape.set_deferred("disabled", is_open)  # passable as soon as it starts rising
	if _slide:
		_slide.kill()
	if not animate:
		leaf.position.y = target_y
		return
	_slide = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	_slide.tween_property(leaf, "position:y", target_y, SLIDE_TIME)
