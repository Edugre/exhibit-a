# How the exterior is made

Everything here is plain Python, run by hand, and it writes into `assets/exterior/` and `scenes/`.
Paths near the top of `gen_front.py` point at the machine it was last run on, so set them first.
Blender jobs run in the background: `blender -b --factory-startup --python <script> -- <args>`.

- `ext_dims.py`: every size of the museum, street and plaza, in one place. Shapes, lights and collision all read it. Sizes are 1:1 with the real site wherever the map could measure them; heights come from photos.
- `osm_measure.py`, `site_measure.py`, `site.json`, `footprint.json`: the real outline, trees and benches, taken from OpenStreetMap data (© OpenStreetMap contributors, ODbL).
- `cap_gen.py`, `cap_final.py`: the Corinthian capital. Sculpted in numpy, fused in Blender, reduced to a game mesh and baked.
- `orn_final.py`: the cornice bracket, the owl keystone, and the Athena and librarian masks on the skyline, the same way.
- `make_stone.py`, `make_trim.py`: the limestone and the carved moulding strip.
- `make_relief.py`, `door_art.py`: the portrait medallions, inscriptions and notices, and the eight bronze door panels, all drawn as height fields.
- `make_banners.py`, `make_stain.py`: the printed banners, and the soot, rain streaks and statue ghosts on the stone.
- `front_build.py`: the whole three-arch centre as game meshes, in Blender. Writes `front.glb`.
- `context_build.py`: everything around it: the plain body of the building, plaza, avenue, far blocks, park and skyline.
- `wings_build.py`: the wings, the returns of the end wings and the first stretch of each side, bay by bay, then the plain lines that tie the back together. Writes `wings.glb`.
- `tree_build.py`, `fountain_build.py`, `pigeon_build.py`: the three plaza trees, the fountain jets and the pigeon.
- `make_props_art.py`, `props_build.py`: the one texture all street props share, then the props and cars.
- `make_sounds.py`: every sound in the street, generated from noise and maths.
- `make_instance_meshes.gd.txt`: saves the meshes drawn in instanced batches as plain mesh resources in `assets/exterior/meshes/`. Rename to .gd and run with `godot --headless --script`.
- `bake_guard_map.gd.txt`: bakes the guard's walkable map from the real game's collision. Add it as a temporary autoload, run the game headless, then paste `guard_map.txt` into the NavigationMesh in `scenes/museum.tscn`. Rebake whenever walkable ground changes.
- `bake_front_light.gd.txt`: renders the floodlights on the centre front into `ext_baked_light.png`, the light map the Low graphics level uses. Add it as a temporary autoload and run `scenes/exterior_night.tscn` with `--resolution 2048x1152 -- --out=<path>`. Rebake whenever the floods or the front change.
- `gen_front.py`, `gen_street.py`: take all of that and write the textures' import files, the materials, and `scenes/exterior.tscn` with its lights, traffic, life, sound and collision.

`scenes/exterior.tscn` is the block on its own; `scenes/exterior_night.tscn` wraps it in the night sky and moon. Tune the lights in the list near the middle of `gen_front.py`, not in the scene, or the next run overwrites them.
