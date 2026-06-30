"""Ausgaben Phase A: GeoTIFFs, Hillshade-PNG mit Q_H-Overlay + Hotspots, Plotly-Karte."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import ThermalConfig
from .grids import Grid
from .viz import draw_hillshade


def write_geotiffs(grid: Grid, mask, terrain, heat, score, out_dir: Path, label: str):
    out_dir = Path(out_dir)
    m = lambda a: np.where(mask, a, np.nan)
    grid.to_geotiff(m(heat.Q_H_daymax), out_dir / f"qh_{label}_daymax.tif")
    grid.to_geotiff(m(heat.Q_H_energy), out_dir / f"qh_{label}_energy.tif")
    grid.to_geotiff(m(score), out_dir / f"score_{label}.tif")


def plot_field_png(grid: Grid, mask, dtm, field, hotspots, title, path, cmap="inferno", unit="W/m²"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fld = np.where(mask, field, np.nan)
    fig, ax = plt.subplots(figsize=(9, 11))
    extent = draw_hillshade(ax, dtm, grid)
    im = ax.imshow(fld, cmap=cmap, extent=extent, origin="upper", alpha=0.8, interpolation="nearest")
    if hotspots:
        ax.scatter([h.e for h in hotspots], [h.n for h in hotspots],
                   s=42, facecolors="none", edgecolors="cyan", linewidths=1.4, label="Hotspots")
        # Top-10 nummerieren
        for h in hotspots[:10]:
            ax.annotate(str(h.id), (h.e, h.n), color="cyan", fontsize=7, ha="center", va="center")
    ax.set_title(title)
    ax.set_xlabel("LV95 East [m]"); ax.set_ylabel("LV95 North [m]")
    fig.colorbar(im, ax=ax, shrink=0.6, label=unit)
    ax.set_aspect("equal")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=185, bbox_inches="tight")
    plt.close(fig)
    return path


def build_energy_3d(grid: Grid, mask, dtm, energy, hotspots, path, title,
                    colorbar="Energy input [Wh/m²]", cmin=None, cmax=None, colorscale="Inferno"):
    """Plotly-3D-Relief (volle Gitterauflösung), Boden nach Feldwert eingefärbt (Sequential-Map)."""
    import plotly.graph_objects as go

    z = np.where(mask, dtm, np.nan).astype(float)
    c = np.where(mask, energy, np.nan).astype(float)
    w, s, e, n = grid.bounds()
    xs = (np.arange(grid.nx) + 0.5) * grid.res                 # lokal, West=0
    ys = (grid.ny - np.arange(grid.ny) - 0.5) * grid.res       # Nord oben

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=xs, y=ys, z=z, surfacecolor=c, colorscale=colorscale, cmin=cmin, cmax=cmax,
        colorbar=dict(title=colorbar), name="Q_H energy",
        lighting=dict(ambient=0.65, diffuse=0.6, specular=0.1), hoverinfo="skip",
    ))
    if hotspots:
        fig.add_trace(go.Scatter3d(
            x=[h.e - w for h in hotspots], y=[h.n - s for h in hotspots],
            z=[h.elev_m + 30 for h in hotspots], mode="markers",
            marker=dict(size=3, color="red", symbol="diamond"),
            text=[f"#{h.id} Q_H {h.q_h_peak:.0f} W/m²" for h in hotspots],
            hoverinfo="text", name="Hotspots"))
    fig.update_layout(
        title=title,
        scene=dict(xaxis_title="East [m]", yaxis_title="North [m]", zaxis_title="Altitude [m a.s.l.]",
                   aspectmode="data"),
        margin=dict(l=0, r=0, t=40, b=0))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    return fig


def plot_cumulative_panels_png(grid: Grid, mask, dtm, fields, path,
                               suptitle="Cumulative Q_H energy input over the day",
                               unit="Energy input [Wh/m²]"):
    """2×2-Hillshade-Panels (matplotlib), je Cutoff ein Feld, GEMEINSAME Farbskala."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # gemeinsame Skala: 0 .. Max des grössten (letzten) Cutoffs → Anwachsen sichtbar
    vmax = max(float(np.nanmax(np.where(mask, f, np.nan))) for _, f in fields)
    fig, axes = plt.subplots(2, 2, figsize=(13, 15), constrained_layout=True)
    im = None
    for ax, (h, f) in zip(axes.ravel(), fields):
        extent = draw_hillshade(ax, dtm, grid)
        im = ax.imshow(np.where(mask, f, np.nan), cmap="inferno", extent=extent, origin="upper",
                       alpha=0.85, interpolation="nearest", vmin=0.0, vmax=vmax)
        ax.set_title(f"bis {int(h):02d}:00 Uhr", fontsize=13)
        ax.set_xlabel("LV95 East [m]"); ax.set_ylabel("LV95 North [m]")
        ax.set_aspect("equal")
    fig.colorbar(im, ax=axes, shrink=0.6, label=unit)
    fig.suptitle(suptitle, fontsize=15)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_attenuation_timeseries(clouds, path, date=""):
    """Tagesgang Bewölkung + Direktstrahl-Dämpfung (Domänenmittel) — Nachvollziehbarkeit A5b."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = clouds.times
    hours = t.hour + t.minute / 60.0
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(hours, clouds.mean_cloud, color="slategray", lw=2, label="Bewölkung (CLCT)")
    ax1.fill_between(hours, clouds.mean_cloud, color="slategray", alpha=0.2)
    ax1.set_xlabel("Lokalzeit [h]"); ax1.set_ylabel("Bewölkung [%]", color="slategray")
    ax1.set_ylim(0, 100); ax1.set_xlim(hours.min(), hours.max())
    ax2 = ax1.twinx()
    ax2.plot(hours, clouds.mean_f_dir, color="darkorange", lw=2, label="f_dir (Direktstrahl real/klar)")
    ax2.set_ylabel("Direktstrahl-Faktor f_dir", color="darkorange"); ax2.set_ylim(0, 1.25)
    ax1.set_title(f"ICON-Wolken-Dämpfung im Tagesgang ({clouds.source}) — {date}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def build_cumulative_energy_3d_files(grid: Grid, mask, dtm, fields, out_dir, title_prefix,
                                     hotspots=None):
    """Je Cutoff EIN eigenständiges 3D-HTML (volle Auflösung), GEMEINSAME Viridis-Skala 0..vmax."""
    out_dir = Path(out_dir)
    vmax = max(float(np.nanmax(np.where(mask, f, np.nan))) for _, f in fields)
    paths = []
    for h, f in fields:
        p = out_dir / f"energy_3d_bis{int(h):02d}h.html"
        build_energy_3d(grid, mask, dtm, f, hotspots, p,
                        f"{title_prefix} — kumuliert bis {int(h):02d}:00 Uhr",
                        cmin=0.0, cmax=vmax)
        paths.append(p)
    return paths, vmax


def plot_hotspot_map_html(hotspots, cfg: ThermalConfig, path):
    import plotly.graph_objects as go
    if not hotspots:
        return None
    fig = go.Figure(go.Scattermap(
        lat=[h.lat for h in hotspots], lon=[h.lon for h in hotspots], mode="markers",
        marker=dict(size=11, color=[h.score for h in hotspots], colorscale="Viridis",
                    colorbar=dict(title="Hotspot-Score"), showscale=True),
        text=[f"#{h.id}  Score {h.score:.2f}<br>Q_H {h.q_h_peak:.0f} W/m²<br>"
              f"{h.elev_m:.0f} m, {h.slope_deg:.0f}°" for h in hotspots],
        hoverinfo="text", name="Hotspots",
    ))
    lats = [h.lat for h in hotspots]; lons = [h.lon for h in hotspots]
    fig.update_layout(
        map=dict(style=cfg.map_style,
                 center=dict(lat=float(np.mean(lats)), lon=float(np.mean(lons))), zoom=11.5),
        margin=dict(l=0, r=0, t=40, b=0), title="Thermal hotspots (Phase A, ideal)")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    return path
