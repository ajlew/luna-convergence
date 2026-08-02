from __future__ import annotations

from html import escape
from typing import Iterable

from date_display import human_date, human_date_range
from luna_editorial_system import (
    DO_LABEL,
    DONT_LABEL,
    FOOTER_DISCLAIMER,
    GATEKEEPER_LINE,
    LUNA_SAYS_LABEL,
    SOLAR_LABEL,
    TECHNICAL_LABEL,
    TIMING_LABEL,
    VALIDATION_LINE,
    WHY_LUNA_LABEL,
    YOUR_MOVE_LABEL,
)
from monthly_narrative_v1 import MonthlyNarrative
from luna_voice import narrator_cue


PRINT_PAPERS = ("A4", "A3")
PRINT_ORIENTATIONS = ("portrait", "landscape")


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _paragraphs(values: Iterable[str], maximum: int | None = None) -> str:
    selected = list(values)
    if maximum is not None:
        selected = selected[:maximum]
    return "".join(f"<p>{_safe(value)}</p>" for value in selected if value)


def _key_date_cards(narrative: MonthlyNarrative) -> str:
    return "".join(
        f"""
<article class="luna-date-card">
  <span>{_safe(item.date_label)}</span>
  <strong>{_safe(item.consequence)}</strong>
  <p>{_safe(item.response)}</p>
  <small>{_safe(item.evidence)}</small>
</article>
        """
        for item in narrative.key_dates
    )


def _story_date_cards(narrative: MonthlyNarrative) -> str:
    dates = list(narrative.key_dates)
    if not dates:
        return ""

    if len(dates) <= 4:
        selected = dates
    else:
        indexes = (0, len(dates) // 2, max(len(dates) - 2, 0), len(dates) - 1)
        selected = []
        for index in indexes:
            item = dates[index]
            if item not in selected:
                selected.append(item)

    return "".join(
        f"""
<article class="luna-story-date-card">
  <span>{_safe(item.date_label)}</span>
  <strong>{_safe(item.response)}</strong>
  <p>{_safe(item.evidence)}</p>
</article>
        """
        for item in selected
    )


def _technical_rows(result: dict) -> str:
    rows = []
    for item in (result.get("dominant_houses") or [])[:6]:
        rows.append(
            "<tr>"
            f"<td>House {_safe(item.get('house'))}</td>"
            f"<td>{_safe(item.get('topic'))}</td>"
            f"<td>{float(item.get('weight', 0.0)):.1f}</td>"
            "</tr>"
        )
    return "".join(rows)


def _transition_rows(result: dict) -> str:
    rows = []
    for item in (result.get("major_transitions") or [])[:12]:
        rows.append(
            "<tr>"
            f"<td>{_safe(human_date(item.get('event_date')))}</td>"
            f"<td>{_safe(item.get('title'))}</td>"
            f"<td>{_safe(', '.join(map(str, item.get('houses') or [])))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _retrograde_rows(result: dict) -> str:
    rows = []
    for item in (result.get("retrograde_cycles") or [])[:8]:
        rows.append(
            "<tr>"
            f"<td>{_safe(item.get('planet'))}</td>"
            f"<td>{_safe(human_date(item.get('retrograde_start')))}</td>"
            f"<td>{_safe(human_date(item.get('direct_date')))}</td>"
            f"<td>{_safe(', '.join(map(str, item.get('houses') or [])))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _arc_evidence_path(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    beats = {
        str(item.get("role", "")).lower(): item
        for item in (arc.get("beats") or [])
    }

    beginning = beats.get("inherited state") or beats.get("inciting event")
    middle = beats.get("complication") or beats.get("pivot")
    relationship = beats.get("relationship test")
    ending_items = [
        item
        for key in ("pivot", "climax", "resolution")
        if (item := beats.get(key)) is not None
    ]

    anchors: list[tuple[str, str, str]] = []
    if beginning:
        anchors.append((
            "Starting condition",
            human_date_range(
                beginning.get("start_date"),
                beginning.get("end_date", beginning.get("start_date")),
            ),
            str(beginning.get("title", "Carryover trigger")),
        ))
    if middle:
        anchors.append((
            "Midmonth test",
            human_date_range(
                middle.get("start_date"),
                middle.get("end_date", middle.get("start_date")),
            ),
            str(middle.get("title", "Turning point")),
        ))
    if relationship:
        anchors.append((
            "Relationship test",
            human_date_range(
                relationship.get("start_date"),
                relationship.get("end_date", relationship.get("start_date")),
            ),
            str(relationship.get("title", "Attention meets standards")),
        ))
    if ending_items:
        first = ending_items[0]
        last = ending_items[-1]
        titles = []
        for item in ending_items:
            title = str(item.get("title", "")).strip()
            if title and title not in titles:
                titles.append(title)
        anchors.append((
            "Release and result",
            human_date_range(
                first.get("start_date"),
                last.get("end_date", last.get("start_date")),
            ),
            ", ".join(titles),
        ))

    return "".join(
        f"""
<div class="luna-evidence-anchor">
  <span>{_safe(label)}</span>
  <strong>{_safe(window)}</strong>
  <p>{_safe(title)}</p>
</div>
        """
        for label, window, title in anchors
    )

def _scenario_rows_html(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    rows = []
    for item in (arc.get("ranked_scenarios") or [])[:8]:
        examples = "; ".join(str(value) for value in (item.get("examples") or [])[:2])
        rows.append(
            "<tr>"
            f"<td>{_safe(item.get('label'))}</td>"
            f"<td>{_safe(item.get('confidence'))}</td>"
            f"<td>{_safe(examples)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _carryover_rows_html(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    rows = []
    for item in arc.get("inherited_events") or []:
        rows.append(
            "<tr>"
            f"<td>{_safe(human_date(item.get('event_date')))}</td>"
            f"<td>{_safe(item.get('title'))}</td>"
            f"<td>{_safe(', '.join(map(str, item.get('houses') or [])))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _chapter_cards(narrative: MonthlyNarrative) -> str:
    acts = []
    for chapter in narrative.chapters:
        acts.append(
            f"""
<article class="luna-story-act">
  <div class="luna-story-date">
    <span>{_safe(chapter.date_range)}</span>
    <small>{_safe(chapter.title)}</small>
  </div>
  <div class="luna-story-copy">
    <h3>{_safe(chapter.hook)}</h3>
    {_paragraphs(chapter.paragraphs)}
  </div>
</article>
            """
        )
    return "".join(acts)


def _life_rows(narrative: MonthlyNarrative) -> str:
    sections = (
        ("Love", narrative.love_hook, narrative.love_story[0]),
        ("Work", narrative.work_hook, narrative.work_story[0]),
        ("Money", narrative.money_hook, narrative.money_story[0]),
    )
    return "".join(
        f"""
<article class="luna-life-row">
  <span>{_safe(label)}</span>
  <h3>{_safe(hook)}</h3>
  <p>{_safe(copy)}</p>
</article>
        """
        for label, hook, copy in sections
    )


def _print_controls(
    default_paper: str,
    default_orientation: str,
) -> str:
    paper_options = "".join(
        f'<option value="{paper}"'
        + (" selected" if paper == default_paper else "")
        + f">{paper}</option>"
        for paper in PRINT_PAPERS
    )
    orientation_options = "".join(
        f'<option value="{orientation}"'
        + (" selected" if orientation == default_orientation else "")
        + f">{orientation.title()}</option>"
        for orientation in PRINT_ORIENTATIONS
    )
    return f"""
<div class="luna-print-controls">
  <div class="luna-print-field">
    <label for="luna-print-paper">Paper</label>
    <select id="luna-print-paper">{paper_options}</select>
  </div>
  <div class="luna-print-field">
    <label for="luna-print-orientation">Orientation</label>
    <select id="luna-print-orientation">{orientation_options}</select>
  </div>
  <button id="luna-print-report" type="button">Print or save report</button>
</div>
    """


def build_monthly_experience_html(
    narrative: MonthlyNarrative,
    result: dict,
    *,
    show_print: bool = True,
    preview: bool = False,
    order_reference: str = "",
    default_paper: str = "A4",
    default_orientation: str = "portrait",
) -> str:
    if default_paper not in PRINT_PAPERS:
        raise ValueError(f"Unsupported paper: {default_paper}")
    if default_orientation not in PRINT_ORIENTATIONS:
        raise ValueError(f"Unsupported orientation: {default_orientation}")

    chapters = _chapter_cards(narrative)
    life_rows = _life_rows(narrative)
    story_dates = _story_date_cards(narrative)
    arc_evidence_path = _arc_evidence_path(result)
    scenario_rows = _scenario_rows_html(result)
    carryover_rows = _carryover_rows_html(result)

    focus_section = ""
    if (
        narrative.main_focus != "General overview"
        or narrative.personal_question
    ):
        question_html = (
            f'<blockquote class="luna-question">{_safe(narrative.personal_question)}</blockquote>'
            if narrative.personal_question
            else ""
        )
        focus_section = f"""
<section class="luna-monthly-section luna-focus-section">
  <div class="luna-eyebrow">{_safe(narrative.focus_title)}</div>
  {question_html}
  {_paragraphs(narrative.focus_answer, maximum=2)}
</section>
        """

    evidence = f"""
<section class="luna-evidence-stack">
  <details>
    <summary>{_safe(WHY_LUNA_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <p>{_safe(narrative.central_storyline)}</p>
      <p><strong>Theme:</strong> {_safe(narrative.headline)}</p>
      <p><strong>Convergence:</strong> {_safe(narrative.convergence_axis)}</p>
      <h3>Evidence path</h3>
      <div class="luna-evidence-path">{arc_evidence_path}</div>
      <p><strong>Rule:</strong> {_safe(VALIDATION_LINE)}</p>
    </div>
  </details>

  <details>
    <summary>{_safe(SOLAR_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <h3>{_safe(narrative.solar_title)}</h3>
      {_paragraphs(narrative.solar_paragraphs, maximum=2)}
      <div class="luna-evidence-grid">
        {''.join(
            f'<div><span>{_safe(label)}</span><strong>{_safe(value)}</strong></div>'
            for label, value in narrative.solar_rows
        )}
      </div>
      <p><strong>Opportunity:</strong> {_safe(narrative.solar_opportunity)}</p>
      <p><strong>Risk:</strong> {_safe(narrative.solar_risk)}</p>
      <p><strong>Response:</strong> {_safe(narrative.solar_action)}</p>
    </div>
  </details>

  <details>
    <summary>{_safe(TIMING_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <div class="luna-date-grid">{_key_date_cards(narrative)}</div>
    </div>
  </details>

  <details>
    <summary>{_safe(TECHNICAL_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <h3>Carryover evidence</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Evidence</th><th>Houses</th></tr></thead>
          <tbody>{carryover_rows}</tbody>
        </table>
      </div>
      <h3>Ranked scenario families</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Event family</th><th>Support level</th><th>Possible manifestations</th></tr></thead>
          <tbody>{scenario_rows}</tbody>
        </table>
      </div>
      <p class="luna-method-note">These are ranked symbolic event families, not measured probabilities or guarantees.</p>
      <h3>Dominant houses</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>House</th><th>Life area</th><th>Weight</th></tr></thead>
          <tbody>{_technical_rows(result)}</tbody>
        </table>
      </div>
      <h3>Major transitions</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Evidence</th><th>Houses</th></tr></thead>
          <tbody>{_transition_rows(result)}</tbody>
        </table>
      </div>
      <h3>Retrograde climate</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Planet</th><th>Retrograde</th><th>Direct</th><th>Houses</th></tr></thead>
          <tbody>{_retrograde_rows(result)}</tbody>
        </table>
      </div>
      {f'<p><strong>Order reference:</strong> {_safe(order_reference)}</p>' if order_reference else ''}
    </div>
  </details>
</section>
    """

    body = ""
    if not preview:
        body = f"""
<section class="luna-monthly-section luna-opening-story">
  <div class="luna-eyebrow">{_safe(LUNA_SAYS_LABEL)}</div>
  <h2>{_safe(narrative.central_storyline)}</h2>
  <p class="luna-opening-rule">Read the month in sequence. The opening shows possibility; the terms reveal cost; the relationship test shows consistency; the ending decides what can fit your real life.</p>
  <div class="luna-do-dont luna-do-dont-light">
    <div><span>{_safe(DO_LABEL)}</span><strong>{_safe(narrative.do_line)}</strong></div>
    <div><span>{_safe(DONT_LABEL)}</span><strong>{_safe(narrative.dont_line)}</strong></div>
  </div>
</section>

{focus_section}

<section class="luna-monthly-section luna-story-section">
  <div class="luna-eyebrow">How {_safe(narrative.label.split()[0])} unfolds — four acts</div>
  <div class="luna-story-timeline">{chapters}</div>
</section>


<section class="luna-monthly-section luna-story-dates-section">
  <div class="luna-eyebrow">Decision calendar</div>
  <h2>What to do when the story moves</h2>
  <div class="luna-story-date-grid">{story_dates}</div>
</section>

<section class="luna-monthly-section luna-romance-section">
  <div class="luna-eyebrow">Romance and validation</div>
  <h2>Whether the spark arrives—or the room stays quiet</h2>
  <div class="luna-romance-grid">
    <article>
      <span>When romance is active</span>
      <p>{_safe(narrative.romance_active)}</p>
    </article>
    <article>
      <span>When romance is quiet</span>
      <p>{_safe(narrative.romance_quiet)}</p>
    </article>
  </div>
</section>

<section class="luna-monthly-section">
  <div class="luna-eyebrow">Where the story lands</div>
  <div class="luna-life-list">{life_rows}</div>
</section>

<section class="luna-monthly-section luna-next-move">
  <div>
    <div class="luna-eyebrow">{_safe(YOUR_MOVE_LABEL)}</div>
    <h2>{_safe(GATEKEEPER_LINE)}</h2>
  </div>
  <ol>
    {''.join(f'<li>{_safe(action)}</li>' for action in narrative.action_plan)}
  </ol>
</section>

{evidence}
        """
    else:
        body = f"""
<section class="luna-monthly-section luna-opening-story">
  <div class="luna-eyebrow">{_safe(LUNA_SAYS_LABEL)}</div>
  <h2>{_safe(narrative.central_storyline)}</h2>
  {_paragraphs(narrative.luna_says, maximum=2)}
</section>
        """

    controls = (
        _print_controls(default_paper, default_orientation)
        if show_print
        else ""
    )

    return f"""
<style id="luna-print-page-size">
@page {{ size: {default_paper} {default_orientation}; margin: 12mm; }}
</style>
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&family=IBM+Plex+Mono:wght@400;500;600&family=Josefin+Sans:wght@300;400;500;600;700&display=swap');

.luna-monthly-report {{
  --black:#050505;
  --white:#fff;
  --soft:#f5f5f2;
  --line:#d8d8d3;
  --muted:#696963;
  width:100%;
  max-width:900px;
  margin:0 auto;
  color:var(--black);
  background:var(--white);
  font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif;
}}
.luna-monthly-report * {{ box-sizing:border-box; }}
.luna-monthly-report h1,
.luna-monthly-report h2,
.luna-monthly-report h3 {{
  font-family:"Bodoni MT","Bodoni 72","Bodoni Moda",Didot,Georgia,serif;
  font-weight:500;
  letter-spacing:-.035em;
}}
.luna-monthly-report p {{
  font-size:clamp(.98rem,1.35vw,1.12rem);
  line-height:1.58;
  margin:.4rem 0 .9rem;
}}
.luna-monthly-hero {{
  display:grid;
  gap:.85rem;
  min-height:0 !important;
  height:auto !important;
  max-height:none !important;
  padding:clamp(1.15rem,2.8vw,2rem);
  color:#fff !important;
  background:#050505 !important;
}}
.luna-monthly-meta {{
  display:flex;
  justify-content:space-between;
  gap:1rem;
  padding-bottom:.7rem;
  border-bottom:1px solid rgba(255,255,255,.28);
  color:#fff !important;
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.045em;
  text-transform:uppercase;
}}
.luna-monthly-hero h1 {{
  display:block !important;
  visibility:visible !important;
  opacity:1 !important;
  position:relative;
  z-index:2;
  max-width:760px;
  margin:.45rem 0 .3rem;
  color:#fff !important;
  font-size:clamp(2.45rem,5.5vw,4.45rem);
  line-height:.95;
}}
.luna-hero-theme {{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:.7rem;
  align-items:baseline;
  color:rgba(255,255,255,.78);
}}
.luna-hero-theme span,
.luna-says span,
.luna-eyebrow,
.luna-story-date span,
.luna-romance-grid span,
.luna-life-row > span {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.05em;
  text-transform:uppercase;
}}
.luna-hero-theme strong {{
  font-size:.95rem;
  font-weight:400;
  line-height:1.35;
}}
.luna-monthly-section {{
  padding:clamp(2.25rem,5vw,4.3rem) clamp(1rem,4vw,3.2rem);
  border-bottom:1px solid var(--black);
}}
.luna-opening-story h2 {{
  max-width:780px;
  margin:.45rem 0 1.35rem;
  font-size:clamp(2.25rem,5vw,4.45rem);
  line-height:.98;
}}
.luna-story-prose {{
  max-width:760px;
}}
.luna-opening-rule {{
  max-width:760px;
  margin:.25rem 0 1.35rem;
  color:var(--muted);
  font-size:clamp(1rem,1.4vw,1.14rem) !important;
  line-height:1.58 !important;
}}
.luna-story-prose p {{
  font-size:clamp(1.03rem,1.5vw,1.18rem);
  line-height:1.68;
}}
.luna-do-dont {{
  display:grid;
  grid-template-columns:1fr 1fr;
  margin-top:1.35rem;
}}
.luna-do-dont div {{
  padding:.9rem .9rem .15rem 0;
}}
.luna-do-dont div + div {{
  padding-left:.9rem;
}}
.luna-do-dont span {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
  margin-bottom:.28rem;
}}
.luna-do-dont strong {{
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.18rem,2vw,1.55rem);
  line-height:1.18;
}}
.luna-do-dont-light {{
  border-top:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-do-dont-light div + div {{
  border-left:1px solid var(--black);
}}
.luna-do-dont-light span {{
  color:var(--muted);
}}
.luna-story-timeline {{
  border-top:1px solid var(--black);
}}
.luna-story-act {{
  display:grid;
  grid-template-columns:minmax(7rem,.34fr) minmax(0,1fr);
  gap:clamp(1rem,4vw,3rem);
  padding:clamp(1.35rem,3vw,2.3rem) 0;
  border-bottom:1px solid var(--black);
}}
.luna-story-date {{
  display:flex;
  flex-direction:column;
  gap:.45rem;
}}
.luna-story-date small {{
  color:var(--muted);
  font-size:.85rem;
  line-height:1.4;
}}
.luna-story-copy {{
  max-width:700px;
}}
.luna-story-copy h3,
.luna-life-row h3 {{
  margin:0 0 .65rem;
  font-size:clamp(1.7rem,3vw,2.55rem);
  line-height:1.02;
}}
.luna-story-copy p {{
  margin:.35rem 0 .8rem;
  line-height:1.62;
}}
.luna-relationship-test {{
  background:var(--soft);
}}
.luna-relationship-test h2 {{
  max-width:760px;
  margin:.45rem 0 1rem;
  font-size:clamp(2.1rem,4.8vw,4rem);
  line-height:1;
}}
.luna-relationship-test p {{
  max-width:720px;
  font-size:clamp(1.02rem,1.45vw,1.16rem);
  line-height:1.62;
}}

.luna-story-dates-section h2 {{
  max-width:680px;
  margin:.45rem 0 1.35rem;
  font-size:clamp(2.1rem,4.5vw,3.8rem);
  line-height:.98;
}}
.luna-story-date-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-story-date-card {{
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-story-date-card span {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.05em;
  text-transform:uppercase;
  margin-bottom:.55rem;
}}
.luna-story-date-card strong {{
  display:block;
  font-size:1.02rem;
  line-height:1.38;
}}
.luna-story-date-card p {{
  margin:.65rem 0 0;
  color:var(--muted);
}}
.luna-focus-section {{
  background:var(--soft);
}}
.luna-focus-section p {{
  max-width:760px;
}}
.luna-question {{
  max-width:760px;
  margin:1rem 0 1.4rem;
  padding-left:1rem;
  border-left:3px solid var(--black);
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.35rem,2.4vw,2rem);
  line-height:1.22;
}}
.luna-romance-grid {{
  display:grid;
  grid-template-columns:1fr 1fr;
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-romance-grid article {{
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-life-list {{
  border-top:1px solid var(--black);
}}
.luna-life-row {{
  display:grid;
  grid-template-columns:5rem minmax(12rem,.75fr) 1.4fr;
  gap:1rem;
  align-items:start;
  padding:1rem 0;
  border-bottom:1px solid var(--black);
}}
.luna-life-row h3,
.luna-life-row p {{
  margin:0;
}}
.luna-next-move {{
  display:grid;
  grid-template-columns:.8fr 1.2fr;
  gap:2rem;
}}
.luna-next-move h2 {{
  margin:.4rem 0 0;
  font-size:clamp(2.2rem,5vw,4.2rem);
  line-height:.98;
}}
.luna-next-move ol {{
  margin:0;
  padding-left:1.25rem;
}}
.luna-next-move li {{
  margin-bottom:.8rem;
  font-size:1.03rem;
  line-height:1.48;
}}
.luna-evidence-path {{
  border-top:1px solid var(--black);
  margin:1rem 0 1.35rem;
}}
.luna-evidence-anchor {{
  display:grid;
  grid-template-columns:minmax(7.5rem,.55fr) minmax(8rem,.7fr) minmax(0,1.5fr);
  gap:1rem;
  align-items:baseline;
  padding:.8rem 0;
  border-bottom:1px solid var(--line);
}}
.luna-evidence-anchor span {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.62rem;
  text-transform:uppercase;
  color:var(--muted);
}}
.luna-evidence-anchor strong {{
  font-size:.9rem;
}}
.luna-evidence-anchor p {{
  margin:0;
  font-size:.95rem;
  line-height:1.4;
}}
.luna-method-note {{
  color:var(--muted);
  font-size:.82rem !important;
}}
.luna-evidence-stack details {{
  border-bottom:1px solid var(--black);
}}
.luna-evidence-stack summary {{
  list-style:none;
  display:flex;
  justify-content:space-between;
  align-items:center;
  min-height:3.8rem;
  cursor:pointer;
  padding:0 clamp(1rem,4vw,3.2rem);
  font-family:"IBM Plex Mono",monospace;
  font-size:.7rem;
  text-transform:uppercase;
}}
.luna-evidence-stack summary::-webkit-details-marker {{ display:none; }}
.luna-detail-body {{
  padding:.8rem clamp(1rem,4vw,3.2rem) 2.4rem;
}}
.luna-evidence-grid,
.luna-date-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-evidence-grid div,
.luna-date-card {{
  padding:.9rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-evidence-grid span,
.luna-date-card span,
.luna-date-card small {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
}}
.luna-date-card strong {{
  display:block;
  margin:.45rem 0;
}}
.luna-table-wrap {{ overflow-x:auto; margin-bottom:1.5rem; }}
.luna-monthly-report table {{
  width:100%;
  border-collapse:collapse;
}}
.luna-monthly-report th,
.luna-monthly-report td {{
  padding:.65rem .4rem;
  border-bottom:1px solid var(--line);
  text-align:left;
  vertical-align:top;
}}
.luna-monthly-report th {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
}}
.luna-report-footer {{
  padding:1.2rem clamp(1rem,4vw,3.2rem);
  color:var(--muted);
  font-size:.72rem;
  line-height:1.5;
  border-top:1px solid var(--line);
}}
.luna-print-controls {{
  position:static;
  z-index:1;
  display:flex;
  align-items:end;
  gap:.75rem;
  padding:.75rem;
  background:rgba(255,255,255,.97);
  border:1px solid var(--black);
}}
.luna-print-field {{
  display:flex;
  flex-direction:column;
  gap:.2rem;
}}
.luna-print-field label {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.6rem;
  text-transform:uppercase;
}}
.luna-print-field select {{
  min-height:2.5rem;
  border:1px solid var(--black);
  background:var(--white);
  padding:.4rem .55rem;
}}
.luna-print-check {{
  margin-left:auto;
  font-size:.85rem;
}}
.luna-print-controls button {{
  min-height:2.5rem;
  border:1px solid var(--black);
  background:var(--black);
  color:var(--white);
  padding:.55rem .8rem;
  font-family:"IBM Plex Mono",monospace;
  text-transform:uppercase;
  cursor:pointer;
}}
@media (max-width:720px) {{
  .luna-monthly-meta,
  .luna-hero-theme,
  .luna-do-dont,
  .luna-romance-grid,
  .luna-next-move,
  .luna-evidence-grid,
  .luna-date-grid,
  .luna-story-date-grid,
  .luna-story-act {{
    grid-template-columns:1fr;
    flex-direction:column;
  }}
  .luna-monthly-hero h1 {{
    font-size:clamp(2.35rem,11vw,3.75rem);
  }}
  .luna-hero-theme {{
    gap:.25rem;
  }}
  .luna-do-dont div + div {{
    border-left:none;
    border-top:1px solid var(--black);
    padding-left:0;
  }}
  .luna-story-act {{
    gap:.8rem;
  }}
  .luna-evidence-anchor {{
    grid-template-columns:1fr;
    gap:.25rem;
  }}
  .luna-story-date {{
    display:grid;
    grid-template-columns:auto 1fr;
    gap:.7rem;
    align-items:baseline;
  }}
  .luna-life-row {{
    grid-template-columns:1fr;
    gap:.35rem;
  }}
  .luna-print-controls {{
    align-items:stretch;
    flex-wrap:wrap;
  }}
  .luna-print-controls button {{
    width:100%;
  }}
}}
#luna-print-portal {{
  display:none;
}}
@media print {{
  body.luna-print-active > *:not(#luna-print-portal):not(style):not(script) {{
    display:none !important;
  }}
  #luna-print-portal {{
    display:block !important;
    position:static !important;
    width:100% !important;
    max-width:none !important;
    margin:0 !important;
    padding:0 !important;
  }}
  #luna-print-portal .luna-monthly-report {{
    display:block !important;
    position:static !important;
    width:100% !important;
    max-width:none !important;
    height:auto !important;
    max-height:none !important;
    overflow:visible !important;
    margin:0 !important;
  }}
  html, body {{
    margin:0 !important;
    padding:0 !important;
    background:#fff !important;
  }}
  .luna-monthly-report {{
    position:static !important;
    width:100%;
    max-width:none;
    margin:0;
  }}
  .luna-print-controls {{ display:none !important; }}
  .luna-monthly-hero {{
    padding:7mm 0 6mm;
    color:#050505 !important;
    background:#fff !important;
    border-top:3mm solid #050505;
    border-bottom:1px solid #050505;
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-meta {{
    color:#050505 !important;
    border-bottom-color:#050505 !important;
  }}
  .luna-monthly-hero h1 {{
    color:#050505 !important;
    font-size:34pt;
  }}
  .luna-hero-theme {{
    color:#050505 !important;
  }}
  .luna-monthly-section {{
    padding:6mm 0;
  }}
  .luna-opening-story h2 {{
    font-size:27pt;
  }}
  .luna-story-prose p {{
    font-size:10.5pt;
    line-height:1.5;
  }}
  .luna-report-footer {{
    padding:3mm 0 0;
  }}
  .luna-story-act,
  .luna-story-date-card,
  .luna-romance-grid article,
  .luna-life-row,
  .luna-date-card,
  .luna-evidence-grid div {{
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-act,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-date-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-romance-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-evidence-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-date-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-life-row,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-next-move {{
    grid-template-columns:1fr;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-life-row {{
    padding:2.5mm 0;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-next-move h2 {{
    font-size:25pt;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-section,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-dates-section {{
    break-before:page;
    page-break-before:always;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-monthly-hero h1 {{
    font-size:30pt;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-monthly-section {{
    padding:4mm 0;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-story-act {{
    grid-template-columns:30mm 1fr;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-life-list {{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    border-left:1px solid #050505;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-life-row {{
    display:block;
    padding:4mm;
    border-right:1px solid #050505;
    border-bottom:1px solid #050505;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-story-date-grid,
  .luna-monthly-report[data-print-orientation="landscape"] .luna-romance-grid,
  .luna-monthly-report[data-print-orientation="landscape"] .luna-evidence-grid,
  .luna-monthly-report[data-print-orientation="landscape"] .luna-date-grid {{
    grid-template-columns:repeat(2,1fr);
  }}
  .luna-evidence-stack {{
    break-before:page;
    page-break-before:always;
  }}
  .luna-evidence-stack details > *:not(summary) {{
    display:block !important;
  }}
  .luna-evidence-stack details summary span {{
    display:none !important;
  }}
  .luna-evidence-stack details summary {{
    break-after:avoid;
    page-break-after:avoid;
  }}
}}
</style>

<div
  class="luna-monthly-report"
  id="luna-monthly-report"
  data-print-paper="{_safe(default_paper)}"
  data-print-orientation="{_safe(default_orientation)}"
>
  <section class="luna-monthly-hero">
    <div class="luna-monthly-meta">
      <span>Monthly / {_safe(narrative.sign)}</span>
      <span>{_safe(narrative.label)}</span>
    </div>
    <h1>{_safe(narrative.hook_headline)}</h1>
    <div class="luna-hero-theme">
      <span>Monthly theme</span>
      <strong>{_safe(narrative.headline)}</strong>
    </div>
  </section>

  {body}

  <footer class="luna-report-footer">
    {_safe(FOOTER_DISCLAIMER)}
    {f'<br>Order reference: {_safe(order_reference)}' if order_reference else ''}
  </footer>

  {controls}
</div>

<script>
(() => {{
  const report = document.getElementById("luna-monthly-report");
  const paper = document.getElementById("luna-print-paper");
  const orientation = document.getElementById("luna-print-orientation");
  const printButton = document.getElementById("luna-print-report");
  const pageStyle = document.getElementById("luna-print-page-size");
  let printPortal = null;

  function selectedPaper() {{
    return paper ? paper.value : "{default_paper}";
  }}

  function selectedOrientation() {{
    return orientation ? orientation.value : "{default_orientation}";
  }}

  function applyPrintSettings() {{
    const paperValue = selectedPaper();
    const orientationValue = selectedOrientation();
    report.dataset.printPaper = paperValue;
    report.dataset.printOrientation = orientationValue;
    pageStyle.textContent =
      "@page {{ size: " + paperValue + " " + orientationValue + "; margin: 12mm; }}";
  }}

  function removePrintPortal() {{
    if (printPortal && printPortal.parentNode) {{
      printPortal.parentNode.removeChild(printPortal);
    }}
    printPortal = null;
    document.body.classList.remove("luna-print-active");
  }}

  function createPrintPortal() {{
    if (printPortal) return printPortal;

    applyPrintSettings();

    printPortal = document.createElement("div");
    printPortal.id = "luna-print-portal";

    const clone = report.cloneNode(true);
    clone.id = "luna-monthly-report-print";
    clone.dataset.printPaper = selectedPaper();
    clone.dataset.printOrientation = selectedOrientation();

    clone.querySelectorAll(".luna-print-controls").forEach((node) => node.remove());
    const expandAllPrintDetails = () => {{
      clone.querySelectorAll("details").forEach((detail) => {{
        detail.open = true;
        detail.setAttribute("open", "");
      }});
    }};

    expandAllPrintDetails();

    // Run again after the clone enters the document. This catches nested
    // disclosures and any browser-created details state before pagination.
    window.requestAnimationFrame(expandAllPrintDetails);

    printPortal.appendChild(clone);
    document.body.appendChild(printPortal);
    document.body.classList.add("luna-print-active");
    return printPortal;
  }}

  function preparePrint() {{
    createPrintPortal();
  }}

  function restorePrint() {{
    window.setTimeout(removePrintPortal, 0);
  }}

  if (paper) paper.addEventListener("change", applyPrintSettings);
  if (orientation) orientation.addEventListener("change", applyPrintSettings);
  window.addEventListener("beforeprint", preparePrint);
  window.addEventListener("afterprint", restorePrint);

  if (printButton) {{
    printButton.addEventListener("click", async () => {{
      createPrintPortal();
      if (document.fonts && document.fonts.ready) {{
        await document.fonts.ready;
      }}
      window.setTimeout(() => window.print(), 180);
    }});
  }}

  applyPrintSettings();
}})();
</script>
    """


def render_monthly_experience(
    narrative: MonthlyNarrative,
    result: dict,
    *,
    show_print: bool = True,
    preview: bool = False,
    order_reference: str = "",
    default_paper: str = "A4",
    default_orientation: str = "portrait",
) -> None:
    import streamlit as st

    st.html(
        build_monthly_experience_html(
            narrative,
            result,
            show_print=show_print,
            preview=preview,
            order_reference=order_reference,
            default_paper=default_paper,
            default_orientation=default_orientation,
        ),
        unsafe_allow_javascript=True,
    )
