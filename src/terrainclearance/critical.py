"""Kritische Flugmomente aus den Abstands-Zeitreihen ableiten."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config
from .igc_loader import FlightTrack
from .terrain import ClearanceResult

_LEVEL_NAME = {0: "ok", 1: "achtung", 2: "warnung", 3: "gefahr"}


@dataclass
class Event:
    idx: int
    t_s: float
    iso_time: str
    lat: float
    lon: float
    altitude_m: float
    d3_terrain: float
    v_terrain: float
    d3_surface: float
    v_surface: float
    level: str
    reason: str
    phase: str       # 'Flug' | 'Landeanflug'
    clipped: bool


def _rank(value: float, thresholds: tuple[float, float, float]) -> int:
    caution, warning, danger = thresholds
    if not np.isfinite(value):
        return 0
    if value < danger:
        return 3
    if value < warning:
        return 2
    if value < caution:
        return 1
    return 0


def point_levels(clr: ClearanceResult, cfg: Config) -> np.ndarray:
    """Pro Fix die kombinierte Kritikalität (0..3) aus Gelände- und Oberflächenabstand."""
    rt = np.array([_rank(v, cfg.crit_terrain_m) for v in clr.d3_terrain])
    rs = np.array([_rank(v, cfg.crit_surface_m) for v in clr.d3_surface])
    return np.maximum(rt, rs)


def find_events(track: FlightTrack, clr: ClearanceResult, alt_cal: np.ndarray,
                airborne: np.ndarray, landing_alt: float, cfg: Config) -> list[Event]:
    ranks = point_levels(clr, cfg)
    flagged = (ranks >= 1) & airborne
    N = track.n

    # Zusammenhängende kritische Abschnitte -> Tiefpunkt je Abschnitt
    candidates: list[int] = []
    i = 0
    while i < N:
        if flagged[i]:
            j = i
            while j < N and flagged[j]:
                j += 1
            # Index des kleinsten Gelände-Abstands im Abschnitt (NaN ignorieren)
            seg = clr.d3_terrain[i:j].copy()
            if np.all(np.isnan(seg)):
                seg = -ranks[i:j].astype(float)  # Fallback: höchster Rang
            k = i + int(np.nanargmin(seg))
            candidates.append(k)
            i = j
        else:
            i += 1

    # Debounce: nahe Events zusammenfassen, schlimmeres behalten
    merged: list[int] = []
    for k in candidates:
        if merged and (track.t_s[k] - track.t_s[merged[-1]]) < cfg.event_min_separation_s:
            if _event_key(clr, k) < _event_key(clr, merged[-1]):
                merged[-1] = k
        else:
            merged.append(k)

    events = []
    for k in merged:
        rt = _rank(clr.d3_terrain[k], cfg.crit_terrain_m)
        rs = _rank(clr.d3_surface[k], cfg.crit_surface_m)
        rank = max(rt, rs)
        reason = "Gelände" if rt >= rs else "Wald/Objekt"
        # Landeanflug = nahe Landeplatzhöhe UND danach kein nennenswertes Steigen
        climb_after = float(np.nanmax(alt_cal[k:])) - float(alt_cal[k])
        near_landing = (float(alt_cal[k]) - landing_alt) < cfg.landing_approach_height_m
        phase = ("Landeanflug" if near_landing and climb_after < cfg.landing_climb_threshold_m
                 else "Flug")
        events.append(Event(
            idx=k,
            t_s=float(track.t_s[k]),
            iso_time=str(track.dt[k]),
            lat=float(track.lat[k]),
            lon=float(track.lon[k]),
            altitude_m=float(alt_cal[k]),
            d3_terrain=float(clr.d3_terrain[k]),
            v_terrain=float(clr.v_terrain[k]),
            d3_surface=float(clr.d3_surface[k]),
            v_surface=float(clr.v_surface[k]),
            level=_LEVEL_NAME[rank],
            reason=reason,
            phase=phase,
            clipped=bool(clr.clipped[k]),
        ))
    return events


def _event_key(clr: ClearanceResult, k: int) -> float:
    """Kleiner = kritischer. Nutzt den kleineren der beiden Abstände."""
    vals = [v for v in (clr.d3_terrain[k], clr.d3_surface[k]) if np.isfinite(v)]
    return min(vals) if vals else np.inf
