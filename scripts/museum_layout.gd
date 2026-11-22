class_name MuseumLayout
extends Node3D
## The museum (task A1): the plaza outside, and the chain of rooms behind the front doors.
## Builds the rooms in a line from the doorway inward: the entrance lobby, the pool rooms, then
## the vault. For now every peer builds the same fixed order in _ready, so node paths match for
## the synchronizers and interact requests. Task A2 moves the building to the host and a spawner;
## task A3 picks the pool rooms.
##
## Other systems ask this node (group "museum") where things are, instead of hard-coding paths.

## The exterior's front doorway, where the entrance room's Entry goes (ext_dims.py: ROOMS_Z front).
const FRONT_DOOR := Vector3(0.0, 0.0, 6.0)
## How deep the rooms may reach in all: the exterior reserves z from 6 back to -54 (ROOMS_Z).
const DEPTH := 60.0

## Pool rooms to put between the entrance and the vault, as indexes into RoomCatalog.POOL
## (0 Sculpture Hall, 1 Twin Archives, 2 Laser Corridor, 3 Security Office). Set it on
## World/Museum in main.tscn to try your room in a real run. Empty plays like HW #3.
@export var debug_order: PackedInt32Array = []

var _rooms: Array[Room] = []

@onready var _rooms_root: Node3D = $Rooms
@onready var _plaza: Node3D = $Plaza


func _ready() -> void:
	add_to_group("museum")
	build(debug_order)


## Replaces the rooms with entrance, the given pool rooms, then the vault.
func build(pool_order: PackedInt32Array) -> void:
	for room in _rooms:
		room.queue_free()
	_rooms.clear()
	var paths: Array[String] = [RoomCatalog.ENTRANCE]
	for index in pool_order:
		if index < 0 or index >= RoomCatalog.POOL.size() or not ResourceLoader.exists(RoomCatalog.POOL[index]):
			push_warning("MuseumLayout: no pool room %d yet, skipping it." % index)
			continue
		paths.append(RoomCatalog.POOL[index])
	paths.append(RoomCatalog.VAULT)

	var door := FRONT_DOOR
	for path in paths:
		var room := (load(path) as PackedScene).instantiate() as Room
		room.name = path.get_file().get_basename()  # the same on every peer
		# Place it before it enters the tree, so its colliders and navmesh are built where it stays
		room.position = door - (room.get_node(^"Entry") as Node3D).position
		_rooms_root.add_child(room)
		_rooms.append(room)
		var exit := room.get_node_or_null(^"Exit") as Node3D
		if exit:
			door = room.position + exit.position
	var last: Room = _rooms.back()
	var back := last.position.z + _deepest_z(last)
	if FRONT_DOOR.z - back > DEPTH + 0.01:
		push_warning("MuseumLayout: the rooms reach %.1f m deep; the building only has %.0f m." % [FRONT_DOOR.z - back, DEPTH])


func get_rooms() -> Array[Room]:
	return _rooms


## Where players start: on the plaza, by the van.
func get_spawn_points() -> Array[Marker3D]:
	var found: Array[Marker3D] = []
	for child in _plaza.get_node(^"SpawnPoints").get_children():
		found.append(child as Marker3D)
	return found


## Where the drop zone goes: on the plaza, behind the van.
func get_extraction_spot() -> Marker3D:
	return _plaza.get_node(^"ExtractionSpot") as Marker3D


## Where the artifact rests at the start of a heist: in the vault, the last room.
func get_artifact_spot() -> Marker3D:
	for room in _rooms:
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
