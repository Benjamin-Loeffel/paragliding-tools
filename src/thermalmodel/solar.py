"""Sonnenstand, Klarhimmel-Einstrahlung (pvlib) und Gelände-Einfallswinkel."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pvlib

from .config import ThermalConfig


def time_axis(cfg: ThermalConfig) -> pd.DatetimeIndex:
    """Lokale Zeitachse für den Modelltag (tz-aware)."""
    start = pd.Timestamp(f"{cfg.date} {cfg.t_start_hour:02d}:00", tz=cfg.timezone)
    end = pd.Timestamp(f"{cfg.date} {cfg.t_end_hour:02d}:00", tz=cfg.timezone)
    return pd.date_range(start, end, freq=f"{cfg.t_step_min}min")


def solar_position(times: pd.DatetimeIndex, lat: float, lon: float, alt: float) -> pd.DataFrame:
    loc = pvlib.location.Location(lat, lon, tz=str(times.tz), altitude=alt)
    return loc.get_solarposition(times)   # apparent_zenith, azimuth, elevation, ...


def clearsky(times: pd.DatetimeIndex, solpos: pd.DataFrame, lat: float, lon: float,
             alt: float, linke: float | None = None) -> pd.DataFrame:
    airmass = pvlib.atmosphere.get_relative_airmass(solpos["apparent_zenith"])
    airmass_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pvlib.atmosphere.alt2pres(alt))
    if linke is None:
        linke = pvlib.clearsky.lookup_linke_turbidity(times, lat, lon)
    return pvlib.clearsky.ineichen(solpos["apparent_zenith"], airmass_abs, linke, altitude=alt)


def incidence_cos(zenith_deg: float, azimuth_deg: float,
                  slope_rad: np.ndarray, aspect_rad: np.ndarray) -> np.ndarray:
    """cos(Einfallswinkel) auf geneigte Flächen, geclippt >=0.
    aspect/azimuth: 0=N, im Uhrzeigersinn (gleiche Konvention)."""
    thz = np.radians(zenith_deg)
    tha = np.radians(azimuth_deg)
    cosi = (np.cos(thz) * np.cos(slope_rad)
            + np.sin(thz) * np.sin(slope_rad) * np.cos(tha - aspect_rad))
    return np.clip(cosi, 0.0, None)
