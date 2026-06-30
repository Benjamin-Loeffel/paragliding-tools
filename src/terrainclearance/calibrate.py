"""Höhen-Kalibrierung gegen das Gelände.

Die GNSS-Höhe hat einen langsam veränderlichen Versatz (Datum EGM-Geoid → LN02
plus Session-GPS-Bias). Über die Ausdehnung eines Fluges ist dieser Versatz
nahezu konstant, also bestimmen wir einen additiven Offset ``c`` so, dass die
am Boden (vor Start / nach Landung) aufgezeichnete Höhe zum DTM passt:
``z_kalibriert = z_roh + c``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import median_filter

from .config import Config
from .igc_loader import FlightTrack
from .tiles import Sampler


@dataclass
class CalibrationResult:
    offset_m: float
    method: str            # 'ground_both' | 'ground_takeoff' | 'ground_landing' | 'none'
    confidence: str        # 'high' | 'medium' | 'low'
    n_ground: int
    offset_start: float | None
    offset_end: float | None
    iqr_m: float | None
    note: str
    takeoff_t_s: float     # Flugzeit (s) des Startmoments (Ende Boden-Lauf bzw. Track-Start)
    landing_t_s: float     # Flugzeit (s) des Landemoments (Beginn Boden-Lauf bzw. Track-Ende)

    def apply(self, alt: np.ndarray) -> np.ndarray:
        return alt + self.offset_m


def _segment_metrics(e, n, alt, t_s, window):
    dt = np.diff(t_s)
    safe = np.where(dt > 0, dt, 1.0)
    dist = np.hypot(np.diff(e), np.diff(n))
    speed = np.where(dt > 0, dist / safe, 0.0)
    vario = np.where(dt > 0, np.diff(alt) / safe, 0.0)
    # Rolling-Median glättet einzelne GPS-Ausreisser, die sonst Bodenläufe zerhacken
    w = max(3, int(window))
    if speed.size >= w:
        speed = median_filter(speed, size=w, mode="nearest")
        vario = median_filter(vario, size=w, mode="nearest")
    return speed, vario


def _leading_true(mask: np.ndarray) -> int:
    i = 0
    while i < len(mask) and mask[i]:
        i += 1
    return i


def calibrate_altitude(track: FlightTrack, e: np.ndarray, n: np.ndarray,
                       dtm: Sampler, cfg: Config) -> CalibrationResult:
    N = track.n
    speed, vario = _segment_metrics(e, n, track.alt, track.t_s, cfg.ground_smooth_window)
    grounded = (speed < cfg.v_ground_thresh) & (np.abs(vario) < cfg.vario_ground_thresh)

    li = _leading_true(grounded)                 # Segmente [0, li) am Boden
    ti = _leading_true(grounded[::-1])           # Segmente am Ende am Boden

    # Start-/Landemoment (für Event-Filterung): Ende des Boden-Laufs bzw. Track-Rand
    takeoff_t_s = float(track.t_s[li]) if li > 0 else float(track.t_s[0])
    landing_t_s = float(track.t_s[N - 1 - ti]) if ti > 0 else float(track.t_s[N - 1])

    if cfg.calibration == "none":
        return CalibrationResult(0.0, "none", "low", 0, None, None, None,
                                 "Kalibrierung deaktiviert (calibration='none').",
                                 takeoff_t_s, landing_t_s)

    start_pts = np.arange(0, li + 1) if li > 0 else np.array([], dtype=int)
    end_pts = np.arange(N - 1 - ti, N) if ti > 0 else np.array([], dtype=int)

    start_dur = float(track.t_s[li] - track.t_s[0]) if li > 0 else 0.0
    end_dur = float(track.t_s[N - 1] - track.t_s[N - 1 - ti]) if ti > 0 else 0.0

    use_start = li > 0 and start_dur >= cfg.ground_min_seconds
    use_end = ti > 0 and end_dur >= cfg.ground_min_seconds

    def residuals(pts):
        if len(pts) == 0:
            return np.array([])
        dtm_h = dtm.sample_bilinear(e[pts], n[pts])
        r = dtm_h - track.alt[pts]
        return r[np.isfinite(r)]

    r_start = residuals(start_pts) if use_start else np.array([])
    r_end = residuals(end_pts) if use_end else np.array([])

    offset_start = float(np.median(r_start)) if r_start.size else None
    offset_end = float(np.median(r_end)) if r_end.size else None

    combined = np.concatenate([r_start, r_end])
    if combined.size == 0:
        return CalibrationResult(
            0.0, "none", "low", 0, offset_start, offset_end, None,
            "Kein Boden-Segment erkannt – kein Offset angewandt (z_roh verwendet). "
            "Ergebnisse mit Vorsicht interpretieren.",
            takeoff_t_s, landing_t_s,
        )

    c = float(np.median(combined)) + cfg.antenna_height_m
    iqr = float(np.subtract(*np.percentile(combined, [75, 25])))

    if use_start and use_end:
        method = "ground_both"
        diff = abs((offset_start or 0) - (offset_end or 0))
        if diff <= 5:
            confidence = "high"
        elif diff <= 15:
            confidence = "medium"
        else:
            confidence = "low"
        note = f"Start/Land-Offset {offset_start:+.1f}/{offset_end:+.1f} m (Δ {diff:.1f} m)."
    elif use_start:
        method, confidence = "ground_takeoff", "medium"
        note = "Nur Start-Bodensegment verwendet (keine saubere Landung erkannt)."
    else:
        method, confidence = "ground_landing", "medium"
        note = "Nur Lande-Bodensegment verwendet (luftiger Start?)."

    if abs(c) > cfg.max_plausible_offset_m:
        confidence = "low"
        note += f" WARNUNG: Offset {c:+.1f} m ungewöhnlich gross – GNSS-Höhe prüfen."

    return CalibrationResult(
        offset_m=c,
        method=method,
        confidence=confidence,
        n_ground=int(combined.size),
        offset_start=offset_start,
        offset_end=offset_end,
        iqr_m=iqr,
        note=note,
        takeoff_t_s=takeoff_t_s,
        landing_t_s=landing_t_s,
    )
