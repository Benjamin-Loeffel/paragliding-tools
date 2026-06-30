# paragliding-tools

Two tools for paraglider pilots in Switzerland, both built on free open geodata and the
high-resolution swisstopo topography.

- **[Terrain clearance](terrain-clearance.md)** — the minimum **3D terrain clearance** along an IGC
  flight track (incl. forest/buildings, GPS uncertainty, distribution over the flight time).
- **[Thermals, step by step](thermal-step-by-step.md)** — **solar-driven thermal modelling**: real
  irradiance over the day → heat flux → hotspots, boundary layer (w\*/z_i) and drifting thermal columns.

All geo/weather data is fetched **at runtime** from open sources — see [Background](background.md).
Code on [GitHub](https://github.com/Benjamin-Loeffel/paragliding-tools).

## Terrain clearance

For every point of a flight track, the shortest 3D distance to the terrain **and** to the
vegetation/building surface — finds critical approaches, estimates the GPS-induced uncertainty
(Monte Carlo) and compares flights over the season.

| 3D relief + flight track (coloured by clearance) | Flight comparison (time-in-clearance) |
|---|---|
| ![3D terrain clearance](assets/terrainclearance/2026-06-25_66km_3d.png) | ![Flight comparison](assets/terrainclearance/aggregate_clearance_kde.png) |

→ details & methodology: **[Terrain clearance](terrain-clearance.md)**.

## Thermal & meteo forecast

Models the solar irradiance on the 3D topography over the day, derives the sensible heat flux
(thermal driver), hotspots, their strength/ceiling and drifting thermal columns — answering
**when to launch, where the spots are, and how strongly the wind shifts them**.

| ideal heat-input map (daily max) | "When to launch?" — diurnal cycle |
|---|---|
| ![Heat-flux map](assets/thermalmodel/qh_ideal_daymax.png) | ![Diurnal cycle](assets/thermalmodel/day_timeline.png) |

→ the full visual walkthrough: **[Thermals, step by step](thermal-step-by-step.md)**.

---

!!! note "Languages"
    This site is available in English and German — use the language selector in the header.
    The figures keep English axis labels; captions are translated.
