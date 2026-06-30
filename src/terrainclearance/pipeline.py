"""End-to-End-Pipeline für einen einzelnen Flug."""

from __future__ import annotations

import logging
import math
from pathlib import Path

import numpy as np
import requests

from .calibrate import calibrate_altitude
from .config import Config
from .critical import find_events, point_levels
from .distribution import build_flight_kde, make_flight_dist
from .geo import CoordTransformer
from .igc_loader import load_igc
from .report import write_outputs
from .stac import find_tiles
from .terrain import compute_clearances
from .tiles import build_mosaic, download_tiles
from .uncertainty import compute_uncertainty

log = logging.getLogger(__name__)


def _expand_bbox(bbox, buffer_m: float):
    minlon, minlat, maxlon, maxlat = bbox
    mid_lat = math.radians((minlat + maxlat) / 2)
    dlat = buffer_m / 111_320.0
    dlon = buffer_m / (111_320.0 * max(math.cos(mid_lat), 0.1))
    return (minlon - dlon, minlat - dlat, maxlon + dlon, maxlat + dlat)


def analyze_flight(path: str | Path, cfg: Config, session: requests.Session,
                   transformer: CoordTransformer) -> dict:
    log.info("=== Flug: %s ===", Path(path).name)
    track = load_igc(path, cfg)
    log.info("%d Fixes, Höhenquelle=%s", track.n, track.alt_source)

    e, n = transformer.to_lv95(track.lon, track.lat)

    bbox = _expand_bbox(track.bbox_wgs84(), cfg.r_cap_m)
    dtm_tiles = find_tiles(cfg, bbox, "dtm", session)
    dsm_tiles = find_tiles(cfg, bbox, "dsm", session)

    dtm_paths = download_tiles(dtm_tiles, cfg.cache_dir / "dtm", session)
    dsm_paths = download_tiles(dsm_tiles, cfg.cache_dir / "dsm", session) if dsm_tiles else []

    dtm = build_mosaic(dtm_paths, cfg.max_mosaic_cells)
    dsm = build_mosaic(dsm_paths, cfg.max_mosaic_cells) if dsm_paths else None

    cal = calibrate_altitude(track, e, n, dtm, cfg)
    alt_cal = cal.apply(track.alt)
    log.info("Kalibrierung: Offset %+.1f m (%s, %s) – %s",
             cal.offset_m, cal.method, cal.confidence, cal.note)

    clr = compute_clearances(e, n, alt_cal, dtm, dsm, cfg)
    levels = point_levels(clr, cfg)

    # Start-/Landephase (Bodenkontakt) aus der Event-Erkennung ausschliessen
    buf = cfg.event_edge_buffer_s
    airborne = (track.t_s >= cal.takeoff_t_s + buf) & (track.t_s <= cal.landing_t_s - buf)
    landing_idx = min(int(np.searchsorted(track.t_s, cal.landing_t_s)), track.n - 1)
    landing_alt = float(alt_cal[landing_idx])
    events = find_events(track, clr, alt_cal, airborne, landing_alt, cfg)

    # "Cruise" = echter Flug ohne finalen Landeabstieg (für aussagekräftige Min-Statistik)
    above = np.where(alt_cal > landing_alt + cfg.landing_approach_height_m)[0]
    last_high = int(above[-1]) if above.size else track.n - 1
    cruise = airborne & (np.arange(track.n) <= last_high)

    unc = None
    if cfg.uncertainty:
        log.info("Monte-Carlo-Unsicherheit (σ_h=%.1f m, σ_v=%.1f m, N=%d) …",
                 cfg.gps_sigma_h_m, cfg.gps_sigma_v_m, cfg.mc_samples)
        unc = compute_uncertainty(e, n, alt_cal, dtm, dsm, clr, cfg)

    def _min(arr, mask):
        v = arr[mask & np.isfinite(arr)]
        return round(float(v.min()), 1) if v.size else None

    meta = {
        "resolution_m": cfg.resolution,
        "n_inflight": int(cruise.sum()),
        "min_d3_terrain_inflight_m": _min(clr.d3_terrain, cruise),
        "min_d3_surface_inflight_m": _min(clr.d3_surface, cruise),
        "dtm_tiles": {t.tile_id: t.year for t in dtm_tiles.values()},
        "dsm_tiles": {t.tile_id: t.year for t in dsm_tiles.values()},
        "transform_pipeline": transformer.description,
        "r_cap_m": cfg.r_cap_m,
    }
    paths = write_outputs(track, alt_cal, clr, cal, events, levels, e, n, dtm, dsm, unc, meta, cfg)

    # Zeit-in-Hangabstand: KDE pro Flug + Daten für den Mehrflug-Zusammenzug
    kde_fig = build_flight_kde(track.name, clr.d3_terrain, clr.d3_surface, track.t_s, airborne, cfg)
    kde_path = cfg.output_dir / f"{track.name}_clearance_kde.html"
    kde_fig.write_html(str(kde_path), include_plotlyjs=True)
    paths["clearance_kde"] = kde_path
    dist_terrain = make_flight_dist(track.name, clr.d3_terrain, track.t_s, airborne, track.dt[0])

    finite_t = clr.d3_terrain[cruise & np.isfinite(clr.d3_terrain)]
    finite_s = clr.d3_surface[cruise & np.isfinite(clr.d3_surface)]
    return {
        "flight": track.name,
        "n_fixes": track.n,
        "alt_source": track.alt_source,
        "offset_m": round(cal.offset_m, 1),
        "calib_confidence": cal.confidence,
        "n_events": len(events),
        "min_d3_terrain_m": round(float(finite_t.min()), 1) if finite_t.size else None,
        "min_d3_surface_m": round(float(finite_s.min()), 1) if finite_s.size else None,
        "paths": {k: str(v) for k, v in paths.items()},
        "events": events,
        "dist_terrain": dist_terrain,
    }
