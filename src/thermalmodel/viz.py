"""Gemeinsame Plot-Helfer — v. a. ein AUFGEHELLTES Hillshade-Relief.

Damit die farbigen Overlays (viridis/inferno) und Wind-Streamlines (cividis) gut gegen das Relief
kontrastieren, wird der Schummerungs-Graukeil auf einen hellen Bereich [~0.55, 1.0] gestaucht
(kein Schwarz). Projektweit über `draw_hillshade` genutzt.
"""

from __future__ import annotations

import numpy as np


def light_hillshade(dtm, res, vert_exag: float = 2.0, lo: float = 0.6):
    """Hillshade in einen hellen Graubereich [lo, 1.0] gestaucht (kein dunkler Hintergrund)."""
    from matplotlib.colors import LightSource
    z = np.where(np.isfinite(dtm), dtm, np.nan)
    hs = LightSource(azdeg=315, altdeg=45).hillshade(z, vert_exag=vert_exag, dx=res, dy=res)
    return lo + (1.0 - lo) * hs


def draw_hillshade(ax, dtm, grid, vert_exag: float = 2.0):
    """Helles Relief als Hintergrund auf ax zeichnen (gibt extent zurück)."""
    w, s, e, n = grid.bounds()
    hs = light_hillshade(dtm, grid.res, vert_exag)
    ax.imshow(hs, cmap="gray", vmin=0.0, vmax=1.0, extent=[w, e, s, n],
              origin="upper", interpolation="bilinear")
    return [w, e, s, n]
