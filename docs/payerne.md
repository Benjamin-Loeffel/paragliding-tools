# Payerne Radiosounding — Emagram & Meteo Analytics

Tooling around the MeteoSwiss radiosounding **Payerne (WMO 06610)**: fetch official
sounding data, draw an **emagram/Skew-T** and compute thermodynamic **indices**
(CAPE, CIN, LI, LCL, LFC, PWAT, freezing level).

## Starting Question & Research Result

> How do we get the past 12-UTC emagrams of the last 2 weeks?

In short: **not at all from official open sources** — this was checked:

| Source | Finding |
|---|---|
| **MeteoSwiss OGD** (`VZUS01.csv`) | Only the **current** sounding (overwritten at each 00/12 UTC launch). No archive, no emagram PDFs. Verified: the file contained live `2026-06-29 12:00 UTC`. |
| **Uni Wyoming archive** (otherwise the standard for historical data) | Does **not** carry Payerne (0/18 timestamps 2025–2026; reference Stuttgart 10739 returns data). MeteoSwiss reports only high-resolution **BUFR**, which Wyoming does not ingest. |
| **MeteoSwiss web app (PDFs)** | Backend decrypted via browser (see below): the real emagram PDFs are directly loadable — but **data.json lists only the current day** (00 & 12 UTC). Yesterday still lingers in the folder as a leftover; from the day before yesterday on, everything is 404. **No 2-week archive.** |
| **opendata.swiss / FSDI-STAC** | No radiosounding collection available (as of 06/2026). |

### Decrypted Web-App Backend (official PDFs)

The app loads:
1. `…/product/output/versions.json` → current version per product, key `radio-soundings/emagram` (e.g. `20260629_1235`).
2. `…/product/output/radio-soundings/emagram/version__<ver>/data.json` → array of published soundings with `timestamp` and PDF paths per station.
3. PDF: `…/version__<ver>/<station>/radio-soundings_emagram_<station>.<YYYYMMDD>_<HHMM>.pdf`

This is loadable headless (verified), but only delivers **the current day**.

**Consequence / chosen approach:** Two complementary routes, both running daily via cron, so
the 2-week window builds itself up day by day:
- **`download`** – fetches the **official MeteoSwiss emagram PDFs** (1:1 as in the app).
- **`harvest` + `latest`/`archive`** – evaluates the official **raw-data** sounding (`VZUS01.csv`)
  itself and draws an emagram/Skew-T **with indices** (CAPE/CIN/… – which the
  PDFs cannot). Full, reproducible data access.

> Genuinely *past* (>1 day) diagrams are no longer retrievable from official sources —
> for Payerne there is no public archive.

## Data Source

- Current sounding: `https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv`
- Legend: `…/Legende_VZUS01.csv` (space-separated, `/` = missing; pressure/altitude/temperature/
  dew point/wind per level).
- License: MeteoSwiss Open Government Data (attribution "MeteoSchweiz").

## Installation

```powershell
.venv\Scripts\python.exe -m pip install -e .[meteo]
```

## Usage

```powershell
# Fetch official MeteoSwiss emagram PDFs (default: Payerne, 12 UTC) -> meteo/pdf_archive/
python meteo\radiosonde_payerne.py download
python meteo\radiosonde_payerne.py download --stations payerne,stuttgart --hour -1   # all stations/timestamps

# Evaluate the current sounding yourself -> emagram + indices (output/meteo/)
python meteo\radiosonde_payerne.py latest

# Store a raw-data snapshot into the archive (cron/Task-Scheduler-ready, idempotent)
python meteo\radiosonde_payerne.py harvest

# Draw all 12-UTC emagrams of the last 14 days from the archive
python meteo\radiosonde_payerne.py archive --hour 12 --days 14

# Index time series (CAPE, PWAT, freezing level …) from the archive -> CSV + table
python meteo\radiosonde_payerne.py trend --hour 12
```

`--rotation 0` draws a classic (unsheared) emagram, default `45` a
Skew-T-logp (easier to read, same content).

### Recording Daily

So that the 2-week window builds up, run `harvest` once or twice daily after the launch times
(sounding available ~00:30 and ~12:30 UTC). Windows Task Scheduler
(daily 13:00 local time):

```powershell
schtasks /create /tn "Payerne-Sondierung" /tr "C:\git\paragliding\.venv\Scripts\python.exe C:\git\paragliding\meteo\radiosonde_payerne.py harvest" /sc daily /st 13:05
```

The archive (`meteo/archive/*.csv`) is the only way to build up history —
so deliberately keep it (version it if needed).

## Outputs

- `output/meteo/payerne_<YYYYMMDD>_<HH>_emagramm.png` — emagram/Skew-T per sounding.
- `output/meteo/payerne_indices_<HH>z.csv` — index time series (from `trend`).
- `meteo/archive/payerne_<YYYYMMDD>_<HH>.csv` — raw snapshots (history).

## Indices (Brief)

CAPE/CIN (J/kg, instability/cap), LI (Lifted Index), LCL/LFC (lifting condensation level /
level of free convection, hPa), PWAT (precipitable water, mm), freezing level (m) — relevant
among other things for thermal quality, cloud base height, and thunderstorm/over-development tendency.
