from __future__ import annotations

from html import escape
from typing import Iterable

from monthly_narrative_v1 import MonthlyNarrative


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _paragraphs(values: Iterable[str]) -> str:
    return "".join(f"<p>{_safe(value)}</p>" for value in values if value)


def _scenario_chips(values: Iterable[str]) -> str:
    return "".join(
        f'<span class="luna-scenario">{_safe(value)}</span>'
        for value in values
    )


def _key_date_cards(narrative: MonthlyNarrative) -> str:
    return "".join(
        f"""
<div class="luna-date-card">
  <span>{_safe(item.date_label)}</span>
  <strong>{_safe(item.consequence)}</strong>
  <p>{_safe(item.response)}</p>
  <small>{_safe(item.evidence)}</small>
</div>
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


def build_monthly_experience_html(
    narrative: MonthlyNarrative,
    result: dict,
    *,
    show_print: bool = True,
    preview: bool = False,
    order_reference: str = "",
) -> str:
    chapters = "".join(
        f"""
<article class="luna-act">
  <div class="luna-mono">{_safe(chapter.label)} / {_safe(chapter.date_range)}</div>
  <h3>{_safe(chapter.hook)}</h3>
  <div class="luna-theme">{_safe(chapter.title)}</div>
  {_paragraphs(chapter.paragraphs)}
  <div class="luna-act-action"><span>Your move</span>{_safe(chapter.action)}</div>
</article>
        """
        for chapter in narrative.chapters
    )

    print_controls = ""
    if show_print:
        print_controls = """
<div class="luna-print-controls">
  <label>
    <input id="luna-include-evidence" type="checkbox">
    Include evidence in print
  </label>
  <button id="luna-print-report" type="button">Print or save report</button>
</div>
        """

    detail_sections = f"""
<section class="luna-evidence-stack">
  <details>
    <summary>Why Luna sees this <span>+</span></summary>
    <div class="luna-detail-body">
      <p><strong>Serious theme:</strong> {_safe(narrative.headline)}</p>
      <p>{_safe(narrative.subtitle)}</p>
      <p><strong>Central storyline:</strong> {_safe(narrative.central_storyline)}</p>
      <p><strong>Monthly convergence:</strong> {_safe(narrative.convergence_axis)}</p>
      <p><strong>Validation rule:</strong> {_safe(narrative.validation_rule)}</p>
    </div>
  </details>

  <details>
    <summary>Solar Convergence <span>+</span></summary>
    <div class="luna-detail-body">
      <h3>{_safe(narrative.solar_title)}</h3>
      {_paragraphs(narrative.solar_paragraphs)}
      <div class="luna-evidence-grid">
        {''.join(
            f'<div><span>{_safe(label)}</span><strong>{_safe(value)}</strong></div>'
            for label, value in narrative.solar_rows
        )}
      </div>
      <p><strong>Opportunity:</strong> {_safe(narrative.solar_opportunity)}</p>
      <p><strong>Risk:</strong> {_safe(narrative.solar_risk)}</p>
      <p><strong>Strategic response:</strong> {_safe(narrative.solar_action)}</p>
      <p><strong>Solar rule:</strong> {_safe(narrative.solar_rule)}</p>
    </div>
  </details>

  <details>
    <summary>Key dates and planetary timing <span>+</span></summary>
    <div class="luna-detail-body">
      <div class="luna-date-grid">{_key_date_cards(narrative)}</div>
    </div>
  </details>

  <details>
    <summary>Full technical evidence <span>+</span></summary>
    <div class="luna-detail-body">
      <p>
        Tropical geocentric planetary positions are calculated with Swiss
        Ephemeris and interpreted using whole-sign houses. Concentration scores
        describe the internal strength of a pattern; they are not guarantees.
      </p>
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

    full_sections = ""
    if not preview:
        full_sections = f"""
<section class="luna-monthly-section">
  <div class="luna-eyebrow">What this may look like</div>
  <h2>Concrete possibilities—not promises</h2>
  <div class="luna-scenario-list">{_scenario_chips(narrative.scenario_examples)}</div>
  <p>
    Luna uses examples so you can recognise the pattern in your own life.
    The event itself is not guaranteed; your response remains the decisive part.
  </p>
</section>

<section class="luna-monthly-section">
  <div class="luna-eyebrow">The month in three acts</div>
  <h2>You remain the main character</h2>
  <div class="luna-act-grid">{chapters}</div>
</section>

<section class="luna-monthly-section luna-romance-section">
  <div class="luna-eyebrow">Romance, flirting and validation</div>
  <h2>Whether love is active—or not</h2>
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
  <blockquote>{_safe(narrative.validation_rule)}</blockquote>
</section>

<section class="luna-monthly-section">
  <div class="luna-eyebrow">Love / work / money</div>
  <div class="luna-life-grid">
    <article>
      <span>Love</span>
      <h3>{_safe(narrative.love_hook)}</h3>
      {_paragraphs(narrative.love_story[:2])}
    </article>
    <article>
      <span>Work</span>
      <h3>{_safe(narrative.work_hook)}</h3>
      {_paragraphs(narrative.work_story[:2])}
    </article>
    <article>
      <span>Money</span>
      <h3>{_safe(narrative.money_hook)}</h3>
      {_paragraphs(narrative.money_story[:2])}
    </article>
  </div>
</section>

<section class="luna-monthly-section luna-next-move">
  <div>
    <div class="luna-eyebrow">Your next move</div>
    <h2>Choose what strengthens your life</h2>
  </div>
  <ol>
    {''.join(f'<li>{_safe(action)}</li>' for action in narrative.action_plan)}
  </ol>
</section>

{detail_sections}
        """
    else:
        full_sections = f"""
<section class="luna-monthly-section">
  <div class="luna-eyebrow">What this may look like</div>
  <div class="luna-scenario-list">{_scenario_chips(narrative.scenario_examples[:4])}</div>
</section>

<section class="luna-monthly-section luna-romance-section">
  <div class="luna-eyebrow">Romance or not</div>
  <h2>You decide what earns access</h2>
  <p>{_safe(narrative.romance_active)}</p>
  <p>{_safe(narrative.romance_quiet)}</p>
</section>
        """

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&family=IBM+Plex+Mono:wght@400;500;600&family=Josefin+Sans:wght@300;400;500;600;700&display=swap');

.luna-monthly-report {{
  --black:#050505;
  --white:#fff;
  --soft:#f5f5f2;
  --line:#d8d8d3;
  --muted:#696963;
  width:100%;
  max-width:1100px;
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
  letter-spacing:-.04em;
}}
.luna-monthly-report p {{
  font-size:clamp(1.02rem,1.5vw,1.2rem);
  line-height:1.62;
  margin:.45rem 0 1rem;
}}
.luna-monthly-hero {{
  min-height:min(760px,88dvh);
  display:flex;
  flex-direction:column;
  justify-content:center;
  gap:1.4rem;
  padding:clamp(1.3rem,5vw,4.8rem);
  color:var(--white);
  background:var(--black);
  position:relative;
  overflow:hidden;
}}
.luna-monthly-hero::after {{
  content:"";
  width:18rem;
  height:18rem;
  border:1px solid rgba(255,255,255,.27);
  position:absolute;
  right:-7rem;
  bottom:-9rem;
  transform:rotate(30deg);
}}
.luna-monthly-brand {{
  position:relative;
  z-index:2;
  display:flex;
  justify-content:space-between;
  gap:1rem;
  padding-bottom:1rem;
  border-bottom:1px solid rgba(255,255,255,.28);
  font-family:"IBM Plex Mono",monospace;
  font-size:.68rem;
  letter-spacing:.05em;
  text-transform:uppercase;
}}
.luna-monthly-axis {{
  position:relative;
  z-index:2;
  color:rgba(255,255,255,.72);
  font-family:"IBM Plex Mono",monospace;
  font-size:.72rem;
  letter-spacing:.05em;
  text-transform:uppercase;
}}
.luna-monthly-hero h1 {{
  position:relative;
  z-index:2;
  max-width:900px;
  margin:0;
  color:var(--white);
  font-size:clamp(3.2rem,9vw,7rem);
  line-height:.92;
}}
.luna-luna-says {{
  position:relative;
  z-index:2;
  max-width:760px;
}}
.luna-luna-says span,
.luna-eyebrow,
.luna-act span,
.luna-romance-grid span,
.luna-life-grid span {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.67rem;
  letter-spacing:.055em;
  text-transform:uppercase;
}}
.luna-luna-says p {{
  color:rgba(255,255,255,.88);
  font-size:clamp(1.1rem,2vw,1.35rem);
  line-height:1.55;
}}
.luna-do-dont {{
  position:relative;
  z-index:2;
  display:grid;
  grid-template-columns:1fr 1fr;
  border-top:1px solid rgba(255,255,255,.3);
  border-bottom:1px solid rgba(255,255,255,.3);
}}
.luna-do-dont div {{ padding:1rem 1rem 1rem 0; }}
.luna-do-dont div + div {{
  border-left:1px solid rgba(255,255,255,.3);
  padding-left:1rem;
}}
.luna-do-dont span {{
  display:block;
  color:rgba(255,255,255,.58);
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  text-transform:uppercase;
  margin-bottom:.35rem;
}}
.luna-do-dont strong {{
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.25rem,2.4vw,1.8rem);
  line-height:1.18;
}}
.luna-agency-rule {{
  position:relative;
  z-index:2;
  max-width:800px;
  margin:0;
  color:var(--white);
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.4rem,3vw,2.3rem);
  line-height:1.2;
}}
.luna-monthly-section {{
  padding:clamp(3.2rem,8vw,7rem) clamp(1.2rem,5vw,4.5rem);
  border-bottom:1px solid var(--black);
}}
.luna-monthly-section h2 {{
  margin:.35rem 0 1.5rem;
  font-size:clamp(2.5rem,6vw,5.5rem);
  line-height:.95;
}}
.luna-scenario-list {{
  display:flex;
  flex-wrap:wrap;
  gap:.6rem;
  margin:1.4rem 0;
}}
.luna-scenario {{
  border:1px solid var(--black);
  padding:.65rem .8rem;
  font-size:.95rem;
}}
.luna-act-grid,
.luna-life-grid,
.luna-romance-grid {{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-act,
.luna-life-grid article,
.luna-romance-grid article {{
  min-width:0;
  padding:1.25rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-act h3,
.luna-life-grid h3 {{
  margin:.6rem 0;
  font-size:clamp(1.65rem,3vw,2.5rem);
  line-height:1.02;
}}
.luna-theme {{
  margin-bottom:1rem;
  color:var(--muted);
  font-size:.95rem;
}}
.luna-act-action {{
  margin-top:1rem;
  padding-top:.8rem;
  border-top:1px solid var(--line);
}}
.luna-act-action span {{
  display:block;
  margin-bottom:.35rem;
}}
.luna-romance-grid {{ grid-template-columns:1fr 1fr; }}
.luna-romance-section blockquote {{
  margin:2rem 0 0;
  padding:1.2rem 0 0;
  border-top:1px solid var(--black);
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.55rem,3vw,2.5rem);
  line-height:1.2;
}}
.luna-life-grid article:first-child {{
  background:var(--black);
  color:var(--white);
}}
.luna-life-grid article:first-child h3 {{ color:var(--white); }}
.luna-next-move {{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:2rem;
}}
.luna-next-move ol {{
  margin:0;
  padding-left:1.5rem;
}}
.luna-next-move li {{
  margin-bottom:1rem;
  font-size:1.08rem;
  line-height:1.5;
}}
.luna-evidence-stack details {{
  border-bottom:1px solid var(--black);
}}
.luna-evidence-stack summary {{
  list-style:none;
  display:flex;
  justify-content:space-between;
  align-items:center;
  min-height:4.2rem;
  cursor:pointer;
  padding:0 clamp(1.2rem,5vw,4.5rem);
  font-family:"IBM Plex Mono",monospace;
  font-size:.74rem;
  text-transform:uppercase;
}}
.luna-evidence-stack summary::-webkit-details-marker {{ display:none; }}
.luna-detail-body {{
  padding:1rem clamp(1.2rem,5vw,4.5rem) 3rem;
}}
.luna-evidence-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
  margin:1rem 0 2rem;
}}
.luna-evidence-grid div {{
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-evidence-grid span {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  text-transform:uppercase;
  margin-bottom:.35rem;
}}
.luna-date-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-date-card {{
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-date-card span,
.luna-date-card small {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  text-transform:uppercase;
}}
.luna-date-card strong {{
  display:block;
  margin:.55rem 0;
  font-size:1.05rem;
}}
.luna-table-wrap {{ overflow-x:auto; margin-bottom:2rem; }}
.luna-monthly-report table {{
  width:100%;
  border-collapse:collapse;
}}
.luna-monthly-report th,
.luna-monthly-report td {{
  padding:.7rem .45rem;
  border-bottom:1px solid var(--line);
  text-align:left;
  vertical-align:top;
}}
.luna-monthly-report th {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  text-transform:uppercase;
}}
.luna-print-controls {{
  position:sticky;
  bottom:0;
  z-index:50;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:1rem;
  padding:.8rem 1rem;
  background:rgba(255,255,255,.96);
  border:1px solid var(--black);
}}
.luna-print-controls label {{
  font-size:.88rem;
}}
.luna-print-controls button {{
  border:1px solid var(--black);
  background:var(--black);
  color:var(--white);
  padding:.8rem 1rem;
  font-family:"IBM Plex Mono",monospace;
  text-transform:uppercase;
  cursor:pointer;
}}
@media (max-width:720px) {{
  .luna-monthly-hero {{
    min-height:calc(100dvh - 1rem);
    justify-content:flex-start;
    padding-top:2rem;
  }}
  .luna-monthly-brand,
  .luna-do-dont {{
    grid-template-columns:1fr;
    flex-direction:column;
  }}
  .luna-do-dont div + div {{
    border-left:none;
    border-top:1px solid rgba(255,255,255,.3);
    padding-left:0;
  }}
  .luna-act-grid,
  .luna-life-grid,
  .luna-romance-grid,
  .luna-next-move,
  .luna-evidence-grid,
  .luna-date-grid {{
    grid-template-columns:1fr;
  }}
  .luna-print-controls {{
    align-items:flex-start;
    flex-direction:column;
  }}
  .luna-print-controls button {{ width:100%; }}
}}
@media print {{
  body * {{ visibility:hidden !important; }}
  .luna-monthly-report,
  .luna-monthly-report * {{ visibility:visible !important; }}
  .luna-monthly-report {{
    position:absolute;
    inset:0;
    width:100%;
    max-width:none;
  }}
  .luna-print-controls {{ display:none !important; }}
  .luna-monthly-hero {{ min-height:auto; page-break-after:always; }}
  .luna-monthly-section {{ break-inside:avoid; }}
  details:not([open]) > *:not(summary) {{ display:none !important; }}
  @page {{ size:A4; margin:14mm; }}
}}
</style>

<div class="luna-monthly-report" id="luna-monthly-report">
  <section class="luna-monthly-hero">
    <div class="luna-monthly-brand">
      <span>Luna Convergence</span>
      <span>Monthly / {_safe(narrative.sign)} / {_safe(narrative.label)}</span>
    </div>
    <div class="luna-monthly-axis">{_safe(narrative.convergence_axis)}</div>
    <h1>{_safe(narrative.hook_headline)}</h1>
    <div class="luna-luna-says">
      <span>Luna says</span>
      {_paragraphs(narrative.luna_says)}
    </div>
    <div class="luna-do-dont">
      <div><span>Do</span><strong>{_safe(narrative.do_line)}</strong></div>
      <div><span>Don't</span><strong>{_safe(narrative.dont_line)}</strong></div>
    </div>
    <blockquote class="luna-agency-rule">{_safe(narrative.agency_rule)}</blockquote>
  </section>

  {full_sections}
  {print_controls}
</div>

<script>
(() => {{
  const report = document.getElementById("luna-monthly-report");
  const printButton = document.getElementById("luna-print-report");
  const includeEvidence = document.getElementById("luna-include-evidence");
  let previousStates = [];

  function preparePrint() {{
    previousStates = [];
    report.querySelectorAll("details").forEach((detail) => {{
      previousStates.push(detail.open);
      if (includeEvidence && includeEvidence.checked) detail.open = true;
    }});
  }}

  function restorePrint() {{
    report.querySelectorAll("details").forEach((detail, index) => {{
      detail.open = previousStates[index] || false;
    }});
  }}

  window.addEventListener("beforeprint", preparePrint);
  window.addEventListener("afterprint", restorePrint);

  if (printButton) {{
    printButton.addEventListener("click", () => window.print());
  }}
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
) -> None:
    import streamlit as st

    html = build_monthly_experience_html(
        narrative,
        result,
        show_print=show_print,
        preview=preview,
        order_reference=order_reference,
    )
    st.html(html, unsafe_allow_javascript=True)
