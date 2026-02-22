#!/usr/bin/env python3
"""Generate a clean management slide deck as a PDF (16 slides).

No external assets needed: uses simple vector shapes/icons.
Designed to be ported into DB corporate PPT template later.
"""

from __future__ import annotations

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.colors import HexColor, white, black

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "data" / "samples" / "DocGenerator_Praesentation_Chef_RapidPrototype.pdf"

ACCENT = HexColor("#4F63D7")  # indigo-ish
BG = HexColor("#F7F8FC")
TEXT = HexColor("#0F172A")
MUTED = HexColor("#475569")
CARD = white

W, H = 1280, 720  # 16:9


def draw_title(c: canvas.Canvas, title: str, subtitle: str | None = None):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # top accent bar
    c.setFillColor(ACCENT)
    c.rect(0, H - 10, W, 10, stroke=0, fill=1)

    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 42)
    c.drawString(72, H - 140, title)

    if subtitle:
        c.setFont("Helvetica", 20)
        c.setFillColor(MUTED)
        c.drawString(72, H - 180, subtitle)


def draw_footer(c: canvas.Canvas, left: str = "DocGenerator • Rapid Prototype", right: str = ""):
    c.setFillColor(HexColor("#CBD5E1"))
    c.setFont("Helvetica", 10)
    c.drawString(72, 28, left)
    if right:
        tw = c.stringWidth(right, "Helvetica", 10)
        c.drawString(W - 72 - tw, 28, right)


def section_header(c: canvas.Canvas, title: str, icon: str = ""):
    # header area
    c.setFillColor(BG)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.rect(0, H - 8, W, 8, stroke=0, fill=1)

    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(72, H - 80, title)

    if icon:
        c.setFont("Helvetica", 16)
        c.setFillColor(MUTED)
        c.drawString(72, H - 105, icon)


def card(c: canvas.Canvas, x: int, y: int, w: int, h: int, title: str):
    c.setFillColor(CARD)
    c.roundRect(x, y, w, h, 18, stroke=0, fill=1)
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x + 20, y + h - 34, title)


def bullets(c: canvas.Canvas, x: int, y: int, items: list[str], size: int = 16, leading: int = 22):
    c.setFont("Helvetica", size)
    c.setFillColor(MUTED)
    yy = y
    for it in items:
        c.circle(x, yy + 4, 3, stroke=0, fill=1)
        c.drawString(x + 12, yy, it)
        yy -= leading


def icon_magnifier(c: canvas.Canvas, x: int, y: int, s: int = 60):
    c.setStrokeColor(ACCENT)
    c.setLineWidth(6)
    c.circle(x + s * 0.35, y + s * 0.55, s * 0.22, stroke=1, fill=0)
    c.line(x + s * 0.48, y + s * 0.42, x + s * 0.70, y + s * 0.20)


def icon_shield(c: canvas.Canvas, x: int, y: int, s: int = 60):
    c.setStrokeColor(ACCENT)
    c.setLineWidth(4)
    p = c.beginPath()
    p.moveTo(x + s * 0.5, y + s * 0.85)
    p.lineTo(x + s * 0.80, y + s * 0.70)
    p.lineTo(x + s * 0.75, y + s * 0.30)
    p.lineTo(x + s * 0.5, y + s * 0.15)
    p.lineTo(x + s * 0.25, y + s * 0.30)
    p.lineTo(x + s * 0.20, y + s * 0.70)
    p.close()
    c.drawPath(p, stroke=1, fill=0)


def arrow(c: canvas.Canvas, x1, y1, x2, y2):
    c.setStrokeColor(HexColor("#94A3B8"))
    c.setLineWidth(2)
    c.line(x1, y1, x2, y2)
    # arrow head
    import math

    ang = math.atan2(y2 - y1, x2 - x1)
    ah = 10
    a1 = ang + math.pi * 0.8
    a2 = ang - math.pi * 0.8
    c.line(x2, y2, x2 + ah * math.cos(a1), y2 + ah * math.sin(a1))
    c.line(x2, y2, x2 + ah * math.cos(a2), y2 + ah * math.sin(a2))


def slide_problem(c):
    section_header(c, "Ausgangslage", "Problem")
    card(c, 72, 140, 560, 470, "Heute")
    bullets(
        c,
        100,
        560,
        [
            "Wissen steckt in PDFs und Ordnerstrukturen",
            "Suche kostet Zeit (Dateinamen, Stichworte, Lesen)",
            "Doppelarbeit bei ähnlichen Berichten",
            "Skalierung: mehr Reports ⇒ linear mehr Aufwand",
        ],
        size=16,
    )
    icon_magnifier(c, 720, 420, 140)
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(TEXT)
    c.drawString(720, 390, "Pain")
    c.setFont("Helvetica", 14)
    c.setFillColor(MUTED)
    c.drawString(720, 365, "Zeit, Qualität, Wiederverwendung")


def slide_goal(c):
    section_header(c, "Zielbild", "In Minuten statt Stunden")
    card(c, 72, 140, 1136, 470, "Was wird besser?")
    bullets(
        c,
        100,
        560,
        [
            "Semantisch finden: auch ohne exakte Schlagworte",
            "Entwürfe aus Quellen: kurz, strukturiert, nachvollziehbar",
            "Immer mit Quellen/Seiten/Nachweis",
            "Angebotsprozess: Textbausteine/Checklisten (keine Kalkulation aus Reports)",
        ],
        size=16,
    )
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 240, "Leitsatz: KI liefert Vorschläge – Entscheidungen & Freigaben bleiben beim Menschen.")


def slide_what(c):
    section_header(c, "Was ist DocGenerator?", "3 Kernfunktionen")
    card(c, 72, 190, 360, 420, "1) Ingest")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 14)
    c.drawString(92, 545, "PDFs einlesen & strukturieren")
    c.drawString(92, 520, "Abschnitte + Metadaten")

    card(c, 460, 190, 360, 420, "2) Search")
    c.setFillColor(MUTED)
    c.drawString(480, 545, "Semantische Suche")
    c.drawString(480, 520, "Treffer + Quellen")

    card(c, 848, 190, 360, 420, "3) Generate")
    c.setFillColor(MUTED)
    c.drawString(868, 545, "Berichtsentwurf")
    c.drawString(868, 520, "aus Top-Fundstellen")

    icon_magnifier(c, 520, 310, 90)
    icon_shield(c, 920, 310, 90)


def slide_arch(c):
    section_header(c, "Architektur (management-tauglich)", "lokal betreibbar • skalierbar")
    card(c, 72, 140, 1136, 470, "Datenfluss")

    # boxes
    bx_y = 420
    bx_w = 210
    gap = 60
    xs = [120, 120 + bx_w + gap, 120 + 2 * (bx_w + gap), 120 + 3 * (bx_w + gap), 120 + 4 * (bx_w + gap)]
    labels = ["PDFs", "Parser/Chunks", "DB", "Embeddings", "UI/API"]
    for x, lab in zip(xs, labels):
        c.setFillColor(white)
        c.roundRect(x, bx_y, bx_w, 80, 14, stroke=0, fill=1)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 14)
        tw = c.stringWidth(lab, "Helvetica-Bold", 14)
        c.drawString(x + (bx_w - tw) / 2, bx_y + 30, lab)

    for i in range(len(xs) - 1):
        arrow(c, xs[i] + bx_w, bx_y + 40, xs[i + 1], bx_y + 40)

    # note
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 14)
    c.drawString(120, 310, "Erklärung: Wir machen Dokumenttext maschinen-suchbar und geben Treffer + Quellen zurück.")


def slide_hallucinations(c):
    section_header(c, "Bedenken: Halluzinationen", "Wie wir Vertrauen schaffen")
    card(c, 72, 140, 560, 470, "Sorge")
    bullets(c, 100, 560, ["KI erfindet plausible Aussagen", "Unklare Nachvollziehbarkeit"], size=16)

    card(c, 648, 140, 560, 470, "Design-Gegenmaßnahmen")
    bullets(
        c,
        676,
        560,
        [
            "Suche liefert Originaltext-Ausschnitte",
            "Generierung basiert auf Top-Fundstellen",
            "Quellenpflicht (Dokument/Seite)",
            "Output als Entwurf (Human-in-the-loop)",
        ],
        size=16,
    )
    icon_shield(c, 1040, 250, 120)


def slide_governance(c):
    section_header(c, "Qualität & Nachvollziehbarkeit", "messbar • prüfbar")
    card(c, 72, 140, 1136, 470, "Qualitätssicherung")
    bullets(
        c,
        100,
        560,
        [
            "Nutzer prüft Treffer + Quellen vor Nutzung",
            "Entwurf ≠ Freigabe (Fachprüfung bleibt Pflicht)",
            "Erfolgsmessung im Feldversuch: Zeit, Trefferqualität, Fehlerklassen",
        ],
        size=16,
    )


def slide_local(c):
    section_header(c, "Betrieb & Datenschutz", "lokal / im eigenen Rechenzentrum")
    card(c, 72, 140, 1136, 470, "Kontrollierter Betrieb")
    bullets(
        c,
        100,
        560,
        [
            "Kein externer SaaS-Zwang: Betrieb im eigenen Netzwerk möglich",
            "Modelle lokal oder intern (DB) betreibbar",
            "Mit größeren internen Modellen steigt Qualität – Architektur bleibt gleich",
        ],
        size=16,
    )


def slide_prototype(c):
    section_header(c, "Rapid Prototype – aber produktionsnah", "professioneller Unterbau")
    card(c, 72, 140, 560, 470, "Rapid Prototype (heute)")
    bullets(c, 100, 560, ["kleiner Scope", "schnelle Iteration", "messbarer Nutzen"], size=16)

    card(c, 648, 140, 560, 470, "Produktionsnaher Unterbau")
    bullets(c, 676, 560, ["klare Module", "Docker-fähig", "erweiterbar (Rechte/Logging)"], size=16)


def slide_benefits(c):
    section_header(c, "Zeitersparnis", "Business Case (messbar)")
    card(c, 72, 140, 1136, 470, "Nutzen")
    bullets(
        c,
        100,
        560,
        [
            "Schneller finden: Sekunden statt Minuten",
            "Schneller starten: Entwurf aus Quellen statt Copy/Paste",
            "Messplan: Vorher/Nachher Zeit + Nutzerfeedback",
        ],
        size=16,
    )


def slide_roadmap(c):
    section_header(c, "Roadmap", "Phase 1: 4 Wochen • Testgruppe: 10 Nutzer")
    card(c, 72, 140, 1136, 470, "Phasen + Gates")

    phases = [
        ("Phase 1", "Qualität prüfen\n~400 Dateien\n4 Wochen", "Gate: Freigabe"),
        ("Phase 2", "On-Prem Migration\n(DB Hardware)", "Gate: KPI Review"),
        ("Phase 3", "Feldversuch\n10 Nutzer", "Gate: Go/No-Go"),
        ("Phase 4", "Rollout\nNachbarabteilungen", "")
    ]

    x0 = 120
    y0 = 420
    w = 240
    h = 140
    gap = 40
    for i, (p, d, g) in enumerate(phases):
        x = x0 + i * (w + gap)
        c.setFillColor(white)
        c.roundRect(x, y0, w, h, 14, stroke=0, fill=1)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x + 16, y0 + h - 30, p)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 12)
        for j, line in enumerate(d.split("\n")):
            c.drawString(x + 16, y0 + h - 55 - j * 16, line)
        if g:
            c.setFillColor(ACCENT)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + 16, y0 + 14, g)
        if i < len(phases) - 1:
            arrow(c, x + w, y0 + h / 2, x + w + gap, y0 + h / 2)


def slide_gate(c):
    section_header(c, "Gate 1: Entscheidung", "Freigabe Phase 1")
    card(c, 72, 140, 1136, 470, "Freigabe (risikoarm, messbar)")
    bullets(
        c,
        100,
        560,
        [
            "Umfang: ~2 Berichtsjahre (~400 Dateien)",
            "Ziel: Zeitersparnis + Qualitätskennzahlen + Fehlerklassen",
            "Ergebnis: Messbericht (Zeit/Qualität) + Empfehlung für Migration & Testgruppe",
        ],
        size=16,
    )


def slide_migration(c):
    section_header(c, "Migration: Hostinger → DB Hardware", "Einschätzung")
    card(c, 72, 140, 1136, 470, "Durchführbarkeit: hoch")
    bullets(
        c,
        100,
        560,
        [
            "Container-/Service-Design ist On-Prem-tauglich",
            "Zeitaufwändig typischerweise: Security/Compliance, Netzwerk/TLS, Rechte, Modellbetrieb",
            "Empfehlung: IT/Security früh einbinden, klare Betriebsprozesse",
        ],
        size=16,
    )


def slide_pilot(c):
    section_header(c, "Feldversuch", "kontrolliert • 10 Nutzer")
    card(c, 72, 140, 1136, 470, "Pilot-Setup")
    bullets(
        c,
        100,
        560,
        [
            "10 Nutzer, definierte Use-Cases (Suche, Entwurf, Quellenprüfung)",
            "Feedback-Schleife + KPI-Review",
            "Ergebnis: Entscheidung für Rollout & Prioritäten",
        ],
        size=16,
    )


def slide_expand(c):
    section_header(c, "Funktionsausbau", "nach Pilot priorisiert")
    card(c, 72, 140, 1136, 470, "Beispiele")
    bullets(
        c,
        100,
        560,
        [
            "Konservativer Modus: nur zitieren + zusammenfassen",
            "Quellen klickbar, Export (PDF/Word)",
            "Rollen/Rechte: Suche vs. Generierung",
            "Feedbackbutton: hilfreich/falsch/Quelle fehlt",
        ],
        size=16,
    )


def slide_licenses(c):
    section_header(c, "Software & Lizenzen", "Transparenz für den Einsatz im Unternehmen")
    card(c, 72, 140, 1136, 470, "Stack (Rapid Prototype)")
    bullets(
        c,
        100,
        560,
        [
            "FastAPI/Uvicorn (API) – Open Source",
            "SQLite (DB) – Open Source / Public Domain",
            "Ollama (Model-Server) – Open Source (Betrieb intern)",
            "Modelle (Embeddings/LLM) – Lizenz pro Modell prüfen",
            "PDF-Tools (pdfplumber/pypdf/reportlab) – Open Source",
        ],
        size=16,
    )
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 240, "Hinweis: Vor Rollout werden Modell-Lizenzen und interne Standards formal geprüft.")


def slide_close(c):
    draw_title(c, "Danke", "Nächster Schritt: Freigabe Phase 1 (4 Wochen) → KPI Review")
    c.setFont("Helvetica", 16)
    c.setFillColor(MUTED)
    c.drawString(72, 260, "Ziel: Nutzen (Zeit) + Qualität (Quellen/Fehlerklassen) objektiv messen.")
    c.drawString(72, 235, "Danach: Entscheidung On-Prem Migration + Feldversuch (10 Nutzer).")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))

    # Slide 1
    draw_title(c, "DocGenerator", "Sichere Suche & Berichtsentwürfe aus technischen Reports (Rapid Prototype)")
    icon_magnifier(c, 72, 420, 120)
    icon_shield(c, 210, 420, 120)
    draw_footer(c, right="v1")
    c.showPage()

    slide_problem(c); draw_footer(c, right="2/16"); c.showPage()
    slide_goal(c); draw_footer(c, right="3/16"); c.showPage()
    slide_what(c); draw_footer(c, right="4/16"); c.showPage()
    slide_arch(c); draw_footer(c, right="5/16"); c.showPage()
    slide_hallucinations(c); draw_footer(c, right="6/16"); c.showPage()
    slide_governance(c); draw_footer(c, right="7/16"); c.showPage()
    slide_local(c); draw_footer(c, right="8/16"); c.showPage()
    slide_prototype(c); draw_footer(c, right="9/16"); c.showPage()
    slide_benefits(c); draw_footer(c, right="10/16"); c.showPage()
    slide_roadmap(c); draw_footer(c, right="11/16"); c.showPage()
    slide_gate(c); draw_footer(c, right="12/16"); c.showPage()
    slide_migration(c); draw_footer(c, right="13/16"); c.showPage()
    slide_pilot(c); draw_footer(c, right="14/16"); c.showPage()
    slide_expand(c); draw_footer(c, right="15/16"); c.showPage()
    slide_licenses(c); draw_footer(c, right="16/16"); c.showPage()

    # Close
    # (Optional extra closing slide; keep under 20. Comment out if you want exactly 16.)
    # slide_close(c); draw_footer(c, right="17/17"); c.showPage()

    c.save()
    print(str(OUT))


if __name__ == "__main__":
    main()
