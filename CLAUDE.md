# Exhibit A — notes for Claude Code

Two-player online co-op museum heist (stealth + puzzles) for a university game dev course.
Team: Eduardo Goncalvez, Alex Waisman, Jonathan Serrano.

## Engine
- Godot **4.7.2 stable, Standard edition, GDScript only**. Never upgrade or convert the project.
- 3D, Forward+ renderer. Placeholder geometry (CSG boxes, primitive meshes) is fine.

## Architecture rules (do not break these)
- **Host is the referee.** ENet, host = peer 1. The host owns all game state: timer, guard AI,
  puzzle state, artifact ownership, win/lose, restart.
- **Clients only ask.** Clients send requests via RPC; the host validates and replicates the result.
  Never let a client change shared game state directly.
- **Exception: movement.** Each player has authority over its own character
  (`set_multiplayer_authority(name.to_int())` in `_enter_tree`), synced by a MultiplayerSynchronizer.
- Players are spawned only by the host, named after their peer id, under `World/Players`,
  replicated by the `PlayerSpawner` (MultiplayerSpawner).
- Autoloads: `NetworkManager` (connection), `GameState` (added in Phase 5).

## Course constraints
- The team writes the gameplay rules: puzzle conditions, artifact ownership/scoring, guard decisions,
  noise/distraction, timer, outcome logic. Godot may provide rendering, physics, navigation, networking.
- No addons, Asset Library plugins, or prebuilt gameplay packages.
- When you use a new built-in engine system, add it to README → "Godot-provided systems".

## Conventions
- Folders: `scenes/`, `scripts/`, `ui/`, `assets/placeholder/`. snake_case file names.
- Input actions (already defined, use these exact names): `move_forward`, `move_back`, `move_left`,
  `move_right`, `jump`, `sneak`, `interact`, `throw`.
- Typed GDScript (`var x: int`, `-> void`), tabs for indentation.

## Workflow
- Do only the phase/task you're asked for. Don't start later phases.
- Never edit anything in `.godot/`.
- After changes, run a headless check (`godot --headless --quit`) and report errors.
- Don't commit; the human reviews `git diff` and commits.
- Multiplayer can't be verified headlessly — say what the human should play-test.
