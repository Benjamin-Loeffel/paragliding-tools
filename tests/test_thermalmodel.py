"""Synthetische Physik-Tests fürs Thermikmodell (ohne Netz).

Insbesondere ein Regressionstest für die Aspekt-Richtung (der 180°-Flip-Bug, ADR-0006).
"""

import numpy as np
import pandas as pd
import pytest

from thermalmodel import config as C
from thermalmodel.config import ThermalConfig
from thermalmodel.boundarylayer import w_star
from thermalmodel.heating import HeatResult, cumulative_energy_at
from thermalmodel.horizon import horizon_and_svf
from thermalmodel.solar import incidence_cos
from thermalmodel.terrain_derivs import _curvature, _slope_aspect


def _aspect_center(z):
    _, aspect = _slope_aspect(np.asarray(z, float), res=1.0)
    return np.degrees(aspect[2, 2])


def test_aspect_cardinal_directions():
    """Regressionstest ADR-0006: Aspekt = Richtung, in die der Hang zeigt (bergab), 0=N im Uhrzeigersinn."""
    col = np.tile(np.arange(5.0), (5, 1))     # steigt nach Osten
    row = np.tile(np.arange(5.0)[:, None], (1, 5))  # steigt nach Süden
    # z fällt nach Osten -> Hang zeigt nach OSTEN (90°)
    assert abs(_aspect_center(-col) - 90.0) < 5
    # z steigt nach Osten -> Hang zeigt nach WESTEN (270°)
    assert abs(_aspect_center(col) - 270.0) < 5
    # z fällt nach Süden (steigt nach Norden) -> Hang zeigt nach SÜDEN (180°)
    assert abs(_aspect_center(-row) - 180.0) < 5
    # z steigt nach Süden -> Hang zeigt nach NORDEN (0°/360°)
    a = _aspect_center(row) % 360
    assert min(a, 360 - a) < 5


def test_slope_known_angle():
    z = np.tile(np.arange(5.0), (5, 1))       # Gefälle 1 m pro 1 m = 45°
    slope, _ = _slope_aspect(z, res=1.0)
    assert abs(np.degrees(slope[2, 2]) - 45.0) < 1e-6


def test_curvature_sign_hill_valley():
    yy, xx = np.mgrid[-3:4, -3:4].astype(float)
    hill = -(xx ** 2 + yy ** 2)               # Kuppe (konvex)
    assert _curvature(hill, 1.0)[3, 3] > 0
    assert _curvature(-hill, 1.0)[3, 3] < 0   # Mulde (konkav)


def test_incidence_cos_flat_and_aligned():
    flat = np.zeros((1, 1)); zero = np.zeros((1, 1))
    assert abs(incidence_cos(0.0, 180.0, flat, zero)[0, 0] - 1.0) < 1e-9     # Sonne im Zenit
    assert incidence_cos(90.0, 180.0, flat, zero)[0, 0] < 1e-9              # Sonne am Horizont
    slope = np.radians(np.array([[30.0]])); asp = np.radians(np.array([[180.0]]))
    assert abs(incidence_cos(30.0, 180.0, slope, asp)[0, 0] - 1.0) < 1e-6    # senkrecht zur Fläche
    # Nordhang in Südsonne wird weggeschnitten
    aspn = np.radians(np.array([[0.0]]))
    assert incidence_cos(80.0, 180.0, np.radians(np.array([[60.0]])), aspn)[0, 0] == 0.0


def test_cumulative_energy_monotone():
    times = pd.date_range("2026-06-29 06:00", "2026-06-29 18:00", freq="30min", tz="Europe/Zurich")
    nt = len(times)
    q = np.ones((nt, 3, 3), dtype=float) * 100.0          # konstant 100 W/m²
    heat = HeatResult(times=times, Q_H=q, Q_H_daymax=q.max(0),
                      Q_H_energy=q.sum(0) * 0.5, label="test")
    cum = cumulative_energy_at(heat, [9, 12, 15, 18])
    vals = [f[0, 0] for _, f in cum]
    assert vals == sorted(vals)                            # monoton steigend
    assert vals[-1] <= heat.Q_H_energy[0, 0] + 1e-6        # ≤ Tagestotal
    # bis 09:00 = 7 Schritte (06:00..09:00) × 100 W/m² × 0.5 h = 350 Wh/m²
    assert abs(vals[0] - 350.0) < 1e-6


def test_w_star_magnitude_and_monotonic():
    w = w_star(200.0, 1500.0)
    assert 1.0 < w < 3.0                                   # Alpensommer-Grössenordnung
    assert w_star(400.0, 1500.0) > w                       # steigt mit Q_H
    assert w_star(200.0, 2500.0) > w                       # steigt mit z_i
    assert w_star(0.0, 1500.0) == 0.0 and w_star(200.0, 0.0) == 0.0


def test_svf_flat_is_one():
    z = np.full((20, 20), 1000.0)
    _, _, svf = horizon_and_svf(z, res=20.0, n_azimuth=8, max_steps=30, step_m=20.0)
    assert np.nanmin(svf) > 0.99                            # freier Himmel auf flachem Gelände


def test_landcover_tables_ranking():
    # Fels heizt am stärksten, Schnee/Wasser am wenigsten (ADR-0011)
    assert C.F_H[C.LC_ROCK] > C.F_H[C.LC_GRASS] > C.F_H[C.LC_CONIFER]
    assert C.F_H[C.LC_SNOW] <= 0.10 and C.F_H[C.LC_WATER] <= 0.10
    assert C.ALBEDO[C.LC_SNOW] > C.ALBEDO[C.LC_GRASS] > C.ALBEDO[C.LC_CONIFER]


# --- Wind / Plume / XC (2. Nachtblock) ---
import types
from thermalmodel.grids import Grid
from thermalmodel.plume import lenschow_w, wind_uv, grid_seeds, _slope_follow, release_curv_threshold
from thermalmodel.wind import GriddedWind
from thermalmodel.xcpotential import logistic


def test_wind_uv_direction():
    bl = types.SimpleNamespace(wind_height_m=np.array([0.0, 4000.0]),
                               wind_dir_deg=np.array([270.0, 270.0]),
                               wind_speed_ms=np.array([10.0, 10.0]))
    u, v = wind_uv(bl, 1000.0)          # Wind AUS Westen → weht nach Osten: u>0, v≈0
    assert u > 9.9 and abs(v) < 1e-6
    bl.wind_dir_deg[:] = 180.0          # aus Süden → weht nach Norden: v>0
    u, v = wind_uv(bl, 1000.0)
    assert v > 9.9 and abs(u) < 1e-6


def test_griddedwind_height_interp():
    g = Grid(res=20.0, west=0.0, north=200.0, nx=10, ny=10)
    U = np.stack([np.full((10, 10), 2.0), np.full((10, 10), 6.0)])   # 2 Niveaus
    V = np.zeros_like(U)
    gw = GriddedWind(Ulev=U, Vlev=V, level_h=np.array([1000.0, 2000.0]), grid=g)
    u, _ = gw.uv(100.0, 100.0, 1500.0)                                # Mitte → 4.0
    assert abs(u - 4.0) < 1e-6
    Uf, _ = gw.field_at_height(2000.0)
    assert np.allclose(Uf, 6.0)


def test_lenschow_profile():
    assert lenschow_w(0.0, 1000.0, 2.0) == 0.0          # am Boden 0
    assert lenschow_w(1000.0, 1000.0, 2.0) == 0.0       # an der Decke 0 (zh>0.95)
    mid = lenschow_w(400.0, 1000.0, 2.0)
    assert 0 < mid < 2.0                                # dazwischen positiv, < w*
    assert lenschow_w(400.0, 1000.0, 4.0) > mid         # skaliert mit w*


def test_xc_logistic_monotonic():
    assert 0 < logistic(1.0, 1.55, 5) < logistic(2.0, 1.55, 5) < 1
    assert abs(logistic(1.55, 1.55, 5) - 0.5) < 1e-9    # bei mu = 0.5


def _cone_terrain(nx=21, ny=21, res=20.0):
    yy, xx = np.mgrid[0:ny, 0:nx].astype(float)
    cx, cy = nx // 2, ny // 2
    dtm = 2000.0 - 8.0 * np.hypot(xx - cx, yy - cy)     # Kegel, Spitze in der Mitte
    slope, aspect = _slope_aspect(dtm, res)
    curv = _curvature(dtm, res)
    g = Grid(res=res, west=0.0, north=ny * res, nx=nx, ny=ny)
    terr = types.SimpleNamespace(dtm=dtm, slope=slope, aspect=aspect, curvature=curv)
    return g, terr


def test_slope_follow_climbs_toward_apex():
    g, terr = _cone_terrain()
    cfg = ThermalConfig()
    c_crit = release_curv_threshold(terr.curvature, np.isfinite(terr.dtm), cfg.d1_release_curv_pct)
    # Start auf der Flanke; hangaufwärts laufen → Endhöhe > Starthöhe (Richtung Spitze)
    e0 = 5 * g.res; n0 = g.north - 5 * g.res
    es, ns, zs = _slope_follow(e0, n0, terr, g, c_crit, cfg)
    assert zs[-1] >= zs[0]                               # ist hangaufwärts gelaufen
    assert len(es) >= 1


def test_grid_seeds_count_and_inside():
    g = Grid(res=20.0, west=0.0, north=400.0, nx=20, ny=20)
    mask = np.ones((20, 20), bool)
    terr = types.SimpleNamespace(dtm=np.full((20, 20), 1500.0))
    seeds = grid_seeds(g, mask, terr, spacing_m=100.0)   # 400m/100m ~ 4x4
    assert 9 <= len(seeds) <= 25
    assert all(g.west <= s.e <= g.west + g.nx * g.res for s in seeds)
