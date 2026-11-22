class_name Room
extends Node3D
## One room of the museum (task A0). Every room scene copies scenes/rooms/room_template.tscn
## and keeps this layout:
##
##   Room (this script)
##     Entry, Exit           Marker3D at the doorway centres, on the floor. Rooms run along -Z,
##                           Entry at local (0, 0, 0). The vault has no Exit: it's the end of the run.
##     NavigationRegion3D    Everything guards walk on or around: the Geometry (CSG, use_collision on)
##                           and every prop that blocks the way. Baked when the room is built, so no
##                           one has to press Bake. Moving parts (gates) stay outside it.
##       Geometry
##     EntryLink             NavigationLink3D through the Entry doorway, so a guard can follow
##                           you into the previous room.
##     Ceiling               Outside the region, so its top isn't baked as floor.
##   Optional: GuardWaypoints (patrol loop, guards are children of the room), ThrowableSpots,
##   ExitGate (a RoomGate), GadgetSocket. Entrance and vault only: SpawnPoints, ArtifactSpot,
##   ExtractionSpot.
##
## The builder lines rooms up so each Entry sits on the previous room's Exit. Rooms are never rotated.

## The navmesh is ready, a frame after the room enters the tree. Guards should wait for it
## (and one more physics frame for the navigation map to sync) before asking for paths.
signal baked

## The contract sizes. assets/interior/source/tools/int_dims.py mirrors them for the art.
const DOOR_WIDTH := 3.0
const WALL_HEIGHT := 4.0
const WALL_THICKNESS := 0.5
## Must match cell_height in the template's NavigationMesh.
const NAV_CELL_HEIGHT := 0.1

## Gadget targets (task C2 and later) join this group and implement a host-only
## `jam(seconds: float) -> void`. The gadget finds them through the group.
const JAMMABLE_GROUP := &"jammable"

## Bake the navmesh on load. Turn it off only for a room whose navmesh you baked by hand.
@export var bake_on_ready := true

@onready var entry: Marker3D = $Entry
@onready var exit: Marker3D = get_node_or_null(^"Exit")
@onready var nav_region: NavigationRegion3D = $NavigationRegion3D


func _ready() -> void:
	add_to_group("rooms")
	if bake_on_ready:
		# CSG builds its shapes at the end of the frame it enters the tree, so wait for them.
		await get_tree().process_frame
		# Rooms bake at a 0.1 m cell height so a 0.46 m bench isn't a step guards can climb.
		# The map has to match, or it warns and merges coarser. (Task A1 may move this to project settings.)
		NavigationServer3D.map_set_cell_height(get_world_3d().navigation_map, NAV_CELL_HEIGHT)
		# Every instance of a room scene shares its NavigationMesh resource; bake into a copy of our own.
		nav_region.navigation_mesh = nav_region.navigation_mesh.duplicate()
		nav_region.bake_navigation_mesh(false)  # small rooms bake in a few milliseconds
		baked.emit()


## Moves the room so its Entry sits on `point` (the previous room's Exit, in world space).
func snap_entry_to(point: Vector3) -> void:
	global_position += point - entry.global_position


## How far the room reaches along -Z, from Entry to Exit. 0 for the vault.
func get_length() -> float:
	return entry.position.z - exit.position.z if exit else 0.0


func get_spawn_points() -> Array[Marker3D]:
	return _markers(^"SpawnPoints")


func get_throwable_spots() -> Array[Marker3D]:
	return _markers(^"ThrowableSpots")


## The node whose children are the patrol markers, the shape guard.gd expects. null if none.
func get_guard_waypoints() -> Node3D:
	return get_node_or_null(^"GuardWaypoints") as Node3D


func get_artifact_spot() -> Marker3D:
	return get_node_or_null(^"ArtifactSpot") as Marker3D


func get_extraction_spot() -> Marker3D:
	return get_node_or_null(^"ExtractionSpot") as Marker3D


func get_exit_gate() -> RoomGate:
	return get_node_or_null(^"ExitGate") as RoomGate


func get_gadget_socket() -> Marker3D:
	return get_node_or_null(^"GadgetSocket") as Marker3D


func _markers(path: NodePath) -> Array[Marker3D]:
	var found: Array[Marker3D] = []
	var holder := get_node_or_null(path)
	if holder:
		for child in holder.get_children():
			if child is Marker3D:
				found.append(child)
	return found
