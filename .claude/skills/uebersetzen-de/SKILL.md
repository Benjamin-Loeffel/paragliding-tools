---
name: uebersetzen-de
description: >-
  Hält die deutschen Doku-Site-Seiten (docs/*.de.md) mit den englischen Master-Seiten (docs/*.md)
  synchron. Nutzen, wenn eine EN-Seite geändert/neu wurde und die deutsche Übersetzung nachgezogen
  werden muss (zweisprachige MkDocs-Site, EN = Master).
when_to_use: >-
  Nach dem Editieren/Hinzufügen einer docs/<page>.md (Englisch): die zugehörige docs/<page>.de.md
  neu erzeugen/aktualisieren. NICHT für Code, READMEs ausserhalb docs/, oder das deutsche ADR-Journal.
---

# Übersetzen EN → DE (Doku-Site)

**EN ist der Master.** Für jede `docs/<page>.md` existiert eine `docs/<page>.de.md`. Dieser Skill
übersetzt geänderte EN-Seiten *faithful* nach Deutsch. Bei vielen Seiten lohnt ein Workflow
(ein Agent je Seite, parallel) — sonst direkt Seite für Seite.

## Ablauf
1. **Geänderte Seiten finden:** welche `docs/*.md` sind neuer/anders als ihr `*.de.md`?
   (Git-Diff seit letztem Übersetzungs-Commit, oder die genannte Seite.)
2. **Je Seite übersetzen** (Original lesen → `*.de.md` schreiben), nach den Regeln unten.
3. **Verifizieren:** Vollständigkeit gegen das Original, kein englischer Resttext, Pfade/Code identisch.
4. **Bauen:** `.venv\Scripts\python.exe -m mkdocs build --strict` muss grün sein (EN + DE).
5. **Committen** (Meilenstein), pushen gemäss [[feedback-public-repo-push-policy]].

## Regeln (faithful)
- Übersetze **Fliesstext, Überschriften, Bild-Alt-Texte/Bildunterschriften** UND die **Knoten-Labels
  innerhalb von ```mermaid-Blöcken** (das ist Markdown, kein Bild) ins natürliche technische Deutsch.
- **Unverändert lassen:** Datei-/Pfadangaben und Bild-/Link-Ziele (`assets/...` — nur Alt-Text/Caption
  übersetzen, NICHT den Pfad), CLI-Befehle/Codeblöcke, URLs, Mermaid-Syntax (Pfeile/Klammern/`<br/>`),
  Eigennamen (swisstopo, MeteoSchweiz, ICON, kk7, Open-Meteo, DWD, Copernicus, BAFU/WSL, Payerne,
  Niesen/Frutigen) und die **wörtlichen Quellenangaben** (`©swisstopo`; `Quelle: MeteoSchweiz`;
  `Weather data by Open-Meteo.com`; `Generated using Copernicus …`) sowie CC-Lizenznamen.
- **Plot-PNGs behalten englische Achsenbeschriftungen** (Entscheid) — nur die deutsche Bildunterschrift drumherum.
- Admonition-Marker (`!!! note "…"`) behalten, Titel/Inhalt übersetzen. In Mermaid-Knoten Umlaute direkt
  (ä/ö/ü) verwenden — MkDocs/Material rendert UTF-8 korrekt (kein ae/oe/ue nötig).

## Glossar (EN → DE)
terrain clearance → Hangabstand · paraglider → Gleitschirm · flight track → Flugspur ·
sensible heat flux / Q_H map → fühlbarer Wärmestrom / Q_H-Wärmebild · thermal(s) → Thermik ·
hotspot → Hotspot · (convective) boundary layer → (konvektive) Grenzschicht · sounding → Sondierung ·
source field → Quellfeld · drift → Drift · plume/thermal column → Plume/Thermiksäule · trigger → Auslöser ·
release → Ablösung · launch window → Startfenster · "when to launch?" → "Wann starten?" ·
diurnal cycle → Tagesgang · climb → Steigflug · validation → Validierung · tile → Kachel ·
resolution → Auflösung · uncertainty → Unsicherheit · barogram → Barogramm · calibration → Kalibrierung ·
forest → Wald · hillshade → Schummerung/Hillshade · irradiance → Einstrahlung · ceiling → Decke/Ceiling ·
elevation model → Höhenmodell · exposure/aspect → Exposition/Aspekt · slope → Hangneigung/Slope ·
land cover → Bodenbedeckung/Landcover.

Optional: ein CI-/Hook-**Drift-Wächter** kann warnen, wenn eine `docs/*.md` neuer als ihr `*.de.md` ist
(dann diesen Skill laufen lassen). Siehe [[feedback-public-repo-push-policy]].
