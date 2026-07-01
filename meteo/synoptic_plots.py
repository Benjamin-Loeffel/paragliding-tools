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
