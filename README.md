# Exhibit A
Two-player online co-op museum heist. Team: Eduardo, Alex Waisman, Jonathan Serrano.

**Engine:** Godot 4.7.2 (Standard, GDScript). Everyone must use this exact version.

## How to run
TBD

## Godot-provided systems
   - High-level multiplayer (ENetMultiplayerPeer, RPCs)
   - MultiplayerSpawner / MultiplayerSynchronizer (player spawning and position/rotation sync)
   - CharacterBody3D physics and CSG geometry
   - RayCast3D (detecting what the player is looking at)
   - Area3D (detecting players on the pressure plates)

## Systems we wrote
- (puzzle conditions, artifact ownership/scoring, guard logic, noise/distraction, timer, outcome logic)
- Pressure plate puzzle condition (scripts/vault_puzzle.gd)

## Asset credits
- (none yet)
