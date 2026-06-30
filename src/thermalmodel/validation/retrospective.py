"""Retrospektive Prognose-Validierung: hätte das Modell die guten Thermiktage erkannt?

Für jeden eigenen IGC-Flugtag wird das Wetter rekonstruiert (historisches ICON-Profil +
ERA5-Strahlung, siehe nwp_historical) und eine leichtgewichtige Modell-Tagesgüte an einem
Referenzpunkt (~mediane Hotspot-Höhe) gerechnet (w*-Peak, Ceiling, z_i, XC-Tag). Diese wird
gegen die beobachtete Flugqualität (max. Höhengewinn, Steigrate, Flugdauer) korreliert.

Ehrlich: reale (Reanalyse-)Strahlung + Analyse-Profil = Vorhersagbarkeits-Obergrenze — zeigt, ob
die MODELL-Physik gute/schlechte Tage trennt, ohne Prognosefehler des NWP einzumischen.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from terrainclearance.config import Config as TCConfig
from terrainclearance.geo import CoordTransformer
from terrainclearance.igc_loader import load_igc

from ..boundarylayer import analyze_sounding, cbl_timeseries, strength_at, w_star
from ..nwp_historical import historical_radiation, historical_sounding
from ..xcpotential import logistic
from .igc_climbs import extract_climbs

log = logging.getLogger(__name__)
F_REP, ALBEDO_REP = 0.45, 0.20          # repräsentativer Q_H-Faktor (Wiese/Fels-Mix)


def flight_quality(igc_path, tf) -> dict | None:
    try:
        tr = load_igc(igc_path, TCConfig())
    except Exception:
        return None
    alt = tr.alt.astype(float); t = tr.t_s.astype(float)
    climbs = extract_climbs(tr, tf)
    rates = [c.climb_rate_ms for c in climbs]
    return {"name": Path(igc_path).stem, "date": str(tr.dt[0])[:10],
            "max_alt": float(np.max(alt)), "max_alt_gain": float(np.max(alt) - alt[0]),
            "duration_min": float((t[-1] - t[0]) / 60.0), "n_climbs": len(climbs),
            "mean_climb_ms": float(np.mean(rates)) if rates else 0.0,
            "top_climb_m": float(max((c.alt_top_m for c in climbs), default=alt[0]))}


def model_day_quality(date, lat, lon, ref_elev=1600.0, cache_dir=None) -> dict | None:
    # ref_elev ≈ Steigflug-Basis (nicht Gipfel!), sonst w* an gedeckelten Tagen genullt (ADR-0025).
    try:
        df, cape = historical_sounding(date, lat, lon, hour=12, cache_dir=cache_dir)
        if len(df) < 4:
            return None
        bl = analyze_sounding(df)
        times, g, cloud = historical_radiation(date, lat, lon, cache_dir=cache_dir)
    except Exception as exc:
        log.warning("Hist-Wetter %s fehlgeschlagen: %s", date, exc)
        return None
    qh = F_REP * (1.0 - ALBEDO_REP) * g                       # repräsentativer Q_H(t) [W/m²]
    cbl = cbl_timeseries(bl, times, qh)
    B_max = strength_at(bl, ref_elev, 300.0)["z_i_m"]         # Arbeitsband (parcel_top)
    wstar = np.array([w_star(qh[i], B_max * cbl["growth"][i]) for i in range(len(times))])
    wstar_peak = float(np.max(wstar)) if wstar.size else 0.0
    wind_bl_kmh = float(np.interp(2500.0, bl.wind_height_m, bl.wind_speed_ms)
                        if len(bl.wind_height_m) else 0.0) * 3.6
    xc = ((2 * logistic(wstar_peak, 1.55, 5) + logistic(B_max, 400.0, 4)) / 3.0
          * (1 - logistic(wind_bl_kmh, 16.0, 6)) * 100.0)
    hh = times.hour
    cloud_mid = float(np.nanmean(cloud[(hh >= 11) & (hh <= 16)]))
    return {"date": date, "wstar_peak": wstar_peak, "band_m": B_max,
            "z_i_peak_amsl": float(cbl["z_i_peak_amsl"]), "xc_day": float(xc),
            "cape": cape, "wind_bl_kmh": wind_bl_kmh, "cloud_mid": cloud_mid}


# XContest-Rekordtage im Niesen-Gebiet (8 km), aus der eingeloggten Browser-Session abgelesen
# (2026-06-30; XContest hat keine API, Bot-requests → HTTP 401). Wert = max. XC-Distanz [km] des Tages.
# Komplementäres Validierungs-Target: hätte das Modell diese Big-Days als gut erkannt?
XCONTEST_BIGDAYS = {"2026-06-18": 306, "2026-06-21": 314, "2026-05-27": 336, "2026-05-23": 337,
                    "2026-05-26": 251, "2025-05-01": 316, "2025-04-30": 296, "2024-07-20": 335,
                    "2024-07-30": 331, "2024-05-11": 314}


def validate_xcontest_bigdays(lat, lon, ref_elev=1600.0, cache_dir=None) -> list[dict]:
    """Modell-Tagesgüte an XContest-Rekordtagen (sollte hoch sein, wenn das Modell gut ist)."""
    recs = []
    for d, km in sorted(XCONTEST_BIGDAYS.items()):
        m = model_day_quality(d, lat, lon, ref_elev, cache_dir)
        if m:
            recs.append({"date": d, "max_km": km, **m})
    return recs


def run_retrospective(igc_dir, lat, lon, ref_elev=1600.0, cache_dir=None) -> dict:
    """ref_elev ≈ mediane Steigflug-Basis (nicht Gipfel!), sonst wird w* an gedeckelten Tagen
    künstlich genullt."""
    tf = CoordTransformer(use_network=False)
    flights = [q for q in (flight_quality(p, tf) for p in sorted(Path(igc_dir).glob("*.igc"))) if q]
    dates = sorted({f["date"] for f in flights})
    mq = {d: model_day_quality(d, lat, lon, ref_elev, cache_dir) for d in dates}
    return {"flights": flights, "model": mq}


def summarize(result, min_climbs=1) -> list[dict]:
    """Je Flugtag: bester Thermikflug (≥min_climbs Steigsegmente) + Modell-Tagesgüte."""
    from collections import defaultdict
    byd = defaultdict(list)
    for f in result["flights"]:
        if f["n_climbs"] >= min_climbs:
            byd[f["date"]].append(f)
    recs = []
    for d in sorted(byd):
        m = result["model"].get(d)
        if not m:
            continue
        best = max(byd[d], key=lambda x: x["top_climb_m"])
        recs.append({"date": d, **{f"m_{k}": v for k, v in m.items() if k != "date"},
                     "f_top": best["top_climb_m"], "f_gain": best["max_alt_gain"],
                     "f_climb": best["mean_climb_ms"],
                     "f_dur": sum(x["duration_min"] for x in byd[d])})
    return recs


def spearman_table(recs) -> dict:
    from scipy.stats import spearmanr
    out = {}
    for mk in ("m_xc_day", "m_wstar_peak", "m_z_i_peak_amsl"):
        for fk in ("f_top", "f_gain", "f_dur"):
            out[f"{mk}~{fk}"] = float(spearmanr([r[mk] for r in recs], [r[fk] for r in recs]).correlation)
    return out


def plot_retrospective(recs, path, dpi=170):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import spearmanr
    x = [r["m_z_i_peak_amsl"] for r in recs]; y = [r["f_top"] for r in recs]
    c = [r["m_xc_day"] for r in recs]
    rho = spearmanr(x, y).correlation
    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(x, y, c=c, cmap="viridis", s=95, edgecolor="k", vmin=0, vmax=100)
    for r in recs:
        ax.annotate(r["date"][5:], (r["m_z_i_peak_amsl"], r["f_top"]), fontsize=7, alpha=0.7)
    fig.colorbar(sc, label="Modell XC-Tagesgüte [%]")
    ax.set_xlabel("Modell z_i-Peak (CBL-Top) [m AMSL]"); ax.set_ylabel("Flug max. Thermik-Top [m AMSL]")
    ax.set_title(f"Retrospektive Validierung (eigene IGC, n={len(recs)}) — Spearman z_i~Top = {rho:+.2f}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return path
