# Payerne Radiosondierung — Emagramm & Meteo-Analytik

Tooling rund um die MeteoSchweiz-Radiosondierung **Payerne (WMO 06610)**: offizielle
Sondierungsdaten beziehen, ein **Emagramm/Skew-T** zeichnen und thermodynamische **Indizes**
berechnen (CAPE, CIN, LI, LCL, LFC, PWAT, Nullgradgrenze).

## Ausgangsfrage & Rechercheergebnis

> Wie kommen wir an die vergangenen 12-UTC-Emagramme der letzten 2 Wochen?

Kurz gesagt: **gar nicht aus offiziellen offenen Quellen** — das wurde geprüft:

| Quelle | Befund |
|---|---|
| **MeteoSchweiz OGD** (`VZUS01.csv`) | Nur die **aktuelle** Sondierung (bei jedem 00/12-UTC-Aufstieg überschrieben). Kein Archiv, keine Emagramm-PDFs. Verifiziert: Die Datei enthielt live `2026-06-29 12:00 UTC`. |
| **Uni Wyoming Archiv** (sonst der Standard für historische Daten) | Führt Payerne **nicht** (0/18-Zeitstempel 2025–2026; Referenz Stuttgart 10739 liefert Daten). MeteoSchweiz meldet nur hochaufgelöstes **BUFR**, das Wyoming nicht einliest. |
| **MeteoSchweiz Web-App (PDFs)** | Backend per Browser entschlüsselt (siehe unten): Die echten Emagramm-PDFs sind direkt ladbar — aber **data.json listet nur den aktuellen Tag** (00 & 12 UTC). Gestern hängt noch als Überbleibsel im Ordner; ab vorgestern ist alles 404. **Kein 2-Wochen-Archiv.** |
| **opendata.swiss / FSDI-STAC** | Keine Radiosondierungs-Collection verfügbar (Stand 06/2026). |

### Entschlüsseltes Web-App-Backend (offizielle PDFs)

Die App lädt:
1. `…/product/output/versions.json` → aktuelle Version pro Produkt, Schlüssel `radio-soundings/emagram` (z.B. `20260629_1235`).
2. `…/product/output/radio-soundings/emagram/version__<ver>/data.json` → Array veröffentlichter Sondierungen mit `timestamp` und PDF-Pfaden pro Station.
3. PDF: `…/version__<ver>/<station>/radio-soundings_emagram_<station>.<YYYYMMDD>_<HHMM>.pdf`

Das ist headless ladbar (verifiziert), liefert aber nur **den aktuellen Tag**.

**Konsequenz / gewählter Ansatz:** Zwei komplementäre Wege, beide täglich per Cron laufend, sodass
sich das 2-Wochen-Fenster Tag für Tag selbst aufbaut:
- **`download`** – holt die **offiziellen MeteoSchweiz-Emagramm-PDFs** (1:1 wie in der App).
- **`harvest` + `latest`/`archive`** – wertet die offizielle **Rohdaten**-Sondierung (`VZUS01.csv`)
  selbst aus und zeichnet ein Emagramm/Skew-T **mit Indizes** (CAPE/CIN/… – was die
  PDFs nicht können). Vollständiger, reproduzierbarer Datenzugriff.

> Echte *vergangene* (>1 Tag) Diagramme sind aus offiziellen Quellen nicht mehr abrufbar —
> für Payerne gibt es kein öffentliches Archiv.

## Datenquelle

- Aktuelle Sondierung: `https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv`
- Legende: `…/Legende_VZUS01.csv` (leerzeichengetrennt, `/` = fehlend; Druck/Höhe/Temperatur/
  Taupunkt/Wind pro Niveau).
- Lizenz: MeteoSchweiz Open Government Data (Quellenangabe "MeteoSchweiz").

## Installation

```powershell
.venv\Scripts\python.exe -m pip install -e .[meteo]
```

## Verwendung

```powershell
# Offizielle MeteoSchweiz-Emagramm-PDFs holen (Default: Payerne, 12 UTC) -> meteo/pdf_archive/
python meteo\radiosonde_payerne.py download
python meteo\radiosonde_payerne.py download --stations payerne,stuttgart --hour -1   # alle Stationen/Zeitstempel

# Aktuelle Sondierung selbst auswerten -> Emagramm + Indizes (output/meteo/)
python meteo\radiosonde_payerne.py latest

# Rohdaten-Snapshot ins Archiv ablegen (Cron-/Task-Scheduler-tauglich, idempotent)
python meteo\radiosonde_payerne.py harvest

# Alle 12-UTC-Emagramme der letzten 14 Tage aus dem Archiv zeichnen
python meteo\radiosonde_payerne.py archive --hour 12 --days 14

# Index-Zeitreihe (CAPE, PWAT, Nullgradgrenze …) aus dem Archiv -> CSV + Tabelle
python meteo\radiosonde_payerne.py trend --hour 12
```

`--rotation 0` zeichnet ein klassisches (ungeschertes) Emagramm, Default `45` ein
Skew-T-logp (leichter lesbar, gleicher Inhalt).

### Tägliches Aufzeichnen

Damit sich das 2-Wochen-Fenster aufbaut, `harvest` ein- bis zweimal täglich nach den Aufstiegszeiten
laufen lassen (Sondierung verfügbar ~00:30 und ~12:30 UTC). Windows Task Scheduler
(täglich 13:00 Ortszeit):

```powershell
schtasks /create /tn "Payerne-Sondierung" /tr "C:\git\paragliding\.venv\Scripts\python.exe C:\git\paragliding\meteo\radiosonde_payerne.py harvest" /sc daily /st 13:05
```

Das Archiv (`meteo/archive/*.csv`) ist die einzige Möglichkeit, Historie aufzubauen —
deshalb bewusst behalten (bei Bedarf versionieren).

## Ausgaben

- `output/meteo/payerne_<YYYYMMDD>_<HH>_emagramm.png` — Emagramm/Skew-T pro Sondierung.
- `output/meteo/payerne_indices_<HH>z.csv` — Index-Zeitreihe (aus `trend`).
- `meteo/archive/payerne_<YYYYMMDD>_<HH>.csv` — Rohdaten-Snapshots (Historie).

## Indizes (Kurz)

CAPE/CIN (J/kg, Instabilität/Deckel), LI (Lifted Index), LCL/LFC (Hebungskondensationsniveau /
Niveau der freien Konvektion, hPa), PWAT (ausfällbares Wasser, mm), Nullgradgrenze (m) — relevant
unter anderem für Thermikqualität, Wolkenbasishöhe und Gewitter-/Überentwicklungstendenz.
