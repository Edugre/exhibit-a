class_name GuardBudget
extends RefCounted
## How many night staff a run gets, and which ones. Pure functions, like RoomOrder, so the same seed always
## gives the same staff and the rule can be tested without a scene. Only the host calls it; clients get the
## result inside the room spawn data, so they never roll.
##
## Every room scene comes with its own staff (the Security Office with two), so a run used to get up to five
## of them, plus the librarian. The rule:
##   1. A room keeps at most one of its staff (the first one in the scene).
##   2. The run gets one staff for every ROOMS_PER_STAFF rooms behind the lobby, rounded up: three pool rooms
##      and the vault make four rooms, so two staff. With the librarian, three guards in the building.
##   3. The vault gallery keeps its staff first: the plates are the last test, and someone should be watching.
##   4. The rest go to the pool rooms that have staff, drawn by our Fisher–Yates on the run's seed (offset, so
##      it doesn't just follow the room order). A room that loses its staff is still patrolled by the librarian.

const ROOMS_PER_STAFF := 2
## Added to the run's seed for the draw, so it's independent of the room shuffle.
const SEED_OFFSET := 7919


## How many staff a run of `rooms` rooms behind the lobby gets.
static func budget(rooms: int) -> int:
	return ceili(float(rooms) / ROOMS_PER_STAFF)


## `staff` holds, for each room behind the lobby in run order, the names of its staff (empty if it has none).
## `always` is the index of the room that keeps its staff first (the vault), or -1.
## Returns, for each of those rooms, the names of the staff it keeps.
static func pick(staff: Array, always: int, seed_value: int) -> Array:
	var keep: Array = []
	for names in staff:
		keep.append(PackedStringArray())
	var left := budget(staff.size())
	if always >= 0 and always < staff.size() and not (staff[always] as PackedStringArray).is_empty() and left > 0:
		keep[always] = PackedStringArray([staff[always][0]])
		left -= 1

	var candidates := PackedInt32Array()
	for index in staff.size():
		if index != always and not (staff[index] as PackedStringArray).is_empty():
			candidates.append(index)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value + SEED_OFFSET
	for index in RoomOrder.shuffled(candidates, rng):
		if left <= 0:
			break
		keep[index] = PackedStringArray([staff[index][0]])
		left -= 1
	return keep
