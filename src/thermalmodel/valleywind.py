"""Phase C (Teil) — anabatische Hangaufwind-Parametrisierung.

Tagsüber strömt erwärmte Luft hangaufwärts (anabatisch). Einfache, terrain-/heizungs-
getriebene Parametrisierung des bodennahen Windfelds (NICHT der synoptische Höhenwind):

  Richtung = bergauf = entgegen dem Aspekt (Aspekt zeigt bergab) → up_az = aspect + 180°.
  Betrag   = max_speed · f(Hangneigung) · f(Q_H)   (steile, heisse Hänge → stärker, gedeckelt).

Wird in D1 nur in der flachen bodennahen Schicht (≲ h_blend) wirksam und geht darüber linear
in den Sondierungswind über. Bewusst eine Parametrisierung (kein gelöstes Windfeld) — die echte
terrain-organisierte Strömung kommt erst mit dem LES (Phase D3+).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .hotspots import _norm01


@dataclass
class ValleyWind:
    u: np.ndarray         # [ny,nx] Ost-Komponente m/s (bodennaher Hangaufwind)
    v: np.ndarray         # [ny,nx] Nord-Komponente m/s
    grid: object
    max_speed: float

    def sample(self, e, n):
        col = int((e - self.grid.west) / self.grid.res)
        row = int((self.grid.north - n) / self.grid.res)
        if 0 <= row < self.grid.ny and 0 <= col < self.grid.nx:
            return float(self.u[row, col]), float(self.v[row, col])
        return 0.0, 0.0


def upslope_field(terrain, q_h, grid, mask, max_speed: float = 3.0,
                  slope_ref_deg: float = 30.0) -> ValleyWind:
    """Bodennahes anabatisches Windfeld (hangaufwärts), skaliert mit Neigung und Heizung."""
    slope_deg = np.degrees(terrain.slope)
    up_az = (terrain.aspect + np.pi) % (2 * np.pi)            # bergauf = entgegen Aspekt
    mag = (max_speed
           * np.clip(np.sin(terrain.slope) / np.sin(np.radians(slope_ref_deg)), 0, 1)
           * _norm01(q_h, mask))
    mag = np.where(slope_deg < 2.0, 0.0, mag)                 # quasi-flach: kein Hangaufwind
    u = mag * np.sin(up_az)                                   # Wind WEHT bergauf
    v = mag * np.cos(up_az)
    return ValleyWind(u=u.astype(np.float32), v=v.astype(np.float32), grid=grid, max_speed=max_speed)
