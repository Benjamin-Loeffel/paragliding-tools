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
- B Höhematte 568 m: Talwind → Linksvolte, Bergwind → Rechtsvolte; starke Turbulenzen bei labiler Luft
  oder starkem Talwind; sofort räumen, kein Groundhandling.
- C Flugplatz 575 m: **nur Notlandeplatz**, im Sperrgebiet des Heliports.

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
- **30.10.2026** (Hochnebel; Bise im Mittelland, in Lehn Bergwind): Amisbühl ganztags 100 % rF, Harder bis 14 h in der Wolke, ab
  ~15 h knapp unter der Basis; Nebel **hob sich nur**, löste sich nicht auf. Lehn bis 9 h NE 10–14 km/h
  (Böen bis 26), danach E/SE 1–6, nie Talwind. Bise-Index nur +1.7–2.4 hPa; Genf hatte
  das Bise-Maximum am Nachmittag (NE 20, Böen 36), genau als Lehn still war → Lehn = Bergwind. **ICON-CH1 lag falsch** (Lehn WSW, Nebel ab Mittag weg).
- **31.10.2026** (Stratus Basis 800–1200 m laut Segelflugprognose): Luegibrüggli nebelfrei (Sicht von
  unten), Bergbo/Amisbühl in der Wolke, Lehn NNE 15 km/h, Böen 22 (Bergwind) → Luegibrüggli im Lee. Bise-Index +3.1 hPa und
  steigend, Bern NE 15/23, aber Thun/Gunten still; Lehn begann ab 08:45 abzuflauen.
  Startplatzwahl daher an die Lage gekoppelt.

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

## Weitere geflogene Startplätze — noch kein Briefing

Tschentenalp/Tschenten, Trutten, Grimer, Niesen (Koordinaten in `src/thermalmodel/config.py`),
Allmenalp Kandersteg (~46.4947 / 7.6501, eigene Tracks), Kuonisbergli, Engstligenalp.
Bei Bedarf nach dem Muster oben anlegen (Tafel, Club, Stationen, Webcams, ÖV).
