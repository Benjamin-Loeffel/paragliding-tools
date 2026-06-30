# Beispiele

Kleine Eingaben + kuratierte Ergebnisse, sodass beide Anwendungsfälle ohne jegliche
Vorbereitung inspiziert und reproduziert werden können. Relief/Wetter/Landcover werden zur Laufzeit
aus den offenen Quellen geladen (siehe [`background.md`](background.md)).

## Eingaben (`data/`)
- `igc/` — die **5 längsten** meiner eigenen Flüge (Geräte-IDs entfernt), benannt nach Datum + Spurlänge.
- `domain_niesen_frutigen.kml` — Analyse-Polygon (Niesen/Frutigen) für die Thermik-Modellierung.

## Reproduzieren

```bash
# 1) Hangabstand für eine Beispiel-Flugspur
python analyze.py examples/data/igc/2026-06-25_66km.igc

# 2) Thermik-/Meteo-Vorhersage über dem Beispiel-Polygon
python thermal.py --kml examples/data/domain_niesen_frutigen.kml --skip-plume

# 3) Payerne-Radiosondierung (Datenquelle für Phase B), neueste Sondierung
python meteo/radiosonde_payerne.py latest
```

## Mitgelieferte Ergebnisse (`output/`)
- `terrainclearance/` — **zwei Vergleichsflüge** als interaktives 3D (`2026-06-25_66km_3d.html`,
  `2026-06-26_60km_3d.html` — Relief + Flugspur nach Hangabstand eingefärbt) und ihr
  `aggregate_clearance_kde.html` (Zeit-im-Hangabstand, die zwei Flüge nebeneinander); zusätzlich
  statisch `…_3d.png` / `aggregate_clearance_kde.png` / `risk_over_time.png`, `…_events.csv`,
  `…_run.json`. Erzeugt mit `--png` (statische PNGs via kaleido).
- `thermalmodel/` — die schrittweisen Erzählfiguren (siehe [thermal-step-by-step.md](thermal-step-by-step.md)):
  `relief.png`, `aspect_slope.png`, `qh_ideal_daymax.png`, `qh_real_daymax.png` + `qh_diff_energy.png`
  (ideal→real), `wind_traces_15h.png`, `drift_15h_grid.png`, `d1_plumes_grid_3d.png` (driftende Plumes
  ≈15 h), zusätzlich `day_timeline.png` ("Wann starten?") und `hotspots.csv`. **Interaktiv:**
  `landcover_3d.html` (Bodenbedeckung auf dem Relief), `energy_3d_ideal_slider.html` /
  `energy_3d_real_slider.html` (kumulierter Q_H-Energieeintrag über den Tag, Zeitschieber),
  `d1_plumes_grid_3d.html` (driftende Plumes, Zeitschieber) und `hotspots.html`.

> Die interaktiven HTML-Dateien sind eigenständig — öffne sie lokal im Browser. Die übrigen
> tageszeit-aufgelösten 3D-Ausgaben (`energy_3d_bis*.html`, `d0_thermal_source_3d.html`, die
> hotspots-/kk7-Plume-Varianten) werden während deines eigenen Laufs erzeugt. kk7-abgeleitete Bilder
> fehlen absichtlich (CC BY-NC-SA; siehe ATTRIBUTION.md).
