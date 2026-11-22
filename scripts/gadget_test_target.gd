extends StaticBody3D
## TEMPORARY test target for the jammer (task C1), until the laser grid (C2) exists.
## A box with a red light that goes dark while jammed. Remove it once C2 lands.
## It follows the jammable contract: group "jammable", host-only jam(seconds).

const ON_COLOR := Color(1.0, 0.1, 0.1)
const OFF_COLOR := Color(0.15, 0.15, 0.15)

@onready var lamp: OmniLight3D = $Lamp
@onready var mesh: MeshInstance3D = $Mesh

var _jam_left := 0.0
var _material := StandardMaterial3D.new()


func _ready() -> void:
	add_to_group("jammable")
	_material.emission_enabled = true
	mesh.material_override = _material
	_show_jammed(false)
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


func _process(delta: float) -> void:
	if not multiplayer.is_server() or _jam_left <= 0.0:
		return
	_jam_left -= delta
	if _jam_left <= 0.0:
		_set_jammed.rpc(false)


## Host only: called by GadgetJammer. A second jam restarts the countdown, it doesn't add to it.
func jam(seconds: float) -> void:
	if not multiplayer.is_server():
		return
	_jam_left = seconds
	_set_jammed.rpc(true)


func _on_heist_reset(_respawn_players: bool) -> void:
	_jam_left = 0.0
	_set_jammed.rpc(false)


@rpc("authority", "call_local", "reliable")
func _set_jammed(jammed: bool) -> void:
	_show_jammed(jammed)


func _show_jammed(jammed: bool) -> void:
	lamp.visible = not jammed
	_material.albedo_color = OFF_COLOR if jammed else ON_COLOR
	_material.emission = OFF_COLOR if jammed else ON_COLOR
