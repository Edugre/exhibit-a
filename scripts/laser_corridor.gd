extends Node
## Room rule for the Laser Corridor (task C3). A laser grid fills the doorway in the wall across the
## middle of the room, with a switch (a pressure plate) on each side of it.
## While anyone stands on either switch, the grid has no power. So one player holds the near switch while
## the other crosses, then the one across holds the far switch while the first one follows.
## The Signal Jammer is the shortcut: one charge drops the grid for both of them at once.
## Once the artifact has been taken, the grid stays off, so the way back out is about stealth.
## Only the host decides; the grid's and the plates' own syncs show it to the client.

@export var grid: LaserGrid
@export var switch_near: PressurePlate
@export var switch_far: PressurePlate

var _returning := false  # host only


func _ready() -> void:
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _physics_process(_delta: float) -> void:
	if not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
		return
	if not _returning:
		var taken := GameState.artifact_state == GameState.ArtifactState.CARRIED \
			or GameState.artifact_state == GameState.ArtifactState.DROPPED
		_returning = taken
	var held := switch_near.is_pressed or switch_far.is_pressed
	# set_powered() does nothing if the power doesn't change, so it's safe to call every frame.
	grid.set_powered(not held and not _returning)


func _on_heist_reset(_respawn_players: bool) -> void:
	_returning = false
