"""Zeitaufgelöste Thermik-Drifts zu festen Uhrzeiten (wie die Energiesummen: 11/13/15/18 h).

Je Zeitpunkt:
  - w*(t) aus dem momentanen (realen, wolkengedämpften) Q_H(t),
  - ICON-Windfeld(t) als Advektion (icon_seamless, Druckniveaus),
  - zwei Karten: (a) Drift ab unseren Hotspots + kk7-Hotspots, (b) Drift-Feld ab regelmässigem Netz,
  - ein Wind-Partikeltrace zum selben Zeitpunkt (visueller Abgleich Drift ↔ Wind).
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)


def _nearest_step(times, hour):
    hrs = times.hour + times.minute / 60.0
    return int(np.argmin(np.abs(hrs - hour)))


def run_time_resolved(cfg, res, bl, vw, session=None):
    from .plume import (run_plumes, seeds_from_hotspots, seeds_from_points, seeds_from_field,
                        grid_seeds, plot_drift_map, plot_drift_quiver, build_plume_3d_timeslider)
    from .reproject import lv95_to_wgs84
    from .validation.kk7 import fetch_kk7_hotspots
    from .wind import fetch_wind_field, plot_wind_traces_levels

    from .boundarylayer import cbl_timeseries
    grid, mask, terr = res["grid"], res["mask"], res["terrain"]
    dtm = terr.dtm
    heat = res["real"]["heat"] if "heat" in res.get("real", {}) else res["heat"]
    out = Path(cfg.output_dir)

    # CBL-Tagesgang z_i(t): skaliert die nutzbare Bandtiefe je Uhrzeit
    qh_mean = np.array([heat.Q_H[i][mask].mean() for i in range(len(heat.times))])
    cbl = cbl_timeseries(bl, heat.times, qh_mean)

    wf = fetch_wind_field(cfg, grid, session)
    w, s, e, n = grid.bounds()
    lons, lats = lv95_to_wgs84(np.array([w, e, w, e]), np.array([s, s, n, n]))
    bbox = (float(lons.min()), float(lats.min()), float(lons.max()), float(lats.max()))
    try:
        kk7 = fetch_kk7_hotspots(bbox, cache_dir=cfg.cache_dir, session=session)
    except Exception:
        kk7 = []
    from .landcover import forest_edge
    vege = forest_edge(res["lc"])                       # Waldgrenzen als Ablöse-Trigger

    # Seed-Sets: 2D-Karten + die 3 zeitaufgelösten 3D-Plume-Varianten
    hot_seeds = seeds_from_hotspots(res["hotspots"])                          # Variante 1: unsere Hotspots
    kk7vec_seeds = seeds_from_points([(k.e, k.n) for k in kk7], terr, grid, id0=10000)  # 2D-Karte: bekannte kk7-Punkte
    gseeds = grid_seeds(grid, mask, terr, spacing_m=cfg.drift_grid_spacing_m)  # 2D-Quiver (feines Netz)
    g3d_seeds = grid_seeds(grid, mask, terr, spacing_m=cfg.plume3d_grid_spacing_m)  # Variante 3: gröberes 3D-Netz
    try:                                                                      # Variante 2: kk7-Heatmap-Quellen
        from .validation.kk7_heatmap import fetch_thermals_intensity
        kk7_field = fetch_thermals_intensity(cfg, grid, category="jul_07", zoom=12)
        kk7field_seeds = seeds_from_field(kk7_field, grid, mask, terr, pct=80.0, max_seeds=400)
    except Exception as exc:
        log.warning("kk7-Heatmap-Seeds übersprungen: %s", exc); kk7field_seeds = []
    log.info("Zeitaufgelöste Drifts/Plumes: %d Hotspot-, %d kk7-Feld-, %d 3D-Netz-Seeds (%.0f m), "
             "%d 2D-Netz-Seeds (%.0f m), %d kk7-Punkte",
             len(hot_seeds), len(kk7field_seeds), len(g3d_seeds), cfg.plume3d_grid_spacing_m,
             len(gseeds), cfg.drift_grid_spacing_m, len(kk7vec_seeds))

    by_hot, by_kk7, by_grid = {}, {}, {}                # {Stunde: tracks} für die 3 Slider

    def _plumes(seeds, qh_t, wind_fn, g):
        return run_plumes(seeds, bl, qh_t, grid, terr, cfg, valley=vw, wind_uv_fn=wind_fn,
                          band_scale=g, veg_edge=vege) if seeds else []

    for h in cfg.cumulative_hours_drift:
        idx = _nearest_step(heat.times, h)
        qh_t = heat.Q_H[idx]
        g = float(cbl["growth"][idx])          # CBL-Wachstumsanteil → Bandtiefe-Skalierung
        gw = wf.griddize(h)
        wind_fn = gw.uv
        hot_tr = _plumes(hot_seeds, qh_t, wind_fn, g)
        kk7vec_tr = _plumes(kk7vec_seeds, qh_t, wind_fn, g)
        kk7field_tr = _plumes(kk7field_seeds, qh_t, wind_fn, g)
        grid2d_tr = _plumes(gseeds, qh_t, wind_fn, g)
        grid3d_tr = _plumes(g3d_seeds, qh_t, wind_fn, g)
        by_hot[h], by_kk7[h], by_grid[h] = hot_tr, kk7field_tr, grid3d_tr
        tr_a = hot_tr + kk7vec_tr                         # 2D-Punktkarte: Hotspots + bekannte kk7
        da = np.median([t.drift_m for t in tr_a]) if tr_a else 0.0
        db = np.median([t.drift_m for t in grid2d_tr]) if grid2d_tr else 0.0
        log.info("  %02d:00: Q_H med %.0f W/m², z_i %.0f m AMSL (growth %.2f), "
                 "Punkt-Drift med %.0f m / Netz-Drift med %.0f m",
                 h, float(np.median(qh_t[mask])), float(cbl["z_i_amsl"][idx]), g, da, db)
        plot_drift_map(grid, mask, dtm, tr_a, res["d0"].prob,
                       out / f"drift_{h:02d}h_points.png",
                       f"Thermik-Drift {h:02d}:00 — Hotspots + kk7 ({cfg.date})")
        plot_drift_quiver(grid, mask, dtm, grid2d_tr, res["d0"].prob,
                          out / f"drift_{h:02d}h_grid.png",
                          f"Thermik-Drift-Feld {h:02d}:00 — {cfg.drift_grid_spacing_m:.0f} m-Netz ({cfg.date})",
                          wind_gw=gw)
        plot_wind_traces_levels(grid, mask, dtm, gw, out / f"wind_traces_{h:02d}h.png",
                                f"ICON-Wind-Traces {h:02d}:00 ({cfg.wind_model}) — {cfg.date}")

    # Die 3 Plume-Varianten zeitaufgelöst als je 1 HTML mit Uhrzeit-Slider (11/13/15/18 h)
    hh = "/".join(f"{h:02d}" for h in cfg.cumulative_hours_drift)
    if any(by_hot.values()):
        build_plume_3d_timeslider(grid, mask, dtm, by_hot, out / "d1_plumes_hotspots_3d.html",
                                  f"D1 Plumes — unsere Hotspots, zeitaufgelöst {hh} h ({cfg.date})")
    if any(by_grid.values()):
        build_plume_3d_timeslider(grid, mask, dtm, by_grid, out / "d1_plumes_grid_3d.html",
                                  f"D1 Plumes — {cfg.plume3d_grid_spacing_m:.0f} m-Netz, zeitaufgelöst {hh} h ({cfg.date})")
    if any(by_kk7.values()):
        build_plume_3d_timeslider(grid, mask, dtm, by_kk7, out / "d1_plumes_kk7_3d.html",
                                  f"D1 Plumes — kk7-Heatmap-Quellen, zeitaufgelöst {hh} h ({cfg.date})")
    log.info("D1-Plumes zeitaufgelöst (Slider %s h): Hotspots/kk7/Netz als 3 HTML geschrieben", hh)

    # XC-Flugpotenzial (soaringmeteo-Adoption) zur Mittagszeit
    try:
        from .xcpotential import xc_potential_field, plot_xc_potential
        qh_day = heat.Q_H_daymax
        thq = xc_potential_field(cfg, res, bl, wf.griddize(13), qh_day)
        grid.to_geotiff(thq, out / "xc_potential.tif")
        plot_xc_potential(grid, mask, terr.dtm, thq, out / "xc_potential.png",
                          f"XC-Flugpotenzial (Tagesgüte, soaringmeteo-Stil) — {cfg.date}")
        log.info("XC-Potenzial: median %.0f%%, max %.0f%% (im Gebiet)",
                 float(np.nanmedian(thq[mask])), float(np.nanmax(thq[mask])))
    except Exception as exc:
        log.warning("XC-Potenzial übersprungen: %s", exc)

    # Tages-Timeline: 'wann starten?' + Wind-Zerstörung
    try:
        from .daytimeline import compute_day_timeline, plot_day_timeline, optimal_window
        tl = compute_day_timeline(cfg, res, bl, wf)
        plot_day_timeline(tl, out / "day_timeline.png",
                          f"Thermik-Tagesgang Niesen/Frutigen — {cfg.date}")
        win = optimal_window(tl)
        if win:
            log.info("Optimales Startfenster: %.0f–%.0f Uhr (Bestzeit ~%.0f:%02d), "
                     "max XC %.0f%%, max w* %.2f m/s",
                     win[0], win[1], int(win[2]), int((win[2] % 1) * 60),
                     float(np.nanmax(tl["xc"])), float(np.nanmax(tl["wstar"])))
        n_destroy = int((~tl["viable"] & (tl["wind_bl"] >= tl["cloud_destroy_ms"])).sum())
        if n_destroy:
            log.info("Wind-Zerstörung: %d Zeitschritte mit BL-Wind > %.0f km/h",
                     n_destroy, tl["cloud_destroy_ms"] * 3.6)
    except Exception as exc:
        log.warning("Tages-Timeline übersprungen: %s", exc)
    return wf
