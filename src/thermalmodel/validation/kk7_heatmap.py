"""thermal.kk7.ch *Thermals-Heatmap* (Raster-Tiles) als kontinuierliches Validierungs-Target.

Reicher als die 18 Vektor-Hotspots: die Thermals-Kacheln (`/tiles/thermals_{cat}/{z}/{x}/{y}.png`,
TMS, EPSG:3857, maxNativeZoom 12) sind ein flächiges Thermik-Antreff-Wahrscheinlichkeitsraster
(KDE über viele IGC-Flüge). Wir holen die Kacheln über dem Gebiet, dekodieren die Jet-artige
Farbskala (Dunkelblau→Blau→Cyan→Grün→Gelb→Rot) über den Farbton in eine relative Intensität 0..1
und reprojizieren von WebMercator aufs LV95-Modellgitter.

Datenlizenz: CC-BY-NC-SA 4.0, © M. von Känel, thermal.kk7.ch (src-Param bei /tiles/ angehängt).
category='{season}_{timeofday}', z. B. jul_07 (Sommer-Mittag).
"""

from __future__ import annotations

import io
import logging
import math
from pathlib import Path

import numpy as np
import requests

from .. import config as _cfg
from ..reproject import lv95_to_wgs84

log = logging.getLogger(__name__)
TILES = "https://thermal.kk7.ch/tiles/thermals_{cat}/{z}/{x}/{y}.png"


def _deg2tile(lat, lon, z):
    n = 2.0 ** z
    xt = (lon + 180.0) / 360.0 * n
    yt = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return xt, yt


def _decode_intensity(rgba):
    """RGBA-Kachel → Intensität 0..1 (über Farbton; Dunkelblau≈0 … Rot≈1). NaN wo transparent."""
    from matplotlib.colors import rgb_to_hsv
    rgb = rgba[:, :, :3].astype(float) / 255.0
    a = rgba[:, :, 3].astype(float)
    hsv = rgb_to_hsv(rgb)
    hue = hsv[:, :, 0] * 360.0
    val = hsv[:, :, 2]
    inten = np.clip((240.0 - hue) / 240.0, 0.0, 1.0)   # Blau(240°)→0, Rot(0°)→1
    inten = inten * np.clip(val / 0.25, 0.0, 1.0)      # sehr dunkle (kaum Daten) abschwächen
    inten[a < 30] = np.nan                              # transparent = keine Flugdaten
    return inten


def plot_heatmap(grid, mask, dtm, kk7, path, title, dpi=160):
    """Dekodierte kk7-Thermik-Dichte über Hillshade."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ..viz import draw_hillshade
    fig, ax = plt.subplots(figsize=(10, 12))
    ext = draw_hillshade(ax, dtm, grid)
    im = ax.imshow(np.where(mask & np.isfinite(kk7), kk7, np.nan), cmap="viridis",
                   extent=ext, origin="upper", alpha=0.8, vmin=0, vmax=1, interpolation="bilinear")
    fig.colorbar(im, ax=ax, shrink=0.6, label="kk7 Thermik-Dichte (dekodiert, 0–1)")
    ax.set_title(title); ax.set_xlabel("LV95 Ost [m]"); ax.set_ylabel("LV95 Nord [m]"); ax.set_aspect("equal")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return path


def fetch_thermals_intensity(cfg, grid, session=None, category="jul_07", zoom=12) -> np.ndarray:
    """kk7-Thermik-Dichte (0..1) aufs Modellgitter; NaN wo keine kk7-Daten. Gecacht (npz)."""
    s = session or requests.Session()
    cache = Path(cfg.cache_dir) / "thermal" / f"kk7_thermals_{category}_z{zoom}_{grid.nx}x{grid.ny}.npz"
    if cache.exists():
        log.info("kk7-Heatmap aus Cache: %s", cache.name)
        return np.load(cache)["field"]

    w, s_, e, n = grid.bounds()
    lons, lats = lv95_to_wgs84(np.array([w, e, w, e]), np.array([s_, s_, n, n]))
    xts, yts = [], []
    for lo, la in zip(lons, lats):
        xt, yt = _deg2tile(la, lo, zoom); xts.append(xt); yts.append(yt)
    x0, x1 = int(np.floor(min(xts))), int(np.floor(max(xts)))
    y0, y1 = int(np.floor(min(yts))), int(np.floor(max(yts)))
    ntx, nty = x1 - x0 + 1, y1 - y0 + 1
    mosaic = np.full((nty * 256, ntx * 256), np.nan)
    ntot = 2 ** zoom
    for xi in range(x0, x1 + 1):
        for yi in range(y0, y1 + 1):
            url = TILES.format(cat=category, z=zoom, x=xi, y=ntot - 1 - yi) + "?src=thermalmodel"
            try:
                r = s.get(url, timeout=30)
                if r.status_code != 200:
                    continue
                from PIL import Image
                rgba = np.array(Image.open(io.BytesIO(r.content)).convert("RGBA"))
                tile = _decode_intensity(rgba)
            except Exception as exc:
                log.warning("kk7-Tile %d/%d/%d: %s", zoom, xi, yi, exc); continue
            mosaic[(yi - y0) * 256:(yi - y0 + 1) * 256, (xi - x0) * 256:(xi - x0 + 1) * 256] = tile

    # Modellgitter-Zentren → WebMercator-Pixel im Mosaik → Nearest-Sampling
    Ec, Nc = grid.cell_centers()
    glon, glat = lv95_to_wgs84(Ec.ravel(), Nc.ravel())
    field = np.full(glon.shape, np.nan)
    for i in range(glon.size):
        xt, yt = _deg2tile(glat[i], glon[i], zoom)
        px = int(round((xt - x0) * 256)); py = int(round((yt - y0) * 256))
        if 0 <= py < mosaic.shape[0] and 0 <= px < mosaic.shape[1]:
            field[i] = mosaic[py, px]
    field = field.reshape(grid.shape).astype(np.float32)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, field=field)
    log.info("kk7-Heatmap %s: %d Kacheln, %.0f%% des Gebiets mit Daten",
             category, ntx * nty, 100 * np.isfinite(field[grid.shape[0] // 2]).mean())
    return field
