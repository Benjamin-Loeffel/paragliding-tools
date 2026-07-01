"""Standardplots fürs Flugtag-Briefing — CH-weiter Kontext + Frutigen-Umkreis.

Zwei Deliverables (im projektweiten `plotstyle`: gross, hohe DPI, feine Schrift):
  * `plot_ch_overview`     — nationale Übersicht: Tages-Max-Niederschlag (+Gewitter),
                             700-hPa-Höhenwind (Betrag + Richtungspfeile), Tages-Max-CAPE.
  * `plot_frutigen_radius` — Umkreis Frutigen (~±24 km): Niederschlag/Gewitter/CAPE als
                             Tages-Zeitreihe + kleine Regionalkarte (Tages-Max-Niederschlag).

Verbraucht ein `synoptic.Synoptic`-Objekt (Open-Meteo ICON-CH). Farbpolitik wie Repo:
viridis/inferno sequential, Wind cividis; Niederschlag YlGnBu; Gewitter rot markiert.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

import synoptic as S


def _use():
    """Zentralen Repo-Plotstil laden (fügt src/ bei Bedarf zum Pfad); gibt pyplot zurück."""
    try:
        from thermalmodel.plotstyle import use
    except ModuleNotFoundError:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from thermalmodel.plotstyle import use
    return use()


def _reshape_ch(syn, key: str) -> np.ndarray:
    """CH-Punktreihe [npts,nh] → Gitter [nlat,nlon,nh] (ch_grid nutzte meshgrid ij)."""
    nlat, nlon = syn.ch_lats.size, syn.ch_lons.size
    return syn.ch[key].reshape(nlat, nlon, -1)


def _peak_hour_idx(syn, target_hour: int = 14) -> int:
    hrs = np.array([t.hour + t.minute / 60.0 for t in syn.times])
    return int(np.argmin(np.abs(hrs - target_hour)))


def _uv_from_dir(spd: np.ndarray, drc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Meteorologische Richtung (woher) → (u,v)-Komponenten (wohin)."""
    r = np.radians(drc)
    return -spd * np.sin(r), -spd * np.cos(r)


def plot_ch_overview(syn, path, title: str):
    plt = _use()

    lons, lats = syn.ch_lons, syn.ch_lats
    precip = np.nanmax(_reshape_ch(syn, "precipitation"), axis=2)     # Tages-Max mm/h
    cape = np.nanmax(_reshape_ch(syn, "cape"), axis=2)
    wc = _reshape_ch(syn, "weather_code")
    thunder = np.isin(wc, list(S.THUNDER_CODES)).any(axis=2)          # [nlat,nlon] bool
    idx = _peak_hour_idx(syn, 14)
    wspd = _reshape_ch(syn, "wind_speed_700hPa")[:, :, idx]
    wdir = _reshape_ch(syn, "wind_direction_700hPa")[:, :, idx]
    u, v = _uv_from_dir(wspd, wdir)
    Lo, La = np.meshgrid(lons, lats)

    fig, axes = plt.subplots(1, 3, figsize=(22, 9), constrained_layout=True)
    for ax in axes:
        ax.set_aspect(1.0 / np.cos(np.radians(46.8)))   # grobe Mercator-Korrektur
        ax.set_xlabel("Länge [°E]")
        ax.plot(S.FRUTIGEN_LON, S.FRUTIGEN_LAT, "*", ms=16, color="magenta",
                mec="black", mew=0.8, zorder=5, label="Frutigen")

    # 1) Niederschlag + Gewitter
    im0 = axes[0].pcolormesh(lons, lats, precip, cmap="YlGnBu", shading="auto",
                             vmin=0, vmax=max(1.0, float(np.nanpercentile(precip, 98))))
    if thunder.any():
        axes[0].scatter(Lo[thunder], La[thunder], s=45, marker="x", c="red", linewidths=1.4,
                        label="Gewitter (weather_code)")
    axes[0].set_title("Tages-Max Niederschlag [mm/h] + Gewitter"); axes[0].set_ylabel("Breite [°N]")
    fig.colorbar(im0, ax=axes[0], shrink=0.6, label="mm/h"); axes[0].legend(loc="upper left")

    # 2) 700-hPa-Höhenwind (~14 h): Betrag + Richtung
    im1 = axes[1].pcolormesh(lons, lats, wspd, cmap="cividis", shading="auto",
                             vmin=0, vmax=max(10.0, float(np.nanpercentile(wspd, 98))))
    axes[1].quiver(Lo, La, u, v, color="white", scale=700, width=0.004, alpha=0.9)
    axes[1].set_title("700-hPa-Wind ~14 h [km/h]")
    fig.colorbar(im1, ax=axes[1], shrink=0.6, label="km/h")

    # 3) CAPE Tages-Max
    im2 = axes[2].pcolormesh(lons, lats, cape, cmap="inferno", shading="auto",
                             vmin=0, vmax=max(300.0, float(np.nanpercentile(cape, 98))))
    axes[2].set_title("Tages-Max CAPE [J/kg]")
    fig.colorbar(im2, ax=axes[2], shrink=0.6, label="J/kg")

    fig.suptitle(title)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path); plt.close(fig)
    return path


def _daytime_idx(syn, h0: int = 6, h1: int = 21) -> np.ndarray:
    hrs = np.array([t.hour for t in syn.times])
    idx = np.where((hrs >= h0) & (hrs <= h1))[0]
    return idx if idx.size else np.arange(len(syn.times))


def _slider(steps_labels, active, prefix):
    steps = [dict(method="animate", label=lbl,
                  args=[[lbl], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                    transition=dict(duration=0))]) for lbl in steps_labels]
    return [dict(active=active, currentvalue=dict(prefix=prefix), pad=dict(t=45), steps=steps)]


# --- Farbskalen (Vorbild MeteoSchweiz-Radar) ---
PRECIP_COLORSCALE = [                         # Radar-Skala mm/h; trocken = transparent
    [0.00, "rgba(43,131,186,0.0)"], [0.03, "rgba(43,131,186,0.55)"],
    [0.15, "#2b83ba"], [0.30, "#66c2a5"], [0.45, "#abdda4"],
    [0.60, "#ffffbf"], [0.72, "#fdae61"], [0.85, "#d7191c"], [1.00, "#7b3294"],
]
PRECIP_ZMAX = 15.0                            # mm/h — feste Skala (tagesübergreifend vergleichbar)
SOLAR_COLORSCALE = "Inferno"
SOLAR_ZMAX = 1000.0                           # W/m²
WIND_COLORSCALE = [                           # grün ruhig → gelb ~25 km/h (Schwelle) → rot ab ~60
    [0.00, "#1a9850"], [0.20, "#66bd63"], [0.36, "#fee08b"],
    [0.55, "#fdae61"], [0.75, "#f46d43"], [1.00, "#a50026"],
]
WIND_ZMAX = 70.0                              # km/h

CH_WIND_LEVELS = [
    ("10 m",              "wind_speed_10m",    "wind_direction_10m"),
    ("850 hPa (~1500 m)", "wind_speed_850hPa", "wind_direction_850hPa"),
    ("700 hPa (~3000 m)", "wind_speed_700hPa", "wind_direction_700hPa"),
    ("500 hPa (~5500 m)", "wind_speed_500hPa", "wind_direction_500hPa"),
]


def _init_hour(syn, key, idxs):
    means = [np.nanmean(syn.ch[key][:, i]) for i in idxs]
    return int(np.nanargmax(means)) if np.isfinite(means).any() else 0


def _cells_geojson(syn):
    """Ein Rechteck-Polygon je CH-Gitterpunkt (für go.Choropleth). Gibt (geojson, locations)."""
    h = S.CH_GRID_STEP_DEG / 2.0
    lon, lat = syn.ch["lon"], syn.ch["lat"]
    feats, locs = [], []
    for i in range(lon.size):
        lo, la = float(lon[i]), float(lat[i])
        feats.append({"type": "Feature", "id": i, "geometry": {"type": "Polygon", "coordinates": [[
            [lo - h, la - h], [lo + h, la - h], [lo + h, la + h], [lo - h, la + h], [lo - h, la - h]]]}})
        locs.append(i)
    return {"type": "FeatureCollection", "features": feats}, locs


def _geo_layout():
    """Dunkle Schweiz-Silhouette mit Kantons-/See-Umrissen (Natural-Earth, kein WebGL, keine Tiles)."""
    return dict(scope="europe", resolution=50, projection_type="mercator",
                lonaxis=dict(range=[5.7, 10.7]), lataxis=dict(range=[45.7, 47.95]),
                showcountries=True, countrycolor="rgb(235,235,235)", countrywidth=1.6,
                showsubunits=True, subunitcolor="rgb(150,150,150)", subunitwidth=0.6,
                showlakes=True, lakecolor="rgb(35,55,80)",
                showland=True, landcolor="rgb(17,17,17)", showframe=False,
                showcoastlines=False, bgcolor="rgba(0,0,0,0)")


REF_POINTS = [   # (Name, lon, lat) — Orientierung auf der Karte; Frutigen hervorgehoben
    ("Frutigen", S.FRUTIGEN_LON, S.FRUTIGEN_LAT), ("Bern", 7.44, 46.95),
    ("Zürich", 8.54, 47.38), ("Genève", 6.14, 46.20), ("Lugano", 8.96, 46.00),
    ("Interlaken", 7.87, 46.68), ("Chur", 9.53, 46.85),
]


def _reference_markers():
    """Frutigen (magenta Stern) + einige Städte (Orientierung), als oberste Ebene."""
    import plotly.graph_objects as go
    names = [p[0] for p in REF_POINTS]
    sizes = [11 if n == "Frutigen" else 5 for n in names]
    colors = ["magenta" if n == "Frutigen" else "white" for n in names]
    return go.Scattergeo(lon=[p[1] for p in REF_POINTS], lat=[p[2] for p in REF_POINTS],
                         mode="markers+text", text=names, textposition="top center",
                         textfont=dict(size=9, color="white"),
                         marker=dict(size=sizes, color=colors, line=dict(width=0.5, color="black")),
                         name="Orte", hoverinfo="text")


def build_ch_slider(syn, key, path, title, colorscale, unit, zmax):
    """CH-Karte eines Skalarfelds als gefüllte Gitterzellen (go.Choropleth auf geo) + ZEIT-SLIDER.
    Self-contained (kein WebGL, keine Tiles); feste `zmax` → tagesübergreifend vergleichbar."""
    import plotly.graph_objects as go
    geojson, locs = _cells_geojson(syn)
    field = np.nan_to_num(syn.ch[key], nan=0.0)
    idxs = _daytime_idx(syn)
    labels = [f"{syn.times[i].hour:02d}:00" for i in idxs]
    init = _init_hour(syn, key, idxs)

    def cho(i, base):
        z = field[:, i]
        kw = dict(locations=locs, z=z, featureidkey="id",
                  text=[f"{v:.1f} {unit}" for v in z], hoverinfo="text")
        if base:                       # Geometrie/Styling nur im Basis-Trace; Frames tragen nur z+Text
            kw.update(geojson=geojson, colorscale=colorscale, zmin=0.0, zmax=zmax,
                      marker_line_width=0, marker_opacity=0.6, colorbar=dict(title=unit))
        return go.Choropleth(**kw)

    frames = [go.Frame(data=[cho(i, False)], name=labels[k], traces=[0]) for k, i in enumerate(idxs)]
    fig = go.Figure(data=[cho(idxs[init], True), _reference_markers()], frames=frames)
    fig.update_layout(title=title, margin=dict(l=0, r=0, t=40, b=0),
                      geo=_geo_layout(), paper_bgcolor="rgb(8,8,8)",
                      font=dict(color="rgb(220,220,220)"), sliders=_slider(labels, init, "Zeit "))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    return path


def build_ch_precip(syn, path, date):
    return build_ch_slider(syn, "precipitation", path, f"Niederschlag CH (mm/h) — {date}",
                           PRECIP_COLORSCALE, "mm/h", PRECIP_ZMAX)


def build_ch_solar(syn, path, date):
    return build_ch_slider(syn, "shortwave_radiation", path, f"Sonneneinstrahlung CH — {date}",
                           SOLAR_COLORSCALE, "W/m²", SOLAR_ZMAX)


def _arrow_paths(lon, lat, u, v, step_deg=0.09, head=0.38):
    """Downwind-Pfeile (Schaft + V-Spitze) als None-getrennte lon/lat-Listen für Scattergeo-lines.
    u,v = Komponenten wohin (aus _uv_from_dir); feste Länge = Richtungsfeld; lon per cos(lat) korrigiert."""
    alon, alat = [], []
    for i in range(len(lon)):
        sp = float(np.hypot(u[i], v[i]))
        if not np.isfinite(sp) or sp < 1e-6:
            continue
        cs = max(np.cos(np.radians(lat[i])), 0.3)
        dx, dy = u[i] / sp, v[i] / sp                          # Einheitsrichtung (wohin)
        tlo = lon[i] + step_deg * dx / cs; tla = lat[i] + step_deg * dy      # Spitze
        h = []
        for ang in (2.618, -2.618):                            # ±150° → Pfeilspitze
            ca, sa = np.cos(ang), np.sin(ang)
            hx, hy = dx * ca - dy * sa, dx * sa + dy * ca
            h.append((tlo + step_deg * head * hx / cs, tla + step_deg * head * hy))
        alon += [float(lon[i]), tlo, h[0][0], tlo, h[1][0], None]
        alat += [float(lat[i]), tla, h[0][1], tla, h[1][1], None]
    return alon, alat


def _wind_subsample(syn, stride=2):
    """Jeder stride-te Gitterpunkt in beiden Richtungen (für ein lesbares Pfeilfeld)."""
    nlat, nlon = syn.ch_lats.size, syn.ch_lons.size
    keep = [ilat * nlon + ilon for ilat in range(0, nlat, stride) for ilon in range(0, nlon, stride)]
    return np.array([k for k in keep if k < syn.ch["lon"].size], int)


def build_ch_wind_slider(syn, path, title, default_level: int = 2):
    """CH-Windkarte: gefülltes Betragsfeld (go.Choropleth) + DOWNWIND-PFEILE (Richtung), mit
    Höhenstufen-DROPDOWN + ZEIT-SLIDER. Farbe = Betrag (grün ruhig → gelb ~25 km/h → rot),
    dunkle Pfeile = Strömungsrichtung (wie die wind_traces); Hover = Betrag + Richtung."""
    import plotly.graph_objects as go
    geojson, locs = _cells_geojson(syn)
    idxs = _daytime_idx(syn)
    labels = [f"{syn.times[i].hour:02d}:00" for i in idxs]
    have = [lv for lv in CH_WIND_LEVELS if lv[1] in syn.ch and np.isfinite(syn.ch[lv[1]]).any()]
    default_level = min(default_level, len(have) - 1)
    init = _init_hour(syn, have[default_level][1], idxs)
    sub = _wind_subsample(syn, stride=2)
    slon, slat = syn.ch["lon"][sub], syn.ch["lat"][sub]
    N = len(have)

    def cho(spk, drk, i, base, visible=None):
        sp = np.nan_to_num(syn.ch[spk][:, i], nan=0.0); dr = np.nan_to_num(syn.ch[drk][:, i], nan=0.0)
        kw = dict(locations=locs, z=sp, featureidkey="id",
                  text=[f"{s:.0f} km/h aus {d:.0f}°" for s, d in zip(sp, dr)], hoverinfo="text")
        if base:                       # Geometrie/Styling nur im Basis-Trace; Frames tragen nur z+Text
            kw.update(geojson=geojson, colorscale=WIND_COLORSCALE, zmin=0.0, zmax=WIND_ZMAX,
                      marker_line_width=0, marker_opacity=0.6, colorbar=dict(title="km/h"))
            if visible is not None:
                kw["visible"] = visible
        return go.Choropleth(**kw)

    def arr(spk, drk, i, base, visible=None):
        sp = np.nan_to_num(syn.ch[spk][sub, i], nan=0.0); dr = np.nan_to_num(syn.ch[drk][sub, i], nan=0.0)
        u, v = _uv_from_dir(sp, dr)
        alon, alat = _arrow_paths(slon, slat, u, v)
        kw = dict(lon=alon, lat=alat)
        if base:
            kw.update(mode="lines", line=dict(width=1.1, color="rgba(10,10,10,0.85)"),
                      hoverinfo="skip", showlegend=False, visible=visible)
        return go.Scattergeo(**kw)

    base = [cho(lv[1], lv[2], idxs[init], True, visible=(j == default_level)) for j, lv in enumerate(have)]
    base += [arr(lv[1], lv[2], idxs[init], True, visible=(j == default_level)) for j, lv in enumerate(have)]
    base.append(_reference_markers())
    frames = [go.Frame(name=labels[k],
                       data=[cho(lv[1], lv[2], i, False) for lv in have]
                            + [arr(lv[1], lv[2], i, False) for lv in have],
                       traces=list(range(2 * N))) for k, i in enumerate(idxs)]
    buttons = [dict(label=lv[0], method="update",
                    args=[{"visible": [j == jj for jj in range(N)]       # Choropleth-Felder
                                    + [j == jj for jj in range(N)]       # Pfeil-Overlays
                                    + [True]}])                          # Orte
               for j, lv in enumerate(have)]
    fig = go.Figure(data=base, frames=frames)
    fig.update_layout(title=title, margin=dict(l=0, r=0, t=40, b=0),
                      geo=_geo_layout(), paper_bgcolor="rgb(8,8,8)", font=dict(color="rgb(220,220,220)"),
                      updatemenus=[dict(buttons=buttons, x=0.01, y=0.99, xanchor="left",
                                        yanchor="top", bgcolor="white", active=default_level)],
                      sliders=_slider(labels, init, "Zeit "))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    return path


def plot_frutigen_radius(syn, path, title: str):
    plt = _use()

    f = syn.frutigen
    hrs = np.array([t.hour + t.minute / 60.0 for t in syn.times])
    precip = np.nanmax(f["precipitation"], axis=0)       # Worst-Case im Umkreis, je Stunde
    cape = np.nanmax(f["cape"], axis=0)
    cloud = np.nanmean(f["cloud_cover"], axis=0)
    pop = np.nanmax(f["precipitation_probability"], axis=0)
    thunder_h = np.isin(f["weather_code"], list(S.THUNDER_CODES)).any(axis=0)  # je Stunde

    fig, (ax, axm) = plt.subplots(1, 2, figsize=(20, 8.5), width_ratios=[2.3, 1],
                                  constrained_layout=True)

    # --- Zeitreihe ---
    ax.bar(hrs, precip, width=0.8, color="#2c7fb8", alpha=0.85, label="Niederschlag [mm/h]")
    ax.set_xlabel("Lokalzeit [h]"); ax.set_ylabel("Niederschlag [mm/h]", color="#2c7fb8")
    ax.set_ylim(0, max(1.0, float(np.nanmax(precip)) * 1.15)); ax.set_xlim(hrs.min(), hrs.max())
    for h in hrs[thunder_h]:
        ax.axvspan(h - 0.5, h + 0.5, color="red", alpha=0.12)
    if thunder_h.any():
        ax.scatter(hrs[thunder_h], np.full(thunder_h.sum(), 0), marker="^", s=90, c="red",
                   zorder=6, label="Gewitter-Code")
    ax2 = ax.twinx()
    ax2.plot(hrs, cape, color="#e6550d", lw=2, label="CAPE [J/kg]")
    ax2.plot(hrs, cloud, color="slategray", lw=1.6, ls="--", label="Bewölkung [%]")
    ax2.plot(hrs, pop, color="#31a354", lw=1.4, ls=":", label="Niederschlags-Wahrsch. [%]")
    ax2.set_ylabel("CAPE [J/kg]  ·  Bewölkung / P(N) [%]")
    ax2.set_ylim(0, max(100.0, float(np.nanmax(cape)) * 1.1))
    l1, la1 = ax.get_legend_handles_labels(); l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, loc="upper left", framealpha=0.85)
    ax.set_title("Frutigen ±24 km — Tagesverlauf")

    # --- kleine Regionalkarte (Tages-Max Niederschlag im Umkreis) ---
    n = S.FRUTIGEN_RADIUS_N
    pr = np.nanmax(f["precipitation"], axis=1).reshape(n, n)
    lo = f["lon"].reshape(n, n)[0]; la = f["lat"].reshape(n, n)[:, 0]
    imm = axm.pcolormesh(lo, la, pr, cmap="YlGnBu", shading="auto", vmin=0,
                         vmax=max(1.0, float(np.nanmax(pr))))
    axm.plot(S.FRUTIGEN_LON, S.FRUTIGEN_LAT, "*", ms=18, color="magenta", mec="black", mew=0.8)
    axm.set_aspect(1.0 / np.cos(np.radians(46.6)))
    axm.set_title("Tages-Max Niederschlag [mm/h]"); axm.set_xlabel("Länge [°E]"); axm.set_ylabel("Breite [°N]")
    fig.colorbar(imm, ax=axm, shrink=0.6, label="mm/h")

    fig.suptitle(title)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path); plt.close(fig)
    return path
