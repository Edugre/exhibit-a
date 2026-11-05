# How the exterior is made

Everything here is plain Python, run by hand, and it writes into `assets/exterior/` and `scenes/`.
Paths at the top of some scripts point at the machine they were last run on, so set them first.

- `ext_dims.py`: every size of the building, in one place. Shapes and collision both read it.
- `blockout_build.py`, `blockout_stage.py`, `gen_exterior_tscn.py`: the grey whole-block blockout and `scenes/exterior.tscn`.
- `cap_gen.py`, `cap_final.py`: the capital. Sculpts it in numpy, fuses it in Blender, makes the game mesh, bakes.
- `orn_final.py`: the carved cornice bracket and the owl keystone, the same way.
- `make_stone.py`, `make_trim.py`: the limestone and the carved moulding strip, from numpy.
- `section_build.py`, `context_build.py`, `gen_section.py`, `lights.json`: the style test bay and `scenes/exterior_section.tscn`.
