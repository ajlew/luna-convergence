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


def _annual_timeline(packet: dict) -> str:
    """One date axis for selected Game activity, exact contacts and the aggregate.

    Each colour trace is derived from that Game's recorded transit windows and
    exact passes. No synthetic periodicity or forecast outcomes are introduced.
    """
    from datetime import timedelta
    from math import exp

    period = packet.get("period") or {}
    start, end = _iso_date(period.get("start")), _iso_date(period.get("end"))
    games = [g for g in packet.get("games", ()) if isinstance(g, dict)]
    if not start or not end or end <= start or not games:
        return ""

    days = (end - start).days
    x0, width = 196.0, 570.0
    samples = [start + timedelta(days=round(days * i / 180)) for i in range(181)]
    colors = ("#765577", "#51758a", "#a0783d", "#597762", "#8c5c50")
    def xpos(day):
        return x0 + width * max(0.0, min(1.0, (day - start).days / days))
    def transits(game):
        seen = set()
        for tr in [game.get("primary_transit"), *(game.get("supporting_transits") or ())]:
            if not isinstance(tr, dict):
                continue
            key = (str(tr.get("technical_label")), str(tr.get("start")), str(tr.get("end")))
            if key not in seen:
                seen.add(key)
                yield tr

    # Amplitude is based on exactly recorded passes and recorded active windows.
    # Each event is a distinct pulse; long-running aspects do not produce an
    # artificial constant-intensity plateau or a sine-wave cycle.
    activity, valid = [], []
    for game in games:
        records = []
        for tr in transits(game):
            a, b = _iso_date(tr.get("start")), _iso_date(tr.get("end"))
            if not a or not b or b < start or a > end or b < a:
                continue
            hits = []
            for hit in tr.get("passes") or ():
                dt = _iso_date(hit.get("date")) if isinstance(hit, dict) else None
                if dt and a <= dt <= b:
                    hits.append(dt)
            records.append((tr, a, b, hits))
        valid.append(records)
        intensity = []
        for day in samples:
            value = 0.0
            for _, a, b, hits in records:
                if a <= day <= b:
                    # Window shoulder is a secondary signal; exact passes
                    # dominate when present. Width follows window duration.
                    value += 0.13
                    sigma = max(5., min(27., (b-a).days / 9.))
                    for dt in hits:
                        value += exp(-0.5 * (((day-dt).days) / sigma) ** 2)
            intensity.append(value)
        activity.append(intensity)

    total = [sum(series[i] for series in activity) for i in range(len(samples))]
    max_total = max(total) if total else 0
    if max_total <= 0:
        return '<p class="quiet">No verified annual transit activity is available to plot.</p>'
    chart_height = 66 * len(games) + 142
    rows = []
    for i, game in enumerate(games):
        y = 42 + 66*i
        color = colors[i % len(colors)]
        title = str(game.get("title") or game.get("human_life_area") or f"Game {i+1}")
        rows.append(f'<text x="4" y="{y+12}" font-size="12" fill="#222">{e(title.title())}</text>')
        rows.append(f'<line x1="{x0}" y1="{y+37}" x2="{x0+width}" y2="{y+37}" stroke="#dedede"/>')
        for _, a, b, hits in valid[i]:
            xa, xb = xpos(max(start,a)), xpos(min(end,b))
            rows.append(f'<line x1="{xa:.2f}" y1="{y+37}" x2="{xb:.2f}" y2="{y+37}" stroke="{color}" stroke-opacity=".28" stroke-width="7" stroke-linecap="round"/>')
        peak = max(activity[i]) or 1
        pts = [(xpos(day), y+34-26*v/peak) for day,v in zip(samples,activity[i])]
        rows.append(f'<path d="{smooth_wave_path(pts)}" fill="none" stroke="{color}" stroke-width="2.7" stroke-linecap="round"/>')
        for _,a,b,hits in valid[i]:
            for dt in hits:
                if start <= dt <= end:
                    j = min(range(len(samples)), key=lambda k: abs((samples[k]-dt).days))
                    yy = y+34-26*activity[i][j]/peak
                    rows.append(f'<circle cx="{xpos(dt):.2f}" cy="{yy:.2f}" r="3.2" fill="{color}"><title>{e(str(dt))}</title></circle>')

    y = 56+66*len(games)
    rows.append(f'<text x="4" y="{y+7}" font-size="12" fill="#222">Combined rhythm</text>')
    rows.append(f'<line x1="{x0}" y1="{y+83}" x2="{x0+width}" y2="{y+83}" stroke="#dedede"/>')
    pts=[(xpos(day), y+79-70*v/max_total) for day,v in zip(samples,total)]
    rows.append(f'<path d="{smooth_wave_path(pts)}" fill="none" stroke="#171717" stroke-width="3" stroke-linecap="round"/>')
    # Calendar ticks are calculated from dates, including partial first/last months.
    tick = date(start.year,start.month,1)
    while tick <= end:
        if tick >= start:
            x=xpos(tick)
            rows.append(f'<line x1="{x:.2f}" y1="27" x2="{x:.2f}" y2="{y+83}" stroke="#999" stroke-opacity=".13"/>')
            rows.append(f'<text x="{x:.2f}" y="22" font-size="9" text-anchor="middle">{tick.strftime("%b").upper()}</text>')
        tick = date(tick.year+1,1,1) if tick.month==12 else date(tick.year,tick.month+1,1)
    rows.append(f'<text x="{x0:.1f}" y="{y+99}" text-anchor="start" font-size="9">{e(d(start))}</text>')
    rows.append(f'<text x="{x0+width:.1f}" y="{y+99}" text-anchor="end" font-size="9">{e(d(end))}</text>')
    return (f'<svg class="annual-timeline" viewBox="0 0 790 {chart_height}" role="img" '
            f'aria-label="Calculated individual Game activity and combined rhythm on a shared date axis">'
            + ''.join(rows) + '</svg>')


def smooth_wave_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    output = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        dx = (x2-x1)/3
        output.append(f"C {x1+dx:.2f} {y1:.2f} {x2-dx:.2f} {y2:.2f} {x2:.2f} {y2:.2f}")
    return " ".join(output)


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
    width = 760; chart_left = 285; chart_width = 455
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
        svg.append(f'<text x="0" y="{y+5}" style="font-size:10px">{e(name[:46])}</text>')
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


def _month_activation_svg(snapshot: Any, transits: list[dict], start: Any = None, end: Any = None) -> str:
    """Labelled chart of computed natal targets and *verified* transit exact points.

    Chart never infers an ambiguous longitude from an aspect name. Passes are
    filtered to the chapter window. A natal target appears once even when
    multiple transits contact it; each contact has a distinct keyed legend.
    """
    from math import cos, sin, radians
    if not transits:
        return '<p class="quiet">No selected personal activation in this period.</p>'
    natal = {str(p.planet).casefold(): p for p in (getattr(snapshot, 'positions', ()) or ())}
    for key in ('ascendant', 'midheaven'):
        value = getattr(snapshot, key, None)
        if value is not None:
            natal[key] = value
    def point(deg, radius):
        angle = radians((float(deg) % 360) - 90)
        return (155 + radius*cos(angle), 155 + radius*sin(angle))
    out = ['<svg class="activation-wheel" viewBox="0 0 310 310" role="img" aria-label="Zodiac positions of natal targets and verified transiting contacts">',
           '<circle cx="155" cy="155" r="121" fill="none" stroke="#aaa"/>',
           '<circle cx="155" cy="155" r="84" fill="none" stroke="#d9d9d9"/>']
    zodiac = ('Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces')
    for i, sign in enumerate(zodiac):
        x1,y1=point(i*30,84); x2,y2=point(i*30,121)
        tx,ty=point(i*30+15,133)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ddd"/>')
        out.append(f'<text class="zodiac-label" x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle">{sign[:3]}</text>')
    begin,end_day=_iso_date(start),_iso_date(end)
    plotted=set(); contact_lines=[]; shown=set(); legend=[]
    for transit in transits:
        label=str(transit.get('technical_label') or 'Calculated transit')
        target=str(transit.get('natal_target') or '').strip()
        if not target:
            for name in natal:
                if 'natal '+name in label.casefold(): target=name;break
        key=target.casefold().replace('natal ','')
        n=natal.get(key)
        if n is None: continue
        longitude=float(n.longitude)%360
        if key not in plotted:
            plotted.add(key)
            x,y=point(longitude,103)
            # Short outward radial tick makes overlapping positions legible.
            out.append(f'<circle class="natal-marker" cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#725aca"/>')
            lx,ly=point(longitude,117)
            out.append(f'<text class="planet-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle">{e(key[:3].upper())}</text>')
        for hit in transit.get('passes') or []:
            if not isinstance(hit,dict): continue
            day=_iso_date(hit.get('date'))
            if begin and (day is None or day<begin): continue
            if end_day and (day is None or day>end_day): continue
            longitude_raw=hit.get('transit_longitude')
            if longitude_raw is None:
                longitude_raw=hit.get('transit_ecliptic_longitude')
            if longitude_raw is None:continue
            try: moving=float(longitude_raw)%360
            except (TypeError,ValueError):continue
            id_=(label,str(day),moving)
            if id_ in shown:continue
            shown.add(id_)
            tx,ty=point(moving,74);nx,ny=point(longitude,103)
            out.append(f'<line class="aspect-line" x1="{tx:.1f}" y1="{ty:.1f}" x2="{nx:.1f}" y2="{ny:.1f}"/>')
            out.append(f'<circle class="transit-marker" cx="{tx:.1f}" cy="{ty:.1f}" r="5" fill="#e58b40"/>')
            planet=label.split(' ',1)[0]
            legend.append(f'<li><strong>{e(planet)}</strong> → {e(target)} · {e(d(day))} (exact)</li>')
        if label not in contact_lines:contact_lines.append(label)
    out.append('<text class="chart-centre" x="155" y="151" text-anchor="middle">NATAL</text>')
    out.append('<text class="chart-centre-small" x="155" y="166" text-anchor="middle">ACTIVATIONS</text></svg>')
    if not plotted:
        return '<p class="quiet">No calculated natal target positions for this chapter.</p>'
    contacts=''.join(f'<li>{e(line)}</li>' for line in contact_lines)
    if legend:
        explanation='Purple: natal positions. Orange: verified exact transits within this chapter. Lines join the contacted natal point.'
    else:
        explanation='Purple: natal positions contacted during this chapter. Exact transit markers are omitted where no verified transit longitude was recorded.'
    exact_block = ('<p class="quiet">Verified exact contacts</p><ul class="activation-contacts">' + ''.join(legend) + '</ul>') if legend else ''
    return (f'<div class="activation-layout"><div>{"".join(out)}</div>'
            f'<div class="activation-description"><p class="quiet">{e(explanation)}</p>'
            f'<ul class="activation-contacts">{contacts}</ul>'
            + exact_block
            + '</div></div>')


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


def _month_editorial_parts(focus: str) -> tuple[str, str]:
    """Preserve model prose but display the possibility and the decision separately.

    The report must never invent events/dates to pad a short provider response.
    """
    import re
    text = " ".join(str(focus or "").split())
    if not text:
        return "", ""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text, maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return text, ""


def _yearly_editorial_date_warnings(editorial: Any, packet: dict) -> list[str]:
    """Flag hard-dated claims that lack support without silently changing source prose."""
    import re
    allowed = set()
    for game in packet.get('games', []):
        for tr in [game.get('primary_transit') or {}, *(game.get('supporting_transits') or [])]:
            for hit in tr.get('passes') or []:
                day = _iso_date(hit.get('date')) if isinstance(hit, dict) else None
                if day: allowed.add(day.isoformat())
    prose = list(getattr(editorial, 'read_year', ()) or ())
    for issue in getattr(editorial, 'issues', ()) or ():
        prose.extend(getattr(issue, 'paragraphs', ()) or ())
    warnings=[]
    for paragraph in prose:
        for literal in re.findall(r'\b(?:19|20)\d{2}-\d{2}-\d{2}\b', str(paragraph)):
            if literal not in allowed:
                warnings.append(literal)
    return sorted(set(warnings))


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
        scenario, decision = _month_editorial_parts(row['focus'])
        month_cards.append(
            f'<section class="month page"><div class="eyebrow">Month {i+1:02d} / {e(row["month"])}</div>'
            f'<h2>{e(theme.title())}</h2><p class="meta">{e(row["phase"])} · {e(row["story"].replace(" And "," and "))}</p>'
            f'<h3>What this month brings into focus</h3><p>{e(scenario)}</p>'
            + (f'<h3>Your decision</h3><p>{e(decision)}</p>' if decision else '')
            + (f'<div class="callout"><strong>Key moment</strong><p>{e(row["strongest"])}</p></div>'
                if row.get('strongest') else '')
            + (f'<h3>Personal transits this period</h3>{_transit_timeline(round_,focused)}'
               f'<ul class="contacts">{contacts}</ul>' if focused else
               '<p class="quiet">A quieter period to consolidate what is already underway.</p>')
            + (f'<h3>Your natal activation</h3>{_month_activation_svg(snapshot, transit_rows, round_.get("start"), round_.get("end"))}' if focused else '')
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
.page{break-before:page}.cover{padding-top:16mm}.deck{font-size:13pt;max-width:160mm}.meta{color:#555}.block,.callout,.lane,.natal-svg,.signature{break-inside:avoid}.signature{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:7mm 0}.signature>div,.callout{padding:4mm;border:1px solid #ddd}.signature span{display:block;font-size:8pt;text-transform:uppercase}.signature strong{display:block;margin-top:2mm}.natal-svg{width:100%;height:108mm;break-before:page;break-inside:avoid;text-align:center;padding-top:4mm}.natal-svg svg{display:block;width:96mm!important;height:96mm!important;margin:0 auto}.divider{border-top:1px solid #aaa;margin:7mm 0}.lanes{margin:7mm 0}.lane{display:grid;grid-template-columns:44mm 1fr;gap:4mm;align-items:center;margin:4mm 0}.lane strong{font-size:9pt;display:block}.lane small{font-size:7pt;display:block}.track{height:12mm;background:#f3f3f3;border-radius:2mm;position:relative}.track span{position:absolute;top:5mm;height:2mm;background:#333;border-radius:2mm}svg text{font:9px Arial,sans-serif;fill:#777}.month-timeline circle,.rhythm-dot{fill:#111}.callout{background:#f6f5f3;margin:7mm 0}.month,.issue{padding-top:3mm}.month{min-height:0}footer{margin-top:10mm;border-top:1px solid #ddd;padding-top:3mm;font-size:8pt;color:#777}
@media screen{body{max-width:820px;margin:auto;padding:25px}.page{padding-top:30px;border-top:1px solid #ddd;margin-top:50px}}

.annual-timeline{display:block;width:100%;height:auto;margin:5mm 0 7mm;break-inside:avoid}.annual-timeline text{font-family:Josefin Sans,Arial,sans-serif}.month-timeline{display:block;width:100%;height:auto;margin:4mm 0 3mm}
.month-timeline text{font:12px 'Josefin Sans',Arial,sans-serif;fill:#444}
.month-timeline circle{fill:#111}
.activation-layout{display:grid;grid-template-columns:70mm 1fr;gap:6mm;align-items:center;break-inside:avoid;page-break-inside:avoid}.activation-wheel{display:block;width:100%;max-width:70mm;height:auto}.activation-wheel .zodiac-label{font:7px Arial,sans-serif;fill:#777}.activation-wheel .planet-label{font:bold 8px Arial,sans-serif;fill:#382a76}.activation-wheel .chart-centre{font:15px Georgia,serif;fill:#333}.activation-wheel .chart-centre-small{font:7px Arial,sans-serif;fill:#777}.activation-wheel .natal-marker{fill:#725aca;stroke:white;stroke-width:1}.activation-wheel .transit-marker{fill:#e58b40;stroke:white;stroke-width:1}.activation-wheel .aspect-line{stroke:#ae9a6b;stroke-width:1.5}.activation-contacts{font-size:8pt;padding-left:5mm}.activation-contacts li{margin-bottom:2mm}.contacts{font-size:9pt;padding-left:5mm}.contacts li{margin:2mm 0}
.evidence-group,.keydate{break-inside:avoid}
.keydate{display:grid;grid-template-columns:32mm 1fr;gap:5mm;padding:3mm 0;border-bottom:1px solid #ddd;font-size:9pt}
.transit-fact{padding:3mm 0;border-bottom:1px solid #eee;font-size:9pt}
.smallfact{margin-top:2mm;font-size:8pt;color:#555}
@media print{.page{break-before:page}.month,.issue{break-before:page}.month h2,.month h3{break-after:avoid}.activation-layout,.month-timeline,.callout{break-inside:avoid}.natal-svg{break-before:auto}.cover{break-after:page}.month{font-size:9.5pt;line-height:1.3}.month h2{font-size:21pt}.month h3{margin:3mm 0 1mm}.month .activation-contacts{font-size:7.5pt}.month .contacts{font-size:8pt;margin:2mm 0}.month .activation-layout{margin:2mm 0}}
'''
    intro=f'<section class="cover"><div class="eyebrow">Luna Convergence · Your Year Ahead</div><h1>{e(getattr(editorial,"headline",None) or "Your Year Ahead")}</h1><p class="deck">{e(label)} · {e(getattr(editorial,"deck",None) or "")}</p><div class="divider"></div><p><b>Focus:</b> {e(main_focus)}</p><p class="quiet">{e(order_reference)}</p><h2>Your natal signature</h2><div class="signature">{signature}</div><div class="natal-svg">{chart}</div><h2>Your strengths</h2>{strengths}</section>'
    overview=f'<section class="page"><div class="eyebrow">The big picture</div><h2>Read the year</h2>{para(getattr(editorial,"read_year",()) or ())}<h2>How your year unfolds</h2><p>Your year has several overlapping stories. Each coloured curve shows activity from the verified transits in that Game, with dots at exact contacts. The black curve combines those same contacts. Peaks reflect concentrations of calculated contacts, not predicted outcomes.</p>{_annual_timeline(packet)}</section>'
    outro=f'<section class="page"><h2>What the year leaves you with</h2>{closing}<h3>About this report</h3><p>Calculated planetary evidence is interpreted symbolically and is not professional advice.</p></section>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Luna Convergence · Your Year Ahead</title><style>{FONT_IMPORT}{_font_face_css()}{css}</style></head><body>{intro}{overview}{"".join(month_cards)}{"".join(issue_cards)}{outro}{appendix}</body></html>'


def render_yearly_html_pdf(html: str) -> bytes:
    from weasyprint import HTML
    result=HTML(string=html).write_pdf()
    if not result.startswith(b'%PDF') or len(result)<10000: raise RuntimeError('PDF rendering did not complete')
    return result
