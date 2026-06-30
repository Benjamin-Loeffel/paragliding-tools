"""CLI: kompletter Thermik-Ablauf reproduzierbar.

  Phase A (ideal+real Wärmebild, D0) → Validierung (IGC + kk7) → Phase B (z_i/w*/Ceiling)
  → D1 (Lagrange-Plume). Schreibt alle Produkte nach output/thermal.

Beispiel:
    python thermal.py
    python thermal.py --date 2026-06-29 --skip-plume
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import numpy as np

from .config import ThermalConfig
from .pipeline import run_phase_a

log = logging.getLogger("thermal")


def _validate(cfg, res, igc_dir):
    from terrainclearance.geo import CoordTransformer
    from .reproject import lv95_to_wgs84
    from .validation.igc_climbs import collect_climbs
    from .validation.kk7 import fetch_kk7_hotspots
    from .validation.metrics import validate, plot_validation_map

    grid, mask = res["grid"], res["mask"]
    tf = CoordTransformer(use_network=False)
    climbs = collect_climbs(igc_dir, tf, bounds_lv95=grid.bounds()) if Path(igc_dir).exists() else []
    w, s, e, n = grid.bounds()
    lons, lats = lv95_to_wgs84(np.array([w, e, w, e]), np.array([s, s, n, n]))
    bbox = (float(lons.min()), float(lats.min()), float(lons.max()), float(lats.max()))
    try:
        kk7 = fetch_kk7_hotspots(bbox, tf=tf, cache_dir=cfg.cache_dir)
    except Exception as exc:
        log.warning("kk7 nicht erreichbar: %s", exc); kk7 = []

    out = Path(cfg.output_dir)
    score, qh, hs = res["score"], res["heat"].Q_H_daymax, res["hotspots"]
    d0 = res["d0"].prob
    for name, fld in (("Phase-A-Score", score), ("D0-Quellwahrsch.", d0)):
        line = f"{name:18s}"
        for tgt, te, tn in (("IGC", [c.e0 for c in climbs], [c.n0 for c in climbs]),
                            ("kk7", [k.e for k in kk7], [k.n for k in kk7])):
            if len(te):
                m = validate(grid, mask, fld, qh, hs, te, tn)
                line += f"  {tgt} AUC {m['auc_score']:.3f}"
        log.info("Validierung %s", line)
    if climbs:
        plot_validation_map(grid, mask, res["terrain"].dtm, d0, hs, climbs,
                            out / "validation_map.png",
                            f"Validierung: D0 vs. IGC-Steigflüge + kk7 — Modelltag {cfg.date}", kk7=kk7)
        log.info("Validierungskarte: %s", out / "validation_map.png")

    # kk7-HEATMAP (Thermals-Tiles) als kontinuierliches Target
    try:
        from .validation.kk7_heatmap import fetch_thermals_intensity, plot_heatmap
        from .validation.metrics import heatmap_metrics
        kk7h = fetch_thermals_intensity(cfg, grid, category="jul_07", zoom=12)
        for name, fld in (("Phase-A-Score", score), ("D0-Quellwahrsch.", d0)):
            m = heatmap_metrics(grid, mask, fld, kk7h)
            if m:
                log.info("kk7-Heatmap %s: Spearman %.3f, AUC(>p70) %.3f (n=%d, 250m-geglättet)",
                         name, m["spearman"], m["auc"], m["n"])
        plot_heatmap(grid, mask, res["terrain"].dtm, kk7h, out / "kk7_heatmap.png",
                     f"kk7 Thermals-Heatmap (jul_07, Sommer-Mittag, klimatologisch) — Modelltag {cfg.date}")
    except Exception as exc:
        log.warning("kk7-Heatmap übersprungen: %s", exc)

    # kk7 ZEITGEFILTERT (jul_04/07/10) gegen das momentan aktive Modellquellfeld
    try:
        _kk7_timefiltered(cfg, res)
    except Exception as exc:
        log.warning("kk7-zeitgefiltert übersprungen: %s", exc)
    return climbs, kk7


def _load_sounding(archive_dir):
    """Payerne-Sondierung laden (meteo-Tool, current-day im Archiv)."""
    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo / "meteo"))
    import radiosonde_payerne as rp
    items = rp.load_archive(Path(archive_dir))
    if not items:
        return None
    meta, df, _ = items[-1]
    return df


def _phase_b_d1(cfg, res, archive_dir):
    from .boundarylayer import analyze_sounding, thermal_strength
    from .plume import run_plumes, plot_drift_map, seeds_from_hotspots
    from .valleywind import upslope_field

    try:
        df = _load_sounding(archive_dir)
    except Exception as exc:
        log.warning("Phase B/D1 übersprungen (Sondierung nicht ladbar): %s", exc); return
    if df is None:
        log.warning("Phase B/D1 übersprungen (keine Sondierung im Archiv)"); return

    bl = analyze_sounding(df)
    qh = res["real"]["heat"].Q_H_daymax if "heat" in res.get("real", {}) else res["heat"].Q_H_daymax
    ts = thermal_strength(bl, res["hotspots"], qh, res["grid"], res["terrain"])
    ws = np.array([t["w_star_ms"] for t in ts])
    log.info("Phase B: Wolkenbasis/Ceiling-Basis %.0f m AMSL, w* median %.2f m/s (max %.2f)",
             bl.cloud_base_amsl, float(np.median(ws)), float(ws.max()))

    out = Path(cfg.output_dir)
    with open(out / "hotspots_strength.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["id", "elev_m", "q_h", "z_i_m", "w_star_ms", "ceiling_amsl"])
        for t in ts:
            wr.writerow([t["id"], round(t["elev_m"]), round(t["q_h"]), round(t["z_i_m"]),
                         round(t["w_star_ms"], 2), round(t["ceiling_amsl"])])

    from .landcover import forest_edge
    vw = upslope_field(res["terrain"], qh, res["grid"], res["mask"])   # Phase C: Hangaufwind
    vege = forest_edge(res["lc"])                                      # Waldgrenzen als Ablöse-Trigger
    seeds = seeds_from_hotspots(res["hotspots"])
    tracks = run_plumes(seeds, bl, qh, res["grid"], res["terrain"], cfg, valley=vw, veg_edge=vege)
    if tracks:
        dr = np.array([t.drift_m for t in tracks])
        rate = float(np.median([t.drift_m / max(t.duration_s, 1) * 60 for t in tracks]))
        relshift = float(np.median([np.hypot(t.release_e - t.e[0], t.release_n - t.n[0])
                                    for t in tracks]))
        log.info("D1 (Tagesmax-Referenz): %d Plumes, Drift median %.0f m (max %.0f m), "
                 "Drift-Rate %.0f m/min (IGC-Ref ~74); Ablöse-Versatz Hotspot→Release median %.0f m",
                 len(tracks), float(np.median(dr)), float(dr.max()), rate, relshift)
        plot_drift_map(res["grid"], res["mask"], res["terrain"].dtm, tracks, res["d0"].prob,
                       out / "d1_drift_map.png", f"D1 Thermik-Drift (Auslöser→Top, Tagesmax) — {cfg.date}")

    # Zeitaufgelöste Drifts + die 3 Plume-Varianten (Hotspots/kk7/Netz) als Slider-3D + Wind-Traces (11/13/15/18 h)
    try:
        from .timedrift import run_time_resolved
        run_time_resolved(cfg, res, bl, vw)
    except Exception as exc:
        log.warning("Zeitaufgelöste Drifts/Plumes übersprungen: %s", exc)


def _kk7_timefiltered(cfg, res):
    """kk7-Heatmap je Tageszeit (jul_04/07/10) gegen das momentan aktive Modellquellfeld
    (D0 × normiertes Q_H(t)) — testet, ob Zeitabgleich die Übereinstimmung hebt."""
    import numpy as np
    from .validation.kk7_heatmap import fetch_thermals_intensity, plot_heatmap
    from .validation.metrics import heatmap_metrics
    from .hotspots import _norm01
    grid, mask, terr = res["grid"], res["mask"], res["terrain"]
    heat = res["real"]["heat"] if "heat" in res.get("real", {}) else res["heat"]
    d0 = res["d0"].prob
    out = Path(cfg.output_dir)
    hrs = heat.times.hour + heat.times.minute / 60.0
    for cat, hour, lbl in (("jul_04", 11, "Morgen"), ("jul_07", 13, "Mittag"), ("jul_10", 17, "Abend")):
        try:
            kk7 = fetch_thermals_intensity(cfg, grid, category=cat, zoom=12)
        except Exception as exc:
            log.warning("kk7 %s übersprungen: %s", cat, exc); continue
        idx = int(np.argmin(np.abs(hrs - hour)))
        model_t = np.where(mask, d0 * _norm01(heat.Q_H[idx], mask), np.nan)
        m_t = heatmap_metrics(grid, mask, model_t, kk7)
        m_s = heatmap_metrics(grid, mask, d0, kk7)
        if m_t and m_s:
            log.info("kk7 %-6s (%s, ~%02d:00): Modell-aktiv AUC %.3f / Spearman %.3f  vs  statisch D0 AUC %.3f",
                     cat, lbl, hour, m_t["auc"], m_t["spearman"], m_s["auc"])
        plot_heatmap(grid, mask, terr.dtm, kk7, out / f"kk7_heatmap_{cat}.png",
                     f"kk7 Thermals-Heatmap {cat} ({lbl}) — Modelltag {cfg.date}")


def _retrospective(cfg, igc_dir):
    from .domain import build_domain
    from .reproject import lv95_to_wgs84
    from .validation.retrospective import (run_retrospective, summarize, spearman_table,
                                           plot_retrospective, validate_xcontest_bigdays)
    from terrainclearance.geo import CoordTransformer
    grid, _, _, _ = build_domain(cfg, CoordTransformer(use_network=False))
    clon, clat = lv95_to_wgs84(grid.west + grid.nx * grid.res / 2, grid.north - grid.ny * grid.res / 2)
    res = run_retrospective(igc_dir, float(clat), float(clon), cache_dir=cfg.cache_dir)
    recs = summarize(res)
    log.info("Retrospektive Validierung: %d Thermik-Flugtage", len(recs))
    for k, v in spearman_table(recs).items():
        log.info("  Spearman %-26s %+.2f", k, v)
    if recs:
        plot_retrospective(recs, Path(cfg.output_dir) / "retro_validation.png")
        log.info("  (reale Reanalyse-Strahlung + Analyse-Profil = Vorhersagbarkeits-Obergrenze; "
                 "kleines Sample → indikativ. Plot: retro_validation.png)")
    # XContest-Rekordtage (browser-quelliert): hätte das Modell die Big-Days erkannt?
    import numpy as np
    bd = validate_xcontest_bigdays(float(clat), float(clon), cache_dir=cfg.cache_dir)
    if bd:
        xc = [b["xc_day"] for b in bd]; zi = [b["z_i_peak_amsl"] for b in bd]
        log.info("XContest-Rekordtage (n=%d): Modell-XC median %.0f%% (min %.0f%%), z_i median %.0f m "
                 "→ z_i robuster Prädiktor; w*-XC verpasst einzelne Big-Days",
                 len(bd), float(np.median(xc)), float(np.min(xc)), float(np.median(zi)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Solargetriebene Thermik-Modellierung (Phase A–D1).")
    ap.add_argument("--kml", default=ThermalConfig.kml_path)
    ap.add_argument("--igc", default="examples/data/igc")
    ap.add_argument("--sounding-archive", default="meteo/archive")
    ap.add_argument("--out", default="output/thermal")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--date", default="2026-06-30")  # heute; Sondierung nutzt die neueste verfügbare
    ap.add_argument("--skip-validation", action="store_true")
    ap.add_argument("--skip-plume", action="store_true", help="Phase B + D1 auslassen")
    ap.add_argument("--retrospective", action="store_true",
                    help="Retrospektive Prognose-Validierung gegen eigene IGC-Flugtage")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = ThermalConfig(kml_path=args.kml, cache_dir=Path(args.cache),
                        output_dir=Path(args.out), date=args.date)
    log.info("== Phase A (ideal+real, D0) ==")
    res = run_phase_a(cfg)
    log.info("Domäne %dx%d, %d Hotspots, Waldquelle %s",
             res["grid"].nx, res["grid"].ny, len(res["hotspots"]), res["forest_source"])
    if not args.skip_validation:
        log.info("== Validierung (IGC + kk7) ==")
        _validate(cfg, res, args.igc)
    if not args.skip_plume:
        log.info("== Phase B + D1 ==")
        _phase_b_d1(cfg, res, args.sounding_archive)
    if args.retrospective:
        log.info("== Retrospektive Validierung (eigene Flugtage) ==")
        _retrospective(cfg, args.igc)
    log.info("Fertig. Ausgaben in %s", cfg.output_dir)
    return 0
