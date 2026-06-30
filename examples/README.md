# Examples

Small inputs + curated results, so that both use cases can be inspected and reproduced
without any preparation. Relief/weather/landcover are fetched from the open sources at run time
(see [`../ATTRIBUTION.md`](../ATTRIBUTION.md)).

## Inputs (`data/`)
- `igc/` — the **5 longest** of my own flights (device IDs removed), named by date + track length.
- `domain_niesen_frutigen.kml` — analysis polygon (Niesen/Frutigen) for the thermal modeling.

## Reproduce

```bash
# 1) Terrain clearance for one example track
python analyze.py examples/data/igc/2026-06-25_66km.igc

# 2) Thermal/meteo forecast over the example polygon
python thermal.py --kml examples/data/domain_niesen_frutigen.kml --skip-plume

# 3) Payerne radiosounding (data source for phase B), latest sounding
python meteo/radiosonde_payerne.py latest
```

## Bundled results (`output/`)
- `terrainclearance/` — `…_3d.png` (3D relief + flight track by terrain clearance), `…_map.html` (interactive
  map), `aggregate_clearance_kde.png` (flight comparison: time-in-terrain-clearance), `risk_over_time.png`,
  `…_events.csv`, `…_run.json`. Generated with `--png` (static PNGs via kaleido).
- `thermalmodel/` — `qh_ideal_daymax.png` (ideal sensible-heat-flux (Q_H) map), `day_timeline.png` ("when to launch?"),
  `drift_15h_grid.png` (wind drift of the thermals at 15 h), `hotspots.html` (interactive), `hotspots.csv`.

> The interactive HTML files are self-contained — open them locally in the browser. Large 3D plots
> (`…_3d.html`, plume slider) are intentionally **not** checked in; they are produced during your own run.
> kk7-derived images are intentionally absent (CC BY-NC-SA; see ATTRIBUTION.md).
