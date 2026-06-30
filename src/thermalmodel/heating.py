"""Fühlbarer Wärmestrom Q_H = f_H·(1−albedo)·G (treibt die Thermik)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .irradiance import IrradianceCube
from .landcover import LandcoverGrid


@dataclass
class HeatResult:
    times: pd.DatetimeIndex
    Q_H: np.ndarray          # [nt,ny,nx] W/m^2
    Q_H_daymax: np.ndarray   # [ny,nx] Spitzen-Leistung W/m^2
    Q_H_energy: np.ndarray   # [ny,nx] Tages-Energieeintrag Wh/m^2
    label: str               # 'ideal' (klar) oder 'real' (bewölkt)


def compute_heat(irr: IrradianceCube, lc: LandcoverGrid, label: str = "ideal") -> HeatResult:
    factor = (lc.f_H * (1.0 - lc.albedo)).astype(np.float32)   # [ny,nx]
    Q_H = factor[None, :, :] * irr.G                            # [nt,ny,nx]
    daymax = Q_H.max(axis=0)
    dt_h = float((irr.times[1] - irr.times[0]).seconds) / 3600.0 if len(irr.times) > 1 else 1.0
    energy = Q_H.sum(axis=0) * dt_h                             # Wh/m^2
    return HeatResult(times=irr.times, Q_H=Q_H, Q_H_daymax=daymax, Q_H_energy=energy, label=label)


def cumulative_energy_at(heat: HeatResult, hours) -> list[tuple[float, np.ndarray]]:
    """Kumulierter Energieeintrag (Wh/m²) je Tageszeit-Cutoff.

    Summiert Q_H·dt über alle Zeitschritte mit Zeitstempel <= `hour:00` (lokal).
    Gibt [(hour, Feld[ny,nx]), …] in aufsteigender Stunde zurück.
    """
    t = heat.times
    dt_h = float((t[1] - t[0]).seconds) / 3600.0 if len(t) > 1 else 1.0
    day = t[0].normalize()                                      # Mitternacht des Modelltags (tz-aware)
    out = []
    for h in sorted(hours):
        cutoff = day + pd.Timedelta(hours=float(h))
        sel = t <= cutoff                                       # exakte Zeitstempel, nicht nur .hour
        field = (heat.Q_H[sel].sum(axis=0) * dt_h) if sel.any() else np.zeros(heat.Q_H.shape[1:])
        out.append((float(h), field.astype(np.float32)))
    return out
