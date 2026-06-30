"""Kacheln herunterladen/cachen und als abtastbares Mosaik bereitstellen."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge

from .stac import TileAsset

log = logging.getLogger(__name__)


def download_tiles(tiles: dict[str, TileAsset], cache_subdir: Path, session) -> list[Path]:
    """Lädt jede Kachel nach ``cache_subdir`` (atomar, überspringt Vorhandenes)."""
    cache_subdir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    n_new = 0
    for tile in tiles.values():
        dest = cache_subdir / tile.name
        if dest.exists() and dest.stat().st_size > 0:
            paths.append(dest)
            continue
        tmp = dest.with_suffix(dest.suffix + ".part")
        with session.get(tile.href, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)
        tmp.replace(dest)
        n_new += 1
        paths.append(dest)
    log.info("Kachel-Cache %s: %d gesamt, %d neu geladen", cache_subdir.name, len(paths), n_new)
    return paths


class Sampler:
    """Ein zusammengefügtes Raster mit bilinearer Punktabtastung und Patch-Ausschnitten."""

    def __init__(self, arr: np.ndarray, transform, nodata):
        self.arr = arr
        self.transform = transform
        self.nodata = nodata
        self.H, self.W = arr.shape
        self.res = float(abs(transform.a))
        self.west = float(transform.c)
        self.north = float(transform.f)

    def _nodata_mask(self, vals: np.ndarray) -> np.ndarray:
        bad = ~np.isfinite(vals)
        if self.nodata is not None:
            bad |= vals == self.nodata
        bad |= vals < -1e4  # defensiv: swisstopo-Sentinel
        return bad

    def sample_bilinear(self, e, n) -> np.ndarray:
        """Bilineare Höhe an (e, n). nodata/ausserhalb -> NaN. Vektorisiert."""
        e = np.asarray(e, float)
        n = np.asarray(n, float)
        fc = (e - self.west) / self.res - 0.5
        fr = (self.north - n) / self.res - 0.5
        c0 = np.floor(fc).astype(np.int64)
        r0 = np.floor(fr).astype(np.int64)
        dc = fc - c0
        dr = fr - r0

        def get(rr, cc):
            inb = (rr >= 0) & (rr < self.H) & (cc >= 0) & (cc < self.W)
            rc = np.clip(rr, 0, self.H - 1)
            cc2 = np.clip(cc, 0, self.W - 1)
            vals = self.arr[rc, cc2].astype(float)
            vals[self._nodata_mask(vals)] = np.nan
            vals[~inb] = np.nan
            return vals

        v00 = get(r0, c0)
        v01 = get(r0, c0 + 1)
        v10 = get(r0 + 1, c0)
        v11 = get(r0 + 1, c0 + 1)
        w = np.stack([(1 - dr) * (1 - dc), (1 - dr) * dc, dr * (1 - dc), dr * dc])
        v = np.stack([v00, v01, v10, v11])
        good = np.isfinite(v)
        w = np.where(good, w, 0.0)
        v = np.where(good, v, 0.0)
        wsum = w.sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            out = np.where(wsum > 0, (v * w).sum(axis=0) / wsum, np.nan)
        return out

    def patch(self, e: float, n: float, R: float, stride: int = 1):
        """Ausschnitt [e±R, n±R] -> (sub, xs, ys) oder None ausserhalb.

        ``stride`` > 1 tastet den Patch grob ab (für grosse, unkritische Radien).
        """
        cmin = int(np.floor((e - R - self.west) / self.res))
        cmax = int(np.ceil((e + R - self.west) / self.res))
        rmin = int(np.floor((self.north - (n + R)) / self.res))
        rmax = int(np.ceil((self.north - (n - R)) / self.res))
        cmin = max(cmin, 0)
        rmin = max(rmin, 0)
        cmax = min(cmax, self.W)
        rmax = min(rmax, self.H)
        if cmin >= cmax or rmin >= rmax:
            return None
        sub = self.arr[rmin:rmax:stride, cmin:cmax:stride]
        xs = self.west + (np.arange(cmin, cmax, stride) + 0.5) * self.res
        ys = self.north - (np.arange(rmin, rmax, stride) + 0.5) * self.res
        return sub, xs, ys


def build_mosaic(tile_paths: list[Path], max_cells: int) -> Sampler:
    """Kacheln zu einem In-RAM-Mosaik zusammenfügen und als Sampler zurückgeben."""
    if not tile_paths:
        raise ValueError("Keine Kacheln zum Zusammenfügen.")
    srcs = [rasterio.open(str(p)) for p in tile_paths]
    try:
        nodata = srcs[0].nodata
        # Grobschätzung der Mosaikgrösse aus der Vereinigungs-Bounding-Box
        lefts = [s.bounds.left for s in srcs]
        rights = [s.bounds.right for s in srcs]
        bottoms = [s.bounds.bottom for s in srcs]
        tops = [s.bounds.top for s in srcs]
        res = abs(srcs[0].transform.a)
        cells = ((max(rights) - min(lefts)) / res) * ((max(tops) - min(bottoms)) / res)
        if cells > max_cells:
            raise MemoryError(
                f"Mosaik wäre ~{cells/1e6:.0f} Mio. Zellen (> Limit). "
                f"Flug zu gross für 0.5 m am Stück – Auflösung 2 m wählen oder Flug aufteilen."
            )
        arr, transform = merge(srcs, nodata=nodata)
    finally:
        for s in srcs:
            s.close()
    return Sampler(arr[0], transform, nodata)
