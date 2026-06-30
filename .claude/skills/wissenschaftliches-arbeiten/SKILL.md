---
name: wissenschaftliches-arbeiten
description: >-
  Forschungs- und modellgetriebene Arbeitsweise für Analyse-, Modellierungs- und
  Validierungsaufgaben in diesem Repo. Nutzen, wenn eine Hypothese geprüft, ein Modellterm/
  Prädiktor hinzugefügt oder verworfen, gegen Messdaten validiert oder ein nicht-offensichtliches
  Ergebnis dauerhaft festgehalten werden soll.
when_to_use: >-
  Bei Modell-/Validierungs-/Forschungsaufgaben (z. B. thermalmodel): neue Annahme, neuer
  Prädiktor/Term, Retro-Validierung, Vergleich gegen Messdaten, Erklärung eines Ergebnisses.
  NICHT nötig für triviale mechanische Edits/Refactors.
---

# Wissenschaftlich-getriebene Arbeitsweise

Ziel: **belastbare, ehrliche Ergebnisse statt plausibel klingender, aber ungeprüfter.**
Folge dem Loop; dokumentiere Entscheidungen **und Negativergebnisse**. Lieber ein verworfener
Term mit Begründung als ein „funktioniert schon"-Bauchgefühl.

## Der Loop

1. **Hypothese explizit machen.** Was genau soll besser werden, und woran würde ich erkennen,
   dass ich falsch liege? Formuliere ein Abbruch-/Verwerf-Kriterium *vorher*.
2. **Plausibilisieren per Websuche.** Zahlen, Formeln, Schwellen und physikalische Annahmen gegen
   Literatur/Quellen prüfen, bevor (oder während) implementiert wird. Quelle im ADR notieren.
   (Beispiele aus dem Repo: Encroachment β≈0.2, Wind-Zerstörung ~25 kt, Lenschow-Profil, ERA5-Zugang.)
3. **Minimal implementieren.** Kleinste lauffähige Version, die die Hypothese testbar macht — kein
   Ausbau, bevor der Skill belegt ist.
4. **Gegen ≥2 unabhängige Datensätze validieren.** In diesem Repo: **eigene IGC-Steigflüge** UND
   **kk7-Heatmap/Hotspots** (zwei unabhängige Ground-Truths). Metriken **gegen den Zufall** stellen
   (AUC, Lift, Hit-Rate, Spearman), nicht nur absolut. Verschiebungstolerant, wo die Wahrheit unscharf ist.
5. **Nur behalten, was generalisiert.** Ein Term, der Set A stark hebt, aber Set B nicht (oder dort
   kippt), ist **Überanpassung → verwerfen** (so geschehen mit Kanten- und Lee/Luv-Term). Das zweite
   Set ist der Überanpassungs-Wächter.
6. **Festhalten.**
   - **Entscheidung → ADR** in [`docs/thermalmodel-journal.md`](../../../docs/thermalmodel-journal.md):
     `Status / Kontext / Entscheidung / Verifikation`. Auch *verworfene* Hypothesen bekommen einen ADR.
   - **Dauerhafte, nicht-offensichtliche Erkenntnis → Memory** (`~/.claude/.../memory/*.md` + Eintrag
     in `MEMORY.md`). Wird per Hook automatisch nach `.claude/agent-memory/` ins Repo gespiegelt.
     Nicht duplizieren, was Code/Git/Journal schon hergeben — den *non-obvious* Schluss festhalten.
7. **Meilenstein committen, NIE pushen** (ohne ausdrücklichen Auftrag). Commit-Message endet mit
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. Auf einem Feature-Branch arbeiten, nicht auf `main`.
8. **Adversarial verifizieren & ehrlich berichten.** Eigene Ergebnisse (und Subagent-/Tool-Output)
   nicht blind glauben — gegenprüfen, Stichproben rendern/inspizieren. Wenn ein Werkzeug versagt
   (z. B. ein Audit-Kritiker lieferte „test"), das **sagen** und auf das verlässliche Signal stützen.
   Misserfolge, übersprungene Schritte und Unsicherheiten offen benennen.

## Repo-Konventionen

- **Tests:** `.venv\Scripts\python.exe -m pytest tests -q` — müssen grün bleiben; Physik-Regression
  (z. B. Aspect-180°) nicht brechen.
- **Daten/Quellen:** alle frei (swisstopo STAC, BAFU, Open-Meteo/ICON, Payerne, kk7, eigene IGC).
  Externe Portale nur ToS-konform (XContest: keine API/Scraping → nur Browser-Metadaten; WeGlide: offene API).
- **Plot-Politik:** nur perzeptuell-uniforme Sequential-Maps (viridis Standard, inferno Energie,
  cividis Wind), helles Relief für Kontrast, Wind in km/h.
- **Reproduzierbarkeit:** teure statische Felder cachen; Modelltag/Datum in Plots schreiben.

## Anti-Muster

- Einen Term behalten, weil er *einen* Datensatz hebt (ohne den zweiten zu prüfen).
- „Sieht plausibel aus" als Validierung ausgeben.
- Tagesabhängige Physik mit Tagesmax-Werten darstellen (Zeitauflösung beachten).
- Subagent-/Workflow-Ergebnisse ungeprüft als Wahrheit übernehmen.
- Personenbezogene Memory in ein öffentliches Repo spiegeln (Repo privat halten).
