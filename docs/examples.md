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
- `terrainclearance/` — **two comparison flights** as interactive 3D (`2026-06-25_66km_3d.html`,
  `2026-06-26_60km_3d.html` — relief + flight track coloured by terrain clearance) and their
  `aggregate_clearance_kde.html` (time-in-terrain-clearance, the two flights side by side); plus
  static `…_3d.png` / `aggregate_clearance_kde.png` / `risk_over_time.png`, `…_events.csv`,
  `…_run.json`. Generated with `--png` (static PNGs via kaleido).
- `thermalmodel/` — the step-by-step narrative figures (see [thermal-step-by-step.md](thermal-step-by-step.md)):
  `relief.png`, `aspect_slope.png`, `qh_ideal_daymax.png`, `qh_real_daymax.png` + `qh_diff_energy.png`
  (ideal→real), `wind_traces_15h.png`, `drift_15h_grid.png`, `d1_plumes_grid_3d.png` (drifting plumes
  ≈15 h), plus `day_timeline.png` ("when to launch?") and `hotspots.csv`. **Interactive:**
  `landcover_3d.html` (land cover on the relief), `energy_3d_ideal_slider.html` /
  `energy_3d_real_slider.html` (cumulative Q_H energy over the day, time slider),
  `d1_plumes_grid_3d.html` (drifting plumes, time slider) and `hotspots.html`.

> The interactive HTML files are self-contained — open them locally in the browser. The other per-time
> 3D outputs (`energy_3d_bis*.html`, `d0_thermal_source_3d.html`, the hotspots/kk7 plume variants) are
> produced during your own run. kk7-derived images are intentionally absent (CC BY-NC-SA; see ATTRIBUTION.md).
