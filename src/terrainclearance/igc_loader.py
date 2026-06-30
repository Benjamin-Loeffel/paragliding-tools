"""IGC-Dateien einlesen und zu einem ``FlightTrack`` mit numpy-Arrays normalisieren.

Wrappt :mod:`aerofiles`. Wichtig ist die *pro Datei* getroffene Wahl der
Höhenquelle: dedizierte Logger (XC Tracer) liefern GNSS- und Druckhöhe,
Handy-Apps (XCTrack ohne Barosensor) liefern Druckhöhe = 0. Wir bevorzugen die
GNSS-Höhe (``HFALG:GEO`` ⇒ geoid-/MSL-bezogen) und fallen nur wenn nötig auf
die Druckhöhe zurück.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from pathlib import Path

import numpy as np

from aerofiles.igc import Reader

from .config import Config


@dataclass
class FlightTrack:
    name: str
    path: Path
    dt: np.ndarray          # datetime64[s], UTC
    t_s: np.ndarray         # float Sekunden seit erstem Fix
    lat: np.ndarray         # Grad (WGS84)
    lon: np.ndarray         # Grad (WGS84)
    gps_alt: np.ndarray     # m, roh (kann 0 enthalten)
    pressure_alt: np.ndarray  # m, roh
    alt: np.ndarray         # gewählte Höhe (m), VOR Kalibrierung
    alt_source: str         # 'gnss' | 'pressure'
    valid: np.ndarray       # bool, validity == 'A' (3D-Fix)
    header: dict

    @property
    def n(self) -> int:
        return len(self.lat)

    def bbox_wgs84(self) -> tuple[float, float, float, float]:
        """(min_lon, min_lat, max_lon, max_lat)."""
        return (
            float(np.min(self.lon)),
            float(np.min(self.lat)),
            float(np.max(self.lon)),
            float(np.max(self.lat)),
        )


def _is_usable(arr: np.ndarray) -> bool:
    """Heuristik: Höhenfeld ist brauchbar, wenn überwiegend != 0 und variabel."""
    finite = np.isfinite(arr)
    if not finite.any():
        return False
    nonzero_frac = float(np.count_nonzero(arr[finite])) / arr.size
    return nonzero_frac > 0.5 and float(np.nanstd(arr)) > 1.0


def _choose_altitude(gps_alt: np.ndarray, pressure_alt: np.ndarray, mode: str) -> tuple[np.ndarray, str]:
    gps_ok = _is_usable(gps_alt)
    prs_ok = _is_usable(pressure_alt)

    if mode == "gnss":
        if not gps_ok:
            raise ValueError("calibration='gnss' verlangt, aber GNSS-Höhe ist unbrauchbar.")
        return gps_alt, "gnss"
    if mode == "pressure":
        if not prs_ok:
            raise ValueError("calibration='pressure' verlangt, aber Druckhöhe ist unbrauchbar (ISA/0).")
        return pressure_alt, "pressure"

    # mode == 'auto' oder 'none': GNSS bevorzugen (geometrisch/geoid-bezogen)
    if gps_ok:
        return gps_alt, "gnss"
    if prs_ok:
        return pressure_alt, "pressure"
    raise ValueError("Weder GNSS- noch Druckhöhe brauchbar – Datei kann nicht ausgewertet werden.")


def load_igc(path: str | Path, cfg: Config) -> FlightTrack:
    path = Path(path)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = Reader().read(f)

    header = data["header"][1] if data.get("header") else {}
    fixes = data["fix_records"][1]
    if not fixes:
        raise ValueError(f"Keine Fix-Records in {path.name}")

    lat = np.array([fx["lat"] for fx in fixes], dtype=float)
    lon = np.array([fx["lon"] for fx in fixes], dtype=float)
    gps_alt = np.array([fx.get("gps_alt") if fx.get("gps_alt") is not None else np.nan for fx in fixes], dtype=float)
    pressure_alt = np.array([fx.get("pressure_alt") if fx.get("pressure_alt") is not None else np.nan for fx in fixes], dtype=float)
    valid = np.array([fx.get("validity") == "A" for fx in fixes], dtype=bool)

    # Volles UTC-datetime kommt von aerofiles bereits inkl. Datum + tz.
    dt_list = []
    for fx in fixes:
        d = fx["datetime"].astimezone(timezone.utc).replace(tzinfo=None)
        dt_list.append(np.datetime64(d, "s"))
    dt = np.array(dt_list, dtype="datetime64[s]")
    t_s = (dt - dt[0]) / np.timedelta64(1, "s")
    t_s = t_s.astype(float)

    alt, alt_source = _choose_altitude(gps_alt, pressure_alt, cfg.calibration)

    return FlightTrack(
        name=path.stem,
        path=path,
        dt=dt,
        t_s=t_s,
        lat=lat,
        lon=lon,
        gps_alt=gps_alt,
        pressure_alt=pressure_alt,
        alt=alt,
        alt_source=alt_source,
        valid=valid,
        header=header,
    )
