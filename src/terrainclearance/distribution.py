"""Verteilung der Flugzeit über den Hangabstand (zeitgewichtete KDE).

Beantwortet: 'Wie viel Flugzeit wurde in welchem Hangabstand verbracht?' — pro
Flug und als Zusammenzug über mehrere Flüge, normiert auf die Flugdauer.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde

from .config import Config


@dataclass
class FlightDist:
    name: str
    clearance: np.ndarray   # Hangabstand je Fix (Flugphase), m
    weights: np.ndarray     # Zeit je Fix, s
    duration_s: float
    start_dt: np.datetime64 | None = None


def weighted_cdf(values, weights, grid) -> np.ndarray | None:
    """% der (gewichteten) Zeit mit Abstand <= grid-Wert (exakte gewichtete ECDF)."""
    m = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    v, w = values[m], weights[m]
    if v.size < 2:
        return None
    order = np.argsort(v)
    v, cum = v[order], np.cumsum(w[order])
    total = cum[-1]
    if total <= 0:
        return None
    cw = np.concatenate([[0.0], cum])
    idx = np.searchsorted(v, grid, side="right")
    return 100.0 * cw[idx] / total


def weighted_quantile(values, weights, q) -> float:
    """Gewichtetes Quantil q (0..1) von values."""
    m = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    v, w = values[m], weights[m]
    if v.size == 0:
        return float("nan")
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) - 0.5 * w
    cw /= w.sum()
    return float(np.interp(q, cw, v))


def fix_durations(t_s: np.ndarray) -> np.ndarray:
    """Vom jeweiligen Fix repräsentierte Zeitspanne (s)."""
    if t_s.size < 2:
        return np.ones_like(t_s)
    dt = np.diff(t_s)
    med = float(np.median(dt)) if dt.size else 1.0
    dt = np.append(dt, med)
    return np.clip(dt, 0.0, None)


def _weighted_density(values, weights, grid) -> np.ndarray | None:
    m = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    v, w = values[m], weights[m]
    if v.size < 5 or np.ptp(v) < 1e-6:
        return None
    try:
        kde = gaussian_kde(v, weights=w)
    except Exception:
        return None
    return kde(grid)


def make_flight_dist(name: str, clearance: np.ndarray, t_s: np.ndarray,
                     airborne: np.ndarray, start_dt=None) -> FlightDist:
    w = fix_durations(t_s)
    return FlightDist(
        name=name,
        clearance=clearance[airborne],
        weights=w[airborne],
        duration_s=float(w[airborne].sum()),
        start_dt=start_dt,
    )


def _grid(cfg: Config) -> np.ndarray:
    return np.linspace(0.0, cfg.kde_max_m, cfg.kde_points)


def _share_below(d: FlightDist, thr: float) -> float:
    tot = d.weights.sum()
    if tot <= 0:
        return float("nan")
    return 100.0 * d.weights[d.clearance < thr].sum() / tot


def _fmt_pct(x: float) -> str:
    if not np.isfinite(x):
        return "—"
    if 0 < x < 0.1:
        return "<0.1 %"
    if x < 10:
        return f"{x:.1f} %"
    return f"{x:.0f} %"


def build_flight_kde(name: str, clr_terrain, clr_surface, t_s, airborne, cfg: Config) -> go.Figure:
    grid = _grid(cfg)
    dt = make_flight_dist(name, clr_terrain, t_s, airborne)
    ds = make_flight_dist(name, clr_surface, t_s, airborne)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
                        subplot_titles=("Dichte: Anteil der Flugzeit pro Meter",
                                        "Kumulativ: Anteil der Flugzeit UNTER x"))
    for d, label, color in [(dt, "Gelände", "#1a9641"), (ds, "Oberfläche/Wald", "#d7191c")]:
        dens = _weighted_density(d.clearance, d.weights, grid)
        if dens is not None:
            fig.add_trace(go.Scatter(x=grid, y=dens * 100.0, name=label, line=dict(color=color),
                                     legendgroup=label), row=1, col=1)
        cdf = weighted_cdf(d.clearance, d.weights, grid)
        if cdf is not None:
            fig.add_trace(go.Scatter(x=grid, y=cdf, name=label, line=dict(color=color),
                                     legendgroup=label, showlegend=False), row=2, col=1)
    ct, wt, dg = cfg.crit_terrain_m
    for r in (1, 2):
        for val, col in [(ct, "#feb24c"), (wt, "#fd8d3c"), (dg, "#d7191c")]:
            fig.add_vline(x=val, line=dict(color=col, dash="dash", width=1), row=r, col=1)
    med = weighted_quantile(dt.clearance, dt.weights, 0.5)
    sub = (f"Median Gelände {med:.0f} m · {_fmt_pct(_share_below(dt, wt))} der Zeit < {wt:.0f} m · "
           f"{_fmt_pct(_share_below(dt, dg))} < {dg:.0f} m")
    fig.update_yaxes(title_text="% pro m", row=1, col=1)
    fig.update_yaxes(title_text="% der Zeit darunter", range=[0, 100], row=2, col=1)
    fig.update_xaxes(title_text="Hangabstand [m]", row=2, col=1)
    fig.update_layout(title=f"{name} — Zeit-Verteilung über Hangabstand<br><sub>{sub}</sub>",
                      hovermode="x unified", margin=dict(l=60, r=20, t=80, b=40))
    return fig


def build_aggregate_kde(flights: list[FlightDist], cfg: Config, which: str = "Gelände") -> go.Figure:
    grid = _grid(cfg)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Dichte (pro Flug, auf Flugdauer normiert)",
                                        "Kumulativ: Anteil der Flugzeit UNTER x"))
    for d in flights:
        label = f"{d.name} ({d.duration_s/60:.0f} min)"
        dens = _weighted_density(d.clearance, d.weights, grid)
        if dens is not None:
            fig.add_trace(go.Scatter(x=grid, y=dens * 100.0, name=label, line=dict(width=1),
                                     opacity=0.55, legendgroup=d.name), row=1, col=1)
        cdf = weighted_cdf(d.clearance, d.weights, grid)
        if cdf is not None:
            fig.add_trace(go.Scatter(x=grid, y=cdf, name=label, line=dict(width=1), opacity=0.55,
                                     legendgroup=d.name, showlegend=False), row=2, col=1)
    # Mittelung (Ø pro Flug) bewusst entfernt — nur Einzelflüge + zeitgewichtetes Total.
    all_c = np.concatenate([d.clearance for d in flights]) if flights else np.array([])
    all_w = np.concatenate([d.weights for d in flights]) if flights else np.array([])
    pooled = _weighted_density(all_c, all_w, grid)
    pooled_cdf = weighted_cdf(all_c, all_w, grid)
    if pooled is not None:
        fig.add_trace(go.Scatter(x=grid, y=pooled * 100.0, name="Total (zeitgewichtet)",
                                 line=dict(color="#1f4e9c", width=3, dash="dot")), row=1, col=1)
    if pooled_cdf is not None:
        fig.add_trace(go.Scatter(x=grid, y=pooled_cdf, name="Total", line=dict(color="#1f4e9c", width=3, dash="dot"),
                                 showlegend=False), row=2, col=1)
    ct, wt, dg = cfg.crit_terrain_m
    for r in (1, 2):
        for val, col in [(ct, "#feb24c"), (wt, "#fd8d3c"), (dg, "#d7191c")]:
            fig.add_vline(x=val, line=dict(color=col, dash="dash", width=1), row=r, col=1)
    total_h = sum(d.duration_s for d in flights) / 3600.0
    fig.update_yaxes(title_text="% pro m", row=1, col=1)
    fig.update_yaxes(title_text="% der Zeit darunter", range=[0, 100], row=2, col=1)
    fig.update_xaxes(title_text="Hangabstand [m]", row=2, col=1)
    fig.update_layout(title=f"Hangabstand-Verteilung über {len(flights)} Flüge ({total_h:.1f} h) — {which}",
                      hovermode="x unified", margin=dict(l=60, r=20, t=70, b=40))
    return fig


def build_risk_over_time(flights: list[FlightDist], cfg: Config) -> go.Figure:
    """Verschiebung der 'Risikobereitschaft' über die Zeit: tiefe Abstands-Perzentile
    und Zeitanteil unter Schwellen, pro Flug chronologisch."""
    fl = [d for d in flights if d.start_dt is not None and d.clearance.size > 0]
    fl.sort(key=lambda d: d.start_dt)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.62, 0.38],
                        subplot_titles=("Hangabstand-Perzentile je Flug (tiefer = mehr Risiko)",
                                        "Anteil der Flugzeit unter Schwelle"))
    if not fl:
        return fig
    dates = [np.datetime64(d.start_dt, "s").astype("datetime64[s]").astype("O") for d in fl]
    ct, wt, dg = cfg.crit_terrain_m
    for qq, name, color in [(0.05, "p05", "#d7191c"), (0.10, "p10", "#fd8d3c"),
                            (0.25, "p25", "#feb24c"), (0.50, "Median", "#1a9641")]:
        ys = [weighted_quantile(d.clearance, d.weights, qq) for d in fl]
        fig.add_trace(go.Scatter(x=dates, y=ys, name=name, mode="lines+markers",
                                 line=dict(color=color)), row=1, col=1)
    for thr, color in [(wt, "#fd8d3c"), (ct, "#feb24c")]:
        ys = [_share_below(d, thr) for d in fl]
        fig.add_trace(go.Scatter(x=dates, y=ys, name=f"< {thr:.0f} m", mode="lines+markers",
                                 line=dict(color=color)), row=2, col=1)
    for val, col in [(ct, "#feb24c"), (wt, "#fd8d3c"), (dg, "#d7191c")]:
        fig.add_hline(y=val, line=dict(color=col, dash="dash", width=1), row=1, col=1)
    fig.update_yaxes(title_text="Hangabstand [m]", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="% der Flugzeit", rangemode="tozero", row=2, col=1)
    fig.update_xaxes(title_text="Flugdatum", row=2, col=1)
    fig.update_layout(title="Risiko über Zeit — Hangabstand-Perzentile je Flug",
                      hovermode="x unified", margin=dict(l=60, r=20, t=70, b=40))
    return fig
