# paragliding-tools

Two tools for paraglider pilots in Switzerland, both built on open geodata and the
high-resolution swisstopo topography:

1. **Terrain clearance** — the minimum **3D terrain clearance** along an IGC flight track
   (incl. forest/buildings, GPS uncertainty, distribution over the flight time).
2. **Thermal/meteo forecast** — **solar-driven thermal modelling**: real
   irradiance over the diurnal cycle → heat flux → hotspots, (convective) boundary layer (w\*/z_i) and
   drifting thermal columns, validated against the author's own flights and thermal.kk7.ch.

All geo/weather data is fetched **at runtime** from open sources (nothing large in the repo).

---

## Terrain clearance

For **every point of a flight track**, the shortest 3D distance to the terrain **and** to the
vegetation/building surface — finds critical approaches, estimates the GPS-induced
uncertainty (Monte Carlo) and evaluates the distribution over the flight time.

| 3D relief + flight track (coloured by terrain clearance) | Flight comparison: time-in-terrain-clearance (density + cumulative) |
|---|---|
| ![3D terrain clearance](examples/output/terrainclearance/2026-06-25_66km_3d.png) | ![Flight comparison](examples/output/terrainclearance/aggregate_clearance_kde.png) |

```bash
python analyze.py examples/data/igc/2026-06-25_66km.igc
```

Produces interactive HTML that can be opened offline: map (track coloured by clearance), 3D relief
with flight track, barogram with uncertainty band, clearance distribution.
**Example outputs:** [`examples/output/terrainclearance/`](examples/output/terrainclearance/)
(interactive `…_map.html` + 3D/comparison PNGs + `risk_over_time.png`) · **Details & methodology:**
[`docs/terrainclearance.md`](docs/terrainclearance.md).

## Thermal & meteo forecast

Models the solar irradiance on the 3D topography over the day, derives the sensible
heat flux (thermal drive), hotspots, their strength/ceiling and drifting thermal columns —
and answers **when to launch, where the spots are, how strongly the wind shifts/destroys them**.

| ideal heat-input map (daily max) | "When to launch?" — thermal diurnal cycle |
|---|---|
| ![Sensible-heat-flux map](examples/output/thermalmodel/qh_ideal_daymax.png) | ![Diurnal cycle](examples/output/thermalmodel/day_timeline.png) |

![Thermal drift 15:00](examples/output/thermalmodel/drift_15h_grid.png)

*Thermal drift at 15:00 (150 m grid) — how strongly the wind shifts/shears the rising columns.*

```bash
python thermal.py --kml examples/data/domain_niesen_frutigen.kml --skip-plume
```

**Example outputs:** [`examples/output/thermalmodel/`](examples/output/thermalmodel/)
(`hotspots.html`, PNGs) · **Pipeline & decisions:** [`src/thermalmodel/README.md`](src/thermalmodel/README.md)
and the ADR journal [`docs/thermalmodel-journal.md`](docs/thermalmodel-journal.md).

---

## Installation (Python 3.11+)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\python.exe -m pip install -e .[thermal]
# macOS/Linux:  .venv/bin/pip install -e .[thermal]
```

`rasterio`/`pyproj` bundle GDAL/PROJ as wheels — no separate GIS setup needed. Without
`[thermal]` the terrain-clearance part runs; the extra pulls in `pvlib`/`metpy`/`scikit-image` for the
thermal modelling. Tests: `python -m pytest tests -q`.

## Data sources & licences

Fetched at runtime, each under its own licence with an attribution requirement — full list with the
**verbatim required attributions** in [`ATTRIBUTION.md`](ATTRIBUTION.md):

- **swissALTI3D / swissSURFACE3D** (relief) — `©swisstopo`
- **Forest mixture degree LFI** (landcover) — BAFU/WSL, opendata.swiss
- **Payerne radiosonde / ICON-CH** — `Quelle: MeteoSchweiz`, CC BY 4.0
- **Open-Meteo** (access to ICON/ERA5) — `Weather data by Open-Meteo.com`, CC BY 4.0;
  underlying **DWD ICON** and **Copernicus ERA5** (each CC BY 4.0)
- **thermal.kk7.ch** (validation) — CC **BY-NC-SA** 4.0 (only derived metrics, no raw data/tiles in the repo)

## Licence

- **Code:** Apache-2.0 — see [`LICENSE`](LICENSE) / [`NOTICE`](NOTICE).
- **Documentation, figures, described methodology** (README, `docs/`, ADR journal): **CC BY 4.0** —
  anyone building on these ideas/texts please name the author and cite the repo
  ([`CITATION.cff`](CITATION.cff)).

## Repo structure

```
analyze.py / thermal.py        Launchers for the two use cases
src/terrainclearance/          Terrain-clearance package
src/thermalmodel/              Thermal modelling (+ validation/)
meteo/                         Payerne radiosonde (data source for phase B)
examples/data/                 Example inputs (5 tracks + domain KML)
examples/output/               curated example results
docs/                          Methodology (terrainclearance.md) + ADR journal
tests/                         pytest suite
```
