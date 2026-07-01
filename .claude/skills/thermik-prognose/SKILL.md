---
name: thermik-prognose
description: >-
  Erstellt eine detaillierte Thermik-Prognose für einen (kommenden) Tag im Fluggebiet
  Adelboden–Frutigen–Niesen: w*/z_i/Ceiling, Hotspots, driftende Plumes (3D), XC-Potenzial,
  Startfenster und eine Pro-Startplatz-Tabelle (Tschentenalp/Trutten/Grimer/Niesen). Nutzen, wenn
  Benjamin die Thermik für morgen (oder einen wählbaren Tag) im Detail wissen will. Läuft `thermik.py`.
when_to_use: >-
  Wenn eine tiefe Thermik-Vorschau für einen kommenden Tag gewünscht ist („wie wird die Thermik
  morgen?“, „Thermik-Prognose für <Datum>“). NICHT die schnelle Go/No-Go-Beurteilung für HEUTE —
  das macht flugtag-analyse. NICHT für historische Flugauswertung (terrainclearance).
---

# Thermik-Prognose — detaillierte Vorschau für einen kommenden Tag

Ziel: die *tiefe* Thermik für einen wählbaren Tag (Default **morgen**) im Fluggebiet Adelboden–
Frutigen–Niesen — inkl. **Pro-Startplatz-Werten**. Ergänzt das tagesaktuelle Briefing (`flugtag-analyse`)
um die vorausschauende Thermik-Detailtiefe.

> **GRUNDSATZ:** Prognose, kein Go/No-Go. w\*/z_i/Ceiling sind **Modellwerte**; die **Konfidenz sinkt mit
> dem Vorlauf** (morgen ICON-CH1 = am zuverlässigsten). Am Flugtag zusätzlich das Briefing + Live-Radar
> prüfen. Benjamin entscheidet selbst.

## Ablauf

1. **Lauf starten** (venv):
   ```powershell
   .venv\Scripts\python.exe thermik.py                 # morgen, volle Tiefe (mit 3D-Plumes) @ 60 m
   .venv\Scripts\python.exe thermik.py --date 2026-07-04
   .venv\Scripts\python.exe thermik.py --skip-plumes   # ohne die schweren 3D-Plume-Slider (schneller)
   # hires: dasselbe komplette Produkt (Plumes + alles) in VOLLER Auflösung übers ganze Gebiet.
   # Der Horizont (Flaschenhals bei feiner Auflösung) läuft parallel auf mehreren Prozessen:
   .venv\Scripts\python.exe thermik.py --resolution 20 --horizon-workers 6
   ```
   Läuft das volle `thermalmodel` auf der Weit-Domäne (~39×39 km, Default @ 60 m; `--resolution 20`
   für hires). Alle Produkte landen in EINEM Ordner `output/thermal_forecast/<datum>/` (nicht auf
   Kacheln verstreut). Die Sondierung kommt für HEUTE aus Payerne (Messung), für kommende Tage aus
   dem **ICON-Prognose-Profil** (`meteo/forecast_sounding.py`). Die 3D-HTMLs dünnen ihr Gelände-Mesh
   fürs Web automatisch aus (Daten/Plumes bleiben voll aufgelöst). Vgl. [[feedback-parallel-compute]].
2. **`output/thermal_forecast/<datum>/thermik_data.json` lesen** — Kennzahlen (CAPE/LI/Nullgrad,
   Wolkenbasis/Thermik-Top, w\* max/median, z_i-Peak, XC, Startfenster) + die **`sites`**-Liste
   (pro Startplatz: `w_star_ms`, `z_i_m`, `ceiling_amsl_m`, `q_h_wm2`, `nearest_hotspot_km`,
   `wind_ceiling_kmh`/`_from_deg`).
3. **Prognose komponieren** in dieser Reihenfolge:
   - **Kopf:** Datum, Quelle (Payerne/ICON-Prognose) + **Vorlauf/Konfidenz** klar benennen.
   - **Tagesüberblick:** Schichtung (CAPE/LI/Nullgrad), Wolkenbasis/Thermik-Top, w\* max/median,
     z_i-Peak, XC, **Startfenster** (aus `day_timeline.png`).
   - **Pro Startplatz (Tabelle):** je Startplatz w\*, z_i, Ceiling, lokales Q_H, Distanz zum nächsten
     Hotspot, Wind auf Ceiling-Höhe. Startplätze ausserhalb der Domäne als solche markieren.
   - **Muster/Interpretation:** wo die Hotspots liegen, Drift-Richtung (aus den Plumes), wann es am
     stärksten ist. „Sehr gute Thermik“ = auch Turbulenz-/Überentwicklungs-Hinweis.
4. **Plots verlinken/zeigen:** `day_timeline.png` (Startfenster), `emagram.png` (Prognose-Sondierung),
   `qh_ideal_daymax.png`/`qh_real_daymax.png` (mit Startplatz-Markern), `xc_potential.png`,
   `hotspots.html`, die **D1-Plume-3D-Slider** (`d1_plumes_grid_3d.html` u. a.), `drift_*_grid.png`,
   `wind_traces_*.png`. `thermik.html` bündelt das.

## Regeln
- **Reuse, nicht neu erfinden:** `thermik.py` orchestriert das bestehende `thermalmodel`; nur der
  Sondierungs-Input ist für kommende Tage das ICON-Prognose-Profil.
- **Konfidenz ehrlich:** Vorlauf nennen; je weiter, desto unsicherer (ICON-CH1 ~33 h, darüber gröber).
  w\*/Ceiling sind Modell-Schätzwerte, keine Garantie.
- **Nicht-präskriptiv:** keine Go/No-Go-Empfehlung; Fakten + Pro-Startplatz-Werte liefern, Benjamin wählt.
- **Sprache Deutsch.** Kein Personendatum ins Repo; `output/thermal_forecast/` ist gitignored.
- Datenquelle: ICON-CH via Open-Meteo + (heute) MeteoSchweiz-Payerne. „Data by Open-Meteo.com“.
