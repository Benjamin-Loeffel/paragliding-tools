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
    webcam     Roundshot-Panoramen: aktuelles Bild oder stündlicher Verlauf eines Tages
               als Kontaktbogen (JPG) — zeigt, wann/ob sich Nebel hebt.
    fahrplan   Verbindungen (transport.opendata.ch), z. B. Rückweg Landeplatz -> Startplatz.

Beispiele:
    python alleinflüge/lagecheck.py holfuy 1850 1808 1829
    python alleinflüge/lagecheck.py smn INT THU BRZ
    python alleinflüge/lagecheck.py bise --ab 6
    python alleinflüge/lagecheck.py webcam interlaken-harderkulm schynige-platte
    python alleinflüge/lagecheck.py webcam interlaken-harderkulm --verlauf 2026-10-30
    python alleinflüge/lagecheck.py fahrplan 8576887 8504110 --datum 2026-10-31 --zeit 11:00

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
    w = sub.add_parser("webcam"); w.add_argument("slugs", nargs="+")
    w.add_argument("--verlauf", metavar="YYYY-MM-DD", help="stündlicher Verlauf dieses Tages")
    w.add_argument("--stunden", default="8-16", help="z. B. 8-16 (Default)")
    f = sub.add_parser("fahrplan"); f.add_argument("von"); f.add_argument("nach")
    f.add_argument("--datum", default=dt.date.today().isoformat()); f.add_argument("--zeit", default="08:00")
    f.add_argument("-n", type=int, default=6)
    a = ap.parse_args(argv)

    if a.cmd == "holfuy":
        holfuy(a.ids, a.n)
    elif a.cmd == "smn":
        smn(a.ids, a.ab)
    elif a.cmd == "bise":
        bise(a.ab)
    elif a.cmd == "webcam":
        lo, hi = (int(x) for x in a.stunden.split("-"))
        webcam(a.slugs, a.verlauf, list(range(lo, hi + 1)))
    elif a.cmd == "fahrplan":
        fahrplan(a.von, a.nach, a.datum, a.zeit, a.n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
