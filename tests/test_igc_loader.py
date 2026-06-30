"""IGC-Laden für beide Recorder-Layouts (XC Tracer + Handy/XCTrack)."""

from pathlib import Path

import numpy as np
import pytest

from terrainclearance.config import Config
from terrainclearance.igc_loader import load_igc

IGC_DIR = Path(__file__).resolve().parent.parent / "source" / "igc"
XCTRACER = IGC_DIR / "2026-06-25-XTR-CF51C5E54B32-01.IGC"
PHONE = IGC_DIR / "2026-06-19-XCT-BLO-02.igc"


@pytest.mark.skipif(not XCTRACER.exists(), reason="IGC-Beispiel fehlt")
def test_xctracer_loads_gnss():
    t = load_igc(XCTRACER, Config())
    assert t.n > 1000
    assert t.alt_source == "gnss"
    assert np.isfinite(t.alt).all()
    assert t.header.get("gnss_altitude") == "GEO"


@pytest.mark.skipif(not PHONE.exists(), reason="IGC-Beispiel fehlt")
def test_phone_uses_gnss_despite_zero_pressure():
    t = load_igc(PHONE, Config())
    # Handy: Druckhöhe = 0 (kein Barosensor), GNSS aber brauchbar (~1726 m am Boden)
    assert t.alt_source == "gnss"
    assert float(np.max(t.pressure_alt)) == 0.0
    assert 1000 < t.alt[0] < 3000


@pytest.mark.skipif(not PHONE.exists(), reason="IGC-Beispiel fehlt")
def test_datetime_is_utc_and_monotonic():
    t = load_igc(PHONE, Config())
    assert t.dt.dtype == np.dtype("datetime64[s]")
    assert (np.diff(t.t_s) >= 0).all()
