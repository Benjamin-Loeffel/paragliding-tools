# Thermikmodell — Entscheidungs-Journal & ADRs

Laufendes Journal der solargetriebenen Thermik-Modellierung (`src/thermalmodel/`).
Format: oben ein chronologisches **Arbeitslog**, darunter **Architecture Decision Records (ADRs)**.
Jeder ADR: Status · Kontext · Entscheidung · Begründung · Annahmen · Konsequenzen · Verifikation.

Geführt teils autonom (Nachtlauf 2026-06-29/30). Quelle der Wahrheit für *warum* etwas
so gebaut ist; das *was* steht im Code, das *wann* in der Git-Historie.

---

## Arbeitslog

### 2026-06-29 (abends, mit dem Autor)
- Phase A (ideales Wärmebild) fertiggestellt: Solar→Q_H→Hotspots, 3D-Energieplot (Viridis).
- Vier kumulative Energie-Stände (11/13/15/18 h), 2D-Panel + je 1 volles 3D-HTML.
- **Bug gefunden (vom Autor)**: morgens leuchteten die West- statt Osthänge → Aspect-180°-Flip
  korrigiert (ADR-0006). Domäne auf volles Rechteck umgestellt (ADR-0007).
- A5b: reales (wolkengedämpftes) Wärmebild via ICON-CH1 über Open-Meteo (ADR-0008).
  Ergebnis 29.06.: 99 % bewölkt, Q_H-Tagesenergie median 2682→1469 Wh/m² (45 % Wolkenverlust).
- Commits: `c8701b2` (Phase A), `2b5f006` (Aspect-Fix), `7728f64` (A5b).

### 2026-06-29 (Nachtlauf ab 22:50, autonom bis 07:00)
- Auftrag: im Plan weiterarbeiten (D0/D1 + Validierung), ADR-Journal führen, per Websuche
  plausibilisieren, Meilensteine committen (kein Push).
- Journal angelegt, ADR-0001..0009 nachdokumentiert.
- **IGC-Steigflüge extrahiert** (`validation/igc_climbs.py`): 42 Steigsegmente aus 28 Flügen,
  alle in der Domäne (der Pilot fliegt genau hier). Raten 1.0–1.7 m/s, Basis 1400–2500 m.
- **Validierung Phase-A-Hotspots vs. Realität** (`validation/metrics.py`, ADR-0010):
  Hit-Rate <300 m 45 % real vs. 21 % Zufall (Lift ×2.2); Score-AUC **0.669**; Q_H-AUC 0.585
  (Terrain-Trigger addieren also Vorhersagewert); Median-Steigpunkt im 67. Score-Perzentil.
  → Modell hat echte, moderate Vorhersagekraft; Steigflüge clustern im Flugkorridor (Niesen-Grat).
- Commit `02ccf1f`/`a5cbbdc` Validierung (IGC + Metriken).
- **Parallel-Recherche** (kk7-Zugriff · Thermik-Trigger · Plausibilisierung) ausgewertet:
  - kk7 hat offene REST-API → `validation/kk7.py` (18 Hotspots in der bbox).
  - Physik-Korrekturen (ADR-0011): f_H Schnee 0.20→0.05 (schmelzender Schnee = Totzone),
    Albedo Fels 0.25→0.28 (helle Kalkfelsen), f_H als „effektiver Heizfaktor" dokumentiert.
  - D0-Trigger-Design literatur-fundiert (vier Säulen, w*-Modell); fehlende Hebel:
    Triggerlinien/Kanten, Bodenfeuchte, Lee/Luv-Wind.
- **Kreuzvalidierung IGC vs. kk7** (zwei unabhängige Ground-Truths) stimmen überein:
  Score-AUC 0.665 (IGC) vs. 0.657 (kk7), Lift ×2.4 vs. ×2.1 @300 m → konsistente,
  ehrliche ~0.66-Güte für ein statisches Proxy (literaturtypisch, Hosmer-Lemeshow „borderline").
- **D0 Thermik-Quell-Proxy** (`buoyancy.py`) gebaut + datengetrieben kalibriert (ADR-0013).
  Ablation (AUC einzeln, IGC/kk7): slope 0.67/0.60, aspect 0.57/0.67, convex 0.60/0.58,
  heat 0.54/0.52, **edge (Triggerlinien) 0.50/0.40 → verworfen**. Finale Gewichtung
  (heat 0.3, conv 0.5, aspect 0.4, slope 0.7) → **D0-AUC 0.712 (IGC) / 0.711 (kk7)**,
  klar über Phase-A-Score (0.66). Terrain-Geometrie dominiert; Heizung schwacher Diskriminator.
  In Pipeline integriert (GeoTIFF + 3D). Commit `…`.
- **Phase B Grenzschicht** (`boundarylayer.py`): aus der archivierten Payerne-Sondierung
  (2026-06-29 12Z) z_i/w*/Ceiling je Hotspot (ADR-0014). Ergebnis: w* median 1.56 m/s
  (max 2.24), Ceilings ~3200–3600 m AMSL — physikalisch plausibel (Alpensommer 1–2.5 m/s).
  Mehrere Iterationen nötig: CCL-z_i unbrauchbar (30 km, zu trockene Luft → Blauthermik),
  θ-CBL-Methode + Bergthermik-Korrektur (Parcel-Aufstieg ab geheiztem Bergboden, Q_H-skalierte
  Überhitzung) statt Tiefland-CBL. Commit `…`.
- Commits durch die Nacht: D0, Phase B, D1, Validierung (IGC+kk7), Tests, CLI/README, Phase C.

### 2026-06-30 (2. Block, iterativ mit dem Autor)
- des Autors Wünsche: kk7-**Heatmap** statt nur Hotspots (ADR-0019); Wind-**Höhen-Subplots** 1×5
  (ADR-0020); einheitliche **Colormaps** + DPI + Datum + Modelltag 30.06 (ADR-0020).
- Kreative Iteration (Kernfragen wann/wo/Wind): **z_i(t)-CBL-Tagesgang** (ADR-0021) → diurnale Drifts;
  **Tages-Timeline/Startfenster + Wind-Zerstörung** (ADR-0022); **Vegetations-Ablösung** (ADR-0023);
  **Plot-Politik** helles Relief/km/h/Halo (ADR-0024).
- **Retrospektive Validierung** (ADR-0025): eigene Flugtage × historisches Wetter (ERA5/ICON) →
  z_i bester Prädiktor (Spearman +0.48); kleines Sample. **kk7 zeitgefiltert** (ADR-0026): Zeitabgleich
  hilft nicht → Thermik-Orte terrain-kontrolliert.
- Durchgehend web-plausibilisiert (Encroachment β=0.2, Wind-Zerstörung 25 kt, ERA5-Zugang, Flugportale);
  34 Tests grün; alle Meilensteine committet (kein Push).

### 2026-06-30 (3. Block, mit dem Autor)
- **D1-Plumes zeitaufgelöst** (ADR-0029): die 3 Varianten (Hotspots/kk7/Netz) je Uhrzeit (11/13/15/18 h)
  mit Q_H(t)/ICON-Wind(t)/z_i(t) → je 1 HTML mit Uhrzeit-Slider (`build_plume_3d_timeslider`). Lauf
  bestätigt den Tagesgang: Drift/Plume-Top wachsen bis 15 h, Kollaps 18 h. Commit `628af3f`.
- **Doku-Audit** (Subagent-Workflow): einzige echte Lücke = kein „project-findings"-Memory →
  `project-thermalmodel-findings` (Memory) angelegt. ADR-0030 (Kanten/Lee-Luv per CV verworfen) +
  ADR-0031 (WeGlide-Datenweg) formalisiert; `ref_elev`-Default-Fix 2200→1600. Commits `9259f97`, `4ba8504`.
- **WeGlide-API reverse-engineered** (ADR-0031): offen nutzbar (kein Key für Reads), `airport_id_in`
  als Regionsfilter, IGC via `flightdetail`. ABER segelflug-zentriert — KEINE PG-Startplätze am Niesen;
  taugt nur als Segelflug-Quelle (Zweisimmen/Thun/Saanen). **Strang PAUSIERT** auf des Autors Wunsch;
  offene Entscheidung: Segelflug-Client vs. nur-Tagesgüte vs. PG-only (eigene IGC + manuelle XContest).
- **Historisches Wetter geklärt** (Autor-Frage): kein echter 33-h-ICON-CH-Vorlauf offen archiviert;
  Retro nutzt Open-Meteo `historical-forecast-api` (icon_seamless, ≥2024) + ERA5 — bewusst die
  Vorhersagbarkeits-Obergrenze (Physik-Skill, nicht Prognose-Skill).

---

## ADRs

### ADR-0001 — Eigenes Paket `thermalmodel`, Wiederverwendung von `terrainclearance`
**Status:** akzeptiert (2026-06-29)
**Kontext:** Das Geländeabstand-Tool (`terrainclearance` + `meteo`) ist fertig und liefert
STAC-Download, Mosaik/Sampler, LV95-Transform, IGC-Loader, Payerne-Sondierung.
**Entscheidung:** Neues Schwester-Paket `src/thermalmodel/`, das `terrainclearance`/`meteo`
importiert; keine Umbauten am Bestehenden (höchstens additiv, z. B. `reproject.py` für die
LV95→WGS84-Inverse).
**Begründung:** Trennung der Belange, kein Risiko fürs erprobte Tool, maximale Wiederverwendung.
**Annahmen:** Die terrainclearance-APIs sind stabil genug zum direkten Import.
**Konsequenzen:** Zwei requirements-Dateien; thermalmodel hängt an terrainclearance.
**Verifikation:** Phase A läuft end-to-end über die wiederverwendeten Module.

### ADR-0002 — Modellgitter 20 m
**Status:** akzeptiert (2026-06-29)
**Kontext:** swissALTI3D gibt es in 0.5/2 m; Zeit-Cubes [nt,ny,nx] über den Tag.
**Entscheidung:** Rechengitter 20 m; DTM-Resampling aus 2-m-Kacheln; 0.5 m nur bei Bedarf (DSM/CHM).
**Begründung:** 20 m löst die thermikrelevante Hangstruktur auf, Cubes bleiben ~20 MB
(29×516×367×4 B ≈ 22 MB), Horizont/SVF in Sekunden–Minuten berechenbar.
**Annahmen:** Thermik-Auslösung ist auf ~20 m hinreichend beschrieben; feinere Struktur
(Einzelbäume) irrelevant fürs Hangskala-Signal.
**Konsequenzen:** ICON-Wolken (~1 km) sind viel gröber als das Gitter → τ räumlich nur grob.
**Verifikation:** Domäne 516×367 @20 m, Laufzeit Phase A ~5–11 s (Horizont gecacht).

### ADR-0003 — Bodenbedeckung aus BAFU/LFI-Waldmischungsgrad
**Status:** akzeptiert (2026-06-29)
**Kontext:** Nadelwald heizt anders als Laubwald/Wiese/Fels. Brauchen Albedo + f_H je Zelle.
**Entscheidung:** Wald + Nadel/Laub-Anteil aus dem LFI-Waldmischungsgrad-COG (10 m, EPSG:2056,
Wert = % Laubholz, nodata = kein Wald) per /vsicurl-Fensterlesen. Nicht-Wald per Heuristik
(Slope/Höhe → Fels/Wiese). Albedo/f_H im Wald linear zwischen Nadel/Laub interpoliert.
Fallback: TLM3D-Wald-WMS (Nadel-Annahme) bzw. reine Heuristik.
**Begründung:** Einzige frei verfügbare, schweizweite, bereits in LV95 vorliegende Nadel/Laub-Info.
**Annahmen:** Wert = % Laubholz (per STAC-Doku/Websuche bestätigt); nodata ⇔ kein Wald.
**Konsequenzen:** Fels/Wiese nur heuristisch (keine TLM-Bodenbedeckung gerastert — später optional).
**Verifikation:** Gebiet 22 % Nadel / 10 % Misch / 9 % Laub / 46 % Wiese / 13 % Fels — plausibel
für die Niesen-Frutigen-Seite.

### ADR-0004 — Sonne/Klarhimmel via pvlib + Horizont/SVF
**Status:** akzeptiert (2026-06-29)
**Entscheidung:** Sonnenstand NREL-SPA (pvlib), Klarhimmel Ineichen (Linke-Klimatologie),
Gelände-Einfallswinkel cos γ, Horizontwinkel je Azimut (numpy-Ray-March) → Schatten + Sky-View-Factor;
G_clear = DNI·cosγ·(unbeschattet) + DHI·SVF + Reflex.
**Begründung:** pvlib ist der Standard; Horizont/SVF einmalig gecacht (geometrisch, tagesunabhängig).
**Annahmen:** Linke-Monatsklimatologie statt tagesaktueller Trübung genügt fürs Klarhimmel-Maximum.
**Konsequenzen:** Reale Trübung/Aerosole nicht tagesscharf — durch A5b (ICON) teils kompensiert.
**Verifikation:** SVF 0.13–1.0 (median 0.70); Schattenwurf im Tagesgang plausibel.

### ADR-0005 — Thermik-Proxy Q_H = f_H·(1−albedo)·G
**Status:** akzeptiert (2026-06-29)
**Kontext:** Thermik wird vom fühlbaren Wärmestrom (sensible heat flux) getrieben, nicht von der
Einstrahlung allein.
**Entscheidung:** Q_H = f_H·(1−albedo)·G_terrain als treibendes Feld; f_H = Sensible-Heat-Anteil
je Bodenklasse (Bowen-artig). Tagesmax = Aptitude, Tagesintegral = Energieeintrag (Wh/m²).
**Begründung:** Einfachstes physikalisch sinnvolles Surrogat; trennt Reflexion (Albedo) und
Verdunstung/Bowen (f_H) von der reinen Einstrahlung.
**Annahmen:** f_H/Albedo-Tabellen aus Literaturwerten; keine Bodenfeuchte-/Speicher-Dynamik (statisch).
**Konsequenzen:** Kein Zeitversatz (Boden-Wärmespeicher) modelliert — Q_H folgt G instantan.
**Verifikation:** Q_H-Tagesmax median ~320 W/m² (Klarhimmel) — in der erwarteten Grössenordnung.
**Offen/zu prüfen:** f_H-Werte gegen Literatur plausibilisieren (Websuche, TODO Nachtlauf).

### ADR-0006 — Aspect-Berechnung: 180°-Flip korrigiert
**Status:** akzeptiert (2026-06-29)
**Kontext:** Im 11-Uhr-Kumulativbild leuchteten die WEST-Hänge (des Autors Beobachtung); morgens
muss aber die OST-Seite besonnt sein.
**Entscheidung:** `_slope_aspect` lieferte die Richtung des steilsten *Anstiegs* statt der
Hang-*Zeigerichtung* (bergab). Korrektur: `aspect = atan2(-dzdx, dzdy) % 2π` (0=N, 90=O, im Uhrzeigersinn,
pvlib-Konvention).
**Begründung:** In (Ost,Nord): dz/dOst=dzdx, dz/dNord=−dzdy (Row→Süd); Bergab=−∇z=(−dzdx,+dzdy);
Kompass-Azimut=atan2(Ost,Nord).
**Konsequenzen:** Alle früheren Hotspots (vermeintlich „SSW 206°") waren real NNE — Phase B/C/D wären
sonst an den falschen Hängen gelaufen.
**Verifikation:** Vormittag O/SO am höchsten (O 1066 Wh/m²), Nachmittag W/SW (W 938); Top-Hotspots
jetzt echt SSW ~200–215°. Numerisch je Aspekt-Oktant geprüft + visuell.

### ADR-0007 — Volle Rechteck-Domäne statt Polygon-Schnitt
**Status:** akzeptiert (2026-06-29)
**Kontext:** Das KML-Polygon beschnitt das Gitter auf 52 % (gezackter Rand im 3D-Plot).
**Entscheidung:** `clip_to_polygon=False` (Default): ganze bbox-Domäne aus den ohnehin geladenen
Kacheln rechnen/zeigen; Polygon bleibt nur als Referenz.
**Begründung:** Der Autor: „verwende einfach alle Kacheln, die unser Polygon enthalten." Kein Datenverlust,
kein gezackter Rand, mehr Kontext um die Hotspots.
**Konsequenzen:** ~2× mehr Zellen aktiv (100 % statt 52 %); minimal mehr Rechenzeit.
**Verifikation:** Domäne 100 % belegt, saubere Rechteck-Reliefs.

### ADR-0008 — ICON-CH-Wolken via Open-Meteo statt meteodata-lab
**Status:** akzeptiert (2026-06-29)
**Kontext:** A5b braucht reale Globalstrahlung/Bewölkung. Recherche (3 Agenten): Globalstrahlung =
ASWDIR_S+ASWDIFD_S (Zeitmittel seit Start, de-aggregieren), Wolken=CLCT. Zwei Wege: meteodata-lab
(offiziell, GRIB) vs. Open-Meteo (JSON).
**Entscheidung:** Open-Meteo `models=meteoswiss_icon_ch1` (direct/diffuse/shortwave_radiation + cloud_cover),
gekapselt in `nwp.py`. Daraus Faktoren f_dir/f_dif/f_ghi gegen pvlib-Klarhimmel; Direkt stärker gedämpft
als Diffus. Räumlich (RegularGridInterpolator über Stützpunkt-Raster) + zeitlich aufs Modellgitter.
**Begründung:** meteodata-lab auf nativem Windows fragil (eccodes/earthkit) und pinnt numpy<2.4 →
Risiko fürs bestehende venv. Open-Meteo = dieselben ICON-CH1-Felder, GRIB-frei, in Lokalzeit, nur
requests+pandas. Der Autor hat Open-Meteo explizit gewählt.
**Annahmen:** Open-Meteo-Werte ≈ ICON-CH1-Roh (leicht nachprozessiert); ~1 km Auflösung → τ v. a. zeitlich;
OGD-Retention ~24–48 h → Tagespull cachen.
**Konsequenzen:** Kein Zugriff aufs native Dreiecksgitter/Member; Quelle aber gekapselt → späterer
Wechsel auf meteodata-lab trivial.
**Verifikation:** 29.06. f_dir 0–0.55 (overcast), f_dif bis 1.8 (Wolkenstreuung >1, erwartet),
45 % Energieverlust — physikalisch stimmig. Siehe Memory `reference-icon-ch-nwp`.

### ADR-0009 — Phase D zweistufig: einfaches Proxy/Plume vor LES
**Status:** akzeptiert (2026-06-29)
**Kontext:** Fernziel ist CFD/LES, aber volles LES = GPU + Wochen; Validierung gegen kk7/IGC ist
klimatologisch (kein tagesscharfer Abgleich über ICON-Retention hinaus).
**Entscheidung:** Erst D0 (statisches Auftriebs-Proxy) + D1 (Lagrange-Plume) — schnell, gegen kk7/IGC
vergleichbar — dann ggf. LES (D3 idealisiert → D4 down-scoped PALM → D5 voll).
**Begründung:** Schnellstes gegen die Realität prüfbares Ergebnis; LES erst, wenn das Proxy trägt.
**Annahmen:** Trefferqualität des Proxy entscheidet, ob LES sich lohnt.
**Konsequenzen:** Validierungs-Harness (IGC-Steigflüge + kk7) ist Voraussetzung und wird zuerst gebaut.
**Verifikation:** offen — Gegenstand des Nachtlaufs.

### ADR-0010 — Validierungs-Methodik: Steig→Modell, verschiebungstolerant, mit Zufalls-Baseline
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** Reale Steigflüge (IGC) sind die beste Bodenwahrheit, aber der Autor befliegt nur einen
schmalen Korridor (Start/Route), nicht die ganze Domäne → starker Sampling-Bias.
**Entscheidung:** Bewertet wird die Richtung **Steigpunkt → Modell** (Hit-Rate: Anteil Steigpunkte
nahe einem Top-N-Hotspot; Score-AUC: P(Score(Steig) > Score(Zufallszelle))), je gegen eine
Zufalls-Baseline gleicher Grösse. Die Gegenrichtung (Modell → Steig, „Precision") wird NICHT als
Gütemass benutzt, da Hotspots in unbeflogenem Gelände sonst unfair als Fehlalarm zählten.
Toleranzen 200/300/500 m (kk7/Drift-unscharf), Einstiegspunkt als Trigger-Proxy.
**Begründung:** Statistische Ko-Lokalisation statt Pixelgenauigkeit; AUC ist schwellenfrei und
robust gegen die willkürliche Top-N-Grenze. Lift gegen Zufall macht „besser als Raten" explizit.
**Annahmen:** Steig-Einstieg ≈ Auslöser (Drift im Steigen vernachlässigt — separat als `drift_m`
protokolliert, Median ~100 m); GNSS-Höhe für Vario zuverlässig.
**Konsequenzen:** Gütemass ist optimistisch begrenzt durch den Korridor-Bias; absolute Hit-Raten
nicht überinterpretieren, Lift/AUC sind die belastbaren Zahlen.
**Verifikation (Phase A):** AUC 0.669, Lift ×2.2 @300 m — signifikant über Zufall, plausibel für ein
statisches Proxy ohne Wind/Grenzschicht. **Web-plausibilisiert**: AUC 0.65–0.70 ist literaturtypisch
für statische Prädiktor→Punkt-Ereignis-Modelle (Hosmer-Lemeshow „borderline acceptable"); >0.8
verlangt dynamische Prädiktoren (Wind/Sondierung). **kk7-Kreuzvalidierung** bestätigt (AUC 0.657).

### ADR-0011 — f_H/Albedo-Tabellen literatur-plausibilisiert (Korrekturen)
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** Web-Recherche gegen Bowen-/MODIS-Literatur.
**Entscheidung:** (1) f_H Schnee 0.20→**0.05** (schmelzender Schnee bei 0 °C: stabile Grenzschicht,
fühlbarer Fluss oft negativ → thermische Totzone; 0.20 war die einzige physikalisch falsche Zeile).
(2) Albedo Fels 0.25→**0.28** (helle Kalk-/Karbonatfelsen der Berner Voralpen). (3) Klarstellung im
config-Kommentar: f_H ist ein **effektiver fühlbarer Heizfaktor** bezogen auf absorbierte Kurzwelle
(1−albedo)·G (schluckt LW-Verlust + Bodenwärmestrom), NICHT reines Bowen B/(1+B) auf R_n — daher
liegen Wiese 0.50 / Fels 0.75 bewusst über dem reinen Bowen-f_H.
**Begründung:** Restliche Werte literaturkonform bestätigt (Albedo durchweg, f_H-Rangfolge korrekt).
**Annahmen:** Für absolute w*-Nutzung Q_H mit ~0.55 (R_n/G) vorskalieren (sonst w* überschätzt).
**Konsequenzen:** AUC praktisch unverändert (0.669→0.665, wenig Schnee/Fels-Anteil) — Korrektur ist
physikalische Ehrlichkeit, kein Skill-Gewinn.
**Verifikation:** Re-Lauf stabil; Rangfolge der Bodenklassen unverändert plausibel.

### ADR-0012 — kk7 als zweites, unabhängiges Validierungs-Target
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** thermal.kk7.ch bietet eine offene REST-API (GeoJSON-Hotspots je bbox/category).
**Entscheidung:** `validation/kk7.py` zieht die Hotspots (gecacht), als KOMPLEMENT zu des Autors IGC.
**Begründung:** kk7 aggregiert viele Piloten (breitere Abdeckung), ist aber startplatz-/routenbiased
und braucht ~20 Flüge/100 m → in dünn beflogenen Zonen lückenhaft. Eigene IGC bleiben primär.
**Annahmen:** probability∈0..1; Hotspot ≙ 250-m-Kreis (passt zur <300-m-Toleranz). Daten © M. v. Känel.
**Konsequenzen:** Zwei unabhängige Targets erlauben Kreuzvalidierung (Robustheit gegen je eigenen Bias).
**Verifikation:** 18 Hotspots in der bbox; AUC 0.657 ≈ IGC 0.665 → konsistent, stützt die ~0.66-Aussage.

### ADR-0013 — D0 Thermik-Quell-Proxy: datengetrieben, Triggerlinien-Term verworfen
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** D0 soll ein gegen IGC/kk7 validiertes, kontinuierliches Quell-Wahrscheinlichkeitsfeld
liefern. Die Recherche legte einen Triggerlinien-/Kanten-Term (Q_H-Gradient) als wahrscheinlichsten
Mehrwert nahe.
**Entscheidung:** D0 = gewichtete Summe aus Heizung (Q_H-Tagesenergie), Konvexität, Aspekt-Sonnen-
ausrichtung (SSW) und Hangband; Wasser/Schnee = 0. Gewichte datengetrieben kalibriert (Grid-Suche
über 36 Kombinationen, bewertet auf IGC UND kk7): **heat 0.3, conv 0.5, aspect 0.4, slope 0.7**.
Der **Kanten-Term wird verworfen** (Default-Gewicht 0).
**Begründung (Ablation, AUC einzeln IGC/kk7):** slope 0.67/0.60 (stärkster Einzelprädiktor),
aspect 0.57/0.67, convex 0.60/0.58, heat 0.54/0.52, **edge 0.50/0.40 = keine bzw. negative
Vorhersagekraft**. Q_H-Heizung ist ein schwacher Diskriminator, weil ihr Geometrie-Anteil
(Aspekt/Slope/Sonne) schon in den expliziten Termen steckt und die Land-Cover-/Albedo-Variation
auf dieser Validierungs-Skala Rauschen ist. Triggerlinien (als Q_H-Gradient) folgen v. a.
Land-Cover-Grenzen, die nicht mit Steigorten korrelieren.
**Annahmen/Caveats:** Gewichte in-sample getunt (42 IGC + 18 kk7) → ~0.71 ist leicht optimistisch;
beide Sets teilen den Korridor-/Terrain-Selektions-Bias (Piloten fliegen steile SSW-Grate → slope/
aspect sagen fast tautologisch gut vorher). heat bewusst auf 0.3 (>0) gehalten für physikalische
Sinnhaftigkeit, obwohl heat=0 minimal höhere AUC gäbe.
**Konsequenzen:** D0-AUC 0.712/0.711 > Phase-A-Score 0.66; robust über beide unabhängigen Sets.
Ehrliche Lesart: Terrain-Geometrie trägt das Signal; echte tagesdynamische Verbesserung (>0.75)
braucht Wind/Sondierung/Konvergenz (Phase B/C).
**Verifikation:** Re-Lauf + Komponenten-Ablation reproduzierbar; 3D-Plot plausibel (gelb auf SSW-Graten).

### ADR-0014 — Phase B: z_i/w*/Ceiling aus Payerne-Sondierung (Bergthermik-Korrektur)
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** Thermikstärke (w*) und Decke je Hotspot aus dem Vertikalprofil. Eine Tiefland-
Sondierung (Payerne, 491 m, ~40 km nördlich) direkt auf Berggelände (Hotspots 2200–2445 m)
anzuwenden ist nicht trivial.
**Entscheidung:** `boundarylayer.py`. z_i NICHT über die CCL (ergab 30 km, da die Luft sehr
trocken ist → Blauthermik), sondern: (a) Tiefland-CBL über die potenzielle Temperatur θ
(Mischungsschicht-Mittel + 1 K Inversion); (b) **pro Hotspot** Thermik-Top via trockenadiabatischem
Parcel-Aufstieg ab dem geheizten Bergboden — θ_Parzelle = θ_Umgebung(Hotspot-Höhe) + Überhitzung,
steigt bis θ_Umgebung sie einholt. Überhitzung ∝ Q_H (1.5–7 K; heisse Fels/SSW-Hänge brechen höher
durch). Cumulus deckelt nur, wenn die Wolkenbasis ÜBER dem Hotspot liegt. w* = Deardorff mit
w'θ'0 = 0.55·Q_H/(ρ·cp) (Faktor 0.55 ≈ R_n/G, ADR-0011).
**Begründung:** Eine Punkt-Tiefland-Sondierung unterschätzt die Bergthermik-Decke (über erhöhtem,
geheiztem Gelände mischt die CBL höher). Der Parcel-ab-Bergboden-Ansatz behebt das physikalisch
nachvollziehbar; volle Korrektheit bräuchte ein 3D-Modell (RASP/Toptherm) — Fernziel LES.
**Annahmen:** Regionale θ-/Wind-Struktur ≈ Payerne; Überhitzung linear in Q_H; T0=290 K, ρ=1.0.
Gilt für den Sondierungstag (2026-06-29 12Z), nicht klimatologisch.
**Konsequenzen:** w* median 1.56 m/s (max 2.24), Ceiling ~3200–3600 m AMSL — plausibel
(Alpensommer 1–2.5 m/s, meteoblue „gut"). Sondierungswind (166 Niveaus) steht für D1-Advektion bereit.
**Verifikation:** Grössenordnung web-plausibilisiert; höhere Q_H → höheres w* (monoton, erwartet).

### ADR-0015 — D1: Lagrange-Plume (driftende Thermik), passiv mit Sondierungswind
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** Erstes räumlich-dynamisches Produkt: wohin driftet eine Thermik beim Aufstieg?
**Entscheidung:** `plume.py`. Parzelle ab Hotspot, Vertikalprofil Lenschow/Allen
w(ẑ)=w*·ẑ^(1/3)·(1−1.1ẑ), horizontal advehiert vom Sondierungs-Höhenwind (u,v interpoliert).
Euler-Integration bis zur „nutzbares-Steigen"-Schwelle w_min=0.4 m/s (statt w→0-Decke). 3D-Plot
der Säulen (nach Höhe gefärbt).
**Begründung:** Schnellster gegen kk7/IGC vergleichbarer Drift-Indikator; nutzt w*/Ceiling aus
Phase B und den bereits vorhandenen Sondierungswind (kein separater ICON-Wind-Fetch nötig).
**Annahmen/Caveats:** PASSIVE Parzelle (keine Verankerung/kein Entrainment-Detail), regionaler
Payerne-Wind. w_min=0.4 schneidet das unrealistische w→0-Kriechen nahe der Decke ab.
**Konsequenzen/Verifikation:** Drift median 1180 m (Aufstieg ~11 min); Richtung dreht mit der Höhe
(unten NE→Drift SW, oben SW→Drift NE) — physikalisch kohärent. ABER Drift-**Rate** 180 m/min vs.
IGC 74 m/min → Modell driftet ~2.4× zu stark: reale Thermik ist terrain-verankert, Piloten coren
eng, und der lokale (geschützte) Talwind ist schwächer als die Payerne-Sondierung. Richtung gut,
Betrag zu gross — erwartetes Verhalten eines passiven Plume-Modells (echte Verankerung erst im LES).

---

### ADR-0016 — Phase C: anabatische Hangaufwind-Parametrisierung (in D1)
**Status:** akzeptiert (2026-06-30, Nachtlauf)
**Kontext:** D1 (passiv, nur Sondierungswind) driftete ~2.4× zu stark (Rate 180 vs. IGC 74 m/min).
**Entscheidung:** `valleywind.py` — bodennahes anabatisches Windfeld: Richtung bergauf (entgegen
Aspekt), Betrag = max_speed·f(Neigung)·f(Q_H), gedeckelt; quasi-flach → 0. In `integrate_plume`
über h_blend=400 m linear in den Sondierungswind übergeblendet (bodennah Hangwind, oben synoptisch).
**Begründung:** Reale Thermik ist bodennah terrain-organisiert (Hangaufwind), nicht passiv mit dem
Höhenwind treibend. Die Parametrisierung bildet das physikalisch ab, ohne ein Windfeld zu lösen.
**Annahmen:** max_speed=3 m/s (typischer anabatischer Hangwind, **a priori** gewählt, NICHT auf die
IGC-Zahl getunt); Tagsituation (kein Katabatik/Nachtfall); h_blend=400 m.
**Konsequenzen/Verifikation:** Drift-Rate 180→**70 m/min** ≈ IGC 74 m/min — die a-priori-Parametri-
sierung trifft die Beobachtung. Drift median 1180→785 m. In `thermal.py`/D1 standardmässig aktiv.
**Caveat:** Nur erste Näherung; echte Tal-/Hangwindzirkulation (Konvergenz, Lee) erst im LES.

### ADR-0017 — D1 Ablöse-Modell: zweiphasig (hangfolgend → Release)
**Status:** akzeptiert (2026-06-30, 2. Nachtblock)
**Kontext:** des Autors Wunsch, das typische „Thermik steigt am Hang auf, bis eine markante
Änderung kommt, dann löst sie sich ab" abzubilden. Recherche (Zardi & Whiteman; XC Mag „The Hunt";
SkyNomad): Hang-Thermik ist ein **bent-over plume** im anabatischen Hangaufwind, kein freier Ballon;
Ablösung an Grat/Gipfel, Col/Sattel oder markanter Konvexität (fluiddynamisch Grenzschichtablösung
am adversen Druckgradienten der konvexen Kuppe).
**Entscheidung:** `plume.py` zweiphasig. Phase 1 (`_slope_follow`): ab Seed hangaufwärts laufen
(Richtung entgegen Aspekt), bis Release — Konvexität > Perzentil-Schwelle (`d1_release_curv_pct=80`)
ODER Grat/Gipfel (Höhe nicht mehr steigend) ODER Abflachung < 5° nach Steilhang. Phase 2: ab
Release-Punkt der bestehende freie Plume (Lenschow + Wind). w*/Ceiling am Release neu (`strength_at`).
Seeds generalisiert (Hotspots/kk7/Netz). `wind_uv_fn`-Hook für zeitaufgelösten Wind vorbereitet.
**Begründung:** Release-Punkt statt Hotspot als Säulen-Fusspunkt = physikalisch korrekter Lee-Versatz;
nutzt die schon vorhandenen Felder curvature/slope/aspect.
**Annahmen:** Perzentil-Schwelle statt fester 1/m (curvature = Laplacian-Proxy); kein Mindesthang-Gate
(kritischer Hangwinkel nur ~0.1°). u_slope=2 m/s.
**Konsequenzen/Verifikation:** Drift-Rate bleibt 73 m/min (≈ IGC 74). Ablöse-Versatz Hotspot→Release
median nur 40 m → D0-Hotspots liegen bereits auf/nahe konvexen Graten (Konsistenz-Check des D0-Scores,
der Konvexität enthält). Bei Netz-Seeds (mid-slope) greift die Hangfolge stärker.

### ADR-0018 — Zeitaufgelöste Drifts + ICON-Wind-Partikeltraces
**Status:** akzeptiert (2026-06-30, 2. Nachtblock)
**Kontext:** des Autors Wunsch: Drifts zu denselben Uhrzeiten wie die Energiesummen (11/13/15/18 h),
je 2 Karten (Hotspots+kk7 / regelmässiges Netz), plus ICON-Wind als Partikeltraces zum Abgleich.
**Entscheidung:** `wind.py` (ICON-Windfeld via Open-Meteo `icon_seamless`, Druckniveaus 925–700 hPa,
da `meteoswiss_icon_ch1` keine Druckwinde liefert — empirisch verifiziert) + `timedrift.py`.
Je Zeitpunkt: w*(t) aus momentanem realem Q_H(t), Advektion mit ICON-Windfeld(t), zwei Karten
(`drift_HHh_points.png` Hotspots+kk7 als Pfeile; `drift_HHh_grid.png` 150-m-Netz als Drift-Feld-Quiver
mit überlagerten Wind-Streamlines) + `wind_traces_HHh.png` (Streamplot @2500 m).
**Begründung:** Drift ist tagesabhängig (Wind dreht/verstärkt sich, Heizung variiert); fester
Tageswert wäre irreführend. Wind-Traces erlauben den direkten visuellen Check Drift↔Wind.
**Annahmen:** Netz 150 m (100 m wäre ~7500 Pfeile = unleserlich; via `drift_grid_spacing_m` änderbar);
z_i/Ceiling aus Sondierung (statisch), nur w* + Wind zeitabhängig; Wind-Trace-Höhe 2500 m AMSL.
**Konsequenzen/Verifikation:** 11→15 h Drift steigend (Wind 0.9→1.6 m/s, gute Heizung), 18 h Kollaps
(Q_H 51 W/m², schwaches/ kurzes Steigen → Drift 40–160 m). Drift-Pfeile und Wind-Streamlines decken
sich visuell. ICON-Wind dreht mit der Höhe (NE unten → SW oben), konsistent zur Payerne-Sondierung.

### Übernommen von soaringmeteo (Recherche-Quervergleich)
soaringmeteo (F. Pieracci, GPL-3, Scala/SolidJS, GFS+WRF) bestätigt unseren Ansatz frappant: gleiche
**Lenschow-Stephens-w\***-Formel; ihr hartcodierter w\*-Median **1.55 m/s** = unsere 1.56. Sie verwerfen
sogar bewusst die rohe Modell-Vertikalgeschwindigkeit zugunsten der w\*-Parametrisierung (validiert
unsere Wahl). Übernahme: **Soaring Layer Depth** = min(z_i, Wolkenbasis−Höhe) ist bei uns implizit das
`usable_band_m`/`z_i_m` (Ceiling−Höhe). **XC-Potenzial** (`xcpotential.py`) IMPLEMENTIERT als
Logistik-Blend (w\* μ=1.55 doppelt, SLD μ=400, Gegenwind μ=16 dämpfend) → Tagesgüte-Feld 0–100 %
(`xc_potential.png/.tif`, median 59 %, hohe Grate grün). Offen: Hennig-Wolkenbasis 122.6·(T−Td)
als billiger Cu-Basis-Zusatz; Schwellen künftig aus IGC/kk7 statt soaringmeteos μ-Werten kalibrieren.

### ADR-0019 — kk7-Heatmap (Thermals-Raster) als kontinuierliches Validierungs-Target
**Status:** akzeptiert (2026-06-30)
**Kontext:** des Autors Wunsch, statt der 18 kk7-Vektor-Hotspots das flächige Thermals-Dichteraster
(Heatmap-Tiles) zu nutzen.
**Entscheidung:** `validation/kk7_heatmap.py` holt die `thermals_jul_07`-Kacheln (z12, TMS, EPSG:3857),
dekodiert die Jet-artige Farbskala über den Farbton (Dunkelblau→Rot ⇒ 0→1; Alpha = Datenmaske),
reprojiziert nach LV95 aufs Gitter (gecacht). Validierung verschiebungstolerant (250-m-Gauss):
Spearman + AUC (`metrics.heatmap_metrics`).
**Begründung:** Reicher als 18 Punkte; flächiger Vergleich. Hue-Dekodierung, da die exakte kk7-
Farbskala→Wahrscheinlichkeit nicht dokumentiert ist — liefert eine monotone relative Dichte.
**Annahmen:** Farbskala ist monoton (visuell + Hue bestätigt); Glättung 250 m gegen kk7-Unschärfe/Drift.
**Verifikation:** Dekodierung räumlich deckungsgleich mit der Web-Heatmap (Sichtprüfung); **Sanity:
kk7-Dichte sagt des Autors IGC-Steigpunkte mit AUC 0.717 voraus** → Dekodierung valide. Modellvergleich:
**D0 Spearman 0.26 / AUC 0.66 vs. Phase-A-Score 0.05 / 0.55** → D0 erneut klar besser, jetzt gegen das
kontinuierliche kk7-Raster (zuvor schon gegen Hotspots/IGC). Absolutwerte moderat (kk7 = Nutzungs-/
Flugkorridore inkl. Drift, D0 = Quellen) — erwartete, ehrliche Grössenordnung.

### ADR-0020 — Wind-Höhen-Subplots, höhere DPI, Modelltag 2026-06-30
**Status:** akzeptiert (2026-06-30)
**Kontext:** des Autors Wünsche: Wind-Traces je Zeit über mehrere Höhen; zoombare (höhere DPI) Plots
mit Datum; Lauf für heute (30.06.).
**Entscheidung:** (1) `wind.plot_wind_traces_levels`: 5 Subplots **10 m AGL / 400 m AGL / 2000 /
2500 / 3000 m AMSL**; 10-m-Bodenwind separat von Open-Meteo (`wind_speed_10m`), AGL = dtm+agl je
Zelle (Druckniveau-Interp, <50 m → 10-m-Feld), gemeinsame Geschwindigkeitsskala. (2) DPI aller
matplotlib-Plots auf 170–185 (zoombar). (3) Modelltag-Default **2026-06-30** (frische ICON-Wolken+
Wind), Datum in alle Titel.
**Annahmen:** Phase-B-**Sondierung = neueste verfügbare = 29.06 12Z** (die 30.06-Sondierung ist
nachts noch nicht publiziert) — Standard „Morgensondierung für die Tagesprognose". Wolken/Wind sind
30.06-Forecast. kk7 ist klimatologisch (jul_07), datumsunabhängig.
**Verifikation:** Voller Lauf 30.06 sauber; Wind nimmt mit Höhe zu (10 m AGL schwach/bodennah →
3000 m AMSL stark), Höhendrehung sichtbar. D1-Drift-Rate 74 m/min (=IGC). 34/34 Tests grün.

### ADR-0021 — z_i(t)-Tagesgang (CBL-Wachstum) für zeitaufgelöste Drifts
**Status:** akzeptiert (2026-06-30)
**Kontext:** Drifts/Stärke waren zeitlich nur über Q_H(t)+Wind(t) variabel; die Mischungsschicht
z_i wuchs nicht. Damit fehlte die „wann starten"-Aussage (morgens flach, nachmittags tief).
**Entscheidung:** `boundarylayer.cbl_timeseries` — Encroachment-Modell: kumulierter Auftriebs-Heat
∫(0.55·Q_H)/(ρcp)dt füllt den θ-Keil über dem Morgenprofil → z_i(t); Entrainment via Faktor (1+2β),
β=0.2. `growth(t)=z_i(t)/z_i_peak` skaliert die nutzbare Bandtiefe je Hotspot (`strength_at` +
`run_plumes` band_scale). In `timedrift` pro Uhrzeit eingerechnet.
**Begründung:** Standard-Slab/Encroachment (Carson/Tennekes); liefert den Tagesgang ohne separates
Modell. Bandtiefe ∝ regionaler CBL-Wachstumsanteil, B_max weiter aus dem Bergboden-parcel_top.
**Annahmen:** β=0.2; regionaler CBL-Wachstumsanteil gilt auch über dem Berg (Form, nicht Betrag).
**Verifikation:** z_i steigt 1200→2350 m, **bricht ~13–14 h durch die Inversion**; **w\* peakt ~14:00**
(~1.9 m/s) — lehrbuchhaft. Drifts: 11 h kurz (209 m, flache CBL) → 15 h max (947 m, tiefe CBL+Wind)
→ 18 h Kollaps (Q_H 44 W/m²). Optimales Startfenster damit ~12–15 h ablesbar.

### ADR-0022 — Tages-Timeline: 'wann starten?' + Wind-Zerstörung (Kernfragen-Synthese)
**Status:** akzeptiert (2026-06-30)
**Kontext:** des Autors Kernfragen: wann starten, wo Spots tageszeitlich, wie Wind-Versatz/-Zerstörung.
**Entscheidung:** `daytimeline.py` aggregiert über den Tag: w*(t) (Median Hotspots, mit z_i(t)-Band +
realem Q_H(t)), z_i(t), Wind_BL(t) @2500 m, Scherung |V_top−V_10m|, Zerstörungs-Flag (Wind > 7 m/s
≈ 25 kt), XC(t) (soaringmeteo-Blend). `optimal_window` = brauchbare, hoch-XC Zeiten. 4-Panel-Diagramm
(soaringmeteo-Meteogramm-Stil). „Wo tageszeitlich" beantworten die zeitaufgelösten Drift-Karten.
**Begründung:** Kombiniert die jetzt vorhandenen Bausteine (z_i(t), w*, Wind, XC) zur direkten
Handlungsempfehlung. Schwellen recherche-gestützt (w* 1.5/2.0; 25 kt Zerstörung; soaringmeteo-µ).
**Verifikation (30.06.):** Startfenster **12–16 h, Bestzeit ~14:00**, max XC 65 %, max w* 1.64 m/s;
keine BL-Wind-Zerstörung, aber Scherung steigt spätnachmittags Richtung Schwelle — physikalisch
stimmig und als `day_timeline.png` ablesbar.

### ADR-0023 — Vegetationskanten als zusätzliche Ablösepunkte
**Status:** akzeptiert (2026-06-30)
**Kontext:** des Autors Hinweis: Wald↔Nichtwald-Grenzen sind Ablösekanten; fällt eine Waldgrenze mit
einem Geländebruch zusammen, ist die Ablösung deutlich wahrscheinlicher (Albedo-/Rauhigkeits-/
Feuchtesprung).
**Entscheidung:** `landcover.forest_edge` (bool-Feld der Wald-Grenzen, 1 Zelle dilatiert). Im
`_slope_follow`-Release-Kriterium gilt an einer Vegetationskante eine reduzierte Konvexitäts-Schwelle
(`d1_veg_edge_curv_factor=0.4`) → schwächere Konvexität löst dort schon ab.
**Begründung:** Direkt am vorhandenen curvature-Release angedockt; nutzt die LFI-Land-Cover-Klassen.
**Annahmen:** Faktor 0.4 (heuristisch); Wald = Nadel/Laub/Misch.
**Verifikation:** Lauf stabil, 34/34 Tests; Hotspot-Release-Versatz ~unverändert (Hotspots liegen schon
auf Graten), greift v. a. bei Netz-Seeds in Waldhängen — wie beabsichtigt.

### ADR-0024 — Plot-Politik: helles Relief, km/h-Wind, Streamline-Halo
**Status:** akzeptiert (2026-06-30, Autor-Feedback)
**Kontext:** Overlays/Streamlines kontrastierten schlecht gegen das dunkle Hillshade; Wind in m/s
ist für Piloten weniger aussagekräftig.
**Entscheidung:** `viz.draw_hillshade` (zentral): Schummerung in einen hellen Graukeil [0.6, 1.0]
gestaucht (kein Schwarz) → farbige Felder (viridis/inferno, Alpha ~0.8) knallen, Relief bleibt
lesbar. Projektweit in allen Plot-Funktionen genutzt. Wind durchgängig in **km/h** (Vario/w* bleibt
m/s). Streamlines mit dezentem dunklem Halo (path_effects) → sichtbar unabhängig von der cividis-Farbe.
**Verifikation:** Feld-Bilder (kk7/Q_H/XC/D0) deutlich kontrastreicher; Wind-Subplots gut lesbar,
Zerstörungs-Schwelle 25 km/h. 34/34 Tests, voller Lauf sauber.

### ADR-0025 — Retrospektive Prognose-Validierung (eigene Flugtage × historisches Wetter)
**Status:** akzeptiert (2026-06-30)
**Kontext:** des Autors Idee: lange Flüge finden → Wetter davor rekonstruieren → hätte das Modell den
guten Tag erkannt? ICON-CH hat kein Archiv; ERA5-Reanalyse/Analyse ist der saubere Ersatz.
**Entscheidung:** `nwp_historical.py` holt pro vergangenem Datum (a) das Vertikalprofil+Wind+CAPE via
historical-forecast-api (icon_seamless, Druckniveaus, ab ~2024) → Sondierungs-Äquivalent für
`analyze_sounding`, und (b) ERA5-Strahlung/Bewölkung via archive-api. `validation/retrospective.py`
rechnet je Flugtag eine leichtgewichtige Tagesgüte (w*-Peak, z_i-Peak via cbl_timeseries, XC) an einem
Referenzpunkt und korreliert (Spearman) mit der Flugqualität (max. Thermik-Top/Höhengewinn/Dauer aus
den eigenen IGC). CLI-Flag `--retrospective`.
**Begründung:** Reanalyse-Strahlung + Analyse-Profil = „perfekte Prognose"/Vorhersagbarkeits-Obergrenze
(trennt Modell-Physik-Fehler von NWP-Prognosefehlern). Reproduzierbar, gecacht pro Datum.
**Annahmen/Lehren:** Referenzhöhe = mediane Steigflug-**Basis ~1600 m** (NICHT Gipfel 2200 m — sonst
wird w* an gedeckelten Tagen künstlich genullt, Diagnose-Befund); nur echte Thermikflüge (≥1 Steig-
segment); Flug-Top als Tagesstärke-Proxy (max_alt_gain ist start­höhen-verzerrt).
**Verifikation (n=8 eigene Thermiktage):** **z_i-Peak ist der beste Prädiktor** (Spearman +0.48 vs.
Thermik-Top, +0.52 vs. Höhengewinn); XC/w* korrelieren moderat mit der Flugdauer (+0.33…0.43); ERA5-
Strahlung war an allen Tagen hoch (826–896 W/m²) → kein Strahlungs-Artefakt. **Kleines Sample →
indikativ, nicht konklusiv.** Statistische Aussagekraft braucht mehr Flüge — WeGlide-API (offen) +
XContest (Metadaten-Scraping, ToS) sind der recherchierte, dokumentierte Erweiterungspfad.

### ADR-0026 — kk7 zeitgefiltert (jul_04/07/10): Zeitabgleich hilft NICHT (Terrain dominiert)
**Status:** akzeptiert (2026-06-30)
**Kontext:** kk7-Heatmap auch tageszeitlich (Morgen/Mittag/Abend) holen und gegen das Modell der
passenden Uhrzeit prüfen.
**Entscheidung/Test:** kk7 jul_04/07/10 (cache via category-Param) gegen das *momentan aktive*
Modellquellfeld D0×norm(Q_H(t)) bei ~11/13/17 h (heatmap_metrics, 250-m-geglättet); je 1 Heatmap-Plot.
**Befund:** Zeitabgleich verbessert NICHT — AUC Modell-aktiv vs. statisch D0: Morgen 0.52/0.58,
Mittag 0.60/0.66, Abend 0.41/**0.72**. Die statische Terrain-D0 ist zu jeder Tageszeit besser; das
Q_H(t)-Gewichten (abends W-Hänge) korreliert sogar negativ.
**Lesart:** Thermik-*Orte* (kk7) sind terrain-kontrolliert und über den Tag ~invariant; die Tageszeit
ändert v. a. *Stärke/Decke* (Timeline/Drift), nicht die Quell-*Lage* — auf kk7-/Gitter-Auflösung.
Konsistent mit den verworfenen Kanten-/Lee-Luv-Termen: Terrain-Geometrie trägt das Lage-Signal.
**Verifikation:** Reproduzierbar im Validierungslauf; 3 kk7-Zeit-Heatmaps als Plots.

### ADR-0027 — D1-Plumes in 3 Varianten (Hotspots / Netz / kk7-Heatmap)
**Status:** akzeptiert (2026-06-30, Autor-Wunsch)
**Kontext:** Bisher stiegen Plumes nur aus unseren Hotspots. Gewünscht: zusätzlich ein Netz mit vielen
Spuren und eine Variante, die aus der kk7-Heatmap seedet.
**Entscheidung:** `cli` erzeugt drei 3D-HTMLs — `d1_plumes_hotspots_3d` (Top-Hotspots),
`d1_plumes_grid_3d` (regelmässiges Netz, `grid_seeds`, ~2900 Spuren) und `d1_plumes_kk7_3d`
(`seeds_from_field` aus den kk7-Dichte-Top-Perzentilen, ~400 Spuren). `build_plume_3d` bündelt alle
Spuren in EINEN None-getrennten Scatter3d → effizient auch bei tausenden Spuren.
**Verifikation:** Alle drei gerendert; Netz = dichter Teppich aufsteigender, nach Höhe gefärbter
Säulen über dem ganzen Relief; kk7-Variante steigt aus den Dichtequellen entlang der Grate.

### ADR-0028 — XContest: keine API (Bot-401), Browser-Zugriff; Rekordtage als Validierung
**Status:** akzeptiert (2026-06-30)
**Kontext:** XContest als Quelle langer Flüge für die retrospektive Validierung.
**Befund (Browser-Inspektion + Test):** XContest hat **keine JSON-API** — die Flugtabelle ist
server-gerendert; die einzigen XHRs sind Karten-/Höhen-Tiles. Bot-`requests` werden mit **HTTP 401**
blockiert (Anti-Scraping); Zugriff nur über die eingeloggte Browser-Session (HTML). Kein automatischer
Scraper (blockiert + ToS). Aus dem Browser (Niesen 8 km, nach Punkten) habe ich die **Rekordtage**
abgelesen (14443 Flüge gesamt; Top 250–405 km).
**Entscheidung:** Kuratierte Rekordtag-Liste (`XCONTEST_BIGDAYS`, browser-quelliert) als komplementäres
Validierungs-Target: hätte das Modell diese Big-Days erkannt?
**Verifikation:** An 10 Rekordtagen (2024–26) Modell-XC median 67 %, aber Treffer gemischt: deutliche
**Misses** (18.06.26: 11 %, 20.07.24: 9 %) — dort ist z_i hoch, w* aber tief. Rebestätigt: **z_i ist
der robuste Prädiktor; die w*-doppelt-gewichtete XC-Formel rated einige Big-Days zu tief** (Region
würde eine z_i-stärkere Gewichtung verlangen). Erweiterung XContest-Massen-Daten: nur mit
Login-Session/Genehmigung, nicht als Bot.

### ADR-0029 — Die 3 Plume-Varianten zeitaufgelöst (Uhrzeit-Slider 11/13/15/18 h)
**Status:** akzeptiert (2026-06-30, Autor-Frage)
**Kontext:** Die 3 Varianten aus ADR-0027 nutzten das **Tagesmax-Q_H** und den **statischen
Sondierungswind** — also gerade NICHT tageszeitabhängig. Der Autor: „diese Plumes sind ja auch
zeitabhängig … wir bräuchten diese Plots dann jeweils für die üblichen Tageszeitpunkte." Korrekt:
Sonneneinstrahlung (→ w*, z_i) und Wind ändern sich im Tagesgang, also müssen es die Säulen auch.
**Entscheidung:** Die 3 Varianten werden in `timedrift.run_time_resolved` je Uhrzeit (11/13/15/18 h)
mit dem **momentanen** Antrieb gerechnet — `qh_t=heat.Q_H[idx]`, ICON-Wind(t) (`wf.griddize(h).uv`),
CBL-Wachstum `band_scale=cbl["growth"][idx]` (z_i(t)), Waldgrenzen als Ablöser. Statt 12 Einzeldateien
**ein HTML pro Variante mit Uhrzeit-Slider** (`build_plume_3d_timeslider`: ein statischer Relief-
Surface + ein Plotly-Frame je Stunde, `traces=[1]` aktualisiert nur die Säulen; gemeinsame Höhen-
Farbskala über alle Frames). Der statische 3-Varianten-Block in `cli._phase_b_d1` entfällt (Tagesmax-
Lauf bleibt nur als Drift-Raten-Logzeile + `d1_drift_map.png`).
**Netzdichte:** das 2D-Quiver bleibt fein (`drift_grid_spacing_m=150`); das 3D-Netz nutzt ein gröberes
`plume3d_grid_spacing_m=300` (~600 Spuren), damit 4 Frames × Spuren als ein HTML handlich bleiben
(8 Spuren × 4 Frames ≈ 5 MB; 600 × 4 entsprechend grösser, aber je Variante eine Datei).
**Verifikation:** Slider mit synthetischen Spuren gebaut (Frames + alle 4 Uhrzeit-Schritte im HTML);
Testsuite 34 grün; End-to-End-Lauf rendert `d1_plumes_{hotspots,grid,kk7}_3d.html` mit Slider.

### ADR-0030 — Verworfene D0-Terme (Kanten/Triggerlinie + Lee/Luv) per Cross-Validation
**Status:** akzeptiert (2026-06-30) — formalisiert, was bisher nur in der Bilanz-Prosa stand
**Kontext:** Zwei plausible Zusatzterme fürs statische Quellfeld D0 wurden getestet: (a) ein
Triggerlinien-/Kanten-Term (Geländebrüche), (b) ein Lee/Luv-Wind-Expositions-Term (Luv = Hang zur
Windquelle der Arbeitsschicht).
**Entscheidung:** **Beide nicht ins statische D0 aufnehmen.** (a) Kanten-Term: kein Skill. (b) Lee/Luv:
hebt die IGC-AUC stark (0.712→0.784 @0.3w), die **unabhängige kk7-AUC aber nur marginal**
(0.711→0.721) und kippt bei mehr Gewicht — d. h. eine Einzeltag-Windrichtung **überanpasst** an
des Autors (gleichtägige) Flüge und generalisiert nicht. Lee/Luv gehört in eine **tagesdynamische**
Variante (mit der jeweiligen Prognose-Windrichtung), nicht ins statische Proxy.
**Lehre/Methodik:** kk7 (viele Tage/Winde) ist der **Überanpassungs-Wächter** neben den eigenen IGC —
ein Term muss gegen BEIDE Sets bestehen. Festgehalten auch in [[project-thermalmodel-findings]].
**Verifikation:** Cross-Validation IGC vs. kk7 (s. o.); D0 bleibt edge_w=0, lee_w=0.

### ADR-0031 — Validierungs-Datenweg: WeGlide-API statt XContest-Scraping
**Status:** akzeptiert (2026-06-30, Autor-Entscheid)
**Kontext:** Für mehr Validierungsflüge (n=8 ist klein) wollte der Autor die Top-Quantil-Flüge im
Gebiet samt IGC. Erste Idee: systematischer XContest-Download.
**Entscheidung:** XContest **nicht** systematisch herunterladen (keine API, Bot→HTTP 401, ToS,
Konto-Risiko, Fremd-IGC gated — s. ADR-0028). Stattdessen **WeGlide offene API**
(`api.weglide.org/v1`, ~60 Req/Tag, Browser-UA): Flüge nach Region/Bewertung filtern, Metadaten + IGC
pro Flug — ToS-sauber, liefert Tracks für die räumliche Co-Lokalisation gegen die Hotspots. XContest
bleibt: nur Metadaten (Datum/Punkte) aus der eingeloggten Browser-Session oder manueller Einzel-Export.
**Befund (2026-06-30, API reverse-engineered):** `api.weglide.org/v1` ist offen — anonyme GET-Reads von
`/v1/flight` liefern JSON OHNE Key (der 60/Tag-Key gilt nur für die offizielle Developer-Nutzung).
Funktionierende Params: `skip`/`limit`, `order_by=-points`, **`airport_id_in=<ID>`** (Regionsfilter über
Flugplatz; `bbox`/`box`/`bounds`/`season`/`aircraft_class` werden still ignoriert). Suche = `POST /v1/search`
mit `{"search_items":[{"key":"name","value":...}],"documents":["airport"]}`. IGC: `/v1/flightdetail/{id}`
→ `igc_file.file` auf `https://weglidefiles.b-cdn.net/{path}`.
**ABER segelflug-zentriert:** Die Niesen-PG-Startplätze (Niederhorn/Frutigen/Beatenberg) existieren dort
NICHT; Geo läuft über Segelflugplätze. Im/um das Gebiet aktiv: Zweisimmen (ID 161540, 519 Flüge),
Thun (161531, 263), Saanen (161517, 196), Reichenbach (161516, ~ungenutzt). → WeGlide taugt als
SEGELFLUG-Quelle (Tagesgüte top; Steig-*Orte* hoch-verzerrt, da Segler höher/schneller), NICHT als
PG-Quelle für den Niesen.
**Verifikation/Status:** Strang **PAUSIERT** (der Autor, 2026-06-30) — noch NICHTS implementiert. Offene
Entscheidung: (1) Segelflug-Client (Top-Punkte Zweisimmen/Thun/Saanen, IGC auf Domäne clippen → Steig-Orte
+ Tagesgüte), (2) nur Tagesgüte-Big-Days ergänzen, (3) PG-only via eigene IGC + manuelle XContest-Exporte.

### ADR-0032 — Memory im Repo (Spiegel-Hook) + Skill „wissenschaftliches-arbeiten"
**Status:** akzeptiert (2026-06-30, Autor-Wunsch)
**Kontext:** (1) Das projektübergreifende Memory lag nur lokal in `~/.claude/.../memory/` (nicht
versioniert/teilbar wie die ADRs). (2) Die in dieser Session wiederholt angewandte Arbeitsweise
(plausibilisieren → validieren → generalisieren → festhalten → committen → ehrlich berichten) sollte
wiederverwendbar werden.
**Entscheidung:**
- **Hook** `.claude/hooks/mirror_memory.py` (PostToolUse, Matcher `Write|Edit`, registriert in
  `.claude/settings.json`): erkennt Schreibvorgänge auf `…/.claude/.../memory/*.md` an der Tool-Payload
  (`tool_input.file_path`) und spiegelt sie automatisch nach `.claude/agent-memory/` im Repo →
  Memory ist versioniert wie die ADRs, ohne dass ich es manuell tun muss. Stdlib-Python, Exit 0 = still.
- **Skill** `.claude/skills/wissenschaftliches-arbeiten/SKILL.md` (projekt-lokal, committet, via
  `/wissenschaftliches-arbeiten` invokebar): kodiert den Loop inkl. „≥2 unabhängige Datensätze",
  „nur Generalisierendes behalten", „nie pushen" und „adversarial verifizieren / ehrlich berichten".
**Caveat:** Der Hook läuft bei jedem Write/Edit (Python-Start ~150 ms) — selbst-filternd per Pfad.
Memory enthält Personenbezug (`user-…`) → Repo privat halten. Lokale Memory-Ablage bleibt die
auto-geladene Quelle; `.claude/agent-memory/` ist die versionierte Spiegelung.
**Verifikation:** Hook gegen 3 Szenarien getestet (Memory-File → gespiegelt; Nicht-Memory → No-op;
leeres stdin → Exit 0). 7 Memory-Dateien initial gespiegelt. Hook-/Skill-Mechanik gegen die
offizielle Claude-Code-Doku abgeglichen (claude-code-guide).

### ADR-0033 — Public-Release-Vorbereitung (Lizenzen, Struktur, Privacy)
**Status:** akzeptiert (2026-06-30, Autor-Wunsch: Repo öffentlich auf GitHub)
**Kontext:** Das Repo soll öffentlich werden. Recherche (Workflow) klärte Datenquellen-Lizenzen +
Privacy-Risiken. Befund: Code-Deps alle permissiv; Daten werden zur Laufzeit geholt (nur Attribution,
keine Massen-Redistribution); persönliche Daten (eigene IGC, Agent-Memory-Profil) waren das echte Risiko.
**Entscheidungen:**
- **Lizenz:** Code **Apache-2.0** (`LICENSE`/`NOTICE`); Doku/Ideen (README, `docs/`, dieses Journal)
  **CC BY 4.0**; `CITATION.cff` — Intention des Autors: „wer die Ideen nutzt, muss es deklarieren".
- **Attribution:** `ATTRIBUTION.md` mit den wörtlich geforderten Quellenangaben je Quelle
  (©swisstopo; BAFU/WSL; Quelle: MeteoSchweiz; Weather data by Open-Meteo.com; DWD; Copernicus ERA5).
- **kk7 ist CC BY-NC-SA 4.0** (NC+SA): KEINE kk7-Tiles/Rohdaten und keine kk7-abgeleiteten Bild-Artefakte
  im Repo — nur aggregierte Metriken mit Attribution; so bleibt der Code sauber Apache-2.0.
- **Privacy:** `source/igc/` (32 private Tracks) + `.claude/agent-memory/` gitignored/untracked;
  stattdessen **5 längste Tracks** anonymisiert (Geräte-Serials/Fingerprints entfernt, Pilotname bleibt —
  Autor ist einverstanden) und nach `examples/data/igc/` umbenannt. Klarname in Journal/Code-Labels
  neutralisiert („der Autor/Pilot"); in IGC-Headern + LICENSE/CITATION bleibt der Name (gewollt).
  **History: frisch** (öffentliches Repo aus bereinigtem Stand, 1 Initial-Commit — keine Altdaten).
- **Reversal von ADR-0032 (für public):** `.claude/agent-memory/` wird NICHT mehr versioniert
  (Personenbezug). Hook/Skill bleiben (lokaler Nutzen); der Mirror ist jetzt gitignored.
- **Struktur:** Pakete/Launcher bleiben am Ort (kein Massen-Move); neu Top-Level-README (beide
  Use-Cases), `examples/` (Inputs + kuratierte Outputs), `pyproject.toml`, `docs/`-Index; entfernt
  `next.md`/`*.code-workspace`/STAC-Export-CSVs; Root-KML → `examples/data/domain_niesen_frutigen.kml`
  (einzige Code-Anpassung: `config.py` Default).
**Verifikation:** Sample-IGC parsen nach Sanitisierung identisch (gleiche Fix-Zahlen); `git ls-files`
zeigt nur die 5 Samples + kein agent-memory; Hangabstand-Demo auf dem 25-km-Track erzeugt.

## Nachtlauf-Bilanz (2026-06-30 früh)
**Fertig & committet:** Phase A (ideal+real Wärmebild, A5b ICON-Wolken), kumulative Energie-Stände,
Aspect-Bugfix, volle Domäne, Validierungs-Harness (IGC-Steigflüge + kk7, AUC/Hit-Rate),
**D0** (validiertes Quell-Proxy, AUC 0.71), **Phase B** (z_i/w*/Ceiling), **D1** (Lagrange-Plume).
Durchgehend web-plausibilisiert; ADR-0001..0015.
**Phase C (Teil) ergänzt:** anabatische Hangaufwind-Parametrisierung (`valleywind.py`, ADR-0016) in
D1 eingeblendet → Drift-Rate 180→**70 m/min**, trifft die IGC-Referenz (74) praktisch exakt.
Auch reproduzierbarer Launcher (`thermal.py`/`cli.py`), README und 8 Physik-Tests (inkl. Aspect-
Regression) ergänzt.
**Offen (Fernziel):** Lee/Luv-Term in D0; gelöstes (statt parametrisiertes) Windfeld; D2
(Cellular-Automata/Massfluss); **D3–D5 LES** (microHH/PALM, braucht WSL2/GPU — bewusst nicht im
Nachtlauf). Reproduzierbarkeit: Phase B/D1 brauchen die Payerne-Sondierung
(`meteo/archive`, current-day) + ICON-Cache (Open-Meteo, tagesweise).
**Lee/Luv-Term für D0 getestet & verworfen (Cross-Validation):** Wind-Expositions-Term (Luv =
Hang zur Windquelle, Arbeitsschicht-Wind ESE 112°) hebt die IGC-AUC stark (0.712→0.784 @0.3w),
aber die unabhängige kk7-AUC nur marginal (0.711→0.721) und kippt bei mehr Gewicht (0.5w→kk7 0.703).
⇒ Eine **Einzeltag-Windrichtung überanpasst** an des Autors (gleichtägige) Flüge und generalisiert
nicht (kk7 = viele Tage/Winde). Wie der Kanten-Term **nicht ins statische D0 aufgenommen** — gehört
in eine tagesdynamische Variante (mit der jeweiligen Prognose-Windrichtung). Lehrt: kk7 als zweites
Set ist der Überanpassungs-Wächter.

**Wichtigste Erkenntnisse:** (1) Aspect-180°-Bug gefunden/behoben (hätte alles verfälscht).
(2) Terrain-Geometrie schlägt das Heizungs-Proxy in der Validierung (AUC 0.71 vs 0.66); Triggerlinien-
Term ohne Skill. (3) IGC- und kk7-Validierung stimmen überein (~0.66/0.71) → robust. (4) Modell ist
ein ehrliches statisches/kinematisches Proxy; >0.8-Güte und korrekter Drift brauchen dynamische
Prädiktoren bzw. LES.
