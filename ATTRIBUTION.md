# Attribution & data-source licences

This project's **code** is licensed under **Apache-2.0** (see [`LICENSE`](LICENSE)).
Its **documentation, figures and described methodology** (README files, [`docs/`](docs/),
the ADR journal) are licensed under **CC BY 4.0** — reuse of the ideas/text/figures must
credit the author and cite this repository (see [`CITATION.cff`](CITATION.cff)).

The tools **download third-party open data at runtime** (elevation, land cover, soundings,
NWP). That data is **not redistributed in bulk** here — only tiny sample extracts and
*derived* results (plots, metrics) are included for demonstration. Each source keeps its own
licence; the required source credits below must be preserved wherever the data or derived
results are shown.

> Disclaimer: this file is a good-faith summary of the sources' terms, not legal advice.
> The authoritative terms are the linked pages.

## Data sources

### swissALTI3D (DTM) & swissSURFACE3D (DSM) — terrain
- **Provider:** Federal Office of Topography **swisstopo**
- **Licence:** swisstopo terms of use for free geodata/geoservices (Open Government Data; not a CC code).
  Free use incl. commercial & adaptation; **source credit mandatory**; no share-alike.
- **Required credit:** `©swisstopo`
- **Terms:** https://www.swisstopo.admin.ch/de/nutzungsbedingungen-kostenlose-geodaten-und-geodienste

### Waldmischungsgrad LFI — forest mixture (conifer/broadleaf) → albedo/heat factor
- **Provider:** Federal Office for the Environment **BAFU** / **WSL**
- **Licence:** opendata.swiss — *"Open use. Must provide the source."* (commercial allowed, no share-alike)
- **Required credit:** `Waldmischungsgrad LFI, BAFU/WSL` + link to the dataset
- **Terms:** https://opendata.swiss/de/dataset/waldmischungsgrad-lfi

### Payerne radiosonde & ICON-CH forecasts — soundings / NWP
- **Provider:** Federal Office of Meteorology and Climatology **MeteoSwiss**
- **Licence:** **CC BY 4.0**
- **Required credit:** `Quelle: MeteoSchweiz / Source: MeteoSwiss`
- **Terms:** https://opendatadocs.meteoswiss.ch/general/terms-of-use

### Open-Meteo — access layer for ICON & ERA5 (weather/profiles/radiation)
- **Provider:** Open-Meteo.com
- **Licence:** **CC BY 4.0** (API data)
- **Required credit:** `Weather data by Open-Meteo.com` (link to https://open-meteo.com/)
- **Terms:** https://open-meteo.com/en/license

### DWD ICON (`icon_seamless`) — underlying NWP model, via Open-Meteo
- **Provider:** Deutscher Wetterdienst (**DWD**)
- **Licence:** **CC BY 4.0 / GeoNutzV** (commercial OK, no share-alike)
- **Required credit:** `Quelle: Deutscher Wetterdienst` (modified data: `Datenbasis: Deutscher Wetterdienst, eigene Elemente ergänzt`)
- **Terms:** https://www.dwd.de/copyright

### ERA5 reanalysis — historical radiation/cloud, via Open-Meteo archive
- **Provider:** Copernicus Climate Change Service (C3S) / ECMWF
- **Licence:** **CC BY 4.0** (since 2025-07-02)
- **Required credit:** `Generated using Copernicus Climate Change Service information [year]`
  (modified data: `Contains modified Copernicus Climate Change Service information [year]`), plus the
  disclaimer: *"neither the European Commission nor ECMWF is responsible for any use that may be made of
  the Copernicus information or data it contains."*
- **Cite:** Hersbach, H. et al. (2023), ERA5 hourly data, ECMWF, DOI 10.24381/cds.adbb2d47;
  Zippenfenig, P. (2023), Open-Meteo.com Weather API, Zenodo, DOI 10.5281/zenodo.7970649

### thermal.kk7.ch — Paragliding Thermal Maps (validation reference) ⚠️ restrictive
- **Provider:** *The Paragliding Thermal Maps Project* by **M. von Känel**
- **Licence:** **CC BY-NC-SA 4.0** — **NonCommercial + ShareAlike**
- **Required credit:** `thermal.kk7.ch — CC-BY-NC-SA 4.0`; on any live tile/API request append `&src=<hostname>`
- **What this repo does:** it does **not** ship kk7 tiles or raw hotspot data; only aggregated validation
  metrics (hit-rate/AUC/correlation) are reported, with the credit above. kk7-derived map artifacts are
  **deliberately not committed** to keep the code under Apache-2.0 (NC/SA would otherwise bind them).
- **Terms:** https://thermal.kk7.ch/ (CC BY-NC-SA 4.0: https://creativecommons.org/licenses/by-nc-sa/4.0/)

### WeGlide — flight database API (research, currently paused)
- **Provider:** WeGlide UG, Mainz (DE)
- **Licence:** proprietary **API Terms of Use** (no open data licence). No raw flight data is stored in
  this repo; data, if used, is fetched at runtime via a personal API key (never committed).
- **Required credit:** `[project name] for WeGlide`; no partnership/endorsement implied.
- **Terms:** https://docs.weglide.org/legal/api_terms_of_use.html

## Sample flight tracks (`examples/data/igc/`)
Five of the author's own paraglider flights (longest by track distance), provided as demo input.
Device serial numbers / app device-fingerprints have been stripped; the pilot name in the IGC header is
the author's and is retained intentionally.

## Code dependencies
All direct Python dependencies are permissively licensed (MIT / BSD-3-Clause / Apache-2.0 / Matplotlib
licence) — no copyleft. See `pyproject.toml`.
