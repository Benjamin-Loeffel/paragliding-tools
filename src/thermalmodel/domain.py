"""Modellgebiet aus dem gezeichneten KML-Polygon ableiten (LV95-Gitter + Maske)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon

from terrainclearance.geo import CoordTransformer

from .config import ThermalConfig
from .grids import Grid


def parse_kml_polygon(path: str | Path) -> list[tuple[float, float]]:
    """Erstes Polygon eines (swisstopo-)KML als Liste von (lon, lat)."""
    text = Path(path).read_text(encoding="utf-8")
    # Namespace-agnostisch: das <coordinates>-Element finden
    root = ET.fromstring(text)
    coords_el = None
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == "coordinates":
            coords_el = el
            break
    if coords_el is None or not coords_el.text:
        raise ValueError(f"Kein <coordinates>-Element im KML {path}")
    pts = []
    for token in coords_el.text.split():
        parts = token.split(",")
        if len(parts) >= 2:
            pts.append((float(parts[0]), float(parts[1])))  # lon, lat
    if len(pts) < 3:
        raise ValueError("Polygon hat zu wenige Stützpunkte.")
    return pts


def build_domain(cfg: ThermalConfig, transformer: CoordTransformer | None = None):
    """-> (grid, mask[ny,nx] bool, polygon_lv95 shapely.Polygon, lonlat_ring)."""
    tf = transformer or CoordTransformer(use_network=False)
    ring = parse_kml_polygon(cfg.kml_path)
    lons = np.array([p[0] for p in ring])
    lats = np.array([p[1] for p in ring])
    E, N = tf.to_lv95(lons, lats)
    poly = Polygon(np.column_stack([E, N]))

    res = cfg.resolution_m
    # bbox auf das Raster snappen
    west = np.floor(E.min() / res) * res
    east = np.ceil(E.max() / res) * res
    north = np.ceil(N.max() / res) * res
    south = np.floor(N.min() / res) * res
    nx = int(round((east - west) / res))
    ny = int(round((north - south) / res))
    grid = Grid(res=res, west=west, north=north, nx=nx, ny=ny)

    # Maske: standardmässig die ganze Rechteck-Domäne (alle geladenen Kacheln).
    # Nur bei clip_to_polygon=True auf das Polygon-Innere beschneiden.
    if cfg.clip_to_polygon:
        Ec, Nc = grid.cell_centers()
        mask = shapely.contains_xy(poly, Ec.ravel(), Nc.ravel()).reshape(grid.shape)
    else:
        mask = np.ones(grid.shape, dtype=bool)
    return grid, mask, poly, (lons, lats)
