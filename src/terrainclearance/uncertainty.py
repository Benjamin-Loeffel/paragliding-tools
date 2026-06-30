"""Monte-Carlo-Unsicherheit des Hangabstands aus GPS-Positionsrauschen.

Der Hangabstand reagiert in steilem Gelände empfindlich auf den GPS-Fehler
(horizontal nahezu 1:1, vertikal 1:1). Wir stören deshalb jede Trackposition
N-fach normalverteilt (σ_h horizontal, σ_v vertikal) und berechnen die
Streuung des Abstands.

Effizienz: pro Punkt wird **ein** (um 3σ vergrösserter) Gelände-Patch gezogen
und alle N Stichproben dagegen gerechnet. Volles MC nur für niedrige (relevante)
Punkte; weit über Grund dominiert der Vertikalfehler → günstige analytische
Näherung (σ ≈ σ_v).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config
from .terrain import ClearanceResult
from .tiles import Sampler

_PCTL = [5, 95]


@dataclass
class UncertaintyResult:
    # je (N,) Arrays
    mean_terrain: np.ndarray
    p05_terrain: np.ndarray
    p95_terrain: np.ndarray
    min_terrain: np.ndarray
    max_terrain: np.ndarray
    std_terrain: np.ndarray
    mean_surface: np.ndarray
    p05_surface: np.ndarray
    p95_surface: np.ndarray
    min_surface: np.ndarray
    max_surface: np.ndarray
    std_surface: np.ndarray
    sigma_h: float
    sigma_v: float
    n_samples: int


def _mc_point(sampler: Sampler, e: float, n: float, z: float,
              offs: np.ndarray, cfg: Config) -> tuple:
    g = sampler.sample_bilinear(np.array([e]), np.array([n]))[0]
    V = (z - g) if np.isfinite(g) else 0.0
    R = min(abs(V) + cfg.margin_m, cfg.r_cap_m) + 3.0 * cfg.gps_sigma_h_m
    n_side = (2.0 * R) / sampler.res
    stride = max(1, int(np.ceil(n_side / cfg.mc_max_dim)))
    p = sampler.patch(e, n, R, stride=stride)
    if p is None:
        return (np.nan,) * 6
    sub, xs, ys = p
    subf = sub.astype(float)
    subf[sampler._nodata_mask(subf)] = np.nan
    if not np.isfinite(subf).any():
        return (np.nan,) * 6
    Xc = xs[None, :]
    Yc = ys[:, None]
    ex = e + offs[:, 0]
    nx = n + offs[:, 1]
    zx = z + offs[:, 2]
    out = np.empty(offs.shape[0])
    for k in range(offs.shape[0]):
        d2 = (Xc - ex[k]) ** 2 + (Yc - nx[k]) ** 2 + (subf - zx[k]) ** 2
        out[k] = np.nanmin(d2)
    out = np.sqrt(out)
    p05, p95 = np.percentile(out, _PCTL)
    return float(out.mean()), float(p05), float(p95), float(out.min()), float(out.max()), float(out.std())


def _analytic(d3: float, sigma_v: float) -> tuple:
    """Weit über Grund: Abstand ≈ vertikal -> Streuung ≈ σ_v."""
    return (d3, max(0.0, d3 - 1.645 * sigma_v), d3 + 1.645 * sigma_v,
            max(0.0, d3 - 3.0 * sigma_v), d3 + 3.0 * sigma_v, sigma_v)


def compute_uncertainty(e: np.ndarray, n: np.ndarray, z: np.ndarray,
                        dtm: Sampler, dsm: Sampler | None,
                        clr: ClearanceResult, cfg: Config) -> UncertaintyResult:
    N = len(e)
    rng = np.random.default_rng(cfg.mc_seed)
    # gemeinsame Stichproben (glatte Spur, reproduzierbar)
    base = rng.standard_normal((cfg.mc_samples, 3))
    offs = base * np.array([cfg.gps_sigma_h_m, cfg.gps_sigma_h_m, cfg.gps_sigma_v_m])

    def empty():
        return np.full(N, np.nan)

    mt, p5t, p95t, mnt, mxt, sdt = (empty() for _ in range(6))
    ms, p5s, p95s, mns, mxs, sds = (empty() for _ in range(6))

    for i in range(N):
        d3t = clr.d3_terrain[i]
        if np.isfinite(d3t):
            stats = (_mc_point(dtm, e[i], n[i], z[i], offs, cfg)
                     if d3t < cfg.mc_full_below_m else _analytic(d3t, cfg.gps_sigma_v_m))
            mt[i], p5t[i], p95t[i], mnt[i], mxt[i], sdt[i] = stats
        d3s = clr.d3_surface[i]
        if dsm is not None and np.isfinite(d3s):
            stats = (_mc_point(dsm, e[i], n[i], z[i], offs, cfg)
                     if d3s < cfg.mc_full_below_m else _analytic(d3s, cfg.gps_sigma_v_m))
            ms[i], p5s[i], p95s[i], mns[i], mxs[i], sds[i] = stats

    return UncertaintyResult(
        mean_terrain=mt, p05_terrain=p5t, p95_terrain=p95t, min_terrain=mnt, max_terrain=mxt, std_terrain=sdt,
        mean_surface=ms, p05_surface=p5s, p95_surface=p95s, min_surface=mns, max_surface=mxs, std_surface=sds,
        sigma_h=cfg.gps_sigma_h_m, sigma_v=cfg.gps_sigma_v_m, n_samples=cfg.mc_samples,
    )
