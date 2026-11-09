# Exhibit A
Two-player online co-op museum heist. Team: Eduardo Goncalvez, Alex Waisman, Jonathan Serrano.

**Engine:** Godot 4.7.2 (Standard, GDScript). Everyone must use this exact version.

## Gameplay video
Youtube Link: https://youtu.be/Om2ZqEZNuqk

## Team
- Eduardo Goncalvez (PID: 6526311)
- Alex Waisman (PID: 6529880)
- Jonathan Serrano (PID: 6524435)

## Concept
Exhibit A is a two-player online co-op heist game in the “friendslop” style of Lethal Company and R.E.P.O. Two thieves break into a museum after hours to steal its most valuable artifacts before the night runs out.

Getting in takes teamwork. Players solve puzzles that need both of them at once, like holding two pressure plates down together to open the vault. Security guards and the museum’s librarian patrol the halls with flashlights, and getting caught ends the heist. Every noise draws their attention, which cuts both ways: a careless player gives the team away, but a well-thrown object can lure a guard out of the way.

Once they have an artifact, players must carry it out and load it into the getaway van before time runs out. The full game will feature hand-designed rooms full of puzzles and secrets, arranged in a new order on every run, along with gadgets that open up new ways to sneak, distract, and escape.

## Objective
Steal **The Last Book of Alexandria** and get it into the Trojan Van before the museum opens.

1. Stand on the two empty statue plates **at the same time** (one player each) to swing open the portrait door to the vault.
82. Pick up the book and carry it out of the museum.
3. Step onto the painted drop zone next to the van while carrying it.

You have **3 minutes**. The librarian patrols the gallery with a flashlight: if she spots you, she gives chase, and if she catches either of you, the heist fails. Throw the Heel of Achilles to make a noise and lure her away.

- **Win:** the book is delivered to the drop zone.
- **Lose:** the guard catches a player, or the timer runs out.
- After either outcome, either player can press **Restart** to play again together.

## Controls
| Action | Key |
|---|---|
| Move | W A S D |
| Look | Mouse |
| Jump | Space |
| Sneak (move slower) | Ctrl |
| Interact: pick up the book or the heel, drop the book | E |
| Throw the heel | Left mouse button |
| Free / recapture the mouse | Esc / click |

## Implemented features
- **Online co-op for two players:** one player hosts, the other joins by IP. The host runs all game rules and both screens stay in sync.
- **One museum gallery, a vault, and an outdoor extraction area** with the getaway van.
- **Cooperative puzzle:** two pressure plinths that must be held at the same time open the vault door. Each plinth lights a picture lamp on the door while it is pressed.
- **Artifact:** pick up, carry, drop, and deliver the book. Only one player can hold it at a time, and you can't carry the book and the heel at once.
- **Guard AI:** patrols a waypoint loop, detects players with a flashlight vision cone blocked by walls, chases, investigates noises and last-seen positions, then returns to patrol. Catching a player ends the heist.
- **Throwable and noise:** the Heel of Achilles can be thrown. Its impact makes a noise that sends the guard within 8 m to investigate.
- **Heist rules:** 3-minute countdown, win/lose outcomes, and a synchronized restart that resets the players, guard, door, plinths, book, and heel.
- **HUD:** time remaining, artifact status (locked / vault open / carried by you or your partner / dropped / in the van), guard alert indicator, waiting-for-partner message, and the end screen.
- **Getaway cutscene** on a win: the van drives off through the exit barrier before the end screen appears.

## Technology stack & dependencies
- **Godot 4.7.2 stable**, Standard edition, scripted entirely in **GDScript**.
- **Networking:** Godot's high-level multiplayer API over ENet (UDP port 7777).
- **Assets:** Blender (all models made for this project, exported as glTF `.glb`).
- **Version control:** Git and GitHub.
- No addons, Asset Library plugins, or third-party packages.

## How to build / run
1. Install **Godot 4.7.2 stable (Standard)** from godotengine.org.
2. Extract the zip file and open `project.godot` from the Godot Project Manager (Import).
3. **Two players on one machine:** Debug → Customize Run Instances → Enable Multiple Instances, set to 2, then press F5. Click **Host** in one window and **Join** in the other (leave the address blank for `127.0.0.1`).
4. **Two machines on the same network:** each player runs the project. One clicks **Host**; the other types the host's local IP address and clicks **Join**. The host's firewall must allow UDP port 7777.
5. The heist starts automatically once both players are connected.

## Engine abstraction disclosure
| Engine features used | External packages/assets | Systems our team wrote |
|---|---|---|
| Rendering, lighting, particles, and animation playback | None. All models, textures, and sounds were made for this project (see Asset credits). | Heist rules: timer, win/lose outcome, restart (`game_state.gd`) |
| Physics: CharacterBody3D, RigidBody3D, Area3D, raycasts | | Cooperative plinth puzzle and vault door (`vault_puzzle.gd`, `pressure_plate.gd`, `vault_door.gd`) |
| Navigation mesh and NavigationAgent3D pathfinding | | Guard decisions: patrol, vision cone, suspicion, chase, investigate, catch (`guard.gd`) |
| High-level multiplayer: ENet, RPCs, MultiplayerSpawner/Synchronizer | | Artifact ownership, carrying, dropping, delivery (`artifact.gd`, `drop_zone.gd`) |
| glTF import, skeletons, AnimationPlayer | | Noise and distraction rules (`noise_system.gd`, `throwable.gd`) |
| UI controls (Label, Button, containers) | | Host authority and networking flow (`network_manager.gd`, `main.gd`, `player.gd`), HUD (`hud.gd`) |

### Godot-provided systems
   - High-level multiplayer (ENetMultiplayerPeer, RPCs)
   - MultiplayerSpawner / MultiplayerSynchronizer (player spawning and position/rotation sync)
   - CharacterBody3D physics and CSG geometry
   - NavigationRegion3D and NavigationAgent3D (navigation mesh baking and the guard's pathfinding)
   - RayCast3D (detecting what the player is looking at)
   - Physics ray queries (guard line of sight, stopping her flashlight beam at walls, placing a dropped book)
   - Area3D (detecting players on the pressure plates)
   - glTF scene import, Skeleton3D skinning and AnimationPlayer (player and guard models)
   - BoneAttachment3D, SpotLight3D and Tween (guard flashlight and lens glare)
   - GPUParticles3D and OmniLight3D (smoke, sparks and ember glow on the artifact)
   - GPUParticles3D and a second Camera3D (the van's exhaust and the getaway shot)
   - RigidBody3D, continuous collision and contact monitoring (throwable physics and impacts)
   - AudioStreamPlayer3D (the heel's landing sound)

### Systems we wrote
- Heist timer, outcome and synchronized restart (scripts/game_state.gd)
- Host/join flow, player spawning and restart respawns (scripts/network_manager.gd, scripts/main.gd)
- Pressure plate puzzle condition and vault door (scripts/vault_puzzle.gd, scripts/pressure_plate.gd, scripts/vault_door.gd)
- Guard AI: patrol, vision cone, suspicion, chase, investigation, catch (scripts/guard.gd)
- Noise system and throw impact rule (scripts/noise_system.gd, scripts/throwable.gd)
- Artifact pickup, carrying and dropping (scripts/artifact.gd)
- Delivery and win condition (scripts/drop_zone.gd)
- Player movement, interaction and throw requests (scripts/player.gd)
- HUD and end screen (scripts/hud.gd)

## Known limitations
- Only one gallery room, one vault, and one guard. Additional rooms and procedural room ordering are planned for HW #4.
- Sneaking only slows the player down. It doesn't yet affect how quickly the guard notices you or make footsteps quieter.
- Exactly two players. There is no lobby or matchmaking: the client must type the host's IP address, and playing across different networks needs port 7777 forwarded on the host's router.
- If the host quits, the client is sent back to the main menu; the session can't continue without the host.
- There is one throwable, and the heel is the only gadget so far.

## Asset credits
- Player and guard characters (`assets/characters/`): made for this project in Blender. Editable sources are in `assets/characters/source/`.
- The Heel of Achilles, its tag and its landing sound (`assets/throwable/`): made for this project, the heel in Blender and the sound generated by script. Editable source is in `assets/throwable/source/`.
- The statue plinths, their labels and the marble (`assets/plates/`): made for this project in Blender. Editable source is in `assets/plates/source/`.
- The portrait door and its label (`assets/door/`): made for this project in Blender. Editable source is in `assets/door/source/`.
- The Last Book of Alexandria and its display stand (`assets/artifact/`): made for this project in Blender. Editable source is in `assets/artifact/source/`.
- Trojan Van, drop zone and road (`assets/getaway/`): made for this project in Blender. Editable source is in `assets/getaway/source/`.

## Contributions
Eduardo Goncalvez (PID: 6526311)
- Project setup: Created the Godot project and organized its folder layout (`project.godot`, `.gitignore`, `.gitattributes`, `.editorconfig`).
- Networking: Implemented the networking features that handle hosting and joining over ENet (`network_manager.gd`, `main.gd`, `main.tscn`).
- Greybox level: Designed the layout of the museum level (`museum.tscn`).
- Game state: Worked on `game_state.gd`, which holds the timer, outcome, and synced restart, and connected it to `hud.gd` and `hud.tscn` to show it on screen.
- Guard AI: Implemented the guard AI, which covers patrol, vision cone, chase, and catching a player (`guard.gd`, `guard.tscn`).

Alex Waisman (PID: 6529880)
- Assets: Made all the 3D models and their textures in Blender, with help from Claude through an MCP connection: the player and guard (`assets/characters/`), the book artifact (`assets/artifact/`), the portrait door (`assets/door/`), the statue plinths (`assets/plates/`), the Heel of Achilles throwable (`assets/throwable/`), and the Trojan Van and drop zone (`assets/getaway/`).
- Character animation: Animated the player and guard models (`player_model.gd`, `guard_model.gd`, `player_model.tscn`, `guard_model.tscn`).
- Artifact: Wrote the logic for the artifact, which handles picking it up and carrying it (`artifact.gd`, `artifact_model.gd`, `artifact.tscn`, `artifact_model.tscn`).
- Win condition: Added the drop zone where players deliver the artifact, and the win scene (`drop_zone.gd`, `drop_zone.tscn`, `trojan_van.gd`, `trojan_van.tscn`, `getaway.tscn`).
- Throwable sound: Added the throwable's landing sound (`assets/throwable/thud.wav`).


Jonathan Serrano (6524435)
- Interaction: Implemented the interact raycast on the player, an on-screen prompt, and interactions the host checks before applying (`player.gd`, `player.tscn`).
- Co-op puzzle: Made the logic for the co-op puzzle where two pressure plates that must be held down at the same time to open the vault door. (`pressure_plate.gd`, `pressure_plate.tscn`, `vault_puzzle.gd`, `vault_door.gd`).
- Noise: Added a reusable system that alerts guards when a noise is made, and worked on how the guards react to noise (`noise_system.gd`, `guard.gd`).
- Throwing: Worked on the throwing logic that handles picking up, throwing, the impact noise, and resetting the object (`throwable.gd`, `throwable.tscn`).


## GenAI statement

Tools used: CXlaude Code and Blender MCP Connection.

Representative prompts:
- "Review my noise and guard logic and identify edge cases I should test."

- "Why does a held RigidBody3D stutter and lag behind the player only on the client? The host positions it and a MultiplayerSynchronizer syncs it."

- "Generate using the Blender  connection, model a guard character: an old librarian
  with a grey bun, glasses on a chain, a cardigan, a long skirt, and sensible shoes, but very
  muscular. She needs two poses: stooped and shuffling on patrol, holding a flashlight and a
  heavy book, and standing tall  in a chase, with the book tucked under her arm
  and her glasses flashing white." (through a Blender MCP connection)

How it supported our workflow:
- Assets: The Player, guard, artifact, throwable and vehicle models were generated with AI through Blender, then adjusted by hand (scale, materials, collision shapes).
- Code: Claude gave us suggestions for each part of the project, pointed out possible errors before we tested, and explained unexpected results. All game rules were designed and written by us.
- Not used for: game design decisions.

How we verified the output:
- Every AI suggestion was read line by line before we kept it, and we rewrote parts we couldn't explain.
- Each change went through a pull request that another teammate reviewed before merging.
- We playtested each feature by hand after merging.
- Each member can walk through the systems they own.
