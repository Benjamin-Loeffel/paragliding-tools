# Sicht & Wolkenabstände – Entscheidungs-Flowchart (SHV/FSVL 2026)

Entscheidungshilfe für die Theorieprüfung Gleitschirmfliegen. Gilt für Hängegleiter/Gleitschirme, die ausschliesslich nach **Sichtflugregeln (VFR)** fliegen.

> **Merke:** Die **Flugsicht** richtet sich nach der **Höhe AMSL** (über Meer) und dem Luftraum.
> Der **Wolkenabstand** richtet sich nach **Höhe AGL** (über Grund), Luftraumklasse und ob eine **LSR for gliders** aktiv ist.

```mermaid
flowchart TD
    START([Wo fliege ich?<br/>Sicht- & Wolkenabstand bestimmen]) --> KLASSE{Luftraumklasse?}

    %% ===== LUFTRAUM G =====
    KLASSE -->|G<br/>unkontrolliert<br/>Grund bis 600 m AGL| G_HOEHE{Höhe über Grund<br/>AGL?}
    G_HOEHE -->|bis 300 m AGL| ABST_KEINE[<b>Keine festen Wolkenabstände</b><br/>aber: frei von Wolken bleiben<br/>+ Boden- oder Wassersicht]
    G_HOEHE -->|über 300 m AGL<br/>auch unter aktiver LSR!| ABST_GROSS_G[<b>Wolkenabstand</b><br/>horizontal: 1500 m<br/>vertikal: 300 m]
    ABST_KEINE --> SICHT_15[/Flugsicht: min. 1,5 km/]
    ABST_GROSS_G --> SICHT_15

    %% ===== LUFTRAUM E =====
    KLASSE -->|E<br/>kontrolliert| E_LSR{LSR for gliders<br/>aktiv?<br/>grüne Zone}

    E_LSR -->|NEIN<br/>normaler Luftraum E| ABST_GROSS_E[<b>Wolkenabstand</b><br/>horizontal: 1500 m<br/>vertikal: 300 m]
    E_LSR -->|JA<br/>aktiv 1. März - 31. Okt.<br/>SA bis SU<br/>ab 600 m AGL bis Obergrenze| ABST_REDUZIERT[<b>Reduzierter Wolkenabstand</b><br/>horizontal: 100 m<br/>vertikal: 50 m]

    ABST_GROSS_E --> E_AMSL{Höhe AMSL<br/>über Meer?}
    ABST_REDUZIERT --> E_AMSL
    E_AMSL -->|unter 3050 m AMSL| SICHT_5[/Flugsicht: 5 km/]
    E_AMSL -->|ab 3050 m AMSL| SICHT_8[/Flugsicht: 8 km/]

    %% Styling
    classDef sicht fill:#e8f0ff,stroke:#3366cc,color:#000;
    classDef abstand fill:#fff0f0,stroke:#cc3333,color:#000;
    class SICHT_15,SICHT_5,SICHT_8 sicht;
    class ABST_KEINE,ABST_GROSS_G,ABST_GROSS_E,ABST_REDUZIERT abstand;
```

## Zusammenfassung als Tabelle

| Luftraum | Höhe | Flugsicht | Wolkenabstand horizontal | Wolkenabstand vertikal |
|---|---|---|---|---|
| **G** | Grund – 300 m AGL | 1,5 km | – (frei von Wolken, Bodensicht) | – (frei von Wolken, Bodensicht) |
| **G** | 300 – 600 m AGL | 1,5 km | 1500 m | 300 m |
| **E** | unter 3050 m AMSL | 5 km | 1500 m | 300 m |
| **E** | ab 3050 m AMSL | 8 km | 1500 m | 300 m |
| **LSR for gliders** (E) | ab 600 m AGL, unter 3050 m AMSL | 5 km | **100 m** | **50 m** |
| **LSR for gliders** (E) | ab 600 m AGL, ab 3050 m AMSL | 8 km | **100 m** | **50 m** |

## Eselsbrücken / Prüfungs-Fallen

- **Sicht hängt an der Höhe AMSL:** Faustregel „**5 unten – 8 oben**“, Grenze bei **3050 m AMSL** (FL 100).
- **Luftraum G ganz unten (≤ 300 m AGL):** keine Zahlen-Abstände, nur **frei von Wolken + Boden-/Wassersicht** und **1,5 km Sicht**.
- **LSR for gliders = grüne Zone = Erleichterung:** nur die **Wolkenabstände** schrumpfen auf **100 m / 50 m**, die **Sicht bleibt** 5 bzw. 8 km.
- **Absurder Sonderfall:** Unter einer aktiven LSR for gliders gelten zwischen **300 und 600 m AGL** die **grossen** Abstände (1500/300), weil die LSR-Untergrenze seit Okt. 2017 nicht unter 600 m AGL abgesenkt werden darf.
- **Reihenfolge bei Zahlen:** horizontal ist immer die **grössere** Zahl (1500 m bzw. 100 m), vertikal die **kleinere** (300 m bzw. 50 m).
