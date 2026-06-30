"""Boden-Kalibrierung auf synthetischen Tracks."""

from pathlib import Path

import numpy as np
from rasterio.transform import from_origin

from terrainclearance.calibrate import calibrate_altitude
from terrainclearance.config import Config
from terrainclearance.igc_loader import FlightTrack
from terrainclearance.tiles import Sampler


def flat_dtm(elev=500.0):
    arr = np.full((400, 400), elev, dtype=np.float32)
    return Sampler(arr, from_origin(1000.0, 2000.0, 0.5, 0.5), -9999.0)


def make_track(alt, e, n, t_s):
    dt = np.array([np.datetime64("2026-06-01T00:00:00") + np.timedelta64(int(s), "s") for s in t_s],
                  dtype="datetime64[s]")
    z = np.asarray(alt, float)
    return FlightTrack(
        name="syn", path=Path("syn.igc"), dt=dt, t_s=np.asarray(t_s, float),
        lat=np.full(z.size, 46.5), lon=np.full(z.size, 7.6),
        gps_alt=z, pressure_alt=z, alt=z, alt_source="gnss",
        valid=np.ones(z.size, bool), header={},
    )


def test_offset_recovered_from_takeoff_ground():
    n = 120
    t_s = np.arange(n)
    true_offset = 12.0          # GPS liest 12 m zu hoch
    e = np.full(n, 1050.0)
    n_coord = np.full(n, 1950.0)
    # 40 s stehend am Boden, dann wegfliegen + steigen
    e[40:] = 1050.0 + np.arange(n - 40) * 5.0
    alt = np.full(n, 500.0 + true_offset)
    alt[40:] = 500.0 + true_offset + np.arange(n - 40) * 3.0

    track = make_track(alt, e, n_coord, t_s)
    cal = calibrate_altitude(track, e, n_coord, flat_dtm(500.0), Config())

    assert cal.method in ("ground_takeoff", "ground_both")
    assert abs(cal.offset_m - (-true_offset)) < 0.5
    # Nach Kalibrierung steht der Pilot am Boden auf ~DTM-Höhe
    assert abs(cal.apply(track.alt)[0] - 500.0) < 0.5


def test_no_ground_segment_low_confidence():
    n = 100
    t_s = np.arange(n)
    e = 1050.0 + np.arange(n) * 6.0      # durchgehend in Bewegung
    n_coord = np.full(n, 1950.0)
    alt = np.full(n, 800.0)
    track = make_track(alt, e, n_coord, t_s)
    cal = calibrate_altitude(track, e, n_coord, flat_dtm(500.0), Config())
    assert cal.method == "none"
    assert cal.confidence == "low"
    assert cal.offset_m == 0.0
