"""Print-focused HTML for the same Year Ahead packet and editorial as the web report.

No new sky calculations, model calls or report text generation occur here.
"""
from __future__ import annotations
from datetime import date
from html import escape
from typing import Any


def e(x: Any) -> str:
    return escape(str(x if x is not None else ''))


def d(x: Any) -> str:
    try: return date.fromisoformat(str(x)[:10]).strftime('%-d %B %Y')
    except Exception: return str(x or '')


def _strips(packet: dict) -> str:
    games = [g for g in packet.get('games', []) if isinstance(g, dict)]
    start = date.fromisoformat(str(packet['period']['start'])[:10]); end = date.fromisoformat(str(packet['period']['end'])[:10])
    span = max((end-start).days, 1)
    parts=[]
    for g in games:
        a=date.fromisoformat(str(g.get('start_date') or start)[:10]); b=date.fromisoformat(str(g.get('end_date') or end)[:10])
        left=max(0,min(100,100*(a-start).days/span)); right=max(left,min(100,100*(b-start).days/span))
        title=g.get('title') or str(g.get('human_life_area') or 'A major story')
        area_label = e(str(g.get('human_life_area') or 'A major story'))
        parts.append(f'<div class="lane"><div><strong>{e(str(title).title())}</strong><small>{area_label}</small></div><div class="track"><span style="left:{left:.1f}%;width:{max(1,right-left):.1f}%"></span></div></div>')
    return ''.join(parts)


def smooth_wave_path(points: list[tuple[float, float]]) -> str:
    """Cubic curve passing through every calculated month sample, without new peaks."""
    if not points:
        return ""
    output = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for (x1,y1),(x2,y2) in zip(points,points[1:]):
        dx=(x2-x1)/3
        output.append(
            f"C {x1+dx:.2f} {y1:.2f} {x2-dx:.2f} {y2:.2f} {x2:.2f} {y2:.2f}"
        )
    return " ".join(output)


def _wave(packet: dict) -> str:
    rows=[r for r in packet.get('year_strip', []) if isinstance(r,dict)]
    if not rows: return ''
    n=len(rows); vals=[max(0,min(1,float(r.get('intensity') or 0))) for r in rows]
    # Smoothed, linear segments between actual calculated monthly concentration samples.
    xy=[(35+i* (730/max(1,n-1)),105-78*v) for i,v in enumerate(vals)]
    path=smooth_wave_path(xy)
    labels=''.join(f'<text x="{x:.1f}" y="128" text-anchor="middle">{e(str(r.get("month") or ""))}</text>' for (x,_),r in zip(xy,rows))
    circles=''.join(f'<circle class="rhythm-dot" cx="{x:.1f}" cy="{y:.1f}" r="3" />' for x,y in xy)
    return f'<svg viewBox="0 0 800 145" role="img" aria-label="Monthly activity concentration based on calculated selected transits"><line x1="35" y1="105" x2="765" y2="105" stroke="#ddd"/><path d="{path}" fill="none" stroke="#151515" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>{circles}{labels}</svg>'


def _iso_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def _active_transits(game: dict, start: object, end: object) -> list[dict]:
    a, b = _iso_date(start), _iso_date(end)
    if a is None or b is None:
        return []
    candidates = [game.get("primary_transit")] + list(game.get("supporting_transits") or [])
    selected = []
    for transit in candidates:
        if not isinstance(transit, dict):
            continue
        transit_start = _iso_date(transit.get("start"))
        transit_end = _iso_date(transit.get("end"))
        if transit_start is not None and transit_end is not None and transit_start <= b and transit_end >= a:
            selected.append(transit)
    return selected


def _transit_timeline(round_: dict, game: dict) -> str:
    """Show only contacts overlapping this rolling month; never infer dates."""
    a = _iso_date(round_.get("start")); b = _iso_date(round_.get("end"))
    if a is None or b is None:
        return ""
    rows = _active_transits(game, a, b)
    if not rows:
        return '<p class="quiet">No major selected personal transit is active in this chapter.</p>'
    width = 760; label_width = 220; chart_left = 230; chart_width = 510
    span = max(1, (b-a).days)
    height = 58 + 45*len(rows)
    svg = [f'<svg class="month-timeline" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Calculated personal transit windows and exact dates">']
    svg.append(f'<text x="{chart_left}" y="18">{e(a.strftime("%d %b"))}</text>')
    svg.append(f'<text x="{chart_left+chart_width}" y="18" text-anchor="end">{e(b.strftime("%d %b %Y"))}</text>')
    for i, transit in enumerate(rows):
        y = 43+45*i
        name = str(transit.get('technical_label') or 'Calculated transit')
        t_start = _iso_date(transit.get('start')) or a
        t_end = _iso_date(transit.get('end')) or b
        left = chart_left+chart_width*max(0,(max(a,t_start)-a).days)/span
        right = chart_left+chart_width*min(span,(min(b,t_end)-a).days)/span
        svg.append(f'<text x="0" y="{y+5}">{e(name[:37])}</text>')
        svg.append(f'<rect x="{chart_left}" y="{y-7}" width="{chart_width}" height="14" rx="5" fill="#f0efed"/>')
        svg.append(f'<rect x="{left:.1f}" y="{y-3}" width="{max(3,right-left):.1f}" height="6" rx="3" fill="#333"/>')
        for hit in transit.get('passes') or []:
            if not isinstance(hit,dict):continue
            hit_day = _iso_date(hit.get('date'))
            if hit_day is None or not a <= hit_day <= b:continue
            x = chart_left+chart_width*(hit_day-a).days/span
            label=str(hit.get('pass_label') or 'Exact')
            svg.append(f'<circle cx="{x:.1f}" cy="{y}" r="5" fill="#0f0f0f"><title>{e(label)} · {e(d(hit_day))}</title></circle>')
    svg.append('</svg>')
    return ''.join(svg)


def _month_activation_svg(snapshot: Any, transits: list[dict]) -> str:
    """A per-month activation map from stored transit targets, never guessed events.

    Violet = natal target longitude; orange = transiting position at a recorded
    exact contact if present. The diagram stays empty if no exact pass is in
    this month, rather than inventing sky positions.
    """
    from math import cos, sin, radians
    if not transits:
        return '<p class="quiet">No selected personal activation in this period.</p>'
    natal = {str(p.planet).casefold(): p for p in (getattr(snapshot, 'positions', ()) or ())}
    for key, item in [('ascendant', getattr(snapshot, 'ascendant', None)), ('midheaven', getattr(snapshot, 'midheaven', None))]:
        if item is not None: natal[key] = item
    cx=cy=155; outer=125; inner=86
    def pt(deg: float, r: float):
        a=radians(deg-90)
        return cx+r*cos(a),cy+r*sin(a)
    out=['<svg class="activation-wheel" viewBox="0 0 310 310" role="img" aria-label="Calculated natal targets contacted by selected transits">',
         f'<circle cx="{cx}" cy="{cy}" r="{outer}" fill="none" stroke="#b6b6b6"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{inner}" fill="none" stroke="#dddddd"/>']
    for index in range(12):
        x1,y1=pt(index*30,inner);x2,y2=pt(index*30,outer)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#dddddd"/>')
    rows=[]; used=set()
    for t in transits:
        label=str(t.get('technical_label') or '')
        target=str(t.get('natal_target') or '').strip()
        if not target:
            for key in natal:
                if ('natal '+key) in label.casefold(): target=key; break
        key=target.casefold().replace('natal ','')
        n=natal.get(key)
        if n is None: continue
        ident=(label,key)
        if ident in used:continue
        used.add(ident)
        x,y=pt(float(n.longitude)%360,outer-14)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#725aca" stroke="white" stroke-width="1"/>')
        # Longitude at the exact pass is available in some packets; do not
        # manufacture a transiting position when that field is absent.
        hit=next((v for v in (t.get('passes') or []) if isinstance(v,dict) and v.get('transit_longitude') is not None),None)
        if hit is not None:
            tx,ty=pt(float(hit['transit_longitude'])%360,outer+5)
            out.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#8f80ce" stroke-width="1.5"/>')
            out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="5" fill="#e58b40"/>')
        rows.append(f'<li>{e(label)} → natal {e(target)}</li>')
    out.append('</svg>')
    if not rows:
        return '<p class="quiet">No natal targets available to plot for the selected contacts.</p>'
    return '<div class="activation-layout"><div>'+''.join(out)+'</div><div><p class="quiet">Purple markers identify the natal points contacted in this chapter. Orange markers appear only when an exact transiting longitude is supplied.</p><ul class="activation-contacts">'+''.join(rows)+'</ul></div></div>'


def _evidence_appendix(games: list[dict]) -> str:
    key_dates: list[tuple[str,str]] = []
    detail: list[str] = []
    for number, game in enumerate(games, 1):
        title = str(game.get('title') or f'Major story {number}')
        detail.append(f'<article class="evidence-group"><h3>{e(title.title())}</h3>')
        all_transits = [game.get('primary_transit')] + list(game.get('supporting_transits') or [])
        for transit in all_transits:
            if not isinstance(transit,dict):continue
            name=str(transit.get('technical_label') or 'Calculated transit')
            target=str(transit.get('natal_target') or '')
            detail.append(f'<div class="transit-fact"><b>{e(name)}</b> · Natal target: {e(target)}'
                          f' · {e(d(transit.get("start")))} – {e(d(transit.get("end")))}')
            for hit in transit.get('passes') or []:
                if not isinstance(hit,dict):continue
                date_raw=str(hit.get('date') or '')[:10]
                if not date_raw:continue
                text=f'{name} · {hit.get("pass_label") or "Exact contact"}'
                key_dates.append((date_raw,text))
                orb=hit.get('orb')
                orb_text = f' · {float(orb):.2f}° orb' if orb is not None else ''
                detail.append(f'<div class="smallfact">{e(d(date_raw))} {e(hit.get("time") or "")} · '
                              f'{e(hit.get("pass_label") or "Exact contact")}'
                              f' · {"Retrograde" if hit.get("retrograde") else "Direct"}{e(orb_text)}</div>')
            detail.append('</div>')
        for trigger in (game.get('primary_transit') or {}).get('triggers') or []:
            if isinstance(trigger,dict) and trigger.get('date'):
                key_dates.append((str(trigger['date'])[:10],str(trigger.get('activation_label') or trigger.get('technical_label') or 'Supporting trigger')))
        detail.append('</article>')
    unique = sorted(set(key_dates))
    events = ''.join(f'<div class="keydate"><b>{e(d(raw))}</b><span>{e(label)}</span></div>' for raw,label in unique)
    return (f'<section class="page"><div class="eyebrow">Reference</div><h2>Key dates</h2>'
            f'<p>A chronological guide to the calculated exact contacts and supporting triggers.</p>'
            f'<div class="keydates">{events}</div></section>'
            f'<section class="page"><div class="eyebrow">Explainable evidence</div>'
            f'<h2>Why Luna sees this</h2><p>The dates and technical positions come from the calculation layer. '
            f'They are not predictions of specific life events.</p>{"".join(detail)}</section>')


def build_yearly_print_html(*, snapshot: Any, packet: dict, editorial: Any, label: str, main_focus: str = '', personal_question: str = '', order_reference: str = '') -> str:
    from monthly_report_pdf_home_v3 import FONT_IMPORT, _font_face_css
    from natal_snapshot import natal_wheel_svg
    games=[g for g in packet.get('games',[]) if isinstance(g,dict)]
    rounds=[r for r in packet.get('monthly_rounds',[]) if isinstance(r,dict)]
    game_by_number={int(g.get('number') or 0):g for g in games}
    months=[]
    for round_ in rounds:
        number=int(round_.get('number') or len(months)+1)
        focus_voice=editorial.month_for(number) if editorial and hasattr(editorial,'month_for') else None
        g=game_by_number.get(int(round_.get('dominant_game_number') or 0),{})
        months.append({
            'month':str(round_.get('label') or ''),
            'phase':str(round_.get('phase') or 'Quieter ground').replace('_',' ').title(),
            'story':str(g.get('human_life_area') or 'Quieter ground').title(),
            'focus':str(getattr(focus_voice,'focus','') or round_.get('focus') or ''),
            'strongest':str(round_.get('strongest_date') or '')+' · '+str(round_.get('strongest_label') or round_.get('strongest_kind') or 'Calculated contact') if round_.get('strongest_date') else '',
        })
    def para(xs): return ''.join(f'<p>{e(s)}</p>' for s in (xs or []) if str(s).strip())
    try: chart=natal_wheel_svg(snapshot,size=760)
    except Exception: chart=''
    if not chart: raise ValueError('Year Ahead print export requires its natal chart; no PDF generated without it')
    positions={str(getattr(p,'planet','')):str(getattr(p,'sign','')) for p in (getattr(snapshot,'positions',()) or ())}
    signature=''.join(f'<div><span>{name}</span><strong>{e(value)}</strong></div>' for name,value in [('Sun',positions.get('Sun','Not calculated')),('Moon',positions.get('Moon','Not calculated')),('Rising',getattr(getattr(snapshot,'ascendant',None),'sign','Not calculated'))])
    # Snapshot attributes vary between versions; use documented dict/signatures where available.
    strengths=''
    for s in list(getattr(snapshot,'signatures',()) or ())[:6]:
        strengths+=f'<article class="block"><h3>{e(getattr(s,"title", ""))}</h3><p>{e(getattr(s,"text",""))}</p></article>'
    month_cards=[]
    for i, row in enumerate(months):
        round_ = rounds[i] if i < len(rounds) else {}
        focused = game_by_number.get(int(round_.get('dominant_game_number') or 0), {})
        theme = str(focused.get('title') or 'A quieter chapter')
        transit_rows = _active_transits(focused, round_.get('start'), round_.get('end'))
        contacts = ''.join(
            f'<li><strong>{e(t.get("technical_label") or "Personal transit")}</strong> '
            f'<span class="quiet">{e(d(t.get("start")))} – {e(d(t.get("end")))}</span></li>'
            for t in transit_rows
        )
        month_cards.append(
            f'<section class="month page"><div class="eyebrow">Month {i+1:02d} / {e(row["month"])}</div>'
            f'<h2>{e(theme.title())}</h2><p class="meta">{e(row["phase"])} · {e(row["story"])}</p>'
            f'<h3>Luna’s focus</h3><p>{e(row["focus"])}</p>'
            + (f'<div class="callout"><strong>Key moment</strong><p>{e(row["strongest"])}</p></div>'
                if row.get('strongest') else '')
            + (f'<h3>Personal transits this period</h3>{_transit_timeline(round_,focused)}'
               f'<ul class="contacts">{contacts}</ul>' if focused else
               '<p class="quiet">A quieter period to consolidate what is already underway.</p>')
            + (f'<h3>Your natal activation</h3>{_month_activation_svg(snapshot, transit_rows)}' if focused else '')
            + '<p class="quiet">For the complete pass-by-pass interpretation, see the relevant major story below.</p>'
            + '</section>'
        )
    issue_cards=[]
    for i,g in enumerate(games):
        voice=editorial.issue_for(int(g.get('number') or i+1)) if editorial is not None and hasattr(editorial,'issue_for') else None
        # Facts are sourced from original game packet; no invented passes.
        primary=g.get('primary_transit') or {}
        passes=primary.get('passes') or []
        evidence=''.join(f'<li>{e(d(hit.get("date")))} · {e(hit.get("pass_label") or hit.get("stage") or "Exact contact")}</li>' for hit in passes if isinstance(hit,dict))
        paragraphs=[]
        if voice is not None:
            paragraphs.extend(list(getattr(voice, 'paragraphs', ()) or ()))
            for attr in ('what_is_changing','what_it_looks_like','what_can_trip_you_up','your_move'):
                v=getattr(voice,attr,None)
                if isinstance(v,str) and v.strip(): paragraphs.append(v)
        title=g.get('title') or f'Major story {i+1}'
        issue_cards.append(f'<section class="issue page"><div class="eyebrow">Major story {i+1:02d}</div><h2>{e(title.title())}</h2>{para(paragraphs)}<h3>Timing and evidence</h3><p>{e(primary.get("technical_label") or primary.get("label") or primary.get("name") or "")}</p><ul>{evidence}</ul></section>')
    appendix = _evidence_appendix(games)
    closing=para(getattr(editorial,'closing',()) or ())
    css='''
@page {size:A4;margin:17mm 17mm 18mm}
*{box-sizing:border-box}body{font-family:'Josefin Sans',Arial,sans-serif;color:#141414;font-size:11pt;line-height:1.48;margin:0}
h1,h2{font-family:'Bodoni Moda',Georgia,serif;font-weight:500;line-height:1.15}h1{font-size:33pt;margin:0 0 10mm}h2{font-size:25pt;margin:0 0 5mm}h3{font-size:12pt;margin:6mm 0 2mm}p{margin:0 0 4mm}small,.quiet{color:#666}.eyebrow{font-size:8pt;text-transform:uppercase;letter-spacing:.12em;font-weight:700;margin-bottom:9mm}
.page{break-before:page}.cover{padding-top:16mm}.deck{font-size:13pt;max-width:160mm}.meta{color:#555}.block,.callout,.lane,.natal-svg,.signature{break-inside:avoid}.signature{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:7mm 0}.signature>div,.callout{padding:4mm;border:1px solid #ddd}.signature span{display:block;font-size:8pt;text-transform:uppercase}.signature strong{display:block;margin-top:2mm}.natal-svg{width:100%;height:108mm;break-before:page;break-inside:avoid;text-align:center;padding-top:4mm}.natal-svg svg{display:block;width:96mm!important;height:96mm!important;margin:0 auto}.divider{border-top:1px solid #aaa;margin:7mm 0}.lanes{margin:7mm 0}.lane{display:grid;grid-template-columns:44mm 1fr;gap:4mm;align-items:center;margin:4mm 0}.lane strong{font-size:9pt;display:block}.lane small{font-size:7pt;display:block}.track{height:12mm;background:#f3f3f3;border-radius:2mm;position:relative}.track span{position:absolute;top:5mm;height:2mm;background:#333;border-radius:2mm}svg text{font:9px Arial,sans-serif;fill:#777}.month-timeline circle,.rhythm-dot{fill:#111}.callout{background:#f6f5f3;margin:7mm 0}.month,.issue{padding-top:3mm}.month{min-height:120mm}footer{margin-top:10mm;border-top:1px solid #ddd;padding-top:3mm;font-size:8pt;color:#777}
@media screen{body{max-width:820px;margin:auto;padding:25px}.page{padding-top:30px;border-top:1px solid #ddd;margin-top:50px}}

.month-timeline{display:block;width:100%;height:auto;margin:4mm 0 3mm}
.month-timeline text{font:12px 'Josefin Sans',Arial,sans-serif;fill:#444}
.month-timeline circle{fill:#111}
.activation-layout{display:grid;grid-template-columns:105mm 1fr;gap:5mm;align-items:center;break-inside:avoid}.activation-wheel{display:block;width:100%;max-width:105mm;height:auto}.activation-contacts{font-size:8pt;padding-left:5mm}.activation-contacts li{margin-bottom:2mm}.contacts{font-size:9pt;padding-left:5mm}.contacts li{margin:2mm 0}
.evidence-group,.keydate{break-inside:avoid}
.keydate{display:grid;grid-template-columns:32mm 1fr;gap:5mm;padding:3mm 0;border-bottom:1px solid #ddd;font-size:9pt}
.transit-fact{padding:3mm 0;border-bottom:1px solid #eee;font-size:9pt}
.smallfact{margin-top:2mm;font-size:8pt;color:#555}
@media print{.page{break-before:page}.month,.issue{break-before:page}}
'''
    intro=f'<section class="cover"><div class="eyebrow">Luna Convergence · Your Year Ahead</div><h1>{e(getattr(editorial,"headline",None) or "Your Year Ahead")}</h1><p class="deck">{e(label)} · {e(getattr(editorial,"deck",None) or "")}</p><div class="divider"></div><p><b>Focus:</b> {e(main_focus)}</p><p class="quiet">{e(order_reference)}</p><h2>Your natal signature</h2><div class="signature">{signature}</div><div class="natal-svg">{chart}</div><h2>Your strengths</h2>{strengths}</section>'
    overview=f'<section class="page"><div class="eyebrow">The big picture</div><h2>Read the year</h2>{para(getattr(editorial,"read_year",()) or ())}<h2>How your year unfolds</h2><p>Your year has several overlapping stories. These bars show when each one comes into focus, while the wave shows when the selected transits become more active or leave room to breathe. A higher point means more concentrated astrological activity, not a predicted outcome.</p><div class="lanes">{_strips(packet)}</div><h3>Your annual rhythm</h3>{_wave(packet)}</section>'
    outro=f'<section class="page"><h2>What the year leaves you with</h2>{closing}<h3>About this report</h3><p>Calculated planetary evidence is interpreted symbolically and is not professional advice.</p></section>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Luna Convergence · Your Year Ahead</title><style>{FONT_IMPORT}{_font_face_css()}{css}</style></head><body>{intro}{overview}{"".join(month_cards)}{"".join(issue_cards)}{outro}{appendix}</body></html>'


def render_yearly_html_pdf(html: str) -> bytes:
    from weasyprint import HTML
    result=HTML(string=html).write_pdf()
    if not result.startswith(b'%PDF') or len(result)<10000: raise RuntimeError('PDF rendering did not complete')
    return result
