"""Koordinatentransformation WGS84 (EPSG:4326) -> Schweizer LV95 (EPSG:2056).

Vektorisiert über numpy-Arrays. Wenn das PROJ-Netzwerk aktiv ist und das
CHENYX06-Grid verfügbar ist, erreicht pyproj ~cm-Genauigkeit; sonst greift eine
Helmert-Näherung (~1–2 m), was gegenüber einem 0.5-m-DTM unkritisch ist.
"""

from __future__ import annotations

import logging

import numpy as np
import pyproj
from pyproj import Transformer

log = logging.getLogger(__name__)


class CoordTransformer:
    def __init__(self, use_network: bool = True):
        if use_network:
            try:
                pyproj.network.set_network_enabled(True)
            except Exception as exc:  # pragma: no cover - netzwerkabhängig
                log.warning("PROJ-Netzwerk konnte nicht aktiviert werden: %s", exc)
        self.transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
        self.description = self.transformer.description
        log.info("Transformations-Pipeline: %s", self.description)

    def to_lv95(self, lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """lon/lat (Grad) -> (easting, northing) in Metern (LV95)."""
        e, n = self.transformer.transform(np.asarray(lon), np.asarray(lat))
        return np.asarray(e, dtype=float), np.asarray(n, dtype=float)
