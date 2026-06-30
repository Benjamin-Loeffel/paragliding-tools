"""Klarhimmel-Geländeeinstrahlung G_clear(t,y,x) = Direkt + Diffus + Reflex (mit Schatten)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import ThermalConfig
from .horizon import sun_is_shadowed
from .solar import clearsky, incidence_cos, solar_position, time_axis


@dataclass
class IrradianceCube:
    times: pd.DatetimeIndex
    G: np.ndarray            # [nt,ny,nx] W/m^2 (gesamt auf der geneigten Fläche)
    ghi: np.ndarray          # [nt] Klarhimmel-Skalare
    dni: np.ndarray
    dhi: np.ndarray
    elevation: np.ndarray    # [nt] Sonnenhöhe (deg)


def compute_clearsky_irradiance(cfg: ThermalConfig, terrain, horizon, azimuths,
                                svf: np.ndarray, lat: float, lon: float, alt: float,
                                atten=None) -> IrradianceCube:
    """Gelände-Einstrahlung G(t,y,x). Ohne atten: Klarhimmel. Mit atten (CloudAttenuation):
    real (bewölkt) — Direktstrahl × f_dir, Diffus × f_dif, Reflex × f_ghi."""
    times = time_axis(cfg)
    solpos = solar_position(times, lat, lon, alt)
    cs = clearsky(times, solpos, lat, lon, alt, cfg.linke_turbidity)

    ny, nx = terrain.slope.shape
    nt = len(times)
    if atten is not None and len(atten.times) != nt:
        raise ValueError("Dämpfungs-Cube passt nicht zur Zeitachse")
    G = np.zeros((nt, ny, nx), dtype=np.float32)
    zen = solpos["apparent_zenith"].to_numpy()
    azi = solpos["azimuth"].to_numpy()
    elev = solpos["elevation"].to_numpy()
    dni = cs["dni"].to_numpy()
    dhi = cs["dhi"].to_numpy()
    ghi = cs["ghi"].to_numpy()

    for i in range(nt):
        if elev[i] <= 0:
            continue   # Nacht
        cosi = incidence_cos(zen[i], azi[i], terrain.slope, terrain.aspect)
        lit = ~sun_is_shadowed(horizon, azimuths, np.radians(azi[i]), np.radians(elev[i]))
        beam = dni[i] * cosi * lit
        diffuse = dhi[i] * svf
        reflect = cfg.ground_albedo_reflect * ghi[i] * (1.0 - svf)
        if atten is not None:
            beam = beam * atten.f_dir[i]
            diffuse = diffuse * atten.f_dif[i]
            reflect = reflect * atten.f_ghi[i]
        G[i] = (beam + diffuse + reflect).astype(np.float32)
    return IrradianceCube(times=times, G=G, ghi=ghi, dni=dni, dhi=dhi, elevation=elev)
