"""Background Blender job (asset plan P1.4): a brass rope-barrier post, the red velvet rope that hangs
between two posts, and a padded gallery bench. Run barrier_bench_art.py first.
usage: blender -b --factory-startup --python barrier_bench_build.py -- <out dir>"""
import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import int_dims as D
import int_mesh as M
importlib.reload(D)
importlib.reload(M)

OUT = pathlib.Path(sys.argv[sys.argv.index("--") + 1])
M.reset()
atlas = M.Atlas(HERE / "barrier_bench_atlas.json", OUT / "int_barrier_bench.png")
BRASS = M.material("brass", atlas.image, metallic=1.0, roughness=0.28)
VELVET = M.material("velvet", atlas.image, roughness=0.95)
LEATHER = M.material("leather", atlas.image, roughness=0.42)
WOOD = M.material("wood", atlas.image, roughness=0.55)


def stanchion():
    """Weighted base, slim shaft, a collar the rope clips to, and a ball on top. Origin on the floor."""
    b = M.Builder()
    brass = atlas.uv("brass")
    r = D.POST_BASE_R
    b.cylinder(r, r, 0.022, 0, brass, M.at(z=0.011), segments=32)
    b.cylinder(r * 0.94, 0.045, 0.05, 0, brass, M.at(z=0.047), segments=32)
    top = D.ROPE_HOOK_Y - 0.025
    b.cylinder(D.POST_SHAFT_R, D.POST_SHAFT_R, top - 0.072, 0, brass, M.at(z=(top + 0.072) / 2))
    b.cylinder(0.036, 0.036, 0.05, 0, brass, M.at(z=D.ROPE_HOOK_Y))
    b.cylinder(0.03, 0.018, 0.03, 0, brass, M.at(z=D.ROPE_HOOK_Y + 0.04))
    ball = 0.042
    b.sphere(ball, 0, brass, M.at(z=D.ROPE_POST_H - ball))
    return b.object("Stanchion", [BRASS])


def rope():
    """Hangs from a post at x = 0 to one at x = ROPE_SPAN, sagging in the middle, with a brass cap
    at each end. rope_barrier.gd stretches it along x for other spans."""
    b = M.Builder()
    h, span, sag = D.ROPE_HOOK_Y, D.ROPE_SPAN, D.ROPE_SAG
    start, end = 0.09, span - 0.09
    pts = []
    for i in range(29):
        t = i / 28
        pts.append((start + (end - start) * t, 0.0, h - 0.02 - sag * (1 - (2 * t - 1) ** 2)))
    b.tube(pts, D.ROPE_R, 0, atlas.uv("velvet"), segments=12)
    for x, rot in ((0.062, -90), (span - 0.062, 90)):
        b.cylinder(0.026, 0.022, 0.06, 1, atlas.uv("brass"), M.at(x=x, z=h - 0.01, ry=rot))
        b.cylinder(0.012, 0.012, 0.05, 1, atlas.uv("brass"), M.at(x=x - 0.04 if rot < 0 else x + 0.04, z=h, ry=rot))
    return b.object("Rope", [VELVET, BRASS])


def bench():
    """A padded gallery bench, long side along x. Origin on the floor, in the middle."""
    b = M.Builder()
    wood, leather = atlas.uv("wood"), atlas.uv("leather")
    length, depth, seat = D.BENCH_L, D.BENCH_D, D.BENCH_H
    board_top = seat - 0.055
    for x in (-length / 2 + 0.16, length / 2 - 0.16):
        b.box(0.07, depth - 0.08, board_top - 0.03, 0, wood, M.at(x=x, z=(board_top - 0.03) / 2))
    b.box(length - 0.4, 0.06, 0.06, 0, wood, M.at(z=0.13))
    b.box(length, depth, 0.03, 0, wood, M.at(z=board_top - 0.015), bevel=0.006)
    b.box(length - 0.04, depth - 0.04, 0.056, 1, leather, M.at(z=board_top + 0.028), bevel=0.02)
    for i in range(5):
        for y in (-0.1, 0.1):
            b.sphere(0.012, 1, leather, M.at(x=(i - 2) * 0.33, y=y, z=seat - 0.001), squash=0.45, segments=10, rings=6)
    return b.object("Bench", [WOOD, LEATHER])


for make, name in ((stanchion, "stanchion"), (rope, "rope"), (bench, "bench")):
    M.export(make(), OUT / f"{name}.gltf")
