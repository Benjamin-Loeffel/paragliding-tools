# Background

## Data sources & required attribution

All data is fetched **at runtime** under open licences — it is not redistributed in bulk here.
Wherever the data or derived figures are shown, the source credit below must be preserved. The full,
verbatim list is in [`ATTRIBUTION.md`](https://github.com/Benjamin-Loeffel/paragliding-tools/blob/main/ATTRIBUTION.md).

| Source | Used for | Licence | Credit |
|---|---|---|---|
| swissALTI3D / swissSURFACE3D | terrain (DTM/DSM) | swisstopo OGD terms | `©swisstopo` |
| Forest mixture degree LFI | land cover | opendata.swiss (open, source required) | `BAFU/WSL` |
| Payerne radiosonde / ICON-CH | soundings / NWP | CC BY 4.0 | `Quelle: MeteoSchweiz` |
| Open-Meteo | access to ICON / ERA5 | CC BY 4.0 | `Weather data by Open-Meteo.com` |
| DWD ICON | underlying NWP model | CC BY 4.0 / GeoNutzV | `Quelle: Deutscher Wetterdienst` |
| Copernicus ERA5 | historical radiation | CC BY 4.0 | `Generated using Copernicus Climate Change Service information` |
| thermal.kk7.ch | validation reference | **CC BY-NC-SA 4.0** | `thermal.kk7.ch` (only derived metrics, no raw data) |

## Licence

- **Code:** Apache-2.0.
- **Documentation, figures and the described methodology** (this site, the repo docs): **CC BY 4.0** —
  if you build on these ideas, please credit the author and cite the repository
  ([`CITATION.cff`](https://github.com/Benjamin-Loeffel/paragliding-tools/blob/main/CITATION.cff)).
- This site is a faithful **translation** (EN ↔ DE) of the same content; figures keep English axis labels.

## Decisions & rationale

The full engineering decision log (assumptions, rejected approaches, validation findings) lives in the
repository as an ADR journal:
[`docs/thermalmodel-journal.md`](https://github.com/Benjamin-Loeffel/paragliding-tools/blob/main/docs/thermalmodel-journal.md)
(kept in German).

## Disclaimer

A research/educational model, not an operational forecast and not flight advice. Always cross-check with
official weather products and your own judgement.
