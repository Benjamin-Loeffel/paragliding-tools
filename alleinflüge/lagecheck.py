#!/usr/bin/env python
"""Lage-Check für Alleinflug-Briefings: Messwerte, Webcams, Fahrplan — reproduzierbar statt ad hoc.

Holt, was sich beim Interlaken-Briefing bewährt hat (Quellen siehe
`.claude/skills/alleinflug-briefing/datenquellen.md`):

    jetzt      Kurz-Briefing Lehn (2-min-Werte): Wind jetzt/10/30 min, Trend, Böigkeit, Berg-/Talwind seit
               wann, Nähe zum Kipppunkt, passende Volte mit Höhen; Amisbühl/Hohwald (Wolke?).
    holfuy     Holfuy-Stationen (15-min-Werte des Tages): Wind, Böe, rF, Temperatur.
               rF 100 % über Stunden = Station steckt in der Wolke (Nebel/Stratus).
    smn        MeteoSchweiz SMN (offene Daten, 10 min): Wind, Böe, Sonne, Globalstrahlung.
               Sonne 0 min + tiefe Strahlung = Hochnebel über der Station.
    bise       Bise-Index: Druckdifferenz Güttingen/Kloten − Genf (QFF) + Wind Genf.
               + ~2 hPa mit NE-Wind = Bise; Bise ist nachmittags am stärksten.
               --prognose: derselbe Index aus dem Modell-Bodendruck für heute/morgen.
    webcam     Roundshot-Panoramen: aktuelles Bild oder stündlicher Verlauf eines Tages
               als Kontaktbogen (JPG) — zeigt, wann/ob sich Nebel hebt.
    verlauf    winds.mobi (alle Netze, ~48 h zurück): Stundenmatrix Station × Stunde für einen
               Tag — Ketten lesen (kommt die Bise an?), Quervergleich mit gestern.
    modell     Open-Meteo-Punktprognose: ICON-CH1 10 m + ICON-D2 Druckflächenwind (850/800/700 hPa),
               mit Vortagen — erst gegen die Messung prüfen, dann für morgen lesen.
    archiv     Tagesarchiv: Rohdaten (winds.mobi) + Stundenmatrix + Bise-Index + Modell nach
               alleinflüge/archiv/<datum>_<name>/ (gitignored). Nur ~48 h zurück möglich!
    fahrplan   Verbindungen (transport.opendata.ch), z. B. Rückweg Landeplatz -> Startplatz.

Beispiele:
    python alleinflüge/lagecheck.py jetzt                 # Lehn + Amisbühl + Hohwald, auf den Punkt
    python alleinflüge/lagecheck.py jetzt --bis 08:20     # Rückblick: Stand um 08:20 heute
    python alleinflüge/lagecheck.py holfuy 1850 1808 1829
    python alleinflüge/lagecheck.py smn INT THU BRZ
    python alleinflüge/lagecheck.py bise --ab 6
    python alleinflüge/lagecheck.py webcam interlaken-harderkulm schynige-platte
    python alleinflüge/lagecheck.py webcam interlaken-harderkulm --verlauf 2026-10-30
    python alleinflüge/lagecheck.py fahrplan 8576887 8504110 --datum 2026-10-31 --zeit 11:00
    python alleinflüge/lagecheck.py verlauf holfuy-484 slf-ADE3 meteoswiss-ABO --datum 2026-10-30
    python alleinflüge/lagecheck.py modell 46.453 7.496 --tage 3
    python alleinflüge/lagecheck.py archiv 2026-10-30 hahnenmoos holfuy-484 slf-ADE3 --punkt 46.453,7.496

Stations-/Webcam-IDs je Fluggebiet: siehe `startplaetze.md` im Skill. Liefert Fakten, keine
Go/No-Go-Entscheidung.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import io
import json
import re
import sys
from pathlib import Path

import requests

UA = {"User-Agent": "Mozilla/5.0 (paragliding lagecheck)"}
OUT = Path(__file__).resolve().parent / "lagecheck_out"   # gitignored (Bilder)
RICHTUNG = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _richtung(grad: float) -> str:
    return RICHTUNG[int((grad + 11.25) % 360 // 22.5)]


# ------------------------------------------------------------------ Holfuy

def holfuy(stationen: list[str], n: int) -> None:
    """Holfuy-Webseite parsen (keine freie API). Erste Tabelle = 15-min-Werte von heute."""
    for sid in stationen:
        t = requests.get(f"https://holfuy.com/en/weather/{sid}", headers=UA, timeout=30).text
        name = re.search(r"<title>([^<]*)</title>", t)
        rows = []
        for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", t, re.S):
            rows.append([re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                         for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.S)])
        try:
            i = next(k for k, r in enumerate(rows) if r and r[0] == "Time")
        except StopIteration:
            print(f"== {sid}: keine Tabelle gefunden (Seite geändert?)")
            continue
        tab = {r[0]: r[1:] for r in rows[i:i + 7] if r}
        tk = next((k for k in tab if k.startswith("Temp")), None)
        rf = tab.get("Humidity (%)")          # nicht jede Station misst rF (z. B. 484 Metschstand)
        zeiten = tab.get("Time", [])
        print(f"== Holfuy {sid}  {html.unescape(name.group(1)).replace('Holfuy: ', '').split(',')[0].strip() if name else ''}")
        print("   Zeit   Richtung   Mittel/Böe     rF      T")
        for k in range(max(0, len(zeiten) - n), len(zeiten)):
            print(f"  {zeiten[k]:>5}  {tab['Direction Deg.'][k]:>9}  {tab['Speed'][k]:>3}/{tab['Gust (km/h)'][k]:>3} km/h"
                  f"  {rf[k] if rf else '-':>5} %  {tab[tk][k] if tk else '-':>5} °C")


# ------------------------------------------------------------------ MeteoSchweiz SMN

def _smn_stunden(abk: str) -> list[tuple[dt.datetime, dict]] | None:
    """MeteoSchweiz OGD, 10-min-Werte des laufenden Tages -> volle Stunden in Lokalzeit."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Zurich")
    except Exception:          # tzdata fehlt -> MEZ annähern
        tz = dt.timezone(dt.timedelta(hours=1))
    s = abk.lower()
    r = requests.get(f"https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/{s}/ogd-smn_{s}_t_now.csv",
                     timeout=30)
    if r.status_code != 200:
        return None
    out = []
    for row in csv.DictReader(io.StringIO(r.content.decode("latin-1")), delimiter=";"):
        t = dt.datetime.strptime(row["reference_timestamp"], "%d.%m.%Y %H:%M").replace(
            tzinfo=dt.timezone.utc).astimezone(tz)
        if t.minute == 0:
            out.append((t, row))
    return out


def smn(stationen: list[str], ab_stunde: int) -> None:
    """MeteoSchweiz OGD, 10-min-Werte des laufenden Tages. Zeitstempel UTC -> Lokalzeit."""
    for s in stationen:
        rows = _smn_stunden(s)
        if rows is None:
            print(f"== SMN {s.upper()}: nicht verfügbar")
            continue
        print(f"== SMN {s.upper()}  (Lokalzeit, volle Stunden)")
        print("   Zeit  Richtung   Mittel  Böe   Sonne/10min  Strahlung")
        for t, row in rows:
            if t.hour < ab_stunde:
                continue
            try:
                d = float(row["dkl010z0"]); v = float(row["fu3010z0"]); g = float(row["fu3010z1"])
                w = f"{_richtung(d):>4} {d:4.0f}°  {v:5.1f}  {g:5.1f}"
            except ValueError:
                w = "  – (kein Wind)            "
            print(f"   {t:%H:%M}  {w}  {row.get('sre000z0', ''):>5} min  {row.get('gre000z0', ''):>6} W/m²")


def bise(ab_stunde: int) -> None:
    """Bise-Indikator: Druckdifferenz Nordost − Genf (QFF) + Wind in Genf.

    Bise, sobald der Druck im Nordosten (Güttingen/Kloten) höher ist als in Genf; je grösser die
    Differenz, desto stärker (Faustregel ab ~2 hPa mit NE-Wind; ~8–9 hPa = aussergewöhnlicher
    Bisensturm laut MeteoSchweiz). Die Bise ist nachmittags am stärksten (SRF Meteo) — ein
    Nacht-/Morgenwind, der mittags einschläft, ist eher Bergwind.
    """
    daten = {k: _smn_stunden(k) for k in ("GVE", "KLO", "GUT")}
    if any(v is None for v in daten.values()):
        print("Stationen nicht verfügbar:", [k for k, v in daten.items() if v is None]); return
    qff = {k: {t: row.get("pp0qffs0") for t, row in v} for k, v in daten.items()}
    print("Bise-Index (QFF hPa, Lokalzeit)   + = Druck NE höher als Genf = Bise")
    print("   Zeit   GUT−GVE  KLO−GVE   Wind Genf")
    for t, row in daten["GVE"]:
        if t.hour < ab_stunde:
            continue
        try:
            g = float(qff["GVE"][t])
            d_gut = float(qff["GUT"][t]) - g
            d_klo = float(qff["KLO"][t]) - g
        except (KeyError, ValueError, TypeError):
            continue
        try:
            w = f"{_richtung(float(row['dkl010z0'])):>4} {float(row['fu3010z0']):4.1f}/{float(row['fu3010z1']):4.1f} km/h"
        except ValueError:
            w = "–"
        print(f"   {t:%H:%M}   {d_gut:+5.1f}    {d_klo:+5.1f}    {w}")


BISE_PUNKTE = {"GVE": (46.2475, 6.1278), "KLO": (47.4797, 8.5361), "GUT": (47.6022, 9.2794)}


def bise_prognose(tage: int, modelle: list[str]) -> None:
    """Bise-Index aus dem Modell-Bodendruck (Open-Meteo pressure_msl) für heute + morgen.

    Am 30./31.10.2026 traf ICON-CH1 den gemessenen Index auf ±0.3 hPa — der Druckgradient ist
    viel verlässlicher als der Modellwind am Pass (der lag am 30.10. mittags um Faktor 2 zu hoch).
    """
    for mod in modelle:
        p = {}
        for k, (la, lo) in BISE_PUNKTE.items():
            j = requests.get("https://api.open-meteo.com/v1/forecast", timeout=60, params={
                "latitude": la, "longitude": lo, "hourly": "pressure_msl", "models": mod,
                "timezone": "Europe/Zurich", "past_days": 1, "forecast_days": tage}).json()
            p[k] = dict(zip(j["hourly"]["time"], j["hourly"]["pressure_msl"]))
        print(f"== Bise-Index Prognose {mod}  (QFF hPa, Lokalzeit)")
        print("   Zeit              GUT−GVE  KLO−GVE")
        for t, g in p["GVE"].items():
            if int(t[11:13]) in (6, 9, 12, 15, 18) and g is not None and None not in (p["GUT"][t], p["KLO"][t]):
                print(f"   {t.replace('T', ' ')}   {p['GUT'][t] - g:+5.1f}    {p['KLO'][t] - g:+5.1f}")


# ------------------------------------------------------------------ Roundshot-Webcams

def _roundshot_bilder(slug: str) -> list[dict]:
    d = requests.get(f"https://jungfrau.roundshot.com/{slug}/structure.json", timeout=30).json()
    return d.get("images", [])


def webcam(slugs: list[str], verlauf: str | None, stunden: list[int]) -> None:
    """Aktuelles Panorama oder stündlicher Verlauf eines Tages als Kontaktbogen."""
    from PIL import Image, ImageDraw, ImageFont
    OUT.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except Exception:
        font = ImageFont.load_default()
    for slug in slugs:
        bilder = _roundshot_bilder(slug)
        if not bilder:
            print(f"{slug}: keine Bilder"); continue
        # Basis-URL aus einem beliebigen Bild ableiten (Speicher-ID der Kamera)
        bsp = bilder[0]["structure"]["quarter"]["url_full"]
        basis = bsp.split("/20")[0]           # https://storageN.roundshot.com/<kamera-id>
        if verlauf:
            urls = [(f"{h:02d}:00", f"{basis}/{verlauf}/{h:02d}-00-00/{verlauf}-{h:02d}-00-00_quarter.jpg")
                    for h in stunden]
            ziel = OUT / f"{slug}_{verlauf}_verlauf.jpg"
        else:
            neu = max(bilder, key=lambda b: b["datetime"])["structure"]["quarter"]["url_full"]
            stamp = re.search(r"/(\d{4}-\d{2}-\d{2})/(\d{2})-(\d{2})", neu)
            urls = [(f"{stamp[1]} {stamp[2]}:{stamp[3]}" if stamp else "aktuell", neu)]
            ziel = OUT / f"{slug}_aktuell.jpg"
        zeilen = []
        for label, url in urls:
            r = requests.get(url, timeout=60)
            if r.status_code != 200:
                print(f"  {slug} {label}: fehlt ({r.status_code})"); continue
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            im = im.resize((1600, int(im.height * 1600 / im.width)))
            dr = ImageDraw.Draw(im)
            dr.rectangle([0, 0, 24 + 19 * len(label), 44], fill=(0, 0, 0))
            dr.text((8, 4), label, fill=(255, 255, 0), font=font)
            zeilen.append(im)
        if not zeilen:
            continue
        bogen = Image.new("RGB", (1600, sum(z.height for z in zeilen)))
        y = 0
        for z in zeilen:
            bogen.paste(z, (0, y)); y += z.height
        bogen.save(ziel, quality=85)
        print(f"{slug}: {ziel}")


# ------------------------------------------------------------------ winds.mobi-Verlauf

ARCHIV = Path(__file__).resolve().parent / "archiv"     # gitignored (Rohdaten Dritter)


def _tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Zurich")
    except Exception:
        return dt.timezone(dt.timedelta(hours=1))


def _windsmobi(sid: str, sekunden: int = 172800) -> tuple[dict, list[dict]]:
    """Stationsinfo + Messungen der letzten `sekunden` (winds.mobi hält ~48 h)."""
    api = "https://winds.mobi/api/2.3/stations"
    info = requests.get(f"{api}/{sid}/", timeout=30).json()
    hist = requests.get(f"{api}/{sid}/historic/", params={"duration": sekunden}, timeout=30).json()
    return info, sorted(hist, key=lambda x: x["_id"])


def _stundenwerte(hist: list[dict], datum: dt.date) -> dict[int, dict]:
    """Pro Lokalstunde: Vektormittel Richtung, Mittel der Mittelwerte, Max der Böen, QFF."""
    import math
    tz, out = _tz(), {}
    for x in hist:
        t = dt.datetime.fromtimestamp(x["_id"], tz)
        if t.date() != datum or x.get("w-avg") is None:
            continue
        out.setdefault(t.hour, []).append(x)
    res = {}
    for h, xs in out.items():
        u = sum(x["w-avg"] * math.sin(math.radians(x["w-dir"])) for x in xs)
        v = sum(x["w-avg"] * math.cos(math.radians(x["w-dir"])) for x in xs)
        qff = [x["pres"]["qff"] for x in xs if (x.get("pres") or {}).get("qff")]
        res[h] = {"dir": math.degrees(math.atan2(u, v)) % 360,
                  "avg": sum(x["w-avg"] for x in xs) / len(xs),
                  "max": max(x.get("w-max") or 0 for x in xs),
                  "qff": sum(qff) / len(qff) if qff else None}
    return res


def _matrix(stationen: dict[str, tuple[dict, list[dict]]], datum: dt.date, stunden: list[int]) -> str:
    """Station × Stunde, Zelle «NE 14/20» (Mittel/Böe km/h). Ruhig (< 3 km/h) als «·»."""
    zeilen = [f"{datum}  Stundenmittel Richtung Mittel/Böe km/h (Lokalzeit), Quelle winds.mobi",
              f"{'Station':34s}{'m':>5} " + "".join(f"{h:>9}h" for h in stunden)]
    for sid, (info, hist) in stationen.items():
        sw = _stundenwerte(hist, datum)
        zellen = []
        for h in stunden:
            w = sw.get(h)
            if not w:
                zellen.append(f"{'–':>10}")
            elif w["avg"] < 3:
                zellen.append(f"{'· ' + str(round(w['max'])):>10}")
            else:
                zellen.append(f"{_richtung(w['dir']):>4} {w['avg']:2.0f}/{w['max']:2.0f}")
        name = f"{sid} {info.get('short', '')}"[:33]
        zeilen.append(f"{name:34s}{info.get('alt', ''):>5} " + "".join(zellen))
    return "\n".join(zeilen)


def _bise_matrix(stationen: dict[str, tuple[dict, list[dict]]], datum: dt.date, stunden: list[int]) -> str | None:
    """Bise-Index aus den QFF von winds.mobi (meteoswiss-GVE/-KLO/-GUT müssen dabei sein)."""
    k = {s: _stundenwerte(stationen[f"meteoswiss-{s}"][1], datum)
         for s in ("GVE", "KLO", "GUT") if f"meteoswiss-{s}" in stationen}
    if "GVE" not in k:
        return None
    z = [f"{datum}  Bise-Index QFF hPa (+ = Druck NE höher als Genf)", "Stunde  GUT−GVE  KLO−GVE"]
    for h in stunden:
        g = (k["GVE"].get(h) or {}).get("qff")
        if g is None:
            continue
        d = [((k.get(s) or {}).get(h) or {}).get("qff") for s in ("GUT", "KLO")]
        z.append(f"{h:>4}h  " + "  ".join(f"{x - g:+7.1f}" if x else f"{'–':>7}" for x in d))
    return "\n".join(z)


def verlauf(ids: list[str], datum: dt.date, stunden: list[int]) -> str:
    st = {sid: _windsmobi(sid) for sid in ids}
    txt = _matrix(st, datum, stunden)
    b = _bise_matrix(st, datum, stunden)
    return txt + ("\n\n" + b if b else "")


# ------------------------------------------------------------------ Modell (Open-Meteo)

def modell(lat: float, lon: float, tage: int, vortage: int, stunden: list[int]) -> str:
    """ICON-CH1 10 m (Böen) + ICON-D2 Druckflächen; Vortage zum Prüfen gegen die Messung."""
    base = "https://api.open-meteo.com/v1/forecast"
    gem = {"latitude": lat, "longitude": lon, "timezone": "Europe/Zurich",
           "past_days": vortage, "forecast_days": tage, "wind_speed_unit": "kmh"}
    ch1 = requests.get(base, params={**gem, "models": "meteoswiss_icon_ch1",
                                     "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m"},
                       timeout=60).json()
    lv = ("850hPa", "800hPa", "700hPa")
    d2 = requests.get(base, params={**gem, "models": "icon_d2", "hourly": ",".join(
        f"wind_{a}_{l}" for l in lv for a in ("speed", "direction"))}, timeout=60).json()
    if "hourly" not in ch1 or "hourly" not in d2:
        return f"Open-Meteo-Fehler: {ch1.get('reason') or d2.get('reason')}"
    H1, H2 = ch1["hourly"], d2["hourly"]

    def zelle(d, v, g=None):
        if d is None or v is None:
            return f"{'–':>12}"
        return f"{_richtung(d):>4} {v:3.0f}" + (f"/{g:3.0f}" if g is not None else "    ")

    z = [f"Open-Meteo {lat:.4f}/{lon:.4f}  (Modellhöhe ≠ Gelände; 800 hPa ≈ 1950 m, 850 hPa ≈ 1500 m)",
         f"{'Zeit':16s}{'CH1 10m Mit/Böe':>16}" + "".join(f"{'D2 ' + l:>13}" for l in lv)]
    for i, t in enumerate(H1["time"]):
        if int(t[11:13]) not in stunden:
            continue
        j = H2["time"].index(t) if t in H2["time"] else None
        z.append(f"{t.replace('T', ' '):16s}  " + zelle(H1["wind_direction_10m"][i], H1["wind_speed_10m"][i],
                                                       H1["wind_gusts_10m"][i])
                 + "".join(" " + zelle(H2[f"wind_direction_{l}"][j] if j is not None else None,
                                       H2[f"wind_speed_{l}"][j] if j is not None else None) for l in lv))
    return "\n".join(z)


def _holfuy_15min(nr: str, datum: dt.date) -> list[dict]:
    """Holfuy-Grafikdaten (Mittel, Böe, Minimum, Richtung, T, rF, Druck; Lokalzeit) — die feinste
    öffentliche Historie: **heute im 2-min-Takt**, die Vortage nur noch 15-min. Darum am Flugtag
    selbst archivieren. Live-Werte (`/puget/mjso.php`) gibt es nur für den Moment."""
    t = requests.get(f"https://holfuy.com/dynamic/graphs/tdarr{nr}.js", headers=UA, timeout=30,
                     params={"v": "1"}).text
    arr = {k: json.loads(v.replace("'", '"'))
           for k, v in re.findall(r"var (\w+) = (\[.*?\]);", t, re.S)}
    zeiten = arr.get("unt", [])
    felder = {"gd_speed": "mittel", "gd_gust": "boee", "gd_min_wind": "minimum", "gd_direction": "richtung",
              "gd_temp": "temp", "gd_humidity": "rf", "gd_pressure": "druck"}
    out = []
    for i, z in enumerate(zeiten):
        if dt.datetime.strptime(z, "%Y/%m/%d %H:%M:%S").date() != datum:
            continue
        out.append({"zeit": z, **{n: (arr[k][i] if k in arr and i < len(arr[k]) else None)
                                  for k, n in felder.items()}})
    return out


# ------------------------------------------------------------------ Kurz-Briefing Lehn (jetzt)

LEHN_STATIONEN = {"1850": "Lehn 560 m", "1808": "Amisbühl 1315 m", "1829": "Hohwald 1600 m"}


def _lehn_klasse(richtung, mittel) -> str:
    """Lehn: Bergwind = NNW–ESE (aus dem Bödeli), Talwind = SSW–WNW (vom Thunersee), sonst «anders»."""
    if mittel is None or richtung is None:
        return "?"
    if mittel < 3:
        return "still"
    if richtung >= 340 or richtung <= 120:
        return "Berg"
    if 190 <= richtung <= 295:
        return "Tal"
    return "anders"


def _fenster(werte: list[dict], t_end: dt.datetime, minuten: int) -> dict | None:
    """Kennzahlen der letzten `minuten`: Vektormittel-Richtung, Mittel (arithm.), Böe max, Streuung, Klassen."""
    import math
    w = [x for x in werte if x["mittel"] is not None and x["richtung"] is not None
         and t_end - dt.timedelta(minutes=minuten) < x["t"] <= t_end]
    if not w:
        return None
    u = sum(x["mittel"] * math.sin(math.radians(x["richtung"])) for x in w)
    v = sum(x["mittel"] * math.cos(math.radians(x["richtung"])) for x in w)
    su = sum(math.sin(math.radians(x["richtung"])) for x in w) / len(w)
    sv = sum(math.cos(math.radians(x["richtung"])) for x in w) / len(w)
    r = min(1.0, math.hypot(su, sv))
    streu = math.degrees(math.sqrt(-2 * math.log(r))) if r > 1e-6 else 180.0    # zirkuläre Std.-Abw.
    return {"n": len(w), "dir": math.degrees(math.atan2(u, v)) % 360,
            "mittel": sum(x["mittel"] for x in w) / len(w), "min": min(x["mittel"] for x in w),
            "boee": max((x["boee"] or x["mittel"]) for x in w), "streu": streu,
            "klassen": [_lehn_klasse(x["richtung"], x["mittel"]) for x in w],
            "temp": [x["temp"] for x in w if x.get("temp") is not None],
            "rf": [x["rf"] for x in w if x.get("rf") is not None]}


LEHN_PUNKT = (46.6808, 7.8236)


def _modell_lehn(stunden_zurueck: int = 7, stunden_vor: int = 7) -> dict[str, dict]:
    """ICON-CH1-EPS (11 Member) und ICON-CH2-EPS (21) 10 m am Landeplatz Lehn, stündlich (Open-Meteo Ensemble).

    Je Modell: Zeiten, Kontrolllauf (= deterministisch) Richtung/Mittel/Böe, 10–90-%-Band des Mittelwinds und
    Anteil der Member mit Berg-/Talwind/still je Stunde."""
    import math
    out = {}
    for m, name in (("meteoswiss_icon_ch1_ensemble", "ICON-CH1"), ("meteoswiss_icon_ch2_ensemble", "ICON-CH2")):
        try:
            h = requests.get("https://ensemble-api.open-meteo.com/v1/ensemble", timeout=60, params={
                "latitude": LEHN_PUNKT[0], "longitude": LEHN_PUNKT[1], "timezone": "Europe/Zurich",
                "wind_speed_unit": "kmh", "models": m, "past_hours": stunden_zurueck, "forecast_hours": stunden_vor,
                "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m"}).json()["hourly"]
        except Exception as e:                       # Modell fehlt -> Grafik trotzdem
            print(f"  ({name} nicht geladen: {e})")
            continue
        mem = [k[len("wind_speed_10m"):] for k in h if k.startswith("wind_speed_10m")]   # "" = Kontrolllauf
        reihe = []
        for i, t in enumerate(h["time"]):
            v = [h["wind_speed_10m" + k][i] for k in mem]
            d = [h["wind_direction_10m" + k][i] for k in mem]
            ok = [(vv, dd) for vv, dd in zip(v, d) if vv is not None and dd is not None]
            if not ok or h["wind_speed_10m"][i] is None:
                continue
            kl = [_lehn_klasse(dd, vv) for vv, dd in ok]
            vs = sorted(vv for vv, _ in ok)
            q = lambda f: vs[min(len(vs) - 1, max(0, round(f * (len(vs) - 1))))]
            reihe.append({"t": dt.datetime.fromisoformat(t), "dir": h["wind_direction_10m"][i],
                          "mittel": h["wind_speed_10m"][i], "boee": h["wind_gusts_10m"][i],
                          "q10": q(0.1), "q90": q(0.9), "n": len(ok),
                          **{k: kl.count(k) / len(kl) for k in ("Berg", "Tal", "still", "anders")}})
        out[name] = reihe
    return out


def _grafik_lehn(lehn: list[dict], titel: str, jetzt_t: dt.datetime, stunden: int = 6) -> Path:
    """Grafik für unterwegs: oben Pfeile (wohin der Wind weht), Mitte Mittel/Böe Holfuy Lehn (2 min) der letzten
    `stunden` h und ICON-CH1/CH2 (Kontrolllauf + 10–90-%-Band der Ensembles, vorher zum Prüfen, danach Prognose),
    unten links Radar (Richtung/Stärke: Holfuy letzte Stunde, Modelle −1…+3 h), unten rechts Anteil der Member
    mit Tal-/Bergwind je Stunde."""
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    farbe = {"Berg": "#2b6cb0", "Tal": "#dd6b20", "still": "#a0aec0", "anders": "#805ad5", "?": "#a0aec0"}
    mfarbe = {"Holfuy": "#2f855a", "ICON-CH1": "#c53030", "ICON-CH2": "#6b46c1"}
    t0, t1 = jetzt_t - dt.timedelta(hours=stunden), jetzt_t + dt.timedelta(hours=stunden)
    w = [x for x in lehn if x["t"] >= t0 and x["mittel"] is not None]
    mod = _modell_lehn(stunden + 1, stunden + 1)
    plt.rcParams.update({"font.size": 7})
    fig = plt.figure(figsize=(6.2, 8.8), dpi=250)
    go = fig.add_gridspec(2, 1, height_ratios=[0.8, 3.0], hspace=0.04, top=0.97, bottom=0.47)
    gu = fig.add_gridspec(1, 2, wspace=0.32, top=0.37, bottom=0.07)
    ap = fig.add_subplot(go[0])
    ax = fig.add_subplot(go[1], sharex=ap)
    pr = fig.add_subplot(gu[0], projection="polar")
    pb = fig.add_subplot(gu[1])
    # --- Zeitreihe
    for a, b in zip(w, w[1:] + [None]):
        b_t = b["t"] if b else a["t"] + dt.timedelta(minutes=2)
        ax.axvspan(a["t"], b_t, color=farbe[_lehn_klasse(a["richtung"], a["mittel"])], alpha=0.16, lw=0)
    ax.fill_between([x["t"] for x in w], [x["mittel"] for x in w], color="#38a169", alpha=0.25, lw=0)
    ax.plot([x["t"] for x in w], [x["mittel"] for x in w], color=mfarbe["Holfuy"], lw=1.4, label="Holfuy Lehn Mittel (2 min)")
    ax.plot([x["t"] for x in w], [x["boee"] for x in w], color=mfarbe["Holfuy"], lw=0.9, ls="--", label="Holfuy Böe")
    for name, reihe in mod.items():
        r = [x for x in reihe if t0 - dt.timedelta(hours=1) <= x["t"] <= t1]
        c = mfarbe[name]
        ax.fill_between([x["t"] for x in r], [x["q10"] for x in r], [x["q90"] for x in r], color=c, alpha=0.10, lw=0)
        ax.plot([x["t"] for x in r], [x["mittel"] for x in r], color=c, lw=1.1, marker="o", ms=2,
                label=f"{name} Mittel (Band 10–90 %, {r[0]['n'] if r else 0} Member)")
        ax.plot([x["t"] for x in r], [x["boee"] for x in r], color=c, lw=0.6, ls=":", label=f"{name} Böe")
    for a_ in (ax, ap):
        a_.axvline(jetzt_t, color="k", lw=0.8)
    ap.text(jetzt_t, 2.0, "  jetzt → Prognose", va="center", fontsize=6.5, fontweight="bold")
    ax.set_ylabel("km/h")
    ax.set_ylim(0, max([12] + [x["boee"] or 0 for x in w] + [x["boee"] or 0 for r in mod.values() for x in r
                                                            if t0 <= x["t"] <= t1]) * 1.1)
    ax.grid(lw=0.3, alpha=0.6)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.25)
    ax.legend(loc="upper left", fontsize=5.4, ncol=2, framealpha=0.85, borderaxespad=0.3)
    ax.set_xlim(t0, t1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H"))
    ax.xaxis.set_major_locator(mdates.HourLocator())
    # --- Pfeilzeilen (wohin der Wind weht)
    zeilen = [("Holfuy", 2.0)] + [(n, 1.0 - 0.9 * k) for k, n in enumerate(mod)]
    for name, y in zeilen:
        if name == "Holfuy":
            pfeile, t = [], t0
            while t < jetzt_t:
                f = _fenster(w, t + dt.timedelta(minutes=15), 15)
                if f:
                    pfeile.append((t + dt.timedelta(minutes=7.5), f["dir"], f["mittel"]))
                t += dt.timedelta(minutes=15)
        else:
            pfeile = [(x["t"], x["dir"], x["mittel"]) for x in mod[name] if t0 <= x["t"] <= t1]
        if pfeile:
            zu = [math.radians(d + 180) for _, d, _ in pfeile]
            ap.quiver([mdates.date2num(t) for t, *_ in pfeile], [y] * len(pfeile),
                      [math.sin(z) for z in zu], [math.cos(z) for z in zu],
                      color=[farbe[_lehn_klasse(d, v)] for _, d, v in pfeile], angles="uv", pivot="middle",
                      scale=50 if name == "Holfuy" else 38, width=0.0030 if name == "Holfuy" else 0.0042,
                      headwidth=3.5, headlength=4, headaxislength=3.5)
        ap.text(-0.01, y, name, transform=ap.get_yaxis_transform(), ha="right", va="center", fontsize=6)
    ap.set_ylim(-0.5, 2.5)
    ap.set_yticks([])
    plt.setp(ap.get_xticklabels(), visible=False)
    for sp in ("top", "right", "left"):
        ap.spines[sp].set_visible(False)
    ap.set_title(titel, fontsize=7.5, loc="left", fontweight="bold")
    # --- Radar: Richtung (woher, Norden oben, im Uhrzeigersinn) und Stärke
    pr.set_theta_zero_location("N")
    pr.set_theta_direction(-1)
    h1 = [x for x in w if x["t"] > jetzt_t - dt.timedelta(hours=1)]
    if h1:
        pr.plot([math.radians(x["richtung"]) for x in h1], [x["mittel"] for x in h1], "-o", color=mfarbe["Holfuy"],
                lw=0.9, ms=2.2, label="Holfuy letzte Stunde")
        pr.plot([math.radians(h1[-1]["richtung"])], [h1[-1]["mittel"]], "o", ms=6, mfc="white",
                mec=mfarbe["Holfuy"], mew=1.5)
    for name, reihe in mod.items():
        r = [x for x in reihe if jetzt_t - dt.timedelta(hours=1) <= x["t"] <= jetzt_t + dt.timedelta(hours=3)]
        if not r:
            continue
        pr.plot([math.radians(x["dir"]) for x in r], [x["mittel"] for x in r], "-o", color=mfarbe[name], lw=0.9,
                ms=2.5, label=f"{name} −1…+3 h")
        for x in r:
            pr.annotate(f"{x['t']:%H}", (math.radians(x["dir"]), x["mittel"]), fontsize=4.8, color=mfarbe[name],
                        xytext=(2, 2), textcoords="offset points")
    rmax = max([8] + [x["mittel"] for x in h1] + [x["mittel"] for r in mod.values() for x in r
                                                 if abs((x["t"] - jetzt_t).total_seconds()) <= 4 * 3600])
    pr.set_ylim(0, rmax * 1.1)
    pr.set_xticks([math.radians(a) for a in range(0, 360, 45)], ["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
    pr.tick_params(labelsize=6, pad=0)
    pr.set_rlabel_position(160)
    for a_, c in ((75, farbe["Berg"]), (250, farbe["Tal"])):
        pr.plot([math.radians(a_)] * 2, [0, rmax * 1.1], color=c, lw=0.7, ls="--")
    pr.set_title("Woher und wie stark (km/h)\n--- 75° Bergwind · 250° Talwind", fontsize=6.5, pad=14)
    pr.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), fontsize=5.6, frameon=False)
    # --- Anteil der Member mit Tal-/Bergwind je Stunde (Prognose)
    zukunft = {n: [x for x in r if jetzt_t - dt.timedelta(minutes=30) <= x["t"] <= t1] for n, r in mod.items()}
    for k, (name, r) in enumerate(zukunft.items()):
        if not r:
            continue
        xs = [mdates.date2num(x["t"]) + (k - 0.5) * 0.012 for x in r]
        unten = [0.0] * len(r)
        for kl in ("Tal", "still", "anders", "Berg"):
            hoehe = [x[kl] * 100 for x in r]
            pb.bar(xs, hoehe, bottom=unten, width=0.011, color=farbe[kl], alpha=1.0 if k else 0.65,
                   edgecolor="white", lw=0.3)
            unten = [u + h_ for u, h_ in zip(unten, hoehe)]
    pb.set_ylim(0, 100)
    pb.set_ylabel("% der Member")
    pb.xaxis.set_major_formatter(mdates.DateFormatter("%H"))
    pb.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    pb.tick_params(labelsize=6)
    pb.set_title("Prognose: Anteil der Member mit Tal-/Bergwind\nje Stunde (heller = CH1, kräftig = CH2)",
                 fontsize=6.5, pad=8)
    from matplotlib.patches import Patch
    pb.legend(handles=[Patch(color=farbe[k], label=l) for k, l in
                       (("Tal", "Talwind"), ("still", "still < 3"), ("anders", "anders"), ("Berg", "Bergwind"))],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=5.6, ncol=4, frameon=False)
    fig.text(0.5, 0.005, "Blau = Bergwind (N–ESE), orange = Talwind (SSW–WNW), grau = still < 3 km/h · Pfeile oben: "
             "wohin der Wind weht · Modelle: 10 m am Gitterpunkt Lehn, stündlich (Open-Meteo Ensemble)",
             ha="center", fontsize=5, color="#4a5568")
    OUT.mkdir(exist_ok=True)
    f = OUT / "jetzt_lehn.png"
    fig.savefig(f, bbox_inches="tight")
    plt.close(fig)
    return f


def jetzt(stationen: list[str], bis: str | None = None, grafik: bool = True) -> None:
    """Kurz-Briefing für unterwegs: Lehn jetzt (10/30 min), Trend, Berg-/Talwind und Nähe zum Kipppunkt,
    passende Volte mit Höhen; dazu Amisbühl/Hohwald in je einer Zeile (Wolke?). `bis` = HH:MM zum Testen."""
    import math
    heute = dt.date.today()
    daten = {}
    for sid in stationen:
        roh = _holfuy_15min(sid, heute)
        w = [{**x, "t": dt.datetime.strptime(x["zeit"], "%Y/%m/%d %H:%M:%S")} for x in roh]
        if bis:
            grenze = dt.datetime.combine(heute, dt.time.fromisoformat(bis))
            w = [x for x in w if x["t"] <= grenze]
        daten[sid] = w
    lehn = daten.get("1850") or []
    if not lehn:
        print("Lehn 1850: keine Daten von heute.")
    else:
        t_end = lehn[-1]["t"]
        alter = (dt.datetime.now() - t_end).total_seconds() / 60
        f10, f30 = _fenster(lehn, t_end, 10), _fenster(lehn, t_end, 30)
        vor = _fenster(lehn, t_end - dt.timedelta(minutes=30), 30)
        letzt = lehn[-1]
        kl = _lehn_klasse(f10["dir"], f10["mittel"])
        print(f"LEHN {t_end:%H:%M}" + (f" (vor {alter:.0f} min)" if not bis else "") +
              f": {_richtung(letzt['richtung'])} {letzt['mittel']:.0f}/{letzt['boee']:.0f} km/h")
        print(f"  10 min: {_richtung(f10['dir'])} {f10['dir']:.0f}°, Mittel {f10['mittel']:.0f}, Böe {f10['boee']:.0f}"
              f" | 30 min: {_richtung(f30['dir'])}, Mittel {f30['mittel']:.0f} (min {f30['min']:.0f}), "
              f"Böe {f30['boee']:.0f}, Richtung ±{f30['streu']:.0f}°")
        gruende = []
        wechsel = len(set(k for k in f30["klassen"] if k in ("Berg", "Tal"))) == 2
        if wechsel:
            gruende.append("Berg- und Talwind wechseln sich ab (30 min)")
        if f10["mittel"] < 3:
            gruende.append("fast still")
        if vor and vor["mittel"] >= 3 and f30["mittel"] < 0.6 * vor["mittel"]:
            gruende.append(f"abflauend ({vor['mittel']:.0f} → {f30['mittel']:.0f})")
        if f30["streu"] > 50:
            gruende.append(f"Richtung unruhig (±{f30['streu']:.0f}°)")
        seit = None
        if kl in ("Berg", "Tal"):                    # Beginn der aktuellen Phase (1 Ausreisser toleriert)
            ks = [_lehn_klasse(x["richtung"], x["mittel"]) for x in lehn]
            i, aus = len(ks) - 1, 0
            while i > 0 and aus <= 1:
                aus = 0 if ks[i - 1] == kl else aus + 1
                i -= 1
            while ks[i] != kl:
                i += 1
            seit = lehn[i]["t"]
            dauer = (t_end - seit).total_seconds() / 60
            if dauer < 45:
                gruende.append(f"{kl}wind erst seit {seit:%H:%M} ({dauer:.0f} min)")
        kv = _lehn_klasse(vor["dir"], vor["mittel"]) if vor else "?"
        if kv in ("Berg", "Tal") and kl in ("Berg", "Tal") and kv != kl:
            gruende.append(f"vor 30–60 min noch {kv}wind → gerade gekippt")
        trend = "" if not vor else (f"zunehmend ({vor['mittel']:.0f} → {f30['mittel']:.0f})"
                                   if f30["mittel"] > vor["mittel"] + 2 else
                                   f"abnehmend ({vor['mittel']:.0f} → {f30['mittel']:.0f})"
                                   if f30["mittel"] < vor["mittel"] - 2 else "gleichbleibend")
        boeig = f30["boee"] - f30["mittel"] > 7
        ruhe = "böig" if boeig else ("unruhig" if f30["streu"] > 30 else "stabil")
        print(f"  Lage: {kl + 'wind' if kl in ('Berg', 'Tal') else kl}"
              + (f" seit {seit:%H:%M}" if seit else "") + f", {trend}, {ruhe}.")
        frisch = seit is not None and (t_end - seit).total_seconds() < 20 * 60
        stufe = "NAH" if (wechsel or frisch or (f10["mittel"] < 3 and len(gruende) >= 2)) else             ("MÖGLICH" if gruende else "nicht in Sicht")
        print(f"  Kipppunkt: {stufe}" + (f" — {'; '.join(gruende)}" if gruende else ""))
        if grafik:
            titel = (f"Lehn {t_end:%d.%m. %H:%M}: {_richtung(f10['dir'])} {f10['mittel']:.0f} km/h, Böe {f10['boee']:.0f}"
                     f" (10 min) · {kl + 'wind' if kl in ('Berg', 'Tal') else kl}"
                     + (f" seit {seit:%H:%M}" if seit else "") + f" · Kipppunkt {stufe.lower()}")
            print(f"  Grafik: {_grafik_lehn(lehn, titel, t_end)}")
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from landeanalyse import KALIB, QUER_RESERVE, ZIELE
        TH = ZIELE["lehn"][2]
        kurs, volte = (75, "Linksvolte, Endanflug 75°") if kl == "Berg" else \
            ((250, "Rechtsvolte, Endanflug 250°") if kl == "Tal" else (None, None))
        if kurs is not None:
            u = max(0.0, f10["mittel"] * math.cos(math.radians(f10["dir"] - kurs)))
            le = 50 * (KALIB["End"][0] - u) / 3.6 / KALIB["End"][1]
            hq = 50 + 210 * KALIB["Quer"][1] / (math.sqrt(max(.01, KALIB["Quer"][0] ** 2 - u * u)) / 3.6) + QUER_RESERVE
            hg = hq + (200 + le) * KALIB["Gegen"][1] / ((KALIB["Gegen"][0] + u) / 3.6)
            print(f"  Volte jetzt: {volte}, Gegenwind {u:.0f} → Gegen {TH + hg:.0f} · Quer {TH + hq:.0f} · End 615, "
                  f"eindrehen {round(le / 5) * 5:.0f} m vor dem Punkt (+ Vario-Korrektur)")
        else:
            print("  Volte jetzt: Windsack entscheidet; Zeile 0 km/h (Gegen 732 · Quer 665 · End 615, 195 m)")
        if f30["temp"] and vor and vor["temp"]:
            print(f"  Temperatur Lehn {f30['temp'][-1]:.1f} °C ({f30['temp'][-1] - vor['temp'][0]:+.1f} in 1 h)")
    for sid in stationen:
        if sid == "1850" or not daten.get(sid):
            continue
        w = daten[sid]
        f = _fenster(w, w[-1]["t"], 30)
        if not f:
            continue
        rf = (f"rF {f['rf'][-1]:.0f} %" + (" → in der Wolke" if min(f["rf"]) >= 98 else "")) if f["rf"] else ""
        print(f"{LEHN_STATIONEN.get(sid, sid)} {w[-1]['t']:%H:%M}: {_richtung(f['dir'])} Mittel {f['mittel']:.0f}, "
              f"Böe {f['boee']:.0f} (30 min), {rf}")


def _smn_tag_csv(abk: str, datum: dt.date) -> str:
    """MeteoSchweiz SMN 10-min-Rohzeilen (UTC) eines Tages; t_now für heute, sonst t_recent."""
    s = abk.lower()
    for teil in (("now", "recent") if datum == dt.date.today() else ("recent",)):
        r = requests.get(f"https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/{s}/ogd-smn_{s}_t_{teil}.csv",
                         timeout=60)
        if r.status_code != 200:
            continue
        zeilen = r.content.decode("latin-1").splitlines()
        tag = [z for z in zeilen[1:] if z.split(";")[1].startswith(datum.strftime("%d.%m.%Y"))]
        if tag:
            return "\n".join([zeilen[0], *tag]) + "\n"
    return ""


def archiv(datum: dt.date, name: str, ids: list[str], punkt: str | None, stunden: list[int]) -> None:
    """Rohdaten + Auswertung eines Tages sichern, solange winds.mobi sie noch hat (~48 h).

    Zusätzlich je `holfuy-<nr>` die Holfuy-15-min-Reihe (7 Tage verfügbar) und je `meteoswiss-<abk>`
    die SMN-10-min-Rohdaten (alle Messgrössen, UTC).
    """
    ziel = ARCHIV / f"{datum}_{name}"
    (ziel / "roh").mkdir(parents=True, exist_ok=True)
    st = {}
    for sid in ids:
        try:
            info, hist = _windsmobi(sid)
        except Exception as e:          # einzelne Station darf fehlen
            print(f"  {sid}: {e}"); continue
        tz = _tz()
        tag = [x for x in hist if dt.datetime.fromtimestamp(x["_id"], tz).date() == datum]
        (ziel / "roh" / f"{sid}.json").write_text(
            json.dumps({"info": info, "messungen": tag}, ensure_ascii=False, indent=1), encoding="utf-8")
        st[sid] = (info, hist)
        extra = ""
        if sid.startswith("holfuy-"):
            h15 = _holfuy_15min(sid.split("-", 1)[1], datum)
            (ziel / "roh" / f"{sid}_15min.json").write_text(json.dumps(h15, indent=1), encoding="utf-8")
            extra = f", Holfuy 15 min: {len(h15)}"
        elif sid.startswith("meteoswiss-"):
            c = _smn_tag_csv(sid.split("-", 1)[1], datum)
            (ziel / "roh" / f"{sid}_10min.csv").write_text(c, encoding="utf-8")
            extra = f", SMN 10 min: {max(0, len(c.splitlines()) - 1)}"
        print(f"  {sid}: {len(tag)} Messungen{extra}")
    teile = [_matrix(st, datum, stunden)]
    b = _bise_matrix(st, datum, stunden)
    if b:
        teile.append(b)
    if punkt:
        lat, lon = (float(x) for x in punkt.split(","))
        vortage = max(0, (dt.date.today() - datum).days) + 1
        teile.append(modell(lat, lon, 2, vortage, stunden))
    txt = "\n\n".join(teile)
    (ziel / "uebersicht.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)
    print(f"\n-> {ziel}")


# ------------------------------------------------------------------ MeteoSchweiz-Prognose (Web-App)

MCH = "https://www.meteoschweiz.admin.ch/product/output"


def prognose(plz: str, datum: dt.date, stunden: list[int], region: str) -> None:
    """Textprognosen (Allgemeine Lage, Wetterbericht) und stündliche Ortsprognose der MeteoSchweiz.

    Quellen wie die Website: `versions.json` → `<produkt>/version__<v>/textproduct_de.xhtml`;
    Ortsprognose über den App-Endpoint `plzDetail` (PLZ sechsstellig, Interlaken = 380000) mit
    Wind/Böe als Median und q10–q90 sowie Richtung im 3-h-Raster.
    """
    ver = requests.get(f"{MCH}/versions.json", timeout=30).json()
    for k in ("generalsituation/text/de", f"weather-report/de/{region}"):
        t = requests.get(f"{MCH}/{k}/version__{ver[k]}/textproduct_de.xhtml", timeout=30).content.decode("utf-8")
        t = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<(br|/p|/h\d|/li)[^>]*>", "\n", t)))
        print(f"== {k} (Version {ver[k]})")
        zeilen = [z for z in re.sub(r"\n\s*\n+", "\n", t).strip().splitlines()]
        print("\n".join(dict.fromkeys(zeilen)), "\n")          # Allgemeine Lage steht im XHTML doppelt
    g = requests.get("https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail", params={"plz": plz},
                     headers={"User-Agent": "MeteoSwissApp-2.16-Android"}, timeout=30).json()["graph"]
    tz, s1, s3 = _tz(), g["start"], g["startLowResolution"]
    H = 3_600_000

    def at(arr, t0, step, t):
        i = (t - t0) // step
        return arr[i] if 0 <= i < len(arr) else None

    print(f"== Ortsprognose PLZ {plz}, {datum}  (Median, q10–q90; Richtung 3-h-Raster)")
    print("  Zeit  Richtung  Wind km/h       Böe km/h        Sonne min  Regen mm")
    for h in stunden:
        t = int(dt.datetime.combine(datum, dt.time(h), tz).timestamp() * 1000)
        t3 = t - ((t - s3) % (3 * H))
        r = at(g["windDirection3h"], s3, 3 * H, t3)
        w = [at(g[k], s1, H, t) for k in ("windSpeed1h", "windSpeed1hq10", "windSpeed1hq90")]
        b = [at(g[k], s1, H, t) for k in ("gustSpeed1h", "gustSpeed1hq10", "gustSpeed1hq90")]
        if w[0] is None:
            continue
        print(f"  {h:02d} h  {_richtung(r) if r is not None else '-':>6}  {w[0]:4.1f} ({w[1]:.0f}–{w[2]:.0f})"
              f"   {b[0]:4.1f} ({b[1]:.0f}–{b[2]:.0f})   {at(g['sunshine1h'], s1, H, t) or 0:5.0f}"
              f"   {at(g['precipitation1h'], s1, H, t) or 0:6.1f}")


# ------------------------------------------------------------------ Fahrplan

def fahrplan(von: str, nach: str, datum: str, zeit: str, n: int) -> None:
    r = requests.get("https://transport.opendata.ch/v1/connections",
                     params={"from": von, "to": nach, "date": datum, "time": zeit, "limit": n},
                     timeout=30).json()
    for c in r.get("connections", []):
        teile = []
        for s in c["sections"]:
            j = s.get("journey")
            if j:
                teile.append(f"{j['category']}{j['number']} {s['departure']['station']['name']} "
                             f"{s['departure']['departure'][11:16]}->{s['arrival']['arrival'][11:16]}")
            elif s.get("walk"):
                dauer = s["walk"].get("duration")
                teile.append(f"zu Fuss {int(dauer) // 60 if dauer else '?'} min")
        print(f"ab {c['from']['departure'][11:16]}  an {c['to']['arrival'][11:16]}  "
              f"({c['duration'][3:8]})  | " + " / ".join(teile))


# ------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("holfuy"); h.add_argument("ids", nargs="+"); h.add_argument("-n", type=int, default=8)
    s = sub.add_parser("smn"); s.add_argument("ids", nargs="+"); s.add_argument("--ab", type=int, default=6)
    b = sub.add_parser("bise"); b.add_argument("--ab", type=int, default=0)
    b.add_argument("--prognose", action="store_true", help="Index aus Modell-Bodendruck (heute+morgen)")
    b.add_argument("--modelle", default="meteoswiss_icon_ch1,meteoswiss_icon_ch2")
    w = sub.add_parser("webcam"); w.add_argument("slugs", nargs="+")
    w.add_argument("--verlauf", metavar="YYYY-MM-DD", help="stündlicher Verlauf dieses Tages")
    w.add_argument("--stunden", default="8-16", help="z. B. 8-16 (Default)")
    f = sub.add_parser("fahrplan"); f.add_argument("von"); f.add_argument("nach")
    f.add_argument("--datum", default=dt.date.today().isoformat()); f.add_argument("--zeit", default="08:00")
    f.add_argument("-n", type=int, default=6)
    v = sub.add_parser("verlauf"); v.add_argument("ids", nargs="+", help="winds.mobi-IDs")
    v.add_argument("--datum", default=dt.date.today().isoformat()); v.add_argument("--stunden", default="6-19")
    m = sub.add_parser("modell"); m.add_argument("lat", type=float); m.add_argument("lon", type=float)
    m.add_argument("--tage", type=int, default=2); m.add_argument("--vortage", type=int, default=1)
    m.add_argument("--stunden", default="8-18")
    pg = sub.add_parser("prognose", help="MeteoSchweiz: Textprognose + Ortsprognose")
    pg.add_argument("--plz", default="380000", help="sechsstellig, z. B. 380000 Interlaken")
    pg.add_argument("--datum", default=(dt.date.today() + dt.timedelta(days=1)).isoformat())
    pg.add_argument("--stunden", default="7-17"); pg.add_argument("--region", default="north")
    j = sub.add_parser("jetzt", help="Kurz-Briefing Lehn: Wind jetzt, Trend, Berg-/Talwind-Kipppunkt, Volte")
    j.add_argument("ids", nargs="*", default=["1850", "1808", "1829"])
    j.add_argument("--bis", metavar="HH:MM", help="nur Daten bis zu dieser Uhrzeit (Test/Rückblick)")
    j.add_argument("--keine-grafik", action="store_true", help="ohne PNG (Holfuy 6 h + ICON-CH1/CH2 ±6 h)")
    r = sub.add_parser("archiv"); r.add_argument("datum"); r.add_argument("name")
    r.add_argument("ids", nargs="+", help="winds.mobi-IDs")
    r.add_argument("--punkt", metavar="LAT,LON", help="zusätzlich Modell an diesem Punkt")
    r.add_argument("--stunden", default="6-19")
    a = ap.parse_args(argv)

    def _std(s: str) -> list[int]:
        lo, hi = (int(x) for x in s.split("-"))
        return list(range(lo, hi + 1))

    if a.cmd == "holfuy":
        holfuy(a.ids, a.n)
    elif a.cmd == "smn":
        smn(a.ids, a.ab)
    elif a.cmd == "bise":
        if a.prognose:
            bise_prognose(3, a.modelle.split(","))
        else:
            bise(a.ab)
    elif a.cmd == "webcam":
        lo, hi = (int(x) for x in a.stunden.split("-"))
        webcam(a.slugs, a.verlauf, list(range(lo, hi + 1)))
    elif a.cmd == "fahrplan":
        fahrplan(a.von, a.nach, a.datum, a.zeit, a.n)
    elif a.cmd == "verlauf":
        print(verlauf(a.ids, dt.date.fromisoformat(a.datum), _std(a.stunden)))
    elif a.cmd == "modell":
        print(modell(a.lat, a.lon, a.tage, a.vortage, _std(a.stunden)))
    elif a.cmd == "prognose":
        prognose(a.plz, dt.date.fromisoformat(a.datum), _std(a.stunden), a.region)
    elif a.cmd == "jetzt":
        jetzt(a.ids, a.bis, not a.keine_grafik)
    elif a.cmd == "archiv":
        archiv(dt.date.fromisoformat(a.datum), a.name, a.ids, a.punkt, _std(a.stunden))
    return 0


if __name__ == "__main__":
    sys.exit(main())
