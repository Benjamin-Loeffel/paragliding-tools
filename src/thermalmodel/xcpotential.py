"""XC-Flugpotenzial (Tagesgüte 0–100 %) — adaptiert von soaringmeteo (XCFlyingPotential.scala).

Logistik-Blend dreier flugrelevanter Grössen (soaringmeteo-Schwellen; w* doppelt gewichtet):
  thermalVelocityCoeff = logistic(w*,  μ=1.55 m/s, k=5)   ← unser w*-Median 1.56 ≈ ihr μ!
  soaringLayerCoeff    = logistic(SLD, μ=400 m,   k=4)
  thermalCoeff = (2·vCoeff + sldCoeff)/3
  windCoeff    = 1 − logistic(windBL[km/h], μ=16, k=6)     ← Gegenwind dämpft
  ThQ = thermalCoeff · windCoeff · 100

Wir nutzen unser sondierungs-/gelände-basiertes w* und die Soaring-Layer-Depth (= nutzbares Band
bis Ceiling) statt soaringmeteos modell-PBL — physikalisch direkter. Feld auf grobem Raster
gerechnet (strength_at je Zelle) und aufs Modellgitter interpoliert.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .boundarylayer import strength_at


def logistic(x, mu, k):
    return 1.0 / (1.0 + np.exp(-(x - mu) / (mu / k)))


def xc_potential_field(cfg, res, bl, gw, qh_field, wind_height_m=2000.0, step=8):
    """ThQ-Feld [ny,nx] (0–100). gw=GriddedWind (für BL-Wind), qh_field=Q_H-Tagesmax (real)."""
    grid, mask, terr = res["grid"], res["mask"], res["terrain"]
    U, V = gw.field_at_height(wind_height_m)
    wind_kmh = np.hypot(U, V) * 3.6

    rows = np.arange(0, grid.ny, step); cols = np.arange(0, grid.nx, step)
    thq = np.zeros((len(rows), len(cols)), float)
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            s = strength_at(bl, float(terr.dtm[r, c]), float(qh_field[r, c]))
            vC = logistic(s["w_star_ms"], 1.55, 5); sldC = logistic(s["z_i_m"], 400.0, 4)
            windC = 1.0 - logistic(float(wind_kmh[r, c]), 16.0, 6)
            thq[i, j] = (2 * vC + sldC) / 3.0 * windC * 100.0

    ip = RegularGridInterpolator((rows.astype(float), cols.astype(float)), thq,
                                 bounds_error=False, fill_value=None)
    rr, cc = np.meshgrid(np.arange(grid.ny, dtype=float), np.arange(grid.nx, dtype=float), indexing="ij")
    full = ip(np.column_stack([rr.ravel(), cc.ravel()])).reshape(grid.ny, grid.nx)
    return np.clip(np.where(mask, full, np.nan), 0, 100).astype(np.float32)


def plot_xc_potential(grid, mask, dtm, thq, path, title):
    from .plotstyle import use as _use
    plt = _use()
    from .viz import draw_hillshade

    fig, ax = plt.subplots(figsize=(13, 15.5))
    ext = draw_hillshade(ax, dtm, grid)
    im = ax.imshow(thq, cmap="viridis", extent=ext, origin="upper", alpha=0.78,
                   interpolation="bilinear", vmin=0, vmax=100)
    fig.colorbar(im, ax=ax, shrink=0.6, label="XC-Flugpotenzial [%]")
    ax.set_title(title); ax.set_xlabel("LV95 Ost [m]"); ax.set_ylabel("LV95 Nord [m]")
    ax.set_aspect("equal")
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path
