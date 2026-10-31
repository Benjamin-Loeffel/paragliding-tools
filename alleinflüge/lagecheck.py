#!/usr/bin/env python
"""Lage-Check für Alleinflug-Briefings: Messwerte, Webcams, Fahrplan — reproduzierbar statt ad hoc.

Holt, was sich beim Interlaken-Briefing bewährt hat (Quellen siehe
`.claude/skills/alleinflug-briefing/datenquellen.md`):

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
        zeiten = tab.get("Time", [])
        print(f"== Holfuy {sid}  {html.unescape(name.group(1)).replace('Holfuy: ', '').split(',')[0].strip() if name else ''}")
        print("   Zeit   Richtung   Mittel/Böe     rF      T")
        for k in range(max(0, len(zeiten) - n), len(zeiten)):
            print(f"  {zeiten[k]:>5}  {tab['Direction Deg.'][k]:>9}  {tab['Speed'][k]:>3}/{tab['Gust (km/h)'][k]:>3} km/h"
                  f"  {tab['Humidity (%)'][k]:>5} %  {tab[tk][k] if tk else '-':>5} °C")


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
    elif a.cmd == "archiv":
        archiv(dt.date.fromisoformat(a.datum), a.name, a.ids, a.punkt, _std(a.stunden))
    return 0


if __name__ == "__main__":
    sys.exit(main())
