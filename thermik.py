#!/usr/bin/env python
"""Detaillierte Thermik-Prognose für einen (kommenden) Tag — Adelboden/Frutigen/Niesen.

Schwesterskript zum Flugtag-Briefing (`flightday.py`), aber in die Tiefe: volles thermalmodel
(Q_H, Hotspots, w*/z_i/Ceiling, D1-Plumes als 3D-Slider, zeitaufgelöste Drifts, Wind-Traces,
XC-Potenzial, Startfenster) für einen wählbaren Tag — plus eine **Pro-Startplatz-Tabelle**.

Der kommende Tag hat keine echte Sondierung → das Vertikalprofil kommt aus dem ICON-Modell
(`meteo/forecast_sounding.py`). Für HEUTE wird, wenn verfügbar, die echte Payerne-Sondierung genommen.

Ausgabe: `output/thermal_forecast/<datum>/` mit thermik.md/.html/.json + allen Plots (inkl. der
interaktiven D1-Plume-3D-Slider und dem Prognose-Emagramm). GRUNDSATZ wie beim Briefing: liefert
Fakten/Modellwerte, entscheidet nicht — Prognose-Konfidenz sinkt mit dem Vorlauf.

Beispiel:
    python thermik.py                     # morgen
    python thermik.py --date 2026-07-04
    python thermik.py --skip-plumes       # ohne die schweren 3D-Plume-Slider (schneller)
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import logging
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "meteo"))

import numpy as np
import requests

log = logging.getLogger("thermik")


def _sample(field, e, n, grid):
    col = min(max(int((e - grid.west) / grid.res), 0), grid.nx - 1)
    row = min(max(int((grid.north - n) / grid.res), 0), grid.ny - 1)
    return float(field[row, col])


def _load_sounding(date: str, center_lat: float, center_lon: float, out_dir: Path, session):
    """(meta, df, quelle) — heute echte Payerne, sonst ICON-Prognose-Profil am Domänenzentrum."""
    import radiosonde_payerne as rp
    import forecast_sounding as fs
    today = _dt.date.today().isoformat()
    if date == today:
        try:
            meta, df = rp.parse_vzus01(rp.fetch_vzus01(session))
            return meta, df, "Payerne-Sondierung (Messung, 12 UTC)"
        except Exception as exc:
            log.warning("Payerne nicht verfügbar (%s) → ICON-Prognose-Profil", exc)
    meta, df = fs.fetch_forecast_profile(center_lat, center_lon, date, hour=13,
                                         cache_dir=str(out_dir.parents[1].parent / "cache")
                                         if False else "cache", session=session)
    return meta, df, "ICON-Prognose-Profil (Druckflächen, ~13 h)"


def _per_site(cfg, res, bl, qh, gw) -> list[dict]:
    """Pro Startplatz: w*/z_i/Ceiling (lokal via strength_at), nächster Hotspot, Wind auf Ceiling.

    gw = GriddedWind (wf.griddize(stunde)) → `uv(e,n,z)` liefert den Wind am Punkt auf Ceiling-Höhe."""
    from thermalmodel.boundarylayer import strength_at
    from terrainclearance.geo import CoordTransformer
    tf = CoordTransformer(use_network=False)
    grid, dtm, hotspots = res["grid"], res["terrain"].dtm, res["hotspots"]
    w, s, e_, n_ = grid.bounds()
    rows = []
    for name, lon, lat in cfg.launch_sites:
        E, N = tf.to_lv95(np.array([lon]), np.array([lat])); e, n = float(E[0]), float(N[0])
        if not (w <= e <= e_ and s <= n <= n_):
            rows.append({"name": name, "in_domain": False}); continue
        elev = _sample(dtm, e, n, grid); qh_local = _sample(qh, e, n, grid)
        st = strength_at(bl, elev, qh_local)
        nearest = min(((math.hypot(e - h.e, n - h.n), h) for h in hotspots), default=(None, None)) \
            if hotspots else (None, None)
        wck = wcd = None
        try:
            uu, vv = gw.uv(e, n, st["ceiling_amsl"])          # Wind auf Ceiling-Höhe am Startplatz
            wck = round(math.hypot(uu, vv) * 3.6); wcd = round(math.degrees(math.atan2(-uu, -vv)) % 360)
        except Exception as exc:
            log.debug("Wind@Ceiling %s übersprungen: %s", name, exc)
        rows.append({"name": name, "in_domain": True, "elev_m": round(elev),
                     "w_star_ms": round(st["w_star_ms"], 2), "z_i_m": round(st["z_i_m"]),
                     "ceiling_amsl_m": round(st["ceiling_amsl"]), "q_h_wm2": round(qh_local),
                     "nearest_hotspot_km": round(nearest[0] / 1000, 1) if nearest[0] is not None else None,
                     "wind_ceiling_kmh": wck, "wind_ceiling_from_deg": wcd})
    return rows


def _site_table_md(rows) -> str:
    L = ["| Startplatz | Höhe | w\\* | z_i | Ceiling | Q_H | näch. Hotspot | Wind @Ceiling |",
         "|---|--:|--:|--:|--:|--:|--:|--:|"]
    for r in rows:
        if not r.get("in_domain"):
            L.append(f"| **{r['name']}** | — | ausserhalb Domäne | | | | | |"); continue
        wind = f"{r['wind_ceiling_kmh']} km/h aus {r['wind_ceiling_from_deg']}°" if r['wind_ceiling_kmh'] is not None else "—"
        L.append(f"| **{r['name']}** | {r['elev_m']} m | {r['w_star_ms']} m/s | {r['z_i_m']} m | "
                 f"{r['ceiling_amsl_m']} m | {r['q_h_wm2']} W/m² | {r['nearest_hotspot_km']} km | {wind} |")
    return "\n".join(L)


def build(date: str, out_root: str, cache: str, kml: str, resolution: float,
          skip_plumes: bool, session, horizon_workers: int = 1) -> dict:
    from thermalmodel.config import ThermalConfig
    from thermalmodel.pipeline import run_phase_a
    from thermalmodel.boundarylayer import analyze_sounding, thermal_strength
    from thermalmodel.wind import fetch_wind_field
    from thermalmodel.daytimeline import compute_day_timeline, optimal_window
    from thermalmodel.valleywind import upslope_field
    from thermalmodel.reproject import lv95_to_wgs84
    import radiosonde_payerne as rp

    out_dir = Path(out_root) / date
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = ThermalConfig(kml_path=kml, resolution_m=resolution, date=date,
                        cache_dir=Path(cache), output_dir=out_dir, horizon_workers=horizon_workers)

    log.info("== Phase A (Q_H, Hotspots, Wolken) für %s ==", date)
    res = run_phase_a(cfg)
    grid = res["grid"]
    clon, clat = lv95_to_wgs84(grid.west + grid.nx * grid.res / 2, grid.north - grid.ny * grid.res / 2)

    log.info("== Sondierung ==")
    meta, df, src = _load_sounding(date, float(clat), float(clon), out_dir, session)
    try:
        rp.plot_emagram(df, meta, out_dir / "emagram.png")
    except Exception as exc:
        log.warning("Emagramm übersprungen: %s", exc)
    idx = rp.compute_indices(df)
    bl = analyze_sounding(df)
    qh = res["real"]["heat"].Q_H_daymax if "heat" in res.get("real", {}) else res["heat"].Q_H_daymax

    log.info("== Phase B / Tagesverlauf ==")
    wf = fetch_wind_field(cfg, grid, session)
    tl = compute_day_timeline(cfg, res, bl, wf)
    win = optimal_window(tl)

    ts = thermal_strength(bl, res["hotspots"], qh, grid, res["terrain"])
    with open(out_dir / "hotspots_strength.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["id", "elev_m", "q_h", "z_i_m", "w_star_ms", "ceiling_amsl"])
        for t in ts:
            wr.writerow([t["id"], round(t["elev_m"]), round(t["q_h"]), round(t["z_i_m"]),
                         round(t["w_star_ms"], 2), round(t["ceiling_amsl"])])

    peak_h = int(round(win[2])) if win else 15     # Wind zur Bestzeit aufs Gitter → Pro-Startplatz-Wind
    gw = wf.griddize(peak_h)
    sites = _per_site(cfg, res, bl, qh, gw)

    if not skip_plumes:
        log.info("== D1-Plumes / zeitaufgelöste Drifts ==")
        try:
            vw = upslope_field(res["terrain"], qh, grid, res["mask"])
            from thermalmodel.timedrift import run_time_resolved
            run_time_resolved(cfg, res, bl, vw, session=session)
        except Exception as exc:
            log.warning("Plumes/Drifts übersprungen: %s", exc)

    ws = np.array([t["w_star_ms"] for t in ts]) if ts else np.array([np.nan])
    summary = {
        "date": date, "forecast": bool(meta.get("forecast")), "sounding_source": src,
        "indices": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in idx.items()},
        "cloud_base_amsl_m": round(bl.cloud_base_amsl) if bl.cloud_base_amsl else None,
        "thermal_top_amsl_m": round(bl.thermal_top_amsl) if getattr(bl, "thermal_top_amsl", None) else None,
        "w_star_max_ms": round(float(np.nanmax(ws)), 2), "w_star_median_ms": round(float(np.nanmedian(ws)), 2),
        "z_i_peak_amsl_m": round(float(np.nanmax(tl["z_i_amsl"]))), "xc_max_pct": round(float(np.nanmax(tl["xc"]))),
        "window": {"start_h": win[0], "end_h": win[1], "peak_h": win[2]} if win else None,
        "sites": sites,
    }
    (out_dir / "thermik_data.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_md_html(out_dir, date, summary, skip_plumes)
    return summary


def _write_md_html(out_dir: Path, date, S, skip_plumes):
    idx = S["indices"]; w = S.get("window") or {}
    conf = "hoch (ICON-CH1, ~morgen)" if S["forecast"] else "Messung (heute)"
    md = [f"# Thermik-Prognose Adelboden–Frutigen–Niesen — {date}\n",
          f"> **{'Prognose' if S['forecast'] else 'Heute'}** ({S['sounding_source']}). w\\*/Ceiling sind "
          f"Modellwerte; Prognose-Konfidenz sinkt mit dem Vorlauf. Kein Go/No-Go — am Flugtag Live-Check (Briefing/Radar).\n",
          "## Tagesüberblick\n",
          f"- Schichtung: CAPE {idx.get('CAPE_Jkg','–')} J/kg · LI {idx.get('LI','–')} · Nullgrad "
          f"{idx.get('Nullgrad_m','–')} m · Wolkenbasis {S['cloud_base_amsl_m']} m · Thermik-Top {S['thermal_top_amsl_m']} m.\n"
          f"- Thermik: **w\\* max {S['w_star_max_ms']} m/s** (Median {S['w_star_median_ms']}) · z_i-Peak "
          f"**{S['z_i_peak_amsl_m']} m** · XC-Potenzial max {S['xc_max_pct']} %.\n"
          + (f"- **Startfenster ~{w.get('start_h')}–{w.get('end_h')} h (Bestzeit ~{w.get('peak_h')} h)** "
             f"— siehe `day_timeline.png`.\n" if w else ""),
          "## Pro Startplatz\n", _site_table_md(S["sites"]), "",
          "## Plots\n",
          "- `day_timeline.png` (Startfenster) · `emagram.png` (Sondierung) · `xc_potential.png`",
          "- Q_H (mit Startplätzen): `qh_ideal_daymax.png`, `qh_real_daymax.png` · Hotspots: `hotspots.html`",
          ("- D1-Plumes (3D-Slider): `d1_plumes_grid_3d.html`, `d1_plumes_hotspots_3d.html` · "
           "Drifts: `drift_*_grid.png` · Wind: `wind_traces_*.png`" if not skip_plumes else "- (Plumes übersprungen)"),
          ""]
    (out_dir / "thermik.md").write_text("\n".join(md), encoding="utf-8")

    html = [f"<!doctype html><meta charset='utf-8'><title>Thermik-Prognose {date}</title>",
            "<style>body{font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}"
            "img{max-width:100%;border:1px solid #ddd;border-radius:.3rem}iframe{width:100%;height:620px;border:1px solid #ccc}"
            "table{border-collapse:collapse;margin:1rem 0}td,th{border:1px solid #ccc;padding:4px 9px;text-align:right}"
            "td:first-child,th:first-child{text-align:left}</style>",
            f"<h1>Thermik-Prognose Adelboden–Frutigen–Niesen — {date}</h1>",
            f"<p><em>{S['sounding_source']} · {conf}. w*/Ceiling = Modellwerte, kein Go/No-Go.</em></p>",
            f"<p>w* max <b>{S['w_star_max_ms']} m/s</b> · z_i-Peak <b>{S['z_i_peak_amsl_m']} m</b> · "
            f"XC max {S['xc_max_pct']} %"
            + (f" · Startfenster <b>{w.get('start_h')}–{w.get('end_h')} h</b>" if w else "") + ".</p>",
            "<h2>Pro Startplatz</h2>", _site_table_html(S["sites"])]
    for lab, fn in [("Startfenster / Tagesverlauf", "day_timeline.png"), ("Prognose-Emagramm", "emagram.png"),
                    ("Q_H ideal (+ Startplätze)", "qh_ideal_daymax.png"), ("XC-Potenzial", "xc_potential.png")]:
        if (out_dir / fn).exists():
            html.append(f"<h2>{lab}</h2><img src='{fn}'>")
    if not skip_plumes and (out_dir / "d1_plumes_grid_3d.html").exists():
        html.append("<h2>Driftende Plumes (3D, Zeit-Slider)</h2>"
                    "<iframe src='d1_plumes_grid_3d.html' loading='lazy'></iframe>")
    (out_dir / "thermik.html").write_text("\n".join(html), encoding="utf-8")


def _site_table_html(rows) -> str:
    h = ["<table><tr><th>Startplatz</th><th>Höhe</th><th>w*</th><th>z_i</th><th>Ceiling</th>"
         "<th>Q_H</th><th>näch. Hotspot</th><th>Wind @Ceiling</th></tr>"]
    for r in rows:
        if not r.get("in_domain"):
            h.append(f"<tr><td>{r['name']}</td><td colspan='7'>ausserhalb Domäne</td></tr>"); continue
        wind = f"{r['wind_ceiling_kmh']} km/h / {r['wind_ceiling_from_deg']}°" if r['wind_ceiling_kmh'] is not None else "—"
        h.append(f"<tr><td>{r['name']}</td><td>{r['elev_m']} m</td><td>{r['w_star_ms']} m/s</td>"
                 f"<td>{r['z_i_m']} m</td><td>{r['ceiling_amsl_m']} m</td><td>{r['q_h_wm2']} W/m²</td>"
                 f"<td>{r['nearest_hotspot_km']} km</td><td>{wind}</td></tr>")
    h.append("</table>")
    return "\n".join(h)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Detaillierte Thermik-Prognose (Adelboden/Frutigen/Niesen).")
    ap.add_argument("--date", default=(_dt.date.today() + _dt.timedelta(days=1)).isoformat(),
                    help="Zieltag (Default: morgen)")
    ap.add_argument("--out", default="output/thermal_forecast")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--kml", default="examples/data/domain_frutigen_wide.kml")
    ap.add_argument("--resolution", type=float, default=60.0)
    ap.add_argument("--horizon-workers", type=int, default=1,
                    help="Parallel-Prozesse für den Horizont (bei 20 m z. B. 6). 1 = seriell.")
    ap.add_argument("--skip-plumes", action="store_true", help="ohne die schweren 3D-Plume-Slider")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    session = requests.Session()
    S = build(args.date, args.out, args.cache, args.kml, args.resolution, args.skip_plumes, session,
              horizon_workers=args.horizon_workers)
    log.info("Fertig: %s → %s", args.date, Path(args.out) / args.date / "thermik.md")
    print(f"\n  Thermik-Prognose {args.date}: w* max {S['w_star_max_ms']} m/s, z_i {S['z_i_peak_amsl_m']} m, "
          f"XC {S['xc_max_pct']}%")
    for r in S["sites"]:
        if r.get("in_domain"):
            print(f"    {r['name']:14s} w* {r['w_star_ms']} m/s · Ceiling {r['ceiling_amsl_m']} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
