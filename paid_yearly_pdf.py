from __future__ import annotations

"""Paid Yearly PDF.

This is the printable companion to the Paid Monthly-style Year Ahead.
It consumes the SAME Natal Snapshot, YearPacket and one PaidYearlyEditorial
used by the web report. It performs no astrology calculations and no LLM call.
"""

from datetime import date
from io import BytesIO
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from natal_snapshot import natal_wheel_svg
from paid_yearly_editorial import PaidYearlyEditorial
from year_ahead import YearPacket


BRAND = "Luna Convergence"
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 18 * mm
MARGIN_BOTTOM = 17 * mm


def _ascii(value: object) -> str:
    return (
        str(value or "")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2192", "->")
        .replace("\u2022", "-")
        .replace("\u00b0", " deg")
        .replace("\u2032", "'")
    )


def _xml(value: object) -> str:
    return (
        _ascii(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _date_label(value: object) -> str:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text[:10]).strftime("%d %B %Y").lstrip("0")
    except Exception:
        return text


def _packet_dict(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    return dict(packet) if isinstance(packet, dict) else packet.to_dict()


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "Brand", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.2, leading=9, textColor=colors.black,
            spaceAfter=7 * mm, uppercase=True,
        ),
        "hero": ParagraphStyle(
            "Hero", parent=base["Title"], fontName="Times-Bold",
            fontSize=29, leading=31, textColor=colors.black,
            spaceAfter=4 * mm,
        ),
        "deck": ParagraphStyle(
            "Deck", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=15, textColor=colors.HexColor("#303030"),
            spaceAfter=7 * mm,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Times-Bold",
            fontSize=22, leading=25, spaceBefore=6 * mm, spaceAfter=4 * mm,
            textColor=colors.black,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=16.5, leading=19.5, spaceBefore=5 * mm, spaceAfter=2.5 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=14, spaceBefore=3.2 * mm, spaceAfter=1.5 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Times-Roman",
            fontSize=10.5, leading=15.6, textColor=colors.HexColor("#151515"),
            spaceAfter=3.1 * mm,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.5, leading=10.3, textColor=colors.HexColor("#555555"),
            spaceAfter=1.5 * mm,
        ),
        "label": ParagraphStyle(
            "Label", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=6.8, leading=8.5, textColor=colors.HexColor("#555555"),
            spaceAfter=1 * mm,
        ),
        "center": ParagraphStyle(
            "Center", parent=base["BodyText"], fontName="Helvetica",
            fontSize=6.6, leading=8, alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
        ),
        "issue": ParagraphStyle(
            "Issue", parent=base["Heading1"], fontName="Times-Bold",
            fontSize=21, leading=23, spaceBefore=3 * mm, spaceAfter=3 * mm,
            textColor=colors.black,
        ),
    }


def _header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    canvas.setStrokeColor(colors.HexColor("#d3d3ce"))
    canvas.setLineWidth(0.45)
    canvas.line(MARGIN_X, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 13 * mm)
    canvas.setFont("Helvetica-Bold", 6.8)
    canvas.drawString(MARGIN_X, PAGE_HEIGHT - 9.8 * mm, BRAND.upper())
    canvas.setFont("Helvetica", 6.8)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 9.8 * mm, "PAID YOUR YEAR AHEAD")
    canvas.line(MARGIN_X, 11 * mm, PAGE_WIDTH - MARGIN_X, 11 * mm)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(MARGIN_X, 7 * mm, "Astrology is interpretive and is not professional advice.")
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 7 * mm, f"Page {page}")
    canvas.restoreState()


def _natal_rows(snapshot: Any) -> list[tuple[str, str]]:
    by_planet = {
        str(getattr(item, "planet", "")): item
        for item in list(getattr(snapshot, "positions", ()) or ())
    }
    sun = by_planet.get("Sun")
    moon = by_planet.get("Moon")
    asc = getattr(snapshot, "ascendant", None)
    mc = getattr(snapshot, "midheaven", None)
    return [
        ("Sun", str(getattr(sun, "sign", "") or "Not calculated")),
        ("Moon", str(getattr(moon, "sign", "") or "Not calculated")),
        ("Rising", str(getattr(asc, "sign", "") or "Not calculated")),
        ("Dominant element", str(getattr(snapshot, "dominant_element", "") or "Not calculated")),
        ("Dominant mode", str(getattr(snapshot, "dominant_modality", "") or "Not calculated")),
        ("Midheaven", str(getattr(mc, "sign", "") or "Not calculated")),
    ]


def _natal_signature(snapshot: Any, styles) -> list:
    rows = []
    for label, value in _natal_rows(snapshot):
        rows.append([
            Paragraph(_xml(label), styles["label"]),
            Paragraph(_xml(value), styles["body"]),
        ])
    table = Table(
        rows,
        colWidths=[38 * mm, PAGE_WIDTH - 2 * MARGIN_X - 38 * mm],
    )
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.45, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.22, colors.HexColor("#d6d6d0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))
    return [Paragraph("Your natal signature", styles["h2"]), table]


def _read_pattern(snapshot: Any, styles) -> list:
    signatures = list(getattr(snapshot, "signatures", ()) or ())
    if not signatures:
        return []
    sig = signatures[0]
    story = [
        Paragraph("Read the pattern", styles["h2"]),
        Paragraph(_xml(getattr(sig, "title", "") or "Your recurring natal pattern"), styles["h3"]),
    ]
    text = str(getattr(sig, "text", "") or "").strip()
    if text:
        story.append(Paragraph(_xml(text), styles["body"]))
    strength = str(getattr(sig, "strength", "") or "").strip()
    if strength:
        story.append(Paragraph(_xml(strength), styles["body"]))
    evidence = str(getattr(sig, "evidence", "") or "").strip()
    if evidence:
        story.append(Paragraph(f"Calculated evidence: {_xml(evidence)}", styles["small"]))
    return story


def _natal_chart(snapshot: Any, styles) -> list:
    """Embed the same natal wheel used on the web when svglib is available."""
    try:
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(BytesIO(natal_wheel_svg(snapshot, size=760).encode("utf-8")))
        if drawing is None:
            return []
        max_width = PAGE_WIDTH - 2 * MARGIN_X
        max_height = 92 * mm
        scale = min(max_width / float(drawing.width), max_height / float(drawing.height))
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)
        return [Spacer(1, 4 * mm), drawing, Spacer(1, 2 * mm)]
    except Exception:
        return []


def _strengths(snapshot: Any, styles) -> list:
    signatures = list(getattr(snapshot, "signatures", ()) or ())
    if not signatures:
        return []
    story = [
        Paragraph("Your strengths", styles["h2"]),
        Paragraph(
            "The strongest capacities in your natal pattern when you use them deliberately.",
            styles["small"],
        ),
    ]
    for sig in signatures[:6]:
        story.append(Paragraph(_xml(getattr(sig, "title", "") or "Natal strength"), styles["h3"]))
        text = str(getattr(sig, "text", "") or "").strip()
        if text:
            story.append(Paragraph(_xml(text), styles["body"]))
        remember = " ".join(
            part for part in [
                str(getattr(sig, "strength", "") or "").strip(),
                (
                    "Watch for " + str(getattr(sig, "watch", "") or "").strip()
                    if str(getattr(sig, "watch", "") or "").strip()
                    else ""
                ),
            ]
            if part
        )
        if remember:
            story.append(Paragraph(f"<b>Remember:</b> {_xml(remember)}", styles["small"]))
    return story


def _year_map(packet: dict[str, Any], styles) -> list:
    rows = [row for row in list(packet.get("year_strip") or []) if isinstance(row, dict)]
    if not rows:
        return []
    cells = []
    for row in rows:
        month = str(row.get("month") or "")
        phase = str(row.get("phase") or "QUIET")
        cells.append(Paragraph(f"<b>{_xml(month)}</b><br/>{_xml(phase)}", styles["center"]))
    width = (PAGE_WIDTH - 2 * MARGIN_X) / len(cells)
    table = Table([cells], colWidths=[width] * len(cells))
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#bcbcbc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0.7 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0.7 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    return [
        Paragraph("Your year map", styles["h2"]),
        Paragraph(
            "Quick reference only. The interpretation is already in Read the year.",
            styles["small"],
        ),
        table,
    ]


def _position(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    sign = str(value.get("sign") or "")
    degree = value.get("degree")
    longitude = value.get("longitude")
    bits = []
    if degree is not None and sign:
        bits.append(f"{float(degree):.2f} deg {sign}")
    elif sign:
        bits.append(sign)
    if longitude is not None:
        bits.append(f"{float(longitude):.2f} deg ecliptic")
    return " / ".join(bits)


def _pass_rows(story: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in list(story.get("passes") or []) if isinstance(row, dict)]


def _strongest(story: dict[str, Any], fallback: object) -> str:
    passes = _pass_rows(story)
    if not passes:
        return _date_label(fallback)
    peak = min(
        passes,
        key=lambda row: (
            float(row.get("orb", 99.0) or 99.0),
            str(row.get("date") or ""),
            str(row.get("time") or ""),
        ),
    )
    label = _date_label(peak.get("date"))
    if peak.get("time"):
        label += f" {peak.get('time')}"
    return label


def _issue_flowables(
    game: dict[str, Any],
    editorial: PaidYearlyEditorial | None,
    styles,
) -> list:
    number = int(game.get("number") or 0)
    primary = dict(game.get("primary_transit") or {})
    supporting = [
        row for row in list(game.get("supporting_transits") or [])
        if isinstance(row, dict)
    ]
    issue = editorial.issue_for(number) if editorial is not None else None

    story = [
        PageBreak(),
        Paragraph(
            f"MAJOR ISSUE {number:02d} / {_xml(game.get('human_life_area') or '')}",
            styles["label"],
        ),
        Paragraph(_xml(game.get("title") or "A major issue of the year"), styles["issue"]),
    ]

    if issue is not None and issue.paragraphs:
        for paragraph in issue.paragraphs:
            story.append(Paragraph(_xml(paragraph), styles["body"]))
    elif primary.get("summary"):
        story.append(Paragraph(_xml(primary.get("summary")), styles["body"]))

    story.append(Paragraph("Timing", styles["h3"]))
    timing = Table([[
        Paragraph(f"<b>Begins</b><br/>{_xml(_date_label(game.get('start_date')))}", styles["small"]),
        Paragraph(f"<b>Strongest</b><br/>{_xml(_strongest(primary, game.get('start_date')))}", styles["small"]),
        Paragraph(f"<b>Eases</b><br/>{_xml(_date_label(game.get('end_date')))}", styles["small"]),
    ]], colWidths=[(PAGE_WIDTH - 2 * MARGIN_X) / 3] * 3)
    timing.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.45, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.22, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.7 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.7 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))
    story.append(timing)

    passes = _pass_rows(primary)
    if passes:
        story.append(Paragraph("How the issue develops", styles["h3"]))
        for row in passes:
            when = _date_label(row.get("date"))
            if row.get("time"):
                when += f" {row.get('time')}"
            motion = "retrograde" if bool(row.get("retrograde")) else "direct"
            story.append(
                Paragraph(
                    _xml(
                        f"Pass {int(row.get('pass_number') or 1)} - "
                        f"{row.get('pass_label') or ''}: {when} / {motion}"
                    ),
                    styles["small"],
                )
            )

    triggers = [
        row for row in list(primary.get("triggers") or [])
        if isinstance(row, dict)
    ]
    if triggers:
        story.append(Paragraph("Trigger dates", styles["h3"]))
        for row in triggers:
            when = _date_label(row.get("date"))
            label = row.get("activation_label") or row.get("technical_label") or "Supporting trigger"
            story.append(Paragraph(_xml(f"{when}: {label}"), styles["small"]))

    if supporting:
        story.append(Paragraph("Also working underneath", styles["h3"]))
        for row in supporting:
            story.append(
                Paragraph(
                    f"<b>{_xml(row.get('technical_label') or '')}</b><br/>{_xml(row.get('summary') or '')}",
                    styles["small"],
                )
            )

    return story


def _key_dates(packet: dict[str, Any], styles) -> list:
    rows: list[tuple[str, str]] = []
    for game in [g for g in list(packet.get("games") or []) if isinstance(g, dict)]:
        story = dict(game.get("primary_transit") or {})
        technical = str(story.get("technical_label") or game.get("title") or "")
        for hit in _pass_rows(story):
            raw = str(hit.get("date") or "")[:10]
            if raw:
                rows.append((
                    raw,
                    f"{technical} / Pass {int(hit.get('pass_number') or 1)} / {hit.get('pass_label') or ''}",
                ))
        for trigger in [t for t in list(story.get("triggers") or []) if isinstance(t, dict)]:
            raw = str(trigger.get("date") or "")[:10]
            if raw:
                rows.append((
                    raw,
                    str(trigger.get("activation_label") or trigger.get("technical_label") or "Supporting trigger"),
                ))

    if not rows:
        return []

    story = [
        PageBreak(),
        Paragraph("Key dates", styles["h1"]),
        Paragraph(
            "Quick reference only. The interpretation is already woven through Read the year and the major issues.",
            styles["small"],
        ),
    ]
    seen = set()
    for raw, label in sorted(rows, key=lambda row: (row[0], row[1]))[:20]:
        key = (raw, label)
        if key in seen:
            continue
        seen.add(key)
        story.append(Paragraph(_xml(_date_label(raw)), styles["label"]))
        story.append(Paragraph(_xml(label), styles["body"]))
        story.append(HRFlowable(width="100%", thickness=0.25, color=colors.HexColor("#d7d7d2"), spaceAfter=2 * mm))
    return story


def _evidence(packet: dict[str, Any], styles) -> list:
    story = [
        Paragraph("Why Luna sees this - chart evidence", styles["h1"]),
        Paragraph(
            "The astrology is calculated, not guessed. Exact transits, passes, timing and houses come from the deterministic calculation layer.",
            styles["small"],
        ),
    ]
    for game in [g for g in list(packet.get("games") or []) if isinstance(g, dict)]:
        story.append(Paragraph(
            f"Major issue {int(game.get('number') or 0):02d} - {_xml(game.get('title') or '')}",
            styles["h3"],
        ))
        stories = [dict(game.get("primary_transit") or {})] + [
            row for row in list(game.get("supporting_transits") or [])
            if isinstance(row, dict)
        ]
        for transit in stories:
            story.append(Paragraph(_xml(transit.get("technical_label") or ""), styles["small"]))
            natal = _position(transit.get("natal_position"))
            if natal:
                story.append(Paragraph(_xml(f"Natal {transit.get('natal_target')}: {natal}"), styles["small"]))
            if transit.get("natal_house") is not None:
                story.append(Paragraph(_xml(f"House {transit.get('natal_house')}"), styles["small"]))
            story.append(Paragraph(
                _xml(f"Active window: {_date_label(transit.get('start'))} - {_date_label(transit.get('end'))}"),
                styles["small"],
            ))
            for hit in _pass_rows(transit):
                when = _date_label(hit.get("date"))
                if hit.get("time"):
                    when += f" {hit.get('time')}"
                pos = _position(hit.get("transit_position"))
                detail = (
                    f"Pass {int(hit.get('pass_number') or 1)} / {hit.get('pass_label') or ''} / "
                    f"{when} / {'retrograde' if bool(hit.get('retrograde')) else 'direct'} / "
                    f"{float(hit.get('orb') or 0.0):.2f} deg orb"
                )
                if pos:
                    detail += f" / {pos}"
                story.append(Paragraph(_xml(detail), styles["small"]))
    return story


def build_paid_yearly_pdf(
    *,
    snapshot: Any,
    packet: YearPacket | dict[str, Any],
    editorial: PaidYearlyEditorial | None,
    sign: str,
    label: str,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> bytes:
    value = _packet_dict(packet)
    styles = _styles()
    output = BytesIO()

    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM,
        PAGE_WIDTH - 2 * MARGIN_X,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="normal",
    )
    doc = BaseDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"{BRAND} - {sign} Paid Year Ahead",
        author=BRAND,
    )
    doc.addPageTemplates([
        PageTemplate(id="paid-yearly", frames=[frame], onPage=_header_footer)
    ])

    games = [g for g in list(value.get("games") or []) if isinstance(g, dict)]
    headline = (
        editorial.headline
        if editorial is not None and editorial.headline
        else str((games[0] if games else {}).get("title") or "Your Year Ahead")
    )
    deck = (
        editorial.deck
        if editorial is not None and editorial.deck
        else "Your natal pattern meets the strongest personal transits of the next rolling year."
    )

    story = [
        Spacer(1, 10 * mm),
        Paragraph(BRAND.upper(), styles["brand"]),
        Paragraph(_xml(headline), styles["hero"]),
        Paragraph(_xml(f"{label} - {deck}"), styles["deck"]),
        HRFlowable(width="100%", thickness=0.6, color=colors.black, spaceAfter=5 * mm),
        Paragraph(f"<b>Main priority:</b> {_xml(main_focus or 'General overview')}", styles["small"]),
    ]
    if str(personal_question or "").strip():
        story.append(Paragraph(f"<b>Your question:</b> {_xml(personal_question)}", styles["small"]))
    if order_reference:
        story.append(Paragraph(f"Order reference: {_xml(order_reference)}", styles["small"]))

    story += _natal_signature(snapshot, styles)
    story += _read_pattern(snapshot, styles)
    story += _natal_chart(snapshot, styles)
    story += _strengths(snapshot, styles)

    story.append(PageBreak())
    story.append(Paragraph("Read the year", styles["h1"]))
    if editorial is not None and editorial.read_year:
        for paragraph in editorial.read_year:
            story.append(Paragraph(_xml(paragraph), styles["body"]))
    else:
        story.append(Paragraph(
            "Luna's long-form reading was unavailable on this run. The calculated annual timing and evidence remain below.",
            styles["small"],
        ))

    story += _year_map(value, styles)

    story.append(PageBreak())
    story.append(Paragraph("The major issues of your year", styles["h1"]))
    story.append(Paragraph(
        "These are the strongest selected personal transit arcs. Each chapter gives the human situation first and the exact timing underneath.",
        styles["small"],
    ))
    for game in games:
        story += _issue_flowables(game, editorial, styles)

    if editorial is not None and editorial.closing:
        story.append(PageBreak())
        story.append(Paragraph("What the year leaves you with", styles["h1"]))
        for paragraph in editorial.closing:
            story.append(Paragraph(_xml(paragraph), styles["body"]))

    story += _key_dates(value, styles)
    story += _evidence(value, styles)

    doc.build(story)
    return output.getvalue()


def paid_yearly_filename(sign: str, start_date: object, end_date: object) -> str:
    clean_sign = re.sub(r"[^A-Za-z0-9]+", "", str(sign or "Report")) or "Report"
    start = str(start_date or "")[:10]
    end = str(end_date or "")[:10]
    return f"{start}_to_{end}_{clean_sign}_Paid_Year_Ahead.pdf"
