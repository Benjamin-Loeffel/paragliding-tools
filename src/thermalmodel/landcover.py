"""Bodenbedeckung → class_id + Albedo/f_H-Karten.

Waldfläche UND Nadel-/Laub-Typ aus dem BAFU/LFI-Waldmischungsgrad (10 m, EPSG:2056,
Wert = % Laubholz; nodata = kein Wald) via /vsicurl/-Fensterlesen. Fels/Wiese per
Heuristik (Slope/Höhe). Fallback: TLM3D-Wald-WMS (Nadel-Annahme) bzw. reine Heuristik.
Albedo/f_H im Wald linear zwischen Nadel- und Laubholz interpoliert.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import numpy as np
import requests

from . import config as C
from .config import ThermalConfig
from .grids import Grid

log = logging.getLogger(__name__)
WMS = "https://wms.geo.admin.ch/"
WALDMISCH_TIF = ("https://data.geo.admin.ch/ch.bafu.landesforstinventar-waldmischungsgrad/"
                 "landesforstinventar-waldmischungsgrad/landesforstinventar-waldmischungsgrad_2056.tif")


@dataclass
class LandcoverGrid:
    class_id: np.ndarray   # uint8, LC_* Codes
    albedo: np.ndarray
    f_H: np.ndarray
    broadleaf_frac: np.ndarray   # 0..1 (NaN ausserhalb Wald)
    forest_source: str           # 'waldmischungsgrad' | 'wms' | 'none'


def broadleaf_pct_from_lfi(grid: Grid) -> np.ndarray | None:
    """% Laubholz aufs Gitter (NaN = kein Wald) aus dem LFI-Waldmischungsgrad-COG."""
    try:
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.windows import from_bounds
        w, s, e, n = grid.bounds()
        # Sidecar-Proben (.aux.xml etc.) unterbinden -> keine 403-Flut, schneller
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                          CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
            with rasterio.open("/vsicurl/" + WALDMISCH_TIF) as src:
                win = from_bounds(w, s, e, n, src.transform)
                arr = src.read(1, window=win, out_shape=(grid.ny, grid.nx),
                               resampling=Resampling.nearest).astype(float)
                nod = src.nodata
        arr[arr == nod] = np.nan
        arr[(arr < 0) | (arr > 100)] = np.nan
        return arr
    except Exception as exc:
        log.warning("Waldmischungsgrad-Read fehlgeschlagen: %s", exc)
        return None


def forest_mask_from_wms(grid: Grid, session: requests.Session) -> np.ndarray | None:
    """Fallback-Waldmaske aus dem TLM3D-Wald-WMS (transparent = kein Wald)."""
    w, s, e, n = grid.bounds()
    params = {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
              "LAYERS": "ch.swisstopo.swisstlm3d-wald", "STYLES": "", "CRS": "EPSG:2056",
              "BBOX": f"{w},{s},{e},{n}", "WIDTH": str(grid.nx), "HEIGHT": str(grid.ny),
              "FORMAT": "image/png", "TRANSPARENT": "TRUE"}
    try:
        r = session.get(WMS, params=params, timeout=120); r.raise_for_status()
        import matplotlib.pyplot as plt
        img = plt.imread(io.BytesIO(r.content), format="png")
        forest = (img[:, :, 3] > 0.3) if (img.ndim == 3 and img.shape[2] == 4) \
            else (img[..., :3].mean(axis=2) < 0.95)
        return forest if forest.shape == grid.shape else None
    except Exception as exc:
        log.warning("TLM3D-Wald-WMS fehlgeschlagen: %s", exc)
        return None


def forest_edge(lc: LandcoverGrid, width_cells: int = 1) -> np.ndarray:
    """Boolesche Wald↔Nichtwald-Kante (Land-Cover-Grenze) — zusätzlicher Ablöse-Trigger.

    An Vegetationsgrenzen (Albedo-/Rauhigkeits-/Feuchte-Sprung) löst Thermik leichter ab; fällt
    eine solche Kante mit einem Geländebruch zusammen, ist die Ablösung deutlich wahrscheinlicher.
    """
    from scipy.ndimage import binary_dilation
    forest = np.isin(lc.class_id, [C.LC_CONIFER, C.LC_BROADLEAF, C.LC_MIXED])
    gy, gx = np.gradient(forest.astype(np.float32))
    edge = np.hypot(gx, gy) > 0.1
    if width_cells > 0:
        edge = binary_dilation(edge, iterations=width_cells)
    return edge


def classify(cfg: ThermalConfig, terrain, grid: Grid,
             session: requests.Session | None = None) -> LandcoverGrid:
    s = session or requests.Session()
    ny, nx = terrain.slope.shape
    slope_deg = np.degrees(terrain.slope)
    cls = np.full((ny, nx), C.LC_GRASS, dtype=np.uint8)
    bf = np.full((ny, nx), np.nan, dtype=np.float32)   # Laubanteil 0..1
    albedo = np.empty((ny, nx), np.float32)
    f_H = np.empty((ny, nx), np.float32)

    # 1) Wald + Typ aus LFI-Waldmischungsgrad
    pct = broadleaf_pct_from_lfi(grid)
    source = "none"
    forest = np.zeros((ny, nx), bool)
    if pct is not None and np.isfinite(pct).any():
        source = "waldmischungsgrad"
        forest = np.isfinite(pct)
        bf[forest] = pct[forest] / 100.0
    else:
        wms = forest_mask_from_wms(grid, s)
        if wms is not None:
            source = "wms"
            forest = wms
            bf[forest] = 0.15   # Annahme nadeldominiert (15% Laub)

    # 2) Klassen (Anzeige) + Albedo/f_H
    cf = 1.0 - bf   # Nadelanteil
    # Wald: linear zwischen Nadel- und Laubholz interpolieren
    albedo[forest] = C.ALBEDO[C.LC_CONIFER] * cf[forest] + C.ALBEDO[C.LC_BROADLEAF] * bf[forest]
    f_H[forest] = C.F_H[C.LC_CONIFER] * cf[forest] + C.F_H[C.LC_BROADLEAF] * bf[forest]
    cls[forest & (cf >= 0.66)] = C.LC_CONIFER
    cls[forest & (bf >= 0.66)] = C.LC_BROADLEAF
    cls[forest & (cf < 0.66) & (bf < 0.66)] = C.LC_MIXED

    # 3) Nicht-Wald: Fels/Geröll (steil/hoch) sonst Wiese
    nonforest = ~forest
    rock = nonforest & ((slope_deg > 42.0) | (terrain.dtm > 2200.0))
    cls[nonforest & ~rock] = C.LC_GRASS
    cls[rock] = C.LC_ROCK
    albedo[nonforest] = np.vectorize(C.ALBEDO.get)(cls[nonforest]).astype(np.float32)
    f_H[nonforest] = np.vectorize(C.F_H.get)(cls[nonforest]).astype(np.float32)

    return LandcoverGrid(class_id=cls, albedo=albedo, f_H=f_H, broadleaf_frac=bf, forest_source=source)
