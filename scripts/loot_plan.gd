class_name LootPlan
extends RefCounted
## Where the small loot goes in a run (stretch goal: scoring). Pure functions, like RoomOrder and GuardBudget,
## so the same seed always lays out the same loot, and the room seed in the menu replays it too. Only the host
## calls it; clients get the result inside each room's spawn data, so they never roll.
##
## Every room marks a few surfaces where something valuable could have been left (its LootSpots markers).
## The rule:
##   1. Each room fills half its spots, rounded up, so a room never has all of them and never has none.
##   2. Which spots, and what lies on each, are drawn by our Fisher–Yates on the run's seed (offset, so it
##      doesn't just follow the room order or the staff draw).
## Display case prizes aren't part of this: every case always holds its own prize, behind its glass.

## The small loot there is, in the order the draw picks from. Values live in each scene.
const KINDS: Array[String] = [
	"res://scenes/loot/gold_ring.tscn",
	"res://scenes/loot/scarab.tscn",
	"res://scenes/loot/laurel.tscn",
	"res://scenes/loot/purse.tscn",
	"res://scenes/loot/owl.tscn",
	"res://scenes/loot/dagger.tscn",
]
const SEED_OFFSET := 104729


## How many spots a room with `spots` spots fills.
static func filled(spots: int) -> int:
	return ceili(spots / 2.0)


## `spots` holds each room's number of loot spots, in run order. Returns, for each room, a list of
## [spot index, kind index] pairs (plain Arrays, so they travel in spawn data).
static func pick(spots: Array, seed_value: int) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value + SEED_OFFSET
	var plan: Array = []
	for count: int in spots:
		var indices := PackedInt32Array()
		for i in count:
			indices.append(i)
		var chosen: Array = []
		for i in RoomOrder.shuffled(indices, rng).slice(0, filled(count)):
			chosen.append([i, rng.randi_range(0, KINDS.size() - 1)])
		plan.append(chosen)
	return plan
