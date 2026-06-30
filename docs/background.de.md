# Hintergrund

## Datenquellen & erforderliche Quellenangaben

Alle Daten werden **zur Laufzeit** unter offenen Lizenzen bezogen — sie werden hier nicht in grossem Umfang weiterverbreitet.
Überall dort, wo die Daten oder daraus abgeleitete Abbildungen gezeigt werden, muss der nachfolgende Quellenhinweis erhalten bleiben. Die vollständige,
wörtliche Liste befindet sich in [`ATTRIBUTION.md`](https://github.com/Benjamin-Loeffel/paragliding-tools/blob/main/ATTRIBUTION.md).

| Quelle | Verwendet für | Lizenz | Quellenangabe |
|---|---|---|---|
| swissALTI3D / swissSURFACE3D | Gelände (DTM/DSM) | swisstopo OGD-Bedingungen | `©swisstopo` |
| Waldmischungsgrad LFI | Bodenbedeckung/Landcover | opendata.swiss (offen, Quellenangabe erforderlich) | `BAFU/WSL` |
| Payerne-Radiosonde / ICON-CH | Sondierungen / NWP | CC BY 4.0 | `Quelle: MeteoSchweiz` |
| Open-Meteo | Zugang zu ICON / ERA5 | CC BY 4.0 | `Weather data by Open-Meteo.com` |
| DWD ICON | zugrundeliegendes NWP-Modell | CC BY 4.0 / GeoNutzV | `Quelle: Deutscher Wetterdienst` |
| Copernicus ERA5 | historische Einstrahlung | CC BY 4.0 | `Generated using Copernicus Climate Change Service information` |
| thermal.kk7.ch | Validierungsreferenz | **CC BY-NC-SA 4.0** | `thermal.kk7.ch` (nur abgeleitete Metriken, keine Rohdaten) |

## Lizenz

- **Code:** Apache-2.0.
- **Dokumentation, Abbildungen und die beschriebene Methodik** (diese Website, die Repo-Dokumentation): **CC BY 4.0** —
  wenn du auf diesen Ideen aufbaust, gib bitte den Autor an und zitiere das Repository
  ([`CITATION.cff`](https://github.com/Benjamin-Loeffel/paragliding-tools/blob/main/CITATION.cff)).
- Diese Website ist eine originalgetreue **Übersetzung** (EN ↔ DE) desselben Inhalts; die Abbildungen behalten englische Achsenbeschriftungen.

## Entscheidungen & Begründung

Das vollständige technische Entscheidungsprotokoll (Annahmen, verworfene Ansätze, Validierungsergebnisse) liegt im
Repository als ADR-Journal:
[`docs/thermalmodel-journal.md`](https://github.com/Benjamin-Loeffel/paragliding-tools/blob/main/docs/thermalmodel-journal.md)
(auf Deutsch geführt).

## Haftungsausschluss

Ein Forschungs-/Lehrmodell, keine operationelle Vorhersage und keine Flugberatung. Überprüfe die Ergebnisse stets
anhand offizieller Wetterprodukte und deines eigenen Urteilsvermögens.
