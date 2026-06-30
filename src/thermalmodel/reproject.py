"""Koordinaten-Hilfen (terrainclearance.geo macht nur WGS84->LV95)."""

from __future__ import annotations

import numpy as np
from pyproj import Transformer

_TO_WGS = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)


def lv95_to_wgs84(E, N):
    lon, lat = _TO_WGS.transform(np.asarray(E), np.asarray(N))
    return np.asarray(lon), np.asarray(lat)
