"""swisstopo STAC-API: Kacheln für eine Bounding-Box finden.

Pro Kachel-Position können mehrere Aufnahmejahre existieren (z. B. swissALTI3D
2019 *und* 2025). Wir wählen den neuesten Jahrgang ('modernste Höhenmodelle').
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import requests

from .config import Config

log = logging.getLogger(__name__)

# z. B. swissalti3d_2025_2613-1160_0.5_2056_5728.tif
_FILENAME_RE = re.compile(
    r"_(?P<year>\d{4})_(?P<tile>\d{4}-\d{4})_(?P<res>[\d.]+)_2056_5728\.tif$"
)


@dataclass
class TileAsset:
    tile_id: str   # "2613-1160"
    year: int
    href: str
    name: str      # Dateiname


def query_items(base: str, collection: str, bbox, session: requests.Session) -> list[dict]:
    """Alle STAC-Items einer Collection in der bbox holen (mit Pagination)."""
    url = f"{base}/collections/{collection}/items"
    params = {"bbox": ",".join(f"{v:.6f}" for v in bbox), "limit": 100}
    items: list[dict] = []
    while url:
        resp = session.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("features", []))
        url = None
        for link in data.get("links", []):
            if link.get("rel") == "next":
                url = link["href"]
                params = None  # next-Link trägt die Query bereits
                break
    return items


def select_tiles(items: list[dict], resolution: float, prefer_year: int | None = None) -> dict[str, TileAsset]:
    """Pro Kachel-ID den passenden Asset (gewünschte Auflösung, neuester Jahrgang) wählen."""
    best: dict[str, TileAsset] = {}
    for item in items:
        for asset in item.get("assets", {}).values():
            href = asset.get("href", "")
            m = _FILENAME_RE.search(href)
            if not m:
                continue
            if abs(float(m.group("res")) - resolution) > 1e-6:
                continue
            tile = m.group("tile")
            year = int(m.group("year"))
            cand = TileAsset(tile, year, href, href.rsplit("/", 1)[-1])
            cur = best.get(tile)
            if cur is None:
                best[tile] = cand
            elif prefer_year is not None:
                # Bevorzugten Jahrgang nehmen, sonst den, der näher dran ist
                if abs(year - prefer_year) < abs(cur.year - prefer_year):
                    best[tile] = cand
            elif year > cur.year:
                best[tile] = cand
    return best


def find_tiles(cfg: Config, bbox, kind: str, session: requests.Session) -> dict[str, TileAsset]:
    """kind = 'dtm' (swissALTI3D) oder 'dsm' (swissSURFACE3D Raster)."""
    collection = cfg.dtm_collection if kind == "dtm" else cfg.dsm_collection
    items = query_items(cfg.stac_base, collection, bbox, session)
    tiles = select_tiles(items, cfg.resolution, cfg.prefer_year)
    years = sorted({t.year for t in tiles.values()})
    log.info("%s: %d Kacheln, Jahrgänge %s", kind.upper(), len(tiles), years)
    return tiles
