"""3D-Plot-Bau (Gitterfenster + Surface/Scatter3d-Figur)."""

from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from rasterio.transform import from_origin

from terrainclearance.config import Config
from terrainclearance.critical import find_events, point_levels
from terrainclearance.igc_loader import FlightTrack
from terrainclearance.report import _grid_window, build_terrain3d
from terrainclearance.terrain import compute_clearances
from terrainclearance.tiles import Sampler


def _sampler(elev=1000.0, size=400):
    rng = np.random.default_rng(0)
    arr = (elev + rng.normal(0, 5, (size, size))).astype(np.float32)
    return Sampler(arr, from_origin(1000.0, 2000.0, 0.5, 0.5), -9999.0)


def _track(e, n, z, t_s):
    dt = np.array([np.datetime64("2026-06-01T00:00:00") + np.timedelta64(int(s), "s") for s in t_s],
                  dtype="datetime64[s]")
    z = np.asarray(z, float)
    return FlightTrack("syn", Path("syn.igc"), dt, np.asarray(t_s, float),
                       np.full(z.size, 46.5), np.full(z.size, 7.6), z, z, z, "gnss",
                       np.ones(z.size, bool), {})


def test_grid_window_shape():
    s = _sampler()
    win = _grid_window(s, 1020.0, 1120.0, 1920.0, 1980.0, target_dim=50)
    assert win is not None
    sub, xs, ys = win
    assert sub.ndim == 2
    assert xs.size == sub.shape[1] and ys.size == sub.shape[0]
    assert max(sub.shape) <= 60  # Downsampling greift


def test_build_terrain3d_has_surface_and_track():
    s = _sampler()
    cfg = Config()
    e = 1000.0 + np.linspace(40, 120, 30) * 0.5
    n = 2000.0 - np.linspace(40, 120, 30) * 0.5
    z = s.sample_bilinear(e, n) + 40.0
    tr = _track(e, n, z, np.arange(30))
    clr = compute_clearances(e, n, z, s, s, cfg)
    _ = point_levels(clr, cfg)
    events = find_events(tr, clr, z, np.ones(30, bool), float(z.min()), cfg)
    fig = build_terrain3d(tr, e, n, z, clr, events, s, s, cfg)
    assert isinstance(fig, go.Figure)
    types = {t.type for t in fig.data}
    assert "surface" in types
    assert "scatter3d" in types
