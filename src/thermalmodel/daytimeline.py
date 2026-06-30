"""Tages-Timeline: 'Wann starten?' + Wind-Zerstörung — die Synthese der Kernfragen.

Aggregiert über den Tag (30-min-Achse):
  w*(t)        — Thermikstärke (Median über Hotspots, mit z_i(t)-Bandtiefe + realem Q_H(t)),
  z_i(t)       — CBL-/Arbeitsband-Höhe (Encroachment),
  Wind_BL(t)   — Domänenmittel-Windgeschwindigkeit @2500 m (ICON),
  Scherung(t)  — |V(3200 m) − V(10 m)| (Domänenmittel),
  Zerstörung   — Flag: Wind_BL > 7 m/s (~25 kt → Thermik zerblasen, Allen/RASP) oder starke Scherung,
  XC(t)        — Tagesgüte (soaringmeteo-Logistik-Blend) je Zeit.
Daraus das optimale Startfenster (brauchbar & nicht zerstört, w* nahe Maximum).
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from .boundarylayer import cbl_timeseries, strength_at, w_star
from .xcpotential import logistic

log = logging.getLogger(__name__)
WIND_DESTROY_MS = 7.0          # ~25 kt: Thermik wird zerblasen (Allen w*→0; FAA/RASP)


def _domain_mean_wind(wf):
    """Domänenmittel-Windprofil (über Stützpunkte): speed@Höhe(t), 10m, und Scherung."""
    um = wf.u.mean(axis=0); vm = wf.v.mean(axis=0)         # [nlvl,nh]
    u10 = wf.u10.mean(axis=0); v10 = wf.v10.mean(axis=0)   # [nh]
    return um, vm, u10, v10


def compute_day_timeline(cfg, res, bl, wf) -> dict:
    grid, mask = res["grid"], res["mask"]
    heat = res["real"]["heat"] if "heat" in res.get("real", {}) else res["heat"]
    hotspots = res["hotspots"]
    times = heat.times
    hrs = times.hour + times.minute / 60.0
    qh_mean = np.array([heat.Q_H[i][mask].mean() for i in range(len(times))])
    cbl = cbl_timeseries(bl, times, qh_mean)
    growth = cbl["growth"]

    um, vm, u10, v10 = _domain_mean_wind(wf)
    wh = wf.times.hour + wf.times.minute / 60.0
    lvl = wf.level_h
    # Windgeschw. @2500 m und @~3200 m (oberstes Niveau) je Wind-Stunde
    def spd_at(h_amsl):
        iu = np.array([np.interp(h_amsl, lvl, um[:, j]) for j in range(um.shape[1])])
        iv = np.array([np.interp(h_amsl, lvl, vm[:, j]) for j in range(vm.shape[1])])
        return np.hypot(iu, iv)
    s2500 = spd_at(2500.0); stop = np.hypot(um[-1], vm[-1]); s10 = np.hypot(u10, v10)
    shear = np.hypot(um[-1] - u10, vm[-1] - v10)             # |V_top − V_10m|

    nt = len(times)
    wstar = np.zeros(nt); band = np.zeros(nt); wind_bl = np.zeros(nt); shr = np.zeros(nt)
    for i in range(nt):
        ws = [strength_at(bl, h.elev_m, float(heat.Q_H[i][min(max(int((grid.north-h.n)/grid.res),0),grid.ny-1),
                                                            min(max(int((h.e-grid.west)/grid.res),0),grid.nx-1)]),
                          band_scale=float(growth[i]))["w_star_ms"] for h in hotspots]
        wstar[i] = float(np.median(ws))
        band[i] = float(np.median([strength_at(bl, h.elev_m, 300.0, band_scale=float(growth[i]))["z_i_m"]
                                   for h in hotspots]))
        wind_bl[i] = float(np.interp(hrs[i], wh, s2500))
        shr[i] = float(np.interp(hrs[i], wh, shear))
    xc = (2 * logistic(wstar, 1.55, 5) + logistic(band, 400.0, 4)) / 3.0 \
        * (1 - logistic(wind_bl * 3.6, 16.0, 6)) * 100.0
    viable = (wind_bl < WIND_DESTROY_MS) & (wstar >= 1.0)
    return {"hrs": hrs, "wstar": wstar, "z_i_amsl": cbl["z_i_amsl"], "band": band,
            "wind_bl": wind_bl, "shear": shr, "xc": xc, "viable": viable,
            "qh": qh_mean, "cloud_destroy_ms": WIND_DESTROY_MS}


def optimal_window(tl) -> tuple:
    """Bestes Startfenster: brauchbare Zeiten, gewichtet nach XC; gibt (start,end,peak_h)."""
    hrs, xc, viable = tl["hrs"], tl["xc"], tl["viable"]
    good = viable & (xc >= 0.6 * np.nanmax(xc))
    if not good.any():
        good = viable
    if not good.any():
        return None
    gh = hrs[good]
    return float(gh.min()), float(gh.max()), float(hrs[np.argmax(np.where(viable, xc, -1))])


def plot_day_timeline(tl, path, title, dpi=180):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h = tl["hrs"]
    fig, axes = plt.subplots(4, 1, figsize=(12, 13), sharex=True, constrained_layout=True)
    win = optimal_window(tl)

    ax = axes[0]
    ax.fill_between(h, tl["xc"], color="#3b528b", alpha=0.35); ax.plot(h, tl["xc"], color="#3b528b", lw=2)
    ax.set_ylabel("XC potential [%]"); ax.set_ylim(0, 100); ax.set_title("Day quality (flight potential)")

    ax = axes[1]
    ax.plot(h, tl["wstar"], color="#21918c", lw=2, label="w* (median hotspots)")
    ax.axhline(1.5, ls=":", c="grey", lw=1); ax.axhline(2.0, ls=":", c="grey", lw=1)
    ax.set_ylabel("w* [m/s]"); ax.legend(loc="upper left", fontsize=9)
    axb = ax.twinx(); axb.plot(h, tl["z_i_amsl"], color="#440154", lw=2, label="z_i (CBL) AMSL")
    axb.set_ylabel("z_i [m AMSL]", color="#440154"); axb.legend(loc="upper right", fontsize=9)
    ax.set_title("Thermal strength w*(t) + mixing layer z_i(t)")

    ax = axes[2]
    ax.plot(h, tl["wind_bl"] * 3.6, color="#5ec962", lw=2, label="Wind BL @2500 m")
    ax.plot(h, tl["shear"] * 3.6, color="#fde725", lw=2, label="Shear |V_top−V_10m|")
    ax.axhline(tl["cloud_destroy_ms"] * 3.6, ls="--", c="red", lw=1.4,
               label="Destruction threshold (~25 km/h)")
    ax.set_ylabel("Wind [km/h]"); ax.legend(loc="upper left", fontsize=9)
    ax.set_title("Wind & shear — thermal destruction")

    ax = axes[3]
    ax.fill_between(h, 0, 1, where=tl["viable"], color="#5ec962", alpha=0.3, transform=ax.get_xaxis_transform())
    ax.plot(h, tl["qh"], color="#e8702a", lw=2, label="Q_H (real) [W/m²]")
    ax.set_ylabel("Q_H [W/m²]"); ax.set_xlabel("Local time [h]")
    ax.legend(loc="upper left", fontsize=9); ax.set_title("Heating Q_H(t) + usable window (green)")

    if win:
        for a in axes:
            a.axvspan(win[0], win[1], color="green", alpha=0.07)
            a.axvline(win[2], color="green", ls="-", lw=1.2, alpha=0.6)
    fig.suptitle(title, fontsize=15)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return path
