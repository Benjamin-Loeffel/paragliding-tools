"""Phase B — Grenzschicht & Thermikstärke aus der Payerne-Sondierung.

Aus dem Vertikalprofil (p, T, Td, Höhe, Wind) werden abgeleitet:
  - Wolkenbasis (CCL = Convective Condensation Level, sonst LCL) — die Thermik-Decke AMSL,
  - konvektive Temperatur Tc (Auslöse-Bodentemperatur),
  - Gleichgewichtsniveau EL (potenzielle Cumulus-Obergrenze),
  - Windprofil (für D1-Advektion).
Pro Hotspot:
  - z_i_lokal = Wolkenbasis_AMSL − Hotspot-Höhe (Konvektionstiefe über dem Auslöser),
  - w* = (g/T0 · w'θ'0 · z_i)^(1/3) mit w'θ'0 = (0.55·Q_H)/(ρ·cp)  [Deardorff],
    Faktor 0.55 ≈ R_n/G (siehe ADR-0011), Q_H = realer (wolkengedämpfter) Tages-Spitzenwert.

Arbeitet auf einem DataFrame im meteo-Format (Spalten pressure/temperature/dewpoint/height/
wind_dir/wind_speed) — entkoppelt von der Paketlage des meteo-Tools.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

G = 9.81
CP = 1005.0


@dataclass
class BoundaryLayer:
    cloud_base_amsl: float        # m, CCL bzw. LCL
    thermal_top_amsl: float       # m, Trockenthermik-Decke (= Wolkenbasis)
    conv_temp_C: float | None     # konvektive Auslöse-Temperatur
    el_amsl: float | None         # Gleichgewichtsniveau (Cumulus-Top)
    surface_elev_m: float
    surface_T_K: float
    wind_height_m: np.ndarray     # AMSL
    wind_dir_deg: np.ndarray
    wind_speed_ms: np.ndarray
    prof_height_m: np.ndarray     # Sondierungs-Höhen AMSL (für θ-Aufstieg)
    prof_theta_K: np.ndarray      # potenzielle Temperatur θ(z)
    method: str

    def parcel_top(self, z_surf_m: float, dtheta_K: float = 3.0) -> float:
        """Trockenadiabatischer Thermik-Top AMSL ab geheiztem Bergboden auf Höhe z_surf.
        θ_Parzelle = θ_Umgebung(z_surf) + Überhitzung; steigt bis θ_Umgebung sie einholt."""
        zp, th = self.prof_height_m, self.prof_theta_K
        if len(zp) < 2:
            return z_surf_m
        th_parcel = float(np.interp(z_surf_m, zp, th)) + dtheta_K
        above = zp > z_surf_m + 50.0
        for z, t in zip(zp[above], th[above]):
            if t >= th_parcel:
                return float(z)
        return float(zp[-1])


def _interp_height(p_hpa, height_m, target_p):
    """Höhe (m) bei Zieldruck via log-p-Interpolation."""
    order = np.argsort(p_hpa)
    return float(np.interp(np.log(target_p), np.log(np.asarray(p_hpa)[order]),
                           np.asarray(height_m)[order]))


def analyze_sounding(df) -> BoundaryLayer:
    import metpy.calc as mpcalc
    from metpy.units import units

    t = df.dropna(subset=["pressure", "temperature", "dewpoint", "height"]).drop_duplicates("pressure")
    t = t.sort_values("pressure", ascending=False)
    p = t["pressure"].to_numpy() * units.hPa
    T = t["temperature"].to_numpy() * units.degC
    Td = t["dewpoint"].to_numpy() * units.degC
    h = t["height"].to_numpy(dtype=float)
    surf_elev = float(h[0]); surf_T_K = float(t["temperature"].iloc[0]) + 273.15

    # Trocken-CBL-Höhe z_i: tiefster Punkt über der Bodenschicht, an dem die
    # potenzielle Temperatur θ wieder die Boden-θ übersteigt (Deckelinversion).
    p_arr = t["pressure"].to_numpy(dtype=float)
    T_K = t["temperature"].to_numpy(dtype=float) + 273.15
    theta = T_K * (1000.0 / p_arr) ** 0.286
    # Mischungsschicht-θ: Mittel über [surf+100, surf+400] m (überadiabatische Bodenhaut auslassen)
    ml = (h - surf_elev >= 100.0) & (h - surf_elev <= 400.0)
    th_ml = float(np.nanmean(theta[ml])) if ml.any() else float(theta[0])
    thermal_top = surf_elev + 3500.0           # Fallback
    for i in range(1, len(h)):
        if (h[i] - surf_elev) > 400.0 and theta[i] >= th_ml + 1.0:
            thermal_top = float(h[i]); break
    method = "theta-cbl"

    # Wolkenbasis: CCL (konvektiv); bei sehr trockener Luft >> z_i -> Blauthermik
    cloud_base = None; conv_T = None
    try:
        ccl_p, _ccl_t, t_conv = mpcalc.ccl(p, T, Td)
        cb = _interp_height(p_arr, h, float(ccl_p.m))
        if np.isfinite(cb) and cb < surf_elev + 8000.0:
            cloud_base = cb; conv_T = float(t_conv.to("degC").m)
    except Exception:
        pass
    if cloud_base is None:                       # LCL als Rückfall
        try:
            lcl_p, _ = mpcalc.lcl(p[0], T[0], Td[0])
            cloud_base = _interp_height(p_arr, h, float(lcl_p.m))
        except Exception:
            cloud_base = thermal_top
    el_amsl = None
    try:
        el_p, _ = mpcalc.el(p, T, Td)
        if el_p is not None and np.isfinite(el_p.m):
            el_amsl = _interp_height(p_arr, h, float(el_p.m))
    except Exception:
        pass

    order = np.argsort(h)
    wsub = df.dropna(subset=["height", "wind_dir", "wind_speed"]).sort_values("height")
    return BoundaryLayer(
        cloud_base_amsl=cloud_base, thermal_top_amsl=thermal_top, conv_temp_C=conv_T,
        el_amsl=el_amsl, surface_elev_m=surf_elev, surface_T_K=surf_T_K,
        wind_height_m=wsub["height"].to_numpy(dtype=float),
        wind_dir_deg=wsub["wind_dir"].to_numpy(dtype=float),
        wind_speed_ms=wsub["wind_speed"].to_numpy(dtype=float),
        prof_height_m=h[order], prof_theta_K=theta[order], method=method)


def w_star(q_h_wm2: float, z_i_m: float, T0_K: float = 290.0, rho: float = 1.0,
           rn_over_g: float = 0.55) -> float:
    """Konvektive Geschwindigkeitsskala w* [m/s] (Deardorff). q_h = G-bezogen, intern ×rn_over_g."""
    if z_i_m <= 0 or q_h_wm2 <= 0:
        return 0.0
    wth0 = (rn_over_g * q_h_wm2) / (rho * CP)        # kinematischer Auftriebsfluss [K m/s]
    return float((G / T0_K * wth0 * z_i_m) ** (1.0 / 3.0))


def cbl_timeseries(bl: BoundaryLayer, times, qh_series, rho: float = 1.0, beta: float = 0.2,
                   rn_over_g: float = 0.55) -> dict:
    """Tagesgang der Mischungsschichthöhe z_i(t) via Encroachment (+ Entrainment β).

    Kumulierter Auftriebs-Heat ∫ w'θ' dt füllt den θ-Keil über dem Morgenprofil:
      ∫₀^{z_i}(θ_env(z_i) − θ_env(z))dz = (1+2β)·∫₀^t (rn_over_g·Q_H)/(ρ·cp) dt'.
    Gibt z_i_amsl(t) und growth(t)=z_i(t)/max(z_i) (0..1) — der Wachstumsanteil skaliert die
    nutzbare Bandtiefe je Hotspot im Tagesverlauf (Antwort 'wann starten').
    """
    zp, th = bl.prof_height_m, bl.prof_theta_K
    dz = np.diff(zp)
    n = len(zp)
    W = np.zeros(n)                              # θ-Keil-Fläche bis Niveau k [K·m]
    for k in range(1, n):
        W[k] = float(np.sum((th[k] - th[:k]) * dz[:k]))
    W = np.maximum.accumulate(W)                 # monoton für die Inversion
    dt_s = float((times[1] - times[0]).seconds) if len(times) > 1 else 1800.0
    H = 0.0
    z_i = np.zeros(len(times))
    qh = np.asarray(qh_series, dtype=float)
    for i in range(len(times)):
        H += (1.0 + 2.0 * beta) * rn_over_g * max(qh[i], 0.0) / (rho * CP) * dt_s
        z_i[i] = float(np.interp(H, W, zp))
    peak = float(np.max(z_i)) if z_i.size else bl.surface_elev_m
    growth = z_i / peak if peak > bl.surface_elev_m else np.ones_like(z_i)
    return {"times": times, "z_i_amsl": z_i, "growth": np.clip(growth, 0.0, 1.0),
            "z_i_peak_amsl": peak}


def strength_at(bl: BoundaryLayer, elev_m: float, qh: float, T0_K: float = 290.0,
                dtheta_K: float | None = None, band_scale: float = 1.0) -> dict:
    """z_i/w*/Ceiling an EINEM Punkt (Höhe + lokales Q_H) — Thermik-Top via θ-Aufstieg ab
    geheiztem Bergboden; Cumulus deckelt nur, wenn die Wolkenbasis über dem Punkt liegt.
    band_scale<1 skaliert die nutzbare Bandtiefe (CBL-Tagesgang, vormittags noch flach)."""
    # Überhitzung ∝ Heizung: heisse Fels-/SSW-Hänge brechen höher durch (1.5–7 K)
    dth = float(np.clip(0.008 * qh + 1.0, 1.5, 7.0)) if dtheta_K is None else dtheta_K
    top = bl.parcel_top(elev_m, dtheta_K=dth)
    cb = bl.cloud_base_amsl
    ceiling_max = min(top, cb) if cb > elev_m + 50.0 else top
    z_i = band_scale * max(ceiling_max - elev_m, 0.0)
    return {"elev_m": elev_m, "q_h": qh, "z_i_m": z_i, "top_amsl": top,
            "w_star_ms": w_star(qh, z_i, T0_K=T0_K), "ceiling_amsl": elev_m + z_i,
            "usable_band_m": z_i}


def _sample(field, e, n, grid):
    col = min(max(int((e - grid.west) / grid.res), 0), grid.nx - 1)
    row = min(max(int((grid.north - n) / grid.res), 0), grid.ny - 1)
    return float(field[row, col])


def thermal_strength(bl: BoundaryLayer, hotspots, q_h_field, grid, terrain,
                     T0_K: float = 290.0, dtheta_K: float | None = None) -> list[dict]:
    """Pro Hotspot z_i, w*, Ceiling (q_h_field = (reales) Q_H-Tagesmax [ny,nx])."""
    out = []
    for h in hotspots:
        s = strength_at(bl, h.elev_m, _sample(q_h_field, h.e, h.n, grid), T0_K=T0_K, dtheta_K=dtheta_K)
        s["id"] = h.id
        out.append(s)
    return out
