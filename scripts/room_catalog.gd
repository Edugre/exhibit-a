class_name RoomCatalog
extends RefCounted
## Every room scene the builder can use (task A0). The pool is filled in ahead of time with the
## four planned rooms, so the room tasks never have to edit this file: a room joins the shuffle
## as soon as its scene exists.

const ENTRANCE := "res://scenes/rooms/entrance_room.tscn"
const VAULT := "res://scenes/rooms/vault_room.tscn"

## The rooms the shuffle picks from, in a fixed order. The ordering rule (task A3) refers to them by index.
const POOL: PackedStringArray = [
	"res://scenes/rooms/sculpture_hall_room.tscn",
	"res://scenes/rooms/twin_archives_room.tscn",
	"res://scenes/rooms/laser_corridor_room.tscn",
	"res://scenes/rooms/security_office_room.tscn",
]


## Indexes into POOL of the rooms whose scene exists yet.
static func available_pool() -> PackedInt32Array:
	var found := PackedInt32Array()
	for i in POOL.size():
		if ResourceLoader.exists(POOL[i]):
			found.append(i)
	return found
