# Datenquellen — wo, wie, worauf achten

Rangfolge für den Entscheid: **Messung > Webcam > offizielle Textprognose > Modell.**
Jede Angabe im Briefing mit Quelle und Uhrzeit.

## MeteoSchweiz-Textprognosen (Primärquelle Wetter)
Kommen als **Screenshots aus der MeteoSchweiz-App** von Benjamin (kein stabiler öffentlicher Endpoint).
- **Allgemeine Lage**, **Wetterbericht** (Abschnitte pro Tag; Wind «in den Bergen», Nullgrad).
- **Gleitschirmprognose:** Abschnitt pro Tag mit eigener Ausgabezeit. Die für «morgen» kann zwei Tage
  alt sein (Ausgabe 00:47).
- **Segelflugprognose:** gilt für den **Ausgabetag**. Wolken (Menge/Basis/Top), Windtabelle 14 h nach
  Höhe und Region, Thermik, **Inversion**, QNH. Für morgen nur **«Aussichten»** verwenden. Ausgabe
  05:30; Saison März–Oktober.
- **Karten** (Wind auf Höhe/AGL, Böen, Niederschlag, Wolken; Modell ICON-CH1): Uhrzeit des Reglers
  ablesen und mitschreiben.

## Holfuy-Stationen (Wind am Platz, Nebel über rF)
- Seite `https://holfuy.com/en/weather/<id>` — keine freie API; `lagecheck.py holfuy <id>` parst die
  erste Tabelle (15-min-Werte des Tages: Richtung, Mittel/Böe km/h, rF, Temperatur). Die zweite Tabelle
  sind Stundenwerte ab gestern 17 h.
- **rF 100 % über Stunden + flache Temperatur** = Station in der Wolke. Darüber liegende Station trocken
  und wärmer = Inversion/Nebelobergrenze dazwischen.
- Updates alle 15 min; Seite kann bis zu ~15 min hinterherhinken.

## MeteoSchweiz SMN (offene Daten, 10 min)
- `https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/<abk>/ogd-smn_<abk>_t_now.csv` (aktueller Tag),
  Stationsliste `…/ogd-smn_meta_stations.csv`. Zeitstempel **UTC**.
- Spalten: `dkl010z0` Richtung, `fu3010z0` Mittel km/h, `fu3010z1` Böe km/h, `sre000z0` Sonne
  min/10 min, `gre000z0` Globalstrahlung W/m², `tre200s0` T, `ure200s0` rF.
- Hochnebel-Test: Sonne 0 min + Mittags-Strahlung weit unter Klarhimmel (Ende Oktober ~400 W/m²).
- Standort prüfen: eine Station am Talausgang misst lokale Talwinde (INT/Lütschinental).

## winds.mobi (alle Windstationen auf einer Karte, mit API)
- Sammelt MeteoSchweiz, Holfuy, Pioupiou, Windline, SLF, METAR u. a. Karte: `winds.mobi/map/<id>`.
- API: `https://winds.mobi/api/2.3/stations/?near-lat=..&near-lon=..&near-distance=<m>&limit=200`
  (letzte Messung je Station: `w-dir`, `w-avg`, `w-max` km/h, `hum`, `pres.qff`, Zeit `_id` = Unix),
  Einzelstation `…/stations/<id>/`, Verlauf `…/stations/<id>/historic/?duration=<s>`.
- Ideal für **Ketten**: erreicht ein grossräumiger Wind (Bise) das Gebiet, oder ist der Wind am
  Landeplatz lokal? Stationen vom Mittelland bis zum Landeplatz nebeneinander lesen.

## Bise-Indikatoren
- **Druckdifferenz Nordost − Genf** (Güttingen oder Kloten minus Genf, QFF): Bise, sobald der Druck
  im Nordosten höher ist; Faustregel ab ~2 hPa mit NE-Wind (Meteomatics: Genf − Konstanz < −2 hPa);
  ~8–9 hPa = aussergewöhnlicher Bisensturm (MeteoSchweiz-Blog Feb. 2023). `lagecheck.py bise`.
- **Tagesgang** (SRF Meteo): Bise nachmittags am stärksten, nachts schwächer; Böen bis ~2–2.5× Mittel.
- Je stärker die Bise, desto höher meist die Hochnebel-Obergrenze (SRF).
- Abgrenzung zum Bergwind: siehe SKILL.md («Bergwind oder Bise?»).
- Quellen: meteoschweiz.admin.ch Blog «Bisensturm» (2023/02), srf.ch/meteo «Tagesgang der Bise»,
  meteomatics.com «wind phenomena».

## Webcams (Roundshot)
- Struktur: `https://jungfrau.roundshot.com/<slug>/structure.json` → Liste der Panoramen des Tages
  (alle 10 min) mit URLs in mehreren Auflösungen (`quarter` ≈ 2971×512 reicht).
- Archiv: `https://storageN.roundshot.com/<kamera-id>/<YYYY-MM-DD>/<HH-MM-SS>/<…>_quarter.jpg`
  (`lagecheck.py webcam <slug> --verlauf <datum>` baut daraus einen stündlichen Kontaktbogen).
- Slug einer Kamera findet man im Quelltext der interlaken.swiss-Webcamseite (`WebcamVideoStreamUrl`).
- Lesen: Kamera **auf Startplatzhöhe** (in/unter der Wolke?) + Kamera **von oben** (Nebelmeer offen?).
  «Sicht nach unten unter geschlossener Decke» = Nebel gehoben, **nicht** aufgelöst.

## ÖV-Fahrplan
- `https://transport.opendata.ch/v1/connections?from=<id|name>&to=<id|name>&date=&time=&limit=`,
  Haltestellensuche `…/v1/locations?query=…&type=station`, Abfahrtstafel `…/v1/stationboard?id=…`.
- Die Auskunft schlägt auch Fusswege vor (z. B. Lehn → Ruchenbühl). Vergangene Tage liefert sie nicht.

## Gelände und Regeln
- SHV-Infotafeln: `https://www.shv-fsvl.ch/fileadmin/files/redakteure/Allgemein/Sicherheit/SHVInfotafeln/<Gebiet>.pdf`
  (Text mit pdfplumber extrahieren — nicht aus dem Bild abschreiben).
- Club-Seiten pro Start-/Landeplatz (Ausrichtung, Lee-Hinweise, Volten), z. B. deltaclub-interlaken.ch.
- Flugbuch-Export (xlsx) für Erfahrungszahlen; eigene IGC-Tracks für Startkoordinaten und Rundenzeiten.

## Modell (nur ergänzend)
- Open-Meteo: `api.open-meteo.com/v1/forecast?...&models=meteoswiss_icon_ch1` (Punktwerte 10 m, Böen,
  Wolken, Strahlung, `past_days=1` für den Quervergleich) bzw. `models=icon_d2` (Druckflächen-Wind
  850/700/600 hPa — ICON-CH1 liefert diese bei Open-Meteo nicht).
- Vor Verwendung **gegen die Messung von heute prüfen**. In Hochnebel-/Bise-Lagen lag ICON-CH1 klar
  daneben (30.10.: Lehn WSW statt NE, Nebel zu früh aufgelöst).
