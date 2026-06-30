# Gleitschirm-Geländeabstand-Analyse

Berechnet für **jeden Punkt eines IGC-Flugtracks den minimalen 3D-Abstand zum Gelände**
auf Basis der höchstaufgelösten swisstopo-Höhenmodelle und findet so **kritische
Flugmomente mit wenig Hangabstand**. Berücksichtigt **Wald/Bewuchs und Gebäude**
(Abstand zur Baumkrone, nicht nur zum nackten Boden), schätzt die **GPS-bedingte
Unsicherheit** des Abstands (Monte Carlo) und wertet die **Verteilung über die Flugzeit**
sowie die **Risiko-Entwicklung über mehrere Flüge** aus.

Funktioniert für jeden Flug im swisstopo-Abdeckungsgebiet (Schweiz); die Beispieltracks
liegen im Berner Oberland.

---

## Datenquellen (swisstopo, frei)

- **swissALTI3D** – Geländemodell (DTM, nackter Boden), 0.5 m –
  <https://www.swisstopo.admin.ch/de/hoehenmodell-swissalti3d>
- **swissSURFACE3D Raster** – Oberflächenmodell (DSM, inkl. Vegetation & Gebäude), 0.5 m –
  <https://www.swisstopo.admin.ch/de/hoehenmodell-swisssurface3d-raster>

Kacheln werden automatisch passend zum Flug über die **STAC-API** geladen (nur der
Track-Umkreis), unter `cache/` zwischengespeichert und über Flüge derselben Region
wiederverwendet. Pro Kachel wird der **neueste Jahrgang** genommen (z. B. swissALTI3D 2025
statt 2019). Ein manueller Download ist **nicht** nötig.

## Installation (Windows, Python 3.11+)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
```

Kein separates GDAL/PROJ nötig – `rasterio` und `pyproj` bringen die Binärbibliotheken
als Wheel mit. (`kaleido` ist nur für statische PNG-Exports nötig und nicht erforderlich.)

## Nutzung

```powershell
# Einzelner Flug (mitgelieferter Beispieltrack)
.venv\Scripts\python.exe analyze.py examples\data\igc\2026-06-25_66km.igc

# Alle Flüge in einem Ordner (Saison-Auswertung)
.venv\Scripts\python.exe analyze.py examples\data\igc

# Schneller ohne Monte-Carlo-Band
.venv\Scripts\python.exe analyze.py examples\data\igc --no-uncertainty
```

### Wichtige Optionen

| Option | Wirkung (Default) |
|---|---|
| `--resolution {0.5\|2}` | Rasterauflösung (0.5 m; DSM bleibt immer 0.5 m) |
| `--r-cap <m>` | Max. 3D-Suchradius (300) |
| `--calibration {auto\|gnss\|pressure\|none}` | Höhenquelle/Kalibrierung (auto) |
| `--no-uncertainty` / `--sigma-h <m>` / `--sigma-v <m>` | Monte-Carlo-Band aus / GPS-σ (an / 3 / 5) |
| `--no-3d` / `--surface3d-model {dsm\|dtm}` | 3D-Plot aus / Relief-Modell (an / dsm) |
| `--surface3d-max-dim <n>` / `--surface3d-darkness <0..1>` | 3D-Auflösung / Dunkelheit (700 / 0.7) |
| `--surface3d-color {clearance\|p05\|mean}` | 3D-Spur-Einfärbung (clearance) |
| `--timezone <tz>` / `--no-proj-network` | Zeitzone (Europe/Zurich) / PROJ-Netz aus |

## Ausgaben (`output/`)

| Datei | Inhalt |
|---|---|
| `*_map.html` | Interaktive Karte: Track nach 3D-Geländeabstand eingefärbt, kritische Stellen markiert. |
| `*_3d.html` | Interaktiver **3D-Plot**: mattes, dunkles Hillshade-Relief + drehbare Flugspur, eingefärbt nach Abstand; MC-Band im Hover. |
| `*_barogram.html` | Höhenprofil (Flughöhe / Gelände / Oberfläche) + Abstand-über-Zeit mit Schwellen, Events und **Unsicherheitsband** (p05–p95). |
| `*_clearance_kde.html` | **Zeit-Verteilung** über den Hangabstand: Dichte + **kumulativ** („% der Zeit unter X m"), Gelände und Wald. |
| `aggregate_clearance_kde.html` | **Mehrflug-Zusammenzug** (Dichte + kumulativ; pro Flug + Ø + zeitgewichtetes Total), auf Flugdauer normiert. |
| `risk_over_time.html` | **Risiko über Zeit**: Hangabstand-Perzentile (p05/p10/p25/Median) + Zeitanteil unter Schwellen je Flug, chronologisch. |
| `*_points.csv` | Pro Fix alle Werte inkl. MC-Band (mean/p05/p95/min/max). |
| `*_events.csv` | Kritische Momente: Zeit, Ort, Level, Phase (Flug/Landeanflug), Abstände inkl. p05/p95. |
| `*_run.json` | Metadaten: Kachel-Jahrgänge, Kalibrier-Offset/-Konfidenz, Transform-Pipeline, MC-σ. |

Alle HTML sind **self-contained** (plotly inline) und offline öffenbar.

---

## Methodik

- **3D-Abstand mit adaptivem Suchradius:** Für einen Punkt P und jede Rasterzelle im
  Horizontalabstand `d` gilt `3D = sqrt(d²+Δz²) ≥ d`. Der vertikale Bodenabstand
  `V = z − Boden(x,y)` ist damit eine **obere Schranke** für den 3D-Abstand, also genügt
  ein Suchradius `R = min(|V|+margin, r_cap)`. Das ist **exakt** für alle bodennahen
  (kritischen) Punkte und sehr schnell; hohe, unkritische Punkte werden grob abgetastet
  und als `clipped` markiert. Gerechnet wird gegen DTM (Hangabstand) **und** DSM
  (Abstand zu Wipfel/Dach). Verifiziert gegen Brute-Force und `scipy.cKDTree` (0.0000 m
  Abweichung bei unkritischen Punkten).
- **Höhen-Kalibrierung:** Die GNSS-Höhe (`HFALG:GEO`, geoid-bezogen) hat einen nahezu
  konstanten Versatz (Datum LN02 + GPS-Bias). Ein additiver Offset wird so bestimmt, dass
  die am Boden (vor Start / nach Landung) aufgezeichnete Höhe zum DTM passt – das
  absorbiert Datum **und** Bias gemeinsam. Boden-Erkennung via geglättetem Speed/Vario.
- **Wald/Bewuchs:** separater Abstand zum DSM. Ein Event ist `Gelände` oder `Wald/Objekt`,
  je nachdem, was näher ist – so werden bewaldete Steilhänge korrekt als kritischer erkannt
  als der nackte Boden.
- **Kritische Momente:** lokale Minima unter konfigurierbaren Schwellen
  (Gelände 50/30/15 m, Oberfläche 30/15/5 m). Bodenkontakt bei Start/Landung zählt nicht;
  reine Endabstiege heissen `Landeanflug`; die „im Flug"-Minimumstatistik klammert den
  finalen Landeabstieg aus.
- **GPS-Unsicherheit (Monte Carlo):** Der Hangabstand reagiert empfindlich auf den
  GPS-Fehler (in steilem Gelände horizontal ~1:1, vertikal 1:1). Jede Position wird N-fach
  normalverteilt gestört (σ_h, σ_v) und gegen denselben Gelände-Patch gerechnet → Mittel,
  p05–p95, min/max. Niedrige Punkte voll per MC, weit über Grund analytisch (σ ≈ σ_v).
  Das Band steckt im Barogramm, in den CSVs und im 3D-Hover.
- **Zeit-Verteilung:** zeitgewichtete KDE des Hangabstands (Dichte + kumulative ECDF) pro
  Flug und als Zusammenzug über alle Flüge, normiert auf die Flugdauer.
- **Risiko über Zeit:** je Flug (chronologisch) die tiefen Hangabstand-Perzentile und der
  Zeitanteil unter den Schwellen – zeigt, wie sich die Annäherung ans Gelände entwickelt.
- **3D-Relief:** monochrome, **matte Schummerung (Hillshade)** aus dem DEM (kein Glanz),
  bewusst **dunkel** gehalten, damit die rot→grün-Abstandsspur abhebt und das Relief
  (Rinnen/Grate) klar lesbar bleibt; echte Proportionen (`aspectmode='data'`).

## Entscheidungen & Begründungen

Die wichtigsten gemeinsam getroffenen Entscheidungen:

1. **Echter 3D-Abstand statt nur vertikal (AGL).** „Hangabstand" ist beim Soaren seitlich
   definiert; man kann 400 m über dem Talboden, aber 20 m neben einer Wand sein. Der
   vertikale AGL-Wert wird als Beiprodukt mitgeführt.
2. **Höchste Auflösung (0.5 m)**, nur Track-Umkreis laden + cachen. 2 m optional für Tempo.
3. **Neuester Kachel-Jahrgang** je Position ("modernste Modelle"); überschreibbar.
4. **GNSS-Höhe als Quelle** (geoid-bezogen, `HFALG:GEO`). Druckhöhe ist ISA-referenziert
   → für Absoluthöhen ungeeignet. Handy-Tracks (XCTrack) haben Druck = 0, GNSS ist nutzbar.
5. **Boden-Kalibrierung statt REFRAME-Höhentransformation:** ein konstanter Offset
   absorbiert Höhendatum (LN02) und GPS-Bias zusammen. REFRAME diente nur zur Prüfung der
   Horizontalgenauigkeit.
6. **Horizontal-Transformation lokal mit pyproj** (WGS84→LV95): gegen die swisstopo-REFRAME-API
   auf **0.01 m** validiert → kein CHENYX06-Grid nötig (das gilt nur für das alte LV03).
7. **Wald über DSM (swissSURFACE3D)**, separat zum nackten Gelände; Events nach beidem.
8. **Start/Landung nicht als Flug-Event;** Endabstiege als `Landeanflug` gekennzeichnet
   (statt versteckt) – nichts wird unterschlagen, aber korrekt eingeordnet.
9. **Unsicherheit per Monte Carlo** mit σ_h = 3 m, σ_v = 5 m (u-blox; Handy höher),
   N = 80, volles MC unter 80 m Abstand, sonst analytisch. Band als p05–p95 (robust) plus
   min/max. **MC auch im 3D** (Hover; optional konservative Einfärbung nach p05).
10. **Verteilungs- statt nur Momentaufnahme-Sicht:** zeitgewichtete KDE + kumulative ECDF,
    plus Risiko-über-Zeit, um Muster über die Saison sichtbar zu machen.
11. **3D matt, dunkel, Hillshade** (nicht glänzend/hell) und Display-Downsampling: volle
    0.5 m über einen ganzen Flug wären ~36 Mio. Punkte und sprengen jeden Browser; der
    Default (~4–5 m) ist via `--surface3d-max-dim` steigerbar.
12. **Self-contained HTML** (offline öffenbar, ohne Server/Token).
13. **Flugdaten (`source/igc/`) sind versioniert** – konsistent mit den ursprünglichen
    Tracks und für reproduzierbare Auswertungen. Bei Bedarf per `.gitignore` ausschliessbar.

## Genauigkeit & Grenzen

- **GNSS-Höhe:** Handy-Tracks sind vertikal verrauschter als dedizierte Logger
  (u-blox). Kalibrier-Konfidenz steht in `*_run.json`. Absolutwerte haben einige Meter
  Unsicherheit – das MC-Band zeigt sie; Abstände unter ~5 m nicht überinterpretieren
  (meist Landung/Bodenkontakt).
- **DTM-/DSM-Jahrgänge** können abweichen (DTM oft neuer) → Waldhöhe mit kleinem Vorbehalt.
- **`clipped`-Punkte** (Abstand > `r_cap`) sind nicht exakt, aber unkritisch.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

## Projektstruktur

```
analyze.py                  Einstiegspunkt (python analyze.py source\igc)
src/terrainclearance/
  config.py                 alle Parameter (Schwellen, σ, Auflösung, 3D-Optik …)
  igc_loader.py             IGC lesen, Höhenquelle pro Datei wählen
  geo.py                    WGS84 -> LV95 (pyproj, cm-genau)
  stac.py                   STAC-Abfrage, Kachelauswahl (neuester Jahrgang)
  tiles.py                  Download/Cache, Mosaik, bilineares Sampling, Patches
  terrain.py                adaptiver 3D-Abstand (DTM & DSM)
  calibrate.py              Boden-Erkennung + Höhen-Offset
  critical.py               Events, Schweregrad, Phase (Flug/Landeanflug)
  uncertainty.py            Monte-Carlo-Unsicherheitsband
  distribution.py           Zeit-Verteilung (KDE/ECDF), Aggregat, Risiko-über-Zeit
  report.py                 Karte, 3D, Barogramm, CSV/JSON
  pipeline.py               Orchestrierung pro Flug
  cli.py                    Kommandozeile
tests/                      pytest-Suite
examples/data/igc/          Beispieltracks (5 längste Flüge; eigene Tracks lokal, gitignored)
cache/  output/             generiert (gitignored)
```
