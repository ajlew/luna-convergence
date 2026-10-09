from __future__ import annotations

"""Printable PDF for the rebuilt paid Luna Year Ahead.

The PDF consumes the same finished YearPacket and the same optional single
Luna voice response used by the paid web report. It does not calculate or
select astrology.
"""

from datetime import date
from io import BytesIO
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from year_ahead import YearPacket


BRAND = "Luna Convergence"
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 18 * mm


def _ascii(value: object) -> str:
    text = str(value or "")
    return (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2192", "->")
        .replace("\u2022", "-")
        .replace("\u00b0", " deg")
        .replace("\u2032", "'")
    )


def _xml(value: object) -> str:
    text = _ascii(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _date_label(value: object) -> str:
    if isinstance(value, date):
        return value.strftime("%d %b %Y").lstrip("0")
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text[:10]).strftime("%d %b %Y").lstrip("0")
    except Exception:
        return text


def _packet_dict(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    if isinstance(packet, dict):
        return dict(packet)
    return packet.to_dict()


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_brand": ParagraphStyle(
            "YearCoverBrand", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=8, leading=10, textColor=colors.white, spaceAfter=10 * mm,
        ),
        "cover_title": ParagraphStyle(
            "YearCoverTitle", parent=base["Title"], fontName="Times-Bold",
            fontSize=28, leading=29, textColor=colors.white, spaceAfter=5 * mm,
        ),
        "cover_meta": ParagraphStyle(
            "YearCoverMeta", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=colors.HexColor("#dddddd"),
        ),
        "h1": ParagraphStyle(
            "YearH1", parent=base["Heading1"], fontName="Times-Bold",
            fontSize=22, leading=25, spaceBefore=4 * mm, spaceAfter=4 * mm,
            textColor=colors.black,
        ),
        "h2": ParagraphStyle(
            "YearH2", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=16, leading=19, spaceBefore=5 * mm, spaceAfter=2.5 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "YearH3", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=14, spaceBefore=3 * mm, spaceAfter=1.5 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "YearBody", parent=base["BodyText"], fontName="Times-Roman",
            fontSize=10.2, leading=15, textColor=colors.HexColor("#151515"),
            spaceAfter=2.7 * mm,
        ),
        "small": ParagraphStyle(
            "YearSmall", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.3, leading=10, textColor=colors.HexColor("#555555"),
        ),
        "label": ParagraphStyle(
            "YearLabel", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.2, leading=9, textColor=colors.HexColor("#555555"),
            spaceAfter=1 * mm,
        ),
        "game_title": ParagraphStyle(
            "YearGameTitle", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=18, leading=20, spaceBefore=4 * mm, spaceAfter=2 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "center_small": ParagraphStyle(
            "YearCenterSmall", parent=base["BodyText"], fontName="Helvetica",
            fontSize=6.4, leading=8, alignment=TA_CENTER, textColor=colors.HexColor("#333333"),
        ),
    }


def _page_header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    canvas.setStrokeColor(colors.HexColor("#d7d7d2"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, PAGE_HEIGHT - 14 * mm, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 14 * mm)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawString(MARGIN_X, PAGE_HEIGHT - 10.5 * mm, BRAND.upper())
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 10.5 * mm, "YOUR YEAR AHEAD")
    canvas.line(MARGIN_X, 12 * mm, PAGE_WIDTH - MARGIN_X, 12 * mm)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(MARGIN_X, 7.5 * mm, "Astrology is a symbolic interpretive framework and not professional advice.")
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 7.5 * mm, f"Page {page}")
    canvas.restoreState()


def _cover(
    packet: dict[str, Any],
    *,
    sign: str,
    label: str,
    main_focus: str,
    personal_question: str,
    order_reference: str,
    styles: dict[str, ParagraphStyle],
):
    period = packet.get("period") or {}
    start = _date_label(period.get("start"))
    end = _date_label(period.get("end"))
    meta = [
        "<b>Paid - Personal Transits &amp; Timing</b>",
        f"{_xml(sign)} / {_xml(label or (start + ' - ' + end))}",
        f"Main priority: {_xml(main_focus or 'General overview')}",
    ]
    if order_reference:
        meta.append(f"Order reference: {_xml(order_reference)}")

    cover = Table(
        [[[
            Paragraph(BRAND.upper(), styles["cover_brand"]),
            Paragraph("YOUR YEAR AHEAD", styles["cover_title"]),
            Paragraph("<br/>".join(meta), styles["cover_meta"]),
        ]]],
        colWidths=[PAGE_WIDTH - 2 * MARGIN_X],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.black),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 13 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 15 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 15 * mm),
    ]))

    rows = [
        [Paragraph("PERSONALISED FOCUS", styles["label"])],
        [Paragraph(_xml(main_focus or "General overview"), styles["body"])],
    ]
    if personal_question.strip():
        rows.extend([
            [Paragraph("YOUR QUESTION", styles["label"])],
            [Paragraph(_xml(personal_question.strip()), styles["body"])],
        ])
    focus = Table(rows, colWidths=[PAGE_WIDTH - 2 * MARGIN_X])
    focus.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f3ef")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d6d6d0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return [cover, Spacer(1, 9 * mm), focus, PageBreak()]


def _natal_signature(packet: dict[str, Any], styles: dict[str, ParagraphStyle]):
    fp = packet.get("natal_fingerprint") or {}
    sun = fp.get("sun") or {}
    moon = fp.get("moon") or {}
    asc = fp.get("ascendant") or {}
    rows = [
        ["Sun", f"{sun.get('degree', '')} {sun.get('sign', '')}".strip()],
        ["Moon", f"{moon.get('degree', '')} {moon.get('sign', '')}".strip()],
        ["Rising", f"{asc.get('degree', '')} {asc.get('sign', '')}".strip() if asc else "Not calculated"],
        ["Element", fp.get("dominant_element") or "-"],
        ["Mode", fp.get("dominant_modality") or "-"],
    ]
    data = [[Paragraph(_xml(a), styles["label"]), Paragraph(_xml(b), styles["body"])] for a, b in rows]
    table = Table(data, colWidths=[35 * mm, PAGE_WIDTH - 2 * MARGIN_X - 35 * mm])
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d6d6d0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))
    story = [Paragraph("Your natal signature", styles["h2"]), table]
    signatures = list(fp.get("strongest_signatures") or [])
    if signatures:
        story.append(Spacer(1, 3 * mm))
        for item in signatures[:5]:
            story.append(Paragraph(_xml(item.get("title") or "Natal signature"), styles["h3"]))
            evidence = item.get("evidence") or ""
            strength = item.get("strength") or ""
            if strength:
                story.append(Paragraph(_xml(strength), styles["body"]))
            if evidence:
                story.append(Paragraph(f"Calculated evidence: {_xml(evidence)}", styles["small"]))
    return story


def _year_at_glance(packet: dict[str, Any], styles: dict[str, ParagraphStyle]):
    stats = packet.get("year_statistics") or {}
    values = [
        ("Major games", stats.get("major_games", 0)),
        ("Turning points", stats.get("turning_points", 0)),
        ("Rule changes", stats.get("rule_changes", 0)),
    ]
    cells = [[
        Paragraph(f"<b>{_xml(label)}</b><br/>{_xml(value)}", styles["body"])
        for label, value in values
    ]]
    table = Table(cells, colWidths=[(PAGE_WIDTH - 2 * MARGIN_X) / 3] * 3)
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return [Paragraph("The year at a glance", styles["h2"]), table]


def _year_strip(packet: dict[str, Any], styles: dict[str, ParagraphStyle]):
    rows = [item for item in list(packet.get("year_strip") or []) if isinstance(item, dict)]
    if not rows:
        return []
    cells = []
    phase_labels = {
        "PRESSURE": "PRESS",
        "OPPORTUNITY": "OPEN",
        "RETURN": "RETURN",
        "ENDING": "ENDING",
        "STRUCTURAL": "STRUCT",
        "MIXED": "MIXED",
        "QUIET": "QUIET",
    }
    for item in rows:
        month = str(item.get("month") or "")
        phase = str(item.get("phase") or "QUIET").upper()
        phase = phase_labels.get(phase, phase[:7])
        intensity = float(item.get("intensity") or 0.0)
        cells.append(Paragraph(
            f"<b>{_xml(month)}</b><br/>{_xml(phase)}<br/>{intensity:.2f}",
            styles["center_small"],
        ))
    width = (PAGE_WIDTH - 2 * MARGIN_X) / max(1, len(cells))
    table = Table([cells], colWidths=[width] * len(cells))
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.45, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bbbbbb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 0.8 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0.8 * mm),
    ]))
    return [Paragraph("Year strip", styles["h2"]), table]


def _voice_story(prose: str, styles: dict[str, ParagraphStyle]):
    clean = str(prose or "").strip()
    if not clean:
        return [
            Paragraph("Read the year", styles["h2"]),
            Paragraph(
                "Luna's narrative voice was unavailable when this PDF was generated. The calculated Year Ahead below remains complete.",
                styles["small"],
            ),
        ]
    story = [Paragraph("Read the year", styles["h2"])]
    for part in re.split(r"\n\s*\n+", clean):
        paragraph = " ".join(part.split())
        if paragraph:
            story.append(Paragraph(_xml(paragraph), styles["body"]))
    return story


def _position(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    sign = str(value.get("sign") or "")
    degree = value.get("degree")
    longitude = value.get("longitude")
    parts = []
    if degree is not None and sign:
        parts.append(f"{float(degree):.2f} deg {sign}")
    elif sign:
        parts.append(sign)
    if longitude is not None:
        parts.append(f"{float(longitude):.2f} deg ecliptic")
    return " / ".join(parts)


def _pass_lines(primary: dict[str, Any]) -> list[str]:
    lines = []
    for item in list(primary.get("passes") or []):
        if not isinstance(item, dict):
            continue
        number = int(item.get("pass_number") or 1)
        label = str(item.get("pass_label") or f"Pass {number}")
        motion = "retrograde" if bool(item.get("retrograde")) else "direct"
        when = _date_label(item.get("date"))
        if item.get("time"):
            when += f" {item.get('time')}"
        pos = _position(item.get("transit_position"))
        pos_text = f" / {pos}" if pos else ""
        lines.append(
            f"Pass {number} - {label}: {when} / {motion}{pos_text} / {float(item.get('orb') or 0.0):.2f} deg orb"
        )
    return lines


def _game_flowables(game: dict[str, Any], styles: dict[str, ParagraphStyle]):
    primary = dict(game.get("primary_transit") or {})
    passes = [item for item in list(primary.get("passes") or []) if isinstance(item, dict)]
    peak = min(
        passes,
        key=lambda item: (float(item.get("orb", 99.0) or 99.0), str(item.get("date") or "")),
    ) if passes else None
    strongest = _date_label((peak or {}).get("date")) if peak else _date_label(game.get("start_date"))
    if peak and peak.get("time"):
        strongest += f" {peak.get('time')}"

    story = [
        HRFlowable(width="100%", thickness=0.6, color=colors.black, spaceBefore=5 * mm, spaceAfter=3 * mm),
        Paragraph(
            f"GAME {int(game.get('number') or 0):02d} / {_xml(str(game.get('polarity') or '').upper())} / {_xml(game.get('human_life_area') or '')}",
            styles["label"],
        ),
        Paragraph(_xml(game.get("title") or "Year Ahead Game"), styles["game_title"]),
        Paragraph(_xml(game.get("strategic_frame") or ""), styles["body"]),
    ]

    summary = primary.get("summary") or ""
    if summary:
        story.append(Paragraph(f"<b>What is changing:</b> {_xml(summary)}", styles["body"]))
    if game.get("advantage"):
        story.append(Paragraph(f"<b>Your strategic edge:</b> {_xml(game.get('advantage'))}", styles["body"]))

    timing = Table([[
        Paragraph(f"<b>Starts</b><br/>{_xml(_date_label(game.get('start_date')))}", styles["small"]),
        Paragraph(f"<b>Strongest</b><br/>{_xml(strongest)}", styles["small"]),
        Paragraph(f"<b>Eases</b><br/>{_xml(_date_label(game.get('end_date')))}", styles["small"]),
    ]], colWidths=[(PAGE_WIDTH - 2 * MARGIN_X) / 3] * 3)
    timing.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.45, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))
    story.extend([timing, Spacer(1, 2.5 * mm)])

    if game.get("move"):
        story.append(Paragraph(f"<b>YOUR MOVE</b><br/>{_xml(game.get('move'))}", styles["body"]))

    if passes:
        story.append(Paragraph("Passes", styles["h3"]))
        for line in _pass_lines(primary):
            story.append(Paragraph(_xml(line), styles["small"]))

    triggers = [item for item in list(primary.get("triggers") or []) if isinstance(item, dict)]
    if triggers:
        story.append(Paragraph("Supporting triggers", styles["h3"]))
        for item in triggers:
            label = item.get("activation_label") or item.get("technical_label") or "Trigger"
            when = _date_label(item.get("date"))
            if item.get("time"):
                when += f" {item.get('time')}"
            pass_no = item.get("activates_pass_number")
            pass_text = f" / activates Pass {pass_no}" if pass_no else ""
            story.append(Paragraph(
                _xml(f"{label} / {when}{pass_text} / {float(item.get('orb') or 0.0):.2f} deg orb"),
                styles["small"],
            ))

    story.append(Paragraph("Why Luna sees this", styles["h3"]))
    natal_position = _position(primary.get("natal_position"))
    evidence = str(primary.get("technical_label") or "")
    if primary.get("natal_house") is not None:
        evidence += f" / natal house {primary.get('natal_house')}"
    story.append(Paragraph(_xml(evidence), styles["small"]))
    if natal_position:
        story.append(Paragraph(_xml(f"Natal {primary.get('natal_target')}: {natal_position}"), styles["small"]))
    story.append(Paragraph(
        _xml(f"Active window: {_date_label(primary.get('start'))} - {_date_label(primary.get('end'))}"),
        styles["small"],
    ))

    supporting = [item for item in list(game.get("supporting_transits") or []) if isinstance(item, dict)]
    if supporting:
        story.append(Paragraph("Supporting transits", styles["h3"]))
        for item in supporting:
            line = str(item.get("technical_label") or "")
            np = _position(item.get("natal_position"))
            if np:
                line += f" / natal {np}"
            story.append(Paragraph(_xml(line), styles["small"]))
            for pass_line in _pass_lines(item):
                story.append(Paragraph(_xml(pass_line), styles["small"]))

    if game.get("risk"):
        story.append(Paragraph(_xml(f"Risk: {game.get('risk')}"), styles["small"]))
    if game.get("dont"):
        story.append(Paragraph(_xml(f"Do not: {game.get('dont')}"), styles["small"]))
    return story


def build_year_ahead_pdf(
    packet: YearPacket | dict[str, Any],
    *,
    voice_prose: str = "",
    sign: str = "",
    label: str = "Rolling 365 days",
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> bytes:
    """Build the printable paid Year Ahead from the finished deterministic packet."""
    value = _packet_dict(packet)
    styles = _styles()
    output = BytesIO()
    frame = Frame(
        MARGIN_X, MARGIN_BOTTOM,
        PAGE_WIDTH - 2 * MARGIN_X,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="normal",
    )
    template = PageTemplate(id="year-ahead", frames=[frame], onPage=_page_header_footer)
    doc = BaseDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"{BRAND} - {sign} Your Year Ahead",
        author=BRAND,
    )
    doc.addPageTemplates([template])

    story = []
    story.extend(_cover(
        value,
        sign=sign,
        label=label,
        main_focus=main_focus,
        personal_question=personal_question,
        order_reference=order_reference,
        styles=styles,
    ))
    story.extend(_natal_signature(value, styles))
    story.extend(_year_at_glance(value, styles))
    story.extend(_year_strip(value, styles))
    story.extend(_voice_story(voice_prose, styles))

    games = [item for item in list(value.get("games") or []) if isinstance(item, dict)]
    if games:
        story.append(Paragraph("Your major games", styles["h2"]))
        story.append(Paragraph(
            "These are the strongest personal transit arcs in chronological order. Repeated direct and retrograde contacts stay together as one developing story.",
            styles["small"],
        ))
        for game in games:
            story.extend(_game_flowables(game, styles))
    else:
        story.append(Paragraph("Your major games", styles["h2"]))
        story.append(Paragraph(
            "No major exact transit arcs passed the current annual threshold in this rolling window.",
            styles["body"],
        ))

    story.extend([
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=0.7, color=colors.black),
        Spacer(1, 3 * mm),
        Paragraph(
            "Calculated first, selected second, organised third, then narrated by Luna. Exact dates, pass labels, positions and houses shown in this report come from the deterministic astrology layer; houses appear only when birth-time/location precision supports them.",
            styles["small"],
        ),
    ])

    doc.build(story)
    return output.getvalue()


def year_ahead_filename(sign: str, start_date: object, end_date: object) -> str:
    clean_sign = re.sub(r"[^A-Za-z0-9]+", "", str(sign or "Report")) or "Report"
    start = str(start_date or "")[:10]
    end = str(end_date or "")[:10]
    return f"{start}_to_{end}_{clean_sign}_Year_Ahead.pdf"
