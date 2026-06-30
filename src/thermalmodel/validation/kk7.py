"""thermal.kk7.ch-Hotspots als unabhängiges, mehr-Piloten-basiertes Validierungs-Target.

Offene REST-API (per Recherche verifiziert, kein Login/Key):
  GET /api/hotspots/geojson/{category}/{latmin},{lonmin},{latmax},{lonmax}?limit=N
  category = '{season}_{timeofday}', season∈{all,jan,apr,jul,oct},
  timeofday∈{all,04,07,10} (04=Morgen, 07=Mittag, 10=Abend). KEIN &src= an /api/hotspots!
properties.probability ∈ 0..1 (CSV-Variante: 0..100). Hotspot = Kreis 250 m Radius.
Methodik: KDE über reale IGC-XC-Flüge vieler Piloten; nur Gebiete mit ~20 Flügen/100 m.

Daten © Michael von Känel, thermal.kk7.ch (Attribution bei wissenschaftlicher Nutzung).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import requests

from terrainclearance.geo import CoordTransformer

log = logging.getLogger(__name__)
KK7_API = "https://thermal.kk7.ch/api/hotspots/geojson/{cat}/{bbox}"


@dataclass
class Kk7Hotspot:
    lat: float
    lon: float
    e: float
    n: float
    prob: float       # 0..1
    alt_m: float


def fetch_kk7_hotspots(bbox_wgs84, category: str = "all_all", tf: CoordTransformer | None = None,
                       cache_dir=None, session: requests.Session | None = None,
                       limit: int = 2000) -> list[Kk7Hotspot]:
    """kk7-Hotspots für bbox_wgs84=(lon_min,lat_min,lon_max,lat_max). Gecacht je category."""
    lon0, lat0, lon1, lat1 = bbox_wgs84
    bbox = f"{lat0:.5f},{lon0:.5f},{lat1:.5f},{lon1:.5f}"   # kk7: lat,lon,lat,lon
    url = KK7_API.format(cat=category, bbox=bbox) + f"?limit={limit}"

    data = None
    cache = None
    if cache_dir is not None:
        cache = Path(cache_dir) / "thermal" / f"kk7_{category}_{bbox}.json"
        if cache.exists():
            data = json.loads(cache.read_text(encoding="utf-8"))
            log.info("kk7 aus Cache: %s", cache.name)
    if data is None:
        r = (session or requests).get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(data), encoding="utf-8")
        log.info("kk7 geladen (%s): %d Hotspots", category, len(data.get("features", [])))

    tf = tf or CoordTransformer(use_network=False)
    out = []
    for f in data.get("features", []):
        c = f["geometry"]["coordinates"]
        lon, lat = float(c[0]), float(c[1])
        alt = float(c[2]) if len(c) > 2 else float(f.get("properties", {}).get("altitude_m_AMSL", 0.0))
        prob = float(f.get("properties", {}).get("probability", 1.0))
        if prob > 1.0:
            prob /= 100.0
        e, n = tf.to_lv95(lon, lat)
        out.append(Kk7Hotspot(lat=lat, lon=lon, e=float(e), n=float(n), prob=prob, alt_m=alt))
    return out
