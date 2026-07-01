---
name: flugtag-analyse
description: >-
  Erstellt am Flugtag-Morgen ein reproduzierbares, strukturiertes Meteo-Briefing für Niesen/Frutigen
  (Berner Oberland) nach der SHV-Meteo-Entscheidungsstrategie. Nutzen, wenn Benjamin vor einem Flugtag
  eine einheitliche Wetter-/Gefahren-Beurteilung will (5 Phänomene + Gelände + Mensch + 3×A). Läuft
  `flightday.py` (Sondierung + Synoptik + Thermikmodell) und komponiert daraus das Briefing.
when_to_use: >-
  Am Morgen vor einem geplanten Flug (oder auf Nachfrage „Flugtag-Analyse/Wetterbriefing“). NICHT für
  historische Flugauswertung (das macht terrainclearance) oder allgemeine Code-Aufgaben.
---

# Flugtag-Analyse — Morgen-Meteo-Briefing (Niesen/Frutigen)

Ziel: **immer nach derselben Methodik** die Verhältnisse des Flugtags beurteilen — Grundlage ist die
**SHV-Meteo-Entscheidungsstrategie** (3×3: Faktoren *Meteo/Gelände/Mensch* × Zeitpunkte *Planung/Anreise/
Vor Ort*), Fokus Zeitpunkt **PLANUNG**. Ein Skript liefert die **Zahlen + Ampeln reproduzierbar**; du
komponierst daraus das Briefing im festen Gerüst.

> **GRUNDSATZ (Sicherheit):** Das Briefing **entscheidet nicht**. Es sammelt Fakten, zeigt je Phänomen
> eine **Ampel** (🟢 günstig / 🟡 achtung / 🔴 alarm) + Zahlen und legt den **3×A-Rahmen** vor —
> **Benjamin entscheidet selbst**, bewusst, rechtzeitig, unabhängig von der Gruppe. Nie ein Go/No-Go-Urteil
> fällen; „mehrere kritische Faktoren = gefährliche Verkettung“ benennen, aber die Wahl offen lassen.

## Ablauf

1. **Datenlauf starten** (venv):
   ```powershell
   .venv\Scripts\python.exe flightday.py                 # heute, volle Analyse (inkl. Thermikmodell)
   .venv\Scripts\python.exe flightday.py --skip-thermal  # schnell (nur Sondierung + Synoptik), wenn Zeit knapp
   .venv\Scripts\python.exe flightday.py --date 2026-07-05
   ```
   Der erste volle Lauf lädt DEM-Kacheln + rechnet den Horizont der vergrösserten Domäne (einige Minuten,
   danach gecacht). Ausgaben landen in `output/briefings/<datum>/`.
2. **`output/briefings/<datum>/briefing_data.json` lesen** — enthält je Phänomen
   `{wert, schwelle, ampel, begruendung}` plus Sondierung (CAPE/LI/Lapse/Wolkenbasis/Nullgrad),
   Thermik (w\*, z_i, XC, Startfenster, viable-Stunden) und die Plot-Dateinamen.
3. **Briefing komponieren** streng in dieser Reihenfolge (siehe Template unten). Zahlen/Ampeln **aus der
   JSON übernehmen** (nicht neu erfinden). `flightday.py` schreibt bereits ein Basis-`briefing.md` — deine
   Aufgabe ist die konsistente, knappe Zusammenschau + die Gelände/Mensch-Prompts + der 3×A-Rahmen.
4. **Interaktive Karten verlinken** (im Ausgabeordner): `ch_precip.html`, `ch_solar.html`,
   `ch_wind.html` (Höhenstufen-Dropdown + Zeit-Slider); statisch `ch_overview.png`, `frutigen_radius.png`,
   `emagram.png`, `day_timeline.png` (Startfenster).
5. **Pilot-Checkliste** ausgeben (die live/visuellen Quellen, die das Skript NICHT abdeckt).

## Briefing-Template

**METEO — 5 Phänomene** (Ampel + Zahl + einordnender Satz je Phänomen, aus der JSON):
1. **Überregionaler/Höhenwind** — 700-hPa-Wind, Böigkeit. Schwelle >25/35 km/h. Kaltluft+Thermik = besonders turbulent.
2. **Föhn** (für Niesen/Frutigen v. a. **Südföhn**) — Δp(N–S). ≥4 hPa durchbrechend, ≥8 hPa bis Flachland.
   Live-Föhnzeichen (Föhnmauer/Linsen-/Rotorwolken, sprunghaft T↑/Feuchte↓) bleiben Pilot-Check vor Ort.
3. **Regiowind / Alpines Pumpen** — Talwind (Kandertal/Simmental/Thunersee), Saison/Tageszeit; aus Thermikmodell
   (`wind_bl`, `viable`) + SHV-„Alpines-Pumpen“-Karte (Pilot).
4. **Wärmegewitter / Luftschichtung** — CAPE, **Lapse ≥ −0.8 °C/100 m = gefährlich labil**, Wolkenbasis,
   Niederschlag/Gewitter-Code im Frutigen-Umkreis. „Sehr gute Thermik“ kann auf Turbulenz/Überentwicklung hinweisen.
5. **Fronten** — CH-weiter Niederschlag + Zuzug aus West; Live-Radar bleibt Pilot-Check.

**Luftschichtung & Thermik**: CAPE/LI/Lapse/Wolkenbasis/Nullgrad; w\* max, z_i-Peak, XC-Potenzial,
**Startfenster** (aus `day_timeline.png`).

**GELÄNDE (Niesen/Frutigen)**: Startplatz (Windrichtung/-stärke, Hangausrichtung, Tageszeit ↔ Startfenster) ·
Flugweg (Starkwind an Pässen/Kreten/Talverengungen, Luv/Lee, bei Südföhn Lee-Turbulenz nördlich der Kreten) ·
Landeplatz (jederzeit erreichbar? Starkwindlandung bei Nachmittags-Talwind?).

**MENSCH**: Selbsteinschätzung (Vorhaben ↔ Fähigkeiten/Tagesform; Bauchgefühl ↔ Verstand) ·
Wahrnehmungsfallen (Vertrautheit, Routine, Gruppendruck, Wunschdenken, Zeitdruck, Social Media) · Gruppe.

**Entscheid — 3×A**: Anzahl Alarm/Achtung nennen; **AUSFÜHREN | ALTERNATIVE | ABBRUCH** als Rahmen; **Plan B**
(Verhältnisse ≠ Erwartung) und **Plan C** (Tag ohne Flug retten). **Keine Empfehlung, welches A** — Benjamin wählt.

## Pilot-Checkliste (selbst anschauen — nicht maschinell im Briefing)
Niederschlagsradar (live) · Satellit/Bodenwetterkarte · Textprognose MeteoSchweiz · soaringmeteo/soarWRF ·
meteo-parapente · SHV-Karte „Alpines Pumpen“ · Fluggebiets-Webcams/Holfuy. (Links stehen in `briefing.md`.)

## Regeln
- **Reproduzierbar:** feste Quellen + feste Schwellen (in `meteo/synoptic.py`), immer dieselbe Struktur.
  Schwellenwerte nicht ad hoc ändern — wenn nötig, in `synoptic.py` an einer Stelle anpassen.
- **Ehrlich über Lücken:** Was das Skript nicht liefert (Live-Radar, Satellit, Föhnzeichen vor Ort), klar als
  **Pilot-Check** kennzeichnen. Fehlt ein Datensatz (Ampel „n/a“), das benennen statt raten.
- **Kein Go/No-Go.** Siehe Grundsatz oben.
- **Sprache Deutsch.** Kein Personendatum ins öffentliche Repo; `output/briefings/` ist gitignored.
- Datenquellen: Open-Meteo (ICON-CH) + MeteoSchweiz-Sondierung; „Data by Open-Meteo.com“ / „Quelle: MeteoSchweiz“.
