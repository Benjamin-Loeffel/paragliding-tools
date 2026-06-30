"""D1 — Lagrange-Plume mit Ablöse-Modell: driftende Thermik-Trajektorien.

Zweiphasig (Recherche Zardi&Whiteman / XC Mag "The Hunt", ADR-0017):
  PHASE 1 — hangfolgender Aufstieg: Die Thermik ist kein freier Ballon, sondern ein
    "bent-over plume", der anabatisch am Hang hochläuft (Richtung bergauf = entgegen Aspekt),
    bis sie sich an einer markanten Geländeänderung ABLÖST: Konvexität (curvature über
    Perzentil-Schwelle), Grat/Gipfel (Höhe lokal maximal) oder Abflachung nach Steilhang.
  PHASE 2 — freier Plume: ab dem Release-Punkt Lenschow/Allen-Profil
    w(ẑ)=w*·ẑ^(1/3)·(1−1.1ẑ) + Höhenwind-Advektion bis Ceiling/w_min.

Der Release-Punkt (nicht der Hotspot) ist der Fusspunkt der driftenden Säule → realistischerer
Lee-Versatz. Validierbar: Steig-Einstiege sollten an Graten/Spornen über den Hotspots liegen.
"""

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass

import numpy as np

from .viz import draw_hillshade

Seed = namedtuple("Seed", "id e n elev")


@dataclass
class PlumeTrack:
    hotspot_id: int
    e: np.ndarray         # LV95 Ost entlang der Bahn
    n: np.ndarray         # LV95 Nord
    z: np.ndarray         # Höhe AMSL
    w: np.ndarray         # Vertikalgeschwindigkeit
    drift_m: float        # horizontaler Versatz Auslöser→Top
    bearing_deg: float    # Driftrichtung (wohin), 0=N
    duration_s: float
    release_idx: int = 0  # Index, an dem Phase 1 (hangfolgend) endet / Ablösung
    release_e: float = 0.0
    release_n: float = 0.0
    release_z: float = 0.0


def lenschow_w(z_agl, z_i, w_star):
    if z_i <= 0:
        return 0.0
    zh = z_agl / z_i
    if zh < 0 or zh > 0.95:
        return 0.0
    return float(w_star * zh ** (1.0 / 3.0) * (1.0 - 1.1 * zh))


def wind_uv(bl, z_amsl):
    """(u,v) [m/s] aus dem Sondierungs-Windprofil an Höhe z (meteorolog. Richtung = woher)."""
    zh, wd, ws = bl.wind_height_m, bl.wind_dir_deg, bl.wind_speed_ms
    if len(zh) == 0:
        return 0.0, 0.0
    d = np.interp(z_amsl, zh, wd)
    s = np.interp(z_amsl, zh, ws)
    u = -s * np.sin(np.radians(d))      # Ost-Komponente
    v = -s * np.cos(np.radians(d))      # Nord-Komponente
    return float(u), float(v)


def integrate_plume(e0, n0, z_surf, ceiling, w_star, bl, dt=10.0, max_steps=600,
                    w_min=0.4, valley=None, h_blend=400.0, wind_uv_fn=None) -> dict:
    """w_min = Schwelle nutzbaren Steigens (m/s): Aufstieg endet, wenn das Steigen darunter
    fällt — Piloten verlassen schwaches Steigen vor der w→0-Decke (sonst unrealistischer Drift).
    valley = optionales bodennahes Hangaufwind-Feld (Phase C); blendet über h_blend in den
    Sondierungswind über. wind_uv_fn(z)->(u,v) überschreibt optional den Sondierungswind."""
    e, n = float(e0), float(n0)
    z_i = ceiling - z_surf
    z = float(z_surf) + max(20.0, 0.05 * z_i)   # Start in der Arbeitsschicht (w=0 exakt am Boden)
    es, ns, zs, ws = [float(e0)], [float(n0)], [float(z_surf)], [0.0]
    for _ in range(max_steps):
        w = lenschow_w(z - z_surf, z_i, w_star)
        if w <= w_min:
            break
        u, v = wind_uv_fn(e, n, z) if wind_uv_fn is not None else wind_uv(bl, z)
        if valley is not None:                  # bodennah Hangaufwind, oben Sondierungswind
            uu, vv = valley.sample(e, n)
            f = float(np.clip((z - z_surf) / h_blend, 0.0, 1.0))
            u = (1 - f) * uu + f * u; v = (1 - f) * vv + f * v
        e += u * dt; n += v * dt; z += w * dt
        es.append(e); ns.append(n); zs.append(z); ws.append(w)
        if z >= ceiling - 1.0:
            break
    return {"e": np.array(es), "n": np.array(ns), "z": np.array(zs), "w": np.array(ws),
            "t": dt * (len(es) - 1)}


def _sample(field, e, n, grid):
    col = min(max(int((e - grid.west) / grid.res), 0), grid.nx - 1)
    row = min(max(int((grid.north - n) / grid.res), 0), grid.ny - 1)
    return float(field[row, col])


def release_curv_threshold(curvature, mask, pct=80.0) -> float:
    v = curvature[mask]; v = v[np.isfinite(v) & (v > 0)]
    return float(np.percentile(v, pct)) if v.size else 0.0


def _slope_follow(e0, n0, terrain, grid, c_crit, cfg, veg_edge=None):
    """Phase 1: hangaufwärts laufen bis Ablösung (Konvexität / Grat / Abflachung / Waldgrenze).
    veg_edge: bool-Feld der Vegetationskanten — dort genügt schon schwächere Konvexität (Faktor).
    Gibt (es, ns, zs) der hangfolgenden Bahn zurück (z = Geländehöhe)."""
    e, n = float(e0), float(n0)
    z = _sample(terrain.dtm, e, n, grid)
    es, ns, zs = [e], [n], [z]
    steep_seen = False
    for _ in range(cfg.d1_max_slope_steps):
        slp = np.degrees(_sample(terrain.slope, e, n, grid))
        if slp > 12.0:
            steep_seen = True
        up_az = _sample(terrain.aspect, e, n, grid) + np.pi      # bergauf = entgegen Aspekt
        e2 = e + cfg.d1_slope_step_m * np.sin(up_az)
        n2 = n + cfg.d1_slope_step_m * np.cos(up_az)
        z2 = _sample(terrain.dtm, e2, n2, grid)
        if z2 <= z + 0.5:                                        # Grat/Gipfel: geht nicht mehr hoch
            break
        e, n, z = e2, n2, z2
        es.append(e); ns.append(n); zs.append(z)
        curv = _sample(terrain.curvature, e, n, grid)
        at_edge = veg_edge is not None and _sample(veg_edge.astype(np.float32), e, n, grid) > 0.5
        thr = c_crit * cfg.d1_veg_edge_curv_factor if at_edge else c_crit
        if curv > thr:                                          # konvexe Kante (an Waldgrenze früher) → Ablösung
            break
        if steep_seen and np.degrees(_sample(terrain.slope, e, n, grid)) < cfg.d1_slope_flatten_deg:
            break
    return np.array(es), np.array(ns), np.array(zs)


def seeds_from_hotspots(hotspots):
    return [Seed(h.id, h.e, h.n, h.elev_m) for h in hotspots]


def seeds_from_points(points, terrain, grid, id0=0):
    """points = Liste von (e,n); Höhe aus dem DTM."""
    return [Seed(id0 + i, e, n, _sample(terrain.dtm, e, n, grid)) for i, (e, n) in enumerate(points)]


def grid_seeds(grid, mask, terrain, spacing_m=100.0):
    """Regelmässiges Startpunkt-Netz (nur im Gebiet)."""
    step = max(1, int(round(spacing_m / grid.res)))
    out = []
    for row in range(step // 2, grid.ny, step):
        for col in range(step // 2, grid.nx, step):
            if mask[row, col]:
                e = grid.west + (col + 0.5) * grid.res
                n = grid.north - (row + 0.5) * grid.res
                out.append(Seed(len(out), float(e), float(n), float(terrain.dtm[row, col])))
    return out


def run_plumes(seeds, bl, q_h_field, grid, terrain, cfg, valley=None, dt=10.0,
               wind_uv_fn=None, band_scale=1.0, veg_edge=None) -> list[PlumeTrack]:
    """Zweiphasige Plumes ab beliebigen Seeds (Hotspots/kk7/Netz).
    wind_uv_fn(e,n,z)->(u,v) überschreibt optional den Sondierungswind (zeitaufgelöster ICON-Wind).
    band_scale skaliert die nutzbare Bandtiefe (CBL-Tagesgang z_i(t)/z_i_peak).
    veg_edge: bool-Feld der Waldgrenzen (zusätzlicher Ablöse-Trigger)."""
    from .boundarylayer import strength_at
    c_crit = release_curv_threshold(terrain.curvature, _domain_mask(grid, terrain),
                                    cfg.d1_release_curv_pct)
    tracks = []
    for sd in seeds:
        sf_e, sf_n, sf_z = _slope_follow(sd.e, sd.n, terrain, grid, c_crit, cfg, veg_edge=veg_edge)
        re, rn, rz = float(sf_e[-1]), float(sf_n[-1]), float(sf_z[-1])
        s = strength_at(bl, rz, _sample(q_h_field, re, rn, grid), band_scale=band_scale)
        if s["w_star_ms"] <= 0 or s["z_i_m"] <= 50:
            continue
        tr = integrate_plume(re, rn, rz, s["ceiling_amsl"], s["w_star_ms"], bl,
                             dt=dt, valley=valley, wind_uv_fn=wind_uv_fn)
        # Phase 1 (hangfolgend) + Phase 2 (frei) verketten; Phase-1-Dauer aus u_slope
        e = np.concatenate([sf_e[:-1], tr["e"]]); n = np.concatenate([sf_n[:-1], tr["n"]])
        z = np.concatenate([sf_z[:-1], tr["z"]])
        w = np.concatenate([np.zeros(len(sf_e) - 1), tr["w"]])
        rel_idx = len(sf_e) - 1
        de, dn = e[-1] - e[0], n[-1] - n[0]
        sf_len = float(np.hypot(np.diff(sf_e), np.diff(sf_n)).sum())
        dur = tr["t"] + sf_len / max(cfg.d1_u_slope_ms, 0.1)
        tracks.append(PlumeTrack(
            hotspot_id=sd.id, e=e, n=n, z=z, w=w, drift_m=float(np.hypot(de, dn)),
            bearing_deg=float(np.degrees(np.arctan2(de, dn)) % 360.0), duration_s=dur,
            release_idx=rel_idx, release_e=re, release_n=rn, release_z=rz))
    return tracks


def _domain_mask(grid, terrain):
    return np.isfinite(terrain.dtm)


def plot_drift_map(grid, mask, dtm, tracks, d0_prob, path, title):
    """2D-Hillshade + D0-Quellfeld + Drift-Pfeile (Auslöser→Top, nach Drift gefärbt)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 12))
    ext = draw_hillshade(ax, dtm, grid)
    ax.imshow(np.where(mask, d0_prob, np.nan), cmap="viridis", extent=ext, origin="upper",
              alpha=0.55, interpolation="nearest")
    drifts = [t.drift_m for t in tracks] or [1.0]
    dmax = max(drifts)
    for t in tracks:
        ax.annotate("", xy=(t.e[-1], t.n[-1]), xytext=(t.e[0], t.n[0]),
                    arrowprops=dict(arrowstyle="->", color=plt.cm.viridis(t.drift_m / dmax),
                                    lw=1.6, alpha=0.9))
        ax.plot(t.e[0], t.n[0], "o", ms=3, color="white", mec="black", mew=0.4)
    ax.set_title(title); ax.set_xlabel("LV95 Ost [m]"); ax.set_ylabel("LV95 Nord [m]")
    ax.set_aspect("equal")
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=185, bbox_inches="tight"); plt.close(fig)
    return path


def plot_drift_quiver(grid, mask, dtm, tracks, d0_prob, path, title, arrow_m=130.0, wind_gw=None):
    """Drift-FELD (Netz-Seeds): Richtungspfeile fester Länge, nach Drift-Betrag gefärbt, über D0.
    Optional wind_gw: ICON-Windrichtung als feine graue Hintergrund-Streamlines zum Abgleich."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 12))
    ext = draw_hillshade(ax, dtm, grid)
    ax.imshow(np.where(mask, d0_prob, np.nan), cmap="viridis", extent=ext, origin="upper",
              alpha=0.5, interpolation="nearest")
    if wind_gw is not None:
        U, V = wind_gw.field_at_height(2500.0)
        xs = grid.west + (np.arange(grid.nx) + 0.5) * grid.res
        ys = grid.north - (np.arange(grid.ny) + 0.5) * grid.res
        ax.streamplot(xs, ys[::-1], U[::-1], V[::-1], color="0.25", density=1.4,
                      linewidth=0.6, arrowsize=0.6)
    e0 = np.array([t.e[0] for t in tracks]); n0 = np.array([t.n[0] for t in tracks])
    de = np.array([t.e[-1] - t.e[0] for t in tracks]); dn = np.array([t.n[-1] - t.n[0] for t in tracks])
    mag = np.hypot(de, dn); u = arrow_m * de / np.maximum(mag, 1e-6); v = arrow_m * dn / np.maximum(mag, 1e-6)
    q = ax.quiver(e0, n0, u, v, mag, angles="xy", scale_units="xy", scale=1.0,
                  cmap="viridis", width=0.0035, headwidth=3)
    fig.colorbar(q, ax=ax, shrink=0.6, label="Drift Auslöser→Top [m]")
    ax.set_title(title); ax.set_xlabel("LV95 Ost [m]"); ax.set_ylabel("LV95 Nord [m]")
    ax.set_aspect("equal"); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=185, bbox_inches="tight"); plt.close(fig)
    return path


def build_plume_3d(grid, mask, dtm, tracks, path, title):
    """3D-Relief (grau) + driftende Thermik-Säulen (nach Höhe gefärbt).
    Alle Spuren in EINEM Scatter3d (None-getrennt) → effizient auch bei vielen Hundert Spuren."""
    import plotly.graph_objects as go

    w, s, e, n = grid.bounds()
    xs = (np.arange(grid.nx) + 0.5) * grid.res
    ys = (grid.ny - np.arange(grid.ny) - 0.5) * grid.res
    z = np.where(mask, dtm, np.nan).astype(float)
    fig = go.Figure(go.Surface(x=xs, y=ys, z=z, colorscale="Greys", showscale=False,
                               opacity=0.9, hoverinfo="skip", lighting=dict(ambient=0.75, diffuse=0.5)))
    X, Y, Z, C = _plume_segments(tracks, w, s)
    if X:
        fig.add_trace(go.Scatter3d(
            x=X, y=Y, z=Z, mode="lines", connectgaps=False, hoverinfo="skip", showlegend=False,
            line=dict(width=3, color=C, colorscale="Viridis",
                      colorbar=dict(title="Höhe [m]"), showscale=True)))
    fig.update_layout(title=title, margin=dict(l=0, r=0, t=40, b=0),
                      scene=dict(xaxis_title="Ost [m]", yaxis_title="Nord [m]",
                                 zaxis_title="Höhe [m]", aspectmode="data"))
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    return fig


def _plume_segments(tracks, w, s):
    X, Y, Z, C = [], [], [], []
    for t in tracks:
        X += list(t.e - w) + [None]; Y += list(t.n - s) + [None]
        Z += list(t.z) + [None]; C += list(t.z) + [t.z[-1] if len(t.z) else 0.0]
    return X, Y, Z, C


def build_plume_3d_timeslider(grid, mask, dtm, tracks_by_hour, path, title):
    """3D-Relief + driftende Thermik-Säulen mit ZEIT-SLIDER (11/13/15/18 h).
    tracks_by_hour: {Stunde: [PlumeTrack,…]} — pro Uhrzeit ein Frame (Wind/w*/z_i tageszeitabhängig)."""
    import plotly.graph_objects as go

    w, s, e, n = grid.bounds()
    xs = (np.arange(grid.nx) + 0.5) * grid.res
    ys = (grid.ny - np.arange(grid.ny) - 0.5) * grid.res
    zsurf = np.where(mask, dtm, np.nan).astype(float)
    surface = go.Surface(x=xs, y=ys, z=zsurf, colorscale="Greys", showscale=False, opacity=0.9,
                         hoverinfo="skip", lighting=dict(ambient=0.75, diffuse=0.5))
    hours = sorted(tracks_by_hour)
    cmin = float(np.nanmin(zsurf))
    cmax = max((max((t.z.max() for t in tracks_by_hour[h] if len(t.z)), default=cmin)
                for h in hours), default=cmin + 1)

    def trace(tracks):
        X, Y, Z, C = _plume_segments(tracks, w, s)
        return go.Scatter3d(x=X or [None], y=Y or [None], z=Z or [None], mode="lines",
                            connectgaps=False, hoverinfo="skip", showlegend=False,
                            line=dict(width=3, color=C or [cmin], colorscale="Viridis",
                                      cmin=cmin, cmax=cmax, colorbar=dict(title="Höhe [m]"), showscale=True))

    frames = [go.Frame(data=[trace(tracks_by_hour[h])], name=f"{h:02d}", traces=[1]) for h in hours]
    fig = go.Figure(data=[surface, trace(tracks_by_hour[hours[0]])], frames=frames)
    steps = [dict(method="animate", label=f"{h:02d}:00",
                  args=[[f"{h:02d}"], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                           transition=dict(duration=0))]) for h in hours]
    fig.update_layout(title=title, margin=dict(l=0, r=0, t=40, b=0),
                      sliders=[dict(active=0, currentvalue=dict(prefix="Uhrzeit "), pad=dict(t=40),
                                    steps=steps)],
                      scene=dict(xaxis_title="Ost [m]", yaxis_title="Nord [m]",
                                 zaxis_title="Höhe [m]", aspectmode="data"))
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=True)
    return fig


def seeds_from_field(field, grid, mask, terrain, pct=75.0, max_seeds=500):
    """Seeds aus den Zellen mit hohem Feldwert (z. B. kk7-Dichte) — Top-Perzentil, ausgedünnt."""
    v = field[mask & np.isfinite(field)]
    if v.size == 0:
        return []
    thr = float(np.percentile(v, pct))
    rows, cols = np.where(mask & np.isfinite(field) & (field >= thr))
    if len(rows) > max_seeds:                       # gleichmässig ausdünnen
        step = len(rows) // max_seeds + 1
        rows, cols = rows[::step], cols[::step]
    out = []
    for i, (r, c) in enumerate(zip(rows, cols)):
        e = grid.west + (c + 0.5) * grid.res; n = grid.north - (r + 0.5) * grid.res
        out.append(Seed(i, float(e), float(n), float(terrain.dtm[r, c])))
    return out
