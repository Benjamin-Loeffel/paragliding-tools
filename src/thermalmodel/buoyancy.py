"""D0 — statisches Thermik-Quell-Proxy (Auftriebs-/Trigger-Wahrscheinlichkeit).

Schnellstes gegen kk7/IGC prüfbares Produkt. Kombiniert literatur-fundierte Säulen der
Thermik-Auslösung (XC Mag / SkyNomad / Reichmann; w*-Modell Allen/Lenschow), aber
DATENGETRIEBEN gewichtet (Ablation gegen 42 IGC-Steigflüge + 18 kk7-Hotspots):

  HEIZUNG (Collector)   Q_H-Tagesenergie — integriert Sonne/Aspekt/Schatten korrekt.
  KONVEXITÄT (Trigger)  Grate/Sporne/Kuppen lösen ab (AUC einzeln ~0.60).
  ASPEKT zur Sonne      Ausrichtung SSW — empirisch prädiktiv (Piloten bevorzugen Sonnenhänge).
  HANGBAND              weiche Gauss-Gewichtung ~28° (stärkster Einzelprädiktor, AUC ~0.67).

VERWORFEN (Ablation): ein Triggerlinien-/Kanten-Term (Q_H-Gradient) hatte AUC ~0.5 (kk7 <0.5),
also keine Vorhersagekraft auf dieser Skala → Default-Gewicht 0 (siehe ADR-0013). Wasser/Schnee
= thermische Totzonen → 0. Ergebnis: relatives Wahrscheinlichkeitsfeld [0,1].
Noch fehlend (Phase C): Lee/Luv-Windexposition, Bodenfeuchte-Dynamik.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import config as C
from .config import ThermalConfig
from .hotspots import _norm01


@dataclass
class ThermalSource:
    prob: np.ndarray              # [ny,nx] 0..1 relative Quell-Wahrscheinlichkeit
    components: dict              # benannte normierte Teilfelder (Nachvollziehbarkeit)
    weights: dict


def thermal_source_field(cfg: ThermalConfig, terrain, heat, lc, mask, weights=None) -> ThermalSource:
    slope_deg = np.degrees(terrain.slope)
    w = {"heat": cfg.d0_w_heat, "conv": cfg.d0_w_conv, "aspect": cfg.d0_w_aspect,
         "slope": cfg.d0_w_slope, "edge": cfg.d0_w_edge}
    if weights:
        w.update(weights)

    heat_n = _norm01(heat.Q_H_energy, mask)
    conv_n = _norm01(np.clip(terrain.curvature, 0, None), mask)
    aspect_n = (np.clip(np.cos(terrain.aspect - np.radians(cfg.d0_aspect_pref_deg)), 0, None)
                * np.clip(slope_deg / 10.0, 0, 1)).astype(np.float32)
    slope_w = np.exp(-(((slope_deg - cfg.d0_slope_opt_deg) / cfg.d0_slope_width_deg) ** 2)).astype(np.float32)
    gy, gx = np.gradient(heat.Q_H_energy.astype(float))
    edge_n = _norm01(np.hypot(gx, gy), mask)

    comp = {"heat": heat_n, "convex": conv_n, "aspect": aspect_n, "slope": slope_w, "edge": edge_n}
    prob = (w["heat"] * heat_n + w["conv"] * conv_n + w["aspect"] * aspect_n
            + w["slope"] * slope_w + w["edge"] * edge_n)

    dead = np.isin(lc.class_id, [C.LC_WATER, C.LC_SNOW])
    prob = np.where(dead, 0.0, prob)
    prob = _norm01(prob, mask)
    prob = np.where(mask, prob, np.nan).astype(np.float32)
    return ThermalSource(prob=prob, components=comp, weights=w)
