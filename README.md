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

Once they have an artifact, players must carry it out and load it into the getaway van before time runs out. The museum is built from hand-designed rooms, each with its own puzzle or guards, and the host arranges them in a new order on every run. A Signal Jammer gadget opens up another way past the museum's security.

## Objective
Steal **The Last Book of Alexandria** and get it into the Trojan Van before the museum opens.

1. Walk in through the front doors and the lobby, then through **three of the four rooms below, picked and shuffled for this run**.
2. In the gallery at the back, stand on the two empty statue plates **at the same time** (one player each) to swing open the portrait door to the vault.
3. Pick up the book and carry it all the way back out of the museum. Puzzle doors and laser grids stay open for the way back.
4. Step onto the painted drop zone next to the van while carrying it.

The rooms between the lobby and the gallery come from this pool:

| Room | What stands in your way |
|---|---|
| Sculpture Hall | A guard on a long patrol. Crates and draped statues give cover, and there's a Heel to throw. |
| Twin Archives | The exit only opens if both players press their plates **within 2 seconds of each other**, from alcoves where they can't see each other. A lamp over the exit shows each press. |
| Laser Corridor | A laser grid that sets off the alarm. Hold the switch on one side while your partner crosses, then swap, or spend a jammer charge to cross together. There's also a guard. |
| Security Office | Two guards whose patrols cross, with a Heel and a coin to split them up. |

You have **3 minutes, plus 30 seconds for every room between the lobby and the gallery** (4½ minutes). Librarians patrol with flashlights: if one spots you, she gives chase, and if she catches either of you, the heist fails. Throw the Heel of Achilles or a coin to make a noise and lure her away; you'll find them on the plaza and in the rooms that have guards.

- **Win:** the book is delivered to the drop zone.
- **Lose:** the guard catches a player, or the timer runs out.
- After either outcome, either player can press **Restart** to play again together. A restart builds a new run with a new room order.

## Controls
| Action | Key |
|---|---|
| Move | W A S D |
| Look | Mouse |
| Jump | Space |
| Sneak (move slower) | Ctrl |
| Interact: pick up the book, the heel, a coin or the jammer; drop the book | E |
| Throw the heel or a coin | Left mouse button |
| Use the Signal Jammer (while you carry it) | Q |
| Put the jammer down for your partner (with nothing else in hand) | Left mouse button |
| Free / recapture the mouse | Esc / click |

## Implemented features
- **Online co-op for two players:** one player hosts, the other joins by IP. The host runs all game rules and both screens stay in sync.
- **A museum of rooms behind a full museum exterior.** The heist starts on the plaza at night in front of a Fifth Avenue-style museum front, built at true scale from OpenStreetMap data, with the getaway van parked at the curb. The block is walkable all the way round, with traffic, pigeons, fountains and sound. Inside, a lobby leads through the run's rooms to the gallery and vault at the back.
- **Procedural room ordering (HW #4):** every run, the host shuffles the four pool rooms with a seeded shuffle and keeps three that fit the building, in that order. The client gets the host's rooms, including after a restart or when joining late.
- **Four pool rooms (HW #4):** Sculpture Hall, Twin Archives, Laser Corridor and Security Office (see the table above). Each has its own props and lighting, and most have a brass plaque over the doorway naming the room.
- **Cooperative puzzles:** two pressure plinths that must be held at the same time open the vault door, and each plinth lights a picture lamp on the door while it is pressed. Twin Archives asks for two presses within 2 seconds from rooms apart. The Laser Corridor asks the players to hand the switches off between them.
- **Room sounds (HW #4):** every room hums at its own pitch; clocks tick in the lobby and the archives, floorboards creak and pages rustle in Twin Archives, the security office buzzes under its tubes with radio chatter from the desk, and the laser grid hums while it's on and zaps when someone walks into it.
- **Signal Jammer gadget (HW #4):** one jammer per heist, waiting on the lobby's ticket desk with its LED blinking. Either player picks it up (E); it clips to their belt, and with nothing else in hand the throw button puts it down for the other. It has two charges for the whole heist, which go wherever it goes (Q). A charge switches off every jammable thing within 6 m for 6 seconds, which right now means laser grids. The HUD shows the charges left. Everyone can see it working: the jammer rides on each player's belt and comes up into your view when you use it, a ring of light sweeps out to its range with a burst of radio static on both screens, and a jammed grid throws sparks while its beams sputter. A use that jams nothing just clicks.
- **Artifact:** pick up, carry, drop, and deliver the book. Only one player can hold it at a time, and you can't carry the book and the heel at once.
- **Guard AI:** patrols a waypoint loop, detects players with a flashlight vision cone blocked by walls, chases (through doorways into other rooms), investigates noises and last-seen positions, then returns to patrol. Catching a player ends the heist. A run has up to four guards across its rooms.
- **Throwable and noise:** the Heel of Achilles can be thrown. Its impact makes a noise that sends any guard within 8 m to investigate. Heels and coins wait on the plaza and in every guarded room.
- **Heist rules:** a countdown of 3 minutes plus 30 seconds per pool room, win/lose outcomes, and a synchronized restart that builds a new run and resets the players, book, throwables and jammer charges.
- **HUD:** time remaining, artifact status (locked / vault open / carried by you or your partner / dropped / in the van), guard alert indicator, waiting-for-partner message, and the end screen.
- **Getaway cutscene** on a win: the van gallops off down the avenue before the end screen appears.
- **More ways to sneak and distract:** fountain coins are a second, quieter throwable. Standing still on an empty plinth outside passes you off as a statue, unless the guard was already watching you. A flock of pigeons scared into the air brings her over.
- **She Will Know alarm:** once the book leaves its stand, the floodlights go red, a bell and siren start, and the stone librarian on the roof turns to watch.
- **Weather:** the host rolls clear, rain or snow for every heist (or picks one in the menu), and both players see the same night.
- **Library card end screen:** the result is typed onto the book's library card and stamped.
- **Opening shot:** the menu opens on a camera move from the moon down to the curb.
- **Graphics levels:** Low, Medium and High, picked per computer and lowered automatically on a weak laptop. The menu can override it.

## Technology stack & dependencies
- **Godot 4.7.2 stable**, Standard edition, scripted entirely in **GDScript**.
- **Networking:** Godot's high-level multiplayer API over ENet (UDP port 7777).
- **Assets:** Blender (all models made for this project, exported as glTF `.glb` and `.gltf`). Most HW #4 and exterior assets are built by our own Python scripts that run Blender in the background, with textures and sounds drawn by Python (numpy, scipy, Pillow). These are asset tools only, not part of the game.
- **Version control:** Git and GitHub.
- No addons, Asset Library plugins, or third-party packages.

## How to build / run
1. Install **Godot 4.7.2 stable (Standard)** from godotengine.org.
2. Extract the zip file and open `project.godot` from the Godot Project Manager (Import).
3. **Two players on one machine:** Debug → Customize Run Instances → Enable Multiple Instances, set to 2, then press F5. Click **Host** in one window and **Join** in the other (leave the address blank for `127.0.0.1`).
4. **Two machines on the same network:** each player runs the project. One clicks **Host**; the other types the host's local IP address and clicks **Join**. The host's firewall must allow UDP port 7777.
5. The heist starts automatically once both players are connected.

### Trying a specific run
The host's Output panel prints each run as `Museum run N (seed S): room, room, …`. On `World/Museum` in `scenes/main.tscn`, set **Debug Seed** to replay a run, or **Debug Order** to pick the rooms yourself (0 Sculpture Hall, 1 Twin Archives, 2 Laser Corridor, 3 Security Office).

### Graphics levels
The game picks Low, Medium or High for each computer and steps down by itself if it runs slowly. The Graphics option in the menu overrides that. Low is built for weak laptops: it draws at a lower resolution and scales up, and the floodlights and their shadows come from a baked texture instead of real lights.

## Engine abstraction disclosure
| Engine features used | External packages/assets | Systems our team wrote |
|---|---|---|
| Rendering, lighting, particles, and animation playback | None. All models, textures, and sounds were made for this project (see Asset credits). | Heist rules: timer, win/lose outcome, restart (`game_state.gd`) |
| Physics: CharacterBody3D, RigidBody3D, Area3D, raycasts | | Cooperative plinth puzzle and vault door (`vault_puzzle.gd`, `pressure_plate.gd`, `vault_door.gd`) |
| Navigation mesh and NavigationAgent3D pathfinding | | Guard decisions: patrol, vision cone, suspicion, chase, investigate, catch (`guard.gd`) |
| High-level multiplayer: ENet, RPCs, MultiplayerSpawner/Synchronizer | | Artifact ownership, carrying, dropping, delivery (`artifact.gd`, `drop_zone.gd`) |
| glTF import, skeletons, AnimationPlayer | | Noise and distraction rules (`noise_system.gd`, `throwable.gd`) |
| UI controls (Label, Button, containers) | | Host authority and networking flow (`network_manager.gd`, `main.gd`, `player.gd`), HUD (`hud.gd`) |
| RandomNumberGenerator (a seeded random source) | | Procedural room ordering: our own Fisher–Yates and the fit-the-building rule (`room_order.gd`), and building the museum from rooms (`museum_layout.gd`, `room.gd`) |
| CSG geometry, runtime navmesh baking, NavigationLink3D | | Room puzzle rules: the two-press timing gate and exit gates that open for the way back (`twin_plate_gate.gd`, `room_gate.gd`) |
| Area3D overlap detection | | Gadget and laser rules: jammer charges and range, the laser alarm, and the switch hand-off (`gadget_jammer.gd`, `laser_grid.gd`, `laser_corridor.gd`) |

### Godot-provided systems
   - High-level multiplayer (ENetMultiplayerPeer, RPCs)
   - MultiplayerSpawner / MultiplayerSynchronizer (player spawning and position/rotation sync; the HW #4 rooms are spawned the same way, so a late joiner and a restart get the host's rooms)
   - CharacterBody3D physics and CSG geometry
   - NavigationRegion3D and NavigationAgent3D (navigation mesh baking and the guard's pathfinding)
   - RayCast3D (detecting what the player is looking at)
   - Physics ray queries (guard line of sight, stopping her flashlight beam at walls, placing a dropped book)
   - Area3D (detecting players on the pressure plates and in the laser grid's beams)
   - glTF scene import, Skeleton3D skinning and AnimationPlayer (player and guard models)
   - BoneAttachment3D, SpotLight3D and Tween (guard flashlight and lens glare)
   - GPUParticles3D and OmniLight3D (smoke, sparks and ember glow on the artifact)
   - GPUParticles3D and a second Camera3D (the van's exhaust and the getaway shot)
   - RigidBody3D, continuous collision and contact monitoring (throwable physics and impacts)
   - AudioStreamPlayer3D (the heel's landing sound)
   - StaticBody3D with box, cylinder, convex and concave collision shapes (the museum exterior, including the smooth ramp under the stairs and the block's full outline)
   - Spatial and sky shaders, ShaderMaterial (the exterior's world-space limestone, carved stone, cast bronze, windblown banners, pigeon wings, asphalt, plaza paving, leaves, flags, steam, headlamp pools, night glass, the distant city's windows, fountain water and jets, and night sky)
   - WorldEnvironment, tonemapping, SSAO, glow and fog (the exterior's night look)
   - DirectionalLight3D and shadowed SpotLight3D (moonlight and floodlights on the exterior)
   - SpotLight3D projector texture (the window's star lattice thrown across the terrace)
   - GPUParticles3D (moths round the exterior's lamps, steam from the street, sparks off a jammed laser grid)
   - Transparent unshaded materials and Tween (the jammer's pulse sweeping out to its range)
   - MultiMeshInstance3D (the pigeons, plaza trees and traffic, drawn in batches)
   - AudioStreamPlayer and AudioStreamPlayer3D (the city's soundscape, fountains, crickets, pigeons and car horns, and each room's background sound)
   - Looping WAV import (the room hums, clocks, fluorescent buzz and laser hum)
   - Global shader uniforms and a shader include (the alarm, rain and snow reaching every exterior material at once)
   - MultiMeshInstance3D with the fall worked out in the vertex shader (rain and snow, no simulation)
   - Screen-space reflections (puddles, on High only)
   - SystemFont, StyleBoxTexture and Tween (the library card and the alarm's words)
   - GradientTexture2D and a Camera3D move (the opening shot behind the menu)
   - Automatic mesh LOD from the glTF importer (carved stone at a distance)
   - Viewport 3D scaling with FSR, FXAA and MSAA (the graphics levels in scripts/exterior_quality.gd)
   - ConfigFile (remembering the graphics level picked in the menu)
   - Physics interpolation fraction (drawing the camera and models between physics steps, so movement is smooth on fast screens)
   - ReflectionProbe with custom ambient light (the rooms' dim indoor air at night)
   - NavigationServer3D baking from collision shapes (the guard's map of the steps and plaza out to the curb, and each room's map when it is built)
   - NavigationRegion3D baked at runtime per room, and NavigationLink3D through each doorway (HW #4 rooms: guards can follow you from room to room)
   - RandomNumberGenerator with a seed (the random source for the room shuffle, so a run can be replayed from its seed)
   - Spatial shaders (the interior's world-space parquet, marble, plaster and carved cornice, so they work on plain CSG boxes; the laser beams, drawn as added light with a flicker)

### Systems we wrote
- Heist timer, outcome and synchronized restart. The timer is 180 s plus 30 s for each pool room in the run, set by the host when the heist starts (scripts/game_state.gd)
- Host/join flow, player spawning and restart respawns (scripts/network_manager.gd, scripts/main.gd)
- Pressure plate puzzle condition and vault door (scripts/vault_puzzle.gd, scripts/pressure_plate.gd, scripts/vault_door.gd)
- Procedural room ordering: each run shuffles the finished pool rooms with our own seeded Fisher–Yates, then keeps rooms in that order while they still fit the 60 m behind the front doors, up to three. A restart draws a new seed; the host prints each run's seed and order (scripts/room_order.gd)
- Museum layout: the host builds the rooms in a line from the front doors (lobby, then the gallery and vault) when it starts hosting and again on every restart, and tells the artifact, drop zone and spawning where things are (scripts/museum_layout.gd)
- Room contract for HW #4: how rooms line up door to door, what each room provides, and the exit gate that stays open once the artifact is taken (scripts/room.gd, scripts/room_gate.gd, scripts/room_catalog.gd, scenes/rooms/room_template.tscn)
- Two-plate timing gate for Twin Archives: the gate opens when both plates are pressed within 2 seconds of each other (scripts/gates/twin_plate_gate.gd). A lamp over the exit for each plate shows each player when the other pressed, worked out by every peer from what it already receives (scripts/gates/twin_plate_lamps.gd)
- Guard AI: patrol, vision cone, suspicion, chase, investigation, catch (scripts/guard.gd)
- Noise system and throw impact rule (scripts/noise_system.gd, scripts/throwable.gd)
- Artifact pickup, carrying and dropping (scripts/artifact.gd)
- Delivery and win condition (scripts/drop_zone.gd)
- Player movement, interaction and throw requests (scripts/player.gd)
- HUD and end screen (scripts/hud.gd), and the library card it fills in (scripts/library_card.gd)
- Pigeons as an alarm: a scared flock calls the guard (scripts/pigeon_noise.gd). The host runs the flock and tells the client, so both players see the same birds (scripts/exterior_pigeons.gd)
- Passing for a statue on the plinths outside (scripts/player.gd, scripts/guard.gd)
- Fountain coins as a second, quieter throwable (scenes/coin.tscn, scripts/throwable.gd)
- Signal Jammer gadget: one jammer per heist, a thing in the museum that either player can pick up and put down for the other (scripts/jammer_pickup.gd). It has 2 charges for the whole heist; the host decides who holds it and spends its charges. The host checks the charges and the range (6 m), spends a charge only when something is jammed, and disables every jammable object in range for 6 seconds (scripts/gadget_jammer.gd, scripts/gadget_hud.gd). The host tells every peer when a charge is spent and what it jammed, and each peer plays the pulse and the jammed look from that (scripts/jam_pulse.gd, scripts/signal_jammer_model.gd, show_jammed in scripts/laser_grid.gd)
- Laser grid: walking through an active grid sets off an alarm, a loud noise (20 m) that sends guards to look, repeated every 1.5 s while someone stays in the beams. It is on while powered and not jammed; standing in it when it comes back on trips it at once (scripts/laser_grid.gd)
- Laser Corridor room rule: a switch on each side of the grid drops it while anyone stands on it, so the players hand off (one holds the near switch while the other crosses, then the far switch brings the first one over), or spend a jammer charge to cross together. Once the artifact is taken, the grid stays off for the way back. The switches are floor pads, so standing on one doesn't pass you off as a statue the way the plinths do (scripts/laser_corridor.gd, scenes/rooms/laser_corridor_room.tscn)
- Weather per heist, rolled by the host and sent to the client (scripts/exterior_weather.gd)
- The She Will Know alarm, played by each peer from the artifact state it already has (scripts/exterior_alarm.gd)
- Graphics levels and the automatic step down (scripts/exterior_quality.gd)
- Cosmetic exterior life: flickering lanterns, front doors that open for anyone near them, traffic that obeys the signal and honks at people in the road, and the opening shot (scripts/exterior_flicker.gd, scripts/exterior_doors.gd, scripts/exterior_traffic.gd, scripts/menu_camera.gd). Each peer runs its own, and none of it touches game state

## Known limitations
- Sneaking only slows the player down. It doesn't yet affect how quickly the guard notices you or make footsteps quieter.
- Exactly two players. There is no lobby or matchmaking: the client must type the host's IP address, and playing across different networks needs port 7777 forwarded on the host's router.
- If the host quits, the client is sent back to the main menu; the session can't continue without the host.
- There are two throwables, the heel and the fountain coins. Laser grids are the only thing the Signal Jammer can switch off so far. The Laser Corridor's displays are the shared crates and cases until its own props are made.
- The whole game takes place at night.

## Asset credits
- Player and guard characters (`assets/characters/`): made for this project in Blender. Editable sources are in `assets/characters/source/`.
- The Heel of Achilles, its tag and its landing sound (`assets/throwable/`): made for this project, the heel in Blender and the sound generated by script. Editable source is in `assets/throwable/source/`.
- The statue plinths, their labels and the marble (`assets/plates/`): made for this project in Blender. Editable source is in `assets/plates/source/`.
- The portrait door and its label (`assets/door/`): made for this project in Blender. Editable source is in `assets/door/source/`.
- The Last Book of Alexandria and its display stand (`assets/artifact/`): made for this project in Blender. Editable source is in `assets/artifact/source/`.
- Trojan Van, drop zone and road (`assets/getaway/`): made for this project in Blender. Editable source is in `assets/getaway/source/`.
- Museum exterior (`assets/exterior/`): made for this project in Blender. Editable source is in `assets/exterior/source/`.
- The museum's outline, street layout and the positions of trees, benches and the obelisk come from OpenStreetMap data, © OpenStreetMap contributors, available under the Open Database License (openstreetmap.org/copyright).
- Lettering on the exterior's banners, carvings and signs is set in Palatino Linotype and Arial, rendered into the textures.
- The exterior's sounds (`assets/exterior/*.wav`), including the alarm and the card's stamp: made for this project, generated by script from noise and sine waves.
- The library card and its stamps (`ui/library_card.png`, `ui/stamp_*.png`): made for this project, drawn by script (`assets/exterior/source/tools/make_card.py`).
- Interior surfaces (`assets/interior/kit/`): made for this project. The parquet, marble and plaster are drawn by script (`assets/interior/source/tools/make_kit.py`), and the carved cornice reuses the exterior's moulding maps.
- Conservation crates and the draped statue (`assets/interior/crates/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/crates_build.py`, using Blender's cloth simulation for the drop cloth), with the texture drawn by script (`make_crates_art.py`). The stencils and labels are set in Impact, Courier New, Arial Black and Ink Free, rendered into the texture.
- Glass display cases (`assets/interior/cases/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/cases_build.py`), with the texture drawn by script (`make_cases_art.py`). The curators' cards and the brass plate are set in Palatino Linotype, rendered into the texture.
- Archive bookcases (`assets/interior/shelves/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/shelves_build.py`), with the spines and the rest of the texture drawn by script (`make_shelves_art.py`). Spine titles and shelf marks are set in Palatino Linotype, rendered into the texture.
- Rope barriers, gallery bench, wet-floor sign and "Do not touch" stand (`assets/interior/barrier_bench/`, `assets/interior/signs/`): made for this project. Modelled in Blender by script (`barrier_bench_build.py`, `signs_build.py`), with the textures drawn by script (`barrier_bench_art.py`, `signs_art.py`); lettering set in Palatino Linotype and Arial, rendered into the texture.
- Doorway arches, exit jambs and room plaques (`assets/interior/doorways/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/doorway_build.py`), with the stone, the owl keystone and the engraved brass drawn by script (`make_doorway_art.py`). The room names are set in Palatino Linotype, rendered into the texture.
- Framed paintings, title labels and picture lights (`assets/interior/paintings/`): made for this project. The six paintings are laid out and then repainted stroke by stroke by script (`assets/interior/source/tools/make_paintings_art.py`), which also draws the gilt frames and labels; modelled in Blender by script (`paintings_build.py`). Titles are set in Palatino Linotype, rendered into the texture.
- Laser grid posts and switch pads (`assets/interior/laser/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/laser_build.py`), with the texture and the switch label drawn by script (`laser_art.py`); the beam shader is ours (`laser_beam.gdshader`). Lettering is set in Arial and Palatino Linotype, rendered into the texture.
- The rooms' sounds (`assets/interior/sounds/`): the hums, clocks, fluorescent buzz, radio chatter, creaks, page rustles and the laser's hum and zap. Made for this project, generated by script from noise and sine waves (`assets/interior/source/tools/make_room_sounds.py`).
- The Hermes Signal Jammer and its sounds (`assets/gadget/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/gadget_build.py`), with the texture drawn and the pulse and dud sounds generated by script from noise and sine waves (`gadget_art.py`). Lettering is set in Arial and Palatino Linotype, rendered into the texture.
- Lobby set: ticket desk, coat check with its rack and coats, donation box, museum map and two banners (`assets/interior/lobby/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/lobby_build.py`), with the texture, signs, map and banners drawn by script (`lobby_art.py`). Lettering is set in Palatino Linotype and Arial, rendered into the texture.
- Security office set: desk, monitor wall, lockers, chair with cardigan, key board (`assets/interior/office/`): made for this project. Modelled in Blender by script (`assets/interior/source/tools/office_build.py`), with the texture and the camera feeds on the screens drawn by script (`make_office_art.py`). Labels and screen text are set in Arial Bold, Consolas Bold and Ink Free, rendered into the texture.

## Contributions
Eduardo Goncalvez (PID: 6526311)
- Project setup: Created the Godot project and organized its folder layout (`project.godot`, `.gitignore`, `.gitattributes`, `.editorconfig`).
- Networking: Implemented the networking features that handle hosting and joining over ENet (`network_manager.gd`, `main.gd`, `main.tscn`).
- Greybox level: Designed the layout of the museum level (`museum.tscn`).
- Game state: Worked on `game_state.gd`, which holds the timer, outcome, and synced restart, and connected it to `hud.gd` and `hud.tscn` to show it on screen.
- Guard AI: Implemented the guard AI, which covers patrol, vision cone, chase, and catching a player (`guard.gd`, `guard.tscn`).
- HW #4 planning: Wrote the HW #4 rooms, team and asset plans that split the work into three tracks (`docs/`).
- HW #4 rooms and ordering: The room contract and template, splitting the museum into rooms, spawning them from the host and rebuilding them on restart, the room ordering rule, and the timer that scales with the run (`room.gd`, `room_gate.gd`, `room_catalog.gd`, `museum_layout.gd`, `room_order.gd`, `game_state.gd`, `entrance_room.tscn`, `vault_room.tscn`).
- HW #4 throwables and props: Placed the throwables in the rooms (B5), and made the rope barriers, bench and signs (`assets/interior/barrier_bench/`, `assets/interior/signs/`).

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

Tools used: Claude Code and Blender MCP Connection.

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
