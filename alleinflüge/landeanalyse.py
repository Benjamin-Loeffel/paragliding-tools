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
    volten    Landevolten je Gegenwind auf der swisstopo-Karte (Endanflug ab 50 m), geflogene
              Volten zum Vergleich darüber.
    karte     Alle Landungen auf einer swisstopo-Karte.
    hoehen    GPS- und Baro-Höhe des IGC an Start und Landung gegen swissALTI3D (Vario-Genauigkeit).

Wind: Holfuy-2-min-Reihe aus `lagecheck.py archiv` (am Flugtag selbst sichern, Vortage gibt
Holfuy nur noch 15-min). Der Wind am Mast (10 m) ist schwächer als auf 50–150 m AGL — die
Luftgeschwindigkeit daraus ist eine Schätzung, der Vergleich zwischen Flügen bleibt gültig.

Beispiele:
    python alleinflüge/landeanalyse.py analyse D:/.../2026-10-31-XTR-...-02.IGC --ziel lehn \
        --wind alleinflüge/archiv/2026-10-31_interlaken/roh/holfuy-1850_15min.json
    python alleinflüge/landeanalyse.py plan --gegenwind 0,5,10,15,20
    python alleinflüge/landeanalyse.py volten --kurs 250 --seite rechts --flug <igc>...   # Talwind
    python alleinflüge/landeanalyse.py volten --kurs 75 --seite links                     # Bergwind
    python alleinflüge/landeanalyse.py hoehen <igc>...
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
VORLAUF = 180          # s vor dem Gegenanflug in Karten/Plots (Höhenabbau im Positionsraum sichtbar)
KARTE = "ch.swisstopo.swissimage"                    # Luftbild; Landeskarte: ch.swisstopo.pixelkarte-farbe


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

def lade_wind(pfad: str | None, utc_offset_h: int = 0) -> list[tuple[float, float, float, float]]:
    """[(sek. Lokalzeit, Richtung aus °, Mittel km/h, Böe km/h)] aus der Holfuy-Archivdatei (JSON)
    oder einer MeteoSchweiz-SMN-10-min-Datei (CSV, UTC; `lagecheck.py archiv`)."""
    if not pfad:
        return []
    out = []
    if pfad.lower().endswith(".csv"):
        z = Path(pfad).read_text(encoding="utf-8").splitlines()
        k = z[0].split(";")
        for x in (dict(zip(k, r.split(";"))) for r in z[1:]):
            if x.get("dkl010z0") and x.get("fu3010z0"):
                t = dt.datetime.strptime(x["reference_timestamp"], "%d.%m.%Y %H:%M")
                out.append(((t.hour + utc_offset_h) * 3600 + t.minute * 60, float(x["dkl010z0"]),
                            float(x["fu3010z0"]), float(x.get("fu3010z1") or x["fu3010z0"])))
        return out
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
    # Endanflug beginnt nach der letzten Abweichung > 90° von der Achse (S-Kurven bis 90° gehören laut
    # Weisung zum Endanflug) beim ersten Kurs innerhalb 45°
    rr = np.nan_to_num(rel[:td + 1], nan=0.0)
    weg_ = np.where(rr > 90)[0]
    e0 = (weg_[-1] if len(weg_) else 0)
    e0 = int(e0 + np.argmax(rr[e0:] <= 45))
    ecke = {"Gegenanflug": seg[g][0] if g is not None else None,
            "Queranflug": seg[q][0] if q is not None else None,
            "Endanflug": e0, "Touchdown": td}

    wind = lade_wind(windpfad, tr.utc_offset_h)
    t_start = tr.t[ecke["Gegenanflug"]] if ecke["Gegenanflug"] is not None else tr.t[td] - 180
    w = wind_im_fenster(wind, t_start - 300, tr.t[td] + 300)
    # Station während der Landung: Beginn Gegenanflug bis Touchdown (+120 s, damit der 2-min-Wert mit dem
    # Touchdown drin ist; Holfuy-Zeitstempel = Ende des Mittelungsintervalls)
    wl = wind_im_fenster(wind, t_start, tr.t[td] + 120)
    if wl:                                            # + arithmetisches Mittel der Mittelwerte (wie Holfuy-Anzeige)
        vs = [v for t, _, v, _ in wind if t_start <= t <= tr.t[td] + 120]
        wl = (*wl, sum(vs) / len(vs))
    stat = "Holfuy Lehn" if windpfad and "holfuy-1850" in windpfad else \
        (f"MeteoSchweiz {Path(windpfad).name.split('_')[0].split('-')[-1]} (nicht Lehn)" if windpfad else None)
    hw = hoehenwind(tr, agl, td)
    wx = wy = 0.0
    gs_wind = _wind_aus_gs(tr, ecke, final)
    # Volten-Höhe (Kreise) schlägt Gegen-/End-Grundgeschwindigkeit schlägt Mast
    quelle = hw if hw else (gs_wind if gs_wind else (w[:2] if w else None))
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

    erg = {"datei": Path(pfad).name, "final_kurs": final, "wind": w, "hoehenwind": hw, "gs_wind": gs_wind,
           "wind_landung": wl, "station": stat, "fenster_landung": (_hms(t_start), _hms(tr.t[td])),
           "td_agl_e": float(agl[e0]), "e_dist": float(math.hypot(dx[e0], dy[e0])), "gnss_off": gnss_off,
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
    erg["_intern"] = (tr, agl, ecke, td)
    return erg


def _wind_aus_gs(tr: Track, ecke: dict, final: float):
    """Fallback ohne Kreise: Achswind aus Gegen- und Endanflug-Grundgeschwindigkeit.

    GS_Gegen = V_G + u, GS_End = V_E − u mit den Fahrten aus KALIB → u = (GS_G − GS_E − V_G + V_E) / 2.
    Nur die Komponente längs der Achse; Rückgabe (aus °, km/h) wie Gegenwind genau von vorn.
    """
    g, q, e0, td = ecke["Gegenanflug"], ecke["Queranflug"], ecke["Endanflug"], ecke["Touchdown"]
    if g is None or q is None or td - e0 < 8:
        return None
    gs = lambda a, b: math.hypot(tr.e[b] - tr.e[a], tr.n[b] - tr.n[a]) / max(1.0, tr.t[b] - tr.t[a]) * 3.6
    u = (gs(g, q) - gs(e0, td) - KALIB["Gegen"][0] + KALIB["End"][0]) / 2
    return (final if u >= 0 else (final + 180) % 360, abs(u))


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
    out.append(("S-Kurven Endanflug ≤ 90°", bool(se <= 90),
                f"max. {se:.0f}° (Endanflug = ab der letzten Abweichung > 90°)"))
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
    wl = erg["wind_landung"]
    if wl:
        print(f"   {erg['station']} während der Landung ({erg['fenster_landung'][0]}–{erg['fenster_landung'][1]}): "
              f"aus {wl[0]:.0f}°, Mittel {wl[4]:.0f} km/h, Spitze {wl[2]:.0f} km/h ({wl[3]} Werte)")
    if hw:
        print(f"   Wind Volten-Höhe (aus {hw[3]} Kreis-Fenstern 120–450 m AGL): aus {hw[0]:.0f}° {hw[1]:.1f} km/h, "
              f"Luft im Kreis {hw[2]:.0f} km/h -> Gegenwind im Endanflug "
              f"{hw[1] * math.cos(math.radians(hw[0] - erg['final_kurs'])):+.1f} km/h")
    if not hw and erg["gs_wind"]:
        gw = erg["gs_wind"]
        print(f"   Wind aus Gegen-/End-Grundgeschw. (keine Kreise, nur Achskomponente): "
              f"Gegenwind im Endanflug {gw[1] * math.cos(math.radians(gw[0] - erg['final_kurs'])):+.1f} km/h")
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


def _plot(tr, agl, vor, rechts, ecke, td, erg, ziel, rand: float = 150, sued: float = 250):
    """Grundriss auf dem Luftbild (gross, mit `rand` m Umgebung, nach Süden `sued` m mehr) + Höhenprofil.

    Höhen an den Eckpunkten als AGL (Baro, am Boden kalibriert) und als GPS-Höhe ü. M. (= Vario-Anzeige).
    """
    from thermalmodel.plotstyle import use
    plt = use()
    a = ecke["Gegenanflug"] if ecke["Gegenanflug"] is not None else max(0, td - 180)
    a = max(0, a - VORLAUF)
    b = min(len(agl), td + 5)
    gps0 = float(np.median(tr.gnss[-8:]))             # GPS am Boden (Ruhe nach der Landung)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 11), gridspec_kw={"width_ratios": [2.3, 1]})
    TE, TN, _, R = ZIELE[ziel]
    ex, ny = tr.e - TE, tr.n - TN                     # Karte: Osten rechts, Norden oben
    ax1.plot(ex[a:b], ny[a:b], lw=0.8, color="white", zorder=2, path_effects=_kontur("black", 2))
    sc = ax1.scatter(ex[a:b], ny[a:b], c=agl[a:b], cmap="viridis", s=9, zorder=3)
    for name, i in ecke.items():
        if i is not None:
            ax1.annotate(f"{name}\n{agl[i]:.0f} m AGL · {tr.gnss[i]:.0f} m GPS", (ex[i], ny[i]), fontsize=8,
                         xytext=(8, 8), textcoords="offset points", bbox=_KASTEN, zorder=6)
            ax1.plot(ex[i], ny[i], "o", ms=7, mfc="none", mec="red", mew=1.5, zorder=5)
    ax1.add_patch(plt.Circle((0, 0), R, fill=False, lw=1.5, color="red", zorder=5))
    ax1.add_patch(plt.Circle((0, 0), 17, fill=False, ls="--", lw=1.0, color="red", zorder=5))
    ax1.set_aspect("equal")
    x0, x1, y0, y1 = _rand(np.r_[ex[a:b], 0], np.r_[ny[a:b], 0], rand)
    _karte(ax1, ziel, x0, x1, y0 - sued, y1)
    wl, hw = erg["wind_landung"], erg["hoehenwind"]
    lehn = wl if erg["station"] == "Holfuy Lehn" else None   # andere Stationen sind für Lehn nicht repräsentativ
    zeilen = [f"Holfuy Lehn {erg['fenster_landung'][0][:5]}–{erg['fenster_landung'][1][:5]} (Gegenanflug → Landung):",
              f"aus {lehn[0]:.0f}° · Mittel {lehn[4]:.0f} km/h · Spitze {lehn[2]:.0f} km/h"] if lehn else \
        ["Holfuy Lehn: keine Daten (Holfuy speichert nur 7 Tage)"]
    if hw:
        zeilen.append(f"Volten-Höhe (aus deinen Kreisen): aus {hw[0]:.0f}° {hw[1]:.0f} km/h")
    pfeil = lehn or hw
    if pfeil:                                         # Windpfeil oben links, weht NACH (aus pfeil[0])
        zu = math.radians(pfeil[0] + 180)
        ax1.annotate("", (0.06 + 0.05 * math.sin(zu), 0.86 + 0.05 * math.cos(zu)), (0.06, 0.86),
                     xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", color="deepskyblue", lw=3,
                                                               path_effects=_kontur("white", 5)))
    ax1.text(0.02, 0.98, "\n".join(zeilen), transform=ax1.transAxes, fontsize=8.5, va="top", bbox=_KASTEN,
             fontweight="bold" if lehn else "normal")
    ax1.set_xlabel("Osten [m] ab Zielpunkt")
    ax1.set_ylabel("Norden [m] ab Zielpunkt")
    ax1.set_title(f"Grundriss (Norden oben), Zielkreis r = {R:.0f} m, Prüfungskreis 34 m Ø gestrichelt")
    ax1.grid(lw=0.3, alpha=0.5)
    fig.colorbar(sc, ax=ax1, label="Höhe AGL [m]", shrink=0.7, pad=0.01)
    dist = np.hypot(ex, ny)
    t_ = tr.t[a:b] - tr.t[td]
    ax2.plot(t_, agl[a:b], color="k", label="Baro AGL (am Boden kalibriert)")
    ax2.plot(t_, tr.gnss[a:b] - gps0, color="tab:blue", lw=0.8, alpha=0.8, label="GPS (Vario-Anzeige)")
    for name, i in ecke.items():
        if i is not None:
            ax2.axvline(tr.t[i] - tr.t[td], color="crimson", lw=0.6, ls=":")
            ax2.text(tr.t[i] - tr.t[td], agl[i] + 6, f"{name}\n{agl[i]:.0f} m AGL\n{tr.gnss[i]:.0f} m GPS\n"
                     f"{dist[i]:.0f} m vom Punkt", fontsize=7.5, bbox=_KASTEN)
    ax2.set_xlabel("Sekunden bis Touchdown")
    ax2.set_ylabel("Höhe AGL [m]")
    lo, hi = ax2.get_ylim()
    ax3 = ax2.twinx()                                 # rechte Achse: GPS-Höhe ü. M. wie am Vario
    ax3.set_ylim(lo + gps0, hi + gps0)
    ax3.set_ylabel(f"GPS-Höhe m ü. M. (am Boden {gps0:.0f} m)")
    ax2.set_title("Höhenprofil")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(lw=0.3)
    fig.suptitle(f"{erg['datei']} — Touchdown {abs(erg['td_vor']):.0f} m "
                 f"{'zu kurz' if erg['td_vor'] > 0 else 'zu weit'}, {abs(erg['td_rechts']):.0f} m seitlich")
    OUT.mkdir(exist_ok=True)
    ziel_png = OUT / f"landung_{Path(erg['datei']).stem}.png"
    fig.savefig(ziel_png)
    print(f"   Plot: {ziel_png}")


# ------------------------------------------------------------------ Karte

_KASTEN = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75)


def _kontur(farbe: str = "white", breite: float = 3.0):
    """Umrandung für Linien/Text auf dem Luftbild."""
    import matplotlib.patheffects as pe
    return [pe.Stroke(linewidth=breite, foreground=farbe), pe.Normal()]


def _rand(x, y, rand: float):
    """Kartenausschnitt (x0, x1, y0, y1) relativ zum Ziel um die Punkte, mit Rand in m."""
    return (float(np.min(x)) - rand, float(np.max(x)) + rand, float(np.min(y)) - rand, float(np.max(y)) + rand)


def _karte(ax, ziel: str, x0: float, x1: float, y0: float, y1: float,
           ebene: str = KARTE, alpha: float = 0.9) -> None:
    """swisstopo-Karte (WMS, LV95) als Hintergrund; Achsen in m relativ zum Zielpunkt. Cache in OUT/karten."""
    import matplotlib.image as mpimg
    import requests
    TE, TN = ZIELE[ziel][:2]
    x0, x1 = math.floor(x0 / 10) * 10, math.ceil(x1 / 10) * 10
    y0, y1 = math.floor(y0 / 10) * 10, math.ceil(y1 / 10) * 10
    px = max(0.5, max(x1 - x0, y1 - y0) / 4000)          # m/Pixel, max. 4000 px
    w, h = int((x1 - x0) / px), int((y1 - y0) / px)
    f = OUT / "karten" / f"{ziel}_{ebene.split('.')[-1]}_{x0}_{x1}_{y0}_{y1}_{w}.png"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get("https://wms.geo.admin.ch/", timeout=60, params={
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": ebene, "STYLES": "",
            "CRS": "EPSG:2056", "BBOX": f"{TE + x0},{TN + y0},{TE + x1},{TN + y1}",
            "WIDTH": w, "HEIGHT": h, "FORMAT": "image/png"})
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
            print(f"   Karte nicht geladen ({r.status_code})")
            return
        f.write_bytes(r.content)
    ax.imshow(mpimg.imread(f), extent=(x0, x1, y0, y1), zorder=-1, alpha=alpha)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.text(0.995, 0.005, "© swisstopo", transform=ax.transAxes, ha="right", va="bottom", fontsize=6,
            bbox=_KASTEN)


def _aus_achse(vor, rechts, kurs: float):
    """(vor, rechts) im Endanflug-System -> (Ost, Nord) relativ zum Ziel (Umkehrung von analyse)."""
    ux, uy = math.sin(math.radians(kurs)), math.cos(math.radians(kurs))
    vor, rechts = np.asarray(vor, float), np.asarray(rechts, float)
    return -vor * ux + rechts * uy, -vor * uy - rechts * ux


def _still(igc: str, ziel: str) -> dict:
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return analyse(igc, ziel, None, False)


def volten(winde: list[float], kurs: float, seite: str, faktor: float, igcs: list[str], ziel: str,
           ebene: str, spicker: bool = False) -> None:
    """Landevolten je Gegenwind auf der swisstopo-Karte, Endanflug ab 50 m AGL (Planmodell).

    Geometrie wie geflogen: Gegenanflug 210 m neben der Achse ab 200 m hinter dem Punkt (Positionsraum
    luvseitig), Queranflug quer zur Achse, Endanflug-Länge je Wind = Gleitweg ab 50 m (KALIB End).
    Plan-Zahlen = Zielhöhe + Höhe über Grund (Vario-GPS zeigt typisch 0–6 m mehr, siehe KALIB), geflogene
    Eckpunkte = GPS-Höhe aus dem IGC. Queranflug mit QUER_RESERVE. `spicker`: kleines Bild mit grosser Schrift
    für den A4-Spicker (ohne geflogene Tracks).
    """
    from thermalmodel.plotstyle import use
    plt = use()
    sg = 1 if seite == "rechts" else -1
    Q, P = GEOM["Quer"], 200.0
    TH = ZIELE[ziel][2]
    fs = 1.45 if spicker else 1.0                     # Schriftfaktor
    fig, ax = plt.subplots(figsize=(7.5, 6.2) if spicker else (15, 12))
    if spicker:
        igcs = []
    farben = plt.get_cmap("plasma")(np.linspace(0.05, 0.85, len(winde)))
    pkt = []
    for j, (u, c) in enumerate(sorted(zip(winde, farben), key=lambda z: -z[0])):
        r = plan_rechnen(u)
        if not r["ok"]:
            continue
        le = r["l_e50"]
        h_q = 50 + Q * KALIB["Quer"][1] / (math.sqrt(max(0.01, KALIB["Quer"][0] ** 2 - u ** 2)) / 3.6)             + QUER_RESERVE
        h_g = h_q + (P + le) * KALIB["Gegen"][1] / ((KALIB["Gegen"][0] + u) / 3.6)
        x, y = _aus_achse([-P, le, le, 0], [sg * Q, sg * Q, 0, 0], kurs)
        pkt += list(zip(x, y))
        ax.plot(x, y, "-", color=c, lw=2.2, zorder=3, path_effects=_kontur("white", 4),
                label=f"Holfuy {u / faktor:.0f} km/h" if spicker else
                      (f"Gegenwind {u:.0f} km/h (Mast ≈ {u / faktor:.0f}): Gegen {TH + h_g:.0f} m · "
                       f"Quer {TH + h_q:.0f} m · End {TH + 50:.0f} m bei {le:.0f} m"))
        ax.plot(x[:3], y[:3], "o", color=c, ms=6, mec="k", mew=0.5, zorder=4)
        for xi, yi, hh, dy in ((x[0], y[0], h_g, 5 + 11 * fs * j), (x[1], y[1], h_q, 5), (x[2], y[2], 50, -12 * fs)):
            ax.annotate(f"{TH + hh:.0f}", (xi, yi), xytext=(5, dy), textcoords="offset points",
                        fontsize=8 * fs, color=c, fontweight="bold", zorder=5, path_effects=_kontur("white", 2.5))
    # Positionsraum (Höhenabbau, Achten) luvseitig hinter dem Punkt
    cx, cy = _aus_achse([-P - 70], [sg * Q * 0.75], kurs)
    ax.add_patch(plt.Circle((cx[0], cy[0]), 90, fc="lime", alpha=0.12, ec="lime", lw=1.2, zorder=2))
    ax.text(cx[0], cy[0], "Positionsraum\n(luvseitig)", ha="center", va="center", fontsize=8 * fs, color="darkgreen",
            bbox=_KASTEN)
    TE, TN = ZIELE[ziel][:2]
    for igc in igcs:                                # geflogene Volten darüber
        tr, agl, ecke, td = _still(igc, ziel)["_intern"]
        a = max(0, (ecke["Gegenanflug"] or td - 180) - VORLAUF)
        ax.plot(tr.e[a:td + 3] - TE, tr.n[a:td + 3] - TN, "-", color="white", lw=1.0, zorder=3,
                path_effects=_kontur("black", 2.2))
        pkt += list(zip(tr.e[a:td + 3] - TE, tr.n[a:td + 3] - TN))
        for k in ("Gegenanflug", "Queranflug", "Endanflug"):
            i = ecke[k]
            if i is not None:
                ax.plot(tr.e[i] - TE, tr.n[i] - TN, "s", ms=5, color="white", mec="k", zorder=4)
                ax.annotate(f"{tr.gnss[i]:.0f}", (tr.e[i] - TE, tr.n[i] - TN), xytext=(-18, 4),
                            textcoords="offset points", fontsize=7.5, bbox=_KASTEN)
    if igcs:
        ax.plot([], [], "-s", color="white", mec="k", lw=1.0, ms=5, path_effects=_kontur("black", 2.2),
                label="geflogen: " + ", ".join(f"{Path(i).stem[:10]} #{Path(i).stem[-1]}" for i in igcs)
                      + " (Eckpunkte GPS m ü. M. wie am Vario)")
    R = ZIELE[ziel][3]
    ax.add_patch(plt.Circle((0, 0), R, fill=False, lw=1.5, color="red", zorder=5))
    ax.add_patch(plt.Circle((0, 0), 17, fill=False, lw=1.0, ls="--", color="red", zorder=5))
    zu = math.radians(kurs + 180)                     # Windpfeil oben rechts, weht entgegen dem Endanflug
    ax.annotate("", (0.92 + 0.05 * math.sin(zu), 0.90 + 0.05 * math.cos(zu)), (0.92, 0.90),
                xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", color="deepskyblue", lw=3,
                                                          path_effects=_kontur("white", 5)))
    if not spicker:
        ax.text(0.92, 0.97, f"Wind aus {kurs % 360:.0f}°", transform=ax.transAxes, color="steelblue", fontsize=9,
                ha="center", bbox=_KASTEN)
    ax.set_aspect("equal")
    xs, ys = zip(*pkt)
    _karte(ax, ziel, *_rand(np.r_[xs, cx], np.r_[ys, cy], 60), ebene=ebene)
    if spicker:
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{'Rechts' if sg > 0 else 'Links'}volte · Endanflug {kurs:.0f}° · "
                     f"{'Talwind' if sg > 0 else 'Bergwind'} aus {kurs % 360:.0f}°", fontsize=11 * fs)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=len(winde), fontsize=9.5,
                  frameon=False, handlelength=1.5, columnspacing=1.2)
    else:
        ax.set_xlabel("Osten [m] ab Zielpunkt")
        ax.set_ylabel("Norden [m] ab Zielpunkt")
        ax.set_title(f"Landevolten Lehn — {'Rechts' if sg > 0 else 'Links'}volte, Endanflug {kurs:.0f}°, "
                     f"Endanflug ab {TH + 50:.0f} m; Zahlen = m ü. M. am Eckpunkt (Plan: Lehn + über Grund, geflogen: GPS); "
                     f"geflogen ab {VORLAUF // 60} min vor dem Gegenanflug", fontsize=10)
        ax.legend(loc="lower left", fontsize=7.5, framealpha=0.9)
    OUT.mkdir(exist_ok=True)
    f = OUT / f"volten_lehn_{kurs:.0f}_{seite}{'_spicker' if spicker else ''}.png"
    fig.savefig(f)
    print(f"Plot: {f}")


def karte_alle(igcs: list[str], ziel: str, ebene: str) -> None:
    """Alle Landungen (letzte Volte bis Touchdown) auf einer Karte, Farbe je Flug."""
    from thermalmodel.plotstyle import use
    plt = use()
    TE, TN, _, R = ZIELE[ziel]
    fig, ax = plt.subplots(figsize=(15, 12))
    farben = plt.get_cmap("tab10")(np.arange(len(igcs)) % 10)
    alle_x, alle_y = [0.0], [0.0]
    for igc, c in zip(igcs, farben):
        e = _still(igc, ziel)
        tr, agl, ecke, td = e["_intern"]
        a = max(0, (ecke["Gegenanflug"] or td - 180) - VORLAUF)
        x, y = tr.e[a:td + 3] - TE, tr.n[a:td + 3] - TN
        alle_x += list(x)
        alle_y += list(y)
        ax.plot(x, y, "-", color=c, lw=1.4, path_effects=_kontur("white", 2.8),
                label=f"{Path(igc).stem[:10]} #{Path(igc).stem[-1]}: Endanflug {e['final_kurs']:.0f}°, ab "
                      f"{agl[ecke['Endanflug']]:.0f} m / {e['e_dist']:.0f} m, "
                      f"{abs(e['td_vor']):.0f} m zu {'kurz' if e['td_vor'] > 0 else 'weit'}")
        for k in ("Gegenanflug", "Queranflug", "Endanflug"):
            i = ecke[k]
            if i is not None:
                ax.plot(tr.e[i] - TE, tr.n[i] - TN, "o", ms=5, color=c, mec="k", mew=0.5)
                ax.annotate(f"{agl[i]:.0f}", (tr.e[i] - TE, tr.n[i] - TN), xytext=(4, 4),
                            textcoords="offset points", fontsize=7, color=c, fontweight="bold",
                            path_effects=_kontur("white", 2.5))
        ax.plot(tr.e[td] - TE, tr.n[td] - TN, "x", ms=8, mew=2, color=c, path_effects=_kontur("white", 4))
    ax.add_patch(plt.Circle((0, 0), R, fill=False, lw=1.5, color="red", zorder=5))
    ax.set_aspect("equal")
    _karte(ax, ziel, *_rand(alle_x, alle_y, 60), ebene=ebene)
    ax.set_xlabel("Osten [m] ab Zielpunkt")
    ax.set_ylabel("Norden [m] ab Zielpunkt")
    ax.set_title(f"Landungen Lehn — ab {VORLAUF // 60} min vor dem Gegenanflug bis Bodennähe (×), "
                 f"Zahlen = Höhe AGL an Gegen/Quer/End", fontsize=10)
    ax.legend(loc="lower left", fontsize=7.5, framealpha=0.9)
    OUT.mkdir(exist_ok=True)
    f = OUT / "landungen_lehn_alle.png"
    fig.savefig(f)
    print(f"Plot: {f}")


def blatt(igcs: list[str], ziel: str, ebene: str, vorlauf: float = 45) -> None:
    """Kartenansicht aller Landungen auf einer A4-Seite (hoch, 2 Spalten), gleicher Massstab für alle.

    Je Flug: Track ab `vorlauf` s vor dem Gegenanflug bis Bodennähe, Farbe = Höhe über Grund, Eckpunkte mit
    GPS-Höhe wie am Vario, Bodennähe (≤ 1 m) mit Abstand zum Punkt, Wind (Holfuy Lehn, sonst aus den Kreisen).
    """
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors
    plt.rcParams.update({"font.size": 6.5})
    TE, TN, TH, R = ZIELE[ziel]
    import contextlib
    import io
    fl = []
    for igc in igcs:
        tag = Path(igc).stem[:10]                    # Holfuy Lehn aus dem Tagesarchiv, falls gesichert
        wp = sorted((Path(__file__).resolve().parent / "archiv").glob(f"{tag}_*/roh/holfuy-1850_15min.json"))
        with contextlib.redirect_stdout(io.StringIO()):
            e = analyse(igc, ziel, str(wp[0]) if wp else None, False)
        tr, agl, ecke, td = e["_intern"]
        a = max(0, int(np.searchsorted(tr.t, tr.t[ecke["Gegenanflug"] or max(0, td - 120)] - vorlauf)))
        fl.append((igc, e, tr, agl, ecke, td, a, tr.e[a:td + 3] - TE, tr.n[a:td + 3] - TN))
    nz = (len(fl) + 2) // 2
    seite = (8.27, 11.69)
    fig = plt.figure(figsize=seite)
    l, r_, o, u_, sp, zs = 0.03, 0.03, 0.045, 0.02, 0.02, 0.03      # Ränder (Anteil Seite)
    bw = (1 - l - r_ - sp) / 2
    bh = (1 - o - u_ - (nz - 1) * zs) / nz
    vb = (bw * seite[0]) / (bh * seite[1])                          # Breite/Höhe eines Feldes
    groesse = max(max(np.ptp(x), np.ptp(y) * vb) for *_, x, y in fl) + 70   # Fensterbreite m, für alle gleich
    norm = colors.Normalize(0, 250)
    for k, (igc, e, tr, agl, ecke, td, a, x, y) in enumerate(fl):
        ax = fig.add_axes([l + (k % 2) * (bw + sp), 1 - o - (k // 2 + 1) * bh - (k // 2) * zs, bw, bh])
        cx, cy = (x.min() + x.max()) / 2, (y.min() + y.max()) / 2
        x0, x1, y0, y1 = cx - groesse / 2, cx + groesse / 2, cy - groesse / vb / 2, cy + groesse / vb / 2
        _karte(ax, ziel, x0, x1, y0, y1, ebene=ebene)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
        ax.plot(x, y, lw=0.5, color="white", zorder=2, path_effects=_kontur("black", 1.3))
        ax.scatter(x, y, c=agl[a:td + 3], cmap="viridis", norm=norm, s=5, zorder=3, lw=0)
        for name, i in ecke.items():
            if i is None:
                continue
            ex, ny = tr.e[i] - TE, tr.n[i] - TN
            ax.plot(ex, ny, "o", ms=4, mfc="none", mec="red", mew=1, zorder=5)
            txt = (f"{abs(e['td_vor']):.0f} m {'kurz' if e['td_vor'] > 0 else 'weit'}" if name == "Touchdown"
                   else f"{name[:-6]} {tr.gnss[i]:.0f}")
            ax.annotate(txt, (ex, ny), xytext=(4, 3), textcoords="offset points", fontsize=6, bbox=_KASTEN,
                        zorder=6, fontweight="bold" if name in ("Endanflug", "Touchdown") else "normal")
        ax.add_patch(plt.Circle((0, 0), R, fill=False, lw=1, color="red", zorder=5))
        ax.add_patch(plt.Circle((0, 0), 17, fill=False, ls="--", lw=0.7, color="red", zorder=5))
        wl, hw = e["wind_landung"], e["hoehenwind"]
        lehn = wl if e["station"] == "Holfuy Lehn" else None
        wind = (f"Holfuy Lehn {lehn[0]:.0f}° {lehn[4]:.0f} km/h (Spitze {lehn[2]:.0f})" if lehn else
                (f"Volten-Höhe {hw[0]:.0f}° {hw[1]:.0f} km/h" if hw else
                 f"Wind aus Grundgeschw. {e['gs_wind'][1]:.0f} km/h" if e["gs_wind"] else ""))
        pf = lehn or hw or e["gs_wind"]
        if pf:
            zu = math.radians(pf[0] + 180)
            ax.annotate("", (0.07 + 0.045 * math.sin(zu), 0.8 + 0.045 * math.cos(zu) * vb), (0.07, 0.8),
                        xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", color="deepskyblue", lw=2,
                                                                  path_effects=_kontur("white", 3.5)))
        st = Path(igc).stem
        ax.text(0.015, 0.975, f"{st[8:10]}.{st[5:7]}. #{st[-1]} · Endanflug {e['final_kurs']:.0f}°\n{wind}",
                transform=ax.transAxes, va="top", fontsize=6.5, bbox=_KASTEN, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
    if len(fl) % 2:                                                 # freies Feld: Legende
        ax = fig.add_axes([l + bw + sp + 0.03, 1 - o - nz * bh - (nz - 1) * zs + 0.04, bw - 0.06, 0.012])
        fig.colorbar(cm.ScalarMappable(norm, "viridis"), cax=ax, orientation="horizontal",
                     label="Höhe über Grund [m]")
        fig.text(l + bw + sp + 0.01, 1 - o - (nz - 1) * (bh + zs) - 0.01,
                 "Kartenansicht aller Landungen in Lehn\n\n"
                 "Alle Felder im gleichen Massstab, Norden oben.\n"
                 f"Track ab {vorlauf:.0f} s vor dem Gegenanflug bis Bodennähe (≤ 1 m).\n"
                 "Rote Kreise: Beginn Gegen-, Quer-, Endanflug,\n"
                 "Zahl = GPS-Höhe am Vario (m ü. M.).\n"
                 "Fett: Endanflug-Beginn und Abstand der Bodennähe\n"
                 "zum Punkt (Fusskontakt 1–3 s später).\n"
                 "Zielkreis r = 15 m, Prüfungskreis 34 m Ø gestrichelt.\n"
                 "Pfeil: Wind (weht in Pfeilrichtung).\n"
                 "Wind: Holfuy Lehn während der Landung (nur 31.10.),\n"
                 "sonst auf Volten-Höhe aus den Kreisen.\n\n"
                 "Plan: Endanflug bei 615 m (+ Korrektur Vario).",
                 va="top", fontsize=7)
    fig.suptitle("Landungen Lehn — Kartenansicht", y=0.995, fontsize=10, fontweight="bold")
    OUT.mkdir(exist_ok=True)
    for f in (OUT / "landungen_lehn_a4.png", OUT / "landungen_lehn_a4.pdf"):
        fig.savefig(f, dpi=300)
        print(f"Plot: {f}")


# ------------------------------------------------------------------ Höhen-Check

def gelaendehoehe(e: float, n: float) -> float:
    """swisstopo-Geländehöhe (swissALTI3D, LN02) an einem LV95-Punkt — wie Rechtsklick auf map.geo.admin.ch."""
    import requests
    r = requests.get("https://api3.geo.admin.ch/rest/services/height",
                     params={"easting": f"{e:.2f}", "northing": f"{n:.2f}", "sr": 2056}, timeout=30)
    return float(r.json()["height"])


def _smn_reihe(datum: dt.date, abk: str = "INT") -> list[dict]:
    """SMN-10-min-Zeilen aus dem Tagesarchiv (lagecheck.py archiv), sonst direkt von MeteoSchweiz."""
    arch = sorted((Path(__file__).resolve().parent / "archiv").glob(f"{datum}_*/roh/meteoswiss-{abk}_10min.csv"))
    if arch:
        txt = arch[0].read_text(encoding="utf-8")
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from lagecheck import _smn_tag_csv
        txt = _smn_tag_csv(abk, datum)
    z = txt.splitlines()
    return [dict(zip(z[0].split(";"), r.split(";"))) for r in z[1:]] if z else []


def _smn_wert(reihe: list[dict], t_lokal: float, utc_off: int, feld: str) -> float | None:
    """Wert des 10-min-Intervalls, das t_lokal enthält (Zeitstempel = Intervallende, UTC)."""
    best = None
    for x in reihe:
        t = dt.datetime.strptime(x["reference_timestamp"], "%d.%m.%Y %H:%M")
        s_ = (t.hour + utc_off) * 3600 + t.minute * 60
        if s_ >= t_lokal and x.get(feld):
            if best is None or s_ < best[0]:
                best = (s_, float(x[feld]))
    return best[1] if best else None


def _ruhe(tr: Track, wo: str, n: int = 10) -> slice:
    """Ruhephase am Boden: vor dem Start (Grundgeschw. < 3 km/h) bzw. die letzten n Fixes."""
    if wo == "landung":
        return slice(len(tr.t) - n, None)
    gs = np.r_[0, np.hypot(np.diff(tr.e), np.diff(tr.n)) / np.maximum(1, np.diff(tr.t))] * 3.6
    los = int(np.argmax(gs > 8)) or n
    return slice(max(0, los - n - 3), max(1, los - 3))


def hoehen(igcs: list[str], ziel: str) -> None:
    """GPS- und Baro-Höhe des IGC an Start und Landung gegen swissALTI3D.

    Baro im IGC = ISA-Druckhöhe (HFALP:ISA, 1013.25 hPa) -> mit dem QNH von Interlaken (SMN INT) auf
    Meereshöhe umgerechnet = was ein auf QNH gestelltes Vario zeigt. Die Höhendifferenz Start -> Landung
    sagt, wie gut ein am Start auf die richtige Höhe gestelltes Vario bei der Landung stimmt.
    Gerät am Piloten: ~1 m über Boden (stehend/sitzend) ist nicht abgezogen.
    """
    print("Flug           Ort      Gelände  GPS (Δ)          Baro QNH (Δ)     QNH     T INT")
    zeilen = []
    for igc in igcs:
        tr = lade_igc(igc)
        reihe = _smn_reihe(tr.datum)
        erg = {}
        for wo in ("start", "landung"):
            sl = _ruhe(tr, wo)
            e, n = float(np.median(tr.e[sl])), float(np.median(tr.n[sl]))
            t = float(np.median(tr.t[sl]))
            gel = gelaendehoehe(e, n)
            gps = float(np.median(tr.gnss[sl]))
            isa = float(np.median(tr.baro[sl]))
            qnh = _smn_wert(reihe, t, tr.utc_offset_h, "pp0qnhs0")
            temp = _smn_wert(reihe, t, tr.utc_offset_h, "tre200s0")
            p = 1013.25 * (1 - isa / 44330.8) ** 5.25588            # Druck aus ISA-Höhe
            baro = 44330.8 * (1 - (p / qnh) ** 0.190263) if qnh else float("nan")
            erg[wo] = (gel, gps, baro, isa, qnh, temp, t)
            print(f"{Path(igc).stem[:10]} #{Path(igc).stem[-1]}  {wo:8s} {gel:7.1f}  {gps:7.1f} ({gps - gel:+5.1f})  "
                  f"{baro:7.1f} ({baro - gel:+5.1f})  {qnh or 0:6.1f}  {temp if temp is not None else float('nan'):4.1f}")
        (g0, gps0, b0, i0, q0, t0, s0), (g1, gps1, b1, i1, q1, t1, s1) = erg["start"], erg["landung"]
        d_true, d_gps, d_isa = g0 - g1, gps0 - gps1, i0 - i1
        # Temperaturkorrektur: Schicht-Mitteltemperatur aus INT + 6.5 K/km gegenüber ISA
        t_mittel = (t1 if t1 is not None else 15) + 273.15 - 0.0065 * d_true / 2
        t_isa = 288.15 - 0.0065 * (i0 + i1) / 2
        d_korr = d_isa * t_mittel / t_isa
        zeilen.append((Path(igc).stem, d_true, d_gps, d_isa, d_korr, (s1 - s0) / 60, (q1 or 0) - (q0 or 0)))
        print(f"   Höhendifferenz Start->Landung: Gelände {d_true:.1f} m | GPS {d_gps:.1f} ({d_gps - d_true:+.1f}) | "
              f"Baro {d_isa:.1f} ({d_isa - d_true:+.1f}) | Baro temperaturkorrigiert {d_korr:.1f} "
              f"({d_korr - d_true:+.1f}) | Flugzeit {(s1 - s0) / 60:.0f} min, QNH-Änderung {(q1 or 0) - (q0 or 0):+.1f} hPa")
    if zeilen:
        a = np.array([[z[2] - z[1], z[3] - z[1], z[4] - z[1]] for z in zeilen])
        print(f"Mittel Fehler Start->Landung: GPS {a[:, 0].mean():+.1f} m (±{a[:, 0].std():.1f}), "
              f"Baro {a[:, 1].mean():+.1f} m (±{a[:, 1].std():.1f}), Baro T-korr. {a[:, 2].mean():+.1f} m")


# ------------------------------------------------------------------ Plan

# Kalibrierung aus 7 Lehn-Flügen (Alpha 6 24; 24.09., 25.09., 31.10.2026), Gegenwind im Endanflug
# 0–15 km/h (Höhenwind aus den Kreisen, 24.09. Flug 3 aus Gegen-/End-Grundgeschwindigkeit):
#   Endanflug   Luft 23–29 km/h (Mittel 25.7), Sinken 1.24–1.85 m/s (Median 1.36; 31.10.: 1.70/1.85)
#   Queranflug  Sinken 1.0–1.8 m/s (Median 1.6);  Gegenanflug Luft 29–35 km/h, Sinken 1.0–2.3 (Median 1.4)
#   Geometrie: Endanflug 118–289 m (Median 153), Queranflug 200–230 m, Gegenanflug 270–370 m.
#   Validierung 05.11.2026 (eigene + unabhängige Zweitprüfung): Gleitweg ab Endanflug-Beginn in 6 von 7
#   Flügen >= Plan mit 1.8 m/s (31.10. #1: −3 m) -> Plan vorsichtig, in ruhiger Luft kommt man hoch an,
#   Rest mit S-Kurven. Bodennähe (<= 1 m) 6–28 m vor dem Punkt, 2 s später im Median nur ~5 m.
#   Gegen-/Queranflug-Sinken im Mittel getroffen (±15–20 m Streuung); Queranflug inkl. Kurve bei ~200 m
#   Länge 47–77 m statt 40 m -> QUER_RESERVE. Höhenwind / Holfuy längs Achse am 31.10.: 0.8–1.0.
#   Höhen hier = wahre Höhe (Baro, am Boden genullt) + Zielhöhe. Vario-GPS zeigte in der Volte im Mittel
#   +3 m mehr (−1…+6, je Tag fest ≈ GPS am Boden in Lehn − 565).
KALIB = {"End": (25.5, 1.80), "Quer": (30.0, 1.60), "Gegen": (30.0, 1.40)}
END_RUHIG = (25.5, 1.35)
GEOM = {"End": 145.0, "Quer": 210.0, "Gegen": 350.0}
QUER_RESERVE = 10.0    # m Reserve am Beginn des Queranflugs (zu tief -> früher eindrehen, zu hoch -> verlängern)
FAKTOR = 1.0           # Höhenwind / Holfuy Lehn (31.10.: 0.8–1.0 längs Achse; früher 1.3, nicht belegt)
# Geflogen (Gegenwind Volten-Höhe km/h, Endanflug ab m AGL, Distanz zum Punkt m, Touchdown zu kurz m)
FLUEGE = [(9.0, 99, 289, 9.5), (0.4, 52, 186, 10.1), (14.6, 50, 118, 14.3), (4.9, 54, 260, 7.4),
          (3.7, 32, 123, -5.6), (7.1, 40, 135, 27.7), (7.9, 49, 153, 5.9)]
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
    h_q = h_e + geom["Quer"] * w_q / gs_q + QUER_RESERVE
    h_g = h_q + geom["Gegen"] * w_g / ((v_g + u) / 3.6)
    return {"u": u, "ok": True, "gs_e": gs_e * 3.6, "gz_e": gs_e / w_e, "h_e": h_e,
            "vorhalt": math.degrees(math.asin(min(1.0, u / v_q))), "h_q": h_q, "h_g": h_g,
            "l_e50": 50 * gs_e / w_e}


def plan(winde: list[float], faktor: float, png: bool) -> None:
    """Tabelle + Grafik: ideale Höhen je Gegenwind (Volten-Höhe), dazu Mast-Äquivalent."""
    print("Kalibrierung Lehn, 7 Flüge 24.09.–31.10.2026 (Alpha 6 24): " + ", ".join(
        f"{k} {v:.0f} km/h / {w:.2f} m/s" for k, (v, w) in KALIB.items()))
    print(f"Geometrie: Endanflug {GEOM['End']:.0f} m, Queranflug {GEOM['Quer']:.0f} m, "
          f"Gegenanflug {GEOM['Gegen']:.0f} m. Höhenwind ≈ Mast Lehn × {faktor:.1f} (31.10.: 0.8–1.0 längs Achse). "
          f"Queranflug mit {QUER_RESERVE:.0f} m Reserve.")
    print("Gegenwind  Mast≈  | Beginn Gegen  Beginn Quer  Beginn End | GS End  GZ Grund | Endanflug-Länge "
          "ab 50 m | Vorhalt Quer | End ruhige Luft | End im Trimm*")
    rows = []
    for u in sorted(set(winde)):
        r, t, q = plan_rechnen(u), plan_rechnen(u, end=TRIMM), plan_rechnen(u, end=END_RUHIG)
        rows.append((r, t))
        if not r["ok"]:
            print(f"  {u:4.0f}    {u / faktor:4.0f}   | angebremst kein Vorwärtskommen — "
                  f"Trimm: Endanflug ab {t['h_e']:.0f} m"); continue
        print(f"  {u:4.0f}    {u / faktor:4.0f}   |   {r['h_g']:5.0f} m      {r['h_q']:5.0f} m    {r['h_e']:5.0f} m "
              f"|  {r['gs_e']:4.0f}    {r['gz_e']:4.1f}   |     {r['l_e50']:4.0f} m          |    {r['vorhalt']:3.0f}°"
              f"       |     {q['h_e']:4.0f} m     |  {t['h_e']:4.0f} m" + ("   ⚠ GS < 12 km/h: Bremse lösen, Trimm-Spalte" if r["gs_e"] < 12 else ""))
    print("Gemessen bei 0–15 km/h Gegenwind (7 Flüge); darüber extrapoliert. Beginn End = mit hohem Sinken "
          "(1.8 m/s, sicher), «ruhige Luft» = 1.35 m/s: dazwischen liegt die Spanne, die du mit S-Kurven ausgleichst.")
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
    a1.plot([q["u"] for q in (plan_rechnen(r["u"], end=END_RUHIG) for r in ok)],
            [plan_rechnen(r["u"], end=END_RUHIG)["h_e"] for r in ok], ":", color="tab:red", lw=0.8,
            label=f"Beginn Endanflug, ruhige Luft ({END_RUHIG[1]} m/s)")
    a1.scatter([f[0] for f in FLUEGE], [f[1] * GEOM["End"] / f[2] for f in FLUEGE], c=[f[3] for f in FLUEGE],
               cmap="coolwarm", vmin=-30, vmax=30, marker="o", edgecolors="k", zorder=5,
               label=f"geflogen, Endanflug auf {GEOM['End']:.0f} m skaliert (Farbe: rot = zu kurz)")
    a1.set_xlabel(f"Gegenwind im Endanflug auf Volten-Höhe [km/h]  (Mast ≈ ÷ {faktor:.1f})")
    a1.set_ylabel("Höhe AGL [m]")
    a1.set_title(f"Lehn: Eckpunkt-Höhen (Endanflug {GEOM['End']:.0f} m, Queranflug {GEOM['Quer']:.0f} m)")
    a1.grid(lw=0.3); a1.legend()
    a2.plot(u, [r["l_e50"] for r in ok], "o-", ms=3, color="tab:red")
    a2.set_xlabel("Gegenwind im Endanflug [km/h]")
    a2.set_ylabel("Distanz zum Punkt [m]")
    a2.set_title("Wo einkurven, wenn der Endanflug auf 50 m AGL beginnt (angebremst)")
    a2.grid(lw=0.3)
    fig.suptitle("Landeeinteilung Lehn — kalibriert auf Alpha 6 24, 7 Flüge 24.09.–31.10.2026")
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
    a.add_argument("--wind", help="Holfuy-Archiv-JSON (*_15min.json) oder SMN-CSV (*_10min.csv) aus lagecheck.py archiv")
    a.add_argument("--kein-plot", action="store_true")
    p = sub.add_parser("plan")
    p.add_argument("--gegenwind", default="0,2,4,6,8,10,12,14,16,18,20",
                   help="Gegenwind im Endanflug auf Volten-Höhe, km/h (Liste)")
    p.add_argument("--faktor", type=float, default=FAKTOR, help="Höhenwind / Mastwind")
    p.add_argument("--kein-plot", action="store_true")
    v = sub.add_parser("volten", help="Landevolten je Gegenwind auf der swisstopo-Karte")
    v.add_argument("--gegenwind", default="0,5,10,15", help="Gegenwind auf Volten-Höhe, km/h (Liste)")
    v.add_argument("--kurs", type=float, default=250, help="Endanflug-Kurs ° (31.10.: 250 = gegen WSW-Wind)")
    v.add_argument("--seite", choices=("rechts", "links"), default="rechts", help="Rechts-/Linksvolte")
    v.add_argument("--faktor", type=float, default=FAKTOR, help="Höhenwind / Mastwind")
    v.add_argument("--flug", nargs="*", default=[], help="geflogene IGC zum Vergleich darüberlegen")
    v.add_argument("--ziel", default="lehn", choices=sorted(ZIELE))
    v.add_argument("--ebene", default=KARTE, help="WMS-Ebene (Landeskarte: ch.swisstopo.pixelkarte-farbe)")
    v.add_argument("--spicker", action="store_true", help="kleines Bild mit grosser Schrift für den A4-Spicker")
    k = sub.add_parser("karte", help="alle Landungen auf einer Karte")
    k.add_argument("igc", nargs="+")
    k.add_argument("--ziel", default="lehn", choices=sorted(ZIELE))
    k.add_argument("--ebene", default=KARTE)
    bl = sub.add_parser("blatt", help="Kartenansicht aller Landungen auf einer A4-Seite (PNG + PDF)")
    bl.add_argument("igc", nargs="+")
    bl.add_argument("--ziel", default="lehn", choices=sorted(ZIELE))
    bl.add_argument("--ebene", default=KARTE)
    h = sub.add_parser("hoehen", help="GPS-/Baro-Höhe an Start und Landung gegen swissALTI3D")
    h.add_argument("igc", nargs="+")
    h.add_argument("--ziel", default="lehn", choices=sorted(ZIELE))
    x = ap.parse_args(argv)
    if x.cmd == "hoehen":
        hoehen(x.igc, x.ziel)
        return 0
    if x.cmd == "volten":
        volten([float(w) for w in x.gegenwind.split(",")], x.kurs, x.seite, x.faktor, x.flug, x.ziel, x.ebene,
               x.spicker)
        return 0
    if x.cmd == "blatt":
        blatt(x.igc, x.ziel, x.ebene)
        return 0
    if x.cmd == "karte":
        karte_alle(x.igc, x.ziel, x.ebene)
        return 0
    if x.cmd == "analyse":
        for f in x.igc:
            analyse(f, x.ziel, x.wind, not x.kein_plot)
            print()
    else:
        plan([float(v) for v in x.gegenwind.split(",")], x.faktor, not x.kein_plot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
