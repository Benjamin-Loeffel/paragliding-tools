#!/usr/bin/env python
"""Voll aufgelöster Thermik-Blick (Q_H) übers ganze Adelboden–Frutigen–Niesen-Gebiet — nur zum Schauen.

Ein Einzelprozess müsste für die ~39×39-km-Domäne bei 20 m ~3,3 Mio. Zellen samt Horizont
rechnen (lange + RAM-hungrig). Dieses Tool KACHELT die Domäne in ein nx×ny-Raster und rechnet
die Kacheln PARALLEL in eigenen Python-Prozessen (`thermal.py --skip-plume --skip-validation
--resolution R`), danach mosaikt es die georeferenzierten `qh_ideal_daymax.tif` via
rasterio.merge zu EINEM nahtlosen Bild (Q_H + Relief, mit Startplatz-Markern). Der Fernhorizont
je Kachel bleibt korrekt (die Pipeline lädt DEM `horizon_margin_m` über den Kachelrand hinaus),
darum ist das Mosaik nahtlos.

    python hires_forecast.py                            # morgen, 2×2 Kacheln @20 m
    python hires_forecast.py --date 2026-07-04 --nx 3 --ny 3
    python hires_forecast.py --stitch-only              # nur mosaiken (Kacheln existieren schon)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from rasterio.merge import merge

from thermalmodel.grids import Grid
from thermalmodel.config import ThermalConfig
from thermalmodel.terrain_derivs import load_terrain
from thermalmodel.report import plot_field_png, plot_relief_png
from thermalmodel.reproject import lv95_to_wgs84
from terrainclearance.geo import CoordTransformer

KML_TPL = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{name}</name>'
           '<Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>\n'
           '{w},{s} {e},{s} {e},{n} {w},{n} {w},{s}\n'
           '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>')


def _kml_bbox(path):
    coords = re.findall(r"(-?\d+\.\d+),(-?\d+\.\d+)", Path(path).read_text(encoding="utf-8"))
    lons = [float(a) for a, _ in coords]; lats = [float(b) for _, b in coords]
    return min(lons), min(lats), max(lons), max(lats)


def _make_tiles(bbox, nx, ny, overlap, out):
    """nx×ny Kachel-KMLs mit `overlap`-Grad Überlappung an den inneren Rändern (nahtloses Mosaik)."""
    w, s, e, n = bbox
    xs = np.linspace(w, e, nx + 1); ys = np.linspace(s, n, ny + 1)
    tiles = []
    for j in range(ny):
        for i in range(nx):
            tw = xs[i] - (overlap if i else 0); te = xs[i + 1] + (overlap if i < nx - 1 else 0)
            ts = ys[j] - (overlap if j else 0); tn = ys[j + 1] + (overlap if j < ny - 1 else 0)
            name = f"tile_{j}{i}"
            p = out / f"{name}.kml"
            p.write_text(KML_TPL.format(name=name, w=round(tw, 4), e=round(te, 4),
                                        s=round(ts, 4), n=round(tn, 4)), encoding="utf-8")
            tiles.append((name, p))
    return tiles


def _run_tile(name, kml, date, res, cache, out):
    tdir = out / name
    cmd = [sys.executable, str(ROOT / "thermal.py"), "--skip-plume", "--skip-validation",
           "--resolution", str(res), "--date", date, "--kml", str(kml),
           "--out", str(tdir), "--cache", cache]
    with open(out / f"{name}.log", "w", encoding="utf-8") as fh:
        rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(ROOT)).returncode
    return name, rc, (tdir / "qh_ideal_daymax.tif").exists()


def _grid_from_transform(t, ny, nx):
    return Grid(res=float(t.a), west=float(t.c), north=float(t.f), nx=int(nx), ny=int(ny))


def _lonlat_bbox(grid, margin=0.01):
    w, s, e, n = grid.bounds()
    lon, lat = lv95_to_wgs84(np.array([w, e, w, e]), np.array([n, n, s, s]))
    return (float(lon.min()) - margin, float(lat.min()) - margin,
            float(lon.max()) + margin, float(lat.max()) + margin)


def stitch(tile_names, out, date):
    """Mosaikt die Kachel-`qh_ideal_daymax.tif` → Q_H- und Relief-PNG (Hillshade + Startplätze)."""
    have = [out / t / "qh_ideal_daymax.tif" for t in tile_names]
    have = [p for p in have if p.exists()]
    if len(have) < 2:
        print(f"Zu wenige Kacheln fertig ({len(have)}) — nichts zu mosaiken."); return 1
    print(f"Mosaik aus {len(have)} Kacheln …")
    srcs = [rasterio.open(p) for p in have]
    Q, tr = merge(srcs, nodata=np.nan)
    for s in srcs:
        s.close()
    Q = Q[0]; ny, nx = Q.shape
    grid = _grid_from_transform(tr, ny, nx)
    print(f"Gitter: {nx}x{ny} @ {grid.res:.0f} m  (~{nx*grid.res/1000:.0f}x{ny*grid.res/1000:.0f} km, "
          f"{nx*ny/1e6:.1f} Mio. Zellen)")
    mask = np.isfinite(Q)
    cfg = ThermalConfig(dtm_resolution=2.0, cache_dir=ROOT / "cache")
    try:
        dtm = load_terrain(cfg, grid, _lonlat_bbox(grid)).dtm
        print("DTM fürs Hillshade nachgeladen (passgenau zum Mosaik).")
    except Exception as exc:
        print(f"DTM-Load fehlgeschlagen ({exc}) → flaches Hillshade."); dtm = np.zeros_like(Q)

    tf = CoordTransformer(use_network=False)
    sites = []
    for nm, lon, lat in cfg.launch_sites:
        E, N = tf.to_lv95(np.array([lon]), np.array([lat])); sites.append((nm, float(E[0]), float(N[0])))

    qp = out / f"qh_ideal_daymax_hires_{date}.png"
    plot_field_png(grid, mask, dtm, Q, None,
                   f"Ideal Q_H (Tagesmax) @ {grid.res:.0f} m — Adelboden–Frutigen–Niesen — {date}",
                   qp, cmap="inferno", unit="W/m²", sites=sites)
    print(f"  geschrieben: {qp}")
    if dtm.any():
        rp = out / "relief_hires.png"
        plot_relief_png(grid, mask, dtm, rp,
                        f"Relief (swissALTI3D) @ {grid.res:.0f} m — Adelboden–Frutigen–Niesen")
        print(f"  geschrieben: {rp}")
    grid.to_geotiff(np.where(mask, Q, np.nan), out / f"qh_ideal_daymax_mosaic_{date}.tif")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Voll aufgelöster Q_H-Blick via parallel gerechneter Kacheln.")
    ap.add_argument("--date", default=(_dt.date.today() + _dt.timedelta(days=1)).isoformat())
    ap.add_argument("--resolution", type=float, default=20.0)
    ap.add_argument("--nx", type=int, default=2)
    ap.add_argument("--ny", type=int, default=2)
    ap.add_argument("--overlap", type=float, default=0.01, help="Kachel-Überlappung [Grad]")
    ap.add_argument("--kml", default="examples/data/domain_frutigen_wide.kml")
    ap.add_argument("--out", default="output/hires")
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--max-parallel", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--stitch-only", action="store_true", help="nur mosaiken (Kacheln existieren schon)")
    ap.add_argument("--force", action="store_true", help="Kacheln neu rechnen, auch wenn tif existiert")
    args = ap.parse_args(argv)

    out = Path(args.out); (out / "tiles").mkdir(parents=True, exist_ok=True)
    tiles = _make_tiles(_kml_bbox(args.kml), args.nx, args.ny, args.overlap, out / "tiles")
    names = [n for n, _ in tiles]

    if not args.stitch_only:
        todo = [(n, k) for n, k in tiles
                if args.force or not (out / n / "qh_ideal_daymax.tif").exists()]
        par = min(max(1, args.max_parallel), len(todo)) if todo else 0
        print(f"{len(tiles)} Kacheln, {len(todo)} zu rechnen, {par} parallel @ {args.resolution:.0f} m, Tag {args.date}")
        with ThreadPoolExecutor(max_workers=max(1, par or 1)) as ex:
            for name, rc, ok in ex.map(
                    lambda t: _run_tile(t[0], t[1], args.date, args.resolution, args.cache, out), todo):
                print(f"  {name}: rc={rc} {'OK' if ok else 'FEHLT — siehe ' + name + '.log'}")
    return stitch(names, out, args.date)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
