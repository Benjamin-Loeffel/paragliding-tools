"""Verschiebungs-tolerante Ko-Lokalisation: Modell-Hotspots/Score vs. reale Steigflüge.

Zwei komplementäre, statistische Masse (kk7 ist unscharf, eine Modell-Realisierung gegen
Mehrwochen-Stichprobe → keine Pixelgenauigkeit):

1. Hit-Rate (Toleranz 200/300/500 m): Anteil realer Steig-Einstiege nahe einem Top-N-Hotspot,
   gegen eine Zufalls-Baseline (gleich viele zufällige Domänenpunkte). Lift = real/zufall.
2. Score-AUC: Wahrscheinlichkeit, dass das Modell-Score-Feld an einem Steigpunkt höher ist als
   an einem zufälligen Domänenpunkt (0.5 = keine Vorhersagekraft, →1 = perfekt). Schwellenfrei.
"""

from __future__ import annotations

import numpy as np


def _nearest_dist(e, n, ref_e, ref_n) -> np.ndarray:
    """Minimaldistanz jedes (e,n) zur Referenzpunktmenge [m]."""
    if len(ref_e) == 0:
        return np.full(len(e), np.inf)
    de = e[:, None] - np.asarray(ref_e)[None, :]
    dn = n[:, None] - np.asarray(ref_n)[None, :]
    return np.sqrt(de * de + dn * dn).min(axis=1)


def _sample_grid(grid, field, e, n) -> np.ndarray:
    """Nearest-Zellwert des Felds an LV95-Punkten (NaN ausserhalb)."""
    col = ((np.asarray(e) - grid.west) / grid.res).astype(int)
    row = ((grid.north - np.asarray(n)) / grid.res).astype(int)
    ok = (row >= 0) & (row < grid.ny) & (col >= 0) & (col < grid.nx)
    out = np.full(len(e), np.nan)
    out[ok] = field[row[ok], col[ok]]
    return out


def _auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """P(pos > neg) per Rang (Mann-Whitney-U / (n_pos*n_neg))."""
    pos = pos[np.isfinite(pos)]; neg = neg[np.isfinite(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort().astype(float) + 1.0   # 1..N, Ties grob ok
    r_pos = ranks[:len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def validate(grid, mask, score, q_h_daymax, hotspots, tgt_e, tgt_n,
             tols=(200.0, 300.0, 500.0), n_random=4000, seed=0) -> dict:
    """Metriken Modell vs. Zielpunkte (Steigflüge oder kk7). tgt_e/tgt_n = LV95-Arrays."""
    ce = np.asarray(tgt_e, dtype=float); cn = np.asarray(tgt_n, dtype=float)
    he = np.array([h.e for h in hotspots]); hn = np.array([h.n for h in hotspots])

    # Zufalls-Baseline aus Domänenzellen
    rng = np.random.default_rng(seed)
    ys, xs = np.where(mask)
    pick = rng.choice(len(ys), size=min(n_random, len(ys)), replace=False)
    rE = grid.west + (xs[pick] + 0.5) * grid.res
    rN = grid.north - (ys[pick] + 0.5) * grid.res

    d_climb = _nearest_dist(ce, cn, he, hn)
    d_rand = _nearest_dist(rE, rN, he, hn)
    hit = {}
    for t in tols:
        hr = float(np.mean(d_climb <= t)); rr = float(np.mean(d_rand <= t))
        hit[int(t)] = {"climb": hr, "random": rr, "lift": (hr / rr if rr > 0 else float("inf"))}

    # Score-/Q_H-AUC
    s_climb = _sample_grid(grid, score, ce, cn)
    s_rand = score[mask]
    q_climb = _sample_grid(grid, q_h_daymax, ce, cn)
    q_rand = q_h_daymax[mask]
    auc_score = _auc(s_climb, s_rand)
    auc_qh = _auc(q_climb, q_rand)

    # Perzentilrang der Steigpunkte im Score-Feld
    pct = float(np.mean([np.mean(s_rand < v) for v in s_climb[np.isfinite(s_climb)]]) * 100)

    return {
        "n_climbs": len(ce), "n_hotspots": len(hotspots),
        "hit_rate": hit, "auc_score": auc_score, "auc_qh": auc_qh,
        "median_score_pct": pct,
        "median_dist_to_hotspot_m": float(np.median(d_climb)),
        "climb_score": s_climb, "climb_qh": q_climb,
    }


def _smooth(field, res, sig_m):
    """Gauss-Glättung mit NaN-Behandlung (für verschiebungstolerante Vergleiche)."""
    from scipy.ndimage import gaussian_filter
    a = np.where(np.isfinite(field), field, 0.0)
    m = np.isfinite(field).astype(float)
    num = gaussian_filter(a, sig_m / res); den = gaussian_filter(m, sig_m / res)
    return np.where(den > 1e-3, num / den, np.nan)


def heatmap_metrics(grid, mask, field, kk7, smooth_m=250.0) -> dict:
    """Verschiebungstolerante Übereinstimmung Modellfeld ↔ kk7-Thermik-Dichte (geglättet).
    Spearman-Rangkorrelation + AUC (Modell unterscheidet kk7-Dichte >p70)."""
    from scipy.stats import spearmanr
    fs = _smooth(field, grid.res, smooth_m); ks = _smooth(kk7, grid.res, smooth_m)
    ok = mask & np.isfinite(ks) & np.isfinite(fs) & (ks > 0.02)
    if ok.sum() < 50:
        return {}
    thr = np.nanpercentile(ks[ok], 70)
    return {"spearman": float(spearmanr(fs[ok], ks[ok]).correlation),
            "auc": float(_auc(fs[ok][ks[ok] >= thr], fs[ok][ks[ok] < thr])), "n": int(ok.sum())}


def plot_validation_map(grid, mask, dtm, score, hotspots, climbs, path, title, kk7=None):
    """Hillshade + Score + Top-Hotspots (Kreise) + reale Steig-Einstiege (Kreuze) + kk7 (Quadrate)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ..viz import draw_hillshade

    fig, ax = plt.subplots(figsize=(10, 12))
    ext = draw_hillshade(ax, dtm, grid)
    ax.imshow(np.where(mask, score, np.nan), cmap="viridis", extent=ext, origin="upper",
              alpha=0.6, interpolation="nearest")
    if hotspots:
        ax.scatter([h.e for h in hotspots], [h.n for h in hotspots], s=55, facecolors="none",
                   edgecolors="white", linewidths=1.2, label="Modell-Hotspots (Top-N)")
    if kk7:
        ax.scatter([k.e for k in kk7], [k.n for k in kk7], s=80, marker="s", facecolors="none",
                   edgecolors="gold", linewidths=1.8, label="kk7-Hotspots (viele Piloten)")
    if climbs:
        ax.scatter([c.e0 for c in climbs], [c.n0 for c in climbs], s=60, marker="x",
                   c="red", linewidths=1.8, label="reale Steig-Einstiege (IGC)")
    ax.set_title(title); ax.set_xlabel("LV95 Ost [m]"); ax.set_ylabel("LV95 Nord [m]")
    ax.legend(loc="upper right", fontsize=9); ax.set_aspect("equal")
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=175, bbox_inches="tight"); plt.close(fig)
    return path
