# Fluglehre — Rezeptbuch

Ein **Kochbuch für die Theorieprüfung**: pro Fragentyp ein festes Vorgehen, Schritt für Schritt.
Keine Herleitungen, die man nicht braucht — aber jede Formel wird einmal in einfachen Worten
erklärt, damit man sie nicht bloss auswendig lernt.

!!! note "Was das hier ist und was nicht"
    Eigene Zusammenfassung, **kein offizielles Prüfungsmaterial**. Alle Zeichnungen sind selbst
    erstellt. Die Zahlenbeispiele sind typische Werte, wie sie in Aufgaben vorkommen.
    Verbindlich ist immer der aktuelle Stand von SHV/FSVL und BAZL.

**So benutzt du das Heft:** Lies zuerst Kapitel 1 (die zwei Formeln). Danach kannst du direkt zum
Rezept springen, das zu deiner Frage passt. Ganz am Schluss stehen die Zahlen zum Auswendiglernen
und die häufigsten Fallen.

---

## 1 · Die zwei Formeln — in einfachen Worten

Fast alles in der Fluglehre hängt an **zwei Formeln, die gleich gebaut sind**. Wenn du eine
verstehst, verstehst du beide.

### Wie stark bremst die Luft einen Körper?

Stell dir vor, du hältst die Hand aus dem Autofenster. Was macht den Druck auf die Hand grösser?

1. **Die Form.** Eine flache Hand bremst stärker als eine schmale, nach vorn gedrehte Hand.
   Diese Form-Eigenschaft heisst **c<sub>W</sub>-Wert** (W wie *Widerstand*). Kleiner Wert = gute Form.
2. **Die Grösse.** Die ganze Hand bremst stärker als ein Finger. Gemeint ist die Fläche, die
   der Luft entgegensteht — die **Stirnfläche**.
3. **Wie dick die Luft ist.** Unten im Tal ist die Luft dicht, hoch oben dünn. Dünne Luft bremst
   weniger. Diese "Dicke" heisst **Luftdichte** und wird mit dem griechischen Buchstaben
   **ρ** ("rho") geschrieben.
4. **Wie schnell du fährst.** Und das ist der wichtigste Punkt: Bei doppelter Geschwindigkeit
   ist der Druck **nicht doppelt, sondern vierfach** so gross.

Alles zusammen ergibt die Widerstandsformel:

> **W  =  c<sub>W</sub> &middot; &frac12; &middot; &rho; &middot; v&sup2; &middot; A**

| Zeichen | heisst | in einfachen Worten |
|---|---|---|
| **W** | Widerstand | wie stark die Luft bremst (in Newton) |
| **c<sub>W</sub>** | Widerstandsbeiwert | wie gut oder schlecht die **Form** ist |
| **ρ** | Luftdichte | wie **dick** die Luft ist |
| **v** | Geschwindigkeit | wie **schnell** die Luft vorbeiströmt |
| **A** | Stirnfläche | wie **gross** der Körper von vorn ist |

Das `½` ist nur ein Umrechnungsfaktor, damit die Einheiten stimmen. Für die Prüfung musst du es
nie ausrechnen — es kürzt sich in jeder Aufgabe weg.

### Und der Auftrieb?

Genau dieselbe Formel, nur mit dem **Auftriebs**beiwert c<sub>A</sub> und der **Flügel**fläche F:

> **Auftrieb  =  c<sub>A</sub> &middot; &frac12; &middot; &rho; &middot; v&sup2; &middot; F**

!!! tip "Der eine Satz, der 35 Fragen löst"
    **Nur die Geschwindigkeit geht im Quadrat ein. Form, Fläche und Luftdichte gehen einfach ein.**

| Was du verdoppelst | Widerstand (und Auftrieb) wird |
|---|---|
| Form c<sub>W</sub> | doppelt |
| Fläche | doppelt |
| Luftdichte ρ | doppelt |
| **Geschwindigkeit v** | **vierfach** |

Die kleine Tabelle solltest du im Kopf haben:

| v wird | ×2 | ×3 | ×4 | ÷2 |
|---|---|---|---|---|
| Widerstand wird | **×4** | **×9** | **×16** | **÷4** |

---

## 2 · Rezepte für Rechenfragen

### Rezept 1 — "Was passiert mit dem Widerstand, wenn …"

Typische Frage: *Ein Körper erzeugt bei 30 km/h einen Widerstand von 300 N. Wie gross ist der
Widerstand bei 60 km/h?*

**Vorgehen**

1. Schau, **was sich ändert**: Geschwindigkeit, Fläche oder Luftdichte?
2. Bilde den **Bruch neu ÷ alt** dieser einen Grösse.
3. Ist es die **Geschwindigkeit** → den Bruch **quadrieren**. Sonst → so lassen.
4. Mit dem alten Widerstand **multiplizieren**.

**Beispiel:** 30 → 60 km/h. Bruch = 60/30 = 2. Geschwindigkeit ⇒ quadrieren: 2² = 4.
Also 300 N × 4 = **1'200 N**.

**Zweites Beispiel:** Fläche 2 m² → 4 m². Bruch = 2. Fläche ⇒ **nicht** quadrieren.
Also 300 N × 2 = **600 N**.

!!! warning "Die Falle"
    Angaben wie "Stirnfläche 0,75 m²" oder "auf Meereshöhe" stehen oft nur als **Ablenkung** da.
    Wenn sie sich nicht ändern, kürzen sie sich weg — sie kommen in der Rechnung gar nicht vor.

### Rezept 2 — c<sub>W</sub>-Werte vergleichen

Typische Frage: *Ein Körper mit c<sub>W</sub> 0,33 erzeugt im Vergleich zu einem mit c<sub>W</sub> 1 …*

**Vorgehen**

1. **Teilen**, nie subtrahieren: 1 ÷ 0,33 = 3.
2. Der **kleinere** c<sub>W</sub> hat **weniger** Widerstand.
3. Antwort ablesen: 3 mal weniger Widerstand.

| Vergleich | so heisst es in der Antwort |
|---|---|
| 0,5 gegen 1 | 2 mal weniger |
| **0,33** gegen 1 | **3 mal weniger** |
| 0,2 gegen 1 | 5 mal weniger |
| 0,05 gegen 1 | 20 mal weniger |
| **1,3** gegen 1 | **30 % mehr** |

!!! warning "Die Falle"
    0,33 ist **nicht** "30 % weniger" — das wären 0,7. Bei Werten **nahe 1** passt die
    Prozent-Sprache, bei Werten **weit unter 1** die Faktor-Sprache.

**Die vier Körper, die im Prüfungsbild vorkommen** — einmal lernen, mehrere Punkte holen:

| Form | c<sub>W</sub> |
|---|---|
| Hohlschale, Öffnung **gegen** den Wind (wie ein Rettungsschirm) | **1,3** |
| senkrechte Platte / Brett | **1,0** |
| Tropfenform **verkehrt** herum (Spitze vorn) | **0,17** |
| Tropfenform **richtig** (runde Nase vorn, Spitze hinten) | **0,08** |

Merksatz: *Fallschirm > Brett ≫ Tropfen verkehrt > Tropfen richtig.*

Und die Einsicht dahinter: **derselbe Tropfen andersherum hat den doppelten Widerstand.**
Widerstand entsteht vor allem **hinten** — die Luft muss sich am Heck wieder sauber schliessen
können. Deshalb bringt beim Gurtzeug eine Heckverkleidung mehr als eine vorne.

### Rezept 3 — Luftwiderstand in der Höhe

Je höher, je dünner die Luft, je weniger Widerstand. Für die Prüfung reicht eine Merkreihe:
**pro 1'000 m rund 10 % weniger.**

| Höhe über Meer | Widerstand / Luftdichte |
|---|---|
| 1'100 m | **90 %** |
| 2'200 m | **81 %** |
| 3'300 m | **72 %** |
| 4'400 m | **64 %** |
| ~5'500 m | **50 %** (Dichte halbiert) |

**Vorgehen:** Höhe auf die nächste 1'000er-Stufe runden, Zeile ablesen. Fertig.

Zwei Zusatzfragen, die dazugehören:

- *Die Abnahme ist nicht linear.* Unten nimmt die Dichte **schneller** ab als oben — deshalb ist
  die Hälfte schon bei 5'500 m erreicht und nicht erst bei 20 km.
- *Was heisst das im Flug?* Auftrieb und Widerstand sinken **gleich stark** ⇒ die **Gleitzahl
  bleibt gleich**, aber man fliegt **schneller**. Start-, Lande- und Überziehgeschwindigkeit sind
  in der Höhe (und bei Hitze) höher, die Startstrecke länger.

### Rezept 4 — Das Gleitzahl-Dreieck

Drei Grössen, drei mögliche Fragen. Immer dieselbe Formel:

> **Gleitzahl  =  Vorw&auml;rtsgeschwindigkeit  &divide;  Sinkgeschwindigkeit**

**Vorgehen**

1. Formel hinschreiben.
2. Die **gesuchte** Grösse freistellen.
3. Einsetzen — beide Geschwindigkeiten in **derselben Einheit** (am besten m/s).

| gegeben | gesucht | Rechnung | Ergebnis |
|---|---|---|---|
| 9 m/s vorwärts, 1,5 m/s Sinken | Gleitzahl | 9 ÷ 1,5 | **6,0** |
| Gleitzahl 9, Sinken 1 m/s | vorwärts | 9 × 1 | **9 m/s = 32,4 km/h** |
| Gleitzahl 10, 12 m/s vorwärts | Sinken | 12 ÷ 10 | **1,2 m/s** |

**Die Gleitzahl bedeutet vier Dinge gleichzeitig** — je nachdem, was in den Antworten steht:

| Lesart | Bruch |
|---|---|
| Kräfte | Auftrieb ÷ Widerstand |
| Beiwerte | c<sub>A</sub> ÷ c<sub>W</sub> |
| Geschwindigkeiten | vorwärts ÷ Sinken |
| Strecke | Strecke ÷ Höhenverlust |

!!! tip "Zwei geschenkte Punkte"
    **„Schub" gibt es beim Gleitschirm und beim Delta nicht** — wir haben keinen Motor. Jede
    Antwort mit dem Wort *Schub* ist automatisch falsch.

    Und: **Gleitzahl und Gleitwinkel laufen gegeneinander.** Grosse Gleitzahl = **kleiner**
    (flacher) Winkel. Mehr Widerstand ⇒ Gleitzahl kleiner ⇒ Winkel grösser.

### Rezept 5 — Wie weit komme ich?

> **Strecke  =  Gleitzahl  &times;  H&ouml;he**

**Vorgehen**

1. Alles in **Meter** umrechnen.
2. Je nach Frage umstellen:
   Strecke = GZ × Höhe · Höhe = Strecke ÷ GZ · GZ = Strecke ÷ Höhe
3. Am Schluss in km umwandeln (÷ 1000).

| Aufgabe | Rechnung | Ergebnis |
|---|---|---|
| Gleitzahl 12, 2'400 m hoch | 12 × 2'400 | **28,8 km** |
| Gleitzahl 8, 800 m hoch | 8 × 800 | **6,4 km** |
| Gleitzahl 8, 1'600 m Strecke | 1'600 ÷ 8 | **200 m Höhenverlust** |
| 7,0 km aus 1'400 m | 7'000 ÷ 1'400 | **Gleitzahl 5** |

Kopfrechen-Faustformel: **Gleitzahl 10 ⇒ 1 km Strecke pro 100 m Höhe.**

!!! warning "Realität"
    Diese Zahlen gelten für **ruhige Luft, ohne Reserve**. In der Praxis rechnet man mit
    Gleitzahl 6–7 statt 10–12 und braucht Ankunftshöhe über dem Landeplatz.

### Rezept 6 — Wind und Auf-/Abwind dazurechnen

Der Schirm fliegt immer **relativ zur Luft**. Die Luft selbst kann sich bewegen — das rechnet man
einfach **dazu**. Und zwar getrennt:

| Die Luft bewegt sich … | ändert | ändert **nicht** |
|---|---|---|
| **waagrecht** (Wind) | die Vorwärtsgeschwindigkeit über Grund | das Sinken |
| **senkrecht** (Auf-/Abwind) | das Sinken über Grund | die Vorwärtsgeschwindigkeit |

> **Gleitzahl &uuml;ber Grund  =  (vorw&auml;rts &plusmn; Wind)  &divide;  (Sinken &plusmn; Auf-/Abwind)**

**Vorgehen**

1. Zwei Zeilen hinschreiben: *vorwärts* und *sinken*.
2. Gegenwind **abziehen** (Rückenwind dazu) — nur in der Zeile *vorwärts*.
3. Abwind **dazuzählen** (Aufwind abziehen) — nur in der Zeile *sinken*.
4. Teilen.

**Beispiel Abwind:** 10 m/s vorwärts, 1 m/s Eigensinken, Abwindfeld mit 1 m/s.
vorwärts: 10 (unverändert) · sinken: 1 + 1 = 2 ⇒ Gleitzahl **10 → 5**.

**Beispiel Gegenwind:** 15 m/s vorwärts, 2 m/s Sinken, 5 m/s Gegenwind.
vorwärts: 15 − 5 = 10 · sinken: 2 (unverändert) ⇒ Gleitzahl **7,5 → 5**.

!!! danger "Das musst du gefühlt haben"
    Schon **1 m/s Abwind halbiert** die Gleitzahl eines 10er-Schirms. Deshalb fliegt man
    Abwindfelder **schnell** durch, statt "sparsam" zu gleiten.

### Rezept 7 — m/s und km/h

> **m/s  &times; 3,6  =  km/h**  &nbsp;&nbsp;&middot;&nbsp;&nbsp;  **km/h  &divide; 3,6  =  m/s**

Anker im Kopf: 5 m/s = 18 km/h · 7 m/s = 25 km/h · 9 m/s = 32,4 km/h · 10 m/s = 36 km/h ·
15 m/s = 54 km/h · 20 m/s = 72 km/h.

---

## 3 · Rezept: die Polare lesen

Die **Geschwindigkeitspolare** ist die Leistungskurve des Geräts: waagrecht die
Vorwärtsgeschwindigkeit, senkrecht (nach unten!) das Sinken. Jeder Punkt der Kurve ist ein
Flugzustand.

<figure markdown="span">
<svg viewBox="0 0 470 200" role="img" aria-label="Geschwindigkeitspolare mit den Punkten geringstes Sinken und bestes Gleiten" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--lightest)" stroke-width="1">
    <line x1="158" y1="25" x2="158" y2="185"/><line x1="204" y1="25" x2="204" y2="185"/>
    <line x1="249" y1="25" x2="249" y2="185"/><line x1="294" y1="25" x2="294" y2="185"/>
    <line x1="340" y1="25" x2="340" y2="185"/>
    <line x1="45" y1="55" x2="395" y2="55"/><line x1="45" y1="85" x2="395" y2="85"/>
    <line x1="45" y1="115" x2="395" y2="115"/><line x1="45" y1="145" x2="395" y2="145"/>
  </g>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="2" fill="none">
    <line x1="45" y1="25" x2="392" y2="25"/>
    <line x1="45" y1="25" x2="45" y2="182"/>
  </g>
  <path d="M392,25 l-8,-4 v8 z" fill="var(--md-default-fg-color--light)"/>
  <path d="M45,182 l-4,-8 h8 z" fill="var(--md-default-fg-color--light)"/>
  <line x1="45" y1="25" x2="395" y2="112" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <line x1="45" y1="70" x2="395" y2="70" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="2 4"/>
  <path d="M158,100 C 175,80 190,72 204,70 C 220,68 235,71 249,76 C 265,82 280,88 294,97 C 310,108 326,120 340,130"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <g fill="var(--md-default-fg-color--light)">
    <circle cx="158" cy="100" r="3"/><circle cx="294" cy="97" r="3"/><circle cx="340" cy="130" r="3"/>
  </g>
  <g fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2">
    <circle cx="204" cy="70" r="5.5"/><circle cx="249" cy="76" r="5.5"/>
  </g>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1" fill="none">
    <path d="M196,68 L150,60"/><path d="M253,82 L272,116"/>
  </g>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="147" y="57" text-anchor="end">geringstes Sinken</text>
    <text x="276" y="120">bestes Gleiten</text>
    <text x="158" y="18" text-anchor="middle">5</text><text x="204" y="18" text-anchor="middle">7</text>
    <text x="249" y="18" text-anchor="middle">9</text><text x="294" y="18" text-anchor="middle">11</text>
    <text x="340" y="18" text-anchor="middle">13</text>
    <text x="38" y="59" text-anchor="end">1</text><text x="38" y="89" text-anchor="end">2</text>
    <text x="38" y="119" text-anchor="end">3</text><text x="38" y="149" text-anchor="end">4</text>
  </g>
  <g style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">
    <text x="396" y="40">vorwärts (m/s)</text>
    <text x="52" y="180">Sinken (m/s)</text>
  </g>
</svg>
<figcaption>Die Prüfungspolare. Gestrichelte lange Linie: <b>Tangente vom Ursprung</b> — sie berührt die Kurve beim <b>besten Gleiten</b>. Gepunktete waagrechte Linie: der <b>tiefste Punkt</b> der Kurve ist das <b>geringste Sinken</b>.</figcaption>
</figure>

Diese Tabelle gehört zur Kurve und ist die ganze Prüfung wert:

| vorwärts | Sinken | Gleitzahl | Das ist … |
|---|---|---|---|
| 5 m/s | 2,5 m/s | **2,0** | **Minimalgeschwindigkeit** (Überziehgrenze) |
| 7 m/s | 1,5 m/s | **4,6** | **geringstes Sinken** — längste Flugdauer |
| 9 m/s | 1,7 m/s | **5,3** | **bestes Gleiten** — weiteste Strecke |
| 11 m/s | 2,4 m/s | 4,6 | schneller Reiseflug |
| 13 m/s | 3,5 m/s | **3,7** | **Maximalgeschwindigkeit** (Vollgas) |

**Vorgehen bei jeder Polaren-Frage**

1. **Welche Zeile?**
   *geringstes Sinken* = kleinste Sinkzahl (1,5) · *bestes Gleiten* = grösste Gleitzahl (5,3) ·
   *minimal* = erste Zeile · *maximal* = letzte Zeile.
2. **Was ist gefragt?**
   *Gleitzahl* → dritte Spalte ablesen.
   *Vorwärtsgeschwindigkeit* → erste Spalte ablesen.
   ***Fluggeschwindigkeit*** → **rechnen** (siehe Schritt 3).
3. Wenn "Fluggeschwindigkeit" gefragt ist: das ist die Geschwindigkeit **entlang der Flugbahn**,
   also die schräge Länge aus vorwärts und Sinken:

> **Fluggeschwindigkeit  =  &radic;( vorw&auml;rts&sup2; + Sinken&sup2; )**

| Zeile | Rechnung | Fluggeschwindigkeit |
|---|---|---|
| 5 / 2,5 | √(25 + 6,25) | **5,6 m/s** (20 km/h) |
| 7 / 1,5 | √(49 + 2,25) | **7,2 m/s** (26 km/h) |
| 9 / 1,7 | √(81 + 2,89) | **9,2 m/s** (33 km/h) |

!!! warning "Genau hierauf zielt die Frage"
    Wenn in den Antworten **9,0 und 9,2** stehen, wird geprüft, ob du
    Vorwärtsgeschwindigkeit und Fluggeschwindigkeit unterscheidest. Steht "Fluggeschwindigkeit"
    in der Frage → **Wurzel rechnen**.

**Zwei Sätze, die dazugehören:**

- **Geringstes Sinken ist nicht bestes Gleiten.** Bestes Gleiten liegt **immer schneller**.
- **Zu langsam kostet mehr als zu schnell:** am langsamen Ende ist die Gleitzahl 2,0, bei
  Vollgas noch 3,7.

---

## 4 · Rezept: Sollfahrt — wann schneller, wann langsamer?

Die Regel in einem Satz:

!!! tip "Sollfahrt"
    **Gegenwind und Abwind ⇒ schneller fliegen. Rückenwind und Aufwind ⇒ langsamer fliegen.**

Warum? Weil die Tangente nicht mehr vom Ursprung kommt, sondern von einem **verschobenen
Punkt**. Und je weiter dieser Punkt verschoben ist, desto weiter rechts (= schneller) berührt sie
die Kurve.

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 -30 215 175" role="img" aria-label="Tangente vom Ursprung bei ruhiger Luft" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="20" x2="200" y2="20"/><line x1="30" y1="20" x2="30" y2="130"/>
  </g>
  <path d="M83,70 C 92,56 98,51 105,50 C 112,49 119,51 126,54 C 133,58 141,62 147,68 C 155,76 162,84 169,90"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="30" y1="20" x2="200" y2="80" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <circle cx="30" cy="20" r="4" fill="var(--md-default-fg-color)"/>
  <circle cx="126" cy="54" r="5" fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2"/>
  <text x="126" y="44" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">9 m/s</text>
</svg>
<figcaption><b>1 · Ruhige Luft.</b> Tangente vom Ursprung ⇒ bestes Gleiten bei 9 m/s.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 -30 215 175" role="img" aria-label="Bei Gegenwind wandert der Bezugspunkt nach rechts" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="20" x2="200" y2="20"/><line x1="30" y1="20" x2="30" y2="130"/>
  </g>
  <path d="M83,70 C 92,56 98,51 105,50 C 112,49 119,51 126,54 C 133,58 141,62 147,68 C 155,76 162,84 169,90"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="115" y1="20" x2="190" y2="118" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="2" fill="none">
    <line x1="34" y1="8" x2="108" y2="8"/>
  </g>
  <path d="M113,8 l-8,-4 v8 z" fill="var(--md-default-fg-color)"/>
  <text x="70" y="0" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">Wind</text>
  <circle cx="115" cy="20" r="4" fill="var(--md-default-fg-color)"/>
  <circle cx="169" cy="90" r="5" fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2"/>
  <text x="169" y="106" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">Vollgas</text>
</svg>
<figcaption><b>2 · Gegenwind.</b> Bezugspunkt wandert nach <b>rechts</b> ⇒ Berührpunkt schneller. Bei 8 m/s Gegenwind bis zur Maximalgeschwindigkeit.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 -30 215 175" role="img" aria-label="Bei Abwind wandert der Bezugspunkt nach oben" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="20" x2="200" y2="20"/><line x1="30" y1="20" x2="30" y2="130"/>
  </g>
  <path d="M83,70 C 92,56 98,51 105,50 C 112,49 119,51 126,54 C 133,58 141,62 147,68 C 155,76 162,84 169,90"
        fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="30" y1="-20" x2="190" y2="103" stroke="var(--md-default-fg-color)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="2" fill="none">
    <line x1="14" y1="16" x2="14" y2="-14"/>
  </g>
  <path d="M14,-19 l-4,8 h8 z" fill="var(--md-default-fg-color)"/>
  <text x="22" y="-8" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">Abwind</text>
  <circle cx="30" cy="-20" r="4" fill="var(--md-default-fg-color)"/>
  <circle cx="147" cy="68" r="5" fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2"/>
  <text x="147" y="84" text-anchor="middle" style="font:600 11px system-ui,sans-serif" fill="var(--md-default-fg-color)">11 m/s</text>
</svg>
<figcaption><b>3 · Abwind.</b> Bezugspunkt wandert nach <b>oben</b> ⇒ Berührpunkt ebenfalls schneller.</figcaption>
</figure>

</div>

!!! warning "Die Ausnahme, die geprüft wird"
    Die **Geschwindigkeit des geringsten Sinkens** ändert sich bei Wind und bei Auf-/Abwind
    **nicht**. Nur die des **besten Gleitens** wandert. Grund: der **tiefste Punkt** der Kurve
    bleibt beim selben Vorwärtstempo, egal wohin man den Bezugspunkt schiebt.

---

## 5 · Rezept: Vektoraddition (Kräfte zusammenzählen)

Das ist der wichtigste Bildaufgaben-Typ, und er hat ein Rezept, das **immer** funktioniert.

!!! tip "Das Rezept in einem Satz"
    **Den ersten Pfeil festhalten. Den zweiten Pfeil am Ende des ersten neu ansetzen. Dann vom
    festgehaltenen Anfang zum Ende des zweiten schauen — das ist die Resultierende.**

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Schritt 1: zwei Kräfte am selben Angriffspunkt" style="max-width:100%;height:auto">
  <defs><pattern id="vga" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#vga)"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="30" y1="120" x2="86" y2="120"/><line x1="30" y1="120" x2="66" y2="84"/>
  </g>
  <path d="M90,120 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M70,80 l-1,-10 l-9,1 z" fill="var(--md-default-fg-color)"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="58" y="138" text-anchor="middle">F₁</text><text x="34" y="80">F₂</text>
  </g>
</svg>
<figcaption><b>1 · Gegeben.</b> Zwei Kräfte, gleicher Angriffspunkt.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Schritt 2: den ersten Pfeil festhalten" style="max-width:100%;height:auto">
  <defs><pattern id="vgb" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#vgb)"/>
  <g stroke="var(--md-default-fg-color--lightest)" stroke-width="2" fill="none">
    <line x1="30" y1="120" x2="66" y2="84"/>
  </g>
  <line x1="30" y1="120" x2="86" y2="120" stroke="var(--md-default-fg-color)" stroke-width="3" stroke-linecap="round"/>
  <path d="M90,120 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <circle cx="30" cy="120" r="6" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2.5"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="58" y="138" text-anchor="middle">F₁</text>
  </g>
  <text x="8" y="146" style="font:400 11px system-ui,sans-serif" fill="var(--md-primary-fg-color)">festhalten</text>
</svg>
<figcaption><b>2 · Ersten festhalten.</b> Anfangspunkt merken — von dort wird gemessen.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Schritt 3: den zweiten Pfeil am Ende des ersten ansetzen" style="max-width:100%;height:auto">
  <defs><pattern id="vgc" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#vgc)"/>
  <line x1="30" y1="120" x2="86" y2="120" stroke="var(--md-default-fg-color)" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M90,120 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <line x1="90" y1="120" x2="126" y2="84" stroke="var(--md-default-fg-color)" stroke-width="2.5" stroke-dasharray="5 4" stroke-linecap="round"/>
  <path d="M130,80 l-1,-10 l-9,1 z" fill="var(--md-default-fg-color)"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="58" y="138" text-anchor="middle">F₁</text><text x="132" y="104">F₂</text>
  </g>
</svg>
<figcaption><b>3 · Zweiten ansetzen.</b> F₂ unverändert verschieben — Länge und Richtung bleiben gleich.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 160" role="img" aria-label="Schritt 4: die Resultierende vom Anfang zum Ende zeichnen" style="max-width:100%;height:auto">
  <defs><pattern id="vgd" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="translate(10,0)">
    <path d="M20 0H0V20" fill="none" stroke="var(--md-default-fg-color--lighter)" stroke-width="1"/></pattern></defs>
  <rect width="190" height="160" fill="url(#vgd)"/>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <line x1="30" y1="120" x2="86" y2="120"/>
    <line x1="90" y1="120" x2="126" y2="84" stroke-dasharray="5 4"/>
  </g>
  <line x1="30" y1="120" x2="124" y2="86" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M130,80 l-11,0 l3,9 z" fill="var(--md-primary-fg-color)"/>
  <circle cx="30" cy="120" r="4" fill="var(--md-default-fg-color)"/>
  <g style="font:700 14px system-ui,sans-serif" fill="var(--md-primary-fg-color)">
    <text x="72" y="96">R</text>
  </g>
</svg>
<figcaption><b>4 · Ablesen.</b> Vom festgehaltenen Anfang zum Ende des zweiten: <b>R</b> ist die Resultierende.</figcaption>
</figure>

</div>

### Die drei Sonderfälle

Wenn beide Pfeile auf **derselben Linie** liegen oder **rechtwinklig** stehen, geht es noch
schneller:

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 120" role="img" aria-label="Gleichgerichtete Kräfte addieren sich" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="20" y1="30" x2="76" y2="30"/><line x1="84" y1="30" x2="120" y2="30" stroke-dasharray="5 4"/>
  </g>
  <path d="M80,30 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M124,30 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <line x1="20" y1="80" x2="118" y2="80" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M124,80 l-10,-5 v10 z" fill="var(--md-primary-fg-color)"/>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="46" y="22" text-anchor="middle">F₁</text><text x="100" y="22" text-anchor="middle">F₂</text>
  </g>
  <text x="66" y="102" text-anchor="middle" style="font:700 13px system-ui,sans-serif" fill="var(--md-primary-fg-color)">R</text>
</svg>
<figcaption><b>Gleiche Richtung:</b> Längen <b>zusammenzählen</b>, Richtung bleibt.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 120" role="img" aria-label="Entgegengesetzte Kräfte subtrahieren sich" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="20" y1="30" x2="126" y2="30"/><line x1="130" y1="52" x2="74" y2="52" stroke-dasharray="5 4"/>
  </g>
  <path d="M130,30 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M70,52 l9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <line x1="20" y1="86" x2="64" y2="86" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M70,86 l-10,-5 v10 z" fill="var(--md-primary-fg-color)"/>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="72" y="22" text-anchor="middle">F₁</text><text x="102" y="70" text-anchor="middle">F₂</text>
  </g>
  <text x="42" y="108" text-anchor="middle" style="font:700 13px system-ui,sans-serif" fill="var(--md-primary-fg-color)">R</text>
</svg>
<figcaption><b>Gegenrichtung:</b> Längen <b>abziehen</b>, Richtung der grösseren Kraft.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 190 120" role="img" aria-label="Rechtwinklige Kräfte ergeben eine Diagonale" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color)" stroke-width="2.5" fill="none" stroke-linecap="round">
    <line x1="30" y1="95" x2="96" y2="95"/><line x1="100" y1="95" x2="100" y2="45" stroke-dasharray="5 4"/>
  </g>
  <path d="M100,95 l-9,-4.5 v9 z" fill="var(--md-default-fg-color)"/>
  <path d="M100,40 l-4.5,9 h9 z" fill="var(--md-default-fg-color)"/>
  <line x1="30" y1="95" x2="97" y2="46" stroke="var(--md-primary-fg-color)" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M102,40 l-10,2 l5,8 z" fill="var(--md-primary-fg-color)"/>
  <path d="M92,95 v-8 h8" fill="none" stroke="var(--md-default-fg-color--light)" stroke-width="1.5"/>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="60" y="112" text-anchor="middle">F₁</text><text x="108" y="72">F₂</text>
  </g>
  <text x="52" y="60" style="font:700 13px system-ui,sans-serif" fill="var(--md-primary-fg-color)">R</text>
</svg>
<figcaption><b>Rechter Winkel:</b> <b>Diagonale</b> des Rechtecks (Pythagoras).</figcaption>
</figure>

</div>

### Und wenn es schräg und gegenläufig ist?

Dann zerlege jeden Pfeil in **waagrecht** und **senkrecht** und rechne die beiden Richtungen
**getrennt** zusammen:

1. Kästchen zählen: F₁ = 3 nach rechts, 0 senkrecht.
2. Kästchen zählen: F₂ = 3 nach links, 2 nach unten.
3. Waagrecht: 3 rechts − 3 links = **0**. Senkrecht: **2 nach unten**.
4. Ergebnis: ein Pfeil **senkrecht nach unten**, Länge 2 Kästchen.

!!! danger "Die Falle, die am meisten kostet"
    Eine schräge Linie sagt **nichts** über die Richtung. **Suche immer die Pfeilspitze.**
    Ein Pfeil, dessen Linie "nach oben rechts" aussieht, kann sehr wohl nach **unten links**
    zeigen — und dann kommt eine völlig andere Resultierende heraus.

**Prüfungstaktik:** Bestimme zuerst nur die **Richtung** der Resultierenden. Meistens fallen
damit schon 3 von 4 Antworten weg. Erst wenn zwei Kandidaten dieselbe Richtung haben, musst du
Kästchen zählen.

---

## 6 · Rezept: Bilderfragen zum Profil

### Die Begriffe am Profil

<figure markdown="span">
<svg viewBox="0 0 440 210" role="img" aria-label="Flügelprofil mit Bezeichnungen: Nase, Hinterkante, Profilsehne, Profiltiefe, Profildicke, Skelettlinie" style="max-width:100%;height:auto">
  <line x1="20" y1="105" x2="330" y2="105" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="14 4 3 4"/>
  <path d="M40,105 C 60,77 120,67 180,73 C 225,78 262,93 300,105 C 260,112 200,116 140,114 C 90,112 55,109 40,105 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2.5"/>
  <path d="M40,105 C 90,89 170,86 300,105" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="4 3"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.5" fill="none">
    <line x1="40" y1="150" x2="300" y2="150"/>
    <line x1="180" y1="73" x2="180" y2="115"/>
  </g>
  <path d="M40,150 l9,-4 v8 z M300,150 l-9,-4 v8 z" fill="var(--md-default-fg-color)"/>
  <path d="M180,73 l-4,9 h8 z M180,115 l-4,-9 h8 z" fill="var(--md-default-fg-color)"/>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1" fill="none">
    <path d="M40,105 L28,62"/><path d="M300,105 L340,72"/><path d="M120,92 L120,40"/><path d="M330,105 L360,128"/>
  </g>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="26" y="56" text-anchor="middle">Nase</text>
    <text x="344" y="68">Hinterkante</text>
    <text x="120" y="34" text-anchor="middle" fill="var(--md-primary-fg-color)">Skelettlinie</text>
    <text x="364" y="132">Profilsehne</text>
    <text x="170" y="167" text-anchor="end">Profiltiefe</text>
    <text x="192" y="98">Profildicke</text>
  </g>
</svg>
<figcaption>Die <b>Profilsehne</b> ist die Strich-Punkt-<b>Linie</b> von der Nase zur Hinterkante — sie ragt in Zeichnungen vorn und hinten über das Profil hinaus. Die <b>Profiltiefe</b> ist die <b>Länge</b> dieser Linie. Der Abstand zwischen Sehne und Skelettlinie ist die <b>Wölbung</b>.</figcaption>
</figure>

| Begriff | in einfachen Worten |
|---|---|
| **Profilsehne** | die gedachte **Linie** von der Nase zur Hinterkante |
| **Profiltiefe** | die **Länge** dieser Linie (also eine Zahl in Metern) |
| **Profildicke** | grösster Abstand zwischen Ober- und Unterseite |
| **Skelettlinie** | Mittellinie zwischen Ober- und Unterseite |
| **Wölbung** | wie weit die Skelettlinie von der Sehne weg ist |
| relative Dicke | Dicke ÷ Tiefe, beim Gleitschirm **15–18 %** (also ein "dickes" Profil) |

!!! danger "Die teuerste Falle im ganzen Fach"
    **Die Prüfung benutzt für verschiedene Fragen verschiedene Profilzeichnungen — mit
    unterschiedlicher Numerierung.** Zwei Bilder können fast gleich aussehen und trotzdem die
    Ziffern 1–4 anders verteilen.

    **Rezept: bei jeder Skizzenfrage die Zeichnung neu lesen.** Nie eine Ziffer aus einer anderen
    Frage übernehmen. Die Zeichnung selbst verrät alles:

    - **Doppelpfeil** = eine gemessene **Länge** (Tiefe oder Dicke)
    - **waagrecht** = Tiefe · **senkrecht** = Dicke
    - **Strich-Punkt-Linie, die über das Profil hinausragt** = **Sehne** (in technischen
      Zeichnungen ist das immer eine Bezugsachse)
    - **Punkt/Pfeil auf eine Stelle der Kontur** = Nase oder Hinterkante
    - **dünne Kurve im Innern** = Skelettlinie

### Warum ist ein Gleitschirmprofil dick und gewölbt?

Weil wir **langsam** fliegen. In der Auftriebsformel steht v² — wenig Geschwindigkeit muss durch
einen **hohen c<sub>A</sub>** ausgeglichen werden, und den liefert ein dickes, stark gewölbtes
(**asymmetrisches**) Profil. Dicke Profile reissen zudem gutmütiger ab.

Symmetrische Profile gibt es nur im Kunstflug — ein symmetrisches Profil erzeugt bei 0°
Anstellwinkel **keinen** Auftrieb. Ein gewölbtes schon; bei ihm liegt der Nullauftrieb erst bei
etwa −3° bis −5°.

---

## 7 · Rezept: die vier Punkte am Profil

<figure markdown="span">
<svg viewBox="0 0 420 220" role="img" aria-label="Profil bei grossem Anstellwinkel mit Staupunkt, Umschlagpunkt, Ablösepunkt, Druckpunkt und Totwasser" style="max-width:100%;height:auto">
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.5" fill="none">
    <path d="M10,40 C 90,40 130,30 200,26 C 270,22 330,26 410,30"/>
    <path d="M10,72 C 90,72 120,54 190,48"/>
    <path d="M10,150 C 90,150 140,152 200,158 C 270,164 340,170 410,174"/>
    <path d="M10,182 C 100,182 150,186 220,190 C 290,194 350,196 410,198"/>
  </g>
  <path d="M12,40 l0,0" fill="none"/>
  <path d="M100,127 C 118,96 150,78 196,72 C 236,68 268,84 300,128 C 258,132 180,134 100,127 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2.5"/>
  <line x1="100" y1="127" x2="300" y2="128" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g fill="none" stroke="var(--md-default-fg-color--light)" stroke-width="1.5">
    <path d="M312,60 a7,7 0 1,1 -0.1,0"/><path d="M336,76 a7,7 0 1,1 -0.1,0"/>
    <path d="M330,50 a6,6 0 1,1 -0.1,0"/><path d="M360,66 a8,8 0 1,1 -0.1,0"/>
    <path d="M356,92 a7,7 0 1,1 -0.1,0"/><path d="M384,54 a7,7 0 1,1 -0.1,0"/>
    <path d="M382,82 a6,6 0 1,1 -0.1,0"/>
  </g>
  <g fill="var(--md-primary-fg-color)" stroke="var(--md-default-bg-color)" stroke-width="2">
    <circle cx="104" cy="124" r="5.5"/><circle cx="160" cy="86" r="5.5"/>
    <circle cx="215" cy="70" r="5.5"/><circle cx="163" cy="128" r="5.5"/>
  </g>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1" fill="none">
    <path d="M104,124 L52,156"/><path d="M160,86 L142,32"/><path d="M215,70 L268,34"/><path d="M163,128 L150,182"/>
  </g>
  <g style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">
    <text x="48" y="170" text-anchor="middle">Staupunkt</text>
    <text x="140" y="26" text-anchor="middle">Umschlagpunkt</text>
    <text x="272" y="28">Ablösepunkt</text>
    <text x="146" y="196" text-anchor="middle">Druckpunkt</text>
    <text x="352" y="118" text-anchor="middle" fill="var(--md-default-fg-color--light)">Totwasser</text>
  </g>
</svg>
<figcaption>Von vorn nach hinten: <b>Staupunkt</b> → laminare Grenzschicht → <b>Umschlagpunkt</b> → turbulente Grenzschicht → <b>Ablösepunkt</b> → Wirbel. Der <b>Druckpunkt</b> liegt auf der Sehne, nicht auf der Oberfläche.</figcaption>
</figure>

| Punkt | Was dort passiert | Woran du ihn im Bild erkennst |
|---|---|---|
| **Staupunkt** | Die Luft wird auf null abgebremst und **teilt sich** in Ober- und Unterseite | vorn an der **Nase**, meist etwas auf der **Unterseite** |
| **Umschlagpunkt** | Die Grenzschicht wechselt von **laminar zu turbulent** | oben, vor dem Ablösepunkt |
| **Ablösepunkt** | Die **Strömung löst sich** vom Flügel, dahinter Wirbel | oben, dort wo die Wirbel beginnen |
| **Druckpunkt** | **Angriffspunkt der Luftkraft** | auf der **Sehne** (der gestrichelten Linie **im** Profil) |

Es gibt auch einen **hinteren Staupunkt**: an der Hinterkante, wo Ober- und Unterseitenströmung
wieder zusammentreffen. Wenn eine Frage nach dem "vorderen" Staupunkt fragt, ist genau das
der Grund.

**Wie die Punkte wandern** — Staupunkt und Druckpunkt laufen **gegeneinander**:

| Anstellwinkel | Staupunkt | Druckpunkt | Ablösepunkt |
|---|---|---|---|
| **grösser** (langsam, Bremsen ziehen) | auf der Unterseite **nach hinten** | nach **vorn** | nach **vorn** |
| **kleiner** (beschleunigen) | **nach vorn zur Nase**, dann auf die Oberseite | nach **hinten** | nach hinten |

**Und was das praktisch heisst:**

- Wandert der Staupunkt bei sehr kleinem Anstellwinkel über die Nase auf die Oberseite, werden
  die Eintrittsöffnungen nicht mehr angeströmt → Innendruck fällt → **Frontklapper**.
  Darum in Turbulenz den Beschleuniger zurücknehmen.
- Erreicht der Ablösepunkt die Nase, ist der ganze Flügel abgelöst → **Strömungsabriss**.

---

## 8 · Rezept: Druckverteilungs-Bilder lesen

In diesen Bildern stehen kleine Pfeile senkrecht auf der Profiloberfläche.

!!! tip "Die zwei Regeln"
    **Pfeil zeigt vom Profil weg = Unterdruck (Sog).**
    **Pfeil zeigt zum Profil hin = Überdruck.**

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 200 140" role="img" aria-label="Negativer Anstellwinkel: Ueberdruck oben, Sog unten" style="max-width:100%;height:auto">
  <path d="M30,70 C 46,55 90,49 130,53 C 158,56 180,64 196,70 C 168,75 120,78 78,77 C 52,76 36,73 30,70 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.6" fill="none">
    <line x1="60" y1="34" x2="60" y2="56"/><line x1="90" y1="30" x2="90" y2="51"/>
    <line x1="120" y1="31" x2="120" y2="52"/><line x1="150" y1="38" x2="150" y2="58"/>
    <line x1="70" y1="78" x2="70" y2="102"/><line x1="100" y1="79" x2="100" y2="106"/>
    <line x1="130" y1="77" x2="130" y2="100"/>
  </g>
  <g fill="var(--md-default-fg-color)">
    <path d="M60,60 l-4,-8 h8 z"/><path d="M90,55 l-4,-8 h8 z"/><path d="M120,56 l-4,-8 h8 z"/><path d="M150,62 l-4,-8 h8 z"/>
    <path d="M70,106 l-4,-8 h8 z"/><path d="M100,110 l-4,-8 h8 z"/><path d="M130,104 l-4,-8 h8 z"/>
  </g>
  <text x="100" y="20" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">Überdruck oben</text>
  <text x="100" y="130" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">Sog unten</text>
</svg>
<figcaption><b>Negativer</b> Anstellwinkel (z. B. −10°): Bild <b>umgekehrt</b>, der Flügel wird nach <b>unten</b> gedrückt.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 200 140" role="img" aria-label="Anstellwinkel etwa null Grad" style="max-width:100%;height:auto">
  <path d="M30,80 C 46,63 90,55 130,59 C 158,62 180,72 196,80 C 168,85 120,88 78,87 C 52,86 36,83 30,80 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M34,74 C 60,44 120,36 176,60 C 190,66 196,74 196,80" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="1.5" stroke-dasharray="4 3"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.6" fill="none">
    <line x1="60" y1="62" x2="60" y2="46"/><line x1="90" y1="55" x2="90" y2="40"/>
    <line x1="120" y1="56" x2="120" y2="42"/><line x1="150" y1="66" x2="150" y2="54"/>
    <line x1="70" y1="96" x2="70" y2="104"/><line x1="100" y1="97" x2="100" y2="105"/>
    <line x1="130" y1="95" x2="130" y2="103"/>
  </g>
  <g fill="var(--md-default-fg-color)">
    <path d="M60,42 l-4,8 h8 z"/><path d="M90,36 l-4,8 h8 z"/><path d="M120,38 l-4,8 h8 z"/><path d="M150,50 l-4,8 h8 z"/>
    <path d="M70,92 l-4,8 h8 z"/><path d="M100,93 l-4,8 h8 z"/><path d="M130,91 l-4,8 h8 z"/>
  </g>
  <text x="100" y="26" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">Sog oben</text>
  <text x="100" y="130" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">unten dünn</text>
</svg>
<figcaption><b>Etwa 0°:</b> Sog oben schon vorhanden, die Überdruckzone unten aber nur <b>flach und dünn</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 200 140" role="img" aria-label="Grosser Anstellwinkel" style="max-width:100%;height:auto">
  <path d="M30,92 C 50,70 92,58 132,60 C 160,62 180,74 196,86 C 166,92 118,96 76,96 C 50,96 36,95 30,92 Z"
        fill="var(--md-primary-fg-color)" fill-opacity="0.08" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M18,86 C 30,34 110,20 176,52 C 190,60 196,76 196,86" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="1.5" stroke-dasharray="4 3"/>
  <g stroke="var(--md-default-fg-color)" stroke-width="1.6" fill="none">
    <line x1="40" y1="80" x2="30" y2="52"/><line x1="62" y1="66" x2="58" y2="34"/>
    <line x1="92" y1="59" x2="92" y2="26"/><line x1="122" y1="59" x2="126" y2="28"/>
    <line x1="152" y1="68" x2="158" y2="44"/>
    <line x1="70" y1="98" x2="70" y2="118"/><line x1="100" y1="98" x2="100" y2="122"/>
    <line x1="130" y1="96" x2="130" y2="118"/>
  </g>
  <g fill="var(--md-default-fg-color)">
    <path d="M29,47 l-3,9 l8,-2 z"/><path d="M57,29 l-4,9 l8,-1 z"/><path d="M92,22 l-4,8 h8 z"/>
    <path d="M127,23 l-5,8 l8,1 z"/><path d="M159,39 l-5,8 l8,1 z"/>
    <path d="M70,122 l-4,-8 h8 z"/><path d="M100,126 l-4,-8 h8 z"/><path d="M130,122 l-4,-8 h8 z"/>
  </g>
  <text x="100" y="16" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">Sog greift nach vorn</text>
  <text x="100" y="136" text-anchor="middle" style="font:600 12px system-ui,sans-serif" fill="var(--md-default-fg-color)">unten dick</text>
</svg>
<figcaption><b>Grosser</b> Anstellwinkel: die Sogzone reicht <b>vor die Nase</b>, unten eine <b>dicke</b> Überdruckzone.</figcaption>
</figure>

</div>

**Vorgehen**

1. **Wo ist der Sog?** Oben ⇒ positiver Anstellwinkel. Unten (und oben Überdruck) ⇒
   **negativer** Anstellwinkel.
2. **Wie gross ist der Anstellwinkel?** Nicht nach der Höhe der Sogfläche gehen! Die zwei
   verlässlichen Merkmale sind:
   - **wie weit die Sogzone nach vorn über die Nase greift** (weiter vorn = grösser)
   - **wie dick die Überdruckzone unten ist** (dicker = grösser)
3. Bei "etwa 0°": Sog oben ist da, aber unten **flach und dünn**.

!!! warning "Genau hier habe ich mich vertan"
    Nach der blossen **Höhe** der Sogfläche zu sortieren führt in die Irre. Entscheidend ist,
    **wie weit vorn** der Sog ansetzt.

### Wo entsteht der Auftrieb?

Zwei Zahlen, zwei verschiedene Aussagen — nicht verwechseln:

| Richtung | Verteilung |
|---|---|
| oben ↔ unten | **2/3 Oberseite (Sog)**, 1/3 Unterseite |
| vorn ↔ hinten | **2/3 im vordersten Drittel** |

Der Auftrieb sitzt also **vorne oben**: der Flügel wird **gesaugt**, nicht gedrückt.
Deshalb liegt der Druckpunkt bei ~25–30 % der Tiefe, tragen die **A-Leinen** die Hauptlast, ist
das **Obersegel** der kritische Bereich, und deshalb beginnen Frontklapper vorn.

---

## 9 · Rezept: Kräfte im Gleitflug

<figure markdown="span">
<svg viewBox="0 0 420 280" role="img" aria-label="Kraeftegleichgewicht im stationaeren Gleitflug mit Auftrieb, Widerstand, Resultierende, Gewicht, Anstellwinkel und Gleitwinkel" style="max-width:100%;height:auto">
  <line x1="20" y1="258" x2="400" y2="258" stroke="var(--md-default-fg-color--light)" stroke-width="2"/>
  <text x="396" y="272" text-anchor="end" style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">Horizont</text>
  <line x1="50" y1="70" x2="200" y2="70" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <line x1="50" y1="70" x2="350" y2="180" stroke="var(--md-default-fg-color--light)" stroke-width="1.5" stroke-dasharray="6 4"/>
  <path d="M50,70 m40,0 a40,40 0 0,1 -2.9,14.6" fill="none" stroke="var(--md-default-fg-color)" stroke-width="1.5"/>
  <text x="98" y="86" style="font:italic 600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">γ</text>
  <text x="120" y="62" style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">Waagrechte</text>
  <text x="248" y="168" style="font:400 11px system-ui,sans-serif" fill="var(--md-default-fg-color--light)">Flugbahn = Anströmung</text>
  <g transform="translate(230,150) rotate(20)">
    <path d="M28,0 C 12,-10 -34,-13 -66,-5 C -44,5 -6,8 28,0 Z"
          fill="var(--md-primary-fg-color)" fill-opacity="0.12" stroke="var(--md-default-fg-color)" stroke-width="2"/>
    <line x1="-72" y1="-2" x2="40" y2="-2" stroke="var(--md-default-fg-color--light)" stroke-width="1.2" stroke-dasharray="8 3 2 3"/>
  </g>
  <path d="M230,150 m34,0 a34,34 0 0,0 -2,-11" fill="none" stroke="var(--md-default-fg-color)" stroke-width="1.5"/>
  <text x="272" y="146" style="font:italic 600 13px system-ui,sans-serif" fill="var(--md-default-fg-color)">α</text>
  <g stroke="var(--md-default-fg-color--light)" stroke-width="1.2" stroke-dasharray="4 3" fill="none">
    <line x1="259" y1="71" x2="230" y2="60"/><line x1="201" y1="139" x2="230" y2="60"/>
  </g>
  <g stroke-width="3" fill="none" stroke-linecap="round">
    <line x1="230" y1="150" x2="255" y2="76" stroke="var(--md-default-fg-color)"/>
    <line x1="230" y1="150" x2="205" y2="140" stroke="var(--md-default-fg-color)"/>
    <line x1="230" y1="150" x2="230" y2="66" stroke="var(--md-primary-fg-color)" stroke-width="3.5"/>
    <line x1="230" y1="150" x2="230" y2="232" stroke="var(--md-default-fg-color)"/>
  </g>
  <path d="M259,68 l-9,3 l6,7 z" fill="var(--md-default-fg-color)"/>
  <path d="M199,138 l8,-5 l1,9 z" fill="var(--md-default-fg-color)"/>
  <path d="M230,60 l-5,10 h10 z" fill="var(--md-primary-fg-color)"/>
  <path d="M230,240 l-5,-10 h10 z" fill="var(--md-default-fg-color)"/>
  <g style="font:700 15px system-ui,sans-serif">
    <text x="266" y="66" fill="var(--md-default-fg-color)">A</text>
    <text x="182" y="132" fill="var(--md-default-fg-color)">W</text>
    <text x="238" y="72" fill="var(--md-primary-fg-color)">R</text>
    <text x="238" y="228" fill="var(--md-default-fg-color)">G</text>
  </g>
</svg>
<figcaption><b>A</b> Auftrieb (senkrecht zur Anströmung) · <b>W</b> Widerstand (entlang der Anströmung, nach hinten) · <b>R</b> Luftkraftresultierende = A ⊕ W · <b>G</b> Gewichtskraft. <b>α</b> Anstellwinkel (Anströmung ↔ Sehne) · <b>γ</b> Gleitwinkel (Flugbahn ↔ Waagrechte).</figcaption>
</figure>

**Die Regeln, die alle Fragen dazu beantworten**

1. **Auftrieb steht senkrecht zur Anströmung**, **Widerstand liegt in Strömungsrichtung** nach
   hinten. Sie stehen also **rechtwinklig aufeinander**.
2. Beide zusammen (vektoriell) ergeben die **Luftkraftresultierende R**.
3. Im **stationären** Gleitflug (also immer, wenn nichts beschleunigt) ist
   **R genau so gross wie das Gewicht G** und zeigt entgegengesetzt.
4. Deshalb: **R ändert sich nicht**, wenn man beschleunigt — nur die **Aufteilung** in A und W
   und damit der Gleitwinkel.

!!! warning "Drei feine Unterschiede, die geprüft werden"
    - **Nicht** "der Auftrieb = das Gewicht". Der Auftrieb allein ist etwas **kleiner** als G.
      Erst A **und** W zusammen ergeben G.
    - Das **Gewicht ist keine Luftkraft** — es ist eine Massenkraft. Die Luftkraft besteht nur
      aus Auftrieb und Widerstand.
    - Bezugssystem ist immer die **Anströmung**, nicht der Horizont. Der Auftrieb ist nur im
      Horizontalflug senkrecht nach oben.

### Die drei Winkel auseinanderhalten

| Winkel | zwischen | Was er ist |
|---|---|---|
| **Anstellwinkel** (α) | Profilsehne ↔ **Anströmung** | ein **Flugzustand** — ändert sich im Flug |
| **Gleitwinkel** (γ) | Flugbahn ↔ **Waagrechte** | das **Leistungsmass** |
| **Einstellwinkel** | Profilsehne ↔ Geräte-Längsachse | **fest gebaut** |

### Anstellwinkel und Geschwindigkeit hängen zusammen

!!! tip "Der Satz, der vier Fragen löst"
    **Anstellwinkel grösser ⇒ c<sub>A</sub> grösser ⇒ langsamer** (Bremsen ziehen).
    **Anstellwinkel kleiner ⇒ c<sub>A</sub> kleiner ⇒ schneller** (Beschleuniger).

Man steuert also nicht "Gas", sondern den **Anstellwinkel**. Und: c<sub>A</sub> steigt mit dem
Anstellwinkel **gleichmässig an — bis zum kritischen Anstellwinkel** (ca. 15–18°). Dort bricht
er ein: **Strömungsabriss**.

### Strömungsabriss und Zuladung

> **mittlere Fl&uuml;geltiefe  =  Fl&auml;che  &divide;  Spannweite**

| Zuladung | Überziehgeschwindigkeit | Anstellwinkel beim Abriss |
|---|---|---|
| minimal | **tiefer** | **gleich** |
| maximal | **höher** | **gleich** |

!!! warning "Die halb-richtige Antwort"
    "Unabhängig von der Zuladung immer bei derselben Geschwindigkeit **und** demselben
    Anstellwinkel" ist zur Hälfte richtig und deshalb gefährlich. Richtig ist:
    **gleicher Anstellwinkel, andere Geschwindigkeit.**

### Randwirbel

**Warum sie entstehen:** Unten Überdruck, oben Unterdruck. An den **Flügelenden** ist der Flügel
zu Ende — dort weicht die Luft von unten nach oben aus und rollt sich zum Wirbel auf. Das ist
keine schlechte Verarbeitung, sondern eine **unvermeidliche Folge des Auftriebs**.

**Wo sie sind:** **hinter der Austrittskante**.

**Was sie kosten:** den **induzierten Widerstand** — der einzige Widerstandsanteil, der bei
**langsamem** Flug **zunimmt**. Grosse Streckung verkleinert seinen Anteil; das ist der
eigentliche Grund für lange, schmale Flügel.

---

## 10 · Rezepte: Geometrie und Gewicht

### Rezept — mittlere Flügeltiefe

> **Streckung  =  Spannweite&sup2;  &divide;  Fl&auml;che  =  Spannweite  &divide;  mittlere Fl&uuml;geltiefe**

Beispiel: 25 m² ÷ 10 m = **2,50 m**. · 12,5 m² ÷ 10 m = **1,25 m**.

### Rezept — Streckung

> **Fl&auml;chenbelastung  =  (Zuladung + Ger&auml;tegewicht)  &divide;  Fl&auml;che**

**Vorgehen**

1. Spannweite **quadrieren**.
2. Durch die Fläche teilen.

Beispiel: 10² ÷ 25 = **4,0**. · 12² ÷ 24 = **6,0**. · 8² ÷ 32 = **2,0**.

**Ohne Rechnen erkennen:** *grösste* Streckung = **grosse Spannweite bei kleiner Fläche**;
*kleinste* Streckung = **kurz und breit**.

In Worten heisst Streckung 5: **"Die Spannweite ist 5 mal grösser als die mittlere Flügeltiefe."**

| Gerät | übliche Streckung |
|---|---|
| Schul-/Anfänger-Gleitschirm | 4,5 – 5 |
| **Intermediate-Gleitschirm** | **5 – 6** |
| Hochleistung / Wettkampf | 6,5 – 7,5 |
| **Intermediate-Delta (Hängegleiter)** | **ca. 7** |
| Segelflugzeug | 20 – 30 |

!!! warning "Zwei Fallen"
    - **Spannweite quadrieren nicht vergessen** — das ist der häufigste Rechenfehler.
    - **Gleitschirm 5–6, Delta 7.** Beide Fragen kommen vor.

**Was Streckung bewirkt:** grosse Streckung ⇒ weniger induzierter Widerstand ⇒ **bessere
Gleitzahl**, aber **klappanfälliger** und heftigere Reaktionen. Gleitleistung kauft man mit
Klappanfälligkeit — genau darum dreht sich die EN-Klassifizierung.

**Projizierte Fläche** = der Schattenwurf des Flügels von oben im Flug. Weil der Flügel im Flug
**gewölbt** ist, ist sie **kleiner oder gleich** der ausgelegten Fläche (Gleitschirm ca. 80–85 %).
Die Richtung gilt bei Delta und Gleitschirm **gleich**, nur unterschiedlich stark.

### Rezept — Flächenbelastung

> **Lastvielfaches  =  Belastung im Flug  &divide;  Gesamtgewicht am Boden**

**Vorgehen**

1. **Gerätegewicht dazuzählen!** "Zuladung" ist Pilot + Ausrüstung **ohne** das Gerät.
2. Fragt die Aufgabe nach **minimaler** oder **maximaler** Zuladung? Zweimal lesen.
3. Durch die Fläche teilen. Einheit **kg/m²**.

| Gerät | Zuladung | + Gerät | ÷ Fläche | Ergebnis |
|---|---|---|---|---|
| Gleitschirm | 70 kg | + 5 kg = 75 | 25 m² | **3,0 kg/m²** |
| Gleitschirm | 95 kg | + 5 kg = 100 | 25 m² | **4,0 kg/m²** |
| Delta | 65 kg | + 35 kg = 100 | 12,5 m² | **8 kg/m²** |
| Delta | 90 kg | + 35 kg = 125 | 12,5 m² | **10 kg/m²** |

!!! danger "Die zwei sicheren Fallen"
    1. **Gerätegewicht vergessen** — beim Delta sind das 35 kg, das verfälscht alles.
    2. **min statt max** (oder umgekehrt) — **beide** Ergebnisse stehen jeweils als Antwort da.

**Was Flächenbelastung bewirkt:** alle Geschwindigkeiten wachsen mit **√Flächenbelastung** —
Trimm-, End- und Überziehgeschwindigkeit höher, Sinken höher, **Gleitzahl gleich**.
Vorteil: turbulenz- und windstabiler. Nachteil: schwache Thermik schlechter nutzbar, schnellere
Landung, längere Startstrecke.

### Rezept — Lastvielfaches

> **&Uuml;berziehgeschwindigkeit  w&auml;chst mit  &radic;Fluggewicht**

Beispiel: 250 kg ÷ 100 kg = **2,5**. Das Ergebnis ist eine **reine Zahl ohne Einheit** — darum
sind "25", "250" und "0,25" typische Zahlendreher-Distraktoren.

| Situation | Lastvielfaches |
|---|---|
| Geradeausflug | **1,0** |
| 30° Querlage | ca. 1,15 |
| 45° Querlage | ca. 1,4 |
| 60° Querlage | **2,0** |
| grosse Querlage / Steilspirale | **2,5 – 4+** |

**Beim Übergang in die Kurve nehmen Flächenbelastung UND minimale Fluggeschwindigkeit zu.**
Weil v<sub>Abriss</sub> mit √Lastvielfaches wächst, überzieht ein Schirm bei 2,5 g rund **58 %**
schneller als geradeaus — das ist die Ursache des Strömungsabrisses beim zu langsamen Kurbeln.

Nicht verwechseln: **Lastvielfaches** (Zahl) · **Flächenbelastung** (kg/m²) ·
**Bruchlast/Prüflast** (Gleitschirm 8 g).

### Die vier Definitionen, die sich gegenseitig als Distraktoren dienen

| Begriff | Definition |
|---|---|
| **Spannweite** | Abstand zwischen linkem und rechtem Flügelende |
| **mittlere Flügeltiefe** | durchschnittlicher Abstand Nase ↔ Hinterkante |
| **Flächenbelastung** | Gesamtgewicht ÷ Flügelfläche |
| **Verwindung / Schränkung** | Anstellwinkel**unterschiede** verschiedener Flügelabschnitte |

In diesen Fragen stehen **immer dieselben vier Antworten**, nur die Frage wechselt. Wer die vier
Zeilen sicher kann, holt mehrere Punkte fast ohne Aufwand.

---

## 11 · Achsen und Stabilität — geschenkte Punkte

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;align-items:start">

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 150 150" role="img" aria-label="Laengsachse: rollen" style="max-width:100%;height:auto">
  <line x1="75" y1="14" x2="75" y2="140" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="7 4"/>
  <ellipse cx="75" cy="68" rx="54" ry="11" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <rect x="71" y="60" width="8" height="46" rx="4" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M112,110 a30,30 0 0,1 -46,10" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M66,120 l10,-4 l-1,9 z" fill="var(--md-default-fg-color)"/>
</svg>
<figcaption><b>Längsachse</b> — in Flugrichtung.<br>Bewegung: <b>rollen</b>.<br>Stabilität: <b>rollstabil</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 150 150" role="img" aria-label="Querachse: nicken" style="max-width:100%;height:auto">
  <line x1="10" y1="68" x2="140" y2="68" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="7 4"/>
  <ellipse cx="75" cy="68" rx="54" ry="11" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <rect x="71" y="60" width="8" height="46" rx="4" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M112,40 a30,30 0 0,0 -8,-20" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M104,16 l8,6 l-9,4 z" fill="var(--md-default-fg-color)"/>
  <path d="M112,96 a30,30 0 0,1 -8,20" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M104,120 l8,-6 l-9,-4 z" fill="var(--md-default-fg-color)"/>
</svg>
<figcaption><b>Querachse</b> — quer zur Flugrichtung.<br>Bewegung: <b>nicken</b>.<br>Stabilität: <b>nick-/pitchstabil</b>.</figcaption>
</figure>

<figure markdown="span" style="margin:0">
<svg viewBox="0 0 150 150" role="img" aria-label="Hochachse: gieren" style="max-width:100%;height:auto">
  <circle cx="75" cy="68" r="9" fill="none" stroke="var(--md-primary-fg-color)" stroke-width="2" stroke-dasharray="5 3"/>
  <line x1="75" y1="59" x2="75" y2="77" stroke="var(--md-primary-fg-color)" stroke-width="1.5"/>
  <line x1="66" y1="68" x2="84" y2="68" stroke="var(--md-primary-fg-color)" stroke-width="1.5"/>
  <ellipse cx="75" cy="68" rx="54" ry="11" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <rect x="71" y="60" width="8" height="46" rx="4" fill="var(--md-primary-fg-color)" fill-opacity="0.10" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M75,124 a42,42 0 0,0 40,-30" fill="none" stroke="var(--md-default-fg-color)" stroke-width="2"/>
  <path d="M117,90 l-1,10 l-8,-5 z" fill="var(--md-default-fg-color)"/>
</svg>
<figcaption><b>Hochachse</b> — senkrecht.<br>Bewegung: <b>gieren</b>.<br>Stabilität: <b>richtungsstabil</b>.</figcaption>
</figure>

</div>

Merkhilfe: **Hoch**achse = Drehung wie ein **Karussell** = **gieren**.

!!! warning "Wörter, die es in dieser Systematik nicht gibt"
    **trudeln, pendeln, höhenstabil, querstabil, längsstabil** — alles reine Distraktoren.

### Stabil, labil, indifferent

| Was das Gerät nach einer Störung macht | Begriff |
|---|---|
| kehrt **von selbst zurück** (z. B. nach Lösen des Beschleunigers) | **stabil** |
| entfernt sich **immer weiter** (wird z. B. immer schneller) | **labil** |
| **bleibt** in der neuen Lage stehen | **indifferent** |
| "inverse" | gibt es nicht |

Merkbild: **stabil = Kugel in der Schüssel** · labil = Kugel auf der Kuppel ·
indifferent = Kugel auf dem Tisch.

Der **Anstellwinkel** gehört zur **Nickachse**. Ein Gerät, das ihn von selbst verändert, ist
also nicht **nickstabil**. Genau diese Stabilität sorgt beim zugelassenen Gleitschirm dafür,
dass er nach einer Störung von selbst in den Trimmflug zurückpendelt.

---

## 12 · Die vier Diagramme nicht verwechseln

| Diagramm | Achsen | Gehört zu |
|---|---|---|
| **Geschwindigkeitspolare** | vorwärts ↔ Sinken | Fluglehre — Leistung des **Geräts** |
| **Profilpolare** (Lilienthal) | c<sub>W</sub> ↔ c<sub>A</sub> | Fluglehre — Eigenschaft des **Profils** |
| **Barogramm** | Zeit ↔ Höhe | Flugaufzeichnung |
| **Emagramm** | Temperatur ↔ Druck/Höhe | **Meteorologie** |

Das **Emagramm** ist ein beliebter Distraktor in Fluglehre-Fragen — es gehört in die Meteorologie
und sagt nichts über das Fluggerät.

---

## 13 · Zahlen zum Auswendiglernen

Vier Tabellen bringen zusammen den grössten Teil der Punkte:

**1 · c<sub>W</sub>-Werte:** 1,3 (Hohlschale) · 1,0 (Platte) · 0,17 (Tropfen verkehrt) ·
0,08 (Tropfen richtig)

**2 · Polare:** 5/2,5 → GZ 2,0 · 7/1,5 → **4,6** · 9/1,7 → **5,3** · 11/2,4 → 4,6 ·
13/3,5 → 3,7

**3 · Höhenreihe:** 1'100 m → 90 % · 2'200 m → 81 % · 3'300 m → 72 % · 4'400 m → 64 % ·
5'500 m → 50 %

**4 · Kräfteskizze:** Auftrieb ⊥ Anströmung · Widerstand ∥ Anströmung · R = A ⊕ W = G ·
α an der Nase · γ am Boden

Dazu:

| Grösse | Formel |
|---|---|
| Auftrieb | c<sub>A</sub> · ½ρv² · Flügelfläche |
| Widerstand | c<sub>W</sub> · ½ρv² · Stirnfläche |
| Gleitzahl | A/W = c<sub>A</sub>/c<sub>W</sub> = vorwärts/Sinken = Strecke/Höhe |
| Streckung | Spannweite² / Fläche |
| mittlere Flügeltiefe | Fläche / Spannweite |
| Flächenbelastung | (Zuladung + Gerätegewicht) / Fläche |
| Lastvielfaches | Belastung im Flug / Gesamtgewicht |
| Reichweite | Gleitzahl × Höhe |
| Einheiten | m/s × 3,6 = km/h |

---

## 14 · Die häufigsten Fallen — Checkliste vor der Prüfung

1. **v geht im Quadrat ein, alles andere einfach.**
2. **Gerätegewicht bei der Flächenbelastung dazuzählen.**
3. **Minimale oder maximale Zuladung?** Zweimal lesen.
4. **Spannweite quadrieren** bei der Streckung.
5. **Fluggeschwindigkeit = Wurzel** aus vorwärts² + Sinken² (9,0 gegen 9,2).
6. **c<sub>W</sub>-Werte teilen**, nicht subtrahieren.
7. **Gleitzahl und Gleitwinkel laufen gegeneinander.**
8. **Geringstes Sinken ≠ bestes Gleiten** — und die Geschwindigkeit des geringsten Sinkens
   ändert sich bei Wind/Auf-/Abwind **nicht**.
9. **Strömungsabriss: gleicher Anstellwinkel, andere Geschwindigkeit.**
10. **"Schub" gibt es nicht** beim antriebslosen Gerät.
11. **R (die ganze Luftkraft) = Gewicht** — nicht der Auftrieb allein.
12. **Bezugssystem ist die Anströmung**, nicht der Horizont.
13. **Gleitschirm-Streckung 5–6, Delta 7.**
14. **Jede Skizze neu lesen** — die Numerierung wechselt von Bild zu Bild.
15. **Bei Vektorbildern die Pfeilspitze suchen**, nicht die Linienlage.
16. **Nur das ableiten, was zwingend folgt.** Aus der Gleitzahl allein folgt nichts über Sinken
    oder Geschwindigkeit.
