# paragliding-tools

Zwei Werkzeuge für Gleitschirmpiloten in der Schweiz, beide aufbauend auf freien offenen Geodaten und
der hochauflösenden swisstopo-Topografie.

- **[Hangabstand](terrain-clearance.md)** — der minimale **3D-Hangabstand** entlang einer
  IGC-Flugspur (inkl. Wald/Gebäude, GPS-Unsicherheit, Verteilung über die Flugzeit).
- **[Thermik, Schritt für Schritt](thermal-step-by-step.md)** — **solargetriebene Thermikmodellierung**:
  reale Einstrahlung über den Tag → Wärmestrom → Hotspots, Grenzschicht (w\*/z_i) und driftende Thermiksäulen.

Alle Geo-/Wetterdaten werden **zur Laufzeit** aus offenen Quellen bezogen — siehe [Hintergrund](background.md).
Code auf [GitHub](https://github.com/Benjamin-Loeffel/paragliding-tools).

## Hangabstand

Für jeden Punkt einer Flugspur die kürzeste 3D-Distanz zum Gelände **und** zur
Vegetations-/Gebäudeoberfläche — findet kritische Annäherungen, schätzt die GPS-bedingte Unsicherheit
(Monte Carlo) und vergleicht Flüge über die Saison.

| 3D-Relief + Flugspur (eingefärbt nach Hangabstand) | Flugvergleich (Zeit-im-Hangabstand) |
|---|---|
| ![3D-Hangabstand](assets/terrainclearance/2026-06-25_66km_3d.png) | ![Flugvergleich](assets/terrainclearance/aggregate_clearance_kde.png) |

→ Details & Methodik: **[Hangabstand](terrain-clearance.md)**.

## Thermik- & Meteo-Prognose

Modelliert die solare Einstrahlung auf die 3D-Topografie über den Tag, leitet daraus den fühlbaren
Wärmestrom (Thermikantrieb), Hotspots, deren Stärke/Decke und driftende Thermiksäulen ab — und beantwortet,
**wann man starten sollte, wo die Spots sind und wie stark der Wind sie verschiebt**.

| ideales Wärmeeintrags-Wärmebild (Tagesmaximum) | "Wann starten?" — Tagesgang |
|---|---|
| ![Q_H-Wärmebild](assets/thermalmodel/qh_ideal_daymax.png) | ![Tagesgang](assets/thermalmodel/day_timeline.png) |

→ der vollständige visuelle Rundgang: **[Thermik, Schritt für Schritt](thermal-step-by-step.md)**.

---

!!! note "Sprachen"
    Diese Seite ist auf Englisch und Deutsch verfügbar — nutze den Sprachwähler im Kopfbereich.
    Die Abbildungen behalten englische Achsenbeschriftungen; Bildunterschriften sind übersetzt.
