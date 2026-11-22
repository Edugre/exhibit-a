"""The rope barriers' and gallery bench's one texture (asset plan P1.4): brushed brass, twisted red
velvet, tufted leather and walnut, one quarter each.
usage: python barrier_bench_art.py <out dir>     (writes int_barrier_bench.png there)"""
import pathlib
import sys
import numpy as np
import int_art as A

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).parent
S = 512
Q = S // 2
rng = np.random.default_rng(1401)

RECTS = {
    "brass": (0, 0, Q, Q),
    "velvet": (Q, 0, S, Q),
    "leather": (0, Q, Q, S),
    "wood": (Q, Q, S, S),
}


def brass():
    base = np.array([0.80, 0.62, 0.30], np.float32)
    shade = 1 + 0.07 * A.streaks(rng, Q, Q, 48, axis=0) + 0.04 * A.blur_noise(rng, Q, Q, 12)
    return base * shade[..., None]


def velvet():
    y, x = np.mgrid[0:Q, 0:Q].astype(np.float32)
    twist = 0.5 + 0.5 * np.sin((x + y) * 2 * np.pi / 18)        # the rope's twisted strands
    base = np.array([0.42, 0.035, 0.05], np.float32)
    shade = 0.78 + 0.28 * twist + 0.06 * A.blur_noise(rng, Q, Q, 0.6)
    return base * shade[..., None]


def leather():
    base = np.array([0.16, 0.095, 0.075], np.float32)
    grain = A.blur_noise(rng, Q, Q, 1.2)
    shade = 1 + 0.07 * grain + 0.05 * A.blur_noise(rng, Q, Q, 20)
    return base * shade[..., None]


def wood():
    y, x = np.mgrid[0:Q, 0:Q].astype(np.float32)
    warp = 9 * A.blur_noise(rng, Q, Q, 30)
    rings = 0.5 + 0.5 * np.sin((y + warp) * 2 * np.pi / 22)
    base = np.array([0.30, 0.17, 0.09], np.float32)
    shade = 0.82 + 0.22 * rings + 0.05 * A.streaks(rng, Q, Q, 40, axis=1)
    return base * shade[..., None]


atlas = np.zeros((S, S, 3), np.float32)
for name, draw in (("brass", brass), ("velvet", velvet), ("leather", leather), ("wood", wood)):
    x0, y0, x1, y1 = RECTS[name]
    atlas[y0:y1, x0:x1] = draw()
A.to_image(atlas).save(OUT / "int_barrier_bench.png")
A.write_layout(HERE / "barrier_bench_atlas.json", [S, S], RECTS)
print("wrote", OUT / "int_barrier_bench.png")
