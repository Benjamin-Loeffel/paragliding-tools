# thermalmodel — solargetriebene Thermik-Modellierung (Niesen/Frutigen)

Modelliert die reale Sonneneinstrahlung im Tagesverlauf auf der 3D-Topografie, leitet daraus
den fühlbaren Wärmestrom (Thermik-Antrieb), Thermik-Hotspots, deren Stärke (w*) und Decke sowie
driftende Thermik-Säulen ab — validiert gegen eigene IGC-Steigflüge und thermal.kk7.ch.

Schwester-Paket zu `terrainclearance` (Geländeabstand) und `meteo` (Payerne-Sondierung) und nutzt
beide nach. **Entscheidungen + Begründungen + Annahmen:** siehe [`docs/thermalmodel-journal.md`](../../docs/thermalmodel-journal.md) (ADRs).

## Ausführen

```bash
python thermal.py                 # kompletter Ablauf
python thermal.py --skip-plume    # nur Phase A + Validierung
python thermal.py --date 2026-06-29 --out output/thermal
```

Erzeugt in `output/thermal/`: Wärmebilder (PNG/GeoTIFF, ideal + real + Differenz), kumulative
Energie-Stände (11/13/15/18 h, 2D + je 1 volles 3D-HTML), D0-Quell-Wahrscheinlichkeit (3D),
Hotspots (GeoJSON/CSV, + `hotspots_strength.csv` mit w*/Ceiling), Validierungskarte,
D1-Plumes (3 Varianten als 3D mit **Uhrzeit-Slider**), zeitaufgelöste Drifts + Wind-Traces,
ICON-Wolken-Tagesgang.

## Pipeline

| Phase | Modul | Inhalt |
|---|---|---|
| **A0/A1** | `domain`, `grids`, `terrain_derivs` | KML → 20 m-LV95-Gitter; swissALTI3D-DTM → slope/aspect/curvature |
| **A2** | `horizon` | Horizontwinkel je Azimut + Sky-View-Factor (gecacht) |
| **A3–A5** | `solar`, `irradiance` | pvlib Sonnenstand + Ineichen-Klarhimmel, Einfallswinkel, Schatten → G_clear(t) |
| **A5b** | `nwp` | ICON-CH1-Wolken (Open-Meteo) → Dämpfung f_dir/f_dif/f_ghi → **reales** Wärmebild |
| **A6/A7** | `landcover`, `heating` | Waldmischungsgrad → Albedo/f_H; Q_H = f_H·(1−albedo)·G; Tagesmax + Energie |
| **A8** | `hotspots` | Score (Q_H+Konvexität+Aspekt+Slope) → Top-N Hotspots |
| **D0** | `buoyancy` | validiertes Quell-Wahrscheinlichkeitsfeld (datengetrieben gewichtet) |
| **B** | `boundarylayer` | Sondierung → w*/Ceiling je Hotspot + **z_i(t)-Tagesgang** (CBL-Encroachment) |
| **D1** | `plume` | Zweiphasige Plume: hangfolgend → **Ablösung** (Konvexität/Grat/**Waldgrenze**) → freier Drift |
| **C** | `valleywind`, `wind` | anabatischer Hangaufwind + ICON-Windfeld (icon_seamless, Druckniveaus) |
| **D1-t** | `timedrift` | zeitaufgelöste Drifts (11/13/15/18 h): je 2 Karten + Wind-Traces (1×5 Höhen, km/h) + **3 Plume-3D-Varianten (Hotspots/kk7/Netz) als Uhrzeit-Slider** |
| **XC** | `xcpotential` | XC-Flugpotenzial (Tagesgüte 0–100 %, soaringmeteo-Stil) |
| **Tag** | `daytimeline` | **„Wann starten?"**: w*/z_i/Wind/Scherung/XC über den Tag + Startfenster |
| **Val.** | `validation/` | IGC-Steigflüge + kk7-Hotspots **+ kk7-Heatmap** → verschiebungstolerante Hit-Rate/AUC |
| **Retro** | `validation/retrospective` | retrospektive Prognose-Skill: eigene Flugtage × historisches Wetter (ERA5/ICON) |

## Datenquellen (alle frei)

- **Relief:** swissALTI3D (swisstopo STAC) — via `terrainclearance`.
- **Wald Nadel/Laub:** BAFU/LFI-Waldmischungsgrad (10 m, EPSG:2056).
- **Wolken/Strahlung:** ICON-CH1 via Open-Meteo (`models=meteoswiss_icon_ch1`, GRIB-frei).
- **Sondierung:** Payerne (MeteoSwiss OGD) — via `meteo/`.
- **Validierung:** eigene IGC (`source/igc`) + thermal.kk7.ch (offene REST-API).

## Ergebnisse (Modelltag 2026-06-30; Phase-A-Zahlen vom Referenzlauf 29.06.)

- **Reales Wärmebild:** 99 % bewölkt → Q_H-Tagesenergie ideal→real median 2669→1467 Wh/m² (~45 % Wolkenverlust).
- **Validierung** (verschiebungstolerant, gegen Zufall): Phase-A-Score AUC **0.66**, **D0 0.71**
  (IGC ≈ kk7 → robust). Lift ×2.2–2.4 @300 m. Terrain-Geometrie trägt das Signal; ein
  Triggerlinien-Term hatte keinen Skill (verworfen).
- **Phase B:** w* median **1.56 m/s** (max 2.24), Ceiling ~3200–3600 m AMSL — plausibel.
- **D1 + Phase C:** anabatischer Hangaufwind bringt die Drift-Rate auf **70 m/min ≈ IGC 74**.
  Ablöse-Modell: Hotspots liegen schon auf konvexen Graten (Release-Versatz median 40 m).
- **Zeitaufgelöst:** Drift 11→15 h steigend (Wind 0.9→1.6 m/s), 18 h Kollaps (schwache Heizung);
  Drift-Pfeile decken sich mit den ICON-Wind-Streamlines (visueller Abgleich).
- **XC-Potenzial:** median 59 %, hohe sonnige Grate ~100 %. soaringmeteo bestätigt unser w*
  (ihr hartcodierter Median 1.55 = unsere 1.56).
- **z_i(t)/„Wann starten":** CBL wächst, bricht ~13–14 h durch die Inversion, w* peakt ~14:00 →
  **optimales Startfenster 12–16 h**. Drifts diurnal: morgens kurz (flache CBL), 15 h max, abends Kollaps.
- **kk7-Heatmap** (kontinuierlich, verschiebungstolerant): D0 Spearman 0.26/AUC 0.66 vs. Phase-A-Score
  0.05/0.55; Zeitabgleich (jul_04/07/10) verbessert NICHT → Thermik-*Orte* terrain-kontrolliert.
- **Retrospektive Validierung** (`--retrospective`, eigene Flugtage × ERA5/ICON-Historie): z_i-Peak
  bester Prädiktor (Spearman +0.48 vs. Thermik-Top); n=8 → indikativ, mehr Flüge (WeGlide/XContest) offen.
- **Plot-Politik:** nur Sequential-Maps (viridis Standard, inferno Energie, cividis Wind), helles
  Relief für Kontrast, Wind in km/h.

Ausgaben u. a.: `qh_*` (Wärmebilder), `energy_3d*.html`, `d0_thermal_source_3d.html`,
`d1_plumes_{hotspots,grid,kk7}_3d.html` (3D-Plumes mit **Uhrzeit-Slider** 11/13/15/18 h),
`d1_drift_map.png` (Tagesmax-Referenz), `drift_HHh_points.png`/`drift_HHh_grid.png`,
`wind_traces_HHh.png`, `xc_potential.png`, `validation_map.png`, `hotspots*.{csv,geojson}`.

## Grenzen & Nächstes

- Statisches/kinematisches Proxy: AUC ~0.7 ist literaturtypisch; **>0.8 braucht dynamische
  Prädiktoren** (Tageswetter, Wind, Konvergenz).
- Sondierung ist Tiefland-Punkt (Payerne) → Bergthermik nur näherungsweise.
- ICON/Sondierung nur ~24 h verfügbar → Tages-Pulls gecacht; Validierung ist klimatologisch.
- **Fernziel:** Phase C (dedizierte Talwind-Parametrisierung, Lee/Luv), D2 (Massfluss/CA),
  **D3–D5 LES** (microHH/PALM, WSL2/GPU).

Abhängigkeiten: `pip install -e .[thermal]` (definiert in `pyproject.toml`).
