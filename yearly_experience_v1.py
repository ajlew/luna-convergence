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
from luna_voice import narrator_cue


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


def _game_map(result: dict) -> dict:
    return dict(result.get("yearly_game_map") or {})


def _hook(result: dict) -> str:
    game_map = _game_map(result)
    if game_map.get("headline"):
        return str(game_map["headline"])
    first, second = _top_houses(result)
    pair = frozenset({first, second})
    if pair == frozenset({5, 9}):
        return "Your world gets bigger. Your standards get sharper."
    if pair == frozenset({3, 5}):
        return "Your voice gets louder. Desire gets clearer."
    if pair == frozenset({7, 10}):
        return "Love and ambition renegotiate the terms"
    return YEARLY_HOOKS[first]


def _luna_says(result: dict) -> tuple[str, ...]:
    game_map = _game_map(result)
    paragraphs = tuple(str(item) for item in (game_map.get("narrator_paragraphs") or ()) if str(item).strip())
    if paragraphs:
        return paragraphs
    first, second = _top_houses(result)
    year = str(result.get("label", "This year"))
    return (
        f"{year} expands {HOUSE_NATURAL[first]} and tests {HOUSE_NATURAL[second]}. "
        "Romance may arrive loudly or stay quiet while validation comes through attention, work or visibility.",
        "Notice what opens. Then choose what proves it can support your future.",
    )


def _romance(result: dict) -> tuple[str, str]:
    game_map = _game_map(result)
    relationship_arc = tuple(str(item) for item in (game_map.get("relationship_arc") or ()) if str(item).strip())
    if relationship_arc:
        active = " ".join(relationship_arc[:2])
        quiet = relationship_arc[-1] + " If romance stays quiet, apply the same test to friendship, visibility and approval."
        return active, quiet
    first, second = _top_houses(result)
    houses = {first, second}
    active = (
        "If romance is active, attraction grows through shared direction. Watch for intention, effort and the ability to plan beyond the first spark."
        if houses & {5, 7, 8, 11}
        else "If someone shows interest, judge whether their behaviour matches your standards and the future you are building."
    )
    quiet = (
        "If romance stays quiet, validation may arrive through work, creativity, friendship or public recognition. Let it strengthen your choices—not replace them."
    )
    return active, quiet


def _chapter_cards(result: dict) -> str:
    return "".join(
        f"""
<article class="luna-year-chapter">
  <span>{_safe(chapter.get('name'))}</span>
  <h3>{_safe(chapter.get('strategic_question'))}</h3>
  <p>{_safe(chapter.get('focus_direction'))}</p>
  <small>{_safe(human_date_range(chapter.get('start_date'), chapter.get('end_date')))}</small>
</article>
        """
        for chapter in (result.get("solar_year_chapters") or [])
    )


def _game_cards(result: dict) -> str:
    cards = []
    for index, game in enumerate((_game_map(result).get("games") or [])[:3], 1):
        cards.append(
            f"""
<article class="luna-game-card">
  <span>Game {index}</span>
  <h3>{_safe(game.get('title'))}</h3>
  <p>{_safe(game.get('question'))}</p>
  <dl>
    <dt>Your leverage</dt><dd>{_safe(game.get('advantage'))}</dd>
    <dt>Main risk</dt><dd>{_safe(game.get('risk'))}</dd>
  </dl>
</article>
            """
        )
    return "".join(cards)


def _player_cards(result: dict) -> str:
    return "".join(
        f"""
<article class="luna-player-card">
  <span>{_safe(item.get('planet'))}</span>
  <strong>{_safe(item.get('role'))}</strong>
  <p>Houses {_safe(', '.join(map(str, item.get('houses') or [])))}</p>
</article>
        """
        for item in (_game_map(result).get("players") or [])[:7]
    )


def _act_cards(result: dict) -> str:
    return "".join(
        f"""
<article class="luna-year-act">
  <div class="luna-year-act-meta">
    <span>{_safe(item.get('name'))} / {_safe(item.get('role'))}</span>
    <small>{_safe(human_date_range(item.get('start_date'), item.get('end_date')))}</small>
  </div>
  <div>
    <h3>{_safe(item.get('dominant_game'))}</h3>
    <p>{_safe(item.get('summary'))}</p>
    <small>Rule change: {_safe(item.get('trigger'))}</small>
  </div>
</article>
        """
        for item in (_game_map(result).get("acts") or [])
    )


def _round_cards(result: dict) -> str:
    return "".join(
        f"""
<article class="luna-round-card">
  <div class="luna-round-meta"><span>{_safe(item.get('month'))}</span><small>{_safe(item.get('role'))}</small></div>
  <h3>{_safe(item.get('headline'))}</h3>
  <p>{_safe(item.get('central_storyline'))}</p>
  <div class="luna-round-footer"><strong>{_safe(item.get('dominant_game'))}</strong><span>{_safe(item.get('key_window'))}</span></div>
</article>
        """
        for item in (_game_map(result).get("rounds") or [])
    )


def _annual_arc_section(result: dict, key: str, title: str) -> str:
    values = tuple(str(item) for item in (_game_map(result).get(key) or ()) if str(item).strip())
    if not values:
        return ""
    return f"""
<article class="luna-domain-arc">
  <span>{_safe(title)}</span>
  {_paragraphs(values)}
</article>
    """


def _moves(result: dict) -> list[str]:
    game_map = _game_map(result)
    games = game_map.get("games") or []
    values = []
    if games:
        values.append(str(games[0].get("do_line", "Back what proves itself.")))
    acts = game_map.get("acts") or []
    if acts:
        values.append("Use the strongest rule change to revise the plan, not repeat the old position.")
    values.append("End the year with fewer options and more leverage.")
    return values[:3]


def _timing_cards(result: dict) -> str:
    game_map = _game_map(result)
    rounds = game_map.get("rounds") or []
    if rounds:
        return "".join(
            f"""
<article class="luna-date-card">
  <span>{_safe(item.get('month'))}</span>
  <strong>{_safe(item.get('role'))}: {_safe(item.get('headline'))}</strong>
  <p>{_safe(item.get('key_window'))}</p>
</article>
            """
            for item in rounds
        )
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


def _game_rows(result: dict) -> str:
    return "".join(
        "<tr>"
        f"<td>{_safe(item.get('title'))}</td>"
        f"<td>{float(item.get('score', 0.0)):.1f}</td>"
        f"<td>{_safe(', '.join(item.get('evidence_months') or []))}</td>"
        "</tr>"
        for item in (_game_map(result).get("games") or [])
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


def _paragraphs(values: tuple[str, ...] | list[str]) -> str:
    return "".join(f"<p>{_safe(value)}</p>" for value in values if value)


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
    game_map = _game_map(result)
    active, quiet = _romance(result)
    moves = _moves(result)
    games = game_map.get("games") or []
    if games:
        do_line = str(games[0].get("do_line", "Back what proves itself."))
        dont_line = str(games[0].get("dont_line", "Mistake possibility for position."))
    else:
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

.luna-yearly-report p strong { font-weight:inherit; font-size:inherit; line-height:inherit; }
.luna-year-prose p { max-width:760px; margin-bottom:1.3rem; line-height:1.72; }

.luna-year-hero {{ display:grid; gap:.85rem; padding:clamp(1.15rem,2.8vw,2rem); background:#050505; color:#fff; min-height:0!important; }}
.luna-year-meta {{ display:flex; justify-content:space-between; gap:1rem; padding-bottom:.8rem; border-bottom:1px solid rgba(255,255,255,.28); font-family:"IBM Plex Mono",monospace; font-size:.65rem; text-transform:uppercase; }}
.luna-year-hero h1 {{ max-width:760px; margin:.45rem 0 .3rem; color:#fff; font-size:clamp(2.45rem,5.5vw,4.45rem); line-height:.95; }}
.luna-eyebrow,.luna-year-chapter span,.luna-romance-grid span,.luna-game-card>span,.luna-domain-arc>span,.luna-player-card>span {{ font-family:"IBM Plex Mono",monospace; font-size:.65rem; text-transform:uppercase; letter-spacing:.05em; }}
.luna-year-theme {{ display:grid; grid-template-columns:auto 1fr; gap:.7rem; align-items:baseline; color:rgba(255,255,255,.8); }}
.luna-year-theme span {{ font-family:"IBM Plex Mono",monospace; font-size:.65rem; text-transform:uppercase; letter-spacing:.05em; }}
.luna-year-theme strong {{ font-size:.95rem; font-weight:400; line-height:1.35; }}
.luna-year-prose {{ max-width:780px; }}
.luna-year-prose p {{ font-size:clamp(1.02rem,1.45vw,1.17rem); line-height:1.66; }}
.luna-do-dont {{ display:grid; grid-template-columns:1fr 1fr; margin-top:1.2rem; }}
.luna-do-dont div {{ padding:.8rem .8rem 0 0; }}
.luna-do-dont div+div {{ border-left:1px solid #050505; padding-left:.8rem; }}
.luna-do-dont span {{ display:block; color:#696963; font-family:"IBM Plex Mono",monospace; font-size:.63rem; text-transform:uppercase; }}
.luna-do-dont strong {{ font-family:"Bodoni Moda",Georgia,serif; font-size:clamp(1.15rem,2vw,1.55rem); }}
.luna-do-dont-light {{ border-top:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-section {{ padding:clamp(2.4rem,6vw,5rem) clamp(1rem,4vw,3.2rem); border-bottom:1px solid #050505; }}
.luna-section-title {{ max-width:760px; margin:.45rem 0 1.3rem; font-size:clamp(2.15rem,4.8vw,4rem); line-height:.98; }}
.luna-game-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-game-card {{ padding:1rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-game-card h3 {{ margin:.5rem 0; font-size:clamp(1.55rem,2.5vw,2.2rem); line-height:1.02; }}
.luna-game-card dl {{ margin:1rem 0 0; }}
.luna-game-card dt {{ font-family:"IBM Plex Mono",monospace; font-size:.62rem; text-transform:uppercase; margin-top:.7rem; }}
.luna-game-card dd {{ margin:.25rem 0 0; line-height:1.45; }}
.luna-act-timeline {{ border-top:1px solid #050505; }}
.luna-year-act {{ display:grid; grid-template-columns:minmax(9rem,.35fr) minmax(0,1fr); gap:clamp(1rem,4vw,3rem); padding:1.4rem 0; border-bottom:1px solid #050505; }}
.luna-year-act-meta {{ display:flex; flex-direction:column; gap:.45rem; font-family:"IBM Plex Mono",monospace; font-size:.65rem; text-transform:uppercase; }}
.luna-year-act h3 {{ margin:0 0 .5rem; font-size:clamp(1.7rem,3vw,2.55rem); }}
.luna-round-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-round-card {{ padding:1rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-round-meta,.luna-round-footer {{ display:flex; justify-content:space-between; gap:1rem; font-family:"IBM Plex Mono",monospace; font-size:.62rem; text-transform:uppercase; }}
.luna-round-card h3 {{ margin:.65rem 0; font-size:clamp(1.45rem,2.4vw,2.05rem); }}
.luna-round-footer {{ margin-top:1rem; padding-top:.7rem; border-top:1px solid #d8d8d3; }}
.luna-domain-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-domain-arc {{ padding:1rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-domain-arc p {{ margin:.7rem 0; }}
.luna-player-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }}
.luna-player-card {{ padding:.9rem; border-right:1px solid #050505; border-bottom:1px solid #050505; }}
.luna-player-card strong {{ display:block; margin:.35rem 0; }}
.luna-method-note {{ color:#696963; font-size:.82rem!important; }}
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
.luna-print-controls {{ position:static; display:flex; align-items:end; gap:.75rem; padding:.75rem; background:rgba(255,255,255,.97); border:1px solid #050505; }}
.luna-print-controls div {{ display:flex; flex-direction:column; gap:.2rem; }}
.luna-print-controls label {{ font-family:"IBM Plex Mono",monospace; font-size:.6rem; text-transform:uppercase; }}
.luna-print-controls select,.luna-print-controls button {{ min-height:2.5rem; border:1px solid #050505; padding:.45rem .6rem; }}
.luna-print-controls button {{ background:#050505; color:#fff; font-family:"IBM Plex Mono",monospace; text-transform:uppercase; }}
.luna-print-check {{ margin-left:auto; }}
@media(max-width:720px) {{
  .luna-year-meta,.luna-year-theme,.luna-do-dont,.luna-game-grid,.luna-year-grid,.luna-romance-grid,.luna-next-move,.luna-date-grid,.luna-round-grid,.luna-domain-grid,.luna-player-grid,.luna-year-act {{ grid-template-columns:1fr; flex-direction:column; }}
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
  .luna-year-chapter,.luna-romance-grid article,.luna-date-card,.luna-game-card,.luna-year-act,.luna-round-card,.luna-domain-arc,.luna-player-card {{ break-inside:avoid; page-break-inside:avoid; }}
  .luna-yearly-report[data-print-orientation="portrait"] .luna-year-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-game-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-romance-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-date-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-round-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-domain-grid,
  .luna-yearly-report[data-print-orientation="portrait"] .luna-player-grid,
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
    <div class="luna-year-theme"><span>The year's game</span><strong>{_safe(game_map.get('central_storyline', 'The long game becomes visible.'))}</strong></div>
  </section>

  <section class="luna-section luna-year-opening">
    <div class="luna-eyebrow">{_safe(narrator_cue('yearly', 0))}</div>
    <div class="luna-year-prose">{_paragraphs(_luna_says(result))}</div>
    <div class="luna-do-dont luna-do-dont-light">
      <div><span>{_safe(DO_LABEL)}</span><strong>{_safe(do_line)}</strong></div>
      <div><span>{_safe(DONT_LABEL)}</span><strong>{_safe(dont_line)}</strong></div>
    </div>
  </section>

  <section class="luna-section">
    <div class="luna-eyebrow">The year's game board</div>
    <h2 class="luna-section-title">Three games organise the year</h2>
    <div class="luna-game-grid">{_game_cards(result)}</div>
  </section>

  <section class="luna-section">
    <div class="luna-eyebrow">How the rules change</div>
    <div class="luna-act-timeline">{_act_cards(result)}</div>
  </section>

  <section class="luna-section luna-rounds-section">
    <div class="luna-eyebrow">The year in twelve moves</div>
    <h2 class="luna-section-title">Each month changes the options available next</h2>
    <div class="luna-round-grid">{_round_cards(result)}</div>
  </section>

  <section class="luna-section">
    <div class="luna-eyebrow">Love / work / money / home</div>
    <div class="luna-domain-grid">
      {_annual_arc_section(result, 'relationship_arc', 'Relationship game')}
      {_annual_arc_section(result, 'career_arc', 'Career game')}
      {_annual_arc_section(result, 'money_arc', 'Money game')}
      {_annual_arc_section(result, 'home_arc', 'Home game')}
    </div>
  </section>

  <section class="luna-section luna-romance-section">
    <div class="luna-eyebrow">Romance and validation</div>
    <h2 class="luna-section-title">Whether attention becomes consistent—or stays entertaining</h2>
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
    <details><summary>{_safe(WHY_LUNA_LABEL)} <span>+</span></summary><div class="luna-detail">
      <p>{_safe(game_map.get('central_storyline', 'The annual structure is built from repeated convergences.'))}</p>
      <p><strong>Equation:</strong> {_safe(game_map.get('equation', 'Players + board + rounds = yearly game'))}</p>
      <div class="luna-game-grid">{_game_cards(result)}</div>
    </div></details>
    <details><summary>Annual players and leverage <span>+</span></summary><div class="luna-detail"><div class="luna-player-grid">{_player_cards(result)}</div></div></details>
    <details><summary>{_safe(SOLAR_LABEL)} <span>+</span></summary><div class="luna-detail"><div class="luna-year-grid">{_chapter_cards(result)}</div></div></details>
    <details><summary>{_safe(TIMING_LABEL)} <span>+</span></summary><div class="luna-detail"><div class="luna-date-grid">{_timing_cards(result)}</div></div></details>
    <details><summary>{_safe(TECHNICAL_LABEL)} <span>+</span></summary><div class="luna-detail">
      <h3>Annual game scores</h3>
      <div class="luna-table-wrap"><table><thead><tr><th>Game</th><th>Score</th><th>Evidence months</th></tr></thead><tbody>{_game_rows(result)}</tbody></table></div>
      <h3>Dominant houses</h3>
      <div class="luna-table-wrap"><table><thead><tr><th>House</th><th>Life area</th><th>Weight</th></tr></thead><tbody>{_technical_rows(result)}</tbody></table></div>
      <p class="luna-method-note">Game scores rank symbolic concentration inside this report. They are not measured probabilities or guarantees.</p>
    </div></details>
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
