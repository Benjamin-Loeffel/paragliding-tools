"""Terrain auf das Modellgitter laden und Ableitungen berechnen.

Lädt swissALTI3D (DTM) und swissSURFACE3D (DSM) über das terrainclearance-STAC/Tiles-
Modul, resamplet auf das Modellgitter und berechnet slope/aspect/curvature/chm.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import requests

from terrainclearance.config import Config as TCConfig
from terrainclearance.stac import find_tiles
from terrainclearance.tiles import build_mosaic, download_tiles

from .config import ThermalConfig
from .grids import Grid, resample_from_sampler


@dataclass
class TerrainGrid:
    grid: Grid
    dtm: np.ndarray       # m ü. M.
    dsm: np.ndarray
    chm: np.ndarray       # Bewuchs/Objekthöhe = dsm - dtm
    slope: np.ndarray     # rad (0=flach)
    aspect: np.ndarray    # rad, 0=Nord, im Uhrzeigersinn (pvlib-Konvention)
    curvature: np.ndarray # 1/m, >0 konvex (Grat/Kuppe), <0 konkav (Mulde)


def _slope_aspect(z: np.ndarray, res: float):
    # np.gradient: dzdy = d/dRow (Row zeigt nach SÜDEN), dzdx = d/dCol (Col zeigt nach OSTEN)
    dzdy, dzdx = np.gradient(z, res, res)
    slope = np.arctan(np.hypot(dzdx, dzdy))
    # Aspect = Richtung, in die der Hang ZEIGT (bergab), 0=N, 90=O, im Uhrzeigersinn
    # (gleiche Konvention wie pvlib-Sonnenazimut). In (Ost,Nord) ist
    #   d z/d Ost = dzdx,  d z/d Nord = -dzdy  (Row -> Süden).
    # Bergab-Richtung = -grad z = (-dzdx, +dzdy); Kompass-Azimut = atan2(Ost-Komp, Nord-Komp).
    aspect = np.arctan2(-dzdx, dzdy) % (2 * np.pi)
    return slope, aspect


def _curvature(z: np.ndarray, res: float) -> np.ndarray:
    dzdy, dzdx = np.gradient(z, res, res)
    d2y, _ = np.gradient(dzdy, res, res)
    _, d2x = np.gradient(dzdx, res, res)
    return -(d2x + d2y)   # Laplacian; Vorzeichen so, dass Kuppen/Grate > 0


def load_terrain(cfg: ThermalConfig, grid: Grid, lonlat_bbox, session: requests.Session | None = None,
                 with_dsm: bool | None = None) -> TerrainGrid:
    s = session or requests.Session()
    if with_dsm is None:
        with_dsm = cfg.use_chm
    # DTM: gewünschte Auflösung (2 m reicht fürs 20-m-Gitter, schlank).
    tc_dtm = TCConfig(resolution=cfg.dtm_resolution, cache_dir=cfg.cache_dir)
    dtm_sampler = build_mosaic(
        download_tiles(find_tiles(tc_dtm, lonlat_bbox, "dtm", s), cfg.cache_dir / "dtm", s),
        tc_dtm.max_mosaic_cells)
    dtm = resample_from_sampler(grid, dtm_sampler)

    # DSM: nur in 0.5 m verfügbar; optional (für CHM/Waldgate) und robust.
    dsm = np.full(grid.shape, np.nan)
    if with_dsm:
        tc_dsm = TCConfig(resolution=0.5, cache_dir=cfg.cache_dir)
        dsm_tiles = find_tiles(tc_dsm, lonlat_bbox, "dsm", s)
        if dsm_tiles:
            dsm_sampler = build_mosaic(
                download_tiles(dsm_tiles, cfg.cache_dir / "dsm", s), tc_dsm.max_mosaic_cells)
            dsm = resample_from_sampler(grid, dsm_sampler)
    chm = np.where(np.isfinite(dsm) & np.isfinite(dtm), dsm - dtm, 0.0)
    chm = np.clip(chm, 0.0, None)

    # NaN (Kachelrand) für Ableitungen mit Nearest füllen, damit Gradienten nicht zerlaufen
    z = dtm.copy()
    if not np.isfinite(z).all():
        m = np.isfinite(z)
        if m.any():
            z[~m] = np.nanmean(z)
    slope, aspect = _slope_aspect(z, grid.res)
    curv = _curvature(z, grid.res)
    return TerrainGrid(grid=grid, dtm=dtm, dsm=dsm, chm=chm, slope=slope, aspect=aspect, curvature=curv)
