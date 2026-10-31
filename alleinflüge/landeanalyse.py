#!/usr/bin/env python
"""Landeanalyse: Volte aus dem IGC zerlegen und mit dem gemessenen Wind am Landeplatz lesen.

    analyse   IGC -> Touchdown, Abstand zum Zielpunkt (zu kurz/zu weit, seitlich), Volte in
              Segmente (Gegen-, Quer-, Endanflug, Kurven) mit Höhe AGL, Grundgeschwindigkeit,
              Sinken, Gleitzahl über Grund, Luftgeschwindigkeit und Vorhaltewinkel
              (Grund- minus Windvektor). Plot: Grundriss + Höhenprofil.
              Prüfregeln der SHV-Weisung (letzte 5 s gerade, S-Kurven ≤ 90°, Queranflug-Kurven
              ≤ 200°, Höhenabbau luvseitig, Kreis 34 m Ø) und Wind auf Volten-Höhe aus den Kreisen.
    plan      Ideale Höhen an den Eckpunkten der Volte je Gegenwind — rückwärts vom Zielpunkt
              gerechnet, kalibriert auf die eigenen Lehn-Flüge (Fahrt/Sinken je Abschnitt).

Wind: Holfuy-2-min-Reihe aus `lagecheck.py archiv` (am Flugtag selbst sichern, Vortage gibt
Holfuy nur noch 15-min). Der Wind am Mast (10 m) ist schwächer als auf 50–150 m AGL — die
Luftgeschwindigkeit daraus ist eine Schätzung, der Vergleich zwischen Flügen bleibt gültig.

Beispiele:
    python alleinflüge/landeanalyse.py analyse D:/.../2026-10-31-XTR-...-02.IGC --ziel lehn \
        --wind alleinflüge/archiv/2026-10-31_interlaken/roh/holfuy-1850_15min.json
    python alleinflüge/landeanalyse.py plan --gegenwind 0,5,10,15,20
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Zielpunkte (LV95 E, N, Höhe m ü. M., Zielkreis-Radius m). Lehn: Mitte des gemähten Zielkreises
# laut Benjamin (map.geo.admin.ch, 31.10.2026), Kreis r = 15 m.
ZIELE = {"lehn": (2629453.66, 1170022.09, 565.1, 15.0)}
OUT = Path(__file__).resolve().parent / "lagecheck_out"   # gitignored

KLASSEN = ("End", "Quer", "Gegen")


# ------------------------------------------------------------------ IGC

@dataclass
class Track:
    t: np.ndarray        # Sekunden seit Mitternacht, Lokalzeit
    e: np.ndarray        # LV95
    n: np.ndarray
    baro: np.ndarray     # Druckhöhe (ISA), m
    gnss: np.ndarray     # GNSS-Höhe, m
    datum: dt.date
    utc_offset_h: int


def lade_igc(pfad: str) -> Track:
    from pyproj import Transformer
    from zoneinfo import ZoneInfo
    tr = Transformer.from_crs(4326, 2056, always_xy=True)
    datum, rows = None, []
    for z in Path(pfad).read_text(encoding="latin-1").splitlines():
        if z.startswith("HFDTE"):
            d = z[5:].split(":")[-1][:6]
            datum = dt.date(2000 + int(d[4:6]), int(d[2:4]), int(d[0:2]))
        elif z.startswith("B") and len(z) >= 35 and z[24] == "A":
            s = int(z[1:3]) * 3600 + int(z[3:5]) * 60 + int(z[5:7])
            la = (int(z[7:9]) + int(z[9:14]) / 60000) * (1 if z[14] == "N" else -1)
            lo = (int(z[15:18]) + int(z[18:23]) / 60000) * (1 if z[23] == "E" else -1)
            rows.append((s, lo, la, int(z[25:30]), int(z[30:35])))
    a = np.array(rows, float)
    e, n = tr.transform(a[:, 1], a[:, 2])
    off = int(dt.datetime.combine(datum, dt.time(12), ZoneInfo("Europe/Zurich")).utcoffset().total_seconds() // 3600)
    return Track(a[:, 0] + off * 3600, np.asarray(e), np.asarray(n), a[:, 3], a[:, 4], datum, off)


def _hms(s: float) -> str:
    s = int(round(s)) % 86400
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}"


# ------------------------------------------------------------------ Wind (Holfuy-Archiv)

def lade_wind(pfad: str | None) -> list[tuple[float, float, float, float]]:
    """[(sek. Lokalzeit, Richtung aus °, Mittel km/h, Böe km/h)] aus der Holfuy-Archivdatei."""
    if not pfad:
        return []
    out = []
    for x in json.loads(Path(pfad).read_text(encoding="utf-8")):
        t = dt.datetime.strptime(x["zeit"], "%Y/%m/%d %H:%M:%S")
        if x.get("mittel") is not None and x.get("richtung") is not None:
            out.append((t.hour * 3600 + t.minute * 60 + t.second, float(x["richtung"]),
                        float(x["mittel"]), float(x.get("boee") or x["mittel"])))
    return out


def wind_im_fenster(wind, t0: float, t1: float):
    """Vektormittel (Richtung aus, km/h), Böe max., Anzahl Werte im Fenster [t0, t1]."""
    w = [x for x in wind if t0 <= x[0] <= t1]
    if not w:
        return None
    u = sum(v * math.sin(math.radians(d)) for _, d, v, _ in w) / len(w)
    v_ = sum(v * math.cos(math.radians(d)) for _, d, v, _ in w) / len(w)
    return (math.degrees(math.atan2(u, v_)) % 360, math.hypot(u, v_), max(g for *_, g in w), len(w))


# ------------------------------------------------------------------ Analyse

def _wrap(a):
    return (np.asarray(a) + 180) % 360 - 180


def analyse(pfad: str, ziel: str, windpfad: str | None, plot: bool) -> dict:
    TE, TN, TH, R = ZIELE[ziel]
    tr = lade_igc(pfad)
    # Kalibrierung am Boden: Ruhe nach der Landung = Zielhöhe (flacher Landeplatz)
    ruhe = slice(-8, None)
    agl = tr.baro - np.median(tr.baro[ruhe])
    gnss_off = np.median(tr.gnss[ruhe]) - TH

    # Touchdown-Fenster: Baro löst nur ~1 m auf, Ausschweben/Flare und Auslaufen sind im IGC nicht
    # trennbar. Anfang = erster Punkt <= 1 m AGL (danach nie mehr über 3 m), Ende = Grundgeschw.
    # (2-s-Mittel) erstmals < 10 km/h. Der echte Fusskontakt liegt dazwischen (31.10.: Benjamins
    # Beobachtung lag 1–3 s nach dem Anfang).
    hoch = np.where(agl > 3)[0]
    td = int(np.argmax((agl <= 1.0) & (np.arange(len(agl)) > hoch[-1])))
    gs = np.r_[0, np.hypot(np.diff(tr.e), np.diff(tr.n)) / np.maximum(1, np.diff(tr.t))] * 3.6
    gs2 = np.convolve(gs, [0.5, 0.5], mode="same")
    langsam = np.where((np.arange(len(gs2)) > td) & (gs2 < 10))[0]
    aus = int(langsam[0]) if len(langsam) else td
    # Kurs geglättet (±3 s), Endanflug-Richtung = Kurs der letzten 10 s vor dem Touchdown
    k = 3
    de = np.r_[np.full(k, np.nan), tr.e[2 * k:] - tr.e[:-2 * k], np.full(k, np.nan)]
    dn = np.r_[np.full(k, np.nan), tr.n[2 * k:] - tr.n[:-2 * k], np.full(k, np.nan)]
    kurs = np.degrees(np.arctan2(de, dn)) % 360
    i0 = max(0, td - 10)
    fe, fn = tr.e[td] - tr.e[i0], tr.n[td] - tr.n[i0]
    final = math.degrees(math.atan2(fe, fn)) % 360
    ux, uy = math.sin(math.radians(final)), math.cos(math.radians(final))   # Einheitsvektor Endanflug

    # Koordinaten im Endanflug-System: x = Abstand VOR dem Ziel (+ = noch davor), y = seitlich (+ = rechts)
    dx, dy = tr.e - TE, tr.n - TN
    vor = -(dx * ux + dy * uy)
    rechts = dx * uy - dy * ux

    # Segmente: relative Richtung zum Endanflug -> End/Quer/Gegen, kurze Stücke (< 5 s) = Kurve
    rel = np.abs(_wrap(kurs - final))
    kl = np.where(rel <= 45, 0, np.where(rel <= 135, 1, 2))
    seg, s0 = [], 0
    for i in range(1, td + 1):
        if i == td or kl[i] != kl[s0]:
            seg.append([s0, i, KLASSEN[kl[s0]] if i - s0 >= 5 else "Kurve"])
            s0 = i
    # benachbarte gleiche Klassen zusammenführen
    zus = []
    for s in seg:
        if zus and zus[-1][2] == s[2]:
            zus[-1][1] = s[1]
        else:
            zus.append(s)
    seg = zus

    # Eckpunkte: letztes Gegen-Segment >= 15 s, danach der erste Quer, danach der letzte End
    try:
        g = max(j for j, s in enumerate(seg) if s[2] == "Gegen" and s[1] - s[0] >= 15)
    except ValueError:
        g = None
    q = next((j for j in range(g + 1, len(seg)) if seg[j][2] == "Quer"), None) if g is not None else None
    e_ = max(j for j, s in enumerate(seg) if s[2] == "End")
    # Endanflug beginnt nach der letzten Nicht-End-Phase
    ecke = {"Gegenanflug": seg[g][0] if g is not None else None,
            "Queranflug": seg[q][0] if q is not None else None,
            "Endanflug": seg[e_][0], "Touchdown": td}

    wind = lade_wind(windpfad)
    t_start = tr.t[ecke["Gegenanflug"]] if ecke["Gegenanflug"] is not None else tr.t[td] - 180
    w = wind_im_fenster(wind, t_start - 300, tr.t[td] + 300)
    hw = hoehenwind(tr, agl, td)
    wx = wy = 0.0
    quelle = hw if hw else (w[:2] if w else None)  # Volten-Höhe schlägt Mast
    if quelle:
        zu = math.radians(quelle[0] + 180)            # Wind weht NACH
        wx, wy = quelle[1] / 3.6 * math.sin(zu), quelle[1] / 3.6 * math.cos(zu)

    def abschnitt(a, b):
        dt_ = max(1.0, tr.t[b] - tr.t[a])
        gx, gy = (tr.e[b] - tr.e[a]) / dt_, (tr.n[b] - tr.n[a]) / dt_
        weg = float(np.sum(np.hypot(np.diff(tr.e[a:b + 1]), np.diff(tr.n[a:b + 1]))))
        sinken = (agl[a] - agl[b]) / dt_
        ax, ay = gx - wx, gy - wy
        crab = _wrap(math.degrees(math.atan2(ax, ay)) - math.degrees(math.atan2(gx, gy)))
        return {"dauer": dt_, "weg": weg, "gs": weg / dt_ * 3.6, "sinken": sinken,
                "gleit": weg / max(0.1, agl[a] - agl[b]), "luft": math.hypot(ax, ay) * 3.6,
                "vorhalt": float(crab)}

    erg = {"datei": Path(pfad).name, "final_kurs": final, "wind": w, "hoehenwind": hw, "gnss_off": gnss_off,
           "regeln": pruefregeln(tr, kurs, final, ecke, td, vor, rechts, quelle, (TE, TN), R),
           "td_zeit": _hms(tr.t[td]), "td_vor": float(vor[td]), "td_rechts": float(rechts[td]),
           "td_dist": float(math.hypot(dx[td], dy[td])), "radius": R,
           "fenster": [(_hms(tr.t[i]), float(math.hypot(dx[i], dy[i])), float(vor[i]), float(gs2[i]))
                       for i in range(td, aus + 1)],
           "ecken": {}, "segmente": []}
    for name, i in ecke.items():
        if i is not None:
            erg["ecken"][name] = {"zeit": _hms(tr.t[i]), "agl": float(agl[i]), "vor": float(vor[i]),
                                  "rechts": float(rechts[i]), "dist": float(math.hypot(dx[i], dy[i]))}
    ab = ecke["Gegenanflug"] if ecke["Gegenanflug"] is not None else max(0, td - 180)
    for a, b, name in seg:
        if b <= ab:
            continue
        a = max(a, ab)
        erg["segmente"].append({"art": name, "von": _hms(tr.t[a]), "agl_von": float(agl[a]),
                                "agl_bis": float(agl[b]), **abschnitt(a, b)})

    _drucke(erg)
    if plot:
        _plot(tr, agl, vor, rechts, ecke, td, erg, ziel)
    return erg


def hoehenwind(tr: Track, agl: np.ndarray, td: int, von: float = 120, bis: float = 450):
    """Wind auf Volten-Höhe aus den Kreisen/Achten im Positionsraum.

    In einem vollen Kreis ist die Luftgeschwindigkeit ~konstant, die Grundgeschwindigkeit schwankt
    um den Windvektor: Fit |v_grund − w| = V über 30-s-Fenster mit ≥ 330° Drehung (rms < 3 km/h),
    Median über alle Fenster zwischen `von` und `bis` m AGL. Rückgabe (aus °, km/h, Luft km/h, n).
    """
    from scipy.optimize import least_squares
    ok = np.r_[True, np.diff(tr.t) > 0]
    t, e, n, h = tr.t[ok], tr.e[ok], tr.n[ok], agl[ok]
    ende = int(np.searchsorted(t, tr.t[td]))
    gx, gy = np.gradient(e, t), np.gradient(n, t)
    kurs = np.unwrap(np.arctan2(gx, gy))
    fits = []
    for s in range(0, ende - 30, 5):
        sl = slice(s, s + 30)
        if not (von <= h[s] <= bis) or np.abs(np.diff(kurs[sl])).sum() < math.radians(330):
            continue
        r = least_squares(lambda p: np.hypot(gx[sl] - p[0], gy[sl] - p[1]) - p[2], [0, 0, 9])
        if np.sqrt(np.mean(r.fun ** 2)) * 3.6 < 3:
            fits.append(r.x)
    if not fits:
        return None
    wx, wy, v = np.median(np.array(fits), axis=0)
    return ((math.degrees(math.atan2(wx, wy)) + 180) % 360, math.hypot(wx, wy) * 3.6, v * 3.6, len(fits))


def pruefregeln(tr, kurs, final, ecke, td, vor, rechts, wind, ziel_en, radius) -> list[tuple[str, bool | None, str]]:
    """SHV-Weisung Pilot GS (Juli 2025), Ziff. 5.7.1 d/e und 5.7.3 — soweit aus dem IGC prüfbar."""
    out = []
    rel = _wrap(kurs - final)
    # letzte 5 s vor dem Aufsetzen geradlinig
    l5 = np.nanmax(np.abs(rel[max(0, td - 5):td + 1]))
    out.append(("Letzte 5 s geradeaus", bool(l5 <= 20), f"max. {l5:.0f}° Abweichung von der Achse"))
    # S-Kurven im Endanflug max. 90° von der Achse
    e0 = ecke["Endanflug"]
    se = np.nanmax(np.abs(rel[e0:td + 1]))
    out.append(("S-Kurven Endanflug ≤ 90°", bool(se <= 90), f"max. {se:.0f}°"))
    # Kurven im Queranflug max. 200° (grösste Drehung in eine Richtung am Stück)
    q0 = ecke["Queranflug"]
    if q0 is not None:
        # nur zwischen dem ersten und letzten Punkt quer zur Achse (70–110°), damit die
        # Eckkurven Gegen→Quer und Quer→End nicht mitzählen
        quer = np.where((np.abs(rel[q0:e0 + 1]) >= 70) & (np.abs(rel[q0:e0 + 1]) <= 110))[0]
        a_, b_ = (q0 + quer[0], q0 + quer[-1]) if len(quer) else (q0, e0)
        d = np.diff(np.unwrap(np.radians(np.nan_to_num(kurs[a_:b_ + 1], nan=final))))
        am_stueck, best, cur = 0.0, 0.0, 0.0
        for x in d:
            cur = cur + x if (cur == 0 or np.sign(x) == np.sign(cur)) else x
            best = max(best, abs(cur))
        am_stueck = math.degrees(best)
        out.append(("Kurven Queranflug ≤ 200°", bool(am_stueck <= 200), f"grösste Drehung am Stück {am_stueck:.0f}°"))
    # Höhenabbau luvseitig des Landepunkts (60 s vor dem Gegenanflug)
    g0 = ecke["Gegenanflug"]
    if g0 is not None and wind:
        a = max(0, g0 - 60)
        de, dn = np.mean(tr.e[a:g0]) - ziel_en[0], np.mean(tr.n[a:g0]) - ziel_en[1]
        luv = de * math.sin(math.radians(wind[0])) + dn * math.cos(math.radians(wind[0]))
        out.append(("Höhenabbau luvseitig", bool(luv > 0), f"{luv:+.0f} m Richtung Luv"))
    # Landefläche: Prüfungskreis 34 m Ø (r = 17 m) bzw. gemähter Kreis
    d0 = math.hypot(vor[td], rechts[td])
    out.append((f"Bodennähe im Kreis r = {radius:.0f} m", bool(d0 <= radius), f"{d0:.0f} m vom Punkt (Fusskontakt 1–3 s später)"))
    out.append(("Prüfungskreis 34 m Ø (r = 17 m)", bool(d0 <= 17), f"{d0:.0f} m vom Punkt"))
    return out



def _drucke(erg: dict) -> None:
    w, hw = erg["wind"], erg["hoehenwind"]
    print(f"== {erg['datei']}   Endanflug-Kurs {erg['final_kurs']:.0f}°")
    if w:
        print(f"   Wind Station (Volte ±5 min): aus {w[0]:.0f}° {w[1]:.1f} km/h, Böe max {w[2]:.0f} "
              f"({w[3]} Werte)  -> Gegenwind im Endanflug "
              f"{w[1] * math.cos(math.radians(w[0] - erg['final_kurs'])):+.1f} km/h (Mast 10 m)")
    if hw:
        print(f"   Wind Volten-Höhe (aus {hw[3]} Kreis-Fenstern 120–450 m AGL): aus {hw[0]:.0f}° {hw[1]:.1f} km/h, "
              f"Luft im Kreis {hw[2]:.0f} km/h -> Gegenwind im Endanflug "
              f"{hw[1] * math.cos(math.radians(hw[0] - erg['final_kurs'])):+.1f} km/h")
    print("   SHV-Prüfregeln (Weisung Pilot GS 07/2025, Ziff. 5.7):")
    for name, ok, txt in erg["regeln"]:
        print(f"     {'✓' if ok else '✗'} {name:32s} {txt}")
    kurz = "zu kurz" if erg["td_vor"] > 0 else "zu weit"
    print(f"   Bodennähe (≤1 m) {erg['td_zeit']}: {abs(erg['td_vor']):.1f} m {kurz}, "
          f"{abs(erg['td_rechts']):.1f} m {'rechts' if erg['td_rechts'] > 0 else 'links'} "
          f"(Distanz {erg['td_dist']:.1f} m; GPS ±3–5 m)")
    r = erg["radius"]
    print(f"   Touchdown-Fenster bis Auslauf < 10 km/h (Zielkreis r = {r:.0f} m):")
    for z, d, v, g in erg["fenster"]:
        lage = "im Kreis" if d <= r else (f"{d - r:.0f} m vor dem Kreis" if v > 0 else f"{d - r:.0f} m hinter dem Kreis")
        print(f"     {z}  {d:5.1f} m vom Punkt  ({lage})  GS {g:4.1f} km/h")
    print("   Eckpunkt       Zeit      Höhe AGL   vor Ziel   seitlich")
    for k, v in erg["ecken"].items():
        print(f"   {k:13s} {v['zeit']}   {v['agl']:6.0f} m   {v['vor']:+6.0f} m   {v['rechts']:+6.0f} m")
    print("   Segment   ab        Höhe von→bis   Dauer   Weg    GS km/h  Sinken  Gleit/Grund  Luft km/h  Vorhalt")
    for s in erg["segmente"]:
        print(f"   {s['art']:8s} {s['von']}  {s['agl_von']:5.0f}→{s['agl_bis']:4.0f} m  {s['dauer']:4.0f} s "
              f"{s['weg']:5.0f} m  {s['gs']:6.1f}  {s['sinken']:5.2f}   {s['gleit']:6.1f}      "
              f"{s['luft']:6.1f}   {s['vorhalt']:+5.0f}°")


def _plot(tr, agl, vor, rechts, ecke, td, erg, ziel):
    from thermalmodel.plotstyle import use
    plt = use()
    a = ecke["Gegenanflug"] if ecke["Gegenanflug"] is not None else max(0, td - 180)
    a = max(0, a - 30)
    b = min(len(agl), td + 5)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5), gridspec_kw={"width_ratios": [1.1, 1]})
    TE, TN, _, R = ZIELE[ziel]
    ex, ny = tr.e - TE, tr.n - TN                     # Karte: Osten rechts, Norden oben
    sc = ax1.scatter(ex[a:b], ny[a:b], c=agl[a:b], cmap="viridis", s=6)
    ax1.plot(ex[a:b], ny[a:b], lw=0.5, color="0.6", zorder=0)
    for name, i in ecke.items():
        if i is not None:
            ax1.annotate(f"{name}\n{agl[i]:.0f} m", (ex[i], ny[i]), fontsize=7.5,
                         xytext=(6, 6), textcoords="offset points")
            ax1.plot(ex[i], ny[i], "o", ms=5, mfc="none", mec="crimson")
    ax1.add_patch(plt.Circle((0, 0), R, fill=False, ls="--", lw=0.7, color="crimson"))
    ax1.plot(0, 0, "+", color="crimson", ms=10)
    ax1.set_aspect("equal")
    w = erg["wind"]
    if w:                                             # Windpfeil: weht NACH (aus w[0])
        zu = math.radians(w[0] + 180)
        x0, y0 = ax1.get_xlim()[0] + 40, ax1.get_ylim()[1] - 40
        ax1.annotate("", (x0 + 60 * math.sin(zu), y0 + 60 * math.cos(zu)), (x0, y0),
                     arrowprops=dict(arrowstyle="-|>", color="steelblue", lw=1.2))
        ax1.text(x0, y0 + 12, f"Wind {w[1]:.0f}/{w[2]:.0f} km/h", color="steelblue", fontsize=7.5)
    ax1.set_xlabel("Osten [m] ab Zielpunkt")
    ax1.set_ylabel("Norden [m] ab Zielpunkt")
    ax1.set_title(f"Grundriss (Norden oben), Zielkreis r = {R:.0f} m")
    ax1.grid(lw=0.3)
    fig.colorbar(sc, ax=ax1, label="Höhe AGL [m]", shrink=0.8)
    dist = np.hypot(tr.e - ZIELE[ziel][0], tr.n - ZIELE[ziel][1])
    ax2.plot(tr.t[a:b] - tr.t[td], agl[a:b], color="k")
    for name, i in ecke.items():
        if i is not None:
            ax2.axvline(tr.t[i] - tr.t[td], color="crimson", lw=0.6, ls=":")
            ax2.text(tr.t[i] - tr.t[td], agl[i] + 4, f"{name}\n{agl[i]:.0f} m / {dist[i]:.0f} m", fontsize=7.5)
    ax2.set_xlabel("Sekunden bis Touchdown")
    ax2.set_ylabel("Höhe AGL [m] (Baro, am Boden kalibriert)")
    w = erg["wind"]
    ax2.set_title(f"Höhenprofil — Wind Station {f'aus {w[0]:.0f}° {w[1]:.0f}/{w[2]:.0f} km/h' if w else 'unbekannt'}")
    ax2.grid(lw=0.3)
    fig.suptitle(f"{erg['datei']} — Touchdown {abs(erg['td_vor']):.0f} m "
                 f"{'zu kurz' if erg['td_vor'] > 0 else 'zu weit'}, {abs(erg['td_rechts']):.0f} m seitlich")
    OUT.mkdir(exist_ok=True)
    ziel_png = OUT / f"landung_{Path(erg['datei']).stem}.png"
    fig.savefig(ziel_png)
    print(f"   Plot: {ziel_png}")


# ------------------------------------------------------------------ Plan

# Kalibrierung aus den Lehn-Flügen 31.10.2026 (Alpha 6 24, Höhenwind aus den Kreisen 8.7/9.3 km/h):
#   Endanflug  Luft 24–29 km/h, Sinken 1.70/1.85 m/s (angebremst)
#   Queranflug Luft 30 km/h,    Sinken 1.68 m/s
#   Gegenanflug Luft 29–31 km/h, Sinken 1.12/1.84 m/s
#   Geometrie: Endanflug 135/153 m, Queranflug (Abstand Gegenanflug–Achse) 204/231 m,
#   Gegenanflug ab Positionsraum 373/325 m. Nachgerechnet trifft das Flug 2 auf ±3 m (End/Quer).
KALIB = {"End": (26.5, 1.80), "Quer": (30.0, 1.70), "Gegen": (30.0, 1.40)}
GEOM = {"End": 145.0, "Quer": 210.0, "Gegen": 350.0}
# Annahme, nicht gemessen: Endanflug im Trimm (Hände oben) für starken Wind
TRIMM = (37.0, 1.20)


def plan_rechnen(u: float, kal: dict = KALIB, geom: dict = GEOM, end=None) -> dict:
    """Höhen an den Eckpunkten rückwärts vom Ziel; u = Gegenwind im Endanflug auf Volten-Höhe."""
    v_e, w_e = end or kal["End"]
    v_q, w_q = kal["Quer"]
    v_g, w_g = kal["Gegen"]
    gs_e = (v_e - u) / 3.6
    if gs_e <= 0.3:
        return {"u": u, "ok": False}
    h_e = geom["End"] * w_e / gs_e
    gs_q = math.sqrt(max(0.01, v_q ** 2 - u ** 2)) / 3.6
    h_q = h_e + geom["Quer"] * w_q / gs_q
    h_g = h_q + geom["Gegen"] * w_g / ((v_g + u) / 3.6)
    return {"u": u, "ok": True, "gs_e": gs_e * 3.6, "gz_e": gs_e / w_e, "h_e": h_e,
            "vorhalt": math.degrees(math.asin(min(1.0, u / v_q))), "h_q": h_q, "h_g": h_g,
            "l_e50": 50 * gs_e / w_e}


def plan(winde: list[float], faktor: float, png: bool) -> None:
    """Tabelle + Grafik: ideale Höhen je Gegenwind (Volten-Höhe), dazu Mast-Äquivalent."""
    print("Kalibrierung Lehn 31.10.2026 (Alpha 6 24): " + ", ".join(
        f"{k} {v:.0f} km/h / {w:.2f} m/s" for k, (v, w) in KALIB.items()))
    print(f"Geometrie: Endanflug {GEOM['End']:.0f} m, Queranflug {GEOM['Quer']:.0f} m, "
          f"Gegenanflug {GEOM['Gegen']:.0f} m. Höhenwind ≈ Mast × {faktor:.1f} (31.10.: 1.1–1.4).")
    print("Gegenwind  Mast≈  | Beginn Gegen  Beginn Quer  Beginn End | GS End  GZ Grund | Endanflug-Länge "
          "ab 50 m | Vorhalt Quer | End im Trimm*: Höhe")
    rows = []
    for u in sorted(set(winde)):
        r, t = plan_rechnen(u), plan_rechnen(u, end=TRIMM)
        rows.append((r, t))
        if not r["ok"]:
            print(f"  {u:4.0f}    {u / faktor:4.0f}   | angebremst kein Vorwärtskommen — "
                  f"Trimm: Endanflug ab {t['h_e']:.0f} m"); continue
        print(f"  {u:4.0f}    {u / faktor:4.0f}   |   {r['h_g']:5.0f} m      {r['h_q']:5.0f} m    {r['h_e']:5.0f} m "
              f"|  {r['gs_e']:4.0f}    {r['gz_e']:4.1f}   |     {r['l_e50']:4.0f} m          |    {r['vorhalt']:3.0f}°"
              f"       |  {t['h_e']:4.0f} m" + ("   ⚠ GS < 12 km/h: Bremse lösen, Trimm-Spalte" if r["gs_e"] < 12 else ""))
    print("Gemessen nur bei 7–9 km/h Gegenwind (2 Flüge); die Zeilen weit davon sind extrapoliert.")
    print("* Trimm-Endanflug: Fahrt 37 km/h / Sinken 1.2 m/s ist eine ANNAHME (keine Messung) — "
          "mit einem Trimm-Gleitflug in Lehn kalibrieren.")
    if png:
        _plan_png(rows, faktor)


def _plan_png(rows, faktor):
    from thermalmodel.plotstyle import use
    plt = use()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.5))
    ok = [r for r, _ in rows if r["ok"]]
    u = [r["u"] for r in ok]
    for k, lab, c in (("h_g", "Beginn Gegenanflug", "tab:green"), ("h_q", "Beginn Queranflug", "tab:orange"),
                      ("h_e", "Beginn Endanflug (angebremst)", "tab:red")):
        a1.plot(u, [r[k] for r in ok], "o-", ms=3, color=c, label=lab)
    a1.plot([t["u"] for _, t in rows if t["ok"]], [t["h_e"] for _, t in rows if t["ok"]], "--",
            color="tab:red", lw=0.8, label="Beginn Endanflug im Trimm (Annahme)")
    a1.scatter([7.1, 7.9], [40, 49], marker="x", color="k", zorder=5, label="geflogen 31.10. (Endanflug)")
    a1.scatter([7.1, 7.9], [117, 96], marker="+", color="k", zorder=5, label="geflogen 31.10. (Queranflug)")
    a1.set_xlabel(f"Gegenwind im Endanflug auf Volten-Höhe [km/h]  (Mast ≈ ÷ {faktor:.1f})")
    a1.set_ylabel("Höhe AGL [m]")
    a1.set_title(f"Lehn: Eckpunkt-Höhen (Endanflug {GEOM['End']:.0f} m, Queranflug {GEOM['Quer']:.0f} m)")
    a1.grid(lw=0.3); a1.legend()
    a2.plot(u, [r["l_e50"] for r in ok], "o-", ms=3, color="tab:red")
    a2.set_xlabel("Gegenwind im Endanflug [km/h]")
    a2.set_ylabel("Distanz zum Punkt [m]")
    a2.set_title("Wo einkurven, wenn der Endanflug auf 50 m AGL beginnt (angebremst)")
    a2.grid(lw=0.3)
    fig.suptitle("Landeeinteilung Lehn — kalibriert auf Alpha 6 24, 31.10.2026 (2 Flüge)")
    OUT.mkdir(exist_ok=True)
    f = OUT / "landeplan_lehn.png"
    fig.savefig(f)
    print(f"Plot: {f}")


# ------------------------------------------------------------------ CLI

def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyse"); a.add_argument("igc", nargs="+")
    a.add_argument("--ziel", default="lehn", choices=sorted(ZIELE))
    a.add_argument("--wind", help="Holfuy-Archiv-JSON (lagecheck.py archiv, *_15min.json)")
    a.add_argument("--kein-plot", action="store_true")
    p = sub.add_parser("plan")
    p.add_argument("--gegenwind", default="0,2,4,6,8,10,12,14,16,18,20",
                   help="Gegenwind im Endanflug auf Volten-Höhe, km/h (Liste)")
    p.add_argument("--faktor", type=float, default=1.3, help="Höhenwind / Mastwind")
    p.add_argument("--kein-plot", action="store_true")
    x = ap.parse_args(argv)
    if x.cmd == "analyse":
        for f in x.igc:
            analyse(f, x.ziel, x.wind, not x.kein_plot)
            print()
    else:
        plan([float(v) for v in x.gegenwind.split(",")], x.faktor, not x.kein_plot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
