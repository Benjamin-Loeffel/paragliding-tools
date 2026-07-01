"""Horizontwinkel je Azimut + Sky-View-Factor aus dem DTM (numpy Ray-March).

Einmal pro Gitter/Gelände berechnet und gecacht (tagesunabhängig). Pro Azimut wird
das Höhenfeld schrittweise verschoben und der maximale Erhebungswinkel verfolgt
(ganzzahlige Zell-Schritte, Nearest — ausreichend bei 10–20 m).
"""

from __future__ import annotations

import numpy as np


def _shift(z: np.ndarray, dr: int, dc: int, fill: float) -> np.ndarray:
    """z[row+dr, col+dc], ausserhalb -> fill."""
    ny, nx = z.shape
    out = np.full_like(z, fill)
    r0s, r1s = max(0, dr), min(ny, ny + dr)       # Ziel-Zeilenbereich (Quelle)
    c0s, c1s = max(0, dc), min(nx, nx + dc)
    r0d, r1d = max(0, -dr), min(ny, ny - dr)      # Zielbereich
    c0d, c1d = max(0, -dc), min(nx, nx - dc)
    if r0s < r1s and c0s < c1s:
        out[r0d:r1d, c0d:c1d] = z[r0s:r1s, c0s:c1s]
    return out


def _clean(z: np.ndarray) -> np.ndarray:
    zf = np.array(z, dtype=float)
    if not np.isfinite(zf).all():
        zf[~np.isfinite(zf)] = np.nanmean(zf)
    return zf


def _one_azimuth(zf: np.ndarray, a: float, res: float, step_m: float, max_steps: int) -> np.ndarray:
    """Horizont-Erhebungswinkel [ny,nx] für EINEN Azimut (Ray-March). Pro Azimut unabhängig."""
    ny, nx = zf.shape
    dr_unit = -np.cos(a)   # Azimut 0=N -> Richtung -Row
    dc_unit = np.sin(a)    # 90=O -> +Col
    maxang = np.full((ny, nx), -np.inf, dtype=float)
    last = (0, 0)
    for k in range(1, max_steps + 1):
        dist = k * step_m
        dr = int(round(dist / res * dr_unit))
        dc = int(round(dist / res * dc_unit))
        if (dr, dc) == last:
            continue
        last = (dr, dc)
        if abs(dr) >= ny and abs(dc) >= nx:
            break
        zs = _shift(zf, dr, dc, fill=-np.inf)
        with np.errstate(invalid="ignore"):
            ang = np.arctan2(zs - zf, dist)
        np.maximum(maxang, np.where(np.isfinite(zs), ang, -np.inf), out=maxang)
    return np.where(np.isfinite(maxang), np.maximum(maxang, 0.0), 0.0).astype(np.float32)


def _svf(horizon: np.ndarray) -> np.ndarray:
    # Isotrope SVF-Näherung (Dozier/Frew): 1 - mittlerer sin(Horizont)
    return (1.0 - np.mean(np.sin(np.clip(horizon, 0.0, np.pi / 2)), axis=0)).astype(np.float32)


def horizon_and_svf(z: np.ndarray, res: float, n_azimuth: int = 36,
                    max_steps: int = 600, step_m: float | None = None):
    """-> (horizon[n_az, ny, nx] Erhebungswinkel rad, azimuths rad, svf[ny,nx] 0..1)."""
    step_m = step_m or res
    zf = _clean(z)
    azimuths = np.linspace(0.0, 2 * np.pi, n_azimuth, endpoint=False)  # 0=N, im Uhrzeigersinn
    horizon = np.stack([_one_azimuth(zf, a, res, step_m, max_steps) for a in azimuths])
    return horizon, azimuths, _svf(horizon)


def _azimuth_chunk(args):
    """Pool-Worker: Horizont für eine Teilmenge Azimute (modul-level → picklebar für spawn)."""
    zf, res, azis, step_m, max_steps = args
    return np.stack([_one_azimuth(zf, a, res, step_m, max_steps) for a in azis])


def horizon_and_svf_parallel(z: np.ndarray, res: float, n_azimuth: int = 36,
                             max_steps: int = 600, step_m: float | None = None, workers: int = 4):
    """Wie horizon_and_svf, aber die (unabhängigen) Azimute auf `workers` Prozesse verteilt.

    Der Horizont ist bei feiner Auflösung der Flaschenhals (O(Zellen × Azimute × Schritte));
    Azimute sind vollständig unabhängig → sauber parallelisierbar. array_split liefert
    zusammenhängende, aufsteigende Azimut-Blöcke, darum stimmt die Reihenfolge nach concatenate."""
    from concurrent.futures import ProcessPoolExecutor
    step_m = step_m or res
    zf = _clean(z)
    azimuths = np.linspace(0.0, 2 * np.pi, n_azimuth, endpoint=False)
    chunks = [c for c in np.array_split(np.arange(n_azimuth), workers) if len(c)]
    tasks = [(zf, res, azimuths[c], step_m, max_steps) for c in chunks]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        parts = list(ex.map(_azimuth_chunk, tasks))
    horizon = np.concatenate(parts, axis=0).astype(np.float32)
    return horizon, azimuths, _svf(horizon)


def sun_is_shadowed(horizon: np.ndarray, azimuths: np.ndarray,
                    sun_az: float, sun_elev: float) -> np.ndarray:
    """Schattenmaske (True=beschattet) für einen Sonnenstand via Horizont-Lookup.
    Lineare Interpolation des Horizonts auf den Sonnen-Azimut."""
    if sun_elev <= 0:
        return np.ones(horizon.shape[1:], dtype=bool)
    n = len(azimuths)
    frac = (sun_az % (2 * np.pi)) / (2 * np.pi) * n
    i0 = int(np.floor(frac)) % n
    i1 = (i0 + 1) % n
    w = frac - np.floor(frac)
    hor = (1 - w) * horizon[i0] + w * horizon[i1]
    return sun_elev < hor
