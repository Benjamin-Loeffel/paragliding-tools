"""Synoptische Zusatzdaten fürs Flugtag-Briefing (Frutigen / Berner Oberland).

Ergänzt die thermalmodel-/Sondierungs-Deliverables um die **synoptischen** Checkpunkte der
SHV-Meteo-Entscheidungsstrategie, die das Geländemodell nicht selbst abdeckt:

  1) überregionaler / Höhenwind + Böen        (Druckflächen-Wind, Böigkeit)
  2) Föhn / Bise                              (Druckdifferenz N–S bzw. W–E aus pressure_msl)
  4) Wärmegewitter / Konvektion               (CAPE/CIN, Niederschlag, weather_code 95–99)
  5) Fronten                                  (grossräumiger Niederschlag + Zuzug aus West)

Datenquelle: **Open-Meteo** (`meteoswiss_icon_ch1`, GRIB-frei als JSON, kein API-Key), Multi-Punkt
(bis 1000 Punkte/Request) → ein Call liefert das **CH-weite Grid** und den **Frutigen-Radius**.
Muster (Fetch + JSON-Tages-Cache) übernommen von `thermalmodel/nwp.py` + `wind.py`.

Der Druck-Gradient (Föhn/Bise) wird aus der Modell-`pressure_msl` an bewährten Stationspaaren
gebildet (Lugano↔Zürich für N–S-Föhn, Genf↔St. Gallen für W–E-Bise) — als *Prognose*-Indikator über
den Tag. Die beobachteten MeteoSchweiz-QFF-Stationswerte sind ein optionales späteres Upgrade.

**Grundsatz:** Dieses Modul ENTSCHEIDET NICHT. Es liefert je Phänomen `{wert, schwelle, ampel,
begruendung}` (Ampel ∈ günstig|achtung|alarm) für ein reproduzierbares, immer gleiches Briefing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import requests

log = logging.getLogger(__name__)

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

# --- Fluggebiet + Betrachtungsregionen --------------------------------------
FRUTIGEN_LAT, FRUTIGEN_LON = 46.588, 7.647       # Frutigen (Berner Oberland)
FRUTIGEN_RADIUS_DEG = 0.22                        # ~ ±24 km (Niederschlag/Gewitter-Umkreis)
FRUTIGEN_RADIUS_N = 5                             # 5×5-Punktraster im Umkreis
CH_BBOX = (45.80, 47.85, 5.95, 10.55)             # (lat_min, lat_max, lon_min, lon_max)
CH_GRID_STEP_DEG = 0.20                           # ~15–22 km Punktabstand (≈ 250 Punkte über CH)

# Stationspaare für die Druckdifferenz (Föhn/Bise) — klassische Alpen-Nord/Süd bzw. West/Ost-Achse.
# (lat, lon) der Modellabfrage; kein Stationscode nötig, da pressure_msl aus dem Modell.
FOEHN_SOUTH = (46.00, 8.96)     # Lugano (Alpensüdseite)
FOEHN_NORTH = (47.48, 8.54)     # Zürich/Kloten (Alpennordseite)
BISE_WEST = (46.25, 6.13)       # Genève (Südwest-Plateau)
BISE_EAST = (47.48, 9.63)       # St. Gallen (Nordost-Plateau)

# --- Schwellen (fix — „immer gleich"; Quellen: SHV-Plakat + Recherche) -------
WIND_UPPER_KMH = (25.0, 35.0)   # Höhenwind 2000–3000 m: >25 achtung, >35 alarm
GUST_RATIO = (1.6, 2.0)         # Böen/Mittel: >1.6 achtung, >2.0 alarm (turbulent)
FOEHN_DP_HPA = (4.0, 8.0)       # |Δp(N–S)|: ≥4 Föhn bricht durch, ≥8 bis ins Flachland
BISE_DP_HPA = (2.0, 5.0)        # Δp(W–E): >2 & zunehmend achtung (Plakat), >5 alarm
CAPE_JKG = (1000.0, 2500.0)     # >1000 Gewitter wahrscheinlich, >2500 schwer
PRECIP_MMH = (0.3, 2.0)         # Tages-Spitze mm/h im Umkreis: >0.3 achtung, >2 alarm
THUNDER_CODES = {95, 96, 97, 98, 99}   # WMO weather_code Gewitter
SHOWER_CODES = {80, 81, 82}            # Schauer

AMPEL = ("günstig", "achtung", "alarm")


def ampel(value: float, thr: tuple[float, float], higher_is_worse: bool = True) -> str:
    """Wert → Ampel anhand zweier Schwellen (achtung, alarm)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "n/a"
    lo, hi = thr
    if higher_is_worse:
        return AMPEL[2] if value >= hi else AMPEL[1] if value >= lo else AMPEL[0]
    return AMPEL[2] if value <= hi else AMPEL[1] if value <= lo else AMPEL[0]


# --- Punktraster ------------------------------------------------------------
def frutigen_radius_grid() -> tuple[np.ndarray, np.ndarray]:
    d = FRUTIGEN_RADIUS_DEG
    lats = np.linspace(FRUTIGEN_LAT - d, FRUTIGEN_LAT + d, FRUTIGEN_RADIUS_N)
    lons = np.linspace(FRUTIGEN_LON - d, FRUTIGEN_LON + d, FRUTIGEN_RADIUS_N)
    La, Lo = np.meshgrid(lats, lons, indexing="ij")
    return La.ravel(), Lo.ravel()


def ch_grid() -> tuple[np.ndarray, np.ndarray]:
    la0, la1, lo0, lo1 = CH_BBOX
    lats = np.arange(la0, la1 + 1e-9, CH_GRID_STEP_DEG)
    lons = np.arange(lo0, lo1 + 1e-9, CH_GRID_STEP_DEG)
    La, Lo = np.meshgrid(lats, lons, indexing="ij")
    return La.ravel(), Lo.ravel(), lats, lons


# --- Open-Meteo Multi-Punkt-Fetch (gecacht je Tag/Region) -------------------
# Oberflächen-/Konvektionsfelder — Modell meteoswiss_icon_ch1 (hat KEINE Druckflächen).
HOURLY_VARS = [
    "precipitation", "showers", "weather_code", "precipitation_probability",
    "cape", "convective_inhibition", "cloud_cover", "cloud_cover_low",
    "pressure_msl", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
    "freezing_level_height",
]
# Schlankes Set fürs CH-weite Grid (Karten + Front-Bewertung). shortwave_radiation = Sonneneinstrahlung.
CH_VARS = ["precipitation", "weather_code", "cape", "cloud_cover", "shortwave_radiation",
           "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]
# Druckflächen-Winde (überregionaler/Höhenwind) — Modell icon_seamless (ICON-CH1/D2/EU), wie im Repo.
UPPER_MODEL = "icon_seamless"
UPPER_VARS = ["wind_speed_850hPa", "wind_direction_850hPa", "wind_speed_700hPa",
              "wind_direction_700hPa", "wind_speed_500hPa", "wind_direction_500hPa"]


def _hourly(loc: dict, key: str, nh: int) -> np.ndarray:
    vals = loc.get("hourly", {}).get(key)
    if not vals:
        return np.full(nh, np.nan)
    return np.array([np.nan if v is None else float(v) for v in vals], dtype=float)


def fetch_openmeteo(lats, lons, date: str, tz: str, cache_dir: Path, tag: str,
                    variables: list[str] | None = None,
                    model: str = "meteoswiss_icon_ch1",
                    session: requests.Session | None = None) -> dict:
    """Open-Meteo-Multi-Punkt-Fetch (POST, damit viele Punkte nicht die URL sprengen).
    Rückgabe: {'times': DatetimeIndex[nh], <var>: array[npts,nh], 'lat':…, 'lon':…}. JSON-Tages-Cache."""
    variables = variables or HOURLY_VARS
    lats = np.asarray(lats, float); lons = np.asarray(lons, float)
    cache = Path(cache_dir) / "flightday" / f"synoptic_{tag}_{model}_{date}_{len(lats)}.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        log.info("Synoptik aus Cache: %s", cache.name)
    else:
        # Open-Meteo-POST verlangt ALLE Parameter als Arrays (auch die Skalare).
        body = {
            "latitude": [round(float(v), 4) for v in lats],
            "longitude": [round(float(v), 4) for v in lons],
            "hourly": variables, "models": [model], "timezone": [tz],
            "start_date": [date], "end_date": [date],
        }
        r = (session or requests).post(OPEN_METEO, json=body, timeout=120)
        r.raise_for_status()
        data = r.json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
        log.info("Synoptik geladen (%s, %s, %d Punkte)", model, tag, len(lats))

    locs = data if isinstance(data, list) else [data]
    times = pd.to_datetime(locs[0]["hourly"]["time"])
    nh = len(times)
    out = {"times": times, "lat": lats, "lon": lons}
    for v in variables:
        out[v] = np.vstack([_hourly(l, v, nh) for l in locs])   # [npts, nh]
    return out


def _pressure_msl_point(lat, lon, date, tz, cache_dir, session) -> np.ndarray:
    d = fetch_openmeteo([lat], [lon], date, tz, cache_dir, tag=f"p_{lat:.2f}_{lon:.2f}",
                        variables=["pressure_msl"], session=session)
    return d["pressure_msl"][0], d["times"]


# --- Kernabruf: alles fürs Briefing -----------------------------------------
@dataclass
class Synoptic:
    date: str
    times: pd.DatetimeIndex
    frutigen: dict          # HOURLY_VARS als [npts,nh] im Frutigen-Radius
    ch: dict                # HOURLY_VARS als [npts,nh] CH-weit
    ch_lats: np.ndarray
    ch_lons: np.ndarray
    dp_ns: np.ndarray       # Δp(Süd−Nord) [nh] hPa  (>0 → Südföhn-Tendenz)
    dp_we: np.ndarray       # Δp(West−Ost) [nh] hPa  (>0 → Bise-Tendenz)
    assessments: dict = field(default_factory=dict)


def fetch_synoptic(date: str, tz: str = "Europe/Zurich", cache_dir: str | Path = "cache",
                   session: requests.Session | None = None) -> Synoptic:
    cache_dir = Path(cache_dir)
    sess = session or requests.Session()
    fla, flo = frutigen_radius_grid()
    frutigen = fetch_openmeteo(fla, flo, date, tz, cache_dir, tag="frutigen", session=sess)
    # Druckflächen-Winde separat (icon_seamless) und in die Frutigen-/CH-Dicts mergen.
    fup = fetch_openmeteo(fla, flo, date, tz, cache_dir, tag="frutigen_upper",
                          variables=UPPER_VARS, model=UPPER_MODEL, session=sess)
    for v in UPPER_VARS:
        frutigen[v] = fup[v]
    cla, clo, ch_lats, ch_lons = ch_grid()
    ch = fetch_openmeteo(cla, clo, date, tz, cache_dir, tag="ch", variables=CH_VARS, session=sess)
    cup = fetch_openmeteo(cla, clo, date, tz, cache_dir, tag="ch_upper",
                          variables=UPPER_VARS, model=UPPER_MODEL, session=sess)
    for v in UPPER_VARS:
        ch[v] = cup[v]

    # Druckdifferenzen aus pressure_msl an den Stationspaaren
    p_s, _ = _pressure_msl_point(*FOEHN_SOUTH, date, tz, cache_dir, sess)
    p_n, _ = _pressure_msl_point(*FOEHN_NORTH, date, tz, cache_dir, sess)
    p_w, _ = _pressure_msl_point(*BISE_WEST, date, tz, cache_dir, sess)
    p_e, _ = _pressure_msl_point(*BISE_EAST, date, tz, cache_dir, sess)
    dp_ns = p_s - p_n       # Südüberdruck → Südföhn
    dp_we = p_w - p_e       # Westüberdruck → Bise (NE-Wind Plateau)

    syn = Synoptic(date=date, times=frutigen["times"], frutigen=frutigen, ch=ch,
                   ch_lats=ch_lats, ch_lons=ch_lons, dp_ns=dp_ns, dp_we=dp_we)
    syn.assessments = assess_all(syn)
    return syn


# --- Bewertungen je Phänomen ------------------------------------------------
def _daymax(arr2d: np.ndarray) -> float:
    """Max über Punkte & Tag (nanmax)."""
    return float(np.nanmax(arr2d)) if np.isfinite(arr2d).any() else float("nan")


def _radius_series(frut: dict, key: str, reducer=np.nanmax) -> np.ndarray:
    """Reduziere den Radius-Punktesatz je Zeitschritt → [nh] (Default: Maximum im Umkreis)."""
    return reducer(frut[key], axis=0)


def assess_wind(syn: Synoptic) -> dict:
    frut = syn.frutigen
    upper = _radius_series(frut, "wind_speed_700hPa")            # ~3000 m, km/h (Open-Meteo)
    up_max = float(np.nanmax(upper)) if np.isfinite(upper).any() else float("nan")
    g = _radius_series(frut, "wind_gusts_10m"); m = _radius_series(frut, "wind_speed_10m")
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.nanmax(g / np.maximum(m, 1.0))
    a = ampel(up_max, WIND_UPPER_KMH)
    return {"phaenomen": "1 Überregionaler/Höhenwind",
            "hoehenwind_700hPa_max_kmh": round(up_max, 1),
            "boeen_verhaeltnis_max": round(float(ratio), 2),
            "schwelle": f"Höhenwind >{WIND_UPPER_KMH[0]:.0f}/{WIND_UPPER_KMH[1]:.0f} km/h",
            "ampel": a,
            "begruendung": f"max. 700-hPa-Wind {up_max:.0f} km/h; Böen/Mittel bis {ratio:.1f}×."}


def assess_foehn(syn: Synoptic) -> dict:
    dp = syn.dp_ns
    dp_max = float(np.nanmax(np.abs(dp))) if np.isfinite(dp).any() else float("nan")
    a = ampel(dp_max, FOEHN_DP_HPA)
    richtung = "Süd" if np.nanmean(dp) > 0 else "Nord"
    return {"phaenomen": "2 Föhn",
            "dp_nord_sued_max_hPa": round(dp_max, 1), "tendenz": richtung,
            "schwelle": f"Δp(N–S) ≥{FOEHN_DP_HPA[0]:.0f} durchbrechend / ≥{FOEHN_DP_HPA[1]:.0f} bis Flachland",
            "ampel": a,
            "begruendung": f"Δp(S−N) max {dp_max:.1f} hPa ({richtung}überdruck). "
                           f"≥8 hPa → Föhn bis ins Flachland; Live-Föhnzeichen (Föhnmauer/Linsen) vor Ort prüfen."}


def assess_bise(syn: Synoptic) -> dict:
    dp = syn.dp_we
    dp_max = float(np.nanmax(dp)) if np.isfinite(dp).any() else float("nan")
    a = ampel(dp_max, BISE_DP_HPA)
    return {"phaenomen": "1 Bise (W–E-Gradient)",
            "dp_west_ost_max_hPa": round(dp_max, 1),
            "schwelle": f"Δp(W−E) >{BISE_DP_HPA[0]:.0f} & zunehmend achtung / >{BISE_DP_HPA[1]:.0f} alarm",
            "ampel": a,
            "begruendung": f"Δp(W−O) max {dp_max:.1f} hPa. Positiv & zunehmend → Bise (NE, kann bodennah stark/böig)."}


def assess_convection(syn: Synoptic, lapse_c_per_100m: float | None = None,
                      cloud_base_amsl: float | None = None) -> dict:
    frut = syn.frutigen
    cape_max = _daymax(frut["cape"])
    precip_max = _daymax(frut["precipitation"])
    wc = frut["weather_code"]
    thunder = bool(np.isin(wc, list(THUNDER_CODES)).any())
    # Ampel = strengste der Einzelbewertungen
    parts = [ampel(cape_max, CAPE_JKG), ampel(precip_max, PRECIP_MMH)]
    if thunder:
        parts.append("alarm")
    if lapse_c_per_100m is not None and lapse_c_per_100m <= -0.8:
        parts.append("alarm")     # Plakat: ≥ −0.8 °C/100 m = gefährlich labil
    a = AMPEL[max(AMPEL.index(p) for p in parts if p in AMPEL)] if any(p in AMPEL for p in parts) else "n/a"
    return {"phaenomen": "4 Wärmegewitter / Luftschichtung",
            "cape_max_Jkg": round(cape_max, 0), "niederschlag_max_mmh": round(precip_max, 2),
            "gewitter_code_im_umkreis": thunder,
            "lapse_flughoehe_C_100m": None if lapse_c_per_100m is None else round(lapse_c_per_100m, 2),
            "wolkenbasis_amsl_m": None if cloud_base_amsl is None else round(cloud_base_amsl),
            "schwelle": f"CAPE >{CAPE_JKG[0]:.0f}/{CAPE_JKG[1]:.0f} J/kg · Labilität ≥ −0.8 °C/100 m",
            "ampel": a,
            "begruendung": f"CAPE max {cape_max:.0f} J/kg, Niederschlag bis {precip_max:.1f} mm/h, "
                           f"Gewitter-Code im Umkreis: {'ja' if thunder else 'nein'}. "
                           f"'Sehr gute Thermik' kann auf Turbulenz/Überentwicklung hinweisen."}


def assess_fronts(syn: Synoptic) -> dict:
    """Grossräumiger Niederschlag CH-weit + Zuzug aus West (untere Modellhälfte der Längen)."""
    ch = syn.ch
    lons = syn.ch_lons
    lon_med = np.median(lons)
    # Punkte westlich der Domänenmitte
    west_mask = syn.ch["lon"] < lon_med
    precip_ch_max = _daymax(ch["precipitation"])
    precip_west_max = _daymax(ch["precipitation"][west_mask]) if west_mask.any() else float("nan")
    wc_thunder = bool(np.isin(ch["weather_code"], list(THUNDER_CODES)).any())
    a = ampel(max(precip_ch_max, 0.0), PRECIP_MMH)
    if precip_west_max >= PRECIP_MMH[1]:
        a = "alarm"
    return {"phaenomen": "5 Fronten",
            "niederschlag_CH_max_mmh": round(precip_ch_max, 2),
            "niederschlag_West_max_mmh": round(precip_west_max, 2),
            "gewitter_CH": wc_thunder,
            "schwelle": "organisierter Niederschlag / Zuzug aus West",
            "ampel": a,
            "begruendung": f"CH-weit max {precip_ch_max:.1f} mm/h (West {precip_west_max:.1f}). "
                           f"Front-/Niederschlagszuzug aus W am Live-Radar bestätigen (Pilot-Check)."}


def assess_all(syn: Synoptic, lapse_c_per_100m: float | None = None,
               cloud_base_amsl: float | None = None) -> dict:
    return {
        "wind": assess_wind(syn),
        "bise": assess_bise(syn),
        "foehn": assess_foehn(syn),
        "konvektion": assess_convection(syn, lapse_c_per_100m, cloud_base_amsl),
        "fronten": assess_fronts(syn),
    }
