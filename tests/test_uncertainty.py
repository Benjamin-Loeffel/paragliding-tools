"""Monte-Carlo-Unsicherheitsband."""

import numpy as np
from rasterio.transform import from_origin

from terrainclearance.config import Config
from terrainclearance.terrain import compute_clearances
from terrainclearance.tiles import Sampler
from terrainclearance.uncertainty import compute_uncertainty


def _sampler(arr):
    return Sampler(arr.astype(np.float32), from_origin(1000.0, 2000.0, 0.5, 0.5), -9999.0)


def test_band_ordering_low_point():
    rng = np.random.default_rng(0)
    s = _sampler(1000 + rng.normal(0, 6, (300, 300)))
    cfg = Config()
    cfg.mc_samples = 40
    e = np.array([1000 + 120 * 0.5])
    n = np.array([2000 - 120 * 0.5])
    z = np.array([float(s.sample_bilinear(e, n)[0]) + 25.0])  # 25 m -> volles MC
    clr = compute_clearances(e, n, z, s, s, cfg)
    unc = compute_uncertainty(e, n, z, s, s, clr, cfg)
    assert unc.min_terrain[0] <= unc.p05_terrain[0] <= unc.mean_terrain[0] <= unc.p95_terrain[0] <= unc.max_terrain[0]
    assert unc.std_terrain[0] > 0.0


def test_analytic_band_high_point():
    s = _sampler(np.full((200, 200), 500.0))
    cfg = Config()
    e = np.array([1000 + 100 * 0.5])
    n = np.array([2000 - 100 * 0.5])
    z = np.array([700.0])  # 200 m AGL > mc_full_below_m -> analytisch
    clr = compute_clearances(e, n, z, s, None, cfg)
    unc = compute_uncertainty(e, n, z, s, None, clr, cfg)
    assert abs(unc.mean_terrain[0] - clr.d3_terrain[0]) < 1e-6
    assert abs(unc.std_terrain[0] - cfg.gps_sigma_v_m) < 1e-6
