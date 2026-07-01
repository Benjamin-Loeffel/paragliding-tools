"""Schwellen-/Ampel-Logik von meteo/synoptic.py (ohne Netz, synthetische Eingaben)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "meteo"))
import synoptic as S


def _syn(nh=6, npts=4, frut=None, ch=None, dp_ns=None, dp_we=None):
    def arr(v):
        return np.full((npts, nh), float(v))
    f = {"wind_speed_700hPa": arr(10), "wind_speed_850hPa": arr(10),
         "wind_gusts_10m": arr(12), "wind_speed_10m": arr(10),
         "cape": arr(100), "precipitation": arr(0.0), "weather_code": arr(3),
         "precipitation_probability": arr(0), "cloud_cover": arr(20),
         "lat": np.zeros(npts), "lon": np.zeros(npts)}
    c = {"precipitation": arr(0.0), "weather_code": arr(3),
         "lon": np.linspace(6, 10, npts)}
    if frut:
        f.update(frut)
    if ch:
        c.update(ch)
    return S.Synoptic(date="2026-07-01",
                      times=pd.date_range("2026-07-01 06:00", periods=nh, freq="h"),
                      frutigen=f, ch=c, ch_lats=np.array([46.0, 47.0]),
                      ch_lons=np.array([6.0, 10.0]),
                      dp_ns=np.zeros(nh) if dp_ns is None else np.asarray(dp_ns, float),
                      dp_we=np.zeros(nh) if dp_we is None else np.asarray(dp_we, float))


def test_ampel_thresholds():
    assert S.ampel(9.0, S.FOEHN_DP_HPA) == "alarm"
    assert S.ampel(5.0, S.FOEHN_DP_HPA) == "achtung"
    assert S.ampel(2.0, S.FOEHN_DP_HPA) == "günstig"
    assert S.ampel(float("nan"), S.FOEHN_DP_HPA) == "n/a"


@pytest.mark.parametrize("dp,expected", [(9.0, "alarm"), (5.0, "achtung"), (2.0, "günstig")])
def test_foehn(dp, expected):
    syn = _syn(dp_ns=[dp] * 6)
    assert S.assess_foehn(syn)["ampel"] == expected


def test_foehn_sign_reported():
    assert S.assess_foehn(_syn(dp_ns=[9.0] * 6))["tendenz"] == "Süd"
    assert S.assess_foehn(_syn(dp_ns=[-9.0] * 6))["tendenz"] == "Nord"


def test_wind_upper():
    assert S.assess_wind(_syn(frut={"wind_speed_700hPa": np.full((4, 6), 45.0)}))["ampel"] == "alarm"
    assert S.assess_wind(_syn(frut={"wind_speed_700hPa": np.full((4, 6), 10.0)}))["ampel"] == "günstig"


def test_convection_cape_and_lapse():
    # hohe CAPE -> alarm
    assert S.assess_convection(_syn(frut={"cape": np.full((4, 6), 3000.0)}))["ampel"] == "alarm"
    # gefährlich labil (>= -0.8 °C/100 m, d.h. -0.9) -> alarm auch ohne CAPE
    assert S.assess_convection(_syn(), lapse_c_per_100m=-0.9)["ampel"] == "alarm"
    # Gewitter-Code im Umkreis -> alarm
    wc = np.full((4, 6), 3.0); wc[0, 3] = 95
    assert S.assess_convection(_syn(frut={"weather_code": wc}))["ampel"] == "alarm"
    # ruhig -> günstig
    assert S.assess_convection(_syn(), lapse_c_per_100m=-0.5)["ampel"] == "günstig"


def test_fronts_precip():
    heavy = np.full((4, 6), 5.0)
    assert S.assess_fronts(_syn(ch={"precipitation": heavy}))["ampel"] == "alarm"
    assert S.assess_fronts(_syn())["ampel"] == "günstig"


def test_assess_all_keys():
    a = S.assess_all(_syn())
    assert set(a) == {"wind", "bise", "foehn", "konvektion", "fronten"}
    for v in a.values():
        assert {"phaenomen", "schwelle", "ampel", "begruendung"} <= set(v)
