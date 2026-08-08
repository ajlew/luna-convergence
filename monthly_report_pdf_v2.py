from __future__ import annotations
from solar_cycle import solar_gate_label

from datetime import date
from io import BytesIO
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from monthly_narrative_v1 import build_monthly_narrative, normalise_personal_question


BRAND = "Luna Convergence"
TAGLINE = "The universe shifts. You've got this."
PAGE_WIDTH, PAGE_HEIGHT = A4
BLACK = colors.HexColor("#050505")
INK = colors.HexColor("#151515")
PAPER = colors.HexColor("#F7F6F1")
SOFT = colors.HexColor("#ECEAE3")
MID = colors.HexColor("#D7D5CE")
GREY = colors.HexColor("#696963")
WHITE = colors.white
CONTENT_X = 17 * mm
CONTENT_TOP = 21 * mm
CONTENT_BOTTOM = 17 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * CONTENT_X


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
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = text.replace("\n", "<br/>")
    return text


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_brand": ParagraphStyle(
            "CoverBrand", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9, leading=11, textColor=WHITE, tracking=2.2,
        ),
        "cover_kicker": ParagraphStyle(
            "CoverKicker", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7, leading=9, textColor=colors.HexColor("#A9A9A4"), tracking=1.6,
        ),
        "cover_hook": ParagraphStyle(
            "CoverHook", parent=base["Title"], fontName="Times-Bold",
            fontSize=38, leading=39, textColor=WHITE, spaceAfter=7 * mm,
        ),
        "cover_theme": ParagraphStyle(
            "CoverTheme", parent=base["BodyText"], fontName="Helvetica",
            fontSize=11, leading=15, textColor=colors.HexColor("#E4E4DF"),
        ),
        "cover_deck": ParagraphStyle(
            "CoverDeck", parent=base["BodyText"], fontName="Times-Roman",
            fontSize=12, leading=17, textColor=WHITE,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.5, leading=13, textColor=colors.HexColor("#D6D6D1"),
        ),
        "kicker": ParagraphStyle(
            "Kicker", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7, leading=9, textColor=GREY, tracking=1.4, spaceAfter=2 * mm,
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Heading1"], fontName="Times-Bold",
            fontSize=28, leading=30, textColor=INK, spaceAfter=5 * mm,
        ),
        "hook": ParagraphStyle(
            "Hook", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=18, leading=21, textColor=INK, spaceAfter=2 * mm,
        ),
        "theme": ParagraphStyle(
            "Theme", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.5, leading=12, textColor=GREY,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Times-Roman",
            fontSize=10.4, leading=15.2, textColor=INK, spaceAfter=3.2 * mm,
        ),
        "body_compact": ParagraphStyle(
            "BodyCompact", parent=base["BodyText"], fontName="Times-Roman",
            fontSize=9.3, leading=13.3, textColor=INK,
        ),
        "sans": ParagraphStyle(
            "Sans", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.5, leading=12, textColor=INK,
        ),
        "sans_small": ParagraphStyle(
            "SansSmall", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.3, leading=10.1, textColor=INK,
        ),
        "label": ParagraphStyle(
            "Label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=6.6, leading=8, textColor=GREY, tracking=1.1,
        ),
        "label_white": ParagraphStyle(
            "LabelWhite", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=6.6, leading=8, textColor=colors.HexColor("#BDBDB8"), tracking=1.1,
        ),
        "card_hook": ParagraphStyle(
            "CardHook", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=15, leading=17.5, textColor=INK, spaceAfter=1.8 * mm,
        ),
        "date_title": ParagraphStyle(
            "DateTitle", parent=base["Heading3"], fontName="Times-Bold",
            fontSize=10.5, leading=12.3, textColor=INK, spaceAfter=1.2 * mm,
        ),
        "card_action": ParagraphStyle(
            "CardAction", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=8.2, leading=11.5, textColor=INK,
        ),
        "white_hook": ParagraphStyle(
            "WhiteHook", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=23, leading=25, textColor=WHITE, spaceAfter=2 * mm,
        ),
        "white_body": ParagraphStyle(
            "WhiteBody", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=colors.HexColor("#E5E5E0"),
        ),
        "tech_h": ParagraphStyle(
            "TechH", parent=base["Heading2"], fontName="Times-Bold",
            fontSize=15, leading=18, textColor=INK, spaceBefore=4 * mm, spaceAfter=2 * mm,
        ),
        "mono": ParagraphStyle(
            "Mono", parent=base["BodyText"], fontName="Courier",
            fontSize=7.2, leading=10, textColor=INK,
        ),
    }


def _cover_canvas(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BLACK)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setStrokeColor(colors.HexColor("#252525"))
    canvas.setLineWidth(0.7)
    canvas.line(18 * mm, 18 * mm, PAGE_WIDTH - 18 * mm, 18 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#A7A7A2"))
    canvas.drawString(18 * mm, 11.5 * mm, TAGLINE.upper())
    canvas.restoreState()


def _content_canvas(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(MID)
    canvas.setLineWidth(0.45)
    canvas.line(CONTENT_X, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - CONTENT_X, PAGE_HEIGHT - 13 * mm)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(INK)
    canvas.drawString(CONTENT_X, PAGE_HEIGHT - 9.4 * mm, BRAND.upper())
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    canvas.drawRightString(
        PAGE_WIDTH - CONTENT_X,
        PAGE_HEIGHT - 9.4 * mm,
        f"{getattr(doc, 'report_sign', '').upper()} / {getattr(doc, 'report_label', '').upper()}",
    )
    canvas.line(CONTENT_X, 11.5 * mm, PAGE_WIDTH - CONTENT_X, 11.5 * mm)
    canvas.setFont("Helvetica", 6.5)
    canvas.drawString(CONTENT_X, 7 * mm, "Symbolic astrology, not professional advice.")
    canvas.drawRightString(PAGE_WIDTH - CONTENT_X, 7 * mm, f"{canvas.getPageNumber()}")
    canvas.restoreState()


def _p(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_safe(text), style)


def _section_header(kicker: str, title: str, styles: dict) -> list:
    return [
        _p(kicker.upper(), styles["kicker"]),
        _p(title, styles["section"]),
        HRFlowable(width="100%", thickness=0.6, color=INK, spaceAfter=5 * mm),
    ]


def _small_card(label: str, value: str, styles: dict, dark: bool = False):
    background = BLACK if dark else PAPER
    label_style = styles["label_white"] if dark else styles["label"]
    value_style = styles["white_body"] if dark else styles["card_action"]
    card = Table(
        [[[_p(label.upper(), label_style), Spacer(1, 1.5 * mm), _p(value, value_style)]]],
    )
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.6, BLACK if not dark else colors.HexColor("#2B2B2B")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _cover(narrative, styles: dict):
    focus_line = narrative.main_focus
    if narrative.personal_question:
        focus_line += f" / {narrative.personal_question}"
    return [
        _p(BRAND.upper(), styles["cover_brand"]),
        Spacer(1, 22 * mm),
        _p("MONTHLY CONVERGENCE", styles["cover_kicker"]),
        Spacer(1, 4 * mm),
        _p(narrative.convergence_axis, styles["cover_theme"]),
        Spacer(1, 7 * mm),
        _p(narrative.hook_headline, styles["cover_hook"]),
        _p(f"**THEME** / {narrative.headline}", styles["cover_theme"]),
        Spacer(1, 10 * mm),
        _p(narrative.at_glance[0], styles["cover_deck"]),
        Spacer(1, 15 * mm),
        HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#474747"), spaceAfter=5 * mm),
        _p(f"MONTHLY STRATEGIC REPORT\n{narrative.sign} / {narrative.label}\nFOCUS / {focus_line}", styles["cover_meta"]),
        NextPageTemplate("content"),
        PageBreak(),
    ]


def _at_glance(narrative, styles: dict):
    strongest = dict(narrative.snapshot_rows).get("Strongest window", "")
    second = dict(narrative.snapshot_rows).get("Second turning point", "")
    left = [
        _p(narrative.headline, styles["hook"]),
        _p(narrative.subtitle, styles["theme"]),
        Spacer(1, 4 * mm),
    ]
    for paragraph in narrative.at_glance:
        left.append(_p(paragraph, styles["body"]))
    if narrative.focus_answer:
        left.extend([
            Spacer(1, 2 * mm),
            _p(narrative.focus_title.upper(), styles["kicker"]),
            _p(narrative.focus_answer[0], styles["body"]),
        ])

    right = [
        _small_card("Do", narrative.do_line, styles, dark=True),
        Spacer(1, 4 * mm),
        _small_card("Don't", narrative.dont_line, styles),
        Spacer(1, 4 * mm),
        _small_card("The opening", strongest, styles),
        Spacer(1, 4 * mm),
        _small_card("The reality check", second, styles),
    ]
    layout = Table(
        [[left, right]],
        colWidths=[112 * mm, CONTENT_WIDTH - 118 * mm],
        hAlign="LEFT",
    )
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 6 * mm),
        ("LEFTPADDING", (1, 0), (1, 0), 0),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return _section_header("Your month", "Your month at a glance", styles) + [layout, PageBreak()]


def _chapter_card(chapter, number: int, styles: dict):
    evidence = " / ".join(chapter.evidence[:3]) or "Calculated monthly transitions"
    body = [
        _p(f"CHAPTER {number} / {chapter.date_range}", styles["label"]),
        Spacer(1, 1.5 * mm),
        _p(chapter.hook, styles["card_hook"]),
        _p(chapter.title, styles["theme"]),
        Spacer(1, 2.5 * mm),
        _p(chapter.paragraphs[0], styles["body_compact"]),
        Spacer(1, 2 * mm),
        _p(f"**YOUR MOVE** / {chapter.action}", styles["card_action"]),
        Spacer(1, 2 * mm),
        _p(f"EVIDENCE / {evidence}", styles["sans_small"]),
    ]
    table = Table([[[*body]]], colWidths=[CONTENT_WIDTH])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER if number % 2 else WHITE),
        ("BOX", (0, 0), (-1, -1), 0.7, INK),
        ("LINEBEFORE", (0, 0), (0, -1), 4, BLACK),
        ("LEFTPADDING", (0, 0), (-1, -1), 7 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _chapters(narrative, styles: dict):
    story = _section_header("Timing", "The month in three chapters", styles)
    for index, chapter in enumerate(narrative.chapters, 1):
        story.extend([_chapter_card(chapter, index, styles), Spacer(1, 4 * mm)])
    story.append(PageBreak())
    return story


def _life_card(label: str, hook: str, paragraphs: tuple[str, ...], styles: dict):
    best_move = paragraphs[-1] if paragraphs else ""
    if best_move.lower().startswith("best ") and ":" in best_move:
        best_move = best_move.split(":", 1)[1].strip()
    content = [
        _p(label.upper(), styles["label"]),
        Spacer(1, 1 * mm),
        _p(hook, styles["card_hook"]),
        _p(paragraphs[0] if paragraphs else "", styles["body_compact"]),
        Spacer(1, 2 * mm),
        _p(f"**BEST MOVE** / {best_move}", styles["card_action"]),
    ]
    card = Table([[[*content]]], colWidths=[CONTENT_WIDTH])
    card.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, MID),
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _life_areas(narrative, styles: dict):
    story = _section_header("Real life", "Love, work and money", styles)
    areas = [
        ("Love and relationships", narrative.love_hook, narrative.love_story),
        ("Work and direction", narrative.work_hook, narrative.work_story),
        ("Money and security", narrative.money_hook, narrative.money_story),
    ]
    for label, hook, paragraphs in areas:
        story.extend([_life_card(label, hook, paragraphs, styles), Spacer(1, 4 * mm)])
    story.append(PageBreak())
    return story


def _key_date_card(item, styles: dict):
    content = [
        _p(item.date_label.upper(), styles["label"]),
        _p(item.evidence, styles["date_title"]),
        _p(item.consequence, styles["sans_small"]),
        Spacer(1, 1.2 * mm),
        _p(f"**YOUR MOVE** / {item.response}", styles["sans_small"]),
    ]
    card = Table([[[*content]]], colWidths=[(CONTENT_WIDTH - 8 * mm) / 3])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), 0.45, MID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card


def _strategy(narrative, styles: dict):
    story = _section_header("Practical direction", "Your monthly strategy", styles)
    top = Table(
        [[
            _small_card("Hidden opportunity", narrative.hidden_opportunity, styles),
            _small_card("Watch out", narrative.watch_out, styles, dark=True),
        ]],
        colWidths=[(CONTENT_WIDTH - 5 * mm) / 2] * 2,
    )
    top.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 2.5 * mm),
        ("LEFTPADDING", (1, 0), (1, 0), 2.5 * mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([top, Spacer(1, 5 * mm)])

    actions = "\n".join(
        f"**{index}**  {action}"
        for index, action in enumerate(narrative.action_plan, 1)
    )
    action_box = Table([[_p(actions, styles["sans"]) ]], colWidths=[CONTENT_WIDTH])
    action_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))
    story.extend([_p("THREE MOVES FOR THE MONTH", styles["kicker"]), action_box, Spacer(1, 5 * mm)])
    story.append(_p("Key dates", styles["hook"]))

    featured_dates = list(narrative.key_dates[:6])
    cards = [_key_date_card(item, styles) for item in featured_dates]
    rows = []
    card_width = (CONTENT_WIDTH - 8 * mm) / 3
    for index in range(0, len(cards), 3):
        group = cards[index:index + 3]
        while len(group) < 3:
            group.append(Spacer(card_width, 1))
        rows.append(group)
    grid = Table(rows, colWidths=[card_width] * 3, hAlign="LEFT")
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    story.append(grid)

    if len(narrative.key_dates) > 6:
        final_date = narrative.key_dates[6]
        story.extend([
            Spacer(1, 2 * mm),
            _small_card(
                f"Also watch {final_date.date_label} / {final_date.evidence}",
                final_date.response,
                styles,
            ),
        ])

    story.append(PageBreak())
    return story


def _evidence_grid(rows: tuple[tuple[str, str], ...], styles: dict):
    cards = []
    for label, value in rows:
        cards.append(_small_card(label, value, styles))
    grid_rows = []
    for index in range(0, len(cards), 2):
        pair = cards[index:index + 2]
        if len(pair) == 1:
            pair.append(Spacer((CONTENT_WIDTH - 5 * mm) / 2, 1))
        grid_rows.append(pair)
    grid = Table(grid_rows, colWidths=[(CONTENT_WIDTH - 5 * mm) / 2] * 2)
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 2.5 * mm),
        ("LEFTPADDING", (1, 0), (1, -1), 2.5 * mm),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return grid


def _solar(narrative, styles: dict):
    story = _section_header("Solar convergence", "The month beneath the month", styles)
    hero = Table(
        [[[
            _p("YOUR SOLAR CONVERGENCE", styles["label_white"]),
            Spacer(1, 2 * mm),
            _p(narrative.solar_title, styles["white_hook"]),
            _p(narrative.solar_rule, styles["white_body"]),
        ]]],
        colWidths=[CONTENT_WIDTH],
    )
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLACK),
        ("LEFTPADDING", (0, 0), (-1, -1), 7 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 7 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7 * mm),
    ]))
    story.extend([hero, Spacer(1, 5 * mm)])
    for paragraph in narrative.solar_paragraphs[:2]:
        story.append(_p(paragraph, styles["body"]))
    story.extend([Spacer(1, 2 * mm), _evidence_grid(narrative.solar_rows, styles), Spacer(1, 3 * mm)])

    response_rows = (
        ("Opportunity", narrative.solar_opportunity),
        ("Risk", narrative.solar_risk),
        ("Strategic response", narrative.solar_action),
    )
    response_cards = [_small_card(label, value, styles, dark=(label == "Risk")) for label, value in response_rows]
    response_table = Table([response_cards], colWidths=[CONTENT_WIDTH / 3] * 3)
    response_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([
        response_table,
        Spacer(1, 4 * mm),
        _p(f"WHY LUNA REACHED THIS CONCLUSION / {narrative.solar_equation}", styles["sans_small"]),
        PageBreak(),
    ])
    return story


def _snapshot(narrative, styles: dict):
    story = _section_header("Explainable evidence", "Monthly Sky Snapshot", styles)
    story.extend([
        _p("Why this month feels different", styles["hook"]),
        _p(
            "The story comes first. These cards preserve the calculation without making the customer read a spreadsheet before receiving the meaning.",
            styles["body"],
        ),
        _evidence_grid(narrative.snapshot_rows, styles),
        Spacer(1, 3 * mm),
        _p(
            "The concentration score measures how strongly one internal astrological pattern dominates the month. It is not the probability that a predicted event will occur.",
            styles["sans_small"],
        ),
        PageBreak(),
    ])
    return story


def _tech_table(headers, rows, widths, styles: dict):
    data = [[_p(header, styles["label"]) for header in headers]]
    for row in rows:
        data.append([_p(value, styles["sans_small"]) for value in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SOFT),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#999994")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    return table


def _date_label(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.strftime('%B')} {parsed.day}"


def _technical(result: dict, narrative, order_reference: str, styles: dict):
    story = _section_header("For readers who want the calculation", "Technical appendix", styles)
    story.append(_p(
        "House numbers, event names and strength scores are the evidence trail. The main report translates them into timing, consequences and practical decisions.",
        styles["body"],
    ))

    solar = result.get("solar_convergence") or {}
    solar_rows = [
        ("Tropical Sun", f"{solar.get('solar_longitude', 'n/a')} deg {solar.get('solar_sign', '')}"),
        ("Solar quarter", str(solar.get("solar_quarter", "n/a"))),
        ("Local light", f"{solar.get('light_direction', 'n/a')} from {solar.get('city', 'timezone estimate')}"),
        ("Activated house", f"{solar.get('activated_house', 'n/a')} - {solar.get('activated_house_name', '')}"),
        ("Solar gate", f"{solar_gate_label(solar.get('next_solar_gate', 'n/a'))} - {solar.get('next_gate_date', '')}"),
        ("Location basis", str(solar.get("location_basis", "n/a"))),
    ]
    story.extend([
        _p("Solar Convergence evidence", styles["tech_h"]),
        _tech_table(("Evidence", "Calculated value"), solar_rows, [55 * mm, CONTENT_WIDTH - 55 * mm], styles),
    ])

    dominant_rows = []
    for rank, item in enumerate(result.get("dominant_houses") or [], 1):
        dominant_rows.append((
            str(rank), str(item.get("house", "")), str(item.get("topic", "")), f"{float(item.get('weight', 0.0)):.1f}",
        ))
    story.extend([
        _p("Dominant house evidence", styles["tech_h"]),
        _tech_table(
            ("Rank", "House", "Customer life area", "Weight"),
            dominant_rows,
            [14 * mm, 16 * mm, CONTENT_WIDTH - 54 * mm, 24 * mm],
            styles,
        ),
    ])

    convergence_rows = []
    for item in result.get("convergences") or []:
        start = _date_label(item.get("start_date", ""))
        end = _date_label(item.get("end_date", ""))
        if start.split()[0] == end.split()[0]:
            window = f"{start}-{end.split()[-1]}"
        else:
            window = f"{start}-{end}"
        convergence_rows.append((
            window,
            str(item.get("label", "Convergence")),
            f"{float(item.get('score', 0.0)):.0f}/100",
            ", ".join(str(value) for value in item.get("dominant_houses") or []),
        ))
    story.extend([
        _p("Convergence windows", styles["tech_h"]),
        _tech_table(
            ("Window", "Type", "Strength", "Houses"),
            convergence_rows,
            [38 * mm, 65 * mm, 27 * mm, CONTENT_WIDTH - 130 * mm],
            styles,
        ),
        PageBreak(),
    ])

    story.extend(_section_header("Calculation trail", "Transitions and climate", styles))
    transition_rows = []
    for item in result.get("major_transitions") or []:
        transition_rows.append((
            _date_label(item.get("event_date", "")),
            str(item.get("title", "Transition")),
            ", ".join(str(value) for value in item.get("houses") or []),
        ))
    story.extend([
        _p("Major transitions", styles["tech_h"]),
        _tech_table(
            ("Date", "Evidence", "Houses"),
            transition_rows,
            [34 * mm, CONTENT_WIDTH - 58 * mm, 24 * mm],
            styles,
        ),
    ])

    retro_rows = []
    for item in result.get("retrograde_cycles") or []:
        retro_rows.append((
            str(item.get("planet", "")),
            _date_label(item.get("retrograde_start", "")),
            _date_label(item.get("direct_date", "")),
            ", ".join(str(value) for value in item.get("houses") or []),
        ))
    story.extend([
        _p("Retrograde climate", styles["tech_h"]),
        _tech_table(
            ("Planet", "Retrograde", "Direct", "Houses"),
            retro_rows,
            [35 * mm, 42 * mm, 42 * mm, CONTENT_WIDTH - 119 * mm],
            styles,
        ),
        _p("Method", styles["tech_h"]),
        _p(
            "Tropical geocentric planetary positions are calculated with Swiss Ephemeris and interpreted using whole-sign houses. Strength labels describe the concentration of the internal astrological pattern; they are not probabilities or guarantees of events.",
            styles["body_compact"],
        ),
    ])
    if order_reference:
        story.extend([
            _p("ORDER REFERENCE", styles["kicker"]),
            _p(order_reference, styles["mono"]),
        ])
    return story


def build_monthly_editorial_pdf(
    result: dict,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> bytes:
    narrative = build_monthly_narrative(
        result,
        main_focus=main_focus,
        personal_question=normalise_personal_question(personal_question),
        order_reference=order_reference,
    )
    styles = _styles()
    output = BytesIO()

    cover_frame = Frame(
        18 * mm, 20 * mm, PAGE_WIDTH - 36 * mm, PAGE_HEIGHT - 38 * mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="cover",
    )
    content_frame = Frame(
        CONTENT_X, CONTENT_BOTTOM, CONTENT_WIDTH,
        PAGE_HEIGHT - CONTENT_TOP - CONTENT_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="content",
    )
    cover_template = PageTemplate(id="cover", frames=[cover_frame], onPage=_cover_canvas)
    content_template = PageTemplate(id="content", frames=[content_frame], onPage=_content_canvas)

    doc = BaseDocTemplate(
        output,
        pagesize=A4,
        leftMargin=CONTENT_X,
        rightMargin=CONTENT_X,
        topMargin=CONTENT_TOP,
        bottomMargin=CONTENT_BOTTOM,
        title=f"{BRAND} - {narrative.sign} {narrative.label}",
        author=BRAND,
    )
    doc.report_sign = narrative.sign
    doc.report_label = narrative.label
    doc.addPageTemplates([cover_template, content_template])

    story = []
    story.extend(_cover(narrative, styles))
    story.extend(_at_glance(narrative, styles))
    story.extend(_chapters(narrative, styles))
    story.extend(_life_areas(narrative, styles))
    story.extend(_strategy(narrative, styles))
    story.extend(_solar(narrative, styles))
    story.extend(_snapshot(narrative, styles))
    story.extend(_technical(result, narrative, order_reference, styles))

    doc.build(story)
    return output.getvalue()
