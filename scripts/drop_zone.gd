extends Node3D
## The drop zone: where the artifact stops being the museum's problem.
## The host checks the rule and reports it to GameState. Every peer shows the paint
## lighting up while the artifact is on the move, from state it already receives.

const DONATED_REASON := "Donation withdrawn."

## Half the size of the painted frame, in metres, along x and z.
const HALF_SIZE := Vector2(2.1, 1.35)

const GLOW_ENERGY := 2.4
const GLOW_SPEED := 4.0

## The museum marks where this goes, so the level stays the one place that says so.
@export var spot_path: NodePath = ^"../Museum/ExtractionSpot"
@export var players_path: NodePath = ^"../Players"

var _glow_materials: Array[BaseMaterial3D] = []
var _glow_time: float = 0.0

@onready var players: Node3D = get_node(players_path)


func _ready() -> void:
	global_position = (get_node(spot_path) as Node3D).global_position
	for mesh_name: String in ["ZonePaint", "Hoofprints"]:
		var mesh := find_child(mesh_name, true, false) as MeshInstance3D
		var glow := mesh.get_active_material(0).duplicate() as BaseMaterial3D
		glow.emission_enabled = true
		glow.emission_texture = glow.albedo_texture
		glow.emission_energy_multiplier = 0.0
		mesh.set_surface_override_material(0, glow)
		_glow_materials.append(glow)


func _physics_process(delta: float) -> void:
	_update_glow(delta)
	if multiplayer.is_server():
		_check_delivery()


## Host only: the artifact counts as delivered the moment its carrier stands in the zone.
func _check_delivery() -> void:
	if GameState.phase != GameState.Phase.PLAYING:
		return
	if GameState.artifact_state != GameState.ArtifactState.CARRIED:
		return
	var carrier := players.get_node_or_null(str(GameState.artifact_holder)) as Node3D
	if carrier == null or not _is_inside(carrier.global_position):
		return
	GameState.set_artifact(GameState.ArtifactState.DELIVERED)
	GameState.end_heist(true, DONATED_REASON)


func _is_inside(point: Vector3) -> bool:
	var offset := point - global_position
	return absf(offset.x) <= HALF_SIZE.x and absf(offset.z) <= HALF_SIZE.y


func _update_glow(delta: float) -> void:
	var carried := GameState.artifact_state == GameState.ArtifactState.CARRIED
	_glow_time = _glow_time + delta * GLOW_SPEED if carried else 0.0
	var energy := GLOW_ENERGY * (0.65 + 0.35 * sin(_glow_time)) if carried else 0.0
	for glow in _glow_materials:
		glow.emission_energy_multiplier = energy
