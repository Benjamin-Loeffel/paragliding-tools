"""Gleitzahlen entlang der Flugspur: Geradeausstücke über Grund und windkorrigiert.

Vorgehen (bewusst einfach und nachvollziehbar):

* Spur auf ein 1-s-Raster interpolieren (IGC-Lücken/Duplikate), Höhe leicht glätten.
* Drehrate aus dem Kurs über Grund; **geradeaus** = Drehrate < ``max_turn_dps`` über mindestens
  ``min_s`` Sekunden (erste/letzte 15 s des Flugs ausgenommen: Start, Landung).
* **Wind** = Mittelpunkt eines Kreis-Fits (Kasa) durch die Grundgeschwindigkeitsvektoren der
  Kurven-/Kreisphasen (Radius = Fahrt). Ohne genug Kurven wird der ganze Flug genommen.
* Gleitzahl über Grund = Weg über Grund / Höhenverlust; **in der Luft** = Weg relativ zur Luft
  (Grundvektor minus Wind) / Höhenverlust.

Steigen/Sinken der Luftmasse steckt im Höhenverlust: das sind Werte des Tages, keine Schirmpolare.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class GlideSegment:
    i0: int                 # Index in der Original-Spur (erster Fix)
    i1: int                 # Index in der Original-Spur (letzter Fix)
    t0_s: float             # Sekunden seit erstem Fix
    duration_s: float
    length_m: float         # Weg über Grund
    loss_m: float           # Höhenverlust
    glide_ground: float
    glide_air: float
    sink_mps: float
    gs_kmh: float
    airspeed_kmh: float
    bearing_deg: float      # Kurs über Grund Anfang -> Ende


@dataclass
class GlideResult:
    segments: list[GlideSegment] = field(default_factory=list)
    wind_from_deg: float = float("nan")
    wind_kmh: float = float("nan")
    airspeed_kmh: float = float("nan")
    track_m: float = float("nan")         # ganzer Flugweg über Grund (Start..Landung)
    loss_m: float = float("nan")          # Höhenverlust Start..Landung
    straight: dict = field(default_factory=dict)

    @property
    def glide_track(self) -> float:
        return self.track_m / self.loss_m if self.loss_m > 0 else float("nan")


def _smooth(x: np.ndarray, n: int) -> np.ndarray:
    if n <= 1 or x.size < n:
        return x
    k = np.ones(n) / n
    return np.convolve(np.pad(x, (n // 2, n // 2), mode="edge"), k, mode="valid")


def _circle_fit(vx: np.ndarray, vy: np.ndarray) -> tuple[float, float, float]:
    """Kasa-Fit (vx-a)^2 + (vy-b)^2 = r^2 -> (a, b, r)."""
    A = np.c_[2 * vx, 2 * vy, np.ones_like(vx)]
    (a, b, c), *_ = np.linalg.lstsq(A, vx ** 2 + vy ** 2, rcond=None)
    return float(a), float(b), float(np.sqrt(max(c + a * a + b * b, 0.0)))


def glide_segments(e: np.ndarray, n: np.ndarray, z: np.ndarray, t_s: np.ndarray,
                   valid: np.ndarray | None = None, min_s: float = 20.0,
                   max_turn_dps: float = 4.0, circle_turn_dps: float = 8.0,
                   move_mps: float = 2.0, edge_s: float = 15.0) -> GlideResult:
    e, n, z, t_s = (np.asarray(a, float) for a in (e, n, z, t_s))
    ok = np.isfinite(e) & np.isfinite(n) & np.isfinite(z) & np.isfinite(t_s)
    if valid is not None:
        ok &= np.asarray(valid, bool)
    idx = np.where(ok)[0]
    if idx.size < 30:
        return GlideResult()
    t, keep = np.unique(t_s[idx], return_index=True)
    idx = idx[keep]
    # Flugphase: Bewegung > move_mps (Boden vor Start / nach Landung weg)
    v = np.hypot(np.gradient(e[idx], t), np.gradient(n[idx], t))
    moving = np.where(v > move_mps)[0]
    if moving.size < 30:
        return GlideResult()
    idx = idx[moving[0]:moving[-1] + 1]
    t = t_s[idx]

    tt = np.arange(t[0], t[-1] + 1.0)
    E, N, Z = (np.interp(tt, t, a[idx]) for a in (e, n, z))
    Zs = _smooth(Z, 9)
    vx, vy = np.gradient(_smooth(E, 3)), np.gradient(_smooth(N, 3))
    gs = np.hypot(vx, vy)
    course = np.degrees(np.arctan2(vx, vy))
    dturn = np.degrees(np.angle(np.exp(1j * np.radians(np.diff(course, prepend=course[0])))))
    turn = np.abs(_smooth(dturn, 7))

    circ = turn > circle_turn_dps
    if circ.sum() < 40:
        circ = np.ones_like(circ)
    wx, wy, va = _circle_fit(vx[circ], vy[circ])
    air = np.hypot(vx - wx, vy - wy)

    k = np.arange(tt.size)
    straight = (turn < max_turn_dps) & (k > edge_s) & (k < tt.size - 1 - edge_s)
    res = GlideResult(
        wind_from_deg=float((np.degrees(np.arctan2(wx, wy)) + 180.0) % 360.0),
        wind_kmh=float(np.hypot(wx, wy) * 3.6), airspeed_kmh=va * 3.6,
        track_m=float(gs.sum()), loss_m=float(Z[0] - Z[-1]),
    )
    s0 = None
    for j, g in enumerate(np.r_[straight, False]):
        if g and s0 is None:
            s0 = j
        elif not g and s0 is not None:
            a, b = s0, j - 1
            s0 = None
            if b - a < min_s:
                continue
            d, dl, dh = float(gs[a:b].sum()), float(air[a:b].sum()), float(Zs[a] - Zs[b])
            if dh <= 1.0:          # Steigen / kein Nettosinken: keine Gleitzahl
                continue
            dur = float(b - a)
            res.segments.append(GlideSegment(
                i0=int(idx[np.searchsorted(t, tt[a], side="right") - 1]),
                i1=int(idx[min(np.searchsorted(t, tt[b]), idx.size - 1)]),
                t0_s=float(tt[a]), duration_s=dur, length_m=d, loss_m=dh,
                glide_ground=d / dh, glide_air=dl / dh, sink_mps=dh / dur,
                gs_kmh=d / dur * 3.6, airspeed_kmh=dl / dur * 3.6,
                bearing_deg=float(np.degrees(np.arctan2(E[b] - E[a], N[b] - N[a])) % 360.0)))
    if res.segments:
        D = sum(s.length_m for s in res.segments)
        DL = sum(s.airspeed_kmh / 3.6 * s.duration_s for s in res.segments)
        H = sum(s.loss_m for s in res.segments)
        T = sum(s.duration_s for s in res.segments)
        res.straight = dict(length_m=D, loss_m=H, duration_s=T, glide_ground=D / H, glide_air=DL / H,
                            sink_mps=H / T, gs_kmh=D / T * 3.6, airspeed_kmh=DL / T * 3.6)
    return res
