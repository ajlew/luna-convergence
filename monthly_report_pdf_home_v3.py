from __future__ import annotations

import base64
from datetime import date
from html import escape
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from monthly_narrative_v1 import build_monthly_narrative, normalise_personal_question
from monthly_report_pdf_v2 import build_monthly_editorial_pdf


BRAND = "Luna Convergence"
TAGLINE = "The universe shifts. You've got this."
FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&"
    "family=IBM+Plex+Mono:wght@400;500;600&"
    "family=Josefin+Sans:wght@300;400;500;600;700&display=swap');"
)


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
    return escape(text)


def _asset_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _font_face_css() -> str:
    """Use exact local families when present and Google Fonts otherwise.

    The public app already imports the three Google Fonts. The local declarations
    make offline generation deterministic in development and do not package or
    redistribute font files with Luna.
    """
    candidates = {
        "Bodoni Moda": [
            ("normal", 400, Path("/usr/share/texlive/texmf-dist/fonts/opentype/impallari/librebodoni/LibreBodoni-Regular.otf")),
            ("normal", 600, Path("/usr/share/texlive/texmf-dist/fonts/opentype/impallari/librebodoni/LibreBodoni-Bold.otf")),
        ],
        "Josefin Sans": [
            ("normal", 300, Path("/usr/share/texlive/texmf-dist/fonts/truetype/public/josefin/JosefinSans-Light.ttf")),
            ("normal", 400, Path("/usr/share/texlive/texmf-dist/fonts/truetype/public/josefin/JosefinSans-Regular.ttf")),
            ("normal", 500, Path("/usr/share/texlive/texmf-dist/fonts/truetype/public/josefin/JosefinSans-Medium.ttf")),
            ("normal", 600, Path("/usr/share/texlive/texmf-dist/fonts/truetype/public/josefin/JosefinSans-SemiBold.ttf")),
            ("normal", 700, Path("/usr/share/texlive/texmf-dist/fonts/truetype/public/josefin/JosefinSans-Bold.ttf")),
        ],
        "IBM Plex Mono": [
            ("normal", 400, Path("/usr/share/texlive/texmf-dist/fonts/opentype/ibm/plex/IBMPlexMono-Regular.otf")),
            ("normal", 500, Path("/usr/share/texlive/texmf-dist/fonts/opentype/ibm/plex/IBMPlexMono-Medium.otf")),
            ("normal", 600, Path("/usr/share/texlive/texmf-dist/fonts/opentype/ibm/plex/IBMPlexMono-SemiBold.otf")),
        ],
    }
    rules: list[str] = []
    for family, variants in candidates.items():
        for style, weight, path in variants:
            if path.exists():
                rules.append(
                    "@font-face {"
                    f"font-family:'{family}';"
                    f"src:url('{path.as_uri()}') format('opentype');"
                    f"font-style:{style};font-weight:{weight};font-display:block;"
                    "}"
                )
    return "\n".join(rules)


def _brand_header(icon_uri: str, right: str) -> str:
    icon = f'<img class="brand-icon" src="{icon_uri}" alt="" />' if icon_uri else '<span class="brand-icon fallback">LC</span>'
    return f"""
<header class="brand-row">
  <div class="brand-lockup">{icon}<span class="brand-name">Luna Convergence</span></div>
  <div class="brand-note">Strategic astrology / planetary timing / convergence</div>
</header>
<nav class="top-nav" aria-label="Report navigation">
  <span class="active">Home</span><span>Daily horoscope</span><span class="active-report">Monthly report</span>
  <span>House guide</span><span>Solar year</span><span>How it works</span>
</nav>
<div class="report-meta-top">{_safe(right)}</div>
"""


def _footer(page: int) -> str:
    return f"""
<footer class="page-footer">
  <span>Symbolic astrology, not professional advice.</span>
  <span>{page}</span>
</footer>
"""


def _page(body: str, icon_uri: str, right: str, page: int, extra_class: str = "") -> str:
    return f"""
<section class="page {extra_class}">
  {_brand_header(icon_uri, right)}
  <main class="page-content">{body}</main>
  {_footer(page)}
</section>
"""


def _card(label: str, title: str, body: str, action: str = "", dark: bool = False) -> str:
    cls = "card dark-card" if dark else "card"
    action_html = f'<div class="best-move"><span>Best move</span><strong>{_safe(action)}</strong></div>' if action else ""
    return f"""
<article class="{cls}">
  <div class="mono-label">{_safe(label)}</div>
  <h3>{_safe(title)}</h3>
  <p>{_safe(body)}</p>
  {action_html}
</article>
"""


def _clean_best_move(paragraphs: tuple[str, ...]) -> str:
    if not paragraphs:
        return ""
    value = paragraphs[-1]
    if ":" in value and value.lower().startswith("best"):
        return value.split(":", 1)[1].strip()
    return value


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    head = "".join(f"<th>{_safe(value)}</th>" for value in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_safe(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _date_label(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.strftime('%B')} {parsed.day}"


def _render_html(result: dict, narrative, order_reference: str, icon_uri: str) -> str:
    report_right = f"{narrative.sign} / {narrative.label}"
    snapshot = dict(narrative.snapshot_rows)

    # Page 1 - direct structural match to the Luna homepage.
    page1_body = f"""
<div class="hero-grid home-hero">
  <section class="hero-left">
    <div class="eyebrow">Monthly / timing / practical interpretation</div>
    <h1 class="editorial-title">{_safe(narrative.hook_headline)}</h1>
    <p class="hero-subtitle">{_safe(narrative.at_glance[0])}</p>
    <div class="hero-rule"></div>
    <div class="form-grid">
      <div class="field"><span>Star sign</span><strong>{_safe(narrative.sign)}</strong></div>
      <div class="field"><span>Report period</span><strong>{_safe(narrative.label)}</strong></div>
      <div class="field"><span>Main focus</span><strong>{_safe(narrative.main_focus)}</strong></div>
      <div class="field"><span>Report type</span><strong>Monthly strategic report</strong></div>
    </div>
  </section>
  <aside class="reading-card">
    <div class="daily-kicker">Monthly convergence / {_safe(narrative.sign)}</div>
    <div class="daily-headline">{_safe(narrative.headline)}</div>
    <p class="muted-white">{_safe(narrative.subtitle)}</p>
    <p class="muted-white compact">{_safe(narrative.at_glance[1] if len(narrative.at_glance) > 1 else narrative.at_glance[0])}</p>
    <div class="daily-date">{_safe(narrative.label)} / {_safe(narrative.convergence_axis)}</div>
  </aside>
</div>
<div class="trust-strip">
  <div class="trust-item">Swiss Ephemeris calculations</div>
  <div class="trust-item">Whole-sign house explanations</div>
  <div class="trust-item">Retrograde-cycle analysis</div>
  <div class="trust-item">Convergence-point interpretation</div>
</div>
<div class="homepage-band">
  <div><span class="mono-label">Your month</span><h2>The story comes first</h2></div>
  <p>The report follows the same Luna method as the daily reading: emotional hook, practical meaning and action first; calculation evidence later.</p>
</div>
"""

    # Page 2 - at a glance, using the homepage hero/card rhythm.
    glance_paragraphs = "".join(f"<p>{_safe(value)}</p>" for value in narrative.at_glance)
    focus_html = "".join(f"<p>{_safe(value)}</p>" for value in narrative.focus_answer[:2])
    page2_body = f"""
<div class="section-hero two-column">
  <section>
    <div class="eyebrow">Your month / at a glance</div>
    <h1 class="section-title">August wants more than a spark</h1>
    <div class="forecast-copy">{glance_paragraphs}</div>
  </section>
  <aside class="reading-card do-card">
    <div class="daily-kicker">Do</div>
    <div class="mini-headline">{_safe(narrative.do_line)}</div>
    <div class="rule-white"></div>
    <div class="daily-kicker">Don't</div>
    <div class="mini-headline">{_safe(narrative.dont_line)}</div>
  </aside>
</div>
<div class="best-move wide"><span>{_safe(narrative.focus_title)}</span><strong>{focus_html}</strong></div>
<div class="trust-strip two">
  <div class="trust-item"><b>The opening</b><br>{_safe(snapshot.get('Strongest window', ''))}</div>
  <div class="trust-item"><b>The reality check</b><br>{_safe(snapshot.get('Second turning point', ''))}</div>
</div>
"""

    # Page 3 - chapters styled as homepage cards, not report blocks.
    chapter_cards = []
    for index, chapter in enumerate(narrative.chapters, 1):
        evidence = " / ".join(chapter.evidence[:3])
        chapter_cards.append(
            f"""
<article class="chapter-row {'black-feature' if index == 2 else ''}">
  <div class="chapter-number">0{index}</div>
  <div>
    <div class="mono-label">Chapter {index} / {chapter.date_range}</div>
    <h2>{_safe(chapter.hook)}</h2>
    <div class="theme-line">{_safe(chapter.title)}</div>
    <p>{_safe(chapter.paragraphs[0])}</p>
    <div class="best-move"><span>Your move</span><strong>{_safe(chapter.action)}</strong></div>
    <div class="evidence-line">Evidence / {_safe(evidence)}</div>
  </div>
</article>
"""
        )
    page3_body = f"""
<div class="eyebrow">Timing / three chapters</div>
<h1 class="section-title">The month moves in four acts</h1>
<div class="hero-rule"></div>
<div class="chapter-list">{''.join(chapter_cards)}</div>
"""

    # Page 4 - strong asymmetric homepage layout.
    love = _card(
        "Love and relationships",
        narrative.love_hook,
        narrative.love_story[0] if narrative.love_story else "",
        _clean_best_move(narrative.love_story),
        dark=True,
    )
    work = _card(
        "Work and direction",
        narrative.work_hook,
        narrative.work_story[0] if narrative.work_story else "",
        _clean_best_move(narrative.work_story),
    )
    money = _card(
        "Money and security",
        narrative.money_hook,
        narrative.money_story[0] if narrative.money_story else "",
        _clean_best_move(narrative.money_story),
    )
    page4_body = f"""
<div class="eyebrow">Real life / consequence first</div>
<h1 class="section-title">Love, work and money</h1>
<div class="life-grid">
  <div class="life-primary">{love}</div>
  <div class="life-secondary">{work}{money}</div>
</div>
"""

    # Page 5 - practical direction and key dates.
    actions = "".join(
        f'<div class="action-row"><span>0{index}</span><strong>{_safe(action)}</strong></div>'
        for index, action in enumerate(narrative.action_plan, 1)
    )
    date_cards = "".join(
        f"""
<article class="date-card">
  <div class="mono-label">{_safe(item.date_label)}</div>
  <h3>{_safe(item.evidence)}</h3>
  <p>{_safe(item.consequence)}</p>
  <div class="best-move"><span>Your move</span><strong>{_safe(item.response)}</strong></div>
</article>
"""
        for item in narrative.key_dates[:6]
    )
    extra = narrative.key_dates[6] if len(narrative.key_dates) > 6 else None
    extra_html = (
        f'<div class="also-watch"><span>Also watch { _safe(extra.date_label) } / { _safe(extra.evidence) }</span><strong>{ _safe(extra.response) }</strong></div>'
        if extra else ""
    )
    page5_body = f"""
<div class="section-hero two-column strategy-hero">
  <section>
    <div class="eyebrow">Practical direction / your next move</div>
    <h1 class="section-title">Make one opening real</h1>
    <div class="best-move wide"><span>Hidden opportunity</span><strong>{_safe(narrative.hidden_opportunity)}</strong></div>
  </section>
  <aside class="reading-card">
    <div class="daily-kicker">Watch out</div>
    <div class="mini-headline">{_safe(narrative.watch_out)}</div>
  </aside>
</div>
<div class="action-strip">{actions}</div>
<h2 class="subsection-title">Key dates</h2>
<div class="date-grid">{date_cards}</div>
{extra_html}
"""

    # Page 6 - solar convergence in the same left/right homepage hero.
    solar_rows = "".join(
        f'<div class="trust-item"><b>{_safe(label)}</b><br>{_safe(value)}</div>'
        for label, value in narrative.solar_rows
    )
    page6_body = f"""
<div class="section-hero two-column solar-hero">
  <section>
    <div class="eyebrow">Solar convergence / local light</div>
    <h1 class="section-title">The month beneath the month</h1>
    <div class="forecast-copy">
      <p>{_safe(narrative.solar_paragraphs[0] if narrative.solar_paragraphs else '')}</p>
      <p>{_safe(narrative.solar_paragraphs[1] if len(narrative.solar_paragraphs) > 1 else '')}</p>
    </div>
  </section>
  <aside class="reading-card">
    <div class="daily-kicker">Your Solar Convergence</div>
    <div class="daily-headline small">{_safe(narrative.solar_title)}</div>
    <p class="muted-white">{_safe(narrative.solar_rule)}</p>
  </aside>
</div>
<div class="trust-strip solar-strip">{solar_rows}</div>
<div class="three-card-grid">
  {_card('Opportunity', 'Bring the developed work into view', narrative.solar_opportunity)}
  {_card('Risk', 'Do not announce the destination too early', narrative.solar_risk, dark=True)}
  {_card('Strategic response', 'Visibility must become dependable', narrative.solar_action)}
</div>
<div class="equation"><span>Why Luna reached this conclusion</span><strong>{_safe(narrative.solar_equation)}</strong></div>
"""

    # Page 7 - evidence cards use homepage's "Why this is different" layout.
    snapshot_cards = "".join(
        f'<article class="card evidence-card"><div class="mono-label">{_safe(label)}</div><h3>{_safe(value)}</h3></article>'
        for label, value in narrative.snapshot_rows
    )
    page7_body = f"""
<div class="eyebrow">Explainable evidence / story first</div>
<h1 class="section-title">Why this month feels different</h1>
<p class="hero-subtitle narrow">The story comes first. These cards preserve the calculation without making the customer read a spreadsheet before receiving the meaning.</p>
<div class="evidence-grid">{snapshot_cards}</div>
<div class="best-move wide"><span>How to read the score</span><strong>The concentration score measures how strongly one internal astrological pattern dominates the month. It is not the probability that a predicted event will occur.</strong></div>
"""

    # Page 8 - technical evidence, using the same typography and thin table system.
    solar = result.get("solar_convergence") or {}
    solar_table_rows = [
        ("Tropical Sun", f"{solar.get('solar_longitude', 'n/a')} deg {solar.get('solar_sign', '')}"),
        ("Solar quarter", str(solar.get("solar_quarter", "n/a"))),
        ("Local light", f"{solar.get('light_direction', 'n/a')} from {solar.get('city', 'timezone estimate')}"),
        ("Activated house", f"{solar.get('activated_house', 'n/a')} - {solar.get('activated_house_name', '')}"),
        ("Next solar gate", f"{solar.get('next_solar_gate', 'n/a')} - {solar.get('next_gate_date', '')}"),
        ("Location basis", str(solar.get("location_basis", "n/a"))),
    ]
    dominant_rows = [
        (str(index), str(item.get("house", "")), str(item.get("topic", "")), f"{float(item.get('weight', 0)):.1f}")
        for index, item in enumerate(result.get("dominant_houses") or [], 1)
    ]
    convergence_rows = []
    for item in result.get("convergences") or []:
        start = _date_label(item.get("start_date", ""))
        end = _date_label(item.get("end_date", ""))
        window = f"{start}-{end.split()[-1]}" if start.split()[0] == end.split()[0] else f"{start}-{end}"
        convergence_rows.append((window, str(item.get("label", "Convergence")), f"{float(item.get('score', 0)):.0f}/100", ", ".join(str(v) for v in item.get("dominant_houses") or [])))
    page8_body = f"""
<div class="eyebrow">For readers who want the calculation</div>
<h1 class="section-title">Technical appendix</h1>
<p class="hero-subtitle narrow">House numbers, event names and strength scores are the evidence trail. The main report translates them into timing, consequences and practical decisions.</p>
<h2 class="subsection-title">Solar Convergence evidence</h2>
{_table(('Evidence', 'Calculated value'), solar_table_rows)}
<h2 class="subsection-title">Dominant house evidence</h2>
{_table(('Rank', 'House', 'Customer life area', 'Weight'), dominant_rows)}
<h2 class="subsection-title">Convergence windows</h2>
{_table(('Window', 'Type', 'Strength', 'Houses'), convergence_rows)}
"""

    # Page 9 - transitions, climate and order trail.
    transition_rows = [
        (_date_label(item.get("event_date", "")), str(item.get("title", "Transition")), ", ".join(str(v) for v in item.get("houses") or []))
        for item in result.get("major_transitions") or []
    ]
    retro_rows = [
        (str(item.get("planet", "")), _date_label(item.get("retrograde_start", "")), _date_label(item.get("direct_date", "")), ", ".join(str(v) for v in item.get("houses") or []))
        for item in result.get("retrograde_cycles") or []
    ]
    order_html = f'<div class="order-reference"><span>Order reference</span><strong>{_safe(order_reference)}</strong></div>' if order_reference else ""
    page9_body = f"""
<div class="eyebrow">Calculation trail / transitions and climate</div>
<h1 class="section-title">What changed in the sky</h1>
<h2 class="subsection-title">Major transitions</h2>
{_table(('Date', 'Evidence', 'Houses'), transition_rows)}
<h2 class="subsection-title">Retrograde climate</h2>
{_table(('Planet', 'Retrograde', 'Direct', 'Houses'), retro_rows)}
<div class="method-grid">
  <div><div class="mono-label">Method</div><p>Tropical geocentric planetary positions are calculated with Swiss Ephemeris and interpreted using whole-sign houses.</p></div>
  <div><div class="mono-label">Reading boundary</div><p>Strength labels describe the concentration of the internal astrological pattern; they are not probabilities or guarantees of events.</p></div>
</div>
{order_html}
"""

    pages = [
        _page(page1_body, icon_uri, report_right, 1, "homepage-page"),
        _page(page2_body, icon_uri, report_right, 2),
        _page(page3_body, icon_uri, report_right, 3),
        _page(page4_body, icon_uri, report_right, 4),
        _page(page5_body, icon_uri, report_right, 5),
        _page(page6_body, icon_uri, report_right, 6),
        _page(page7_body, icon_uri, report_right, 7),
        _page(page8_body, icon_uri, report_right, 8),
        _page(page9_body, icon_uri, report_right, 9),
    ]

    local_font_css = _font_face_css()
    font_loader = local_font_css or FONT_IMPORT
    css = f"""
{font_loader}
:root {{ --white:#fff; --black:#050505; --ink:#151515; --soft:#f5f5f2; --line:#d8d8d3; --muted:#696963; }}
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; background:#e9e9e6; color:var(--ink); font-family:'Josefin Sans','Avenir Next','Century Gothic',Arial,sans-serif; }}
body {{ print-color-adjust:exact; -webkit-print-color-adjust:exact; }}
.page {{ width:210mm; height:297mm; position:relative; overflow:hidden; background:var(--white); padding:13mm 16mm 14mm; break-after:page; page-break-after:always; }}
.page:last-child {{ break-after:auto; page-break-after:auto; }}
.page-content {{ position:relative; z-index:1; }}
.brand-row {{ display:flex; align-items:center; justify-content:space-between; min-height:10mm; padding:0 0 3mm; }}
.brand-lockup {{ display:flex; align-items:center; gap:2.7mm; }}
.brand-icon {{ width:7mm; height:7mm; object-fit:contain; }}
.brand-icon.fallback {{ display:grid; place-items:center; background:var(--black); color:white; font:500 6pt 'IBM Plex Mono'; }}
.brand-name {{ font:600 8.7pt 'Josefin Sans'; letter-spacing:.17em; text-transform:uppercase; white-space:nowrap; }}
.brand-note {{ font:500 4.7pt 'IBM Plex Mono'; letter-spacing:.04em; text-transform:uppercase; opacity:.68; }}
.top-nav {{ height:8mm; display:flex; align-items:center; gap:5.1mm; border-top:.35pt solid var(--black); border-bottom:.35pt solid var(--black); font:500 4.6pt 'IBM Plex Mono'; text-transform:uppercase; white-space:nowrap; }}
.top-nav span::before {{ content:'○'; margin-right:1.1mm; font-size:4pt; }}
.top-nav span.active::before, .top-nav span.active-report::before {{ content:'●'; }}
.report-meta-top {{ position:absolute; right:16mm; top:24mm; font:500 4.5pt 'IBM Plex Mono'; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); }}
.page-footer {{ position:absolute; left:16mm; right:16mm; bottom:6.2mm; display:flex; justify-content:space-between; border-top:.3pt solid var(--line); padding-top:2.2mm; font:400 5pt 'IBM Plex Mono'; color:var(--muted); }}
.eyebrow, .mono-label {{ font:500 5.5pt 'IBM Plex Mono'; letter-spacing:.055em; text-transform:uppercase; color:var(--black); }}
h1, h2, h3 {{ margin:0; color:var(--black); font-family:'Bodoni Moda','Libre Bodoni',Didot,Georgia,serif; font-optical-sizing:auto; font-weight:500; letter-spacing:-.035em; }}
.editorial-title {{ margin:2.2mm 0 5mm; font-size:40pt; line-height:.91; letter-spacing:-.045em; }}
.section-title {{ margin:2.2mm 0 4.8mm; font-size:31pt; line-height:.95; letter-spacing:-.045em; }}
.subsection-title {{ margin:5mm 0 2.6mm; font-size:18pt; line-height:1; }}
h2 {{ font-size:19pt; line-height:1.04; }}
h3 {{ font-size:13.5pt; line-height:1.08; }}
p {{ margin:0 0 3.2mm; font:400 8.2pt/1.48 'Josefin Sans'; }}
.hero-subtitle {{ max-width:116mm; font:300 10.2pt/1.45 'Josefin Sans'; }}
.hero-subtitle.narrow {{ max-width:158mm; }}
.hero-rule {{ border-top:.5pt solid var(--black); margin:5mm 0 5.2mm; }}
.hero-grid, .two-column {{ display:grid; grid-template-columns:1.2fr .8fr; gap:9mm; align-items:start; }}
.home-hero {{ margin-top:12mm; }}
.reading-card {{ position:relative; overflow:hidden; background:var(--black); color:var(--white); border:.5pt solid var(--black); padding:8mm 7mm; min-height:98mm; }}
.reading-card::after {{ content:''; position:absolute; width:42mm; height:42mm; border:.4pt solid rgba(255,255,255,.34); transform:rotate(30deg); right:-19mm; bottom:-22mm; }}
.reading-card * {{ position:relative; z-index:1; }}
.daily-kicker {{ font:500 5pt 'IBM Plex Mono'; letter-spacing:.04em; text-transform:uppercase; color:rgba(255,255,255,.78); }}
.daily-headline {{ margin:4mm 0 4mm; font:500 26pt/.94 'Bodoni Moda','Libre Bodoni',Didot,Georgia,serif; letter-spacing:-.045em; color:white; }}
.daily-headline.small {{ font-size:21pt; }}
.mini-headline {{ margin:3mm 0; font:500 19pt/1.02 'Bodoni Moda','Libre Bodoni',Didot,Georgia,serif; color:white; }}
.muted-white {{ color:rgba(255,255,255,.79); font-size:7.7pt; line-height:1.5; }}
.muted-white.compact {{ font-size:7.1pt; }}
.daily-date {{ position:absolute !important; bottom:7mm; left:7mm; right:7mm; font:500 4.9pt 'IBM Plex Mono'; text-transform:uppercase; color:rgba(255,255,255,.72); }}
.form-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:2.5mm; }}
.field {{ background:var(--soft); border:.35pt solid transparent; padding:2.8mm 3mm; }}
.field span {{ display:block; margin-bottom:1mm; font:500 4.4pt 'IBM Plex Mono'; letter-spacing:.05em; text-transform:uppercase; }}
.field strong {{ font:500 7pt 'Josefin Sans'; }}
.trust-strip {{ display:grid; grid-template-columns:repeat(4,1fr); margin-top:6mm; border-top:.45pt solid var(--black); border-left:.45pt solid var(--black); }}
.trust-strip.two {{ grid-template-columns:1fr 1fr; margin-top:5mm; }}
.trust-strip.solar-strip {{ grid-template-columns:repeat(3,1fr); }}
.trust-item {{ min-height:10mm; border-right:.45pt solid var(--black); border-bottom:.45pt solid var(--black); padding:2.5mm; font:500 4.6pt/1.4 'IBM Plex Mono'; text-transform:uppercase; }}
.trust-item b {{ font-weight:600; }}
.homepage-band {{ margin-top:10mm; display:grid; grid-template-columns:.8fr 1.2fr; align-items:end; gap:8mm; border-top:.45pt solid var(--black); padding-top:5mm; }}
.homepage-band h2 {{ font-size:22pt; }}
.homepage-band p {{ margin:0; }}
.section-hero {{ margin-top:12mm; }}
.forecast-copy p {{ font-size:9.4pt; line-height:1.58; font-weight:300; }}
.do-card {{ min-height:107mm; display:flex; flex-direction:column; justify-content:center; }}
.rule-white {{ border-top:.45pt solid rgba(255,255,255,.35); margin:8mm 0; }}
.best-move {{ margin-top:3.5mm; border-top:.45pt solid currentColor; border-bottom:.45pt solid currentColor; padding:3.4mm 0; display:grid; grid-template-columns:24mm 1fr; gap:4mm; }}
.best-move span {{ font:500 4.8pt 'IBM Plex Mono'; text-transform:uppercase; }}
.best-move strong {{ font:500 8.2pt/1.4 'Josefin Sans'; }}
.best-move.wide {{ margin-top:7mm; grid-template-columns:36mm 1fr; }}
.best-move.wide strong p {{ margin:0 0 2mm; }}
.chapter-list {{ display:grid; gap:4mm; }}
.chapter-row {{ display:grid; grid-template-columns:14mm 1fr; gap:5mm; border:.45pt solid var(--black); padding:4.5mm 5mm; min-height:55mm; }}
.chapter-row.black-feature {{ background:var(--black); color:white; }}
.chapter-row.black-feature h2, .chapter-row.black-feature .mono-label, .chapter-row.black-feature .theme-line, .chapter-row.black-feature p, .chapter-row.black-feature .evidence-line {{ color:white; }}
.chapter-number {{ font:400 23pt 'Bodoni Moda','Libre Bodoni',serif; }}
.chapter-row h2 {{ margin:1.6mm 0 1.4mm; font-size:17pt; }}
.theme-line {{ font:400 7.4pt 'Josefin Sans'; color:var(--muted); }}
.chapter-row p {{ margin-top:3mm; font-size:7.7pt; line-height:1.45; }}
.evidence-line {{ margin-top:2.5mm; font:400 4.8pt/1.4 'IBM Plex Mono'; text-transform:uppercase; }}
.life-grid {{ display:grid; grid-template-columns:1.05fr .95fr; gap:5mm; margin-top:6mm; }}
.life-secondary {{ display:grid; gap:5mm; }}
.card {{ background:white; border:.45pt solid var(--black); padding:5.3mm; }}
.card h3 {{ margin:3mm 0; }}
.card p {{ font-size:7.8pt; line-height:1.5; }}
.dark-card {{ background:var(--black); color:white; }}
.dark-card h3, .dark-card .mono-label, .dark-card p {{ color:white; }}
.life-primary .card {{ min-height:177mm; display:flex; flex-direction:column; justify-content:center; }}
.life-secondary .card {{ min-height:86mm; }}
.strategy-hero .reading-card {{ min-height:77mm; }}
.action-strip {{ display:grid; grid-template-columns:repeat(3,1fr); border-top:.45pt solid var(--black); border-left:.45pt solid var(--black); margin-top:6mm; }}
.action-row {{ border-right:.45pt solid var(--black); border-bottom:.45pt solid var(--black); padding:3.3mm; min-height:24mm; display:grid; grid-template-columns:8mm 1fr; gap:2mm; }}
.action-row span {{ font:500 12pt 'Bodoni Moda','Libre Bodoni',serif; }}
.action-row strong {{ font:500 6.8pt/1.4 'Josefin Sans'; }}
.date-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; }}
.date-card {{ background:var(--soft); border:.35pt solid var(--line); padding:3.5mm; min-height:49mm; }}
.date-card h3 {{ margin:2mm 0; font-size:11.3pt; }}
.date-card p {{ font-size:6.6pt; line-height:1.38; }}
.date-card .best-move {{ grid-template-columns:18mm 1fr; padding:2mm 0; margin-top:2mm; }}
.date-card .best-move strong {{ font-size:6.2pt; }}
.also-watch {{ margin-top:3mm; border:.45pt solid var(--black); padding:3.5mm; display:grid; grid-template-columns:63mm 1fr; gap:4mm; }}
.also-watch span {{ font:500 4.8pt 'IBM Plex Mono'; text-transform:uppercase; }}
.also-watch strong {{ font:600 7pt 'Josefin Sans'; }}
.solar-hero .reading-card {{ min-height:87mm; }}
.three-card-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin-top:5mm; }}
.three-card-grid .card {{ min-height:50mm; }}
.equation {{ margin-top:4mm; border-top:.45pt solid var(--black); border-bottom:.45pt solid var(--black); padding:3mm 0; display:grid; grid-template-columns:47mm 1fr; gap:4mm; }}
.equation span {{ font:500 4.8pt 'IBM Plex Mono'; text-transform:uppercase; }}
.equation strong {{ font:500 6.9pt/1.4 'Josefin Sans'; }}
.evidence-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin-top:7mm; }}
.evidence-card {{ min-height:36mm; }}
.evidence-card h3 {{ margin-top:3mm; font-size:11.5pt; }}
.table-wrap {{ width:100%; }}
table {{ width:100%; border-collapse:collapse; table-layout:fixed; font:400 6.4pt/1.35 'Josefin Sans'; }}
th, td {{ border:.35pt solid #999994; padding:2.3mm; text-align:left; vertical-align:top; overflow-wrap:anywhere; }}
th {{ background:var(--soft); font:600 4.8pt 'IBM Plex Mono'; text-transform:uppercase; }}
.method-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:5mm; margin-top:6mm; }}
.method-grid > div {{ border-top:.45pt solid var(--black); padding-top:3mm; }}
.method-grid p {{ font-size:7.5pt; }}
.order-reference {{ margin-top:6mm; border:.45pt solid var(--black); padding:4mm; }}
.order-reference span {{ display:block; margin-bottom:2mm; font:500 4.8pt 'IBM Plex Mono'; text-transform:uppercase; }}
.order-reference strong {{ font:400 5.4pt/1.4 'IBM Plex Mono'; overflow-wrap:anywhere; }}
"""

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{_safe(BRAND)} - {_safe(narrative.sign)} {_safe(narrative.label)}</title><style>{css}</style></head>
<body>{''.join(pages)}<script>document.fonts.ready.then(function(){{document.documentElement.dataset.fonts='ready';}});</script></body></html>"""


def _find_browser() -> str | None:
    configured = os.environ.get("LUNA_PDF_BROWSER", "").strip()
    candidates = [configured] if configured else []
    candidates.extend([
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("google-chrome") or "",
        shutil.which("google-chrome-stable") or "",
        shutil.which("chrome") or "",
        shutil.which("msedge") or "",
    ])
    if os.name == "nt":
        roots = [
            os.environ.get("PROGRAMFILES", ""),
            os.environ.get("PROGRAMFILES(X86)", ""),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for root in roots:
            if not root:
                continue
            candidates.extend([
                str(Path(root) / "Google/Chrome/Application/chrome.exe"),
                str(Path(root) / "Microsoft/Edge/Application/msedge.exe"),
            ])
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    return None


def build_monthly_homepage_pdf(
    result: dict,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> bytes:
    """Render a monthly report with the Luna homepage's visual system.

    Chrome/Edge prints the same HTML/CSS font stack and layout language used by
    the public site. If no supported browser is available, Luna falls back to the
    stable ReportLab Editorial v2 generator rather than failing an order.
    """
    narrative = build_monthly_narrative(
        result,
        main_focus=main_focus,
        personal_question=normalise_personal_question(personal_question),
        order_reference=order_reference,
    )
    icon_uri = _asset_data_uri(Path(__file__).parent / "assets" / "saturn_hex_brand.png")
    html = _render_html(result, narrative, order_reference, icon_uri)

    # Prefer a native HTML/CSS print engine when available. WeasyPrint is used
    # by the Linux build environment; Windows installations can use Chrome or
    # Edge without adding a Python dependency.
    try:
        from weasyprint import HTML

        rendered = HTML(string=html, base_url=str(Path(__file__).parent)).write_pdf()
        if rendered.startswith(b"%PDF") and len(rendered) > 10_000:
            return rendered
    except Exception:
        pass

    browser = _find_browser()
    if not browser:
        return build_monthly_editorial_pdf(
            result,
            main_focus=main_focus,
            personal_question=personal_question,
            order_reference=order_reference,
        )

    with tempfile.TemporaryDirectory(prefix="luna-home-report-") as temporary:
        work = Path(temporary)
        html_path = work / "report.html"
        pdf_path = work / "report.pdf"
        profile_path = work / "browser-profile"
        html_path.write_text(html, encoding="utf-8")

        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=7000",
            f"--user-data-dir={profile_path}",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ]
        if os.name != "nt":
            command.insert(1, "--no-sandbox")
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=45,
                creationflags=creationflags,
            )
        except (subprocess.TimeoutExpired, OSError):
            completed = None
        if completed is not None and completed.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 10_000:
            return pdf_path.read_bytes()

    return build_monthly_editorial_pdf(
        result,
        main_focus=main_focus,
        personal_question=personal_question,
        order_reference=order_reference,
    )


def build_monthly_homepage_html(
    result: dict,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> str:
    narrative = build_monthly_narrative(
        result,
        main_focus=main_focus,
        personal_question=normalise_personal_question(personal_question),
        order_reference=order_reference,
    )
    icon_uri = _asset_data_uri(Path(__file__).parent / "assets" / "saturn_hex_brand.png")
    return _render_html(result, narrative, order_reference, icon_uri)
