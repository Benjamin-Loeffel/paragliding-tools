"""Gleitzahlen der Geradeausstücke (glide.py)."""

import numpy as np

from terrainclearance.glide import glide_segments


def _flug(wind=(0.0, 0.0), va=9.0, sink=1.0):
    """60 s geradeaus nach Osten, 2 Vollkreise (je 36 s), 60 s geradeaus nach Norden; 1-s-Fixe."""
    hdg = np.r_[np.full(60, 90.0), 90.0 + np.arange(72) * 10.0, np.full(60, 0.0)]
    vx = va * np.sin(np.radians(hdg)) + wind[0]
    vy = va * np.cos(np.radians(hdg)) + wind[1]
    e, n = np.cumsum(vx), np.cumsum(vy)
    t = np.arange(hdg.size, dtype=float)
    z = 1500.0 - sink * t
    return e, n, z, t


def test_still_gleitzahl_gleich_fahrt_durch_sinken():
    e, n, z, t = _flug(va=9.0, sink=1.0)
    r = glide_segments(e, n, z, t, edge_s=5)
    assert len(r.segments) == 2
    for s in r.segments:
        assert abs(s.glide_ground - 9.0) < 0.3
        assert abs(s.glide_air - 9.0) < 0.3
    assert r.wind_kmh < 1.0


def test_wind_aus_kreisen_korrigiert_luftgleitzahl():
    # Wind 3 m/s nach Osten (= aus Westen): Ost-Stück über Grund besser, in der Luft gleich
    e, n, z, t = _flug(wind=(3.0, 0.0), va=9.0, sink=1.0)
    r = glide_segments(e, n, z, t, edge_s=5)
    assert abs(r.wind_kmh - 10.8) < 1.5
    assert abs(r.wind_from_deg - 270.0) < 10.0
    ost = r.segments[0]
    assert ost.glide_ground > 11.0
    assert abs(ost.glide_air - 9.0) < 0.5


def test_steigen_gibt_keine_gleitzahl():
    e, n, z, t = _flug(sink=-0.5)
    assert glide_segments(e, n, z, t, edge_s=5).segments == []
