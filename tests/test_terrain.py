"""Korrektheit des adaptiven 3D-Abstands gegen Brute-Force."""

import numpy as np
from rasterio.transform import from_origin

from terrainclearance.config import Config
from terrainclearance.terrain import _nearest, compute_clearances
from terrainclearance.tiles import Sampler


def make_sampler(arr, west=1000.0, north=2000.0, res=0.5, nodata=-9999.0):
    tr = from_origin(west, north, res, res)
    return Sampler(arr.astype(np.float32), tr, nodata)


def brute(sampler, e, n, z, R):
    sub, xs, ys = sampler.patch(e, n, R, stride=1)
    sub = sub.astype(np.float64)
    bad = sampler._nodata_mask(sub)
    dx = xs[None, :] - e
    dy = ys[:, None] - n
    dz = sub - z
    d2 = dx * dx + dy * dy + dz * dz
    d2[bad] = np.inf
    return float(np.sqrt(d2.min()))


def test_adaptive_equals_brute_random():
    rng = np.random.default_rng(42)
    arr = 1000 + rng.normal(0, 8, size=(300, 300))
    s = make_sampler(arr)
    cfg = Config()
    for _ in range(20):
        e = 1000 + rng.uniform(40, 110) * 0.5
        n = 2000 - rng.uniform(40, 110) * 0.5
        z = float(s.sample_bilinear(np.array([e]), np.array([n]))[0]) + rng.uniform(2, 60)
        R = min(abs(z - 1000) + cfg.margin_m, cfg.r_cap_m)
        d_adapt, _, _, _ = _nearest(s, e, n, z, R, cfg.max_patch_dim)
        d_brute = brute(s, e, n, z, R)
        assert abs(d_adapt - d_brute) < 1e-6


def test_flat_terrain_vertical():
    arr = np.full((100, 100), 500.0)
    dtm = make_sampler(arr)
    e = np.array([1000 + 25.0])
    n = np.array([2000 - 25.0])
    z = np.array([530.0])
    clr = compute_clearances(e, n, z, dtm, None, Config())
    assert abs(clr.v_terrain[0] - 30.0) < 1e-6
    # über flachem Gelände ist der nächste Punkt ~senkrecht darunter
    assert abs(clr.d3_terrain[0] - 30.0) < 0.5


def test_3d_beats_vertical_on_slope():
    # Steile Wand: Höhe steigt stark nach Osten -> nächster Punkt ist seitlich
    cols = np.arange(200)
    arr = np.tile(500 + cols * 2.0, (200, 1))  # +2 m pro 0.5-m-Zelle -> sehr steil
    dtm = make_sampler(arr.astype(float))
    e = np.array([1000 + 50 * 0.5])
    n = np.array([2000 - 100 * 0.5])
    ground = float(dtm.sample_bilinear(e, n)[0])
    z = np.array([ground + 40.0])
    clr = compute_clearances(e, n, z, dtm, None, Config())
    # 3D-Abstand muss <= vertikalem Abstand sein (seitliche Wand näher)
    assert clr.d3_terrain[0] <= clr.v_terrain[0] + 1e-6
    assert clr.d3_terrain[0] < 40.0
