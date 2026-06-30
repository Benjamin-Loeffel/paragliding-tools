"""ICON-Windfeld (Open-Meteo, Druckniveaus) + Partikeltrace-Visualisierung.

meteoswiss_icon_ch1 liefert keine Druckniveau-Winde → icon_seamless (ICON-CH1/D2/EU).
Holt u/v auf mehreren Druckflächen (≈ Grenzschicht über Gelände) an einem Stützpunkt-Raster,
hourly, und erlaubt:
  - field_at_height(z): 2D-(u,v)-Feld auf dem Modellgitter zu fester Höhe/Zeit (für Streamplot),
  - uv(e,n,z): Wind an einem Punkt/Höhe (für die zeitaufgelöste Plume-Advektion).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.interpolate import RegularGridInterpolator

from .config import ThermalConfig
from .grids import Grid
from .reproject import lv95_to_wgs84

log = logging.getLogger(__name__)
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def _arr(loc, key, nh):
    return np.array([np.nan if v is None else float(v) for v in loc["hourly"].get(key, [None] * nh)], float)


@dataclass
class GriddedWind:
    Ulev: np.ndarray      # [nlvl,ny,nx] m/s Ost je Druckniveau
    Vlev: np.ndarray      # [nlvl,ny,nx] m/s Nord
    level_h: np.ndarray   # [nlvl] Höhe AMSL je Niveau (aufsteigend)
    grid: Grid
    U10: np.ndarray = None  # [ny,nx] 10-m-Bodenwind Ost
    V10: np.ndarray = None  # [ny,nx] 10-m-Bodenwind Nord

    def field_agl(self, dtm, agl_m):
        """(U,V)-Feld in agl_m über Grund. <=50 m: 10-m-Bodenwind; sonst Druckniveau-Interp je Zelle."""
        if agl_m <= 50.0 and self.U10 is not None:
            return self.U10, self.V10
        Z = dtm + agl_m
        idx = np.clip(np.searchsorted(self.level_h, Z) - 1, 0, len(self.level_h) - 2)
        h0 = self.level_h[idx]; h1 = self.level_h[idx + 1]
        w = np.clip((Z - h0) / np.maximum(h1 - h0, 1e-6), 0.0, 1.0)
        U0 = np.take_along_axis(self.Ulev, idx[None], 0)[0]; U1 = np.take_along_axis(self.Ulev, (idx + 1)[None], 0)[0]
        V0 = np.take_along_axis(self.Vlev, idx[None], 0)[0]; V1 = np.take_along_axis(self.Vlev, (idx + 1)[None], 0)[0]
        return (1 - w) * U0 + w * U1, (1 - w) * V0 + w * V1

    def _blend(self, z):
        h = self.level_h
        if z <= h[0]:
            return 0, 0, 0.0
        if z >= h[-1]:
            return len(h) - 2, len(h) - 1, 1.0
        i = int(np.searchsorted(h, z) - 1)
        return i, i + 1, (z - h[i]) / (h[i + 1] - h[i])

    def field_at_height(self, z):
        a, b, w = self._blend(z)
        return (1 - w) * self.Ulev[a] + w * self.Ulev[b], (1 - w) * self.Vlev[a] + w * self.Vlev[b]

    def uv(self, e, n, z):
        col = min(max(int((e - self.grid.west) / self.grid.res), 0), self.grid.nx - 1)
        row = min(max(int((self.grid.north - n) / self.grid.res), 0), self.grid.ny - 1)
        a, b, w = self._blend(z)
        u = (1 - w) * self.Ulev[a, row, col] + w * self.Ulev[b, row, col]
        v = (1 - w) * self.Vlev[a, row, col] + w * self.Vlev[b, row, col]
        return float(u), float(v)


@dataclass
class WindField:
    times: pd.DatetimeIndex
    level_h: np.ndarray   # [nlvl] mittlere Höhe AMSL
    u: np.ndarray         # [npts,nlvl,nh] m/s Ost
    v: np.ndarray         # [npts,nlvl,nh] m/s Nord
    es: np.ndarray        # Stützpunkt-Gitter (aufsteigend) LV95 Ost
    ns: np.ndarray        # LV95 Nord
    grid: Grid
    u10: np.ndarray = None  # [npts,nh] 10-m-Bodenwind Ost
    v10: np.ndarray = None

    def _to_grid(self, vals_pts):
        n_n, n_e = len(self.ns), len(self.es)
        Ec, Nc = self.grid.cell_centers()
        qpts = np.column_stack([Nc.ravel(), Ec.ravel()])
        ip = RegularGridInterpolator((self.ns, self.es), vals_pts.reshape(n_n, n_e),
                                     bounds_error=False, fill_value=None)
        return ip(qpts).reshape(self.grid.ny, self.grid.nx).astype(np.float32)

    def griddize(self, hour: int) -> GriddedWind:
        """2D-(u,v)-Felder je Druckniveau + 10-m-Bodenwind zur Stunde `hour` aufs Modellgitter."""
        idx = int(np.argmin(np.abs((self.times.hour + self.times.minute / 60.0) - hour)))
        nlvl = len(self.level_h)
        Ulev = np.stack([self._to_grid(self.u[:, l, idx]) for l in range(nlvl)])
        Vlev = np.stack([self._to_grid(self.v[:, l, idx]) for l in range(nlvl)])
        U10 = self._to_grid(self.u10[:, idx]) if self.u10 is not None else None
        V10 = self._to_grid(self.v10[:, idx]) if self.v10 is not None else None
        return GriddedWind(Ulev=Ulev, Vlev=Vlev, level_h=self.level_h, grid=self.grid, U10=U10, V10=V10)


def fetch_wind_field(cfg: ThermalConfig, grid: Grid, session: requests.Session | None = None) -> WindField:
    n_e, n_n = cfg.nwp_points
    w, s, e, n = grid.bounds()
    es = np.linspace(w, e, n_e); ns = np.linspace(s, n, n_n)
    Eg, Ng = np.meshgrid(es, ns)
    lon, lat = lv95_to_wgs84(Eg.ravel(), Ng.ravel())
    lvls = list(cfg.wind_levels_hpa)

    cache = Path(cfg.cache_dir) / "thermal" / f"wind_{cfg.wind_model}_{cfg.date}_{n_e}x{n_n}.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        log.info("Wind aus Cache: %s", cache.name)
    else:
        hourly = ["wind_speed_10m", "wind_direction_10m"]
        for L in lvls:
            hourly += [f"wind_speed_{L}hPa", f"wind_direction_{L}hPa", f"geopotential_height_{L}hPa"]
        params = {"latitude": ",".join(f"{v:.4f}" for v in lat),
                  "longitude": ",".join(f"{v:.4f}" for v in lon),
                  "hourly": ",".join(hourly), "models": cfg.wind_model,
                  "timezone": cfg.timezone, "start_date": cfg.date, "end_date": cfg.date}
        r = (session or requests).get(OPEN_METEO, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")
        log.info("Wind geladen (%s, %d Niveaus, %d Stützpunkte)", cfg.wind_model, len(lvls), len(lat))

    locs = data if isinstance(data, list) else [data]
    times = pd.to_datetime(locs[0]["hourly"]["time"]).tz_localize(cfg.timezone)
    nh = len(times); npts = len(locs); nlvl = len(lvls)
    u = np.zeros((npts, nlvl, nh)); v = np.zeros((npts, nlvl, nh)); gh = np.zeros((npts, nlvl, nh))
    u10 = np.zeros((npts, nh)); v10 = np.zeros((npts, nh))
    for p, loc in enumerate(locs):
        s10 = _arr(loc, "wind_speed_10m", nh) / 3.6; d10 = _arr(loc, "wind_direction_10m", nh)
        u10[p] = -s10 * np.sin(np.radians(d10)); v10[p] = -s10 * np.cos(np.radians(d10))
        for li, L in enumerate(lvls):
            spd = _arr(loc, f"wind_speed_{L}hPa", nh) / 3.6        # km/h -> m/s
            wd = _arr(loc, f"wind_direction_{L}hPa", nh)
            gh[p, li] = _arr(loc, f"geopotential_height_{L}hPa", nh)
            u[p, li] = -spd * np.sin(np.radians(wd))
            v[p, li] = -spd * np.cos(np.radians(wd))
    for a in (u, v, u10, v10):
        np.nan_to_num(a, copy=False)
    level_h = np.nanmean(gh.reshape(-1, nlvl, nh).transpose(1, 0, 2).reshape(nlvl, -1), axis=1)
    order = np.argsort(level_h)                                    # nach Höhe sortieren
    return WindField(times=times, level_h=level_h[order], u=u[:, order], v=v[:, order],
                     es=es, ns=ns, grid=grid, u10=u10, v10=v10)


def _stream_on_ax(ax, grid, dtm, U, V, density=2.0, vmax_kmh=None):
    """Streamlines (nach Geschwindigkeit in km/h gefärbt) über hellem Relief."""
    from matplotlib.colors import Normalize
    from .viz import draw_hillshade
    draw_hillshade(ax, dtm, grid)
    spd_kmh = np.hypot(U, V) * 3.6
    xs = grid.west + (np.arange(grid.nx) + 0.5) * grid.res
    ys = (grid.north - (np.arange(grid.ny) + 0.5) * grid.res)[::-1]   # aufsteigend für streamplot
    import matplotlib.patheffects as pe
    strm = ax.streamplot(xs, ys, U[::-1], V[::-1], color=spd_kmh[::-1], cmap="cividis",
                         density=density, linewidth=1.4, arrowsize=1.1,
                         norm=None if vmax_kmh is None else Normalize(0, vmax_kmh))
    strm.lines.set_path_effects([pe.Stroke(linewidth=2.8, foreground=(0, 0, 0, 0.32)), pe.Normal()])
    w, s, e, n = grid.bounds()
    ax.set_aspect("equal"); ax.set_xlim(w, e); ax.set_ylim(s, n)
    return strm, float(np.nanmax(spd_kmh))


def plot_wind_traces(grid, mask, dtm, gw: GriddedWind, z_amsl, path, title, density=2.2, dpi=150):
    """Streamplot des ICON-Windfelds in Höhe z über hellem Relief (einzelnes Panel, km/h)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    U, V = gw.field_at_height(z_amsl)
    fig, ax = plt.subplots(figsize=(10, 12))
    strm, _ = _stream_on_ax(ax, grid, dtm, U, V, density)
    fig.colorbar(strm.lines, ax=ax, shrink=0.6, label="Windgeschwindigkeit [km/h]")
    ax.set_title(title); ax.set_xlabel("LV95 Ost [m]"); ax.set_ylabel("LV95 Nord [m]")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return path


def plot_wind_traces_levels(grid, mask, dtm, gw: GriddedWind, path, title, dpi=170):
    """5 Höhenstufen als Subplots (1×5): 10/400 m AGL, 2000/2500/3000 m AMSL; Wind in km/h."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    levels = [("10 m AGL", gw.field_agl(dtm, 10.0)), ("400 m AGL", gw.field_agl(dtm, 400.0)),
              ("2000 m AMSL", gw.field_at_height(2000.0)), ("2500 m AMSL", gw.field_at_height(2500.0)),
              ("3000 m AMSL", gw.field_at_height(3000.0))]
    vmax = max(float(np.nanmax(np.hypot(U, V))) for _, (U, V) in levels) * 3.6 or 1.0
    fig, axes = plt.subplots(1, 5, figsize=(30, 8.5), constrained_layout=True)
    strm = None
    for ax, (lbl, (U, V)) in zip(axes, levels):
        strm, _ = _stream_on_ax(ax, grid, dtm, U, V, density=1.7, vmax_kmh=vmax)
        ax.set_title(lbl, fontsize=13); ax.set_xticks([]); ax.set_yticks([])
    if strm is not None:
        fig.colorbar(strm.lines, ax=axes, shrink=0.85, label="Windgeschwindigkeit [km/h]")
    fig.suptitle(title, fontsize=15)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return path
