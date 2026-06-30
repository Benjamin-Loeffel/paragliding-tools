# Beispiele

Kleine Eingaben + kuratierte Ergebnisse, damit man beide Use-Cases ohne Vorbereitung ansehen
und reproduzieren kann. Relief/Wetter/Landcover werden beim Lauf aus den offenen Quellen geholt
(siehe [`../ATTRIBUTION.md`](../ATTRIBUTION.md)).

## Eingaben (`data/`)
- `igc/` — die **5 längsten** eigenen Flüge (Geräte-IDs entfernt), benannt nach Datum + Streckenlänge.
- `domain_niesen_frutigen.kml` — Analyse-Polygon (Niesen/Frutigen) für die Thermik-Modellierung.

## Reproduzieren

```bash
# 1) Hangabstand für einen Beispieltrack
python analyze.py examples/data/igc/2026-06-25_66km.igc

# 2) Thermik-/Meteo-Prognose über das Beispiel-Polygon
python thermal.py --kml examples/data/domain_niesen_frutigen.kml --skip-plume

# 3) Payerne-Radiosonde (Datenquelle für Phase B), aktuellste Sondierung
python meteo/radiosonde_payerne.py latest
```

## Mitgelieferte Ergebnisse (`output/`)
- `terrainclearance/` — `…_3d.png` (3D-Relief + Flugspur nach Hangabstand), `…_map.html` (interaktive
  Karte), `aggregate_clearance_kde.png` (Flugvergleich: Zeit-in-Hangabstand), `risk_over_time.png`,
  `…_events.csv`, `…_run.json`. Erzeugt mit `--png` (statische PNGs via kaleido).
- `thermalmodel/` — `qh_ideal_daymax.png` (ideales Wärmebild), `day_timeline.png` („wann starten?"),
  `drift_15h_grid.png` (Wind-Drift der Thermik um 15 h), `hotspots.html` (interaktiv), `hotspots.csv`.

> Die interaktiven HTML sind self-contained — lokal im Browser öffnen. Grosse 3D-Plots
> (`…_3d.html`, Plume-Slider) sind bewusst **nicht** eingecheckt; sie entstehen beim eigenen Lauf.
> kk7-abgeleitete Bilder fehlen bewusst (CC BY-NC-SA; siehe ATTRIBUTION.md).
