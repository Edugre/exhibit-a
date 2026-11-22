class_name RoomOrder
extends RefCounted
## The procedural room ordering rule (task A3). Pure functions, so the same seed always gives the
## same run, and the rule can be tested without a scene. Only the host calls it; the result goes to
## clients as the rooms themselves, so clients never roll.
##
## The rule:
##   1. Shuffle every pool room that exists, with our own Fisher–Yates driven by a seeded
##      RandomNumberGenerator. (Array.shuffle() uses the global random state, so it can't replay a seed.)
##   2. Walk the shuffled list and keep each room that still fits in the depth left behind the doors,
##      until the run has ROOMS_PER_RUN rooms. A room that doesn't fit is skipped, not cut short.
##   3. The kept rooms go between the entrance and the vault in the order they were kept.

## How many pool rooms a run uses (the plan: 3 of 4).
const ROOMS_PER_RUN := 3


## Fisher–Yates: from the back, swap each slot with a random slot at or before it.
## Every order of `items` is equally likely for a fair random source.
static func shuffled(items: PackedInt32Array, rng: RandomNumberGenerator) -> PackedInt32Array:
	var out := items.duplicate()
	for i in range(out.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var held := out[i]
		out[i] = out[j]
		out[j] = held
	return out


## The pool rooms for one run, in order. `depths` maps each pool index to its depth in metres,
## and `budget` is how much depth the pool rooms may use in all.
static func pick(available: PackedInt32Array, depths: Dictionary, budget: float, seed_value: int) -> PackedInt32Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var run := PackedInt32Array()
	var left := budget
	for index in shuffled(available, rng):
		if run.size() >= ROOMS_PER_RUN:
			break
		var depth: float = depths.get(index, 0.0)
		if depth <= left + 0.001:
			run.append(index)
			left -= depth
	return run
