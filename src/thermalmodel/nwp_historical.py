"""Historisches Wetter für die RETROSPEKTIVE Prognose-Validierung (vergangene Flugtage).

Zwei Open-Meteo-Endpunkte (JSON, kein Auth):
  - Vertikalprofil + Wind + CAPE: historical-forecast-api (models=icon_seamless), Druckniveaus
    1000..700 hPa (ab ~2024 belastbar). Dewpoint aus T+RH (MetPy). → df im meteo-Format für
    boundarylayer.analyze_sounding (ersetzt die Payerne-Sondierung als Sondierungs-Äquivalent).
  - Strahlung/Bewölkung: archive-api (ERA5-Reanalyse), shortwave/direct/diffuse_radiation, cloud_cover.

Wissenschaftlich: reale Strahlung (Reanalyse) + Analyse-Profil = „perfekte Prognose"/Vorhersagbarkeits-
Obergrenze — beantwortet „hätte das Modell den guten Tag erkannt?", ohne Prognosefehler einzumischen.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import requests

log = logging.getLogger(__name__)
HFA = "https://historical-forecast-api.open-meteo.com/v1/forecast"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
UA = {"User-Agent": "Mozilla/5.0 (thermalmodel research)"}
LEVELS = (1000, 925, 900, 850, 800, 700)


def _get(url, params, cache):
    if cache and Path(cache).exists():
        return json.loads(Path(cache).read_text(encoding="utf-8"))
    r = requests.get(url, params=params, headers=UA, timeout=60)
    r.raise_for_status()
    data = r.json()
    if cache:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_text(json.dumps(data), encoding="utf-8")
    return data


def historical_sounding(date, lat, lon, hour=12, cache_dir=None):
    """Sondierungs-Äquivalent (df im meteo-Format) am gegebenen Tag/Stunde (icon_seamless-Profil)."""
    import metpy.calc as mpcalc
    from metpy.units import units
    hourly = []
    for L in LEVELS:
        hourly += [f"temperature_{L}hPa", f"relative_humidity_{L}hPa",
                   f"wind_speed_{L}hPa", f"wind_direction_{L}hPa", f"geopotential_height_{L}hPa"]
    cache = Path(cache_dir) / "thermal" / f"hist_prof_{date}.json" if cache_dir else None
    data = _get(HFA, {"latitude": lat, "longitude": lon, "start_date": date, "end_date": date,
                      "hourly": ",".join(hourly + ["cape"]), "models": "icon_seamless",
                      "timezone": "Europe/Zurich"}, cache)
    h = data["hourly"]; t = h["time"]
    key = f"{date}T{hour:02d}:00"
    i = t.index(key) if key in t else min(hour, len(t) - 1)
    rows = []
    for L in LEVELS:
        T = h[f"temperature_{L}hPa"][i]; RH = h[f"relative_humidity_{L}hPa"][i]
        gh = h[f"geopotential_height_{L}hPa"][i]
        if T is None or gh is None:
            continue
        Td = float(mpcalc.dewpoint_from_relative_humidity(
            T * units.degC, max(RH or 1.0, 1.0) / 100.0 * units.dimensionless).to("degC").m)
        rows.append({"pressure": float(L), "temperature": float(T), "dewpoint": Td,
                     "height": float(gh),
                     "wind_dir": float(h[f"wind_direction_{L}hPa"][i] or 0.0),
                     "wind_speed": float(h[f"wind_speed_{L}hPa"][i] or 0.0) / 3.6})
    df = pd.DataFrame(rows).dropna(subset=["pressure", "temperature", "height"])
    cape = h.get("cape", [None])[i]
    return df, (float(cape) if cape is not None else float("nan"))


def historical_radiation(date, lat, lon, cache_dir=None):
    """ERA5-Strahlung/Bewölkung (stündlich, lokal) → (times, G[W/m²], cloud[%])."""
    cache = Path(cache_dir) / "thermal" / f"hist_rad_{date}.json" if cache_dir else None
    data = _get(ARCHIVE, {"latitude": lat, "longitude": lon, "start_date": date, "end_date": date,
                          "hourly": "shortwave_radiation,cloud_cover,direct_radiation,diffuse_radiation",
                          "timezone": "Europe/Zurich"}, cache)
    h = data["hourly"]
    times = pd.to_datetime(h["time"]).tz_localize("Europe/Zurich")
    g = np.array([x if x is not None else 0.0 for x in h["shortwave_radiation"]], dtype=float)
    cloud = np.array([x if x is not None else np.nan for x in h["cloud_cover"]], dtype=float)
    return times, g, cloud
