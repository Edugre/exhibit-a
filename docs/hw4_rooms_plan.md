# HW #4 plan: additional rooms + procedural ordering

Status: draft for the team to review. The new gadget is a separate task; this plan only
leaves a hook for it.

## Decisions

- **Linear chain.** The entrance lobby first, then 3 shuffled rooms, then the vault last.
- **Pool of 4 rooms, 3 used per run**, in random order. Both the order and which room is left out change.
- **New order on every restart.** The host picks it; both peers rebuild.
- **Room content:** guard patrols, co-op puzzle gates, throwable pickups, and a hook for the new gadget.

## Run layout

```
(plaza + van) -> [Entrance lobby] -> [Pool room] -> [Pool room] -> [Pool room] -> [Gallery + Vault]
       fixed                  shuffled: 3 of 4                          fixed (HW #3 puzzle)
```

The current gallery, plates and vault become the fixed **Vault room**. The HW #3 puzzle and
the artifact stay exactly as they are. Since the exterior merged (`museum-extras`), the van and
drop zone live outside on the plaza (`World/Exterior`, `World/Getaway`) and stay there. The fixed
**Entrance room** is the lobby inside the front doors, which joins the exterior to the first shuffled room.
Players enter through the lobby, cross the museum to steal the artifact, and carry it all the way
back out to the van. Every room is crossed twice, so the stealth matters more.

## Room contract (every room scene follows this)

`scenes/rooms/<name>_room.tscn`, root `Node3D` with `scripts/room.gd` (`class_name Room`):

| Child | Required | Purpose |
|---|---|---|
| `Entry`, `Exit` (Marker3D) | yes (vault: no Exit) | Doorway centres, on the floor. The rooms run along -Z, Entry at local z = 0. |
| `NavigationRegion3D` | yes | This room's own navmesh, **baked at runtime** a frame after the room loads (0.1 m cell height, so benches aren't steps). Put the `Geometry` *and every blocking prop* under it. Moving parts like gates stay outside it. |
| `NavigationRegion3D/Geometry` (CSGCombiner3D, `use_collision`) | yes | Floor and walls, with a doorway of fixed width (3 m) at Entry and Exit. **All geometry stays inside the room's footprint**, so the walls of two neighbouring rooms sit back to back and never overlap. |
| `EntryLink` (NavigationLink3D) | yes | Joins this room's navmesh to the previous room's through the Entry doorway. |
| `Ceiling` | yes | Outside the region, so its top isn't baked as floor. |
| `GuardWaypoints` | optional | Patrol loop for this room's guard(s). Guards are children of the room. |
| `ThrowableSpots` (Marker3Ds) | optional | Where throwables are placed. |
| `ExitGate` (`scenes/room_gate.tscn`, `RoomGate`) | optional | A door across the Exit. `starts_open` for rooms with no puzzle. A puzzle rule calls `open()`. It opens by itself once the artifact is taken (`stays_open_on_return`). |
| `GadgetSocket` | optional | Marks where the HW #4 gadget can act (laser grid, camera...). |
| `ArtifactSpot` | vault only | Where the artifact rests. (Spawns and the extraction spot are outside, under `Museum/Plaza`.) |

The builder (`scripts/museum_layout.gd` on `World/Museum`) places room N+1 so its `Entry` sits on room N's `Exit`,
starting at the front doorway (z = 6). No rotation is needed.

**Depth budget:** the exterior reserves 60 m behind the doors (z 6 to -54). The lobby takes 6 m and the gallery
and vault 18 m, so **each pool room may be at most 12 m deep** (Entry to Exit), like the template. Width is free
up to 50 m. The builder warns if a run is too deep. To try your room in a run, set `debug_order` on
`World/Museum` in `main.tscn` (indexes into `RoomCatalog.POOL`).
Start a new room by duplicating `scenes/rooms/room_template.tscn`. Gadget targets join the
`"jammable"` group (`Room.JAMMABLE_GROUP`) and implement a host-only `jam(seconds: float)`.

## Networking approach

- *(Done in A2.)* A **`RoomSpawner` (MultiplayerSpawner)** under `World/Museum`, with a `spawn_function`,
  using the same pattern as `PlayerSpawner`. The host spawns rooms with `{path, name, door}`.
  The spawner rebuilds them on the client, replays them to a peer who joins late, and makes sure
  synchronizers inside rooms (guards, doors, plates) exist before they sync.
- **Host is the referee for the order.** *(Done in A3.)* `scripts/room_order.gd` (`RoomOrder`) shuffles the
  finished pool rooms with our own seeded Fisher–Yates on a `RandomNumberGenerator`, then keeps rooms in that
  order while they still fit the depth budget, up to 3. A room that doesn't fit is skipped, so an oversized room
  makes a run shorter rather than too deep. `Array.shuffle()` uses the global random state, so we don't use it.
  Only the result is sent; clients never roll. The host prints `Museum run N (seed S): ...`; set `debug_seed`
  on `World/Museum` to replay a run, or `debug_order` to force one.
- **Restart:** *(done in A2)* the host frees the old rooms and spawns new ones; the players respawn on the plaza.
  Each guard waits for her room's navmesh to reach the navigation server before she moves. Room node names
  include a build counter (`vault_room_3`) so old and new paths never collide. Only the host bakes navmeshes.
- **Hard-coded paths to remove:** `artifact.gd` (`../Museum/ArtifactSpot`), `drop_zone.gd`
  (`../Museum/ExtractionSpot`), `guard.gd` (`../Museum/GuardWaypoints`), and `main.gd`
  (`World/Museum/SpawnPoints`). These are looked up from the built layout instead, and the
  artifact re-reads its home spot on `heist_reset`.

## Room pool (proposal, open to change)

1. **Sculpture Hall** has one guard on a long patrol, crates for cover, and a throwable. The exit is always open.
2. **Twin Archives** is a co-op gate. Two plates sit in alcoves split by a wall, and both must be
   pressed within 2 s of each other to open the exit (a variant of the HW #3 rule, not a copy).
3. **Laser Corridor** is the gadget hook. A laser grid blocks the exit and touching it alerts guards.
   Until the gadget exists, one player holds a switch to drop the grid while the other crosses.
4. **Security Office** has two guards whose patrols cross, and two throwables. The exit is always open.

The gate rooms have their exit gate *open on the way back*, so the return trip with the
artifact is about stealth, not repeating puzzles.

## Work breakdown (in order; each step should leave the game playable)

> The task split for three developers, with dependencies, is in [hw4_team_plan.md](hw4_team_plan.md).
> The list below is the single-developer view of the same work.

1. **Room contract + split.** Add `room.gd`, then turn `museum.tscn` into `entrance_room` and
   `vault_room`, built in a fixed order by the builder. The game plays exactly like HW #3. *Play-test checkpoint.*
2. **RoomSpawner + path refactor.** Rooms are spawned by the host, with a late join and a restart rebuild.
   The order is still fixed. *Play-test checkpoint.*
3. **Ordering rule.** Seeded pick-3-of-4 shuffle, a new order on each restart, and the order shown in the HUD
   or a debug print.
4. **The four pool rooms.** These can be split across teammates once step 1 defines the contract.
5. **Gate scripts.** Twin Archives timing rule and the Laser Corridor switch and grid.
6. **README.** Add "Systems we wrote" (room ordering, gates) and "Godot-provided systems"
   (RandomNumberGenerator, per-room NavigationRegion3D linking), and update the known limitations.

## Risks to check early

- Navmesh regions merging across doorways, so a guard can chase through a door. Test this in step 2.
- Synchronizer timing when rooms are freed and re-spawned on restart.
- The run length versus the 180 s timer: the museum gets about 3× longer, so the timer likely needs tuning.

## Play-test checklist (needs two instances; can't be checked headlessly)

- Both peers see the same room order. A client joining after the host started also sees it.
- A restart shows a new order on both peers, and the players are at the entrance.
- A guard chases across a doorway. Gates open for both peers. The artifact can be carried through every room.
