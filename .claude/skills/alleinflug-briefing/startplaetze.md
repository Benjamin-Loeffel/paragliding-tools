# Startplatz-Briefings

Pro Gebiet: Gelände und Regeln (Quelle!), Messstationen, Webcams, ÖV, Erfahrungswerte.
Nur Belegtes eintragen; Lücken als **offen** markieren. Neue Gebiete nach demselben Muster ergänzen.

---

## Interlaken (Beatenberg-Hang → Lehn)

Quellen: SHV-Infotafel «Fluggebiet Interlaken» (Stand 3-2024,
`shv-fsvl.ch/fileadmin/files/redakteure/Allgemein/Sicherheit/SHVInfotafeln/Interlaken.pdf`);
Deltaclub Interlaken DCI (`deltaclub-interlaken.ch/startplatz-…`, `/landeplatz-lehn/`).

### Startplätze

| Startplatz | Höhe | Koord. | Ausrichtung | Zugang | Regeln / Gefahren |
|---|---|---|---|---|---|
| **Bergbo** (Tafel Nr. 2) | 1290 m (Tafel) / 1275 m (DCI) | 46.7003 / 7.8208 | SE (DCI), «alle» (Tafel) | Bus 101 bis Waldegg, ~15 min zu Fuss | Ideale Thermikstartzeit Vormittag bis früher Nachmittag (Tafel). DCI: «Bei stärkerem Talwind muss durch das Lee vom Hüenderhubel geflogen werden», «Turbulenzen!». Nur Gleitschirm. |
| **Luegibrüggli** (Nr. 6) | 1060 m | 46.6910 / 7.8104 | S–SSW (DCI) | Bus 101 bis Bhendenchehr, ~5 min | Ideale Startzeit ab Mittag (Tafel). **Bei Bergwind am Landeplatz Lehn im Lee → nicht starten** (Tafel). DCI: bei starkem Bergwind oder **Bise** Luegibrüggli meiden. |
| Amisbühl oben/unten (Nr. 3/4) | 1325 / 1310 m | 46.7025 / 7.8222 | — | Bus 101 bis Waldegg, ~20 min | Oben: Fr–So Vorrang Solo-Gleitschirm linke Startbahn. Hier steht Holfuy 1808. |
| Chalet, Hohwald, Niederhorn, Breitlauenen | — | siehe Tafel | — | — | noch nicht geflogen — Tafel lesen |

Für alle Plätze gilt laut Tafel: **starke Talwinde bei labilen NW-Lagen ab Mittag möglich.**

### Landeplätze
- **A Lehn 565 m** (46.6808 / 7.8236): **Rechtsvolte bei Talwind, Linksvolte bei Bergwind.**
  Turbulenzen bei starkem Talwind. **Keine tiefen Überflüge über Schiessstand und Schussbahn, keine
  Landung in der Schussbahn (Lebensgefahr).** Landetaxe für Nicht-DCI-Mitglieder CHF 2.– (Twint/Kasse).
  DCI: nur gelb markierte Fläche (orange Eckpunkte), umliegendes Ackerland nicht betreten.
- **Zielpunkt Lehn** = Mitte des gemähten **Zielkreises r = 15 m** (im Orthofoto sichtbar; Punkt von
  Benjamin auf map.geo.admin.ch gesetzt): LV95 2'629'453.66 / 1'170'022.09,
  565.1 m (46.680774 / 7.823607; swissALTI3D 564.6–565.0 an den Landepunkten). Landeanalyse:
  `alleinflüge/landeanalyse.py analyse <igc> --ziel lehn --wind <archiv>/roh/holfuy-1850_15min.json`
  (ältere Tage: `meteoswiss-INT_10min.csv`, aber INT ist für Lehn nicht repräsentativ).
- B Höhematte 568 m: Talwind → Linksvolte, Bergwind → Rechtsvolte; starke Turbulenzen bei labiler Luft
  oder starkem Talwind; sofort räumen, kein Groundhandling.
- C Flugplatz 575 m: **nur Notlandeplatz**, im Sperrgebiet des Heliports.

### Praxisprüfung (SHV-Weisung Pilot GS, Juli 2025, Ziff. 5.7)
Benjamins Prüfung: **6.11.2026 in Lehn**. Was für die Landeeinteilung zählt:
- Der Landeanflug beginnt **luvseitig** des Landepunkts, im vorgegebenen Sektor und mit der
  vorgegebenen Voltenrichtung. Danach folgen Gegenanflug, Kurve, Queranflug, Kurve und Endanflug.
- Den Queranflug darf man bei mangelnder Höhe weglassen. Bei Überhöhe darf man ihn durch Kurven
  von **höchstens 200°** wiederholen.
- Im Endanflug sind S-Kurven bis **90° von der Achse** erlaubt. Die **letzten 5 s** müssen
  geradeaus sein.
- Landefläche: ein **Kreis von 34 m Ø**, ein Rechteck 20 × 45 m oder 15 × 60 m. Vorher den Boden
  nicht berühren, nur mit den Füssen landen. Liegt die Landung mehr als 120 m vom Zentrum weg, ist
  die Prüfung nicht bestanden.
- Am Start wird der Schirm im **zugelassenen Gewichtsbereich** geprüft (Ziff. 5.2).

Die Regeln prüft `landeanalyse.py analyse`. Die Eckpunkt-Höhen je Wind liefert
`landeanalyse.py plan`, als Volten auf der swisstopo-Karte `landeanalyse.py volten` (Talwind:
`--kurs 250 --seite rechts`, Bergwind: `--kurs 75 --seite links`).

**Höhenmesser (XC Tracer Maxx III, `landeanalyse.py hoehen`, 7 Flüge):** Laut Handbuch (R06,
18.10.2026, «Screen Options → Altitude») zeigt das Gerät die **GPS-Höhe (MSL)** und/oder die **Höhe über
Grund (AGL)** aus dem vorinstallierten Geländemodell (Auflösung nicht angegeben). Eine QNH-/Baro-Höhe
zum Einstellen gibt es nicht; der Drucksensor dient dem Vario. Im IGC: GPS = `HFALG:GEO` (Meereshöhe),
Baro = ISA-Druckhöhe (`HFALP:ISA`).
- **GPS am Boden in Lehn** +0.4…+5 m über swissALTI3D (Gerät ~1 m über Boden), am Start +1…+10 m.
- **GPS in der Volte** (ab Gegenanflug) gegen Baro (am Boden genullt): Mittel −1…+3 m, an den
  Eckpunkten meist ±1 m, höchstens +6 m. Die GPS-Anzeige taugt also für die Volten-Höhen.
- **Lehn = 565 m:** Volten-Höhen + 565 m ablesen (Gegenanflug ~700–720 m, Queranflug ~655–660 m,
  Endanflug 615 m). AGL-Anzeige vorher am Boden in Lehn prüfen (soll 0–1 m zeigen).
- Nur fürs IGC: Baro mit QNH Interlaken liegt in Lehn immer 17–19 m zu tief (Sensor-Offset), die
  Höhendifferenz Start → Lehn je nach Temperatur −10…+17 m daneben.

### Luftraum
TMA HX Meiringen — Status per Tonband **0800 496 347** (Updates 07:30, 13:15, 17:05). Violette Zonen
(Heliports Interlaken/Gsteigwiler): Flugverbot; Abstand zu den markierten Heli-Routen.
Auswärtige Flugschulen: Online-Registrierung beim DCI.

### Messstationen

| Station | Höhe | Wozu | Abruf |
|---|---|---|---|
| **Holfuy 1850 Lehn** | 560 m | Wind am Landeplatz: Berg-/Talwind, Volte, Lee-Regel Luegibrüggli | `lagecheck.py holfuy 1850` |
| **Holfuy 1808 Amisbühl** | 1315 m | **≈ Bergbo** (250 m daneben): Startplatz in der Wolke? (rF) | `holfuy 1808` |
| **Holfuy 1829 Hohwald** | 1600 m | über/unter Nebelobergrenze? | `holfuy 1829` |
| MeteoSchweiz INT Interlaken | 578 m | Sonne/Strahlung (Hochnebel?) | `lagecheck.py smn INT` |
| MeteoSchweiz THU / BRZ | 570 / 567 m | Windmuster an den Seeenden (Thun = Bise-Kette, Brienz = Bergwind Brienzersee) | `smn THU BRZ` |
| Holfuy 1804 Höhematte | 630 m | S-Wind = Bergwind aus dem Lütschinental (wie INT) | `holfuy 1804` |
| windline 4109 Niederhorn | 1960 m | Wind über dem Nebeldeckel | winds.mobi |

**INT liegt in Matten am Ausgang des Lütschinentals.** Ihr Morgenwind (S) ist der Bergwind aus dem
Lütschinental und für Lehn **nicht repräsentativ** — für Lehn immer Holfuy 1850.

**Lehn-Wind lesen:** Der NNE in Lehn ist meist **lokaler Bergwind** (aus Richtung Habkern/Lombach):
nachts und morgens 10–15 km/h (Böen ~20), bricht gegen **~10 h** zusammen, kommt gegen 18 h zurück
(30./31.10. gemessen). Bise erkennt man nicht an Lehn allein, sondern an der Kette unten.

**Bise-Kette** (winds.mobi-IDs; erreicht die Bise das Bödeli?):
Bern/Zollikofen `meteoswiss-BER` (Koppigen `meteoswiss-KOP`, Bantiger `meteoswiss-BAN`) →
Thun `meteoswiss-THU`, Thun Hafeneinfahrt `pioupiou-1723`, Tschingel ob Gunten `pioupiou-2029` →
Lehn `holfuy-1850`. Solange Thun/Gunten still bleiben oder SE zeigen (Abfluss den See hinunter), kommt
die Bise **nicht** den Thunersee herauf (31.10.: Bern NE 15/23, Thun ESE 4, Gunten still). Dazu
`lagecheck.py bise` (Index Güttingen − Genf).

**Wo entscheiden:** an der Haltestelle **Interlaken West vor dem Bus 101** — mit Holfuy Lehn/Amisbühl auf
dem Handy. Von Bhendenchehr (Luegibrüggli) zum Bergbo ist es zu weit; lieber einen Bus/Zug später.

### Webcams (Roundshot, mit Tagesarchiv)
- `interlaken-harderkulm` — Harder Kulm **1322 m ≈ Bergbo-Höhe**. Blick nach W zeigt den Beatenberg-Hang
  mit Bergbo und Luegibrüggli: in/unter der Wolke?
- `schynige-platte` — 1967 m, von oben auf das Nebelmeer (Bödeli/Thunersee vs. Lütschinental).
- Weitere (nur Livebild): interlaken.swiss «Webcam Beatenberg Waldegg», «Webcam Niederhorn».

### ÖV (Haltestellen-IDs für `lagecheck.py fahrplan`)

| Haltestelle | ID | Bezug |
|---|---|---|
| Beatenberg, Waldegg | 8507775 | Bergbo (~15 min), Amisbühl (~20 min) |
| Beatenberg, Bhendenchehr | 8504110 | Luegibrüggli (~5 min) |
| Unterseen, Schiessstand Lehn | 8576887 | ~170 m vom Landeplatz Lehn; Bus 21 |
| Unterseen, Ruchenbühl | 8579807 | Bus 101, ab Lehn 19 min zu Fuss |
| Interlaken West, Bahnhof | — | Umsteigen Zug ↔ Bus 101 |

Bus 101 ab Interlaken West → Ruchenbühl +6 → Bhendenchehr +12 → Waldegg +18 min.
**Rückweg Lehn → Startplatz:** zu Fuss zum Ruchenbühl (19 min) oder Bus 21 Lehn → Interlaken West
(5 min), beide auf denselben Bus 101. Takt prüfen: Samstag im Winterhalbjahr fährt der 101 zwischen
~12 und 15 h nur stündlich.
**Runden:** Luegibrüggli passt in den Stundentakt (an :17, Start ~:30, Landung ~:36, ab Lehn :52).
Bergbo (an :23, Start ~:45, Landung ~:55) verpasst über Mittag den Anschluss → alle 2 h; mit
Halbstundentakt ~85–90 min (24.09.: Starts 09:50 / 11:15 / 12:46).

### Erfahrungswerte
- **24.09.2026** (erster Tag, 3 Flüge Bergbo → Lehn): Flug 1+2 Bergwind 10–12 km/h; Flug 3 Talwind
  15–20 km/h → nur 180 m AGL über Lehn, souverän gemeistert. **Entscheid: im neuen Gebiet bewusst
  konservativ, bei Talwind nicht mehr fliegen.**
  Landeanalyse: Flug 1 Linksvolte, Endanflug 67° (Bergwind, 9 km/h auf Volten-Höhe) ab 99 m bei
  289 m, 10 m zu kurz. Flug 2 fast windstill, Endanflug 99° mit S-Kurven ab 52 m, 10 m zu kurz (letzte
  5 s nicht ganz gerade, 26°). Flug 3 Talwind, Endanflug 250° ab 50 m bei 118 m, GS nur 11 km/h
  (Gegenwind ~15 km/h, aus Gegen-/End-Grundgeschwindigkeit), 14 m zu kurz.
- **25.09.2026** (2 Flüge → Lehn): Flug 1 Bergwind 5 km/h, Endanflug 83° ab 54 m bei 260 m, 7 m zu kurz.
  Flug 2 Talwind 4 km/h (W, INT zeigte gleichzeitig E 8 → INT nicht für Lehn), Endanflug 252° ab 32 m
  bei 123 m, 6 m zu weit. Alle Prüfregeln erfüllt.
- **30.10.2026** (Hochnebel; Bise im Mittelland, in Lehn Bergwind): Amisbühl ganztags 100 % rF, Harder bis 14 h in der Wolke, ab
  ~15 h knapp unter der Basis; Nebel **hob sich nur**, löste sich nicht auf. Lehn bis 9 h NE 10–14 km/h
  (Böen bis 26), danach E/SE 1–6, nie Talwind. Bise-Index nur +1.7–2.4 hPa; Genf hatte
  das Bise-Maximum am Nachmittag (NE 20, Böen 36), genau als Lehn still war → Lehn = Bergwind. **ICON-CH1 lag falsch** (Lehn WSW, Nebel ab Mittag weg).
- **31.10.2026** (Stratus Basis 800–1200 m laut Segelflugprognose): Luegibrüggli nebelfrei (Sicht von
  unten), Bergbo/Amisbühl in der Wolke, Lehn NNE 15 km/h, Böen 22 (Bergwind) → Luegibrüggli im Lee. Bise-Index +3.1 hPa und
  steigend, Bern NE 15/23, aber Thun/Gunten still; Lehn begann ab 08:45 abzuflauen.
  Startplatzwahl daher an die Lage gekoppelt.
  **Geflogen** wurden zwei Flüge, beide mit Rechtsvolte. In Lehn drehte der Wind ab ~11 h auf WSW
  (Talwind) 6–9 km/h, Böen 13–15.
  - *Flug 1:* Bergbo 11:47, Landung 11:58, **~3 m vor dem Kreis** (Benjamin: ~2 m; IGC: Bodennähe
    bei 28 m vom Punkt, Fusskontakt nach ~3 s Ausschweben bei ~18 m). Endanflug ab 40 m AGL bei
    135 m vor dem Ziel. Im Queranflug zwei S-Kurven zum Höhenabbau.
  - *Flug 2:* Luegibrüggli 13:32, Landung 13:38, **Punktlandung** (Benjamin: ~1 m; IGC: nächster
    Punkt 2 m). Endanflug ab 49 m bei 153 m.
  - *Wind auf Volten-Höhe* (aus den Kreisen im Positionsraum, `landeanalyse.py`): SW 213–221°,
    9 km/h; am Mast Lehn 7–8 km/h aus WSW. Höhenwind ≈ Mast × 1.1–1.4.
  - *Prüfregeln:* Flug 1 hatte im Queranflug eine Drehung von **219° am Stück**. Die Weisung erlaubt
    höchstens 200°, das wäre an der Prüfung ein Abzug. Flug 2 hat alle Regeln erfüllt.
  - Das Baro löst nur ~1 m auf: Der Fusskontakt lag 1–3 s nach «≤ 1 m AGL», also 5–10 m weiter.
    Darum zeigt `landeanalyse.py` ein Touchdown-Fenster.
  - Gleitzahl über Grund im Endanflug 2.8–3.1, mit Bremse, Sinken 1.7–1.85 m/s (im September nur
    1.24–1.48 m/s bei gleicher Fahrt ~25 km/h).
- **Alle 7 Landungen (24.09.–31.10.):** 6 von 7 lagen 6–28 m zu kurz (Median 10 m). Der Landeplan
  rechnet darum mit dem hohen Sinken (1.8 m/s) und lässt Überhöhe mit S-Kurven abbauen.
  - Archiv: `alleinflüge/archiv/2026-10-31_interlaken/`.

---

## Frutigen (Mäggisseren → Frutigen)

Quellen: eigene IGC-Tracks (`source/igc/`), Flugbuch, Briefing mit Benjamin (14.08.2026).

| Startplatz | Höhe | Koord. | Hinweise |
|---|---|---|---|
| **Mäggisseren / Mäggisserenegg** | ~1730 m | 46.5880 / 7.6096 (Median der eigenen Starts) | Hausstartplatz, ~2.8 km W von Frutigen. Weiter über **Zismas** (Schreibweise bestätigt) bei tragender Thermik an die Niesenkette. |

- Landeplätze: **Frutigen Hangar** (Hauptlandeplatz), **Oberfeld**, **Chriesbaum**.
- **Talwind beim Überqueren von Frutigen** sehr gut berücksichtigen, genügend Vorhaltewinkel; im
  Queranflug nicht vom Landeplatz weggewindet werden.
- Auf der Auffahrt den **Loowald** beobachten: genügend Talwind zum Soaren? Klappt das Soaring nicht,
  folgt eine Aussenlandung im Oberfeld (vermeiden).
- **Luftraum Reichenbach** beachten.
- Messstationen: MeteoSchweiz FRU Frutigen 756 m (`smn FRU`). Holfuy/Webcams: **offen**.
- Erfahrungswerte: Hitzegewitterlage Juli/August 2026 — späteste Landezeit nach der Talwind-Zunahme
  setzen (14.08.: 14:30, Böenkarte 25–35 km/h ab ~14:45).

---

## Adelboden — Hahnenmoospass (Soaring/Spielen bei Bise)

Quellen: Benjamin (Konzept, typische Route als GPX von map.geo.admin.ch, 31.10.2026), swisstopo
(Namen/Höhen via api3.geo.admin.ch), winds.mobi. **Keine SHV-Infotafel** (Adelboden/Lenk → 404).

**Idee:** Die Bise (NE) wird durch das Frutigtal und das Engstligental nach Adelboden hinauf
kanalisiert und über den Hahnenmoospass (Sattel zwischen Engstligental und Lenk/Simmental)
**verstärkt** → Soaren/Spielen an den NE-exponierten Hängen beim Pass.

| Ort | Höhe | Koord. | Hinweise |
|---|---|---|---|
| **Hahnenmoospass** (Start) | 1959 m (DTM am Track-Anfang) | 46.4543 / 7.4944 | Berghotel und Bergstation Bühlberg daneben. Typische Route: ENE hinunter Richtung Geils |
| Ende typische Route (Landung) | ~1740 m | 46.4573 / 7.5102 | ~250 m vor **Geils** (Talstation Geils–Hahnenmoos, Bus). Track: 1.6 km, 220 m Abstieg |
| Metschstand | 2100 m | 46.4445 / 7.4951 | Grat ~1 km S des Passes, Holfuy 484 |

- Landeplatz, Volten und Hindernisse (Bahnseile Geils–Hahnenmoos, Bühlberg, Luegli): **offen**.
- Lee: *Annahme, nicht bestätigt:* Bei Bise liegt die Lenker Seite (SW) im Lee des Passes.
  **offen:** Erfahrungen vor Ort.

### Messstationen (winds.mobi-IDs)

| Station | Höhe | Lage | Wozu |
|---|---|---|---|
| **`holfuy-484` Metschstand** | 2100 m | Grat 1.2 km S des Passes | **Leitstation**: Bise am Pass (Benjamin) |
| `slf-ADE3` Lavey-Sattligrat | 2355 m | 2.4 km N | Gegenstück N des Passes |
| `pgsonda-seewlen` Seewle | 1971 m | 2.4 km NW, Lenker Seite | SW = Lenker Talwind/Thermik gegen die Bise |
| `slf-FAE1` Albristhorn | 2761 m | 4.8 km N | Höhenwind über dem Pass |
| `meteoswiss-ABO` Adelboden | 1357 m | Engstligental | Kanal: kommt NE das Tal herauf? |
| `meteoswiss-FRU` Frutigen, `pioupiou-1660` Helgisberg | 766 / 1010 m | Frutigtal | Kette Thunersee → Engstligental |
| `meteoswiss-BOL` Boltigen | 830 m | Simmental | Vergleich: Bise im Nachbartal |
| `holfuy-1340` Tschenten, `slf-ADE2` Engstligenalp | 2031 / 2304 m | Adelboden | Umgebung |
| `pgsonda-landemetsch` Landeplatz Metsch | 1072 m | Lenk | Landeplatz der Lenker Seite |

**Bise-Kette:** Bantiger `meteoswiss-BAN` / Bern `meteoswiss-BER` → Thun `meteoswiss-THU` →
Frutigen `meteoswiss-FRU` → Adelboden `meteoswiss-ABO` → Metschstand `holfuy-484`. Dazu
`lagecheck.py bise` bzw. `bise --prognose`.

Kompletter Satz für `verlauf`/`archiv`:
`holfuy-484 slf-ADE3 pgsonda-seewlen slf-FAE1 slf-FAE2 holfuy-1340 meteoswiss-ABO slf-ADE2
pgsonda-landemetsch holfuy-1059 slf-LAU1 slf-LAU2 meteoswiss-FRU pioupiou-1660 meteoswiss-BOL
gxaircom-08CA48 meteoswiss-THU meteoswiss-BER meteoswiss-BAN meteoswiss-GVE meteoswiss-KLO
meteoswiss-GUT --punkt 46.4545,7.4945`

### Webcams
**offen.** Es gibt kein Roundshot-Panorama gefunden. snow-online.com führt eine Webcam
«Hahnenmoos» (1940 m) mit 2-h-Archiv; Qualität nicht geprüft.

### ÖV
Haltestellen: Adelboden, Geils `8576332`; Bahn Geils–Hahnenmoos `8530314` → `8530315`.
**Ende Oktober leerer Fahrplan** (31.10./01.11. keine Bus- und keine Bahnkurse). Zwischensaison, also
Anreise und Aufstieg selbst planen. **offen:** Wie ging es am 30.10.?

### Erfahrungswerte
- **30.10.2026 — zu wenig Wind am Pass** (Benjamin vor Ort). Archiv:
  `alleinflüge/archiv/2026-10-30_hahnenmoos/`.
  - *Bise schwach:* Index morgens +1.7…+2.0 hPa, **ab 11 h nur +0.7…+1.1**. Im Mittelland trotzdem
    Bise mit Maximum am Nachmittag (Bantiger ENE 18–28, Genf NE 17–18 km/h).
  - *Metschstand:* durchgehend NE, aber nur 6–11 km/h morgens, **11–15 h nur 3–7 km/h**
    (Böen 9–15) und ab 16 h wieder 10–13.
  - *Lavey-Sattligrat:* morgens E 8–14, 12–15 h still bzw. **SW 4–5**. Seewle 11–15 h **SW 4–5**.
    Über Mittag hielt also die Lenker Seite (SW) gegen die schwache Bise.
  - *Albristhorn:* NNE 13–17 morgens, bis 14 h auf 4 km/h gefallen.
  - *Engstligental:* Adelboden 11–16 h ENE 7–10, Frutigen 13–15 h NE 9–13. Das Tal zog, am Pass kam
    wenig an.
  - *Simmental:* Boltigen 14–16 h NE 18–19 km/h, die Bise lief also eher das Simmental hinauf.
  - *Modell:* ICON-CH1 10 m am Pass mittags ENE 10–12 (Böen 24–31), also etwa **Faktor 2 zu hoch**.
    Den Index traf es (+1.5).
- **31.10.2026** (Vergleich, ohne Flug): Index +3.0 hPa → Metschstand 09–10 h **NE 13–14 km/h**
  (Böen 17–19), Lavey-Sattligrat NE 14, Albristhorn NE 16–21.
- **Arbeitshypothese** (am Abend des 31.10. mit dem Nachmittag prüfen): Am Pass braucht es einen
  Index von **≥ ~+3 hPa auch über Mittag**. Bei ~+1 hPa setzt sich über Mittag die lokale SW-Zirkulation
  der Lenker Seite durch.

---

## Weitere geflogene Startplätze — noch kein Briefing

Tschentenalp/Tschenten, Trutten, Grimer, Niesen (Koordinaten in `src/thermalmodel/config.py`),
Allmenalp Kandersteg (~46.4947 / 7.6501, eigene Tracks), Kuonisbergli, Engstligenalp.
Bei Bedarf nach dem Muster oben anlegen (Tafel, Club, Stationen, Webcams, ÖV).
