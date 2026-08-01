from __future__ import annotations

from html import escape
from typing import Iterable

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
            f"<td>{_safe(item.get('event_date'))}</td>"
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
            f"<td>{_safe(item.get('retrograde_start'))}</td>"
            f"<td>{_safe(item.get('direct_date'))}</td>"
            f"<td>{_safe(', '.join(map(str, item.get('houses') or [])))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _chapter_cards(narrative: MonthlyNarrative) -> str:
    cards = []
    for chapter in narrative.chapters:
        paragraph = chapter.paragraphs[0] if chapter.paragraphs else ""
        cards.append(
            f"""
<article class="luna-act">
  <div class="luna-mono">{_safe(chapter.date_range)}</div>
  <h3>{_safe(chapter.hook)}</h3>
  <p>{_safe(paragraph)}</p>
</article>
            """
        )
    return "".join(cards)


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

    evidence = f"""
<section class="luna-evidence-stack">
  <details>
    <summary>{_safe(WHY_LUNA_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <p>{_safe(narrative.central_storyline)}</p>
      <p><strong>Theme:</strong> {_safe(narrative.headline)}</p>
      <p><strong>Convergence:</strong> {_safe(narrative.convergence_axis)}</p>
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
<section class="luna-monthly-section">
  <div class="luna-eyebrow">How {_safe(narrative.label.split()[0])} unfolds</div>
  <div class="luna-act-grid">{chapters}</div>
</section>

<section class="luna-monthly-section luna-romance-section">
  <div class="luna-eyebrow">Romance and validation</div>
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
  <div class="luna-eyebrow">Love / work / money</div>
  <div class="luna-life-list">{life_rows}</div>
</section>

<section class="luna-monthly-section luna-next-move">
  <div class="luna-eyebrow">{_safe(YOUR_MOVE_LABEL)}</div>
  <h2>{_safe(GATEKEEPER_LINE)}</h2>
  <ol>
    {''.join(f'<li>{_safe(action)}</li>' for action in narrative.action_plan)}
  </ol>
</section>

{evidence}
        """
    else:
        body = f"""
<section class="luna-monthly-section luna-romance-section">
  <div class="luna-eyebrow">Romance and validation</div>
  <p>{_safe(narrative.romance_active)}</p>
  <p>{_safe(narrative.romance_quiet)}</p>
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
  padding:clamp(1.4rem,4vw,3.2rem);
  color:var(--white);
  background:var(--black);
}}
.luna-monthly-meta {{
  display:flex;
  justify-content:space-between;
  gap:1rem;
  padding-bottom:.8rem;
  border-bottom:1px solid rgba(255,255,255,.28);
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.045em;
  text-transform:uppercase;
}}
.luna-monthly-hero h1 {{
  max-width:760px;
  margin:1.2rem 0 1rem;
  color:var(--white);
  font-size:clamp(2.9rem,7vw,5.8rem);
  line-height:.94;
}}
.luna-says {{
  max-width:720px;
}}
.luna-says span,
.luna-eyebrow,
.luna-act span,
.luna-romance-grid span,
.luna-life-row > span {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.05em;
  text-transform:uppercase;
}}
.luna-says p {{
  color:rgba(255,255,255,.88);
  font-size:clamp(1.02rem,1.7vw,1.22rem);
  line-height:1.5;
}}
.luna-do-dont {{
  display:grid;
  grid-template-columns:1fr 1fr;
  border-top:1px solid rgba(255,255,255,.3);
  margin-top:1rem;
}}
.luna-do-dont div {{
  padding:.8rem .8rem 0 0;
}}
.luna-do-dont div + div {{
  border-left:1px solid rgba(255,255,255,.3);
  padding-left:.8rem;
}}
.luna-do-dont span {{
  display:block;
  color:rgba(255,255,255,.58);
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
  margin-bottom:.25rem;
}}
.luna-do-dont strong {{
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.15rem,2vw,1.55rem);
  line-height:1.16;
}}
.luna-monthly-section {{
  padding:clamp(2.4rem,6vw,5rem) clamp(1rem,4vw,3.2rem);
  border-bottom:1px solid var(--black);
}}
.luna-act-grid {{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-act {{
  min-width:0;
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-act h3,
.luna-life-row h3 {{
  margin:.5rem 0;
  font-size:clamp(1.5rem,2.5vw,2.15rem);
  line-height:1.02;
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
  position:sticky;
  bottom:0;
  z-index:50;
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
  .luna-do-dont,
  .luna-act-grid,
  .luna-romance-grid,
  .luna-next-move,
  .luna-evidence-grid,
  .luna-date-grid {{
    grid-template-columns:1fr;
    flex-direction:column;
  }}
  .luna-do-dont div + div {{
    border-left:none;
    border-top:1px solid rgba(255,255,255,.3);
    padding-left:0;
  }}
  .luna-life-row {{
    grid-template-columns:1fr;
    gap:.35rem;
  }}
  .luna-print-controls {{
    align-items:stretch;
    flex-wrap:wrap;
  }}
  .luna-print-check {{
    width:100%;
    margin-left:0;
  }}
  .luna-print-controls button {{
    width:100%;
  }}
}}
@media print {{
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
    padding:8mm 0 7mm;
    color:#050505 !important;
    background:#fff !important;
    border-top:3mm solid #050505;
    border-bottom:1px solid #050505;
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-meta {{
    border-bottom-color:#050505 !important;
  }}
  .luna-monthly-hero h1,
  .luna-says p,
  .luna-do-dont strong {{
    color:#050505 !important;
  }}
  .luna-says span,
  .luna-do-dont span {{
    color:#696963 !important;
  }}
  .luna-do-dont {{
    border-top-color:#050505 !important;
  }}
  .luna-do-dont div + div {{
    border-left-color:#050505 !important;
  }}
  .luna-monthly-hero h1 {{
    font-size:38pt;
  }}
  .luna-says p {{
    font-size:11pt;
  }}
  .luna-monthly-section {{
    padding:6mm 0;
  }}
  .luna-report-footer {{
    padding:3mm 0 0;
  }}
  .luna-act,
  .luna-romance-grid article,
  .luna-life-row,
  .luna-date-card,
  .luna-evidence-grid div {{
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-act-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-romance-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-evidence-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-date-grid {{
    grid-template-columns:1fr;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-life-row,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-next-move {{
    grid-template-columns:1fr;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-life-row {{
    padding:2.5mm 0;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-next-move h2 {{
    font-size:26pt;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-romance-section {{
    break-before:page;
    page-break-before:always;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-monthly-hero h1 {{
    font-size:32pt;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-says p {{
    font-size:9.5pt;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-monthly-section {{
    padding:4mm 0;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-act-grid {{
    grid-template-columns:repeat(3,1fr);
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
    <div class="luna-says">
      <span>{_safe(LUNA_SAYS_LABEL)}</span>
      {_paragraphs(narrative.luna_says, maximum=1)}
    </div>
    <div class="luna-do-dont">
      <div><span>{_safe(DO_LABEL)}</span><strong>{_safe(narrative.do_line)}</strong></div>
      <div><span>{_safe(DONT_LABEL)}</span><strong>{_safe(narrative.dont_line)}</strong></div>
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
  let previousStates = [];
  let printPrepared = false;

  function applyPrintSettings() {{
    const selectedPaper = paper ? paper.value : "{default_paper}";
    const selectedOrientation = orientation ? orientation.value : "{default_orientation}";
    report.dataset.printPaper = selectedPaper;
    report.dataset.printOrientation = selectedOrientation;
    pageStyle.textContent =
      "@page {{ size: " + selectedPaper + " " + selectedOrientation + "; margin: 12mm; }}";
  }}

  function preparePrint() {{
    if (printPrepared) return;
    printPrepared = true;
    applyPrintSettings();
    previousStates = [];
    report.querySelectorAll("details").forEach((detail) => {{
      previousStates.push(detail.open);
      detail.open = true;
    }});
  }}

  function restorePrint() {{
    report.querySelectorAll("details").forEach((detail, index) => {{
      detail.open = previousStates[index] || false;
    }});
    printPrepared = false;
  }}

  if (paper) paper.addEventListener("change", applyPrintSettings);
  if (orientation) orientation.addEventListener("change", applyPrintSettings);
  window.addEventListener("beforeprint", preparePrint);
  window.addEventListener("afterprint", restorePrint);
  if (printButton) {{
    printButton.addEventListener("click", async () => {{
      preparePrint();
      if (document.fonts && document.fonts.ready) {{
        await document.fonts.ready;
      }}
      window.setTimeout(() => window.print(), 120);
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
