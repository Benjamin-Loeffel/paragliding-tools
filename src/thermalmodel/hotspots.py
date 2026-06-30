"""Hotspot-Erkennung: Score-Feld → lokale Maxima → Hotspot-Liste."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass

import numpy as np
from skimage.feature import peak_local_max

from .config import ThermalConfig
from .grids import Grid
from .reproject import lv95_to_wgs84


@dataclass
class Hotspot:
    id: int
    e: float
    n: float
    lat: float
    lon: float
    elev_m: float
    score: float
    q_h_peak: float       # W/m^2
    slope_deg: float
    aspect_deg: float
    class_id: int


def _norm01(a, mask):
    v = a[mask]
    v = v[np.isfinite(v)]
    if v.size == 0:
        return np.zeros_like(a)
    lo, hi = np.percentile(v, 2), np.percentile(v, 98)
    if hi <= lo:
        return np.zeros_like(a)
    return np.clip((a - lo) / (hi - lo), 0.0, 1.0)


def score_field(cfg: ThermalConfig, terrain, heat, mask) -> np.ndarray:
    slope_deg = np.degrees(terrain.slope)
    qn = _norm01(heat.Q_H_daymax, mask)
    convex = _norm01(np.clip(terrain.curvature, 0, None), mask)
    # Ausrichtung zur Nachmittagssonne (~SSW, 210°), nur auf nennenswerten Hängen
    aspect_align = np.clip(np.cos(terrain.aspect - np.radians(210.0)), 0, None) * np.clip(slope_deg / 10.0, 0, 1)
    slope_band = np.exp(-(((slope_deg - cfg.hotspot_slope_opt_deg) / cfg.hotspot_slope_width_deg) ** 2))
    score = (cfg.w_qh * qn + cfg.w_convex * convex
             + cfg.w_aspect * aspect_align + cfg.w_slope * slope_band)
    return np.where(mask, score, 0.0).astype(np.float32)


def detect(cfg: ThermalConfig, terrain, heat, lc, grid: Grid, mask) -> tuple[list[Hotspot], np.ndarray]:
    score = score_field(cfg, terrain, heat, mask)
    min_dist = max(1, int(round(cfg.hotspot_min_distance_m / grid.res)))
    coords = peak_local_max(score, min_distance=min_dist, num_peaks=cfg.hotspot_top_n,
                            threshold_rel=0.25, exclude_border=False)
    rows, cols = coords[:, 0], coords[:, 1]
    E = grid.west + (cols + 0.5) * grid.res
    N = grid.north - (rows + 0.5) * grid.res
    lon, lat = lv95_to_wgs84(E, N)
    hotspots = []
    for k in range(len(rows)):
        r, c = int(rows[k]), int(cols[k])
        hotspots.append(Hotspot(
            id=k, e=float(E[k]), n=float(N[k]), lat=float(lat[k]), lon=float(lon[k]),
            elev_m=float(terrain.dtm[r, c]), score=float(score[r, c]),
            q_h_peak=float(heat.Q_H_daymax[r, c]), slope_deg=float(np.degrees(terrain.slope[r, c])),
            aspect_deg=float(np.degrees(terrain.aspect[r, c])), class_id=int(lc.class_id[r, c])))
    hotspots.sort(key=lambda h: h.score, reverse=True)
    for i, h in enumerate(hotspots):
        h.id = i
    return hotspots, score


def write_hotspots(hotspots: list[Hotspot], csv_path, geojson_path=None) -> None:
    from pathlib import Path
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        cols = list(asdict(hotspots[0]).keys()) if hotspots else []
        w.writerow(cols)
        for h in hotspots:
            w.writerow([round(v, 6) if isinstance(v, float) else v for v in asdict(h).values()])
    if geojson_path:
        feats = [{"type": "Feature",
                  "geometry": {"type": "Point", "coordinates": [h.lon, h.lat]},
                  "properties": asdict(h)} for h in hotspots]
        with open(geojson_path, "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "features": feats}, fh, indent=1)
