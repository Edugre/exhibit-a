# How the interior is made

Plain Python, run by hand, writing into `assets/interior/`. Same pipeline as the exterior
(`assets/exterior/source/tools/README.md`); the asset list and its order are in `docs/hw4_assets_plan.md`.

- `int_dims.py`: every shared size inside the museum: wall height, doorway, the skirting and cornice
  bands, cover height, and the heights of plinths, benches, cases and crates. Build scripts import it,
  so never hard-code a size. Frozen once K0 merged: tell the team before changing it.
- `make_kit.py` (K0): draws the parquet, marble and plaster textures and the shared wear map (dirt,
  scratches and dull patches, on its own repeat so it never lines up with the surface under it), then
  writes their import settings and every kit material into `assets/interior/kit/`. Run `python make_kit.py assets/interior/kit`
  from the repo root. Rerunning keeps existing `.import` files, so the textures keep their uids.
- `crates_layout.py`, `crates_build.py`, `make_crates_art.py` (P1.1): the conservation crates and the
  draped statue. `crates_build.py` runs in a background Blender and builds the three crates, drops a
  simulated cloth over a statue shape, bakes the shading in its folds, and writes each prop's `.glb`,
  its import settings and its scene in `scenes/props/`. Then `make_crates_art.py` draws the one texture
  (plywood with stencils and shipping labels, pine battens, the cloth and its tag) and the two materials:
  `blender -b --factory-startup --python crates_build.py -- assets/interior/crates scenes/props`, then
  `python make_crates_art.py assets/interior/crates`. Both rebuild their outputs exactly.
- `cases_layout.py`, `cases_build.py`, `make_cases_art.py` (P1.2): the tall and low glass display cases.
  `blender -b --factory-startup --python cases_build.py -- assets/interior/cases scenes/props`, then
  `python make_cases_art.py assets/interior/cases`. The glass collision is its own StaticBody in the group
  `see_through`, so it stops players but the guard's sight check can be told to look through it.
- `shelves_layout.py`, `shelves_build.py`, `make_shelves_art.py` (P2.3): the archive bookcases, double-sided
  and against-the-wall, 1.2 m wide so a row makes a straight wall. Each shelf is filled with runs of books,
  each run a box showing its own stretch of one of three spine strips (picked by the books' height).
  `blender -b --factory-startup --python shelves_build.py -- assets/interior/shelves scenes/props`, then
  `python make_shelves_art.py assets/interior/shelves`.

- `int_mesh.py`, `int_art.py`: small shared helpers for script-built props. `int_mesh.py` (Blender) makes parts,
  fits them into an atlas and lays printed faces; `int_art.py` (Pillow) has noise, streaks and fitted fonts.
- `barrier_bench_art.py`, `barrier_bench_build.py` (P1.4): the brass rope-barrier post, the velvet rope and the
  gallery bench. From the repo root: `python assets/interior/source/tools/barrier_bench_art.py assets/interior/barrier_bench`,
  then `blender -b --factory-startup --python assets/interior/source/tools/barrier_bench_build.py -- assets/interior/barrier_bench`.
  Each prop is a `.gltf` with the set's one atlas kept beside it, so the three share a texture.
- `make_room_sounds.py` (P4): every room sound, from noise and maths (numpy only), into `assets/interior/sounds`.
  Each sound has its own seed. The loops are listed in `loops.txt` there; their `.import` files need
  `edit/loop_mode=2`. Rooms play them through `RoomTone` nodes (`scripts/room_tone.gd`), and the laser grid
  plays its own hum and zap.
- `gadget_art.py`, `gadget_build.py` (P2.4): the Hermes Signal Jammer, its texture, and its pulse and dud sounds, into
  `assets/gadget` (it's carried, not part of a room, so it lives outside `assets/interior`).
- `lobby_art.py`, `lobby_build.py` (P3.5): the lobby set (ticket desk, coat check, donation box, map board, two
  banners), the same way, into `assets/interior/lobby`. `int_mesh.material()` takes `alpha` (the donation box's glass)
  and `emission` (the desk lamp's shade).
- `signs_art.py`, `signs_build.py` (P1.6): the wet-floor A-frame and the "Do not touch" stand, the same way,
  into `assets/interior/signs`.

## Using the kit in a room

Every kit material is laid on in world space, so it works on plain CSG boxes with no UVs, at any size.

| Material | Use it on |
|---|---|
| `int_floor_parquet.tres` | Floors: oak blocks in a checkerboard |
| `int_floor_marble.tres` | Floors: cream marble slabs, 0.8 m, with grout |
| `int_wall_paint.tres`, `int_wall_paint_red.tres`, `int_wall_paint_green.tres` | Walls: cream, Pompeian red and library green. Walls darken a little towards the floor and ceiling |
| `int_ceiling.tres` | The underside of the roof |
| `int_skirting.tres` | A box `SKIRTING_H` tall and `SKIRTING_T` deep along the foot of each wall, broken at doorways |
| `int_moulding.tres` | A box `CORNICE_T` deep filling the band from `CORNICE_Y0` to `CORNICE_Y1` along the top of each wall. The carving is placed by world height, so the box must sit exactly in that band |

Open `scenes/props/kit_preview.tscn` (F6) to see all of them together at night lighting, with a
player, a statue plinth and a 1.4 m cover box for scale. `scenes/props/prop_template.tscn` is the
layout every prop scene copies; its root's editor description lists the rules.
