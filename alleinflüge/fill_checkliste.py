#!/usr/bin/env python
"""Füllt die SHV-Alleinflug-Checklisten aus — Text-Overlay auf eine Kopie der Vorlage.

Beide SHV-Vorlagen sind *flache* PDFs (keine AcroForm-Felder), also wird der Text an
ausgemessenen Zellkoordinaten aufgestempelt: reportlab zeichnet ein Overlay, pypdf legt
es über die unveränderte Vorlagenseite. Die Vorlage selbst wird nie angefasst.

GRUNDSATZ: Unterschriften werden **nicht** gesetzt. «Ort, Datum» wird gefüllt, die
Unterschriftslinien bleiben leer und werden von Hand signiert.

Vorlagen (gewählt über den Schlüssel `vorlage` in den Daten):
    3x3   -> Alleinflug_Checkliste_3x3_def_DE.pdf  (SHV Sept. 2023; Fragen vorgedruckt,
                                                    14 Checkboxen zum Ankreuzen)
    2025  -> 2025_Alleinflug_Checkliste_DE.pdf     (SHV V2, Juni 2025; «Flugplanung» und
                                                    «Instruktionen für Unterwegs» als Freitext)

Beispiel:
    python fill_checkliste.py beispiel.yaml
    python fill_checkliste.py beispiel.yaml -o /tmp/probe.pdf
    python fill_checkliste.py --felder 3x3          # zeigt alle Feld-/Checkbox-Schlüssel
"""

from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph

ROOT = Path(__file__).resolve().parent

PAGE_W, PAGE_H = 595.32, 841.92  # A4, in allen Vorlagen gleich
FONT = "Helvetica"
SIZE = 10.0  # Formularfliesstext ist 11 pt; 10 pt füllt sich sauber ein und lässt Platz
PAD_X, PAD_Y = 4.0, 3.0  # Innenabstand in den Tabellenzellen
INK = black  # Ausgefülltes in Schwarz; für "sichtbar ergänzt" z. B. Color(0, .2, .45)


def _leading(size: float) -> float:
    return size * 1.24


# ---------------------------------------------------------------- Geometrie

@dataclass(frozen=True)
class Cell:
    """Zellrahmen in pdfplumber-Koordinaten (Ursprung oben links, y = `top`)."""

    x0: float
    top: float
    x1: float
    bottom: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.bottom - self.top


@dataclass(frozen=True)
class DotLine:
    """Punktlinie («…………»), auf die geschrieben wird."""

    x0: float
    x1: float
    top: float


@dataclass
class Layout:
    vorlage: str
    zellen: dict[str, Cell]
    dotlines: dict[str, DotLine]
    checkboxen: dict[str, tuple[float, float]] = field(default_factory=dict)
    # Zellen, deren Inhalt umbrechen darf (mehrzeilig / Fliesstext)
    mehrzeilig: tuple[str, ...] = ()


# Alle Koordinaten mit pdfplumber aus den Originalen ausgemessen (find_tables /
# extract_text_lines), nicht geschätzt.
LAYOUTS: dict[str, Layout] = {
    "3x3": Layout(
        vorlage="Alleinflug_Checkliste_3x3_def_DE.pdf",
        zellen={
            "fluglehrer": Cell(141.7, 142.1, 560.0, 177.5),
            "flugschueler": Cell(141.7, 177.5, 560.0, 212.9),
            "hoehenflug": Cell(141.7, 212.9, 560.0, 261.6),
            "kontakt": Cell(141.7, 549.4, 560.0, 578.3),
        },
        dotlines={
            "ort_datum_schueler": DotLine(35.4, 253.2, 663.9),
            "ort_datum_fluglehrer": DotLine(35.4, 256.1, 753.1),
        },
        checkboxen={
            # «Flugplanung» — 9 Fragen
            "wetterphaenomene": (165.3, 283.0),
            "tagesverlauf": (165.3, 296.6),
            "wettererfahrung": (165.3, 310.1),
            "flug_geplant": (165.3, 323.7),
            "selbsteinschaetzung": (165.3, 337.4),
            "plan_b": (165.3, 364.4),
            "entscheidungen": (165.3, 391.4),
            "plan_c": (165.3, 405.0),
            "mehr_zeit_info": (165.3, 418.5),
            # «Instruktionen für Unterwegs» — 5 Fragen
            "verhaeltnisse_prognose": (165.3, 462.1),
            "plan_passt": (165.3, 475.8),
            "selbsteinschaetzung_vorort": (165.3, 502.8),
            "wahrnehmungsfallen": (165.3, 529.8),
            "mehr_info": (165.3, 543.3),
        },
        mehrzeilig=("hoehenflug", "kontakt"),
    ),
    "2025": Layout(
        vorlage="2025_Alleinflug_Checkliste_DE.pdf",
        zellen={
            "fluglehrer": Cell(141.7, 126.3, 560.0, 155.1),
            "flugschueler": Cell(141.7, 155.1, 560.0, 184.0),
            "hoehenflug": Cell(141.7, 184.0, 560.0, 224.8),
            "flugplanung": Cell(141.7, 224.8, 560.0, 390.4),
            "unterwegs": Cell(141.7, 390.4, 560.0, 513.4),
            "kontakt": Cell(141.7, 513.4, 560.0, 542.4),
        },
        dotlines={
            "ort_datum_schueler": DotLine(35.4, 253.2, 638.9),
            "ort_datum_fluglehrer": DotLine(35.4, 256.1, 732.9),
        },
        mehrzeilig=("hoehenflug", "flugplanung", "unterwegs", "kontakt"),
    ),
}

# Klartext zu den Checkbox-Schlüsseln — nur für `--felder` und Fehlermeldungen.
CHECKBOX_TEXTE = {
    "wetterphaenomene": "Welche Wetterphänomene gilt es am Flugtag im Auge zu behalten?",
    "tagesverlauf": "Verändert sich das Wetter im Tagesverlauf?",
    "wettererfahrung": "Habe ich Wettererfahrung mit diesem Gebiet?",
    "flug_geplant": "Habe ich den Flug sorgfältig geplant? (Startplatz, Flugweg, Landeplatz)",
    "selbsteinschaetzung": "Selbsteinschätzung: Vorhaben vs. Fähigkeiten und Tagesform",
    "plan_b": "Plan B: Verhältnisse vor Ort entsprechen nicht meinen Erwartungen",
    "entscheidungen": "Wann und wo fälle ich Entscheidungen?",
    "plan_c": "Plan C: Wie rette ich den Tag ohne Flug?",
    "mehr_zeit_info": "Brauche ich mehr Zeit und Information?",
    "verhaeltnisse_prognose": "Entsprechen die aktuellen Verhältnisse den Prognosen?",
    "plan_passt": "Passt mein Plan noch zu den aktuellen Verhältnissen?",
    "selbsteinschaetzung_vorort": "Selbsteinschätzung vor Ort (Bauchgefühl und Verstand)",
    "wahrnehmungsfallen": "Gibt es aus der Situation mögliche Wahrnehmungsfallen?",
    "mehr_info": "Brauche ich mehr Information? Wo kriege ich diese?",
}


# ---------------------------------------------------------------- Zeichnen

def _y(top: float) -> float:
    """pdfplumber-`top` (oben links) -> reportlab-y (unten links)."""
    return PAGE_H - top


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _absaetze(text: str, size: float) -> list[Paragraph]:
    """Text -> Paragraph-Flowables.

    Zeilen mit «- » werden zu Aufzählungspunkten. **Eingerückte** Folgezeilen gehören zum
    vorherigen Absatz — so darf die YAML von Hand umbrochen sein, ohne dass daraus eigene
    Absätze werden (reportlab bricht selbst um). Nicht eingerückte Zeilen bleiben getrennt.
    """
    stil = ParagraphStyle("zelle", fontName=FONT, fontSize=size, leading=_leading(size),
                          textColor=INK, spaceAfter=1.5)
    stil_bullet = ParagraphStyle("bullet", parent=stil, leftIndent=10, bulletIndent=1)
    blocks: list[tuple[bool, str]] = []   # (ist_bullet, text)
    for zeile in str(text).splitlines():
        roh = zeile.strip()
        if not roh:
            continue
        if zeile[:1].isspace() and blocks:          # eingerückt -> an den letzten Block anhängen
            ist_bullet, vorher = blocks[-1]
            blocks[-1] = (ist_bullet, f"{vorher} {roh}")
        elif roh.startswith(("- ", "• ", "* ")):
            blocks.append((True, roh[2:].strip()))
        else:
            blocks.append((False, roh))
    return [Paragraph(_escape(t), stil_bullet, bulletText="•") if b else Paragraph(_escape(t), stil)
            for b, t in blocks]


def _zelle_schreiben(c: canvas.Canvas, cell: Cell, text: str, mehrzeilig: bool,
                     size: float) -> None:
    if not mehrzeilig and "\n" not in str(text).strip():
        # einzeilig: vertikal in der Zelle zentriert
        c.setFont(FONT, size)
        c.setFillColor(INK)
        mitte = (cell.top + cell.bottom) / 2
        c.drawString(cell.x0 + PAD_X, _y(mitte) - size * 0.34, str(text).strip())
        return
    rahmen = Frame(
        cell.x0 + PAD_X, _y(cell.bottom) + PAD_Y,
        cell.width - 2 * PAD_X, cell.height - 2 * PAD_Y,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        showBoundary=0,
    )
    fluss = _absaetze(text, size)
    rahmen.addFromList(fluss, c)
    if fluss:  # addFromList lässt übrig, was nicht mehr in die Zelle passt
        raise SystemExit(
            f"Text passt nicht in die Zelle (x0={cell.x0}, top={cell.top}): "
            f"{len(fluss)} Absatz/Absätze bleiben übrig. Text kürzen oder "
            f"'schriftgroesse' in den Daten reduzieren (aktuell {size})."
        )


def _haken(c: canvas.Canvas, x: float, top: float) -> None:
    """Häkchen als Vektorzug in die □-Box (kein Font-Glyph -> rendert überall gleich)."""
    y = _y(top)
    c.setStrokeColor(INK)
    c.setLineWidth(1.1)
    c.setLineCap(1)
    p = c.beginPath()
    p.moveTo(x + 1.2, y + 0.4)
    p.lineTo(x + 2.8, y - 1.6)
    p.lineTo(x + 6.0, y + 3.0)
    c.drawPath(p, stroke=1, fill=0)


def _dotline_schreiben(c: canvas.Canvas, dot: DotLine, text: str, size: float) -> None:
    """Schreibt über die Punktlinie.

    Die Punktglyphen sitzen auf der Grundlinie ihrer Zeile (ca. `top` + 8.6 bei 11 pt).
    Die Grundlinie des eigenen Texts muss deutlich darüber liegen, sonst streichen die
    Punkte den Text durch.
    """
    c.setFont(FONT, size)
    c.setFillColor(INK)
    c.drawString(dot.x0 + 6.0, _y(dot.top + 4.0), str(text).strip())


# ---------------------------------------------------------------- Overlay + Merge

def ausfuellen(daten: dict, ziel: Path | None = None) -> Path:
    key = str(daten.get("vorlage", "2025"))
    if key not in LAYOUTS:
        raise SystemExit(f"Unbekannte Vorlage {key!r} — erlaubt: {', '.join(LAYOUTS)}")
    layout = LAYOUTS[key]

    quelle = ROOT / layout.vorlage
    if not quelle.exists():
        raise SystemExit(f"Vorlage fehlt: {quelle}")

    felder = dict(daten.get("felder") or {})
    haken = list(daten.get("haken") or [])

    unbekannt = set(felder) - set(layout.zellen) - set(layout.dotlines)
    if unbekannt:
        raise SystemExit(f"Unbekannte Felder für Vorlage {key!r}: {sorted(unbekannt)}\n"
                         f"Erlaubt: {sorted(set(layout.zellen) | set(layout.dotlines))}")
    if haken and not layout.checkboxen:
        raise SystemExit(f"Vorlage {key!r} hat keine Checkboxen — 'haken' entfernen.")
    unbekannt = set(haken) - set(layout.checkboxen)
    if unbekannt:
        raise SystemExit(f"Unbekannte Checkboxen: {sorted(unbekannt)}\n"
                         f"Erlaubt: {sorted(layout.checkboxen)}")

    # `schriftgroesse`: eine Zahl für alles, oder ein Mapping mit optionalem `default`
    # und Feldnamen als Schlüssel (die grossen Freitextfelder brauchen kleinere Schrift).
    gr = daten.get("schriftgroesse", SIZE)
    if isinstance(gr, dict):
        default_size = float(gr.get("default", SIZE))
        pro_feld = {k: float(v) for k, v in gr.items() if k != "default"}
        unbekannt = set(pro_feld) - set(layout.zellen) - set(layout.dotlines)
        if unbekannt:
            raise SystemExit(f"schriftgroesse: unbekannte Felder {sorted(unbekannt)}")
    else:
        default_size, pro_feld = float(gr), {}

    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(PAGE_W, PAGE_H))
    for name, wert in felder.items():
        if wert is None or str(wert).strip() == "":
            continue
        size = pro_feld.get(name, default_size)
        if name in layout.zellen:
            _zelle_schreiben(c, layout.zellen[name], wert, name in layout.mehrzeilig, size)
        else:
            _dotline_schreiben(c, layout.dotlines[name], wert, size)
    for name in haken:
        _haken(c, *layout.checkboxen[name])
    c.showPage()
    c.save()
    puffer.seek(0)

    seite = PdfReader(quelle).pages[0]
    seite.merge_page(PdfReader(puffer).pages[0])
    schreiber = PdfWriter()
    schreiber.add_page(seite)

    if ziel is None:
        ziel = ROOT / f"{quelle.stem}_ausgefuellt.pdf"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "wb") as fh:
        schreiber.write(fh)
    return ziel


# ---------------------------------------------------------------- CLI

def _felder_zeigen(key: str) -> None:
    layout = LAYOUTS[key]
    print(f"Vorlage {key!r}  ->  {layout.vorlage}\n")
    print("felder: (Text)")
    for name in list(layout.zellen) + list(layout.dotlines):
        mehr = "  [mehrzeilig]" if name in layout.mehrzeilig else ""
        print(f"  {name}{mehr}")
    if layout.checkboxen:
        print("\nhaken: (anzukreuzende Fragen)")
        for name in layout.checkboxen:
            print(f"  {name:28} {CHECKBOX_TEXTE.get(name, '')}")


def _platz_zeigen(daten: dict) -> None:
    """Wieviel Raum jedes mehrzeilige Feld noch hat — bevor der Text zu lang wird."""
    layout = LAYOUTS[str(daten.get("vorlage", "2025"))]
    gr = daten.get("schriftgroesse", SIZE)
    hole = (lambda f: float(gr.get(f, gr.get("default", SIZE)))) if isinstance(gr, dict) \
        else (lambda f: float(gr))
    print(f"{'Feld':14} {'pt':>4} {'belegt':>8} {'Zelle':>8} {'Reserve':>9}  Zeilen frei")
    for name in layout.mehrzeilig:
        text = (daten.get("felder") or {}).get(name)
        if not text:
            continue
        cell = layout.zellen[name]
        size = hole(name)
        frei_h = cell.height - 2 * PAD_Y
        belegt = sum(p.wrap(cell.width - 2 * PAD_X, 10_000)[1] + p.style.spaceAfter
                     for p in _absaetze(text, size))
        rest = frei_h - belegt
        marke = "PASST" if rest >= 0 else "ZU LANG"
        print(f"{name:14} {size:4.1f} {belegt:7.1f}p {frei_h:7.1f}p {rest:+8.1f}p  "
              f"{rest / _leading(size):+5.1f}  {marke}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("daten", nargs="?", type=Path, help="YAML-Datei mit den Inhalten")
    ap.add_argument("-o", "--out", type=Path, help="Zieldatei (Standard: <Vorlage>_ausgefuellt.pdf)")
    ap.add_argument("--felder", choices=sorted(LAYOUTS),
                    help="Feld- und Checkbox-Schlüssel einer Vorlage auflisten")
    ap.add_argument("--platz", action="store_true",
                    help="nur zeigen, wieviel Platz die Freitextfelder noch haben")
    args = ap.parse_args(argv)

    if args.felder:
        _felder_zeigen(args.felder)
        return 0
    if not args.daten:
        ap.error("YAML-Datei angeben (oder --felder <vorlage>)")

    daten = yaml.safe_load(args.daten.read_text(encoding="utf-8")) or {}
    if args.platz:
        _platz_zeigen(daten)
        return 0
    ziel = ausfuellen(daten, args.out)
    print(f"geschrieben: {ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
