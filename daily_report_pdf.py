from __future__ import annotations

from io import BytesIO
from html import escape as html_escape
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from luna_focus_reset import (
    FOCUS_RESET_ASSET,
    FOCUS_RESET_CUE,
    FOCUS_RESET_DURATION,
    FOCUS_RESET_LABEL,
    FOCUS_RESET_METHOD,
)


BRAND = "Luna Convergence"
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 16 * mm
MARGIN_TOP = 16 * mm
MARGIN_BOTTOM = 15 * mm


def daily_report_filename(narrative) -> str:
    return f"{narrative.reading_date.isoformat()}_{narrative.sign}_Daily.pdf"


def _safe(value: object) -> str:
    text = str(value or "")
    replacements = {
        "\u2014": " - ",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00d7": " x ",
        "\u00a0": " ",
        "\u00b0": "°",
        "\u2032": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"\s+", " ", text).strip()
    return html_escape(text)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "meta": ParagraphStyle(
            "DailyMeta", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, leading=9, textColor=colors.HexColor("#555555"),
            spaceAfter=4,
        ),
        "title": ParagraphStyle(
            "DailyTitle", parent=base["Title"], fontName="Times-Roman",
            fontSize=30, leading=32, textColor=colors.black,
            alignment=TA_LEFT, spaceAfter=8,
        ),
        "theme": ParagraphStyle(
            "DailyTheme", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=14, spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "DailyH1", parent=base["Heading1"], fontName="Times-Roman",
            fontSize=21, leading=24, spaceBefore=8, spaceAfter=7,
        ),
        "h2": ParagraphStyle(
            "DailyH2", parent=base["Heading2"], fontName="Times-Roman",
            fontSize=16, leading=19, spaceBefore=7, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "DailyBody", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.5, leading=14, spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "DailySmall", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.5, leading=10, textColor=colors.HexColor("#555555"),
            spaceAfter=5,
        ),
        "label": ParagraphStyle(
            "DailyLabel", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7, leading=9, textTransform="uppercase", spaceAfter=2,
        ),
        "table": ParagraphStyle(
            "DailyTable", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.5, leading=9,
        ),
    }


def _page_header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(MARGIN_X, 9 * mm, BRAND)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _section(title: str, styles: dict[str, ParagraphStyle]) -> list:
    return [Spacer(1, 2 * mm), HRFlowable(width="100%", thickness=0.6, color=colors.black), Paragraph(_safe(title), styles["h2"])]


def _paragraphs(values, styles: dict[str, ParagraphStyle]) -> list:
    return [Paragraph(_safe(value), styles["body"]) for value in values if value]


def _two_column_box(left_title: str, left_text: str, right_title: str, right_text: str, styles) -> Table:
    data = [[
        [Paragraph(_safe(left_title), styles["label"]), Paragraph(_safe(left_text), styles["body"])],
        [Paragraph(_safe(right_title), styles["label"]), Paragraph(_safe(right_text), styles["body"])],
    ]]
    table = Table(data, colWidths=[(PAGE_WIDTH - 2 * MARGIN_X) / 2] * 2)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _simple_table(rows: list[tuple[str, str]], styles, widths=None) -> Table:
    data = [[Paragraph(_safe(a), styles["label"]), Paragraph(_safe(b), styles["table"])] for a, b in rows]
    table = Table(data, colWidths=widths or [42 * mm, PAGE_WIDTH - 2 * MARGIN_X - 42 * mm], repeatRows=0)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#bbbbbb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _focus_reset_card(styles: dict[str, ParagraphStyle]):
    """Render Luna's signature ritual as a compact, non-instructional strip."""
    image_cell = Spacer(22 * mm, 22 * mm)
    if FOCUS_RESET_ASSET.exists():
        image_cell = RLImage(str(FOCUS_RESET_ASSET), width=22 * mm, height=22 * mm)

    copy = [
        Paragraph(_safe(FOCUS_RESET_LABEL), styles["label"]),
        Paragraph(_safe(FOCUS_RESET_METHOD), styles["h2"]),
        Paragraph(_safe(FOCUS_RESET_CUE), styles["body"]),
    ]
    duration = Paragraph(_safe(FOCUS_RESET_DURATION), styles["small"])
    table = Table(
        [[image_cell, copy, duration]],
        colWidths=[27 * mm, PAGE_WIDTH - 2 * MARGIN_X - 58 * mm, 31 * mm],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.7, colors.black),
        ("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    return KeepTogether([Spacer(1, 3 * mm), table, Spacer(1, 2 * mm)])


def _matrix_flowables(markdown: str, styles) -> list:
    lines = [line.strip() for line in str(markdown or "").splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if not table_lines:
        return [Paragraph(_safe(str(markdown or "Not available")), styles["small"])]
    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", cell or "-") for cell in cells):
            continue
        rows.append([Paragraph(_safe(cell), styles["table"]) for cell in cells])
    if not rows:
        return []
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#999999")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [table]


def build_daily_report_pdf(narrative, solar: dict | None = None, *, include_evidence: bool = True) -> bytes:
    """Build an isolated searchable A4 Daily PDF."""
    output = BytesIO()
    styles = _styles()
    frame = Frame(
        MARGIN_X, MARGIN_BOTTOM,
        PAGE_WIDTH - 2 * MARGIN_X,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="daily",
    )
    doc = BaseDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"{narrative.reading_date.isoformat()}_{narrative.sign}_Daily",
        author=BRAND,
        subject="Sign-based whole-sign daily forecast",
    )
    doc.addPageTemplates([PageTemplate(id="daily", frames=[frame], onPage=_page_header_footer)])

    story = [
        HRFlowable(width="100%", thickness=8, color=colors.black),
        Spacer(1, 6 * mm),
        Paragraph(f"DAILY / {_safe(narrative.sign.upper())}", styles["meta"]),
        Paragraph(_safe(narrative.reading_date.strftime("%A, %B %d, %Y")), styles["meta"]),
        Paragraph(_safe(narrative.hook_headline), styles["title"]),
        Paragraph(f"Today's theme: {_safe(narrative.hook_subline)}", styles["theme"]),
        HRFlowable(width="100%", thickness=0.7, color=colors.black),
        Spacer(1, 4 * mm),
        Paragraph("Luna says", styles["label"]),
        *_paragraphs(narrative.today_story[:2], styles),
        _two_column_box("Do", narrative.action_today, "Don't", narrative.watch_out, styles),
    ]

    story.extend(_section("Why this matters today", styles))
    story.append(_simple_table([(f"Evidence {i}", value) for i, value in enumerate(narrative.why_today_points, 1)], styles))
    story.append(Spacer(1, 3 * mm))
    story.append(_two_column_box("Weather / today", narrative.emotional_weather, "Climate / longer current", narrative.long_term_current, styles))
    story.extend(_section("Hidden opportunity", styles))
    story.append(Paragraph(_safe(narrative.hidden_opportunity), styles["body"]))
    story.append(_focus_reset_card(styles))

    if solar:
        solar_rows = [
            ("Solar phase", solar.get("solar_quarter", "Unavailable")),
            ("Light movement", f"{solar.get('light_direction', 'Unavailable')} / {solar.get('daylight_change', 0):.1f} min/day"),
            ("Next solar gate", f"{solar.get('next_solar_gate', 'Unavailable')} / {solar.get('days_to_next_gate', '?')} days"),
            ("Activated house", f"House {solar.get('activated_house', '?')} / {solar.get('activated_house_name', '')}"),
            ("Location", solar.get("city", "Timezone estimate")),
        ]
        story.extend(_section("Solar position", styles))
        story.append(_simple_table([(str(a), str(b)) for a, b in solar_rows], styles))
        if solar.get("focus_meaning"):
            story.append(Paragraph(_safe(solar.get("focus_meaning")), styles["body"]))

    story.extend(_section("Relationships, work and money", styles))
    story.append(Paragraph("Relationships", styles["label"]))
    story.append(Paragraph(_safe(narrative.relationship_story), styles["body"]))
    story.append(_two_column_box("Work", narrative.work_note, "Money", narrative.money_note, styles))

    question = narrative.reflection_questions[0] if narrative.reflection_questions else "What matters most now?"
    story.extend(_section("One question to sit with", styles))
    story.append(Paragraph(_safe(question), styles["h2"]))

    if include_evidence:
        story.append(PageBreak())
        story.append(Paragraph("Full technical evidence", styles["h1"]))
        evidence = narrative.evidence
        story.append(_simple_table([
            ("Aspect", evidence.aspect_label),
            ("Type", evidence.aspect_type),
            ("Orb", "Not applicable" if evidence.orb is None else f"{evidence.orb:.2f} degrees"),
            ("Timing", evidence.phase),
            ("Active planets", ", ".join(evidence.active_planets)),
            ("Activated houses", ", ".join(str(item) for item in evidence.activated_houses)),
            ("Influence window", evidence.active_window),
            ("Convergence", f"{evidence.convergence_label} / {evidence.convergence_window}"),
            ("Strength", f"{evidence.confidence_label} ({evidence.strength_score}/100)"),
        ], styles))
        story.extend(_section("Calculated daily theme", styles))
        story.append(Paragraph(_safe(narrative.daily_theme), styles["body"]))
        story.extend(_section("Wider convergence context", styles))
        story.append(Paragraph(_safe(narrative.wider_context), styles["body"]))
        story.extend(_section("Dominant aspects", styles))
        for item in narrative.technical_aspects:
            clean = re.sub(r"\*\*", "", str(item))
            story.append(Paragraph(_safe(clean), styles["small"]))
        story.extend(_section("House-based conclusion", styles))
        story.append(Paragraph(_safe(narrative.house_conclusion), styles["body"]))

        story.extend(_section("Planetary positions", styles))
        position_data = [[
            Paragraph("Body", styles["label"]),
            Paragraph("Position", styles["label"]),
            Paragraph("House", styles["label"]),
            Paragraph("Life area", styles["label"]),
        ]]
        for planet, position, house, meaning in narrative.sky_rows:
            position_data.append([
                Paragraph(_safe(planet), styles["table"]),
                Paragraph(_safe(position), styles["table"]),
                Paragraph(_safe(house), styles["table"]),
                Paragraph(_safe(meaning), styles["table"]),
            ])
        table = Table(position_data, colWidths=[24*mm, 34*mm, 18*mm, PAGE_WIDTH-2*MARGIN_X-76*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#999999")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(table)
        story.extend(_section("The 12-house reference matrix", styles))
        story.extend(_matrix_flowables(narrative.house_matrix, styles))

    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=0.7, color=colors.black))
    story.append(Paragraph(
        "Tropical geocentric astrology using whole-sign houses. This is a sign-based forecast adjusted for local time and solar context, not a natal chart or a guarantee of events.",
        styles["small"],
    ))
    doc.build(story)
    return output.getvalue()
