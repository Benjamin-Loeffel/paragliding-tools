#!/usr/bin/env python
"""Landeanalyse: Volte aus dem IGC zerlegen und mit dem gemessenen Wind am Landeplatz lesen.

    analyse   IGC -> Touchdown, Abstand zum Zielpunkt (zu kurz/zu weit, seitlich), Volte in
              Segmente (Gegen-, Quer-, Endanflug, Kurven) mit Höhe AGL, Grundgeschwindigkeit,
              Sinken, Gleitzahl über Grund, Luftgeschwindigkeit und Vorhaltewinkel
              (Grund- minus Windvektor). Plot: Grundriss + Höhenprofil.
    plan      Ideale Höhen an den Eckpunkten der Volte für einen Wind (Richtung/Stärke) —
              rückwärts vom Zielpunkt gerechnet, mit dem aus eigenen Flügen kalibrierten
              Sinken/Fahrt je Abschnitt.

Wind: Holfuy-2-min-Reihe aus `lagecheck.py archiv` (am Flugtag selbst sichern, Vortage gibt
Holfuy nur noch 15-min). Der Wind am Mast (10 m) ist schwächer als auf 50–150 m AGL — die
Luftgeschwindigkeit daraus ist eine Schätzung, der Vergleich zwischen Flügen bleibt gültig.

Beispiele:
    python alleinflüge/landeanalyse.py analyse D:/.../2026-10-31-XTR-...-02.IGC --ziel lehn \
        --wind alleinflüge/archiv/2026-10-31_interlaken/roh/holfuy-1850_15min.json
    python alleinflüge/landeanalyse.py plan --ziel lehn --wind-aus 245 --wind 9
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
    wx = wy = 0.0
    if w:
        zu = math.radians(w[0] + 180)            # Wind weht NACH
        wx, wy = w[1] / 3.6 * math.sin(zu), w[1] / 3.6 * math.cos(zu)

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

    erg = {"datei": Path(pfad).name, "final_kurs": final, "wind": w, "gnss_off": gnss_off,
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


def _drucke(erg: dict) -> None:
    w = erg["wind"]
    print(f"== {erg['datei']}   Endanflug-Kurs {erg['final_kurs']:.0f}°")
    if w:
        print(f"   Wind Station (Volte ±5 min): aus {w[0]:.0f}° {w[1]:.1f} km/h, Böe max {w[2]:.0f} "
              f"({w[3]} Werte)  -> Gegenwind im Endanflug "
              f"{w[1] * math.cos(math.radians(w[0] - erg['final_kurs'])):+.1f} km/h (Mast 10 m; in der Höhe meist mehr)")
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

def plan(gegenwind: list[float], l_end: float, l_quer: float, luft: dict, sinken: dict) -> None:
    """Höhen an den Eckpunkten rückwärts vom Ziel: h = Weg / Grundgeschw. × Sinken.

    Geometrie fest (Endanflug-Länge, Queranflug-Länge); Endanflug gegen den Wind (Gegenwind u),
    Queranflug quer (Vorhalten: Grundgeschw. = √(V² − u²)), Gegenanflug mit Rückenwind.
    """
    print(f"Geometrie: Endanflug {l_end:.0f} m, Queranflug {l_quer:.0f} m. Fahrt/Sinken je Abschnitt: "
          + ", ".join(f"{k} {luft[k]:.0f} km/h / {sinken[k]:.2f} m/s" for k in ("End", "Quer")))
    print("Gegenwind km/h | GS End | Höhe Beginn Endanflug | GS Quer | Vorhalt | Höhe Beginn Queranflug")
    for u in gegenwind:
        v_e, v_q = luft["End"] / 3.6, luft["Quer"] / 3.6
        gs_e = v_e - u / 3.6
        if gs_e <= 0.5:
            print(f"  {u:5.0f}        steht/rückwärts — Geometrie nicht fliegbar"); continue
        h_e = l_end / gs_e * sinken["End"]
        gs_q = math.sqrt(max(0.01, v_q ** 2 - (u / 3.6) ** 2))
        crab = math.degrees(math.asin(min(1, (u / 3.6) / v_q)))
        h_q = h_e + l_quer / gs_q * sinken["Quer"]
        print(f"  {u:5.0f}        {gs_e * 3.6:5.1f}        {h_e:5.0f} m              {gs_q * 3.6:5.1f}   "
              f"{crab:4.0f}°        {h_q:5.0f} m")


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
    p.add_argument("--gegenwind", default="0,5,10,15,20", help="km/h im Endanflug, Liste")
    p.add_argument("--l-end", type=float, default=130); p.add_argument("--l-quer", type=float, default=170)
    p.add_argument("--luft-end", type=float, default=30); p.add_argument("--luft-quer", type=float, default=34)
    p.add_argument("--sinken-end", type=float, default=1.9); p.add_argument("--sinken-quer", type=float, default=1.6)
    x = ap.parse_args(argv)
    if x.cmd == "analyse":
        for f in x.igc:
            analyse(f, x.ziel, x.wind, not x.kein_plot)
            print()
    else:
        plan([float(v) for v in x.gegenwind.split(",")], x.l_end, x.l_quer,
             {"End": x.luft_end, "Quer": x.luft_quer}, {"End": x.sinken_end, "Quer": x.sinken_quer})
    return 0


if __name__ == "__main__":
    sys.exit(main())
