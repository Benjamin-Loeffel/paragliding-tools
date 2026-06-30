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


def plot_relief_png(grid: Grid, mask, dtm, path, title):
    """Schritt 1 der Herleitung: das nackte Höhenmodell (Hillshade + Höhen-Tönung)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    z = np.where(mask, dtm, np.nan)
    fig, ax = plt.subplots(figsize=(9, 11))
    extent = draw_hillshade(ax, dtm, grid)
    im = ax.imshow(z, cmap="viridis", extent=extent, origin="upper", alpha=0.55, interpolation="nearest")
    ax.set_title(title); ax.set_xlabel("LV95 East [m]"); ax.set_ylabel("LV95 North [m]")
    fig.colorbar(im, ax=ax, shrink=0.6, label="Elevation [m a.s.l.]")
    ax.set_aspect("equal")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight"); plt.close(fig)
    return path


def plot_aspect_slope_png(grid: Grid, mask, terrain, path, title):
    """Schritt 2: aus dem Relief abgeleitete Exposition (Aspekt, zyklisch) + Steilheit (Slope)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    slope_deg = np.where(mask, np.degrees(terrain.slope), np.nan)
    aspect_deg = np.where(mask, np.degrees(terrain.aspect), np.nan)
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5))
    # Steilheit — sequenziell (viridis)
    ext = draw_hillshade(axes[0], terrain.dtm, grid)
    s = axes[0].imshow(slope_deg, cmap="viridis", extent=ext, origin="upper", alpha=0.8,
                       vmin=0, vmax=55, interpolation="nearest")
    axes[0].set_title("Steepness (slope)"); axes[0].set_aspect("equal")
    axes[0].set_xlabel("LV95 East [m]"); axes[0].set_ylabel("LV95 North [m]")
    fig.colorbar(s, ax=axes[0], shrink=0.6, label="Slope [°]")
    # Exposition — Aspekt ist ZYKLISCH → zyklische Map (twilight), bewusste Ausnahme zur viridis-Politik
    ext = draw_hillshade(axes[1], terrain.dtm, grid)
    a = axes[1].imshow(aspect_deg, cmap="twilight", extent=ext, origin="upper", alpha=0.85,
                       vmin=0, vmax=360, interpolation="nearest")
    axes[1].set_title("Exposure (aspect)"); axes[1].set_aspect("equal")
    axes[1].set_xlabel("LV95 East [m]")
    cb = fig.colorbar(a, ax=axes[1], shrink=0.6, label="Aspect [° from N, clockwise]")
    cb.set_ticks([0, 90, 180, 270, 360]); cb.set_ticklabels(["N", "E", "S", "W", "N"])
    fig.suptitle(title, fontsize=15)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig)
    return path


def plot_landcover_3d(grid: Grid, mask, dtm, lc, path, title):
    """Schritt 3: Waldbedeckungsart (Nadel/Laub/Misch/offen …) auf das Relief drapiert (3D)."""
    import plotly.graph_objects as go
    from . import config as C

    codes = [C.LC_UNKNOWN, C.LC_CONIFER, C.LC_BROADLEAF, C.LC_MIXED, C.LC_GRASS,
             C.LC_ROCK, C.LC_WATER, C.LC_SNOW, C.LC_URBAN]
    names = ["unknown", "conifer", "broadleaf", "mixed", "grass",
             "rock/scree", "water", "snow/ice", "urban"]
    colors = ["#999999", "#1b7837", "#a6dba0", "#5aae61", "#d9ef8b",
              "#bdbdbd", "#4393c3", "#f7f7f7", "#b2182b"]
    nb = len(codes)
    cs = []
    for i, c in enumerate(colors):
        cs += [[i / nb, c], [(i + 1) / nb, c]]          # diskrete (gestufte) Colorscale

    z = np.where(mask, dtm, np.nan).astype(float)
    col = np.where(mask, lc.class_id, np.nan).astype(float)
    w, s, e, n = grid.bounds()
    xs = (np.arange(grid.nx) + 0.5) * grid.res
    ys = (grid.ny - np.arange(grid.ny) - 0.5) * grid.res
    fig = go.Figure(go.Surface(
        x=xs, y=ys, z=z, surfacecolor=col, colorscale=cs, cmin=-0.5, cmax=nb - 0.5,
        colorbar=dict(title="Land cover", tickmode="array",
                      tickvals=codes, ticktext=names),
        lighting=dict(ambient=0.7, diffuse=0.55), hoverinfo="skip"))
    fig.update_layout(title=title, margin=dict(l=0, r=0, t=40, b=0),
                      scene=dict(xaxis_title="East [m]", yaxis_title="North [m]",
                                 zaxis_title="Altitude [m a.s.l.]", aspectmode="data"))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    try:                                                # statisches PNG fürs README (kaleido)
        fig.write_image(str(Path(path).with_suffix(".png")), width=1500, height=1000, scale=2)
    except Exception:
        pass
    return fig


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


def build_energy_3d_timeslider(grid: Grid, mask, dtm, fields, path, title,
                               colorbar="Energy input [Wh/m²]", colorscale="Inferno",
                               cmax=None, stride=2):
    """3D-Relief mit kumuliertem Q_H-Energieeintrag drapiert + ZEIT-SLIDER über die
    Tageszeit-Stützstellen (11/13/15/18 h).

    fields: [(Stunde, Feld[ny,nx]), …] kumulierter Energieeintrag je Cutoff.
    Die Relief-Geometrie ist STATISCH (Basis-Trace 0); die Frames updaten NUR `surfacecolor`
    (kein Geometrie-Bloat — wie beim Plume-Slider). `stride` dünnt das Mesh fürs Web aus.
    Ein gemeinsames `cmax` (von aussen vorgegeben) macht ideal- vs. real-Slider direkt
    vergleichbar (real wirkt dunkler = Wolkenverlust sichtbar)."""
    import plotly.graph_objects as go

    z = np.where(mask, dtm, np.nan).astype(float)[::stride, ::stride]
    xs = ((np.arange(grid.nx) + 0.5) * grid.res)[::stride]
    ys = ((grid.ny - np.arange(grid.ny) - 0.5) * grid.res)[::stride]
    cols = [(int(h), np.where(mask, f, np.nan).astype(float)[::stride, ::stride])
            for h, f in sorted(fields)]
    if cmax is None:
        cmax = max(float(np.nanmax(c)) for _, c in cols)
    hours = [h for h, _ in cols]
    init = min(range(len(hours)), key=lambda i: abs(hours[i] - 15))   # bei ~15 h starten (Story-konsistent)

    def surface(col, with_geom):
        kw = dict(surfacecolor=col, colorscale=colorscale, cmin=0.0, cmax=cmax,
                  colorbar=dict(title=colorbar), hoverinfo="skip",
                  lighting=dict(ambient=0.65, diffuse=0.6, specular=0.1))
        if with_geom:                                   # nur der Basis-Trace trägt die Geometrie
            kw.update(x=xs, y=ys, z=z)
        return go.Surface(**kw)

    frames = [go.Frame(data=[surface(col, with_geom=False)], name=f"{h:02d}", traces=[0])
              for h, col in cols]
    fig = go.Figure(data=[surface(cols[init][1], with_geom=True)], frames=frames)
    steps = [dict(method="animate", label=f"{h:02d}:00",
                  args=[[f"{h:02d}"], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                           transition=dict(duration=0))]) for h, _ in cols]
    fig.update_layout(
        title=title, margin=dict(l=0, r=0, t=40, b=0),
        sliders=[dict(active=init, currentvalue=dict(prefix="Energy accumulated until "),
                      pad=dict(t=40), steps=steps)],
        scene=dict(xaxis_title="East [m]", yaxis_title="North [m]",
                   zaxis_title="Altitude [m a.s.l.]", aspectmode="data"))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    try:                                                # statisches PNG (Initialframe ~15 h) fürs README
        fig.write_image(str(Path(path).with_suffix(".png")), width=1500, height=1000, scale=2)
    except Exception:
        pass
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
