extends StaticBody3D
## The artifact in the world. Clients only ask for it; the host checks every request and records
## the result in GameState. Every peer then works out where to show the book from that state, so
## the one thing sent over the network here is the spot where it was put down.

## In a teammate's arms, relative to the carry_socket bone: resting on the forearms like a heavy
## tray, tipped forward so the face stays clear and anyone ahead can see the cover.
const ARMS_OFFSET := Transform3D(Basis(Vector3.RIGHT, 0.44), Vector3(0.0, -0.07, -0.07))
## In your own hands, relative to your camera, low enough to see past.
const VIEW_OFFSET := Transform3D(Basis(Vector3.RIGHT, 1.2), Vector3(0.0, -0.42, -0.62))
const VIEW_SCALE := 0.8
## Lying in the van's bay, relative to the van, so it rides away with it.
const BAY_OFFSET := Transform3D(Basis.IDENTITY, Vector3(0.05, 0.95, -0.55))

## How far in front of its carrier the book lands, and how high its middle sits when flat.
const DROP_REACH := 1.0
const WALL_MARGIN := 0.4
const FLOOR_HEIGHT := 0.12

@export var spot_path: NodePath = ^"../Museum/ArtifactSpot"
@export var players_path: NodePath = ^"../Players"
@export var van_path: NodePath = ^"../Getaway/TrojanVan"

var _home: Transform3D
var _dropped: Transform3D

@onready var shape: CollisionShape3D = $CollisionShape3D
@onready var model: Node3D = $Model
@onready var players: Node3D = get_node(players_path)
@onready var van: Node3D = get_node(van_path)


func _ready() -> void:
	_home = (get_node(spot_path) as Node3D).global_transform
	global_transform = _home


func _process(_delta: float) -> void:
	var state := GameState.artifact_state
	var holder := players.get_node_or_null(str(GameState.artifact_holder))
	var carried := state == GameState.ArtifactState.CARRIED and holder != null
	var in_my_hands: bool = carried and holder.is_multiplayer_authority()

	# Only something lying around can be looked at, walked into or picked up.
	shape.disabled = carried or state == GameState.ArtifactState.DELIVERED
	model.held_in_view = in_my_hands
	model.lying_flat = state == GameState.ArtifactState.DROPPED
	model.scale = Vector3.ONE * (VIEW_SCALE if in_my_hands else 1.0)

	if in_my_hands:
		global_transform = holder.camera.global_transform * VIEW_OFFSET
	elif carried:
		global_transform = holder.model.carry_anchor.global_transform * ARMS_OFFSET
	elif state == GameState.ArtifactState.DELIVERED:
		global_transform = van.global_transform * BAY_OFFSET
	elif state == GameState.ArtifactState.DROPPED:
		global_transform = _dropped
	else:
		global_transform = _home


# --- Host: the rules ---------------------------------------------------------

## Called by player.gd on the host, once it has checked who is asking and how far away they are.
func interact(peer_id: int) -> void:
	if not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
		return
	if _is_holding_something(peer_id):
		return
	var state := GameState.artifact_state
	if state == GameState.ArtifactState.AVAILABLE or state == GameState.ArtifactState.DROPPED:
		GameState.set_artifact(GameState.ArtifactState.CARRIED, peer_id)


## One thing in your hands at a time, so the book and a throwable can't overlap.
func _is_holding_something(peer_id: int) -> bool:
	for throwable: Throwable in get_tree().get_nodes_in_group("throwables"):
		if throwable.holder_id == peer_id:
			return true
	return false


## Any peer: asks the host to let go of the book.
func request_drop() -> void:
	_request_drop.rpc_id(1)


@rpc("any_peer", "call_local", "reliable")
func _request_drop() -> void:
	if not multiplayer.is_server() or GameState.phase != GameState.Phase.PLAYING:
		return
	var sender := multiplayer.get_remote_sender_id()
	if GameState.artifact_state != GameState.ArtifactState.CARRIED or GameState.artifact_holder != sender:
		return  # only the person holding it can let go
	var carrier := players.get_node_or_null(str(sender)) as Node3D
	if carrier == null:
		return
	_put_down.rpc(_landing_spot(carrier))
	GameState.set_artifact(GameState.ArtifactState.DROPPED)


func _landing_spot(carrier: Node3D) -> Transform3D:
	var space := get_world_3d().direct_space_state
	var forward := -carrier.global_basis.z
	var chest := carrier.global_position + Vector3.UP
	var spot := chest + forward * DROP_REACH

	var ahead := PhysicsRayQueryParameters3D.create(chest, spot)
	ahead.exclude = [carrier.get_rid()]
	var wall := space.intersect_ray(ahead)
	if not wall.is_empty():
		spot = chest + forward * maxf(chest.distance_to(wall["position"]) - WALL_MARGIN, 0.0)

	var down := PhysicsRayQueryParameters3D.create(spot, spot + Vector3.DOWN * 3.0)
	down.exclude = [carrier.get_rid()]
	var ground := space.intersect_ray(down)
	if ground.is_empty():
		spot = carrier.global_position  # nothing under that spot: it lands at their feet instead
	else:
		spot.y = ground["position"].y
	spot.y += FLOOR_HEIGHT
	return Transform3D(Basis(Vector3.UP, carrier.rotation.y), spot)


## Sent before the state change, on the same reliable channel, so no peer sees it land in the wrong place.
@rpc("authority", "call_local", "reliable")
func _put_down(at: Transform3D) -> void:
	_dropped = at
