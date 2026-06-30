# Radiosondierung Payerne — Emagramm & Meteo-Analytics

Werkzeug rund um die MeteoSchweiz-Radiosondierung **Payerne (WMO 06610)**: offizielle
Sondierungsdaten holen, ein **Emagramm/Skew-T** zeichnen und thermodynamische **Indizes**
(CAPE, CIN, LI, LCL, LFC, PWAT, Nullgradgrenze) berechnen.

## Ausgangsfrage & Recherche-Ergebnis

> Wie kommen wir an die vergangenen 12-UTC-Emagramme der letzten 2 Wochen?

Kurz: **gar nicht aus offiziellen offenen Quellen** — das wurde geprüft:

| Quelle | Befund |
|---|---|
| **MeteoSchweiz OGD** (`VZUS01.csv`) | Nur die **aktuelle** Sondierung (je Start 00/12 UTC überschrieben). Kein Archiv, keine Emagramm-PDFs. Verifiziert: die Datei enthielt live `2026-06-29 12:00 UTC`. |
| **Uni Wyoming Archiv** (sonst Standard für Historie) | Führt **Payerne nicht** (0/18 Termine 2025–2026; Referenz Stuttgart 10739 liefert Daten). MeteoSchweiz meldet nur hochauflösendes **BUFR**, das Wyoming nicht einliest. |
| **MeteoSchweiz Web-App (PDFs)** | Backend per Browser entschlüsselt (s. u.): die echten Emagramm-PDFs sind direkt ladbar — aber **data.json listet nur den aktuellen Tag** (00 & 12 UTC). Gestern liegt als Rest noch im Ordner, ab vorgestern alles 404. **Kein 2-Wochen-Archiv.** |
| **opendata.swiss / FSDI-STAC** | Keine Radiosondierungs-Collection vorhanden (Stand 06/2026). |

### Entschlüsseltes Web-App-Backend (offizielle PDFs)

Die App lädt:
1. `…/product/output/versions.json` → aktuelle Version je Produkt, Schlüssel `radio-soundings/emagram` (z. B. `20260629_1235`).
2. `…/product/output/radio-soundings/emagram/version__<ver>/data.json` → Array der publizierten Sondierungen mit `timestamp` und PDF-Pfaden je Station.
3. PDF: `…/version__<ver>/<station>/radio-soundings_emagram_<station>.<JJJJMMTT>_<HHMM>.pdf`

Das ist headless ladbar (verifiziert), liefert aber nur **den aktuellen Tag**.

**Konsequenz / gewählter Weg:** Zwei sich ergänzende Routen, beide täglich per cron, damit
das 2-Wochen-Fenster mit jedem Tag von selbst entsteht:
- **`download`** – holt die **offiziellen MeteoSchweiz-Emagramm-PDFs** (1:1 wie in der App).
- **`harvest` + `latest`/`archive`** – wertet die offizielle **Rohdaten**-Sondierung (`VZUS01.csv`)
  selbst aus und zeichnet ein Emagramm/Skew-T **mit Indizes** (CAPE/CIN/… – das können die
  PDFs nicht). Voller, reproduzierbarer Daten-Zugriff.

> Echte *vergangene* (>1 Tag) Diagramme sind aus offiziellen Quellen nicht mehr abrufbar —
> für Payerne existiert kein öffentliches Archiv.

## Datenquelle

- Aktuelle Sondierung: `https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv`
- Legende: `…/Legende_VZUS01.csv` (Leerzeichen-getrennt, `/` = fehlend; Druck/Höhe/Temp/
  Taupunkt/Wind je Niveau).
- Lizenz: MeteoSchweiz Open Government Data (Quellenangabe „MeteoSchweiz").

## Installation

```powershell
.venv\Scripts\python.exe -m pip install -e .[meteo]
```

## Nutzung

```powershell
# Offizielle MeteoSchweiz-Emagramm-PDFs holen (Default: Payerne, 12 UTC) -> meteo/pdf_archive/
python meteo\radiosonde_payerne.py download
python meteo\radiosonde_payerne.py download --stations payerne,stuttgart --hour -1   # alle Stationen/Termine

# Aktuelle Sondierung selbst auswerten -> Emagramm + Indizes (output/meteo/)
python meteo\radiosonde_payerne.py latest

# Rohdaten-Snapshot ins Archiv legen (cron/Task-Scheduler-tauglich, idempotent)
python meteo\radiosonde_payerne.py harvest

# Alle 12-UTC-Emagramme der letzten 14 Tage aus dem Archiv zeichnen
python meteo\radiosonde_payerne.py archive --hour 12 --days 14

# Index-Zeitreihe (CAPE, PWAT, Nullgradgrenze …) aus dem Archiv -> CSV + Tabelle
python meteo\radiosonde_payerne.py trend --hour 12
```

`--rotation 0` zeichnet ein klassisches (ungeschertes) Emagramm, Default `45` ein
Skew-T-logp (besser ablesbar, gleicher Inhalt).

### Täglich mitschneiden

Damit das 2-Wochen-Fenster entsteht, `harvest` ein-/zweimal täglich nach den Startzeiten
laufen lassen (Sondierung ~00:30 und ~12:30 UTC verfügbar). Windows-Aufgabenplanung
(täglich 13:00 Lokalzeit):

```powershell
schtasks /create /tn "Payerne-Sondierung" /tr "C:\git\paragliding\.venv\Scripts\python.exe C:\git\paragliding\meteo\radiosonde_payerne.py harvest" /sc daily /st 13:05
```

Das Archiv (`meteo/archive/*.csv`) ist die einzige Möglichkeit, Historie aufzubauen —
daher bewusst aufbewahren (ggf. versionieren).

## Ausgaben

- `output/meteo/payerne_<JJJJMMTT>_<HH>_emagramm.png` — Emagramm/Skew-T je Sondierung.
- `output/meteo/payerne_indices_<HH>z.csv` — Index-Zeitreihe (aus `trend`).
- `meteo/archive/payerne_<JJJJMMTT>_<HH>.csv` — Roh-Snapshots (Historie).

## Indizes (Kurz)

CAPE/CIN (J/kg, Labilität/Deckel), LI (Lifted Index), LCL/LFC (Kondensations-/freies
Auftriebsniveau, hPa), PWAT (niederschlagbares Wasser, mm), Nullgradgrenze (m) — relevant
u. a. für Thermikgüte, Basishöhe, Gewitter- und Überentwicklungsneigung.
