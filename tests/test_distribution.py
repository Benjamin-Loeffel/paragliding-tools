"""Zeit-in-Hangabstand-Verteilung (KDE) + Aggregat."""

import numpy as np
import plotly.graph_objects as go

from terrainclearance.config import Config
from terrainclearance.distribution import (build_aggregate_kde, build_flight_kde,
                                           build_risk_over_time, fix_durations,
                                           make_flight_dist, weighted_cdf, weighted_quantile)


def test_fix_durations():
    t = np.array([0.0, 1.0, 2.0, 5.0])
    w = fix_durations(t)
    assert w.size == 4
    assert w[0] == 1.0 and w[2] == 3.0


def test_make_flight_dist():
    clr = np.linspace(5, 200, 100)
    t = np.arange(100.0)
    air = np.ones(100, bool)
    air[:10] = False  # Boden
    d = make_flight_dist("f1", clr, t, air)
    assert d.clearance.size == 90
    assert d.duration_s > 0


def test_build_figs():
    cfg = Config()
    clr_t = np.linspace(5, 220, 200)
    clr_s = clr_t - 3
    t = np.arange(200.0)
    air = np.ones(200, bool)
    fig = build_flight_kde("f", clr_t, clr_s, t, air, cfg)
    assert isinstance(fig, go.Figure) and len(fig.data) >= 1
    d = make_flight_dist("f", clr_t, t, air)
    agg = build_aggregate_kde([d, d], cfg)
    assert isinstance(agg, go.Figure) and len(agg.data) >= 1


def test_weighted_quantile_and_cdf():
    v = np.array([10.0, 20.0, 30.0, 40.0])
    w = np.ones(4)
    assert abs(weighted_quantile(v, w, 0.5) - 25.0) < 2.0
    grid = np.array([0.0, 25.0, 100.0])
    cdf = weighted_cdf(v, w, grid)
    assert cdf[0] == 0.0
    assert 40.0 <= cdf[1] <= 60.0     # ~50% unter 25
    assert cdf[2] == 100.0


def test_risk_over_time():
    cfg = Config()
    t = np.arange(120.0)
    air = np.ones(120, bool)
    d1 = make_flight_dist("f1", np.linspace(40, 200, 120), t, air, np.datetime64("2026-06-01T09:00:00"))
    d2 = make_flight_dist("f2", np.linspace(10, 150, 120), t, air, np.datetime64("2026-06-20T09:00:00"))
    fig = build_risk_over_time([d2, d1], cfg)  # unsortiert -> Funktion sortiert
    assert isinstance(fig, go.Figure) and len(fig.data) >= 4
