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
- `terrainclearance/` — `…_3d.png` (3D-Relief + Flugspur nach Hangabstand), `…_map.html` (interaktive
  Karte), `aggregate_clearance_kde.png` (Flugvergleich: Zeit-im-Hangabstand), `risk_over_time.png`,
  `…_events.csv`, `…_run.json`. Erzeugt mit `--png` (statische PNGs via kaleido).
- `thermalmodel/` — die schrittweisen Erzählfiguren (siehe [`src/thermalmodel/README.md`](thermal-step-by-step.md)):
  `relief.png`, `aspect_slope.png`, `landcover_3d.png`, `qh_ideal_daymax.png`, `qh_real_daymax.png` +
  `qh_diff_energy.png` (ideal→real), `wind_traces_13h.png`, `drift_15h_grid.png`, `d1_plumes_grid_3d.png`
  (driftende Plumes ≈15 h); zusätzlich `day_timeline.png` ("Wann starten?") sowie die interaktiven
  `hotspots.html` und `d1_plumes_hotspots_3d.html` (Tageszeit-Schieberegler). `hotspots.csv`.

> Die interaktiven HTML-Dateien sind eigenständig — öffne sie lokal im Browser. Nur der (kleinere)
> Hotspots-Plume-Schieberegler ist eingecheckt; die Grid-/kk7-Plume-Varianten und das übrige 3D-HTML werden
> während deines eigenen Laufs erzeugt. kk7-abgeleitete Bilder fehlen absichtlich (CC BY-NC-SA; siehe ATTRIBUTION.md).
