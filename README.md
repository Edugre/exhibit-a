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
   - glTF scene import, Skeleton3D skinning and AnimationPlayer (player and guard models)
   - BoneAttachment3D, SpotLight3D and Tween (guard flashlight and lens glare)
   - GPUParticles3D and a second Camera3D (the van's exhaust and the getaway shot)

## Systems we wrote
- (puzzle conditions, artifact ownership/scoring, guard logic, noise/distraction, timer, outcome logic)

## Asset credits
- Player and guard characters (`assets/characters/`): made for this project in Blender. Editable sources are in `assets/characters/source/`.
- Trojan Van, drop zone and road (`assets/getaway/`): made for this project in Blender. Editable source is in `assets/getaway/source/`.
