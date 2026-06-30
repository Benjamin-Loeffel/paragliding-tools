"""STAC-Kachelauswahl: neuester Jahrgang, richtige Auflösung."""

from terrainclearance.stac import select_tiles

BASE = "https://data.geo.admin.ch/ch.swisstopo.swissalti3d/"


def _item(href):
    return {"assets": {"a": {"href": href}}}


def test_select_newest_year_and_resolution():
    items = [
        _item(BASE + "swissalti3d_2019_2613-1160/swissalti3d_2019_2613-1160_0.5_2056_5728.tif"),
        _item(BASE + "swissalti3d_2025_2613-1160/swissalti3d_2025_2613-1160_0.5_2056_5728.tif"),
        _item(BASE + "swissalti3d_2025_2613-1160/swissalti3d_2025_2613-1160_2_2056_5728.tif"),
        _item(BASE + "swissalti3d_2019_2614-1160/swissalti3d_2019_2614-1160_0.5_2056_5728.tif"),
    ]
    sel = select_tiles(items, resolution=0.5)
    assert set(sel) == {"2613-1160", "2614-1160"}
    # Mehrjahres-Kachel: neuester Jahrgang gewinnt
    assert sel["2613-1160"].year == 2025
    # 2-m-Variante wird bei resolution=0.5 ignoriert
    assert sel["2613-1160"].name.endswith("_0.5_2056_5728.tif")
    # Einzeljahr-Kachel bleibt erhalten
    assert sel["2614-1160"].year == 2019


def test_select_2m():
    items = [
        _item(BASE + "swissalti3d_2025_2613-1160/swissalti3d_2025_2613-1160_0.5_2056_5728.tif"),
        _item(BASE + "swissalti3d_2025_2613-1160/swissalti3d_2025_2613-1160_2_2056_5728.tif"),
    ]
    sel = select_tiles(items, resolution=2.0)
    assert sel["2613-1160"].name.endswith("_2_2056_5728.tif")


def test_prefer_year():
    items = [
        _item(BASE + "swissalti3d_2019_2613-1160/swissalti3d_2019_2613-1160_0.5_2056_5728.tif"),
        _item(BASE + "swissalti3d_2025_2613-1160/swissalti3d_2025_2613-1160_0.5_2056_5728.tif"),
    ]
    sel = select_tiles(items, resolution=0.5, prefer_year=2019)
    assert sel["2613-1160"].year == 2019
