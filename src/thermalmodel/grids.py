"""Modellgitter (LV95) + GeoTIFF-I/O + Resampling aus einem terrainclearance-Sampler."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from terrainclearance.tiles import Sampler

LV95 = "EPSG:2056"


@dataclass
class Grid:
    """Reguläres LV95-Raster. Zellzentren-Konvention wie terrainclearance.Sampler."""
    res: float
    west: float    # westliche Kante (LV95 E)
    north: float   # nördliche Kante (LV95 N)
    nx: int
    ny: int

    @property
    def transform(self):
        return from_origin(self.west, self.north, self.res, self.res)

    @property
    def shape(self):
        return (self.ny, self.nx)

    def cell_centers(self):
        xs = self.west + (np.arange(self.nx) + 0.5) * self.res
        ys = self.north - (np.arange(self.ny) + 0.5) * self.res
        return np.meshgrid(xs, ys)   # E[ny,nx], N[ny,nx]

    def bounds(self):
        return (self.west, self.north - self.ny * self.res,
                self.west + self.nx * self.res, self.north)

    def to_geotiff(self, arr: np.ndarray, path: Path, nodata=np.nan, dtype=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        a = arr.astype(dtype or ("float32" if np.issubdtype(arr.dtype, np.floating) else arr.dtype))
        with rasterio.open(
            str(path), "w", driver="GTiff", height=self.ny, width=self.nx, count=1,
            dtype=a.dtype, crs=LV95, transform=self.transform, nodata=nodata,
            compress="deflate",
        ) as dst:
            dst.write(a, 1)
        return path


def resample_from_sampler(grid: Grid, sampler: Sampler) -> np.ndarray:
    """Sampler (z. B. DTM/DSM-Mosaik) bilinear an die Gitter-Zellzentren abtasten."""
    E, N = grid.cell_centers()
    vals = sampler.sample_bilinear(E.ravel(), N.ravel())
    return vals.reshape(grid.shape)
