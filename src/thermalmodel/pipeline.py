"""Phase-A-Orchestrierung: KML → Terrain → Horizont → Einstrahlung → Wärme → Hotspots."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np
import requests

from terrainclearance.geo import CoordTransformer

from .config import ThermalConfig
from .domain import build_domain
from .heating import compute_heat, cumulative_energy_at
from .horizon import horizon_and_svf
from .hotspots import detect, write_hotspots
from .irradiance import compute_clearsky_irradiance
from .buoyancy import thermal_source_field
from .landcover import classify
from .nwp import fetch_cloud_attenuation
from .report import (build_cumulative_energy_3d_files, build_energy_3d, plot_attenuation_timeseries,
                     plot_cumulative_panels_png, plot_field_png, plot_hotspot_map_html,
                     plot_relief_png, plot_aspect_slope_png, plot_landcover_3d, write_geotiffs)
from .reproject import lv95_to_wgs84
from .terrain_derivs import load_terrain

log = logging.getLogger(__name__)


def _horizon_cached(cfg: ThermalConfig, grid, dtm):
    """Horizont/SVF berechnen oder aus Cache laden (tagesunabhängig)."""
    key = f"{grid.west:.0f}_{grid.north:.0f}_{grid.nx}_{grid.ny}_{grid.res:.1f}_{cfg.n_azimuth}"
    h = hashlib.md5(key.encode()).hexdigest()[:10]
    cache = Path(cfg.cache_dir) / "thermal" / f"horizon_{h}.npz"
    if cache.exists():
        d = np.load(cache)
        log.info("Horizont aus Cache: %s", cache.name)
        return d["horizon"], d["azimuths"], d["svf"]
    log.info("Horizont/SVF berechnen (einmalig) …")
    horizon, az, svf = horizon_and_svf(dtm, grid.res, cfg.n_azimuth, cfg.horizon_max_steps, cfg.horizon_step_m)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, horizon=horizon, azimuths=az, svf=svf)
    return horizon, az, svf


def run_phase_a(cfg: ThermalConfig) -> dict:
    session = requests.Session()
    tf = CoordTransformer(use_network=False)
    grid, mask, poly, (lons, lats) = build_domain(cfg, tf)
    bbox = (float(lons.min()), float(lats.min()), float(lons.max()), float(lats.max()))
    log.info("Gebiet: %dx%d @ %.0f m (%.0f%% im Polygon)", grid.nx, grid.ny, grid.res, 100 * mask.mean())

    terrain = load_terrain(cfg, grid, bbox, session)
    horizon, az, svf = _horizon_cached(cfg, grid, terrain.dtm)

    # Domänen-Mittelpunkt für Sonnenstand/Klarhimmel
    clon, clat = lv95_to_wgs84((grid.west + grid.nx * grid.res / 2), (grid.north - grid.ny * grid.res / 2))
    alt = float(np.nanmean(terrain.dtm[mask]))
    irr = compute_clearsky_irradiance(cfg, terrain, horizon, az, svf, float(clat), float(clon), alt)

    lc = classify(cfg, terrain, grid, session)
    heat = compute_heat(irr, lc, label="ideal")
    hotspots, score = detect(cfg, terrain, heat, lc, grid, mask)
    d0 = thermal_source_field(cfg, terrain, heat, lc, mask)   # D0 Quell-Wahrscheinlichkeit

    out = Path(cfg.output_dir)
    write_geotiffs(grid, mask, terrain, heat, score, out, "ideal")
    # Schritt-für-Schritt-Herleitung (für die README-Narrative): Relief → Exposition/Steilheit → Wald aufs Relief
    plot_relief_png(grid, mask, terrain.dtm, out / "relief.png",
                    "Elevation model (swissALTI3D) — Niesen/Frutigen")
    plot_aspect_slope_png(grid, mask, terrain, out / "aspect_slope.png",
                          "Exposure (aspect) & steepness (slope), derived from the relief")
    plot_landcover_3d(grid, mask, terrain.dtm, lc, out / "landcover_3d.html",
                      f"Forest cover type on the relief — {cfg.date}")
    png = plot_field_png(grid, mask, terrain.dtm, heat.Q_H_daymax, hotspots,
                         f"Ideal Q_H heat-flux map (daily max) — {cfg.date}", out / "qh_ideal_daymax.png")
    html = plot_hotspot_map_html(hotspots, cfg, out / "hotspots.html")
    build_energy_3d(grid, mask, terrain.dtm, heat.Q_H_energy, hotspots,
                    out / "energy_3d.html",
                    f"Deposited Q_H energy (ideal) — {cfg.date}")
    # D0: Thermik-Quell-Wahrscheinlichkeit (validiertes Proxy) als GeoTIFF + 3D
    grid.to_geotiff(np.where(mask, d0.prob, np.nan), out / "d0_thermal_source.tif")
    build_energy_3d(grid, mask, terrain.dtm, d0.prob, hotspots, out / "d0_thermal_source_3d.html",
                    f"D0 thermal-source probability — {cfg.date}",
                    colorbar="Source prob. [0..1]", cmin=0.0, cmax=1.0, colorscale="Viridis")

    # Kumulierter Energieeintrag zu mehreren Tageszeiten
    cum = cumulative_energy_at(heat, cfg.cumulative_hours)
    cum_png = plot_cumulative_panels_png(
        grid, mask, terrain.dtm, cum, out / "energy_cumulative_panels.png",
        f"Cumulative Q_H energy input (ideal) — {cfg.date}")
    cum_3d_paths, _ = build_cumulative_energy_3d_files(
        grid, mask, terrain.dtm, cum, out, f"Q_H energy input (ideal, {cfg.date})")
    for h, f in cum:
        grid.to_geotiff(np.where(mask, f, np.nan), out / f"qh_ideal_energy_bis{int(h):02d}h.tif")

    # --- A5b: reales (wolkengedämpftes) Wärmebild via ICON-CH1 (Open-Meteo) ---
    real = {}
    try:
        clouds = fetch_cloud_attenuation(cfg, grid, float(clat), float(clon), alt, session)
        real_irr = compute_clearsky_irradiance(cfg, terrain, horizon, az, svf,
                                                float(clat), float(clon), alt, atten=clouds)
        heat_real = compute_heat(real_irr, lc, label="real")
        write_geotiffs(grid, mask, terrain, heat_real, score, out, "real")
        diff_energy = heat.Q_H_energy - heat_real.Q_H_energy   # durch Wolken "verlorene" Energie
        grid.to_geotiff(np.where(mask, diff_energy, np.nan), out / "qh_diff_energy.tif")
        real["att_png"] = plot_attenuation_timeseries(clouds, out / "icon_attenuation.png", cfg.date)
        real["daymax_png"] = plot_field_png(
            grid, mask, terrain.dtm, heat_real.Q_H_daymax, hotspots,
            f"Real Q_H heat-flux map (daily max, ICON clouds) — {cfg.date}", out / "qh_real_daymax.png")
        real["diff_png"] = plot_field_png(
            grid, mask, terrain.dtm, diff_energy, None,
            f"Cloud loss of Q_H energy (ideal − real) — {cfg.date}", out / "qh_diff_energy.png",
            cmap="inferno", unit="Wh/m²")
        build_energy_3d(grid, mask, terrain.dtm, heat_real.Q_H_energy, hotspots,
                        out / "energy_3d_real.html",
                        f"Reale Energiemenge Q_H (ICON-Wolken) — {cfg.date}")
        cum_real = cumulative_energy_at(heat_real, cfg.cumulative_hours)
        real["cum_png"] = plot_cumulative_panels_png(
            grid, mask, terrain.dtm, cum_real, out / "energy_cumulative_real_panels.png",
            f"Kumulierter realer Energieeintrag Q_H (ICON-Wolken) — {cfg.date}")
        real.update(clouds=clouds, heat=heat_real)
        log.info("A5b real: Bewölkung Tagesmittel %.0f%%, Q_H-Energie ideal->real median %.0f->%.0f Wh/m²",
                 float(clouds.mean_cloud.mean()), float(np.median(heat.Q_H_energy[mask])),
                 float(np.median(heat_real.Q_H_energy[mask])))
    except Exception as exc:
        log.warning("A5b (reales Wärmebild) übersprungen: %s", exc)

    write_hotspots(hotspots, out / "hotspots.csv", out / "hotspots.geojson")

    paths = {"png": str(png), "html": str(html), "energy_3d": str(out / "energy_3d.html"),
             "cum_png": str(cum_png), "cum_3d": [str(p) for p in cum_3d_paths], "out": str(out)}
    paths.update({k: str(v) for k, v in real.items() if k.endswith("_png")})
    return {
        "grid": grid, "mask": mask, "terrain": terrain, "irr": irr, "lc": lc,
        "heat": heat, "hotspots": hotspots, "score": score, "cumulative": cum,
        "d0": d0, "real": real, "forest_source": lc.forest_source, "paths": paths,
    }
