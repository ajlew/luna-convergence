from __future__ import annotations

from datetime import date
from io import BytesIO
import re
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


BRAND = "Luna Convergence"
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 20 * mm
MARGIN_TOP = 22 * mm
MARGIN_BOTTOM = 18 * mm

FOCUS_GUIDANCE = {
    "General overview": "The report keeps a balanced view across relationships, work, money, home and personal direction.",
    "General year ahead": "The report keeps a balanced view across the full calendar year and highlights the most important turning points.",
    "Love and relationships": "Relationship, attraction, boundaries, communication and mutual effort receive additional attention.",
    "Career and work": "Career direction, workload, visibility, professional relationships and practical timing receive additional attention.",
    "Career or business": "Career, business decisions, clients, reputation, operations and practical timing receive additional attention.",
    "Money and security": "Income, pricing, shared money, obligations, risk and long-term security receive additional attention.",
    "Home and family": "Home, family, private life, property and emotional foundations receive additional attention.",
    "Home or relocation": "Home, family, property, relocation and emotional foundations receive additional attention.",
    "Personal growth": "Identity, confidence, habits, learning and personal direction receive additional attention.",
    "Personal reinvention": "Identity, visibility, changing priorities and the practical work of reinvention receive additional attention.",
}


def _ascii_safe(value: str) -> str:
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
    }
    text = value
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _inline_markup(value: str) -> str:
    text = _ascii_safe(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover_brand": ParagraphStyle(
            "CoverBrand",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.white,
            tracking=2,
            alignment=TA_LEFT,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=30,
            leading=34,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=6 * mm,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=14,
            textColor=colors.white,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=21,
            leading=25,
            textColor=colors.black,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.black,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.black,
            spaceBefore=4 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10.2,
            leading=15,
            textColor=colors.HexColor("#161616"),
            spaceAfter=2.5 * mm,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#555555"),
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#555555"),
            textTransform="uppercase",
        ),
        "focus": ParagraphStyle(
            "Focus",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=11,
            leading=16,
            textColor=colors.black,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            spaceAfter=2 * mm,
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
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 10.5 * mm, "STRATEGIC ASTROLOGY / EXPLAINABLE EVIDENCE")
    canvas.line(MARGIN_X, 12 * mm, PAGE_WIDTH - MARGIN_X, 12 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(MARGIN_X, 7.5 * mm, "Astrology is a symbolic interpretive framework and not professional advice.")
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 7.5 * mm, f"Page {page}")
    canvas.restoreState()


def _cover_block(result: dict, main_focus: str, personal_question: str, order_reference: str, styles: dict):
    sign = _ascii_safe(str(result.get("sign", "")))
    label = _ascii_safe(str(result.get("label", result.get("period", "Report"))))
    report_type = "Monthly Strategic Report" if result.get("period") == "monthly" else "Year-Ahead Strategic Report"
    meta_lines = [
        f"<b>{_inline_markup(report_type)}</b>",
        f"{_inline_markup(sign)} / {_inline_markup(label)}",
        f"Main focus: {_inline_markup(main_focus)}",
    ]
    if order_reference:
        meta_lines.append(f"Order reference: {_inline_markup(order_reference)}")

    cover = Table(
        [[
            [
                Paragraph(BRAND.upper(), styles["cover_brand"]),
                Spacer(1, 15 * mm),
                Paragraph(f"{_inline_markup(sign)}<br/>{_inline_markup(label)}", styles["cover_title"]),
                Paragraph("<br/>".join(meta_lines), styles["cover_meta"]),
            ]
        ]],
        colWidths=[PAGE_WIDTH - 2 * MARGIN_X],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.black),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 14 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 16 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    focus_text = FOCUS_GUIDANCE.get(main_focus, FOCUS_GUIDANCE["General overview"])
    focus_data = [
        [Paragraph("PERSONALISED FOCUS", styles["label"])],
        [Paragraph(_inline_markup(focus_text), styles["focus"])],
    ]
    if personal_question.strip():
        focus_data.extend([
            [Paragraph("YOUR QUESTION", styles["label"])],
            [Paragraph(_inline_markup(personal_question.strip()), styles["focus"])],
        ])
    focus_table = Table(focus_data, colWidths=[PAGE_WIDTH - 2 * MARGIN_X])
    focus_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f3ef")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfcfca")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5 * mm),
    ]))
    return [cover, Spacer(1, 10 * mm), focus_table, Spacer(1, 7 * mm), Paragraph(
        "This report begins with your requested focus, then presents the calculated transitions, convergence windows, retrograde cycles and strategic conclusions.",
        styles["body"],
    ), PageBreak()]


def _markdown_table(lines: list[str], styles: dict, available_width: float):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append([Paragraph(_inline_markup(cell), styles["small"]) for cell in cells])
    if not rows:
        return Spacer(1, 1)
    column_count = max(len(row) for row in rows)
    for row in rows:
        row.extend([Paragraph("", styles["small"])] * (column_count - len(row)))
    widths = [available_width / column_count] * column_count
    table = Table(rows, colWidths=widths, repeatRows=1 if len(rows) > 1 else 0, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#8e8e88")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ededE8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    return table


def _markdown_flowables(markdown: str, styles: dict, available_width: float):
    lines = markdown.splitlines()
    story = []
    paragraph_buffer: list[str] = []
    list_buffer: list[tuple[str, str]] = []

    def flush_paragraph():
        if paragraph_buffer:
            text = " ".join(item.strip() for item in paragraph_buffer if item.strip())
            if text:
                story.append(Paragraph(_inline_markup(text), styles["body"]))
            paragraph_buffer.clear()

    def flush_list():
        if list_buffer:
            ordered = all(kind == "ordered" for kind, _ in list_buffer)
            items = [ListItem(Paragraph(_inline_markup(text), styles["body"]), leftIndent=4 * mm) for _, text in list_buffer]
            story.append(ListFlowable(items, bulletType="1" if ordered else "bullet", leftIndent=7 * mm, bulletFontName="Helvetica", bulletFontSize=8))
            list_buffer.clear()

    index = 0
    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip()

        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            flush_paragraph(); flush_list()
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(_markdown_table(table_lines, styles, available_width))
            story.append(Spacer(1, 3 * mm))
            continue

        stripped = line.strip()
        if not stripped:
            flush_paragraph(); flush_list()
            index += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph(); flush_list()
            level = len(heading.group(1))
            style = styles[{1: "h1", 2: "h2", 3: "h3"}[level]]
            story.append(Paragraph(_inline_markup(heading.group(2)), style))
            index += 1
            continue

        bullet = re.match(r"^-\s+(.+)$", stripped)
        numbered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            list_buffer.append(("ordered" if numbered else "bullet", (numbered or bullet).group(1)))
            index += 1
            continue

        if stripped in {"---", "***"}:
            flush_paragraph(); flush_list()
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999"), spaceBefore=2 * mm, spaceAfter=3 * mm))
            index += 1
            continue

        paragraph_buffer.append(stripped)
        index += 1

    flush_paragraph(); flush_list()
    return story


def build_report_pdf(
    result: dict,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> bytes:
    """Generate a print-ready A4 PDF from a deterministic report result."""
    output = BytesIO()
    styles = _styles()
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
    template = PageTemplate(id="report", frames=[frame], onPage=_page_header_footer)
    doc = BaseDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"{BRAND} - {result.get('sign', '')} {result.get('label', '')}",
        author=BRAND,
    )
    doc.addPageTemplates([template])

    story = []
    story.extend(_cover_block(result, main_focus, personal_question, order_reference, styles))
    story.extend(_markdown_flowables(str(result.get("markdown", "")), styles, PAGE_WIDTH - 2 * MARGIN_X))
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=0.7, color=colors.black))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Prepared by Luna Convergence using tropical geocentric planetary positions and whole-sign houses. The strength and timing labels describe the internal astrological framework; they are not probabilities or guarantees of events.",
        styles["small"],
    ))

    doc.build(story)
    return output.getvalue()


def report_filename(result: dict) -> str:
    sign = re.sub(r"[^a-z0-9]+", "-", str(result.get("sign", "report")).lower()).strip("-")
    label = re.sub(r"[^a-z0-9]+", "-", str(result.get("label", result.get("period", "report"))).lower()).strip("-")
    return f"luna-convergence-{sign}-{label}.pdf"
