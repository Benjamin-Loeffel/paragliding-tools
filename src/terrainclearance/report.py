"""Ausgaben: interaktive plotly-Karte, Barogramm, CSV/JSON-Export."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone as _utc
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .calibrate import CalibrationResult
from .config import Config
from .critical import Event
from .igc_loader import FlightTrack

import logging

log = logging.getLogger(__name__)


def save_png(fig, path, width: int, height: int, scale: int = 2) -> bool:
    """Statisches PNG via kaleido. Fehlt kaleido, wird nur gewarnt (kein Abbruch)."""
    try:
        fig.write_image(str(path), width=width, height=height, scale=scale)
        return True
    except Exception as exc:  # kaleido fehlt o. Render-Fehler
        log.warning("PNG-Export übersprungen (%s): %s — `pip install kaleido`", Path(path).name, exc)
        return False
from .terrain import ClearanceResult

# Farbskala: kleiner Abstand = rot, gross = grün
_COLORSCALE = [[0.0, "#d7191c"], [0.25, "#fdae61"], [0.5, "#ffffbf"],
               [0.75, "#a6d96a"], [1.0, "#1a9641"]]


def _local_times(dt: np.ndarray, tzname: str) -> list[datetime]:
    tz = _utc.utc if tzname == "UTC" else ZoneInfo(tzname)
    secs = dt.astype("datetime64[s]").astype("int64")
    return [datetime.fromtimestamp(int(s), _utc.utc).astimezone(tz).replace(tzinfo=None) for s in secs]


def _zoom(bbox) -> float:
    minlon, minlat, maxlon, maxlat = bbox
    span = max(maxlon - minlon, maxlat - minlat, 1e-4)
    return float(max(8.0, min(15.5, math.log2(360.0 / span) - 1.0)))


def _hover(track, alt_cal, clr, i, times, unc=None) -> str:
    def fmt(x, unit="m"):
        return f"{x:.0f} {unit}" if np.isfinite(x) else "—"
    txt = (
        f"{times[i]:%H:%M:%S}<br>"
        f"Altitude: {fmt(alt_cal[i])}<br>"
        f"3D terrain: {fmt(clr.d3_terrain[i])}<br>"
        f"3D surface: {fmt(clr.d3_surface[i])}<br>"
        f"AGL (vertical): {fmt(clr.v_terrain[i])}<br>"
        f"above canopy/roof: {fmt(clr.v_surface[i])}"
    )
    if unc is not None:
        txt += (f"<br><i>MC terrain p05–p95: {fmt(unc.p05_terrain[i])}–{fmt(unc.p95_terrain[i])}</i>")
    return txt


def build_map(track: FlightTrack, alt_cal, clr: ClearanceResult,
              events: list[Event], cfg: Config, unc=None) -> go.Figure:
    times = _local_times(track.dt, cfg.timezone)
    hover = [_hover(track, alt_cal, clr, i, times, unc) for i in range(track.n)]

    fig = go.Figure()
    # Grundspur
    fig.add_trace(go.Scattermap(
        lat=track.lat, lon=track.lon, mode="lines",
        line=dict(width=1.5, color="rgba(60,60,60,0.4)"),
        name="Track", hoverinfo="skip",
    ))
    # Punkte eingefärbt nach Gelände-Abstand
    fig.add_trace(go.Scattermap(
        lat=track.lat, lon=track.lon, mode="markers",
        marker=dict(
            size=6,
            color=clr.d3_terrain,
            colorscale=_COLORSCALE,
            cmin=0, cmax=cfg.color_max_m,
            colorbar=dict(title="3D clearance<br>terrain [m]"),
        ),
        text=hover, hoverinfo="text", name="Clearance",
    ))
    # Kritische Events
    if events:
        fig.add_trace(go.Scattermap(
            lat=[e.lat for e in events], lon=[e.lon for e in events],
            mode="markers",
            marker=dict(size=15, color="rgba(0,0,0,0)",
                        symbol="circle"),
            text=[f"{e.level.upper()} · {e.phase} ({e.reason})<br>"
                  f"{e.iso_time}<br>3D terrain {e.d3_terrain:.0f} m / "
                  f"surface {e.d3_surface:.0f} m" for e in events],
            hoverinfo="text",
            name="critical",
        ))
        # auffälliger Rand für Events
        fig.add_trace(go.Scattermap(
            lat=[e.lat for e in events], lon=[e.lon for e in events],
            mode="markers",
            marker=dict(size=13, color=[
                {"gefahr": "#d7191c", "warnung": "#fd8d3c", "achtung": "#feb24c"}.get(e.level, "#feb24c")
                for e in events]),
            hoverinfo="skip", name="Events", showlegend=True,
        ))

    bbox = track.bbox_wgs84()
    fig.update_layout(
        map=dict(style=cfg.map_style,
                 center=dict(lat=float(np.mean(track.lat)), lon=float(np.mean(track.lon))),
                 zoom=_zoom(bbox)),
        margin=dict(l=0, r=0, t=40, b=0),
        title=f"{track.name} — terrain clearance",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
    )
    return fig


def build_barogram(track: FlightTrack, alt_cal, clr: ClearanceResult,
                   events: list[Event], cfg: Config, unc=None) -> go.Figure:
    times = _local_times(track.dt, cfg.timezone)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[0.58, 0.42],
                        subplot_titles=("Altitude profile", "3D distance to terrain / surface"))

    # Unsicherheitsband (p05–p95) hinter die Abstandslinien
    if unc is not None:
        fig.add_trace(go.Scatter(x=times, y=unc.p95_terrain, mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"), row=2, col=1)
        fig.add_trace(go.Scatter(x=times, y=unc.p05_terrain, mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(26,150,65,0.18)",
                                 name="Terrain p05–p95", hoverinfo="skip"), row=2, col=1)

    # Reihe 1: Höhen
    fig.add_trace(go.Scatter(x=times, y=clr.terrain_elev, name="Terrain (DTM)",
                             line=dict(color="#8c6d31"), fill="tozeroy",
                             fillcolor="rgba(140,109,49,0.25)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=times, y=clr.surface_elev, name="Surface (DSM)",
                             line=dict(color="#3a7d3a", dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=times, y=alt_cal, name="Flight altitude (calibrated)",
                             line=dict(color="#1f4e9c", width=2)), row=1, col=1)

    # Reihe 2: Abstände
    fig.add_trace(go.Scatter(x=times, y=clr.d3_terrain, name="3D terrain",
                             line=dict(color="#1a9641")), row=2, col=1)
    fig.add_trace(go.Scatter(x=times, y=clr.d3_surface, name="3D surface",
                             line=dict(color="#d7191c", dash="dot")), row=2, col=1)

    caution, warning, danger = cfg.crit_terrain_m
    for val, txt, col in [(caution, "Caution", "#feb24c"),
                          (warning, "Warning", "#fd8d3c"),
                          (danger, "Danger", "#d7191c")]:
        fig.add_hline(y=val, line=dict(color=col, dash="dash", width=1),
                      annotation_text=txt, annotation_position="right", row=2, col=1)

    if events:
        ev_times = [times[e.idx] for e in events]
        fig.add_trace(go.Scatter(
            x=ev_times, y=[e.d3_terrain for e in events], mode="markers",
            marker=dict(size=9, color="black", symbol="x"),
            name="Events", hovertext=[f"{e.level} · {e.phase} ({e.reason})" for e in events],
        ), row=2, col=1)

    fig.update_yaxes(title_text="m a.s.l.", row=1, col=1)
    fig.update_yaxes(title_text="Clearance [m]", rangemode="tozero", row=2, col=1)
    fig.update_xaxes(title_text=f"Time ({cfg.timezone})", row=2, col=1)
    fig.update_layout(title=f"{track.name} — barogram & clearance",
                      hovermode="x unified", margin=dict(l=60, r=20, t=60, b=40))
    return fig


def _grid_window(sampler, e_min, e_max, n_min, n_max, target_dim):
    """Downsampling-Gitter eines Sampler-Ausschnitts für die 3D-Oberfläche."""
    res = sampler.res
    cmin = max(int(np.floor((e_min - sampler.west) / res)), 0)
    cmax = min(int(np.ceil((e_max - sampler.west) / res)), sampler.W)
    rmin = max(int(np.floor((sampler.north - n_max) / res)), 0)
    rmax = min(int(np.ceil((sampler.north - n_min) / res)), sampler.H)
    if cmin >= cmax or rmin >= rmax:
        return None
    stride = max(1, int(np.ceil(max(cmax - cmin, rmax - rmin) / target_dim)))
    sub = sampler.arr[rmin:rmax:stride, cmin:cmax:stride].astype(float)
    sub[sampler._nodata_mask(sub)] = np.nan
    xs = sampler.west + (np.arange(cmin, cmax, stride) + 0.5) * res
    ys = sampler.north - (np.arange(rmin, rmax, stride) + 0.5) * res
    return sub, xs, ys


_EVENT_COLOR = {"gefahr": "#d7191c", "warnung": "#fd8d3c", "achtung": "#feb24c"}

# Monochrome Gelände-Palette: neutral, damit die rot->grün-Abstandsspur abhebt.
# Sanfter Helligkeitsverlauf; das Relief kommt v. a. aus der gerichteten Beleuchtung.
_TERRAIN_SCALES = {
    "gray": [[0.0, "#8c887f"], [0.5, "#c2bdb3"], [1.0, "#f4f1ec"]],
    "earth": [[0.0, "#2c5e2e"], [0.4, "#a9a066"], [0.72, "#d8cdb0"], [1.0, "#ffffff"]],
}


def _hillshade(z, res, azimuth=315.0, altitude=45.0):
    """Klassische Schummerung (0..1) aus dem DEM. NaN-Löcher werden geebnet,
    damit Gradienten an gültigen Nachbarzellen nicht verseucht werden."""
    zf = np.array(z, dtype=float)
    bad = ~np.isfinite(zf)
    if bad.any():
        zf[bad] = np.nanmean(zf)
    gy, gx = np.gradient(zf, res, res)
    slope = np.pi / 2.0 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gy, gx)
    az = np.radians(azimuth)
    alt = np.radians(altitude)
    shaded = (np.sin(alt) * np.sin(slope)
              + np.cos(alt) * np.cos(slope) * np.cos((az - np.pi / 2.0) - aspect))
    return np.clip((shaded + 1.0) / 2.0, 0.0, 1.0)


def _gray_scale(darkness: float):
    """Graustufenband für die Schummerung; höhere darkness = dunkler insgesamt.
    Helligkeit interpoliert von hell (d=0) zu dunkel (d=1)."""
    d = min(max(darkness, 0.0), 1.0)
    lit = int(round(235 - 175 * d))   # besonnte Flächen: d=0.7 -> 113
    sha = int(round(70 - 56 * d))     # Schatten:         d=0.7 -> 31
    return [[0.0, f"rgb({sha},{sha},{max(sha - 4, 0)})"],
            [1.0, f"rgb({lit},{lit},{max(lit - 7, 0)})"]]


def build_terrain3d(track: FlightTrack, e, n, alt_cal, clr: ClearanceResult,
                    events: list[Event], dtm, dsm, cfg: Config, unc=None) -> go.Figure:
    use_dsm = cfg.surface3d_model == "dsm" and dsm is not None
    surf = dsm if use_dsm else dtm
    surf_name = ("Surface (swissSURFACE3D, incl. forest/buildings)" if use_dsm
                 else "Terrain (swissALTI3D)")
    det = clr.d3_surface if use_dsm else clr.d3_terrain
    track_clear = det
    suffix = " surface" if use_dsm else " terrain"
    clear_title = f"3D clearance<br>{suffix.strip()} [m]"
    # MC im 3D berücksichtigen: optional nach konservativer Untergrenze/Mittel einfärben
    if unc is not None and cfg.surface3d_color_by in ("p05", "mean"):
        src = {"p05": (unc.p05_surface if use_dsm else unc.p05_terrain),
               "mean": (unc.mean_surface if use_dsm else unc.mean_terrain)}[cfg.surface3d_color_by]
        track_clear = src
        tag = "p05 (conservative)" if cfg.surface3d_color_by == "p05" else "mean"
        clear_title = f"3D clearance {tag}<br>{suffix.strip()} [m]"

    m = cfg.surface3d_margin_m
    win = _grid_window(surf, e.min() - m, e.max() + m, n.min() - m, n.max() + m,
                       cfg.surface3d_max_dim)

    fig = go.Figure()
    if win is not None:
        sub, xs, ys = win
        e0, n0 = float(xs.min()), float(ys.min())
        xr = float(xs.max() - xs.min()) or 1.0
        yr = float(ys.max() - ys.min()) or 1.0
        zmax = float(np.nanmax(sub))
        zr = zmax - float(np.nanmin(sub)) or 1.0
        res_disp = float(xs[1] - xs[0]) if xs.size > 1 else surf.res
        if cfg.surface3d_colorscale == "hillshade":
            # Matt & dunkel: Relief steckt in der Schummerung (surfacecolor),
            # Plotly-Licht flach + kein Specular => kein Glanz, alle Rinnen sichtbar.
            fig.add_trace(go.Surface(
                x=xs - e0, y=ys - n0, z=sub, surfacecolor=_hillshade(sub, res_disp),
                cmin=0.0, cmax=1.0, colorscale=_gray_scale(cfg.surface3d_darkness),
                showscale=False, opacity=1.0, name=surf_name, hoverinfo="skip",
                lighting=dict(ambient=0.9, diffuse=0.12, specular=0.0, roughness=1.0, fresnel=0.0),
            ))
        else:
            fig.add_trace(go.Surface(
                x=xs - e0, y=ys - n0, z=sub,
                colorscale=_TERRAIN_SCALES.get(cfg.surface3d_colorscale, _TERRAIN_SCALES["gray"]),
                showscale=False, opacity=1.0, name=surf_name, hoverinfo="skip",
                lighting=dict(ambient=0.38, diffuse=0.95, specular=0.12, roughness=0.85, fresnel=0.1),
                lightposition=dict(x=-0.6 * xr, y=1.4 * yr, z=zmax + 2.5 * zr),
            ))
    else:
        e0, n0 = float(e.min()), float(n.min())

    times = _local_times(track.dt, cfg.timezone)
    hover = [_hover(track, alt_cal, clr, i, times, unc) for i in range(track.n)]
    fig.add_trace(go.Scatter3d(
        x=e - e0, y=n - n0, z=alt_cal, mode="markers",
        marker=dict(size=2.5, color=track_clear, colorscale=_COLORSCALE,
                    cmin=0, cmax=cfg.color_max_m, colorbar=dict(title=clear_title)),
        text=hover, hoverinfo="text", name="Flight track",
    ))
    if events:
        fig.add_trace(go.Scatter3d(
            x=[e[ev.idx] - e0 for ev in events], y=[n[ev.idx] - n0 for ev in events],
            z=[alt_cal[ev.idx] for ev in events], mode="markers",
            marker=dict(size=5, symbol="diamond", line=dict(color="black", width=1),
                        color=[_EVENT_COLOR.get(ev.level, "#feb24c") for ev in events]),
            text=[f"{ev.level.upper()} · {ev.phase}<br>{ev.iso_time}<br>"
                  f"Terrain {ev.d3_terrain:.0f} m / Surface {ev.d3_surface:.0f} m"
                  for ev in events],
            hoverinfo="text", name="critical",
        ))

    fig.update_layout(
        title=f"{track.name} — 3D relief & flight track",
        scene=dict(xaxis_title="East [m]", yaxis_title="North [m]", zaxis_title="Altitude [m a.s.l.]",
                   aspectmode="data"),
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=0.0, x=0),
    )
    return fig


def write_csv_points(path: Path, track: FlightTrack, alt_cal, clr: ClearanceResult, levels, unc=None) -> None:
    def r(x, nd=1):
        return round(float(x), nd) if np.isfinite(x) else ""
    header = ["idx", "datetime_utc", "lat", "lon", "alt_raw_m", "alt_cal_m",
              "terrain_elev_m", "surface_elev_m", "v_terrain_m", "d3_terrain_m",
              "v_surface_m", "d3_surface_m", "clipped", "level"]
    if unc is not None:
        header += ["d3_terrain_mean_m", "d3_terrain_p05_m", "d3_terrain_p95_m",
                   "d3_terrain_min_m", "d3_terrain_max_m",
                   "d3_surface_mean_m", "d3_surface_p05_m", "d3_surface_p95_m"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for i in range(track.n):
            row = [i, str(track.dt[i]), round(float(track.lat[i]), 6), round(float(track.lon[i]), 6),
                   r(track.alt[i]), r(alt_cal[i]), r(clr.terrain_elev[i]), r(clr.surface_elev[i]),
                   r(clr.v_terrain[i]), r(clr.d3_terrain[i]), r(clr.v_surface[i]), r(clr.d3_surface[i]),
                   int(clr.clipped[i]), int(levels[i])]
            if unc is not None:
                row += [r(unc.mean_terrain[i]), r(unc.p05_terrain[i]), r(unc.p95_terrain[i]),
                        r(unc.min_terrain[i]), r(unc.max_terrain[i]),
                        r(unc.mean_surface[i]), r(unc.p05_surface[i]), r(unc.p95_surface[i])]
            w.writerow(row)


def write_csv_events(path: Path, events: list[Event], unc=None) -> None:
    def r(x):
        return round(float(x), 1) if np.isfinite(x) else ""
    header = ["iso_time", "level", "reason", "phase", "lat", "lon", "altitude_m",
              "d3_terrain_m", "v_terrain_m", "d3_surface_m", "v_surface_m", "clipped"]
    if unc is not None:
        header += ["d3_terrain_mean_m", "d3_terrain_p05_m", "d3_terrain_p95_m"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for e in events:
            row = [e.iso_time, e.level, e.reason, e.phase, round(e.lat, 6), round(e.lon, 6),
                   round(e.altitude_m, 1), round(e.d3_terrain, 1), round(e.v_terrain, 1),
                   round(e.d3_surface, 1), round(e.v_surface, 1), int(e.clipped)]
            if unc is not None:
                row += [r(unc.mean_terrain[e.idx]), r(unc.p05_terrain[e.idx]), r(unc.p95_terrain[e.idx])]
            w.writerow(row)


def write_outputs(track: FlightTrack, alt_cal, clr: ClearanceResult, cal: CalibrationResult,
                  events: list[Event], levels, e, n, dtm, dsm, unc, meta: dict, cfg: Config) -> dict:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    stem = track.name
    paths = {
        "map": cfg.output_dir / f"{stem}_map.html",
        "barogram": cfg.output_dir / f"{stem}_barogram.html",
        "points": cfg.output_dir / f"{stem}_points.csv",
        "events": cfg.output_dir / f"{stem}_events.csv",
        "run": cfg.output_dir / f"{stem}_run.json",
    }
    if cfg.surface3d:
        paths["terrain3d"] = cfg.output_dir / f"{stem}_3d.html"

    map_fig = build_map(track, alt_cal, clr, events, cfg, unc)
    map_fig.write_html(str(paths["map"]), include_plotlyjs=True)
    build_barogram(track, alt_cal, clr, events, cfg, unc).write_html(str(paths["barogram"]), include_plotlyjs=True)
    if cfg.surface3d:
        t3d_fig = build_terrain3d(track, e, n, alt_cal, clr, events, dtm, dsm, cfg, unc)
        t3d_fig.write_html(str(paths["terrain3d"]), include_plotlyjs=True)
    if cfg.export_png:
        save_png(map_fig, cfg.output_dir / f"{stem}_map.png", 1500, 950)
        if cfg.surface3d:
            save_png(t3d_fig, cfg.output_dir / f"{stem}_3d.png", 1500, 1000)
    write_csv_points(paths["points"], track, alt_cal, clr, levels, unc)
    write_csv_events(paths["events"], events, unc)

    run = {
        "flight": stem,
        "source_file": str(track.path),
        "n_fixes": track.n,
        "altitude_source": track.alt_source,
        "calibration": asdict(cal),
        "n_events": len(events),
        **meta,
    }
    if unc is not None:
        run["uncertainty"] = {"sigma_h_m": unc.sigma_h, "sigma_v_m": unc.sigma_v,
                              "n_samples": unc.n_samples, "calib_iqr_m": cal.iqr_m}
    with open(paths["run"], "w", encoding="utf-8") as fh:
        json.dump(run, fh, indent=2, ensure_ascii=False)
    return paths
