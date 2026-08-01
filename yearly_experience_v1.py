from __future__ import annotations

from html import escape

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
    luna_do_dont,
)
from monthly_experience_v1 import PRINT_ORIENTATIONS, PRINT_PAPERS
from monthly_narrative_v1 import HOUSE_DISPLAY, HOUSE_NATURAL


YEARLY_HOOKS = {
    1: "Your next version wants the final say",
    2: "Your standards become part of the strategy",
    3: "Your voice gets louder. Your choices get clearer.",
    4: "Your private life sets the terms",
    5: "Desire gets serious about the future",
    6: "The life you want needs a rhythm",
    7: "Relationships meet your new standards",
    8: "Intensity now needs proof",
    9: "Your world gets bigger. Your standards get sharper.",
    10: "Visibility raises the stakes",
    11: "Your future edits the guest list",
    12: "Closure clears the next entrance",
}


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _top_houses(result: dict) -> tuple[int, int]:
    rows = result.get("dominant_houses") or []
    first = int(rows[0].get("house", 1)) if rows else 1
    second = int(rows[1].get("house", first)) if len(rows) > 1 else first
    return first, second


def _hook(result: dict) -> str:
    first, second = _top_houses(result)
    pair = frozenset({first, second})
    if pair == frozenset({5, 9}):
        return "Your world gets bigger. Your standards get sharper."
    if pair == frozenset({3, 5}):
        return "Your voice gets louder. Desire gets clearer."
    if pair == frozenset({7, 10}):
        return "Love and ambition renegotiate the terms"
    return YEARLY_HOOKS[first]


def _luna_says(result: dict) -> str:
    first, second = _top_houses(result)
    year = str(result.get("label", "This year"))
    return (
        f"{year} expands {_safe(HOUSE_NATURAL[first])} and tests "
        f"{_safe(HOUSE_NATURAL[second])}. Romance may arrive loudly or stay "
        "quiet while validation comes through attention, work or visibility. "
        "Notice what opens. Then choose what proves it can support your future."
    )


def _romance(result: dict) -> tuple[str, str]:
    first, second = _top_houses(result)
    houses = {first, second}
    if houses & {5, 7, 8, 11}:
        active = (
            "If romance is active, attraction grows through shared direction. "
            "Watch for intention, effort and the ability to plan beyond the first spark."
        )
    else:
        active = (
            "If someone shows interest, judge whether their behaviour matches "
            "your standards and the future you are building."
        )
    quiet = (
        "If romance stays quiet, validation may arrive through work, creativity, "
        "friendship or public recognition. Let it strengthen your choices—not replace them."
    )
    return active, quiet


def _chapter_cards(result: dict) -> str:
    cards = []
    for chapter in result.get("solar_year_chapters") or []:
        cards.append(
            f"""
<article class="luna-year-chapter">
  <span>{_safe(chapter.get('name'))}</span>
  <h3>{_safe(chapter.get('strategic_question'))}</h3>
  <p>{_safe(chapter.get('focus_direction'))}</p>
  <small>{_safe(human_date_range(chapter.get('start_date'), chapter.get('end_date')))}</small>
</article>
            """
        )
    return "".join(cards)


def _moves(result: dict) -> list[str]:
    values = []
    for item in result.get("strategic_chapters") or []:
        strategy = str(item.get("strategy", "")).strip()
        if strategy and strategy not in values:
            values.append(strategy[0].upper() + strategy[1:].rstrip(".") + ".")
        if len(values) == 3:
            break
    return values or [
        "Back what proves itself.",
        "Protect the structure behind the opportunity.",
        "Review the result before expanding again.",
    ]


def _timing_cards(result: dict) -> str:
    return "".join(
        f"""
<article class="luna-date-card">
  <span>{_safe(human_date(item.get('event_date')))}</span>
  <strong>{_safe(item.get('title'))}</strong>
  <p>{_safe(item.get('detail'))}</p>
</article>
        """
        for item in (result.get("major_transitions") or [])[:10]
    )


def _technical_rows(result: dict) -> str:
    return "".join(
        "<tr>"
        f"<td>House {_safe(item.get('house'))}</td>"
        f"<td>{_safe(item.get('topic'))}</td>"
        f"<td>{float(item.get('weight', 0.0)):.1f}</td>"
        "</tr>"
        for item in (result.get("dominant_houses") or [])[:8]
    )


def _print_controls(default_paper: str, default_orientation: str) -> str:
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
  <div><label>Paper</label><select id="luna-print-paper">{paper_options}</select></div>
  <div><label>Orientation</label><select id="luna-print-orientation">{orientation_options}</select></div>
  <button id="luna-print-report" type="button">Print or save report</button>
</div>
    """


def build_yearly_experience_html(
    result: dict,
    *,
    show_print: bool = True,
    order_reference: str = "",
    default_paper: str = "A4",
    default_orientation: str = "portrait",
) -> str:
    if result.get("period") != "yearly":
        raise ValueError("Yearly experience requires a yearly result")
    if default_paper not in PRINT_PAPERS:
        raise ValueError(f"Unsupported paper: {default_paper}")
    if default_orientation not in PRINT_ORIENTATIONS:
        raise ValueError(f"Unsupported orientation: {default_orientation}")

    sign = str(result.get("sign", ""))
    label = str(result.get("label", "Year ahead"))
    first, second = _top_houses(result)
    active, quiet = _romance(result)
    moves = _moves(result)
    do_line, dont_line = luna_do_dont(first, second)

    controls = _print_controls(default_paper, default_orientation) if show_print else ""

    return f"""
<style id="luna-print-page-size">
@page {{ size: {default_paper} {default_orientation}; margin:12mm; }}
</style>
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&family=IBM+Plex+Mono:wght@400;500;600&family=Josefin+Sans:wght@300;400;500;600;700&display=swap');
.luna-yearly-report {{
  --black:#050505; --white:#fff; --line:#d8d8d3; --muted:#696963;
  max-width:900px; margin:0 auto; color:var(--black); background:#fff;
  font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif;
}}
.luna-yearly-report * {{ box-sizing:border-box; }}
.luna-yearly-report h1,.luna-yearly-report h2,.luna-yearly-report h3 {{
  font-family:"Bodoni MT","Bodoni 72","Bodoni Moda",Didot,Georgia,serif;
  font-weight:500; letter-spacing:-.035em;
}}
.luna-yearly-report p {{ font-size:clamp(.98rem,1.35vw,1.12rem); line-height:1.58; }}
.luna-year-hero {{ padding:clamp(1.4rem,4vw,3.2rem); background:#050505; color:#fff; }}
.luna-year-meta {{ display:flex; justify-content:space-between; gap:1rem; padding-bottom:.8rem; border-bottom:1px solid rgba(255,255,255,.28); font-family:"IBM Plex Mono",monospace; font-size:.65rem; text-transform:uppercase; }}
.luna-year-hero h1 {{ max-width:760px; margin:1.2rem 0 1rem; color:#fff; font-size:clamp(2.9rem,7vw,5.8rem); line-height:.94; }}
.luna-says span,.luna-eyebrow,.luna-year-chapter span,.luna-romance-grid span {{ font-family:"IBM Plex Mono",monospace; font-size:.65rem; text-transform:uppercase; letter-spacing:.05em; }}
.luna-says p {{ color:rgba(255,255,255,.88); max-width:720px; font-size:clamp(1.02rem,1.7vw,1.22rem); }}
.luna-do-dont {{ display:grid; grid-template-columns:1fr 1fr; border-top:1px solid rgba(255,255,255,.3); margin-top:1rem; }}
.luna-do-dont div {{ padding:.8rem .8rem 0 0; }}
.luna-do-dont div+div {{ border-left:1px solid rgba(255,255,255,.3); padding-left:.8rem; }}
.luna-do-dont span {{ display:block; color:rgba(255,255,255,.58); font-family:"IBM Plex Mono",monospace; font-size:.63rem; text-transform:uppercase; }}
.luna-do-dont strong {{ font-family:"Bodoni Moda",Georgia,serif; font-size:clamp(1.15rem,2vw,1.55rem); }}
.luna-section {{ padding:clamp(2.4rem,6vw,5rem) clamp(1rem,4vw,3.2rem); border-bottom:1px solid #050505; }}
.luna-year-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-year-chapter {{ padding:1rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-year-chapter h3 {{ font-size:clamp(1.5rem,2.5vw,2.15rem); margin:.45rem 0; }}
.luna-year-chapter small {{ font-family:"IBM Plex Mono",monospace; font-size:.62rem; }}
.luna-romance-grid {{ display:grid; grid-template-columns:1fr 1fr; border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-romance-grid article {{ padding:1rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-next-move {{ display:grid; grid-template-columns:.8fr 1.2fr; gap:2rem; }}
.luna-next-move h2 {{ font-size:clamp(2.2rem,5vw,4.2rem); line-height:.98; margin:.4rem 0 0; }}
.luna-next-move li {{ margin-bottom:.8rem; line-height:1.48; }}
.luna-evidence details {{ border-bottom:1px solid #050505; }}
.luna-evidence summary {{ list-style:none; display:flex; justify-content:space-between; align-items:center; min-height:3.8rem; padding:0 clamp(1rem,4vw,3.2rem); cursor:pointer; font-family:"IBM Plex Mono",monospace; font-size:.7rem; text-transform:uppercase; }}
.luna-evidence summary::-webkit-details-marker {{ display:none; }}
.luna-detail {{ padding:.8rem clamp(1rem,4vw,3.2rem) 2.4rem; }}
.luna-date-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-date-card {{ padding:.9rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-date-card span {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:.63rem; text-transform:uppercase; }}
.luna-date-card strong {{ display:block; margin:.45rem 0; }}
.luna-table-wrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ padding:.65rem .4rem; border-bottom:1px solid var(--line); text-align:left; }}
th {{ font-family:"IBM Plex Mono",monospace; font-size:.63rem; text-transform:uppercase; }}
.luna-footer {{ padding:1.2rem clamp(1rem,4vw,3.2rem); color:var(--muted); font-size:.72rem; line-height:1.5; }}
.luna-print-controls {{ position:sticky; bottom:0; display:flex; align-items:end; gap:.75rem; padding:.75rem; background:rgba(255,255,255,.97); border:1px solid #050505; }}
.luna-print-controls div {{ display:flex; flex-direction:column; gap:.2rem; }}
.luna-print-controls label {{ font-family:"IBM Plex Mono",monospace; font-size:.6rem; text-transform:uppercase; }}
.luna-print-controls select,.luna-print-controls button {{ min-height:2.5rem; border:1px solid #050505; padding:.45rem .6rem; }}
.luna-print-controls button {{ background:#050505; color:#fff; font-family:"IBM Plex Mono",monospace; text-transform:uppercase; }}
.luna-print-check {{ margin-left:auto; }}
@media(max-width:720px) {{
  .luna-year-meta,.luna-do-dont,.luna-year-grid,.luna-romance-grid,.luna-next-move,.luna-date-grid {{ grid-template-columns:1fr; flex-direction:column; }}
  .luna-do-dont div+div {{ border-left:none; border-top:1px solid rgba(255,255,255,.3); padding-left:0; }}
  .luna-print-controls {{ flex-wrap:wrap; align-items:stretch; }}
  .luna-print-check {{ width:100%; margin-left:0; }}
  .luna-print-controls button {{ width:100%; }}
}}
#luna-year-print-portal {{ display:none; }}
@media print {{
  body.luna-year-print-active > *:not(#luna-year-print-portal):not(style):not(script) {{
    display:none !important;
  }}
  #luna-year-print-portal {{
    display:block !important;
    position:static !important;
    width:100% !important;
    max-width:none !important;
    margin:0 !important;
    padding:0 !important;
  }}
  #luna-year-print-portal .luna-yearly-report {{
    display:block !important;
    position:static !important;
    width:100% !important;
    max-width:none !important;
    height:auto !important;
    max-height:none !important;
    overflow:visible !important;
    margin:0 !important;
  }}
  html,body {{ margin:0!important; padding:0!important; background:#fff!important; }}
  .luna-yearly-report {{ position:static!important; width:100%; max-width:none; margin:0; }}
  .luna-print-controls {{ display:none!important; }}
  .luna-year-hero {{
    padding:8mm 0 7mm;
    color:#050505!important;
    background:#fff!important;
    border-top:3mm solid #050505;
    border-bottom:1px solid #050505;
    break-inside:avoid;
  }}
  .luna-year-meta {{ border-bottom-color:#050505!important; }}
  .luna-year-hero h1,.luna-says p,.luna-do-dont strong {{ color:#050505!important; }}
  .luna-says span,.luna-do-dont span {{ color:#696963!important; }}
  .luna-do-dont {{ border-top-color:#050505!important; }}
  .luna-do-dont div+div {{ border-left-color:#050505!important; }}
  .luna-year-hero h1 {{ font-size:38pt; }}
  .luna-section {{ padding:8mm 0; }}
  .luna-year-chapter,.luna-romance-grid article,.luna-date-card {{ break-inside:avoid; }}
  .luna-yearly-report[data-print-orientation="portrait"] .luna-year-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-romance-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-date-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-next-move {{ grid-template-columns:1fr; }}
  .luna-evidence {{ break-before:page; page-break-before:always; }}
  .luna-evidence details>*:not(summary) {{ display:block!important; }}
  .luna-evidence details summary span {{ display:none!important; }}
  .luna-evidence details summary {{ break-after:avoid; page-break-after:avoid; }}
}}
</style>

<div class="luna-yearly-report" id="luna-yearly-report" data-print-paper="{_safe(default_paper)}" data-print-orientation="{_safe(default_orientation)}">
  <section class="luna-year-hero">
    <div class="luna-year-meta"><span>Year ahead / {_safe(sign)}</span><span>{_safe(label)}</span></div>
    <h1>{_safe(_hook(result))}</h1>
    <div class="luna-says"><span>{_safe(LUNA_SAYS_LABEL)}</span><p>{_luna_says(result)}</p></div>
    <div class="luna-do-dont">
      <div><span>{_safe(DO_LABEL)}</span><strong>{_safe(do_line)}</strong></div>
      <div><span>{_safe(DONT_LABEL)}</span><strong>{_safe(dont_line)}</strong></div>
    </div>
  </section>

  <section class="luna-section">
    <div class="luna-eyebrow">How the year unfolds</div>
    <div class="luna-year-grid">{_chapter_cards(result)}</div>
  </section>

  <section class="luna-section">
    <div class="luna-eyebrow">Romance and validation</div>
    <div class="luna-romance-grid">
      <article><span>When romance is active</span><p>{_safe(active)}</p></article>
      <article><span>When romance is quiet</span><p>{_safe(quiet)}</p></article>
    </div>
  </section>

  <section class="luna-section luna-next-move">
    <div><div class="luna-eyebrow">{_safe(YOUR_MOVE_LABEL)}</div><h2>{_safe(GATEKEEPER_LINE)}</h2></div>
    <ol>{''.join(f'<li>{_safe(item)}</li>' for item in moves)}</ol>
  </section>

  <section class="luna-evidence">
    <details><summary>{_safe(WHY_LUNA_LABEL)} <span>+</span></summary><div class="luna-detail"><p>Primary areas: {_safe(HOUSE_DISPLAY[first])} and {_safe(HOUSE_DISPLAY[second])}.</p><p>{_safe(VALIDATION_LINE)}</p></div></details>
    <details><summary>{_safe(SOLAR_LABEL)} <span>+</span></summary><div class="luna-detail"><div class="luna-year-grid">{_chapter_cards(result)}</div></div></details>
    <details><summary>{_safe(TIMING_LABEL)} <span>+</span></summary><div class="luna-detail"><div class="luna-date-grid">{_timing_cards(result)}</div></div></details>
    <details><summary>{_safe(TECHNICAL_LABEL)} <span>+</span></summary><div class="luna-detail"><div class="luna-table-wrap"><table><thead><tr><th>House</th><th>Life area</th><th>Weight</th></tr></thead><tbody>{_technical_rows(result)}</tbody></table></div></div></details>
  </section>

  <footer class="luna-footer">{_safe(FOOTER_DISCLAIMER)}{f'<br>Order reference: {_safe(order_reference)}' if order_reference else ''}</footer>
  {controls}
</div>

<script>
(() => {{
  const report=document.getElementById("luna-yearly-report");
  const paper=document.getElementById("luna-print-paper");
  const orientation=document.getElementById("luna-print-orientation");
  const printButton=document.getElementById("luna-print-report");
  const pageStyle=document.getElementById("luna-print-page-size");
  let printPortal=null;

  function selectedPaper() {{
    return paper?paper.value:"{default_paper}";
  }}

  function selectedOrientation() {{
    return orientation?orientation.value:"{default_orientation}";
  }}

  function settings() {{
    const p=selectedPaper();
    const o=selectedOrientation();
    report.dataset.printPaper=p;
    report.dataset.printOrientation=o;
    pageStyle.textContent="@page {{ size: "+p+" "+o+"; margin:12mm; }}";
  }}

  function removePortal() {{
    if(printPortal&&printPortal.parentNode) {{
      printPortal.parentNode.removeChild(printPortal);
    }}
    printPortal=null;
    document.body.classList.remove("luna-year-print-active");
  }}

  function createPortal() {{
    if(printPortal)return printPortal;
    settings();

    printPortal=document.createElement("div");
    printPortal.id="luna-year-print-portal";

    const clone=report.cloneNode(true);
    clone.id="luna-yearly-report-print";
    clone.dataset.printPaper=selectedPaper();
    clone.dataset.printOrientation=selectedOrientation();

    clone.querySelectorAll(".luna-print-controls").forEach(node=>node.remove());

    const expandAllPrintDetails=()=>{{
      clone.querySelectorAll("details").forEach(detail=>{{
        detail.open=true;
        detail.setAttribute("open","");
      }});
    }};

    expandAllPrintDetails();
    window.requestAnimationFrame(expandAllPrintDetails);

    printPortal.appendChild(clone);
    document.body.appendChild(printPortal);
    document.body.classList.add("luna-year-print-active");
    return printPortal;
  }}

  function prepare() {{
    createPortal();
  }}

  function restore() {{
    window.setTimeout(removePortal,0);
  }}

  if(paper)paper.addEventListener("change",settings);
  if(orientation)orientation.addEventListener("change",settings);
  window.addEventListener("beforeprint",prepare);
  window.addEventListener("afterprint",restore);

  if(printButton)printButton.addEventListener("click",async()=>{{
    createPortal();
    if(document.fonts&&document.fonts.ready){{
      await document.fonts.ready;
    }}
    window.setTimeout(()=>window.print(),180);
  }});

  settings();
}})();
</script>
    """


def render_yearly_experience(
    result: dict,
    *,
    show_print: bool = True,
    order_reference: str = "",
    default_paper: str = "A4",
    default_orientation: str = "portrait",
) -> None:
    import streamlit as st

    st.html(
        build_yearly_experience_html(
            result,
            show_print=show_print,
            order_reference=order_reference,
            default_paper=default_paper,
            default_orientation=default_orientation,
        ),
        unsafe_allow_javascript=True,
    )
