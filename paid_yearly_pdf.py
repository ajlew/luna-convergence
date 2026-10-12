from __future__ import annotations

"""Paid Yearly PDF.

This is the printable companion to the Paid Monthly-style Year Ahead.
It consumes the SAME Natal Snapshot, YearPacket and one PaidYearlyEditorial
used by the web report. It performs no astrology calculations and no LLM call.
"""

from datetime import date, datetime, timedelta
from io import BytesIO
import math
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
    Image,
    KeepTogether,
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
            "Hero", parent=base["Title"], fontName="Times-Roman",
            fontSize=30, leading=34, textColor=colors.black,
            spaceAfter=4 * mm,
        ),
        "deck": ParagraphStyle(
            "Deck", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=15, textColor=colors.HexColor("#303030"),
            spaceAfter=7 * mm,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Times-Roman",
            fontSize=21, leading=25, spaceBefore=6 * mm, spaceAfter=4 * mm,
            textColor=colors.black,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Times-Roman",
            fontSize=16.5, leading=20, spaceBefore=5 * mm, spaceAfter=2.5 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=14, spaceBefore=3.2 * mm, spaceAfter=1.5 * mm,
            textColor=colors.black, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.4, leading=15, textColor=colors.HexColor("#151515"),
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
            "Issue", parent=base["Heading1"], fontName="Times-Roman",
            fontSize=21, leading=25, spaceBefore=3 * mm, spaceAfter=3 * mm,
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


def _svg_image(svg_text: str, max_width: float, max_height: float):
    """Render the canonical SVG as an in-memory image for predictable A4 printing.

    The web SVG remains authoritative. Never recalculate its positions here.
    """
    try:
        import cairosvg
        from PIL import Image as PILImage
        # Web SVG uses responsive percentage width; printed media needs explicit pixel dimensions.
        svg_text = re.sub(r'<svg[^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="760" viewBox="0 0 760 760">', svg_text, count=1)
        png = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), output_width=1400, background_color="white")
        pil = PILImage.open(BytesIO(png))
        width, height = pil.size
        scale = min(max_width / width, max_height / height)
        result = Image(BytesIO(png), width=width * scale, height=height * scale)
        result.hAlign = 'CENTER'
        return result
    except Exception:
        try:
            from svglib.svglib import svg2rlg
            drawing = svg2rlg(BytesIO(svg_text.encode("utf-8")))
            if drawing is None:
                return None
            scale = min(max_width / drawing.width, max_height / drawing.height)
            drawing.width *= scale
            drawing.height *= scale
            drawing.scale(scale, scale)
            return drawing
        except Exception:
            return None


def _natal_chart(snapshot: Any, styles) -> list:
    """Print the exact natal wheel SVG already used by the live site."""
    try:
        graphic = _svg_image(natal_wheel_svg(snapshot, size=760),
                             PAGE_WIDTH - 2*MARGIN_X, 100*mm)
        if graphic is not None:
            return [Spacer(1, 3*mm), graphic, Spacer(1, 3*mm)]
    except Exception:
        pass
    return [Paragraph("Natal chart graphic unavailable; chart evidence remains in the report.", styles['small'])]


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


class _YearTimeline(Flowable):
    """Printable analogue of the website's multi-lane Year Map."""
    def __init__(self, packet):
        super().__init__()
        self.packet = packet
        self.width = PAGE_WIDTH-2*MARGIN_X
        self.games = [g for g in packet.get('games', []) if isinstance(g,dict)]
        self.months = [m for m in packet.get('year_strip', []) if isinstance(m,dict)]
        self.height = 29*mm + max(1,len(self.games))*18*mm

    def draw(self):
        c=self.canv
        margin_label=37*mm
        left=margin_label
        track_w=self.width-left-3*mm
        period=self.packet.get('period',{})
        try:
            start=date.fromisoformat(str(period.get('start'))[:10]); end=date.fromisoformat(str(period.get('end'))[:10]); total=max(1,(end-start).days)
        except Exception:
            return
        c.setFillColor(colors.HexColor('#555555'))
        c.setFont('Helvetica',6.2)
        for idx,mo in enumerate(self.months[:12]):
            x=left+track_w*(idx+.5)/12
            label=str(mo.get('month') or '').upper()[:6]
            c.drawCentredString(x,self.height-9*mm,label)
        for ix,g in enumerate(self.games):
            y=self.height-(20+18*ix)*mm
            title=str(g.get('title') or 'Major game')
            if len(title)>21: title=title[:20]+'…'
            c.setFillColor(colors.HexColor('#222222'))
            c.setFont('Helvetica-Bold',7.1)
            c.drawString(0,y+2*mm,title)
            c.setFillColor(colors.HexColor('#eeeeed'))
            c.roundRect(left,y,track_w,6*mm,2*mm,fill=1,stroke=0)
            try:
                a=date.fromisoformat(str(g.get('start_date'))[:10]); b=date.fromisoformat(str(g.get('end_date'))[:10]);
                aa=max(start,a); bb=min(end,b)
                if bb>=aa:
                    xa=left+track_w*max(0,(aa-start).days)/total
                    xb=left+track_w*min(total,(bb-start).days)/total
                    c.setFillColor(colors.HexColor('#666666'))
                    c.roundRect(xa,y+1*mm,max(2*mm,xb-xa),4*mm,1.7*mm,fill=1,stroke=0)
            except Exception: pass
            primary=g.get('primary_transit') or {}
            for hit in primary.get('passes',[]) or []:
                try:
                    dt=date.fromisoformat(str(hit.get('date'))[:10]);
                    if start<=dt<=end:
                        x=left+track_w*(dt-start).days/total
                        c.setFillColor(colors.black); c.circle(x,y+3*mm,1.6*mm,stroke=0,fill=1)
                except Exception: pass
        ry=8*mm
        c.setFillColor(colors.HexColor('#555555')); c.setFont('Helvetica-Bold',7)
        c.drawString(0,ry+3*mm,'MONTHLY RHYTHM')
        for i,mo in enumerate(self.months[:12]):
            val=float(mo.get('intensity') or mo.get('score') or 0)
            if val<=0: val=1
            h=min(9*mm,2*mm+val*mm/5)
            x=left+track_w*(i+.2)/12
            c.setFillColor(colors.HexColor('#666666'))
            c.rect(x,ry,track_w*.55/12,h,fill=1,stroke=0)


def _year_map(packet: dict[str, Any], styles) -> list:
    if not packet.get('games'):
        return []
    return [Paragraph('How your year unfolds',styles['h2']),
            Paragraph('Each lane shows an important story; dots mark exact contacts. All dates come from your calculated transits.',styles['small']),
            _YearTimeline(packet)]




class _MonthContacts(Flowable):
    """Compact timeline of actual pass dates in this rolling month, not an invented chart."""
    def __init__(self, month, game):
        super().__init__()
        self.month=month; self.game=game
        self.width=PAGE_WIDTH-2*MARGIN_X; self.height=23*mm
    def draw(self):
        c=self.canv
        a=str(self.month.get('start_date') or self.month.get('start') or '')[:10]
        b=str(self.month.get('end_date') or self.month.get('end') or '')[:10]
        try:
            start=date.fromisoformat(a); end=date.fromisoformat(b)
        except Exception: return
        total=max(1,(end-start).days)
        x0=10*mm; w=self.width-20*mm; y=10*mm
        c.setLineWidth(1); c.setStrokeColor(colors.HexColor('#bcbcbc')); c.line(x0,y,x0+w,y)
        c.setFillColor(colors.HexColor('#666666')); c.setFont('Helvetica',7)
        c.drawString(x0,3*mm,start.strftime('%d %b'))
        c.drawRightString(x0+w,3*mm,end.strftime('%d %b'))
        primary=self.game.get('primary_transit') or {}
        for hit in primary.get('passes',[]) or []:
            try:
                d=date.fromisoformat(str(hit.get('date'))[:10]);
                if start<=d<=end:
                    x=x0+w*(d-start).days/total
                    c.setFillColor(colors.black); c.circle(x,y,2.4*mm,stroke=0,fill=1)
                    c.setFont('Helvetica',6.5); c.drawCentredString(x,y+4*mm,d.strftime('%d %b'))
            except Exception: pass

class _YearMonthlyActivation(Flowable):
    """Compact per-month natal activation from the precomputed YearPacket."""
    def __init__(self, snapshot, game):
        super().__init__()
        self.snapshot=snapshot
        self.game=game
        self.width=PAGE_WIDTH-2*MARGIN_X
        self.height=70*mm

    def draw(self):
        c=self.canv
        center=self.width/2
        cy=33*mm
        outer=29*mm
        c.setStrokeColor(colors.HexColor('#aaa'))
        c.setLineWidth(.7)
        c.circle(center,cy,outer,stroke=1,fill=0)
        c.circle(center,cy,outer*.75,stroke=1,fill=0)
        positions={str(p.planet):float(p.longitude) for p in getattr(self.snapshot,'positions',())}
        for i in range(12):
            a=math.radians(i*30-90)
            c.setStrokeColor(colors.HexColor('#c8c8c8'))
            c.line(center+outer*.75*math.cos(a),cy+outer*.75*math.sin(a),center+outer*math.cos(a),cy+outer*math.sin(a))
        for name, lon in positions.items():
            a=math.radians(lon-90)
            r=outer*.61
            x,y=center+r*math.cos(a),cy+r*math.sin(a)
            c.setFont('Helvetica',5.4)
            c.setFillColor(colors.HexColor('#666'))
            c.drawCentredString(x,y,name[:3].upper())
        contacts=[self.game.get('primary_transit') or {}]+list(self.game.get('supporting_transits') or [])[:2]
        seen=set()
        for item in contacts:
            target=str(item.get('natal_target') or '')
            if target in seen or target not in positions:continue
            seen.add(target)
            a=math.radians(positions[target]-90)
            x,y=center+outer*.85*math.cos(a),cy+outer*.85*math.sin(a)
            c.setStrokeColor(colors.HexColor('#8872a8'))
            c.setLineWidth(1.1)
            c.line(center,cy,x,y)
            c.setFillColor(colors.HexColor('#d2c5e7'))
            c.circle(x,y,2.7*mm,stroke=0,fill=1)
        c.setFillColor(colors.black)
        c.setFont('Helvetica',7)
        c.drawCentredString(center,cy-3*mm,'LUNA')
        c.setFillColor(colors.HexColor('#555'))
        c.setFont('Helvetica',6.6)
        c.drawCentredString(center,1*mm,'Natal reference and selected game activations - calculated positions only')


def _monthly_chapter_pages(packet: dict[str, Any], editorial: PaidYearlyEditorial | None, styles, snapshot=None) -> list:
    """Twelve stand-alone printed monthly chapters from the existing YearPacket.

    Layout only: do not calculate astrology or make a provider call. Each
    chapter starts on a new A4 page, while oversized contents flow naturally.
    """
    rounds = [r for r in (packet.get("monthly_rounds") or []) if isinstance(r, dict)]
    games = {int(g.get("number") or 0): g for g in (packet.get("games") or []) if isinstance(g, dict)}
    if not rounds:
        return []
    out = [PageBreak(), Paragraph("Your year, one month at a time", styles["h1"]),
           Paragraph("Each chapter is one stage of your rolling year. Dates and themes come from your calculated transits.", styles["small"])]
    for index, month in enumerate(rounds, start=1):
        if index > 1:
            out.append(PageBreak())
        game = games.get(int(month.get("dominant_game_number") or 0), {})
        editorial_month = editorial.month_for(index) if editorial is not None else None
        focus = str(getattr(editorial_month, "focus", "") or month.get("focus") or "").strip()
        out.extend([
            Paragraph(f"MONTH {index:02d} / {_xml(month.get('label') or '')}", styles["label"]),
            Paragraph(_xml(month.get("dominant_game_title") or "A quieter chapter"), styles["h1"]),
            Paragraph(f"<b>Period:</b> {_xml(str(month.get('phase') or '').replace('_', ' ').title())}", styles["small"]),
        ])
        if focus:
            out.extend([Paragraph("Luna's focus", styles["h3"]), Paragraph(_xml(focus), styles["body"])])
        if month.get("strongest_date"):
            out.extend([
                Paragraph("Key moment", styles["h3"]),
                Paragraph(_xml(_date_label(month["strongest_date"])) + " - " + _xml(month.get("strongest_label") or month.get("strongest_kind") or "Calculated contact"), styles["body"]),
            ])
        if game:
            out.append(Paragraph("Personal transit timeline", styles["h3"]))
            out.append(_MonthContacts(month,game))
            out.append(Paragraph("The longer story at work", styles["h3"]))
            primary = game.get("primary_transit") or {}
            if primary.get("technical_label"):
                out.append(Paragraph(_xml(primary["technical_label"]), styles["body"]))
            for support in (game.get("supporting_transits") or [])[:2]:
                if isinstance(support, dict) and support.get("technical_label"):
                    out.append(Paragraph(_xml(support["technical_label"]), styles["small"]))
            if snapshot is not None:
                out.append(Paragraph("Your natal activation", styles["h3"]))
                out.append(_YearMonthlyActivation(snapshot, game))
            out.append(Paragraph("Explore the full Major Issue chapter for pass-by-pass interpretation and technical evidence.", styles["small"]))
    return out

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
    # Use the same HTML/CSS design language as Paid Monthly for print output.
    # Fall back to the previous ReportLab renderer only if the HTML engine is absent.
    try:
        from yearly_print_html import build_yearly_print_html, render_yearly_html_pdf
        html = build_yearly_print_html(snapshot=snapshot, packet=value, editorial=editorial,
            label=label, main_focus=main_focus, personal_question=personal_question,
            order_reference=order_reference)
        return render_yearly_html_pdf(html)
    except (ImportError, OSError) as exc:
        # Linux Streamlit hosts can lack the native GLib/Pango dependencies
        # required by WeasyPrint. Do not block paid/owner report delivery.
        # Render the established ReportLab Year Ahead PDF instead.
        pass
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
        story.append(Paragraph(f"<b>Order reference:</b> {_xml(order_reference)}", styles["small"]))

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
    story += _monthly_chapter_pages(value, editorial, styles, snapshot=snapshot)

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
