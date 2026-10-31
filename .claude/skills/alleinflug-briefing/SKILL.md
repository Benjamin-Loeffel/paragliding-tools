---
name: alleinflug-briefing
description: >-
  Plant einen (überwachten) Alleinflug bzw. Flugtag an einem Startplatz und füllt das SHV-Formular
  «Alleinflug: Checkliste» aus: Startplatz-Briefing (Gelände, Volten, Lee-Regeln), Wetter aus den
  MeteoSchweiz-Textprognosen, Messwerte (Holfuy, MeteoSchweiz-Stationen), Webcams, Quervergleich mit dem
  Vortag, ÖV-Anreise und Rückweg Landeplatz -> Startplatz, Go/No-Go-Kriterien für den Flugtag-Morgen.
  Nutzen, wenn Benjamin einen konkreten Flug (heute/morgen) an einem Startplatz plant oder am Flugtag einen
  «Check» der aktuellen Lage will.
when_to_use: >-
  «Plane Alleinflug/Flug morgen in <Gebiet>», «Check» am Flugtag-Morgen, Formular ausfüllen, Startplatz-
  oder Fahrplanfrage für einen Flugtag. NICHT für die modellbasierte Thermik-Tiefe (thermik-prognose) und
  NICHT für historische Flugauswertung (terrainclearance).
---

# Alleinflug-Briefing — Startplatz, Wetter, Messwerte, Formular

Ziel: einen konkreten Flugtag so vorbereiten, dass Benjamin und sein Fluglehrer auf **überprüfbaren
Fakten** entscheiden können, und das SHV-Formular sauber ausgefüllt vorliegt. Werkzeuge:

- `alleinflüge/lagecheck.py` — Messwerte, Webcams, Fahrplan (reproduzierbar statt ad hoc)
- `alleinflüge/fill_checkliste.py` — stempelt die YAML auf die SHV-Vorlage (`--platz` prüft den Platz)
- `alleinflüge/beispiel.yaml` — anonyme Vorlage; echte Planung = `alleinflug_<datum>_<gebiet>.yaml`
- [startplaetze.md](startplaetze.md) — Startplatz-Briefings je Gebiet (Gelände, Stationen, Webcams, ÖV)
- [datenquellen.md](datenquellen.md) — wo welche Daten herkommen und wie man sie liest

> **GRUNDSATZ:** Das Briefing **entscheidet nicht**. Fakten, Messwerte und Kriterien liefern; kritische
> Punkte klar benennen (auch wenn sie unbequem sind) — **Benjamin und der Fluglehrer entscheiden.**
> Vorgeschlagene Schwellwerte als **Vorschlag** kennzeichnen («mit dem Fluglehrer abstimmen»).

## Ablauf

### 1. Rahmen klären (Tag -1)
- Datum, Gebiet, Startplätze, Landeplatz, gewünschte Startzeit. Unklare Ortsnamen **nachfragen**, nicht
  raten (Beispiele: «Zismas» war richtig; «Luegibrüggli» ist ein Start-, kein Landeplatz).
- Gebiet in [startplaetze.md](startplaetze.md) nachschlagen. Fehlt es: SHV-Infotafel und Club-Seiten lesen
  (siehe datenquellen.md) und **dort ergänzen**. Koordinaten nie schätzen — aus Tafel oder eigenen
  IGC-Starts (Median der ersten Fixes) ableiten.

### 2. Wetter — offizielle Textprognosen zuerst
- Benjamin schickt **Screenshots der MeteoSchweiz-App** (Allgemeine Lage, Wetterbericht, Gleitschirm-,
  Segelflugprognose, Wind-/Böen-/Niederschlagskarten). Diese sind die Primärquelle.
- **Für jede Quelle Ausgabezeit UND Gültigkeitstag prüfen.** Fallen, die real passiert sind:
  - Die Segelflugprognose gilt für den **Ausgabetag**; Tabellen und «Weitere Hinweise» gehören zum
    Ausgabetag, für morgen zählt nur der Abschnitt **«Aussichten»**.
  - Die Gleitschirmprognose für «morgen» kann **zwei Tage alt** sein (Ausgabe 00:47 vom Vortag).
  - Ende Oktober endet die Segelflug-Saison (nächste Ausgabe 1. März).
- Modelldaten (Open-Meteo ICON-CH1/D2) nur **ergänzend und markiert** («Modell, vorläufig»). Kein
  `thermik.py`-Lauf für ein Formular — Benjamin hat das abgebrochen («anders machen»): zu schwer, und
  die Textprognosen sind für den Entscheid massgebend.
- Neue Prognose um **05:30** am Flugtag → Wetterteil vor der Unterschrift nachziehen.

### 3. Messwerte und Quervergleich mit heute
- `lagecheck.py holfuy …` und `smn …` für die Stationen des Gebiets (IDs in startplaetze.md).
- **Quervergleich:** Was das Modell für **heute** gesagt hat gegen das, was heute **gemessen** wurde.
  Liegt das Modell daneben (Interlaken 30.10.: Lehn WSW statt gemessen NE, Nebel zu früh aufgelöst),
  entscheiden **Messwerte und Webcams**, nicht das Modell von morgen.
- Nebel/Hochnebel lesen: Station mit **rF 100 % über Stunden** = in der Wolke. Station darüber trocken
  und wärmer = über dem Deckel → Nebelobergrenze liegt dazwischen. Sonnenscheindauer 0 + tiefe
  Globalstrahlung im Tal = Hochnebel über dem Tal.
- **Webcam-Verlauf** (`lagecheck.py webcam <slug> --verlauf <gestern>`): stündlich zeigt, ob sich Nebel
  **auflöst** oder nur **hebt** und wann. Eine Kamera auf **Startplatzhöhe** (Interlaken: Harder Kulm)
  und eine **von oben** (Schynige Platte) zusammen lesen.

### 4. Startplatz-Logik
- Lee-, Volten- und Windregeln aus Tafel/Club pro Startplatz anwenden (startplaetze.md).
- Bei Gleitflügen (Prüfungsmanöver im Abstieg) gilt als Kriterium: **Startplatz nebelfrei + Sicht zum
  Boden und zum Landeplatz.** Höhe unter der Basis braucht es nicht (Benjamins Korrektur, 31.10.).
  Hinweis bleibt: die Basis kann wieder auf den Startplatz sinken; kein Start in eine Nebellücke.
- Reihenfolge der Startplätze **an die Lage koppeln**, nicht fix setzen (31.10.: Luegibrüggli nebelfrei,
  aber Bise = Lee; Bergbo windtauglich, aber in der Wolke).

### 5. ÖV und Tagesplan
- `lagecheck.py fahrplan <von> <nach> --datum … --zeit …` (Haltestellen-IDs in startplaetze.md).
- Hin: ab Wohnort (steht in der lokalen YAML). Zurück: Landeplatz -> Startplatz-Haltestelle. Taktwechsel
  beachten (Wochenende, Winterhalbjahr, Mittagsloch). Aus Bus-Ankunft + Fussweg + Aufbau + Flugdauer die
  realistischen **Runden** pro Startplatz rechnen (Interlaken: Luegibrüggli passt in den Stundentakt,
  Bergbo verpasst über Mittag den Anschluss knapp).
- Bei unsicherem Nebel/Wind: **laufende Beobachtung** zuhause, erster passender Zug — kein fixer Termin.

### 6. Formular füllen (`fill_checkliste.py`)
- YAML aus `beispiel.yaml` kopieren; Gelände, Stationen, Quervergleich und Quellen (mit Ausgabezeit) in
  den Kommentarkopf.
- **Worte des Piloten verwenden** (Selbsteinschätzung, Plan B/C, Flugweg, Reflexion). Eigene
  Formulierungen als solche kennzeichnen und nachfragen, ob sie stimmen. Interpretationen nicht
  stillschweigend festschreiben (24.09.: «Lehre: bei Talwind nicht mehr fliegen» war falsch gelesen —
  gemeint war «souverän gemeistert, im neuen Gebiet bewusst konservativ»).
- **Zahlen statt Adjektive** (Erfahrung aus dem Flugbuch: Flüge/Stunden, Flüge im Gebiet).
- Reflexion des Vortags als eigenen Punkt aufnehmen; daraus abgeleitete Regeln in Entscheidungen und
  Wahrnehmungsfallen spiegeln.
- `--platz` vor dem Generieren; bei Überlauf zuerst **eigenen** Wetterteil straffen, dann Schrift
  (nicht unter 7.0 pt). Keine Wörter am Zeilenende trennen (YAML-Folgezeilen werden mit Leerzeichen
  verbunden).
- Am Schluss: PDF rendern und **ansehen**, auf verbliebene `<…>` prüfen, dann schicken.
- **Unterschriften nie setzen** — nur «Ort, Datum».

### 7. Flugtag-Morgen: «Check»
- Auf «Check» hin: `lagecheck.py holfuy …`, `smn …`, `webcam …` (aktuell + Vortag gleiche Uhrzeit) →
  Tabelle «Station | Wert | Bedeutung», Kriterien erfüllt ja/nein, nächster passender Zug.
- Beobachtungen des Piloten (z. B. Sicht von zuhause auf den Startplatz) sind vollwertige Daten.

## Datenschutz (öffentliches GitHub-Repo)
- Namen, Mobilnummern, Wohnort, ausgefüllte PDFs → nur in den gitignorten `alleinflug*.yaml` /
  `*_ausgefuellt*.pdf`. In Skill, Skript und `beispiel.yaml` nur Platzhalter.
- SHV-Vorlage und Infotafeln lokal halten (`alleinflüge/*.pdf` ist ignoriert), Quelle verlinken.

## Sprache
Deutsch. Fakten mit Quelle und Uhrzeit; Modellwerte als solche kennzeichnen.
