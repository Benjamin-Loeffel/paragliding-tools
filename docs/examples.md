# Examples

Small inputs + curated results, so that both use cases can be inspected and reproduced
without any preparation. Relief/weather/landcover are fetched from the open sources at run time
(see [`background.md`](background.md)).

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
- `thermalmodel/` — the step-by-step narrative figures (see [`src/thermalmodel/README.md`](thermal-step-by-step.md)):
  `relief.png`, `aspect_slope.png`, `landcover_3d.png`, `qh_ideal_daymax.png`, `qh_real_daymax.png` +
  `qh_diff_energy.png` (ideal→real), `wind_traces_13h.png`, `drift_15h_grid.png`, `d1_plumes_grid_3d.png`
  (drifting plumes ≈15 h); plus `day_timeline.png` ("when to launch?") and the interactive
  `hotspots.html` and `d1_plumes_hotspots_3d.html` (time-of-day slider). `hotspots.csv`.

> The interactive HTML files are self-contained — open them locally in the browser. Only the (smaller)
> hotspots plume slider is checked in; the grid/kk7 plume variants and the other 3D HTML are produced
> during your own run. kk7-derived images are intentionally absent (CC BY-NC-SA; see ATTRIBUTION.md).
