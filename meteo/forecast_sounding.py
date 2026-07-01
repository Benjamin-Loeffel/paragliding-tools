"""Prognose-Sondierung (Vertikalprofil) aus ICON-Druckflächen (Open-Meteo) für einen kommenden Tag.

Ermöglicht Thermik-Prognosen für Tage OHNE echte Payerne-Sondierung: liefert ein Profil im selben
DataFrame-Format wie `radiosonde_payerne.parse_vzus01` (Spalten: pressure, height, temperature,
dewpoint, wind_dir, wind_speed) → füttert direkt `radiosonde_payerne.compute_indices`/`plot_emagram`
UND `thermalmodel.boundarylayer.analyze_sounding` (z_i/w*/Ceiling für den Prognosetag).

Modell: `icon_seamless` (ICON-CH1/D2/EU; hat Druckflächen, GRIB-frei via Open-Meteo). Taupunkt aus
Temperatur + relativer Feuchte (Magnus). Unterirdische Niveaus (Druck > Bodendruck) werden verworfen,
damit der bodennahe Parzellenaufstieg physikalisch startet.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import requests

log = logging.getLogger(__name__)
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

# Druckflächen (hPa) — Boden bis ~9 km; reicht für CBL/Thermik weit über die Ceiling hinaus.
LEVELS = [1000, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300]


def _dewpoint(t_c: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    """Taupunkt [°C] aus Temperatur [°C] + rel. Feuchte [%] (Magnus)."""
    rh = np.clip(rh_pct, 1.0, 100.0) / 100.0
    a, b = 17.625, 243.04
    g = np.log(rh) + a * t_c / (b + t_c)
    return b * g / (a - g)


def _hourly(data: dict, key: str) -> np.ndarray:
    v = data.get("hourly", {}).get(key)
    return np.array([np.nan if x is None else float(x) for x in v], dtype=float) if v else None


def fetch_forecast_profile(lat: float, lon: float, date: str, hour: int = 13,
                           tz: str = "Europe/Zurich", cache_dir: str | Path = "cache",
                           model: str = "icon_seamless",
                           session: requests.Session | None = None) -> tuple[dict, pd.DataFrame]:
    """ICON-Prognose-Vertikalprofil am Punkt (lat,lon) für `date` zur Stunde `hour` (Lokalzeit).
    -> (meta, df) mit df-Spalten pressure/height/temperature/dewpoint/wind_dir/wind_speed."""
    cache = Path(cache_dir) / "flightday" / f"profile_{model}_{date}_{lat:.3f}_{lon:.3f}.json"
    hourly = []
    for L in LEVELS:
        hourly += [f"temperature_{L}hPa", f"relative_humidity_{L}hPa", f"geopotential_height_{L}hPa",
                   f"wind_speed_{L}hPa", f"wind_direction_{L}hPa"]
    hourly += ["surface_pressure"]
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        log.info("Prognose-Profil aus Cache: %s", cache.name)
    else:
        body = {"latitude": [round(lat, 4)], "longitude": [round(lon, 4)], "hourly": hourly,
                "models": [model], "timezone": [tz], "start_date": [date], "end_date": [date]}
        r = (session or requests).post(OPEN_METEO, json=body, timeout=90)
        r.raise_for_status()
        data = r.json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
        log.info("Prognose-Profil geladen (%s, %s, %.3f/%.3f)", model, date, lat, lon)
    data = data[0] if isinstance(data, list) else data

    times = pd.to_datetime(data["hourly"]["time"])
    idx = int(np.argmin(np.abs((times.hour + times.minute / 60.0) - hour)))
    sp = _hourly(data, "surface_pressure")
    p_surf = float(sp[idx]) if sp is not None and np.isfinite(sp[idx]) else 1013.0

    rows = []
    for L in LEVELS:
        if L > p_surf + 5:               # unterirdisch → verwerfen
            continue
        T = _hourly(data, f"temperature_{L}hPa"); H = _hourly(data, f"geopotential_height_{L}hPa")
        RH = _hourly(data, f"relative_humidity_{L}hPa")
        WS = _hourly(data, f"wind_speed_{L}hPa"); WD = _hourly(data, f"wind_direction_{L}hPa")
        if T is None or H is None or not np.isfinite(T[idx]) or not np.isfinite(H[idx]):
            continue
        rows.append({"pressure": float(L), "height": float(H[idx]), "temperature": float(T[idx]),
                     "dewpoint": float(_dewpoint(T[idx], RH[idx] if RH is not None else 50.0)),
                     "wind_dir": float(WD[idx]) if WD is not None else np.nan,
                     "wind_speed": (float(WS[idx]) / 3.6 if WS is not None else np.nan)})  # km/h→m/s
    df = pd.DataFrame(rows).dropna(subset=["pressure", "temperature"]).sort_values(
        "pressure", ascending=False).reset_index(drop=True)
    meta = {"station": f"ICON-Prognose {model}", "datetime": times[idx].to_pydatetime(),
            "lat": lat, "lon": lon, "forecast": True, "surface_pressure_hPa": p_surf}
    return meta, df
