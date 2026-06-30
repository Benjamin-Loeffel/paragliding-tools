"""IGC-Steigsegmente extrahieren — Bodenwahrheit für die Hotspot-Validierung.

Idee: Wo der Pilot tatsächlich steigt (anhaltendes positives Vario), liegt eine reale
Thermik. Der *Einstiegspunkt* (Basis des Steigflugs) ist der beste verfügbare Proxy für
den Auslöser/Hotspot — höher driftet die Parzelle bereits mit dem Wind ab. Wir extrahieren
zusätzlich den Schwerpunkt und die Höhenspanne je Steigsegment.

Vario = geglättete Höhenänderung (GNSS bevorzugt, siehe igc_loader). Schwellen
konservativ (anhaltendes Kreisen-Steigen), Werte plausibilisiert gegen Soaring-Praxis
(~0.5–1 m/s als Thermik-Untergrenze).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.ndimage import median_filter

from terrainclearance.config import Config as TCConfig
from terrainclearance.geo import CoordTransformer
from terrainclearance.igc_loader import load_igc


@dataclass
class ClimbSegment:
    flight: str
    e0: float; n0: float; lat0: float; lon0: float          # Einstiegspunkt (Basis)
    ec: float; nc: float                                     # Schwerpunkt (LV95)
    alt_base_m: float; alt_top_m: float
    climb_rate_ms: float; duration_s: float
    drift_m: float                                           # horizontaler Versatz Basis->Top


def _runs(mask: np.ndarray):
    """Start/Ende-Indizes zusammenhängender True-Läufe."""
    if not mask.any():
        return []
    d = np.diff(mask.astype(np.int8))
    starts = list(np.where(d == 1)[0] + 1)
    ends = list(np.where(d == -1)[0])
    if mask[0]:
        starts = [0] + starts
    if mask[-1]:
        ends = ends + [len(mask) - 1]
    return list(zip(starts, ends))


def extract_climbs(track, tf: CoordTransformer, vario_thresh: float = 0.7,
                   min_duration_s: float = 45.0, smooth_s: float = 15.0,
                   min_gain_m: float = 50.0) -> list[ClimbSegment]:
    """Anhaltende Steigsegmente eines Flugs als ClimbSegment-Liste."""
    e, n = tf.to_lv95(track.lon, track.lat)
    t = track.t_s.astype(float)
    alt = track.alt.astype(float)
    if len(t) < 5:
        return []
    dt = np.diff(t)
    vario = np.zeros_like(alt)
    vario[1:] = np.where(dt > 0, np.diff(alt) / np.maximum(dt, 1e-3), 0.0)
    dt_med = float(np.median(dt[dt > 0])) if (dt > 0).any() else 1.0
    w = max(3, int(round(smooth_s / max(dt_med, 0.5))))
    vario_s = median_filter(vario, size=w, mode="nearest")

    out = []
    for a, b in _runs(vario_s > vario_thresh):
        dur = t[b] - t[a]
        gain = alt[b] - alt[a]
        if dur < min_duration_s or gain < min_gain_m:
            continue
        sl = slice(a, b + 1)
        drift = float(np.hypot(e[b] - e[a], n[b] - n[a]))
        out.append(ClimbSegment(
            flight=track.name,
            e0=float(e[a]), n0=float(n[a]), lat0=float(track.lat[a]), lon0=float(track.lon[a]),
            ec=float(np.mean(e[sl])), nc=float(np.mean(n[sl])),
            alt_base_m=float(alt[a]), alt_top_m=float(alt[b]),
            climb_rate_ms=float(gain / max(dur, 1e-3)), duration_s=float(dur), drift_m=drift))
    return out


def collect_climbs(igc_dir: str | Path, tf: CoordTransformer | None = None,
                   bounds_lv95=None, **kw) -> list[ClimbSegment]:
    """Alle IGC in igc_dir → Steigsegmente; optional auf eine LV95-bbox (w,s,e,n) filtern."""
    tf = tf or CoordTransformer(use_network=False)
    cfg = TCConfig()
    segs: list[ClimbSegment] = []
    for p in sorted(Path(igc_dir).glob("*.igc")):
        try:
            track = load_igc(p, cfg)
        except Exception:
            continue
        for c in extract_climbs(track, tf, **kw):
            if bounds_lv95 is not None:
                w, s, e, n = bounds_lv95
                if not (w <= c.e0 <= e and s <= c.n0 <= n):
                    continue
            segs.append(c)
    return segs
