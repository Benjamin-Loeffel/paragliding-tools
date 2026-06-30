"""Kernalgorithmus: minimaler 3D-Abstand jedes Trackpunkts zum Gelände.

Idee: Für einen Punkt P=(x,y,z) und jede Rasterzelle im Horizontalabstand d gilt
3D-Abstand = sqrt(d² + Δz²) >= d. Der vertikale Abstand V = z − Boden(x,y) ist
also eine obere Schranke für den wahren 3D-Abstand. Deshalb genügt ein
Suchradius R = min(|V| + margin, r_cap) — exakt, solange |V| <= r_cap.

Für hohe (unkritische) Punkte wird der Patch mit einem Stride grob abgetastet:
Die Distanz ist dann ohnehin gross, Sub-Meter-Präzision irrelevant; bodennahe
(kritische) Punkte werden immer voll aufgelöst abgetastet.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config
from .tiles import Sampler


@dataclass
class ClearanceResult:
    terrain_elev: np.ndarray   # DTM-Höhe unter dem Punkt (m)
    surface_elev: np.ndarray   # DSM-Höhe unter dem Punkt (m)
    v_terrain: np.ndarray      # vertikaler Abstand AGL = z − DTM (m, kann < 0)
    v_surface: np.ndarray      # z − DSM (m, kann < 0 = unter Wipfel/Dach)
    d3_terrain: np.ndarray     # 3D-Abstand zum nackten Gelände (m)
    d3_surface: np.ndarray     # 3D-Abstand zur Oberfläche/Baumkrone (m)
    near_e: np.ndarray         # easting des nächsten Geländepunkts (DTM)
    near_n: np.ndarray         # northing des nächsten Geländepunkts (DTM)
    clipped: np.ndarray        # bool: R war begrenzt UND Minimum am Rand -> evtl. inexakt


def _nearest(sampler: Sampler, e: float, n: float, z: float, R: float, max_dim: int):
    """(d3, near_e, near_n, capped_boundary) für den nächsten gültigen Zellpunkt."""
    n_side = (2.0 * R) / sampler.res
    stride = max(1, int(np.ceil(n_side / max_dim)))
    p = sampler.patch(e, n, R, stride=stride)
    if p is None:
        return np.nan, np.nan, np.nan, False
    sub, xs, ys = p
    sub = sub.astype(np.float64)
    bad = sampler._nodata_mask(sub)
    dx = xs[None, :] - e
    dy = ys[:, None] - n
    dz = sub - z
    dist2 = dx * dx + dy * dy + dz * dz
    dist2[bad] = np.inf
    if not np.isfinite(dist2).any():
        return np.nan, np.nan, np.nan, False
    idx = int(np.argmin(dist2))
    r, c = np.unravel_index(idx, dist2.shape)
    d3 = float(np.sqrt(dist2[r, c]))
    at_boundary = d3 >= R - 1e-6
    return d3, float(xs[c]), float(ys[r]), at_boundary


def compute_clearances(
    e: np.ndarray, n: np.ndarray, z: np.ndarray,
    dtm: Sampler, dsm: Sampler | None, cfg: Config,
) -> ClearanceResult:
    N = len(e)
    terrain_elev = dtm.sample_bilinear(e, n)
    surface_elev = dsm.sample_bilinear(e, n) if dsm is not None else np.full(N, np.nan)
    v_terrain = z - terrain_elev
    v_surface = z - surface_elev

    d3_terrain = np.full(N, np.nan)
    d3_surface = np.full(N, np.nan)
    near_e = np.full(N, np.nan)
    near_n = np.full(N, np.nan)
    clipped = np.zeros(N, dtype=bool)

    max_dim = cfg.max_patch_dim
    for i in range(N):
        vt = v_terrain[i]
        if np.isfinite(vt):
            need = abs(vt) + cfg.margin_m
            R = min(need, cfg.r_cap_m)
            d3, ne, nn, boundary = _nearest(dtm, e[i], n[i], z[i], R, max_dim)
            d3_terrain[i] = d3
            near_e[i] = ne
            near_n[i] = nn
            clipped[i] = (need > cfg.r_cap_m) and boundary

        vs = v_surface[i]
        if dsm is not None and np.isfinite(vs):
            R = min(abs(vs) + cfg.margin_m, cfg.r_cap_m)
            d3s, _, _, _ = _nearest(dsm, e[i], n[i], z[i], R, max_dim)
            d3_surface[i] = d3s

    return ClearanceResult(
        terrain_elev=terrain_elev,
        surface_elev=surface_elev,
        v_terrain=v_terrain,
        v_surface=v_surface,
        d3_terrain=d3_terrain,
        d3_surface=d3_surface,
        near_e=near_e,
        near_n=near_n,
        clipped=clipped,
    )
