#!/usr/bin/env python
"""Radiosondierung Payerne (MeteoSchweiz) – Emagramm/Skew-T + thermodynamische Indizes.

HINTERGRUND / DATENQUELLEN (Stand 2026-06, recherchiert & verifiziert)
----------------------------------------------------------------------
* MeteoSchweiz Open Data (OGD) liefert nur die **aktuelle** Payerne-Sondierung als CSV:
    https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv
    (Legende: .../Legende_VZUS01.csv) — je Start (00 & 12 UTC) überschrieben.
  → KEIN öffentliches Archiv und KEINE Archiv-PDFs der Emagramme.
* Das Uni-Wyoming-Archiv (sonst Standard für historische Soundings) führt Payerne
  (WMO 06610) NICHT – MeteoSchweiz meldet nur hochauflösendes BUFR, das Wyoming nicht
  einliest (verifiziert: 0/18 Termine, Referenzstation Stuttgart 10739 liefert Daten).
* Die MeteoSchweiz-Web-App zeigt zwar Vergangenheit, ihr Backend ist aber nicht
  öffentlich dokumentiert.

KONSEQUENZ
----------
Die *vergangenen* 12-UTC-Emagramme sind aus offiziellen offenen Quellen nicht abrufbar.
Tragfähiger Weg: die offizielle aktuelle Sondierung selbst auswerten (dieses Skript)
und **ab jetzt täglich mitschneiden** (`harvest`), damit ein 2-Wochen-Archiv entsteht.
Das Emagramm wird mit MetPy aus den Rohdaten gezeichnet (volle Kontrolle + Indizes) –
inhaltlich identisch zum MeteoSchweiz-Emagramm, aber reproduzierbar.

Zusätzlich liess sich das Backend der Web-App entschlüsseln: die **offiziellen
Emagramm-PDFs** sind über versions.json -> data.json -> PDF headless ladbar – aber auch
data.json listet nur den aktuellen Tag (00 & 12 UTC), also ebenfalls kein Archiv.
`download` lädt diese offiziellen PDFs (täglich per cron -> Archiv wächst).

NUTZUNG
-------
    python meteo/radiosonde_payerne.py download              # offizielle Emagramm-PDFs (Payerne, 12 UTC)
    python meteo/radiosonde_payerne.py latest                # Rohdaten selbst -> Emagramm + Indizes
    python meteo/radiosonde_payerne.py harvest               # Rohdaten-Snapshot ins Archiv (cron-tauglich)
    python meteo/radiosonde_payerne.py archive --hour 12 --days 14   # alle 12-UTC-Emagramme aus Archiv
    python meteo/radiosonde_payerne.py trend  --hour 12      # Index-Zeitreihe aus Archiv
"""

from __future__ import annotations

import argparse
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

VZUS01_URL = "https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv"
STATION = "Payerne (06610)"

# Offizielle Emagramm-PDFs der MeteoSchweiz-Web-App (per Browser-Reverse-Engineering gefunden):
#   versions.json -> aktuelle Version je Produkt
#   .../emagram/version__<ver>/data.json -> verfügbare Sondierungen + PDF-Pfade
# ACHTUNG: data.json listet nur den AKTUELLEN Tag (00 & 12 UTC). Kein Archiv ->
# für ein 2-Wochen-Fenster täglich herunterladen (cron).
PRODUCT_BASE = "https://www.meteoschweiz.admin.ch/product/output"
EMAGRAM_BASE = f"{PRODUCT_BASE}/radio-soundings/emagram"

# Spalten-Codes (aus Legende_VZUS01.csv) -> sprechende Namen
COLMAP = {
    "zzzztttt": "datetime", "yloclas0": "lat", "yloclos0": "lon",
    "zxltcos0": "level_type", "zreppps0": "pressure", "zreppzs0": "height",
    "zrettts0": "temperature", "zretdes0": "dewpoint", "zretdds0": "dewpoint_depr",
    "zklddds0": "wind_dir", "zklfffs0": "wind_speed",
}


# ----------------------------------------------------------------------------- fetch/parse
def fetch_vzus01(session: requests.Session | None = None) -> str:
    s = session or requests.Session()
    s.headers.setdefault("User-Agent", "meteo-analytics/0.1")
    r = s.get(VZUS01_URL, timeout=60)
    r.raise_for_status()
    return r.text


def parse_vzus01(text: str) -> tuple[dict, pd.DataFrame]:
    """Rohes VZUS01-CSV (Leerzeichen-getrennt, '/' = fehlend) -> (meta, profil-DataFrame)."""
    codes: list[str] | None = None
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.split()[0] == "IIiii":          # Spaltenkopf
            codes = line.split()
            continue
        if line.startswith("0-20000-0-06610") and codes:
            rows.append(line.split())
    if not codes or not rows:
        raise ValueError("VZUS01: keine Profildaten gefunden.")

    raw = pd.DataFrame(rows, columns=codes)
    df = pd.DataFrame()
    for code, name in COLMAP.items():
        if code in raw.columns:
            df[name] = raw[code]
    df = df.replace("/", np.nan)
    for c in ["lat", "lon", "pressure", "height", "temperature", "dewpoint",
              "dewpoint_depr", "wind_dir", "wind_speed"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Taupunkt ggf. aus Temperatur - Taupunktdifferenz ergänzen
    if "dewpoint" in df and "dewpoint_depr" in df and "temperature" in df:
        miss = df["dewpoint"].isna() & df["temperature"].notna() & df["dewpoint_depr"].notna()
        df.loc[miss, "dewpoint"] = df.loc[miss, "temperature"] - df.loc[miss, "dewpoint_depr"]

    dt_raw = str(raw["zzzztttt"].iloc[0]) if "zzzztttt" in raw else ""
    meta = {
        "station": STATION,
        "datetime": datetime.strptime(dt_raw, "%Y%m%d%H%M").replace(tzinfo=timezone.utc) if len(dt_raw) >= 12 else None,
        "lat": float(df["lat"].dropna().iloc[0]) if df["lat"].notna().any() else None,
        "lon": float(df["lon"].dropna().iloc[0]) if df["lon"].notna().any() else None,
    }
    df = df.dropna(subset=["pressure"]).sort_values("pressure", ascending=False).reset_index(drop=True)
    return meta, df


# ----------------------------------------------------------------------------- analytics + plot
def _thermo(df: pd.DataFrame):
    """Saubere, druckmonoton fallende Profilarrays mit Einheiten (für MetPy)."""
    from metpy.units import units
    t = df.dropna(subset=["pressure", "temperature", "dewpoint"]).drop_duplicates("pressure")
    t = t.sort_values("pressure", ascending=False)
    p = t["pressure"].to_numpy() * units.hPa
    T = t["temperature"].to_numpy() * units.degC
    Td = t["dewpoint"].to_numpy() * units.degC
    return p, T, Td


def compute_indices(df: pd.DataFrame) -> dict:
    import metpy.calc as mpcalc
    from metpy.units import units
    p, T, Td = _thermo(df)
    out: dict[str, float] = {}
    if len(p) < 3:
        return out
    try:
        prof = mpcalc.parcel_profile(p, T[0], Td[0]).to("degC")
        cape, cin = mpcalc.surface_based_cape_cin(p, T, Td)
        out["CAPE_Jkg"] = float(cape.m); out["CIN_Jkg"] = float(cin.m)
        out["LI"] = float(mpcalc.lifted_index(p, T, prof).m[0])
    except Exception:
        pass
    try:
        lcl_p, _ = mpcalc.lcl(p[0], T[0], Td[0]); out["LCL_hPa"] = float(lcl_p.m)
    except Exception:
        pass
    try:
        lfc_p, _ = mpcalc.lfc(p, T, Td)
        out["LFC_hPa"] = None if np.isnan(lfc_p.m) else float(lfc_p.m)
    except Exception:
        pass
    try:
        out["PWAT_mm"] = float(mpcalc.precipitable_water(p, Td).to("mm").m)
    except Exception:
        pass
    # Nullgradgrenze (erste Höhe mit T <= 0)
    z = df.dropna(subset=["temperature", "height"]).sort_values("pressure", ascending=False)
    below = z[z["temperature"] <= 0]
    if not below.empty:
        out["Nullgrad_m"] = float(below["height"].iloc[0])
    return out


def plot_emagram(df: pd.DataFrame, meta: dict, out_path: Path, rotation: float = 45.0) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import metpy.calc as mpcalc
    from metpy.plots import SkewT
    from metpy.units import units

    p, T, Td = _thermo(df)
    idx = compute_indices(df)

    fig = plt.figure(figsize=(8.5, 9.5))
    skew = SkewT(fig, rotation=rotation)
    skew.plot(p, T, "tab:red", linewidth=2, label="Temperatur")
    skew.plot(p, Td, "tab:green", linewidth=2, label="Taupunkt")
    try:
        prof = mpcalc.parcel_profile(p, T[0], Td[0]).to("degC")
        skew.plot(p, prof, "k", linestyle="--", linewidth=1.3, label="Parzelle (SB)")
        skew.shade_cape(p, T, prof)
        skew.shade_cin(p, T, prof, Td)
    except Exception:
        pass

    # Wind-Barbs (m/s -> Knoten), ausgedünnt
    w = df.dropna(subset=["pressure", "wind_dir", "wind_speed"]).drop_duplicates("pressure")
    if len(w) > 2:
        spd = (w["wind_speed"].to_numpy() * units("m/s")).to("knots")
        u, vv = mpcalc.wind_components(spd, w["wind_dir"].to_numpy() * units.deg)
        step = max(1, len(w) // 30)
        skew.plot_barbs(w["pressure"].to_numpy()[::step] * units.hPa, u[::step], vv[::step])

    skew.plot_dry_adiabats(alpha=0.3, linewidth=0.7)
    skew.plot_moist_adiabats(alpha=0.3, linewidth=0.7)
    skew.plot_mixing_lines(alpha=0.3, linewidth=0.7)
    skew.ax.set_ylim(1000, 100)
    skew.ax.set_xlim(-45, 40)
    skew.ax.set_xlabel("Temperatur [°C]")
    skew.ax.set_ylabel("Druck [hPa]")
    skew.ax.legend(loc="upper right", fontsize=8)

    dt = meta.get("datetime")
    dt_s = dt.strftime("%Y-%m-%d %H:%M UTC") if dt else "?"
    fig.suptitle(f"Radiosondierung {meta.get('station', STATION)} — {dt_s}", fontsize=13, y=0.98)

    def f(key, unit, nd=0):
        v = idx.get(key)
        return f"{v:.{nd}f} {unit}" if isinstance(v, (int, float)) and v is not None and not np.isnan(v) else "—"
    txt = (f"CAPE {f('CAPE_Jkg','J/kg')}   CIN {f('CIN_Jkg','J/kg')}   LI {f('LI','',1)}\n"
           f"LCL {f('LCL_hPa','hPa')}   LFC {f('LFC_hPa','hPa')}   PWAT {f('PWAT_mm','mm',1)}\n"
           f"Nullgradgrenze {f('Nullgrad_m','m')}")
    skew.ax.text(0.01, 0.01, txt, transform=skew.ax.transAxes, fontsize=8,
                 va="bottom", ha="left", bbox=dict(boxstyle="round", fc="white", alpha=0.8))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return idx


# ----------------------------------------------------------------------------- archive (harvest)
def harvest(archive_dir: Path, session: requests.Session | None = None) -> Path | None:
    text = fetch_vzus01(session)
    meta, _ = parse_vzus01(text)
    dt = meta["datetime"]
    if dt is None:
        raise ValueError("Kein Sondierungszeitpunkt im VZUS01 gefunden.")
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"payerne_{dt:%Y%m%d_%H}.csv"
    if dest.exists():
        print(f"schon vorhanden: {dest.name}")
        return None
    dest.write_text(text, encoding="utf-8")
    print(f"neu archiviert: {dest.name}  ({dt:%Y-%m-%d %H:%M UTC})")
    return dest


def load_archive(archive_dir: Path, hour: int | None = None, days: int | None = None):
    items = []
    for f in sorted(archive_dir.glob("payerne_*.csv")):
        try:
            meta, df = parse_vzus01(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        dt = meta.get("datetime")
        if dt is None:
            continue
        if hour is not None and dt.hour != hour:
            continue
        items.append((meta, df, f))
    if days is not None and items:
        newest = max(m["datetime"] for m, _, _ in items)
        cutoff = newest.timestamp() - days * 86400
        items = [it for it in items if it[0]["datetime"].timestamp() >= cutoff]
    return sorted(items, key=lambda it: it[0]["datetime"])


# ----------------------------------------------------------------------------- offizielle PDFs
def current_emagram_version(session: requests.Session) -> str:
    v = session.get(f"{PRODUCT_BASE}/versions.json", timeout=60).json()
    return v["radio-soundings/emagram"]


def list_available_soundings(session: requests.Session) -> tuple[str, list[dict]]:
    """(version, [ {datetime, measurements:[{name,path,size}]} ]) der aktuell publizierten Sondierungen."""
    ver = current_emagram_version(session)
    data = session.get(f"{EMAGRAM_BASE}/version__{ver}/data.json", timeout=60).json()
    out = []
    for entry in data:
        dt = datetime.fromtimestamp(entry["timestamp"], tz=timezone.utc)
        out.append({"datetime": dt, "measurements": entry.get("measurements", [])})
    return ver, out


def download_pdfs(pdf_dir: Path, stations=("payerne",), hour: int | None = 12,
                  session: requests.Session | None = None) -> list[Path]:
    """Lädt die aktuell verfügbaren Emagramm-PDFs (gefiltert nach Station/Termin) ins Archiv.
    Idempotent – täglich per cron ausführen, um ein Mehr-Tage-/Wochen-Archiv aufzubauen."""
    s = session or requests.Session()
    s.headers.setdefault("User-Agent", "meteo-analytics/0.1")
    ver, soundings = list_available_soundings(s)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for snd in soundings:
        if hour is not None and snd["datetime"].hour != hour:
            continue
        for m in snd["measurements"]:
            if m.get("type") != "pdf":
                continue
            if stations and m.get("name") not in stations:
                continue
            dest = pdf_dir / Path(m["path"]).name        # Dateiname enthält Station + Zeit
            if dest.exists() and dest.stat().st_size > 0:
                continue
            r = s.get(f"{EMAGRAM_BASE}/version__{ver}/{m['path']}", timeout=60)
            r.raise_for_status()
            dest.write_bytes(r.content)
            saved.append(dest)
            print(f"  geladen: {dest.name}  ({len(r.content)} B)")
    if not saved:
        print("  nichts Neues (alles schon vorhanden oder kein passender Termin).")
    return saved


# ----------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Payerne-Radiosondierung: Emagramm + Indizes.")
    ap.add_argument("mode", choices=["latest", "harvest", "archive", "trend", "download"],
                    nargs="?", default="latest")
    ap.add_argument("--archive-dir", default="meteo/archive")
    ap.add_argument("--pdf-dir", default="meteo/pdf_archive", help="Zielordner für offizielle PDFs (download)")
    ap.add_argument("--stations", default="payerne", help="Komma-Liste, z.B. payerne,stuttgart (download)")
    ap.add_argument("--output-dir", default="output/meteo")
    ap.add_argument("--hour", type=int, default=12, help="UTC-Termin; -1 = alle (Default 12)")
    ap.add_argument("--days", type=int, default=14, help="Zeitfenster für archive/trend (Default 14)")
    ap.add_argument("--rotation", type=float, default=45.0, help="0 = Emagramm, 45 = Skew-T (Default)")
    args = ap.parse_args(argv)

    out_dir = Path(args.output_dir)
    arch = Path(args.archive_dir)
    session = requests.Session()

    if args.mode == "download":
        stations = tuple(x.strip() for x in args.stations.split(",") if x.strip())
        hour = None if args.hour < 0 else args.hour
        print(f"Offizielle Emagramm-PDFs (Stationen={list(stations)}, "
              f"Termin={'alle' if hour is None else f'{hour:02d} UTC'}) -> {args.pdf_dir}")
        download_pdfs(Path(args.pdf_dir), stations=stations, hour=hour, session=session)
        return 0

    if args.mode == "harvest":
        harvest(arch, session)
        return 0

    if args.mode == "latest":
        meta, df = parse_vzus01(fetch_vzus01(session))
        dt = meta["datetime"]
        name = f"payerne_{dt:%Y%m%d_%H}_emagramm.png" if dt else "payerne_emagramm.png"
        idx = plot_emagram(df, meta, out_dir / name, rotation=args.rotation)
        print(f"{meta['station']}  {dt:%Y-%m-%d %H:%M UTC}" if dt else meta["station"])
        print("  Indizes:", {k: round(v, 1) for k, v in idx.items() if isinstance(v, (int, float)) and v is not None})
        print(f"  -> {out_dir / name}")
        return 0

    if args.mode == "archive":
        items = load_archive(arch, hour=args.hour, days=args.days)
        if not items:
            print(f"Kein Archiv unter {arch} (erst per 'harvest' aufbauen).")
            return 1
        for meta, df, _ in items:
            dt = meta["datetime"]
            idx = plot_emagram(df, meta, out_dir / f"payerne_{dt:%Y%m%d_%H}_emagramm.png", rotation=args.rotation)
            print(f"  {dt:%Y-%m-%d %H:%M}  CAPE={idx.get('CAPE_Jkg', float('nan')):.0f}  -> emagramm.png")
        print(f"{len(items)} Emagramme erzeugt in {out_dir}")
        return 0

    if args.mode == "trend":
        items = load_archive(arch, hour=args.hour, days=args.days)
        if not items:
            print(f"Kein Archiv unter {arch} (erst per 'harvest' aufbauen).")
            return 1
        rows = []
        for meta, df, _ in items:
            r = {"datetime": meta["datetime"]}
            r.update(compute_indices(df))
            rows.append(r)
        ts = pd.DataFrame(rows).set_index("datetime")
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"payerne_indices_{args.hour:02d}z.csv"
        ts.to_csv(csv_path)
        print(ts.round(1).to_string())
        print(f"  -> {csv_path}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
