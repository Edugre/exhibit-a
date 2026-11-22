class_name MuseumLayout
extends Node3D
## The museum (tasks A1, A2): the plaza outside, and the chain of rooms behind the front doors.
## The host builds the rooms in a line from the doorway inward (the entrance lobby, the pool
## rooms, then the vault) when it starts hosting, and again on every restart. The RoomSpawner
## (MultiplayerSpawner) builds the same rooms on the client, including one who joins late, so
## node paths match for the synchronizers and interact requests. RoomOrder (task A3) picks the pool
## rooms and their order from a new seed every build.
##
## Other systems ask this node (group "museum") where things are, instead of hard-coding paths.

## The exterior's front doorway, where the entrance room's Entry goes (ext_dims.py: ROOMS_Z front).
const FRONT_DOOR := Vector3(0.0, 0.0, 6.0)
## How deep the rooms may reach in all: the exterior reserves z from 6 back to -54 (ROOMS_Z).
const DEPTH := 60.0

## Testing only: these pool rooms, in this order, instead of the shuffle. Indexes into
## RoomCatalog.POOL (0 Sculpture Hall, 1 Twin Archives, 2 Laser Corridor, 3 Security Office).
## Set it on World/Museum in main.tscn to try your room in a real run.
@export var debug_order: PackedInt32Array = []
## Testing only: build every run from this seed (the host prints each run's seed), to replay one.
## -1 picks a new seed every build.
@export var debug_seed := -1

## The seed and pool rooms of the current build, for debugging.
var last_seed := 0
var last_order := PackedInt32Array()

## Counts builds, so a rebuilt room never shares a node path with the one it replaces.
var _build := 0
## Draws a fresh seed for each run.
var _seeds := RandomNumberGenerator.new()
## Room scene path -> depth in metres, measured once.
var _depths := {}

@onready var _rooms_root: Node3D = $Rooms
@onready var _plaza: Node3D = $Plaza
@onready var _spawner: MultiplayerSpawner = $RoomSpawner


func _ready() -> void:
	add_to_group("museum")
	_spawner.spawn_function = _create_room
	_seeds.randomize()
	GameState.heist_reset.connect(_on_heist_reset)  # only fires on the host


## Host only. Replaces the rooms with entrance, the pool rooms, then the vault. Called when hosting
## starts and on every restart; the spawner copies each room to the client.
func build() -> void:
	if not multiplayer.is_server():
		return
	for room in get_rooms():
		room.queue_free()  # the spawner removes it on the client too
	_build += 1
	last_seed = debug_seed if debug_seed >= 0 else _seeds.randi()
	last_order = debug_order if not debug_order.is_empty() else _pick(last_seed)
	print("Museum run %d (seed %d): %s" % [_build, last_seed, ", ".join(_names(last_order))])
	var paths: Array[String] = [RoomCatalog.ENTRANCE]
	for index in last_order:
		if index < 0 or index >= RoomCatalog.POOL.size() or not ResourceLoader.exists(RoomCatalog.POOL[index]):
			push_warning("MuseumLayout: no pool room %d yet, skipping it." % index)
			continue
		paths.append(RoomCatalog.POOL[index])
	paths.append(RoomCatalog.VAULT)

	var door := FRONT_DOOR
	var last: Room = null
	for path in paths:
		last = _spawner.spawn({
			"path": path,
			"name": "%s_%d" % [path.get_file().get_basename(), _build],
			"door": door,
		})
		if last.exit:
			door = last.position + last.exit.position
	var back := last.position.z + _deepest_z(last)
	if FRONT_DOOR.z - back > DEPTH + 0.01:
		push_warning("MuseumLayout: the rooms reach %.1f m deep; the building only has %.0f m." % [FRONT_DOOR.z - back, DEPTH])


## Runs on every peer with the data the host passed to spawn(), so all peers build the same room.
## It's placed before it enters the tree, so its colliders and navmesh are built where it stays.
func _create_room(data: Dictionary) -> Node:
	var room := (load(data.path) as PackedScene).instantiate() as Room
	room.name = data.name
	room.position = data.door - (room.get_node(^"Entry") as Node3D).position
	return room


func _on_heist_reset(respawn_players: bool) -> void:
	if respawn_players:
		build()  # a restart gets a new run: new rooms in a new order, doors shut, guards on patrol


## The shuffle and fit rule lives in RoomOrder; this gathers what it needs.
func _pick(seed_value: int) -> PackedInt32Array:
	var available := RoomCatalog.available_pool()
	var depths := {}
	for index in available:
		depths[index] = _depth_of(RoomCatalog.POOL[index])
	var budget := DEPTH - _depth_of(RoomCatalog.ENTRANCE) - _depth_of(RoomCatalog.VAULT)
	return RoomOrder.pick(available, depths, budget, seed_value)


## How deep a room scene is, Entry to Exit (or to its back wall), measured once from a throwaway copy.
func _depth_of(path: String) -> float:
	if not _depths.has(path):
		var room := (load(path) as PackedScene).instantiate() as Node3D
		var entry_z := (room.get_node(^"Entry") as Node3D).position.z
		_depths[path] = entry_z - _deepest_z(room)
		room.free()
	return _depths[path]


func _names(order: PackedInt32Array) -> PackedStringArray:
	var names := PackedStringArray()
	for index in order:
		names.append(RoomCatalog.POOL[index].get_file().get_basename() if index >= 0 and index < RoomCatalog.POOL.size() else str(index))
	return names if not names.is_empty() else PackedStringArray(["no pool rooms"])


## The rooms in the current build, front to back. Rooms on their way out are left out.
func get_rooms() -> Array[Room]:
	var rooms: Array[Room] = []
	for child in _rooms_root.get_children():
		if child is Room and not child.is_queued_for_deletion():
			rooms.append(child)
	return rooms


## Where players start: on the plaza, by the van.
func get_spawn_points() -> Array[Marker3D]:
	var found: Array[Marker3D] = []
	for child in _plaza.get_node(^"SpawnPoints").get_children():
		found.append(child as Marker3D)
	return found


## Where the drop zone goes: on the plaza, behind the van.
func get_extraction_spot() -> Marker3D:
	return _plaza.get_node(^"ExtractionSpot") as Marker3D


## Where the artifact rests at the start of a heist: in the vault. null until the rooms exist
## (in the menu, or on a client while the spawner is still building them).
func get_artifact_spot() -> Marker3D:
	for room in get_rooms():
		var spot := room.get_artifact_spot()
		if spot:
			return spot
	return null


## How far back the room's last wall reaches, in its own z (the vault has no Exit to measure by).
func _deepest_z(room: Node3D) -> float:
	var exit := room.get_node_or_null(^"Exit") as Node3D
	if exit:
		return exit.position.z
	var lowest := 0.0
	var geometry := room.get_node_or_null(^"NavigationRegion3D/Geometry")
	if geometry:
		for child in geometry.get_children():
			if child is CSGBox3D:
				lowest = minf(lowest, child.position.z - child.size.z / 2.0)
	return lowest
