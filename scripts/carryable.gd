class_name Carryable
extends RigidBody3D
## Anything a player can pick up into their hotbar: the throwables and the Signal Jammer.
## The host decides who holds it (holder_id) and in which of the holder's slots it sits (slot); the
## MultiplayerSynchronizer copies both. Which slot is in hand is the holder's own choice
## (player.selected_slot, synced from them), so each peer works out what to draw from those three values.
## Using or dropping an item is always asked of the host, which checks holder_id again.

const SLOTS := 4
const DROP_REACH := 0.7  # how far in front of you something lands when you put it down

## What the hotbar calls it.
@export var display_name := "Item"

## Peer id of the player carrying it, 0 if it's lying somewhere. Replicated.
@export var holder_id := 0:
	set(value):
		holder_id = value
		if value == 0:
			slot = -1
		_holder_changed()

## Which hotbar slot it's in, 0 to SLOTS - 1, or -1 when nobody holds it. Replicated.
@export var slot := -1


func _enter_tree() -> void:
	add_to_group("carryables")


## Subclasses react to being picked up or let go (hide a collider, a model...).
func _holder_changed() -> void:
	pass


func find_holder() -> Node3D:
	if holder_id == 0:
		return null
	for player in get_tree().get_nodes_in_group("players"):
		if player.name == str(holder_id):
			return player as Node3D
	return null


## True on every peer while it's in its holder's hand: its slot is the one they've picked, and the
## book isn't taking up both their hands.
func in_hand() -> bool:
	var holder := find_holder()
	if holder == null or holder.get("selected_slot") != slot:
		return false
	return not (GameState.artifact_state == GameState.ArtifactState.CARRIED and GameState.artifact_holder == holder_id)


## Everything a player is carrying, in no particular order.
static func held_by(tree: SceneTree, peer_id: int) -> Array[Carryable]:
	var found: Array[Carryable] = []
	if peer_id == 0:
		return found
	for item: Carryable in tree.get_nodes_in_group("carryables"):
		if item.holder_id == peer_id and not item.is_queued_for_deletion():
			found.append(item)
	return found


## What's in one of a player's slots, or null.
static func in_slot(tree: SceneTree, peer_id: int, index: int) -> Carryable:
	for item in held_by(tree, peer_id):
		if item.slot == index:
			return item
	return null


## The first empty slot, or -1 when the hotbar is full.
static func free_slot(tree: SceneTree, peer_id: int) -> int:
	var used := {}
	for item in held_by(tree, peer_id):
		used[item.slot] = true
	for index in SLOTS:
		if not used.has(index):
			return index
	return -1


# --- Host only -------------------------------------------------------------------

## Puts it in the player's first free slot. False if it's already held or their hotbar is full.
func take(peer_id: int) -> bool:
	if not multiplayer.is_server() or holder_id != 0:
		return false
	var index := free_slot(get_tree(), peer_id)
	if index < 0:
		return false
	holder_id = peer_id
	slot = index
	freeze = true
	return true


## Sets it down on the floor in front of whoever holds it. Quietly: a dropped thing makes no noise.
func drop_from(player: Node3D) -> void:
	if not multiplayer.is_server() or holder_id != player.name.to_int():
		return
	var forward := -player.global_basis.z
	global_position = player.global_position + forward * DROP_REACH + Vector3(0.0, 0.4, 0.0)
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	holder_id = 0
	freeze = false
