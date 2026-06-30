"""ICON-CH1-Strahlung/Bewölkung via Open-Meteo (MeteoSwiss-Modell) → Dämpfungsfaktoren.

Holt die echten (bewölkten) Bodenstrahlungs-Komponenten von Open-Meteo
(models=meteoswiss_icon_ch1, GRIB-frei als JSON, bereits in Lokalzeit) an einem
groben Stützpunkt-Raster über der Domäne und bildet daraus zeitlich aufgelöste,
grob ortsabhängige Faktoren relativ zur pvlib-Klarhimmel-Referenz:

  f_dir = direkte_real / direkte_klar      → dämpft den Direktstrahl (clip 0..1.2)
  f_dif = diffuse_real / diffus_klar       → Diffusanteil (Wolken können >1 streuen)
  f_ghi = global_real / global_klar        → für den Reflexanteil

So wird bei Bewölkung der Direktanteil stärker reduziert als der Diffusanteil
(physikalisch gewünscht). ICON-CH1 ist ~1 km; über die 8×10-km-Domäne ist τ(t)
v. a. zeitlich, räumlich nur grob — daher reicht ein Stützpunkt-Raster + Interpolation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.interpolate import RegularGridInterpolator, interp1d

from .config import ThermalConfig
from .grids import Grid
from .reproject import lv95_to_wgs84
from .solar import clearsky, solar_position, time_axis

log = logging.getLogger(__name__)
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


@dataclass
class CloudAttenuation:
    times: pd.DatetimeIndex   # = Modell-Zeitachse
    f_dir: np.ndarray         # [nt,ny,nx] Direktstrahl-Überlebensanteil (0..1.2)
    f_dif: np.ndarray         # [nt,ny,nx] Diffusfaktor (>=0, kann >1)
    f_ghi: np.ndarray         # [nt,ny,nx] Globalfaktor (0..1.2)
    cloud: np.ndarray         # [nt,ny,nx] Gesamtbewölkung %
    pts_lonlat: np.ndarray    # [npts,2] abgefragte Stützpunkte
    source: str

    @property
    def mean_cloud(self) -> np.ndarray:        # [nt] Domänenmittel Bewölkung %
        return np.nanmean(self.cloud.reshape(len(self.times), -1), axis=1)

    @property
    def mean_f_dir(self) -> np.ndarray:        # [nt] Domänenmittel Direktdämpfung
        return np.nanmean(self.f_dir.reshape(len(self.times), -1), axis=1)


def _hourly_array(loc: dict, key: str) -> np.ndarray:
    return np.array([np.nan if v is None else float(v) for v in loc["hourly"][key]], dtype=float)


def fetch_cloud_attenuation(cfg: ThermalConfig, grid: Grid, lat0: float, lon0: float, alt: float,
                            session: requests.Session | None = None) -> CloudAttenuation:
    """ICON-CH1-Dämpfungsfaktoren auf das Modellgitter (gecacht je Tag/Stützpunktzahl)."""
    n_e, n_n = cfg.nwp_points
    w, s, e, n = grid.bounds()
    es = np.linspace(w, e, n_e)
    ns = np.linspace(s, n, n_n)
    Eg, Ng = np.meshgrid(es, ns)                       # (n_n, n_e)
    lon, lat = lv95_to_wgs84(Eg.ravel(), Ng.ravel())   # je [npts]

    cache = Path(cfg.cache_dir) / "thermal" / f"openmeteo_{cfg.date}_{n_e}x{n_n}.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        log.info("ICON/Open-Meteo aus Cache: %s", cache.name)
    else:
        params = {
            "latitude": ",".join(f"{v:.4f}" for v in lat),
            "longitude": ",".join(f"{v:.4f}" for v in lon),
            "hourly": "shortwave_radiation,direct_radiation,diffuse_radiation,cloud_cover",
            "models": cfg.nwp_model,
            "timezone": cfg.timezone,
            "start_date": cfg.date, "end_date": cfg.date,
        }
        r = (session or requests).get(OPEN_METEO, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
        log.info("ICON/Open-Meteo geladen (%s, %d Stützpunkte)", cfg.nwp_model, len(lat))

    locs = data if isinstance(data, list) else [data]
    if len(locs) != len(lat):
        log.warning("Open-Meteo lieferte %d statt %d Stützpunkte", len(locs), len(lat))

    # Stündliche ICON-Werte je Stützpunkt: [npts, nh]
    htimes = pd.to_datetime(locs[0]["hourly"]["time"]).tz_localize(cfg.timezone)
    nh = len(htimes)
    B = np.vstack([_hourly_array(l, "direct_radiation") for l in locs])
    D = np.vstack([_hourly_array(l, "diffuse_radiation") for l in locs])
    G = np.vstack([_hourly_array(l, "shortwave_radiation") for l in locs])
    C = np.vstack([_hourly_array(l, "cloud_cover") for l in locs])
    np.nan_to_num(B, copy=False); np.nan_to_num(D, copy=False); np.nan_to_num(G, copy=False)

    # Klarhimmel-Referenz (Domänenzentrum) an denselben stündlichen Zeitpunkten
    solpos = solar_position(htimes, lat0, lon0, alt)
    cs = clearsky(htimes, solpos, lat0, lon0, alt, cfg.linke_turbidity)
    zen = solpos["apparent_zenith"].to_numpy()
    dni_c, dhi_c, ghi_c = cs["dni"].to_numpy(), cs["dhi"].to_numpy(), cs["ghi"].to_numpy()
    b_clear = dni_c * np.clip(np.cos(np.radians(zen)), 0.0, None)   # direkt auf Horizontale

    eps = 1.0
    f_dir = np.clip(B / np.maximum(b_clear[None, :], eps), 0.0, 1.2)
    f_dif = np.clip(D / np.maximum(dhi_c[None, :], eps), 0.0, 3.0)
    f_ghi = np.clip(G / np.maximum(ghi_c[None, :], eps), 0.0, 1.2)
    night = ghi_c < 5.0                       # nachts Faktoren neutral (Strahl ohnehin 0)
    f_dir[:, night] = 1.0; f_dif[:, night] = 1.0; f_ghi[:, night] = 1.0

    # 1) räumlich vom Stützpunkt-Raster aufs Modellgitter (regulär -> RegularGridInterpolator)
    Ec, Nc = grid.cell_centers()
    qpts = np.column_stack([Nc.ravel(), Ec.ravel()])     # Reihenfolge (N, E) wie (ns, es)

    def to_grid_hourly(field_pts):                       # [npts,nh] -> [ny,nx,nh]
        vals = field_pts.reshape(n_n, n_e, nh)
        ip = RegularGridInterpolator((ns, es), vals, bounds_error=False, fill_value=None)
        return ip(qpts).reshape(grid.ny, grid.nx, nh)

    # 2) zeitlich von stündlich auf die Modell-Zeitachse
    mtimes = time_axis(cfg)
    h_hr = htimes.hour + htimes.minute / 60.0
    m_hr = mtimes.hour + mtimes.minute / 60.0

    def to_model(field_pts):                             # [npts,nh] -> [nt,ny,nx]
        cube_h = to_grid_hourly(field_pts)
        ft = interp1d(h_hr, cube_h, axis=2, bounds_error=False,
                      fill_value=(cube_h[..., 0], cube_h[..., -1]))
        return np.moveaxis(ft(m_hr), 2, 0).astype(np.float32)

    return CloudAttenuation(
        times=mtimes, f_dir=to_model(f_dir), f_dif=to_model(f_dif), f_ghi=to_model(f_ghi),
        cloud=to_model(C), pts_lonlat=np.column_stack([lon, lat]), source=cfg.nwp_model)
