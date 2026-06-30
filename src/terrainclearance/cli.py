"""Kommandozeilen-Schnittstelle der Geländeabstand-Analyse."""

from __future__ import annotations

import argparse
import glob
import logging
import sys
from pathlib import Path

import requests

from .config import Config
from .distribution import build_aggregate_kde, build_risk_over_time
from .geo import CoordTransformer
from .pipeline import analyze_flight
from .report import save_png


def _resolve_inputs(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            for ext in ("*.igc", "*.IGC"):
                files.extend(p.glob(ext))
        elif any(ch in item for ch in "*?[]"):
            files.extend(Path(x) for x in glob.glob(item))
        elif p.exists():
            files.append(p)
        else:
            logging.warning("Eingabe nicht gefunden: %s", item)
    # Dedupe (Windows: case-insensitiv)
    seen, out = set(), []
    for f in files:
        key = str(f.resolve()).lower()
        if key not in seen:
            seen.add(key)
            out.append(f)
    return sorted(out)


def main(argv=None) -> int:
    # Windows-Konsole ist standardmässig cp1252 -> Umlaute/Symbole crashen sonst.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(
        prog="terrainclearance",
        description="Minimaler 3D-Geländeabstand für Gleitschirm-IGC-Tracks (swisstopo).",
    )
    ap.add_argument("inputs", nargs="+", help="IGC-Datei(en), Glob-Muster oder Verzeichnis")
    ap.add_argument("--output-dir", default="output")
    ap.add_argument("--cache-dir", default="cache")
    ap.add_argument("--resolution", type=float, default=0.5, help="Rasterauflösung in m (0.5 oder 2)")
    ap.add_argument("--r-cap", type=float, default=None, help="Max. Suchradius in m (Default 300)")
    ap.add_argument("--calibration", choices=["auto", "gnss", "pressure", "none"], default="auto")
    ap.add_argument("--timezone", default="Europe/Zurich", help="Zeitzone fürs Barogramm")
    ap.add_argument("--no-proj-network", action="store_true",
                    help="PROJ-Netzwerk (CHENYX06-Grid) nicht nutzen")
    ap.add_argument("--no-3d", action="store_true", help="Keinen interaktiven 3D-Plot erzeugen")
    ap.add_argument("--surface3d-model", choices=["dsm", "dtm"], default="dsm",
                    help="Modell der 3D-Oberfläche (Default dsm = inkl. Wald/Gebäude)")
    ap.add_argument("--surface3d-max-dim", type=int, default=None,
                    help="Max. Gitter-Kantenlänge des 3D-Reliefs (höher = feiner, grössere HTML)")
    ap.add_argument("--surface3d-darkness", type=float, default=None,
                    help="0..1: Dunkelheit der 3D-Schummerung (Default 0.5)")
    ap.add_argument("--surface3d-color", choices=["clearance", "p05", "mean"], default=None,
                    help="3D-Spur einfärben nach Schätzwert (clearance), MC-Untergrenze (p05) oder Mittel")
    ap.add_argument("--no-uncertainty", action="store_true",
                    help="Kein Monte-Carlo-Unsicherheitsband (schneller)")
    ap.add_argument("--sigma-h", type=float, default=None, help="1σ horizontaler GPS-Fehler [m]")
    ap.add_argument("--sigma-v", type=float, default=None, help="1σ vertikaler GPS-Fehler [m]")
    ap.add_argument("--png", action="store_true",
                    help="Zusätzlich statische PNGs exportieren (3D-Karte, Aggregat-KDE, Risiko; braucht kaleido)")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )

    cfg = Config(
        resolution=args.resolution,
        cache_dir=Path(args.cache_dir),
        output_dir=Path(args.output_dir),
        calibration=args.calibration,
        timezone=args.timezone,
        use_proj_network=not args.no_proj_network,
        surface3d=not args.no_3d,
        surface3d_model=args.surface3d_model,
        uncertainty=not args.no_uncertainty,
    )
    if args.r_cap is not None:
        cfg.r_cap_m = args.r_cap
    if args.sigma_h is not None:
        cfg.gps_sigma_h_m = args.sigma_h
    if args.sigma_v is not None:
        cfg.gps_sigma_v_m = args.sigma_v
    if args.surface3d_max_dim is not None:
        cfg.surface3d_max_dim = args.surface3d_max_dim
    if args.surface3d_darkness is not None:
        cfg.surface3d_darkness = args.surface3d_darkness
    if args.surface3d_color is not None:
        cfg.surface3d_color_by = args.surface3d_color
    cfg.export_png = args.png

    files = _resolve_inputs(args.inputs)
    if not files:
        print("Keine IGC-Dateien gefunden.", file=sys.stderr)
        return 1

    session = requests.Session()
    transformer = CoordTransformer(cfg.use_proj_network)

    print(f"\n{len(files)} Flug/Flüge zu analysieren.\n")
    summaries = []
    for f in files:
        try:
            s = analyze_flight(f, cfg, session, transformer)
            summaries.append(s)
            _print_summary(s)
        except Exception as exc:  # pragma: no cover
            logging.exception("Fehler bei %s: %s", f.name, exc)

    # Mehrflug-Zusammenzug der Hangabstand-Verteilung
    dists = [s["dist_terrain"] for s in summaries if s.get("dist_terrain") is not None]
    if dists:
        agg_path = cfg.output_dir / "aggregate_clearance_kde.html"
        agg_fig = build_aggregate_kde(dists, cfg)
        agg_fig.write_html(str(agg_path), include_plotlyjs=True)
        if cfg.export_png:
            save_png(agg_fig, cfg.output_dir / "aggregate_clearance_kde.png", 1100, 950)
        print(f"\n══ Zusammenzug über {len(dists)} Flüge → {agg_path}")
        if sum(1 for d in dists if d.start_dt is not None) >= 2:
            risk_path = cfg.output_dir / "risk_over_time.html"
            risk_fig = build_risk_over_time(dists, cfg)
            risk_fig.write_html(str(risk_path), include_plotlyjs=True)
            if cfg.export_png:
                save_png(risk_fig, cfg.output_dir / "risk_over_time.png", 1100, 750)
            print(f"══ Risiko über Zeit → {risk_path}")

    return 0


def _print_summary(s: dict) -> None:
    print(f"\n── {s['flight']} ──")
    print(f"   Fixes: {s['n_fixes']}, Höhenquelle: {s['alt_source']}, "
          f"Offset: {s['offset_m']:+} m ({s['calib_confidence']})")
    print(f"   Min. 3D-Abstand im Flug — Gelände: {s['min_d3_terrain_m']} m | "
          f"Oberfläche: {s['min_d3_surface_m']} m")
    print(f"   Kritische Events: {s['n_events']}")
    for e in s["events"][:8]:
        print(f"     • {e.iso_time}  {e.level:7s} {e.phase:11s} "
              f"Gelände {e.d3_terrain:5.0f} m / Oberfläche {e.d3_surface:5.0f} m"
              + ("  [clipped]" if e.clipped else ""))
    if s["n_events"] > 8:
        print(f"     … und {s['n_events'] - 8} weitere (siehe events.csv)")
    print(f"   → Karte: {s['paths']['map']}")
    print(f"   → Barogramm: {s['paths']['barogram']}")
    if "terrain3d" in s["paths"]:
        print(f"   → 3D-Plot: {s['paths']['terrain3d']}")
    if "clearance_kde" in s["paths"]:
        print(f"   → Abstand-Verteilung: {s['paths']['clearance_kde']}")


if __name__ == "__main__":
    raise SystemExit(main())
