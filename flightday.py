#!/usr/bin/env python
"""Flugtag-Morgen-Briefing (Niesen/Frutigen) — orchestriert Sondierung + Synoptik + Thermikmodell
zu einem reproduzierbaren, strukturierten Briefing nach der SHV-Meteo-Entscheidungsstrategie.

Erzeugt in `output/briefings/<datum>/`:
  briefing_data.json   — Maschinendaten: je Phänomen {wert, schwelle, ampel, begründung} + Kennzahlen
  briefing.md          — automatisches Basis-Briefing (Claude/Skill komponiert daraus die Endfassung)
  briefing.html        — Übersicht mit eingebetteten interaktiven Plots + PNGs
  ch_precip.html / ch_solar.html / ch_wind.html — interaktive CH-Karten (Zeit-Slider)
  ch_overview.png / frutigen_radius.png / emagram.png / day_timeline.png [+ wind/xc]

GRUNDSATZ: entscheidet NICHT. Liefert Fakten + Ampeln + den 3×A-Rahmen — der Pilot entscheidet.

Beispiel:
    python flightday.py                     # heute, volle Analyse (inkl. Thermikmodell)
    python flightday.py --skip-thermal      # nur Sondierung + Synoptik (schnell)
    python flightday.py --date 2026-07-01 --resolution 60
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "meteo"))

import numpy as np
import requests

log = logging.getLogger("flightday")

AMPEL_EMOJI = {"günstig": "🟢", "achtung": "🟡", "alarm": "🔴", "n/a": "⚪"}

# Pilot-Checkliste: Quellen, die nur der Pilot anschaut (nicht maschinell im Briefing).
PILOT_LINKS = [
    ("Niederschlagsradar (live)", "https://www.meteoschweiz.admin.ch/service-und-publikationen/applikationen/messwerte-und-messnetze.html#niederschlag"),
    ("Satellitenbild / Bodenwetterkarte", "https://www.meteoschweiz.admin.ch/wetter/wetter-und-klima-in-der-schweiz.html"),
    ("Textprognose MeteoSchweiz", "https://www.meteoschweiz.admin.ch/wetter/wettervorhersage/lokalprognosen.html"),
    ("soaringmeteo (soarWRF Alpen)", "https://soaringmeteo.org/"),
    ("meteo-parapente (RASP)", "https://meteo-parapente.com/"),
    ("SHV-Karte «Alpines Pumpen»", "https://www.shv-fsvl.ch/de/ausbildung-sicherheit/sicherheit/meteo/"),
    ("Fluggebiets-Webcams / Holfuy", "https://holfuy.com/de/map"),
]


def _lapse_band(df, z0=1500.0, z1=3000.0):
    """Temperaturgradient im Flughöhenband [°C/100 m] (negativ = Abkühlung mit Höhe)."""
    d = df.dropna(subset=["height", "temperature"]).sort_values("height")
    h = d["height"].to_numpy(float); t = d["temperature"].to_numpy(float)
    if len(h) < 2 or h.min() > z0 or h.max() < z1:
        return None
    return float((np.interp(z1, h, t) - np.interp(z0, h, t)) / (z1 - z0) * 100.0)


def run_sounding(out_dir: Path, session) -> dict:
    """Payerne-Sondierung: Indizes + Lapse-Rate + Wolkenbasis + Emagramm (best effort)."""
    import radiosonde_payerne as rp
    out = {"ok": False}
    try:
        rp.harvest(Path("meteo/archive"), session)     # archivieren → Thermikmodell nutzt es
    except Exception as exc:
        log.warning("Sondierung harvest übersprungen: %s", exc)
    try:
        meta, df = rp.parse_vzus01(rp.fetch_vzus01(session))
        idx = rp.compute_indices(df)
        try:
            rp.plot_emagram(df, meta, out_dir / "emagram.png")
        except Exception as exc:
            log.warning("Emagramm übersprungen: %s", exc)
        cb = None
        if idx.get("LCL_hPa"):
            d = df.dropna(subset=["pressure", "height"]).sort_values("pressure")
            cb = float(np.interp(idx["LCL_hPa"], d["pressure"].to_numpy(),
                                 d["height"].to_numpy()))
        out = {"ok": True, "indices": idx, "lapse_c_per_100m": _lapse_band(df),
               "cloud_base_amsl_m": cb, "datetime": str(meta.get("datetime")), "_df": df}
    except Exception as exc:
        log.warning("Sondierung nicht verfügbar: %s", exc)
    return out


def run_thermal(date: str, kml: str, resolution: float, cache: str, out_dir: Path,
                sounding_df, session) -> dict:
    """Thermikmodell für heute auf der (vergrösserten) Briefing-Domäne → Tagesverlauf/Startfenster."""
    from thermalmodel.config import ThermalConfig
    from thermalmodel.pipeline import run_phase_a
    from thermalmodel.boundarylayer import analyze_sounding
    from thermalmodel.wind import fetch_wind_field
    from thermalmodel.daytimeline import compute_day_timeline, optimal_window, plot_day_timeline

    # Modell-Rohprodukte (energy_3d*, hotspots, qh_*, tifs …) in einen Unterordner; im Briefing-Ordner
    # bleiben nur die zwei briefing-relevanten Plots (day_timeline, wind_traces).
    thermal_out = out_dir / "thermal"
    thermal_out.mkdir(parents=True, exist_ok=True)
    cfg = ThermalConfig(kml_path=kml, resolution_m=resolution, date=date,
                        cache_dir=Path(cache), output_dir=thermal_out)
    res = run_phase_a(cfg)
    bl = analyze_sounding(sounding_df) if sounding_df is not None else None
    if bl is None:
        raise RuntimeError("keine Sondierung für Phase B")
    wf = fetch_wind_field(cfg, res["grid"], session)
    tl = compute_day_timeline(cfg, res, bl, wf)
    win = optimal_window(tl)
    plot_day_timeline(tl, out_dir / "day_timeline.png", f"Tagesverlauf Frutigen — {date}")
    # optionale Zusatzplots (bei Signatur-/Datenproblemen einfach überspringen)
    try:
        from thermalmodel.wind import plot_wind_traces_levels
        gw = wf.griddize(int(round(win[2])) if win and win[2] else 14)
        plot_wind_traces_levels(res["grid"], res["mask"], res["terrain"].dtm, gw,
                                out_dir / "wind_traces.png", f"ICON-Wind Höhenstufen — {date}")
    except Exception as exc:
        log.warning("Wind-Traces-Plot übersprungen: %s", exc)
    hrs = tl["hrs"]
    return {"ok": True,
            "w_star_max_ms": round(float(np.nanmax(tl["wstar"])), 2),
            "z_i_peak_amsl_m": round(float(np.nanmax(tl["z_i_amsl"]))),
            "cloud_base_amsl_m": round(float(bl.cloud_base_amsl)) if bl.cloud_base_amsl else None,
            "xc_max_pct": round(float(np.nanmax(tl["xc"]))),
            "window": {"start_h": win[0], "end_h": win[1], "peak_h": win[2]} if win else None,
            "viable_hours": [round(float(h), 1) for h in hrs[tl["viable"]]]}


def _row(a: dict) -> str:
    e = AMPEL_EMOJI.get(a.get("ampel"), "⚪")
    return f"| {e} **{a['phaenomen']}** | {a['schwelle']} | {a['begruendung']} |"


def build_briefing_md(date, syn, sounding, thermal, plots) -> str:
    A = syn.assessments
    L = []
    L.append(f"# Flugtag-Briefing Niesen/Frutigen — {date}\n")
    L.append("> **Kein Go/No-Go.** Dieses Briefing sammelt Fakten + Ampeln entlang der SHV-Meteo-"
             "Entscheidungsstrategie. Der 3×A-Entscheid (Ausführen / Alternative / Abbruch) liegt bei dir.\n")
    # METEO
    L.append("## METEO — 5 Phänomene\n")
    L.append("| Ampel · Phänomen | Schwelle | Befund |")
    L.append("|---|---|---|")
    for key in ("wind", "bise", "foehn", "konvektion", "fronten"):
        L.append(_row(A[key]))
    L.append("")
    # Sondierung / Thermik
    if sounding.get("ok"):
        idx = sounding["indices"]
        lp = sounding.get("lapse_c_per_100m"); cb = sounding.get("cloud_base_amsl_m")
        lp_s = f"{lp:.2f}" if lp is not None else "n/a"
        cb_s = f"{cb:.0f}" if cb is not None else "n/a"
        L.append("## Luftschichtung (Payerne-Sondierung)\n")
        L.append(f"- CAPE {idx.get('CAPE_Jkg', float('nan')):.0f} J/kg · LI {idx.get('LI', float('nan')):.1f} · "
                 f"Lapse (1.5–3 km) {lp_s} °C/100 m (≥ −0.8 = gefährlich labil) · "
                 f"Wolkenbasis {cb_s} m · Nullgrad {idx.get('Nullgrad_m')} m. Emagramm: `emagram.png`.\n")
    if thermal.get("ok"):
        w = thermal.get("window") or {}
        L.append("## Thermik & Startfenster (Thermikmodell)\n")
        L.append(f"- w\\* max **{thermal['w_star_max_ms']} m/s** · z_i-Peak **{thermal['z_i_peak_amsl_m']} m** · "
                 f"Wolkenbasis {thermal.get('cloud_base_amsl_m')} m · XC-Potenzial max {thermal['xc_max_pct']} %.\n")
        if w:
            L.append(f"- **Startfenster ~{w.get('start_h')}–{w.get('end_h')} h (Bestzeit ~{w.get('peak_h')} h).** "
                     f"Siehe `day_timeline.png`.\n")
    # interaktive Plots
    L.append("## Interaktive Karten (Zeit-Slider)\n")
    for label, fn in plots.get("interactive", []):
        L.append(f"- [{label}]({fn})")
    L.append("\nStatische Übersichten: `ch_overview.png`, `frutigen_radius.png`"
             + (", `day_timeline.png`" if thermal.get("ok") else "") + ".\n")
    # GELÄNDE
    L.append("## GELÄNDE (Niesen/Frutigen)\n")
    L.append("- **Startplatz:** Windrichtung/-stärke am Start? Hangausrichtung zur erwarteten Strömung? Tageszeit passend zum Startfenster?\n"
             "- **Flugweg:** Starkwind-Stellen (Pässe, Kreten, Talverengungen)? Luv/Lee bei der prognostizierten Höhenwind-/Föhnlage? Bei Südföhn: Lee-Turbulenz nördlich der Kreten.\n"
             "- **Landeplatz:** jederzeit erreichbar? Starkwindlandung möglich (Talwind Kandertal/Thunersee am Nachmittag)?\n")
    # MENSCH
    L.append("## MENSCH\n")
    L.append("- **Selbsteinschätzung:** Vorhaben ↔ Fähigkeiten/Tagesform? Bauchgefühl ↔ Verstand? Mehr Zeit/Info nötig?\n"
             "- **Wahrnehmungsfallen:** Vertrautheit, Routine (ging schon immer gut), Gruppendruck, seltene Gelegenheit, Wunschdenken, Zeit-/Wirtschaftsdruck, Social Media.\n"
             "- **Gruppe:** Wer kommt mit, Erwartungen, Rollen, offene Kommunikation?\n")
    # Entscheid
    L.append("## Entscheid — 3×A\n")
    n_alarm = sum(1 for a in A.values() if a.get("ampel") == "alarm")
    n_acht = sum(1 for a in A.values() if a.get("ampel") == "achtung")
    L.append(f"- Meteo-Ampeln: **{n_alarm}× Alarm**, {n_acht}× Achtung. Mehrere kritische Faktoren = gefährliche Verkettung.\n"
             "- **AUSFÜHREN | ALTERNATIVE | ABBRUCH** — bewusst, rechtzeitig, unabhängig von der Gruppe. Plan B/C bereithalten.\n")
    # Checkliste
    L.append("## Pilot-Checkliste (selbst anschauen)\n")
    for name, url in PILOT_LINKS:
        L.append(f"- [{name}]({url})")
    L.append("")
    return "\n".join(L)


def build_briefing_html(date, md_html_note, plots) -> str:
    parts = [f"<!doctype html><meta charset='utf-8'><title>Flugtag-Briefing {date}</title>",
             "<style>body{font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}"
             "iframe{width:100%;height:620px;border:1px solid #ccc;border-radius:.3rem}"
             "img{max-width:100%;border:1px solid #ddd;border-radius:.3rem}h2{margin-top:2rem}</style>",
             f"<h1>Flugtag-Briefing Niesen/Frutigen — {date}</h1>",
             "<p><em>Kein Go/No-Go — Fakten + Ampeln nach SHV-Meteo-Entscheidungsstrategie; der 3×A-Entscheid liegt beim Piloten.</em></p>",
             md_html_note]
    for label, fn in plots.get("interactive", []):
        parts.append(f"<h2>{label}</h2><iframe src='{fn}' loading='lazy'></iframe>")
    for label, fn in plots.get("static", []):
        parts.append(f"<h2>{label}</h2><img src='{fn}'>")
    return "\n".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Flugtag-Morgen-Briefing (Niesen/Frutigen).")
    ap.add_argument("--date", default=_dt.date.today().isoformat())
    ap.add_argument("--out", default="output/briefings")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--kml", default="examples/data/domain_frutigen_wide.kml")
    ap.add_argument("--resolution", type=float, default=60.0, help="Modellgitter [m] für den Morgenlauf")
    ap.add_argument("--skip-thermal", action="store_true", help="Thermikmodell auslassen (schnell)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    date = args.date
    out_dir = Path(args.out) / date
    out_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    import synoptic as S
    import synoptic_plots as SP

    log.info("== Synoptik (CH + Frutigen-Radius) ==")
    syn = S.fetch_synoptic(date, cache_dir=args.cache, session=session)

    log.info("== Payerne-Sondierung ==")
    sounding = run_sounding(out_dir, session)
    # Konvektions-Ampel mit Sondierungs-Labilität/Wolkenbasis verfeinern
    syn.assessments["konvektion"] = S.assess_convection(
        syn, sounding.get("lapse_c_per_100m"), sounding.get("cloud_base_amsl_m"))

    thermal = {"ok": False}
    if not args.skip_thermal:
        log.info("== Thermikmodell (vergrösserte Domäne %s @ %.0f m) ==", args.kml, args.resolution)
        try:
            thermal = run_thermal(date, args.kml, args.resolution, args.cache, out_dir,
                                  sounding.get("_df"), session)
        except Exception as exc:
            log.warning("Thermikmodell übersprungen: %s", exc)

    log.info("== Plots ==")
    interactive, static = [], []
    try:
        SP.build_ch_precip(syn, out_dir / "ch_precip.html", date)
        interactive.append(("Niederschlag CH (Zeit-Slider)", "ch_precip.html"))
        SP.build_ch_solar(syn, out_dir / "ch_solar.html", date)
        interactive.append(("Sonneneinstrahlung CH (Zeit-Slider)", "ch_solar.html"))
        SP.build_ch_wind_slider(syn, out_dir / "ch_wind.html", f"Wind CH (Höhenstufen) — {date}")
        interactive.append(("Wind CH — Höhenstufen + Zeit-Slider", "ch_wind.html"))
        SP.plot_ch_overview(syn, out_dir / "ch_overview.png", f"Schweiz-Übersicht — {date}")
        static.append(("Schweiz-Übersicht", "ch_overview.png"))
        SP.plot_frutigen_radius(syn, out_dir / "frutigen_radius.png", f"Frutigen ±24 km — {date}")
        static.append(("Frutigen-Radius — Tagesverlauf", "frutigen_radius.png"))
    except Exception as exc:
        log.warning("Ein Plot übersprungen: %s", exc)
    if sounding.get("ok") and (out_dir / "emagram.png").exists():
        static.append(("Payerne-Emagramm", "emagram.png"))
    if thermal.get("ok") and (out_dir / "day_timeline.png").exists():
        static.append(("Tagesverlauf / Startfenster", "day_timeline.png"))
    plots = {"interactive": interactive, "static": static}

    # briefing_data.json (ohne den DataFrame)
    sdump = {k: v for k, v in sounding.items() if k != "_df"}
    data = {"date": date, "assessments": syn.assessments, "sounding": sdump,
            "thermal": thermal, "plots": plots,
            "dp_ns_max_hPa": round(float(np.nanmax(np.abs(syn.dp_ns))), 1),
            "dp_we_max_hPa": round(float(np.nanmax(syn.dp_we)), 1)}
    (out_dir / "briefing_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    md = build_briefing_md(date, syn, sounding, thermal, plots)
    (out_dir / "briefing.md").write_text(md, encoding="utf-8")
    (out_dir / "briefing.html").write_text(
        build_briefing_html(date, "<p>Automatisches Basis-Briefing — Details siehe briefing.md.</p>", plots),
        encoding="utf-8")

    n_alarm = sum(1 for a in syn.assessments.values() if a.get("ampel") == "alarm")
    log.info("Fertig: %s  (%d× Alarm) → %s", date, n_alarm, out_dir / "briefing.md")
    print("\n" + "\n".join(f"  {AMPEL_EMOJI.get(a['ampel'],'⚪')} {a['phaenomen']}: {a['ampel']}"
                           for a in syn.assessments.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
