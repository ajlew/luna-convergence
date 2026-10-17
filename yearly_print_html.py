"""Print-focused HTML for the same Year Ahead packet and editorial as the web report.

No new sky calculations, model calls or report text generation occur here.
"""
from __future__ import annotations
from datetime import date
import re
from html import escape
from typing import Any


def e(x: Any) -> str:
    return escape(str(x if x is not None else ''))


def clean_cover_headline(value: Any) -> str:
    """Return a display-only plain headline without enclosing Markdown emphasis."""
    headline = str(value or "Your Year Ahead").strip()
    while headline.startswith("**") and headline.endswith("**") and len(headline) > 4:
        headline = headline[2:-2].strip()
    return headline


def print_headline(value: Any) -> str:
    """Discard literal Markdown decoration in an HTML heading, not the prose.

    This is presentation-only: Groq owns words and Python owns typography.
    """
    return e(clean_cover_headline(value))


def d(x: Any) -> str:
    try: return date.fromisoformat(str(x)[:10]).strftime('%-d %B %Y')
    except Exception: return str(x or '')


def _annual_timeline(packet: dict, natal_longitudes: dict[str, float] | None = None) -> str:
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
    samples = [start + timedelta(days=round(days * i / 240)) for i in range(241)]
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
            for transit, a, b, hits in records:
                if not a <= day <= b:
                    continue
                # Use measured Swiss-Ephemeris orb whenever the natal position
                # is available. The curve is not an outcome probability.
                orb = (_sample_transit_orb(transit, natal_longitudes, day)
                       if natal_longitudes else None)
                if orb is not None:
                    orb_limit = max(0.1, float(transit.get('orb_limit') or transit.get('max_orb') or 3.0))
                    proximity = max(0., 1. - orb / orb_limit)
                    value += proximity ** 2
                elif hits:
                    # Explicitly labelled fallback only when the ephemeris or
                    # natal longitude cannot be sampled: verified exact-pass
                    # date kernel, not asserted measured angular precision.
                    sigma = max(3., min(16., (b-a).days / 14.))
                    value += sum(exp(-0.5 * (((day-dt).days)/sigma)**2) for dt in hits)
                else:
                    value += 0.08
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
        rows.append(f'<path d="{smooth_wave_path(pts)}" fill="none" stroke="{color}" stroke-width="2.25" stroke-linejoin="round" stroke-linecap="round"/>')
        for _,a,b,hits in valid[i]:
            for dt in hits:
                if start <= dt <= end:
                    j = min(range(len(samples)), key=lambda k: abs((samples[k]-dt).days))
                    yy = y+34-26*activity[i][j]/peak
                    rows.append(f'<circle cx="{xpos(dt):.2f}" cy="{yy:.2f}" r="3.2" fill="{color}"><title>{e(str(dt))}</title></circle>')

    y = 56+66*len(games)
    rows.append(f'<text x="4" y="{y+7}" font-size="12" fill="#222">Combined rhythm</text>')
    rows.append(f'<line x1="{x0}" y1="{y+83}" x2="{x0+width}" y2="{y+83}" stroke="#dedede"/>')
    for guide in (0.25, 0.5, 0.75):
        gy = y+79-70*guide
        rows.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x0+width}" y2="{gy:.1f}" stroke="#dadada" stroke-dasharray="2 5" stroke-opacity=".6"/>')
    pts=[(xpos(day), y+79-70*v/max_total) for day,v in zip(samples,total)]
    # Subtle uncertainty-neutral visual halo, not confidence intervals.
    upper=[(x, yy-5) for x,yy in pts]
    lower=[(x, yy+5) for x,yy in reversed(pts)]
    halo_path = 'M ' + ' L '.join(f'{x:.2f} {yy:.2f}' for x,yy in upper+lower) + ' Z'
    rows.append(f'<path d="{halo_path}" fill="#d3d3d3" opacity=".42"/>')
    rows.append(f'<path d="{smooth_wave_path(pts)}" fill="none" stroke="#171717" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>')
    # Subtle score-independent chart guides aid comparison; these are not probabilities.
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


def _sample_transit_orb(transit: dict, natal_longitudes: dict[str, float], day: date, hour_utc: float = 12.0) -> float | None:
    """Absolute aspect orb, calculated from Swiss Ephemeris; no synthetic peaks."""
    import re
    try:
        import swisseph as swe
        label = str(transit.get('technical_label') or '')
        name = label.split(' ', 1)[0].casefold()
        bodies = {'sun': swe.SUN, 'moon': swe.MOON, 'mercury': swe.MERCURY,
                  'venus': swe.VENUS, 'mars': swe.MARS, 'jupiter': swe.JUPITER,
                  'saturn': swe.SATURN, 'uranus': swe.URANUS,
                  'neptune': swe.NEPTUNE, 'pluto': swe.PLUTO}
        match = re.search(r'\b(conjunction|sextile|square|trine|opposition)\b', label, re.I)
        if not match or name not in bodies:
            return None
        angles = {'conjunction':0., 'sextile':60., 'square':90.,
                  'trine':120., 'opposition':180.}
        target = str(transit.get('natal_target') or '').casefold().strip()
        if not target:
            m = re.search(r'\bnatal\s+(\w+)', label, re.I)
            target = m.group(1).casefold() if m else ''
        if target not in natal_longitudes:
            return None
        jd = swe.julday(day.year, day.month, day.day, hour_utc)
        actual = float(swe.calc_ut(jd, bodies[name], swe.FLG_SWIEPH)[0][0]) % 360
        delta = abs((actual - natal_longitudes[target] + 180) % 360 - 180)
        return abs(delta - angles[match.group(1).casefold()])
    except (ValueError, TypeError, KeyError, ImportError):
        return None
    except Exception:
        # An ephemeris failure must never be rendered as invented precision.
        return None


def _natal_longitudes(snapshot: Any) -> dict[str, float]:
    values = {}
    for p in getattr(snapshot, 'positions', ()) or ():
        try: values[str(p.planet).casefold()] = float(p.longitude) % 360
        except (AttributeError, TypeError, ValueError): pass
    for name in ('ascendant', 'midheaven'):
        point = getattr(snapshot, name, None)
        if point is not None:
            try: values[name] = float(point.longitude) % 360
            except (AttributeError, TypeError, ValueError): pass
    return values


def _transit_timeline(round_: dict, game: dict, *, color: str = "#765577", natal_longitudes: dict[str, float] | None = None) -> str:
    """Show only contacts overlapping this rolling month; never infer dates."""
    a = _iso_date(round_.get("start")); b = _iso_date(round_.get("end"))
    if a is None or b is None:
        return ""
    rows = _active_transits(game, a, b)
    if not rows:
        return '<p class="quiet">No major selected personal transit is active in this chapter.</p>'
    from datetime import timedelta
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
        # Sample the *actual* angular orb each day. Draw only inside the verified
        # transit window; exact-hit markers remain the packet's certified passes.
        # Six-hour ephemeris samples: a finely resolved measured signal, not
        # a sine-wave approximation. A lower orb plots higher on the chart.
        # The identical daily window and calculated birth longitude are retained.
        steps = span * 4
        measurements = []
        for step in range(steps + 1):
            day = a + timedelta(days=step // 4)
            if not t_start <= day <= t_end:
                continue
            hour = float((step % 4) * 6)
            orb = _sample_transit_orb(transit, natal_longitudes or {}, day, hour)
            if orb is not None:
                measurements.append((step / 4, orb))
        max_orb = max((orb for _, orb in measurements), default=0.0)
        def signal_y(orb):
            return y + 3 - 20 * (1 - orb / max(max_orb, 0.000001))
        if len(measurements) >= 2:
            # Paired straight segments preserve every measured inflection.
            # Applying = angular orb narrowing; separating = widening.
            for (t0, o0), (t1, o1) in zip(measurements, measurements[1:]):
                x0 = chart_left + chart_width * t0 / span
                x1 = chart_left + chart_width * t1 / span
                opacity = '0.90' if o1 < o0 else '0.52' if o1 > o0 else '0.70'
                phase = 'applying' if o1 < o0 else 'separating' if o1 > o0 else 'stationary'
                svg.append(f'<path class="orb-curve orb-{phase}" d="M {x0:.2f} {signal_y(o0):.2f} L {x1:.2f} {signal_y(o1):.2f}" '
                           f'fill="none" stroke="{e(color)}" stroke-width="1.55" opacity="{opacity}" stroke-linecap="round"/>')
        elif len(measurements) == 1:
            t0, o0 = measurements[0]
            x0 = chart_left + chart_width * t0 / span
            svg.append(f'<circle cx="{x0:.2f}" cy="{signal_y(o0):.2f}" r="1.7" fill="{e(color)}"/>')
        else:
            svg.append(f'<rect x="{left:.1f}" y="{y-1.5}" width="{max(3,right-left):.1f}" height="3" rx="1.5" fill="{e(color)}" opacity="0.68"/>')
        for hit in transit.get('passes') or []:
            if not isinstance(hit,dict):continue
            hit_day = _iso_date(hit.get('date'))
            if hit_day is None or not a <= hit_day <= b:continue
            x = chart_left+chart_width*(hit_day-a).days/span
            label=str(hit.get('pass_label') or 'Exact')
            near = _sample_transit_orb(transit, natal_longitudes or {}, hit_day)
            dot_y = signal_y(near) if (near is not None and measurements) else y
            svg.append(f'<circle cx="{x:.1f}" cy="{dot_y:.1f}" r="3.2" fill="{e(color)}" stroke="white" stroke-width="1.0"><title>{e(label)} · {e(d(hit_day))}</title></circle>')
    svg.append('</svg>')
    return ''.join(svg)


# Print-safe SVG contours for the twelve standard zodiac glyphs.
# These are graphical assets, not calculated/customer-specific data.
_ZODIAC_VECTOR = {'♈': ('M854 0Q854 600 711.0 986.5Q568 1373 399 1373Q270 1373 253.0 1274.5Q236 1176 236 1142Q236 1014 320 886H186Q93 1018 93 1179Q93 1311 174.5 1404.5Q256 1498 402 1498Q774 1498 905 725Q913 676 918 636Q922 676 930 725Q1062 1498 1433 1498Q1580 1498 1661.0 1404.5Q1742 1311 1742 1179Q1742 1018 1649 886H1515Q1600 1014 1600 1143Q1600 1177 1583.0 1275.0Q1566 1373 1436 1373Q1268 1373 1125.0 986.5Q982 600 982 0Z', (93, 0, 1742, 1498)), '♉': ('M917 860Q770 860 667.0 756.5Q564 653 564.0 506.0Q564 359 667.0 256.0Q770 153 917.0 153.0Q1064 153 1167.5 256.0Q1271 359 1271.0 506.0Q1271 653 1168.5 756.5Q1066 860 917 860ZM917 1010Q1048 1015 1124 1076Q1210 1142 1258.5 1232.0Q1307 1322 1387.5 1409.0Q1468 1496 1653 1496V1388Q1530 1388 1446.5 1232.0Q1363 1076 1232 968Q1211 949 1188 934Q1234 904 1277 863Q1423 714 1423 504Q1423 295 1275.5 147.5Q1128 0 917 0Q709 0 561.0 147.5Q413 295 413 504Q413 714 561 863Q602 905 650 935Q626 949 605 968Q476 1076 390.5 1232.0Q305 1388 183 1388V1496Q368 1496 461.0 1409.0Q554 1322 590.0 1232.0Q626 1142 711 1076Q788 1015 917 1010Z', (183, 0, 1653, 1496)), '♊': ('M530 1276Q362 1298 192 1350V1498Q539 1408 919.0 1408.0Q1299 1408 1642 1498V1347Q1466 1300 1300 1276V222Q1466 199 1642 152V0Q1299 91 919.0 91.0Q539 91 192 0V148Q362 201 530 222ZM682 234Q798 247 915 247Q915 247 1148 234V1265Q1032 1252 915 1252Q915 1252 682 1265Z', (192, 0, 1642, 1498)), '♋': ('M1251 241Q1345 241 1411.5 307.5Q1478 374 1478.0 469.0Q1478 564 1412.0 630.0Q1346 696 1251.0 696.0Q1156 696 1090.0 630.0Q1024 564 1024.0 469.0Q1024 374 1090.0 307.5Q1156 241 1251 241ZM1060 64Q748 66 566.0 86.0Q384 106 231 149V273Q484 189 666.0 178.0Q848 167 907 167Q1037 167 1029 193Q898 301 898 468Q898 615 1000.5 718.5Q1103 822 1250 822Q1399 822 1502.0 718.5Q1605 615 1605.0 468.0Q1605 321 1501 218Q1428 141 1305.0 103.0Q1182 65 1060 64ZM585 759Q679 759 745.5 825.0Q812 891 812.0 986.0Q812 1081 745.5 1147.0Q679 1213 585.0 1213.0Q491 1213 424.0 1147.0Q357 1081 357.0 986.0Q357 891 423.5 825.0Q490 759 585 759ZM775 1391Q1088 1389 1270.0 1368.5Q1452 1348 1605 1305V1182Q1352 1266 1171.0 1276.5Q990 1287 932 1287Q799 1287 807 1261Q938 1153 938 987Q938 839 835.5 735.5Q733 632 586 632Q437 632 334.0 735.5Q231 839 231 987Q231 1133 335 1236Q408 1313 530.5 1351.5Q653 1390 775 1391Z', (231, 64, 1605.0, 1391)), '♌': ('M660 396Q735 425 760.0 481.5Q785 538 785 577Q785 612 771 647Q742 722 685.5 747.0Q629 772 590 772Q554 772 519 758Q444 728 419.5 672.5Q395 617 395 578Q395 543 409 507Q439 431 494.5 406.5Q550 382 589 382Q624 382 660 396ZM672 1134Q672 1295 783.5 1395.5Q895 1496 1075 1496Q1247 1496 1356.0 1385.5Q1465 1275 1465 1099Q1465 912 1320.0 661.0Q1175 410 1175 230Q1179 106 1313 103Q1384 103 1484 191L1549 119Q1422 0 1311 0Q1212 0 1140.0 60.5Q1068 121 1068 232Q1068 431 1211.5 671.5Q1355 912 1355 1106Q1355 1240 1273.0 1322.5Q1191 1405 1059 1405Q932 1405 857.0 1327.5Q782 1250 782 1121Q782 1061 805.0 988.5Q828 916 853 854Q890 756 894.5 692.0Q899 628 899 611Q899 524 867 456Q816 341 700 296Q644 274 588 274Q528 274 441.5 311.5Q355 349 308 469Q286 523 286 579Q286 639 313 699Q364 813 481 859Q536 880 591 880Q667 880 741 839Q749 839 749 852Q749 878 710.5 970.0Q672 1062 672 1134Z', (286, 0, 1549, 1496)), '♍': ('M680 1496Q743 1496 802.5 1397.0Q862 1298 862 1170Q902 1289 1001.0 1392.5Q1100 1496 1175 1496Q1237 1496 1278.0 1412.5Q1319 1329 1319 1110V908Q1367 1033 1432.5 1092.5Q1498 1152 1566 1152Q1626 1152 1676.0 1036.0Q1726 920 1726 647Q1726 239 1345 -82Q1346 -176 1492 -369H1324Q1278 -328 1204 -167Q1037 -268 862 -275V-159Q1053 -131 1177 -44L1168 173V1028Q1168 1046 1168 1063Q1168 1344 1122 1345Q1064 1344 997.5 1235.5Q931 1127 868 927V0H717V922Q717 1243 701.5 1296.0Q686 1349 651 1349Q651 1349 650 1349Q650 1349 649 1349Q608 1349 518.5 1236.0Q429 1123 410 908V0H261V1089Q261 1279 109 1470H251Q369 1391 405 1215Q428 1308 519.5 1402.0Q611 1496 680 1496ZM1319 618V58Q1577 308 1601 646Q1601 839 1578.5 908.5Q1556 978 1528 978Q1528 978 1524 978Q1494 978 1422.5 875.0Q1351 772 1319 618Z', (109, -369, 1726, 1496)), '♎': ('M171 259H1665V107H171ZM728 506H171V658H525Q458 762 458 893Q458 1078 586.5 1207.5Q715 1337 900 1337Q1086 1337 1215.5 1207.5Q1345 1078 1345 893Q1345 762 1277 658H1665V506H1072V658H1071Q1089 671 1106 688Q1192 773 1192 894Q1192 1016 1107.0 1101.0Q1022 1186 900.0 1186.0Q778 1186 693.0 1101.0Q608 1016 608 894Q608 773 693 688Q709 671 728 658Z', (171, 107, 1665, 1337)), '♏': ('M1280 271Q1280 160 1331.5 97.5Q1383 35 1472 34H1561V152H1565L1768 -21L1565 -196L1561 -192V-74H1472Q1269 -74 1201 46Q1157 120 1149 238L1128 1028Q1128 1046 1128 1063Q1128 1344 1082 1345Q1024 1344 957.5 1235.5Q891 1127 828 927V0H677V922Q677 1243 661.5 1296.0Q646 1349 611 1349Q611 1349 610 1349Q610 1349 609 1349Q568 1349 478.5 1236.0Q389 1123 370 908V0H221V1089Q221 1279 69 1470H211Q329 1391 365 1215Q388 1308 479.5 1402.0Q571 1496 640 1496Q703 1496 762.5 1397.0Q822 1298 822 1170Q862 1289 961.0 1392.5Q1060 1496 1135 1496Q1197 1496 1238.0 1412.5Q1279 1329 1279 1110V908L1280 272Z', (69, -196, 1768, 1496)), '♐': ('M1514 728V1236L809 531L1126 214L1018 106L701 423L277 -1L276 0L170 106L169 107L593 531L276 848L277 849L383 955L384 956L701 639L1406 1344H898V1496H1666V728Z', (169, -1, 1666, 1496)), '♑': ('M851 1496Q958 1496 998.5 1063.0Q1039 630 1064 634Q1173 855 1368 855Q1489 855 1565.5 760.0Q1642 665 1642 562Q1642 417 1570.5 331.5Q1499 246 1357 246Q1202 246 1080 379Q1036 219 973.0 111.5Q910 4 772 0H604V118L758 119Q880 123 985 499Q935 515 903.0 909.5Q871 1304 813 1304Q777 1304 700.0 1070.5Q623 837 623 642Q623 627 623 613L465 611Q465 864 394.5 1112.0Q324 1360 192 1366V1463Q339 1463 419.5 1352.0Q500 1241 540 966Q586 1167 631 1255Q672 1346 733.0 1421.0Q794 1496 851 1496ZM1137 510Q1230 365 1360 365Q1521 365 1530 562Q1523 719 1364 738Q1212 738 1137 510Z', (192, 0, 1642, 1496)), '♒': ('M176 413Q501 684 616 684Q661 684 674 644Q698 573 754.0 573.0Q810 573 896.0 644.0Q982 715 1038 715Q1092 715 1116 644Q1142 573 1199.0 573.0Q1256 573 1342 644Q1385 680 1426 680Q1550 680 1659 364L1565 313Q1502 498 1407 498Q1356 498 1296 445Q1210 369 1154.0 369.0Q1098 369 1073 444Q1045 522 986 522Q931 522 848 455Q761 384 706 384Q650 384 625 456Q601 526 547 526Q492 526 363.0 419.5Q234 313 229 313L176 411ZM176 884Q500 1153 616 1153Q660 1153 674 1114Q698 1044 754 1044Q809 1044 895 1114Q982 1186 1037.0 1186.0Q1092 1186 1115 1114Q1142 1044 1198 1044Q1255 1044 1341 1114Q1384 1149 1425 1149Q1550 1149 1659 834L1565 784Q1502 969 1407 969Q1356 969 1296 915Q1209 838 1154 838Q1098 838 1072 914Q1045 992 986 992Q931 992 847 924Q761 853 705 853Q650 853 625 925Q601 997 546.0 997.0Q491 997 362.5 890.5Q234 784 229 784L176 881Z', (176, 313, 1659, 1186.0)), '♓': ('M1038 665 797 662Q765 324 487 3L322 0Q629 351 656 662H360V834H656Q628 1144 321 1496L487 1493Q765 1173 797 834H1039Q1070 1173 1349 1493L1514 1496Q1207 1144 1180 834H1475L1474 662H1178Q1207 351 1514 0L1348 3Q1069 324 1038 662Z', (321, 0, 1514, 1496))}


from functools import lru_cache


@lru_cache(maxsize=1)
def _bodoni_wheel_face():
    from pathlib import Path
    from fontTools.ttLib import TTFont
    path = Path(__file__).resolve().parent / "assets" / "fonts" / "BodoniModa-SemiBold.ttf"
    font = TTFont(str(path))
    return font.getGlyphSet(), font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm


def _bodoni_wheel_label(text: str, x: float, y: float, size: float, color: str) -> str:
    """Draw wheel lettering as Bodoni vector outlines for reliable printed PDFs.

    WeasyPrint's SVG renderer can ignore the HTML @font-face declaration and
    fall back to DejaVu Sans. Glyph outlines preserve the exact existing Bodoni
    face without depending on system fonts or modifying the LLM output.
    """
    from fontTools.pens.svgPathPen import SVGPathPen

    glyphset, cmap, metrics, units = _bodoni_wheel_face()
    glyphs = []
    width = 0
    for ch in text:
        name = cmap.get(ord(ch))
        if not name:
            continue
        pen = SVGPathPen(glyphset)
        glyphset[name].draw(pen)
        path_data = pen.getCommands()
        if path_data:
            glyphs.append(f'<path d="{path_data}" transform="translate({width} 0)"/>')
        width += metrics[name][0]
    if not glyphs:
        return ''
    scale = size / units
    return (f'<g class="bodoni-wheel-outline" fill="{color}" '
            f'transform="translate({x:.2f} {y:.2f}) scale({scale:.8f} {-scale:.8f}) '
            f'translate({-width/2:.2f} 0)">{"".join(glyphs)}</g>')


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
    zodiac = ('♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓')
    # Fine 5-degree engraving ticks; they indicate geometry only.
    for degree in range(0, 360, 5):
        major = degree % 30 == 0
        x1,y1=point(degree, 121)
        x2,y2=point(degree, 127 if major else 124)
        out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#b6b6b6" stroke-width="{0.7 if major else 0.35}"/>')
    out.append('<circle cx="155" cy="155" r="128" fill="none" stroke="#bdbdbd" stroke-width=".5"/>')
    for i, sign in enumerate(zodiac):
        x1,y1=point(i*30,84); x2,y2=point(i*30,121)
        tx,ty=point(i*30+15,133)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ddd"/>')
        path, (xmin, ymin, xmax, ymax) = _ZODIAC_VECTOR[sign]
        factor = 12.0 / max(xmax-xmin, ymax-ymin)
        centre_x, centre_y = (xmin+xmax)/2, (ymin+ymax)/2
        out.append(f'<path class="zodiac-symbol" d="{path}" transform="translate({tx:.2f} {ty:.2f}) scale({factor:.6f} -{factor:.6f}) translate({-centre_x:.2f} {-centre_y:.2f})" fill="#424242"/>')
    begin,end_day=_iso_date(start),_iso_date(end)
    # Collect once before drawing so nearby natal targets can be laid out together.
    # Geometry is display-only: all source longitudes remain untouched.
    targets = {}
    for tr in transits:
        label = str(tr.get('technical_label') or '')
        target = str(tr.get('natal_target') or '').strip()
        if not target:
            for name in natal:
                if 'natal ' + name in label.casefold():
                    target = name
                    break
        key = target.casefold().replace('natal ', '')
        if key in natal:
            targets[key] = float(natal[key].longitude) % 360

    # Greedy deterministic non-overlapping placements, estimated in SVG user units.
    # Markers remain at the true coordinate. Only their labels move; thin leader
    # lines reconnect displaced labels to those natal positions.
    placed_boxes = []
    label_coords = {}
    for key, longitude in sorted(targets.items(), key=lambda item: (item[1], item[0])):
        anchor_x, anchor_y = point(longitude, 103)
        best = None
        for radius in (91, 76, 110, 63):
            for shift in (0, 18, -18, 36, -36, 54, -54, 72, -72):
                lx, ly = point(longitude + shift, radius)
                # Font-aware safe label box; geometry only, never moves the true natal point.
                box = (lx - 30, ly - 15, lx + 30, ly + 12)
                collision = sum(max(0, min(box[2], old[2]) - max(box[0], old[0])) *
                                max(0, min(box[3], old[3]) - max(box[1], old[1]))
                                for old in placed_boxes)
                # Also avoid painting a label over another natal marker.
                marker_overlap = sum(1 for other_key, other_lon in targets.items()
                                     if other_key != key and
                                     abs(lx - point(other_lon, 103)[0]) < 28 and
                                     abs(ly - point(other_lon, 103)[1]) < 17)
                score = (collision + marker_overlap * 200, abs(shift) + abs(radius-91) * .4)
                if best is None or score < best[0]:
                    best = (score, lx, ly, box)
                if score[0] == 0 and shift == 0 and radius == 91:
                    break
            if best and best[0] == (0, 0):
                break
        _, lx, ly, box = best
        placed_boxes.append(box)
        label_coords[key] = (lx, ly)

    # Coincident points retain their true angle. Spread only their display
    # radii, with a fine spoke back to the exact calculated anchor.
    marker_radii = {key: 103.0 for key in targets}
    sorted_targets = sorted(targets, key=lambda key: (targets[key], key))
    groups = []
    for key in sorted_targets:
        if groups and (targets[key] - targets[groups[-1][-1]]) <= 6:
            groups[-1].append(key)
        else:
            groups.append([key])
    if len(groups) > 1 and ((targets[groups[0][0]] + 360) - targets[groups[-1][-1]]) <= 6:
        groups[0] = groups[-1] + groups[0]
        groups.pop()
    for group in groups:
        if len(group) > 1:
            for index, key in enumerate(sorted(group, key=lambda k: (targets[k], k))):
                marker_radii[key] = 103 + (index - (len(group)-1)/2) * 12

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
            true_x,true_y=point(longitude,103)
            x,y=point(longitude,marker_radii[key])
            if marker_radii[key] != 103:
                out.append(f'<line class="natal-label-leader" x1="{true_x:.1f}" y1="{true_y:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>')
            out.append(f'<circle class="natal-marker" cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#725aca"/>')
            lx,ly=label_coords[key]
            if ((lx-x)**2 + (ly-y)**2)**.5 > 21:
                out.append(f'<line class="natal-label-leader" x1="{x:.1f}" y1="{y:.1f}" x2="{lx:.1f}" y2="{ly-3:.1f}"/>')
            out.append(_bodoni_wheel_label(key[:3].title(), lx, ly, 14, '#382a76'))
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
    out.append(_bodoni_wheel_label('Natal', 155, 151, 18, '#333333'))
    out.append(_bodoni_wheel_label('Activations', 155, 166, 14, '#555555'))
    out.append('</svg>')
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


def _print_reflow_natal_labels(svg: str) -> str:
    """Move ONLY print natal label text when neighbouring abbreviations collide.

    Planet dots/aspects retain their exact calculated coordinates. No natal
    calculations or shared natal renderer are modified.
    """
    pattern = re.compile(r'(<text x="(?P<x>-?[\d.]+)" y="(?P<y>-?[\d.]+)"[^>]*>)(?P<label>SUN|MOON|MER|VEN|MAR|JUP|SAT|URA|NEP|PLU|NODE)(</text>)')
    placed = []
    def place(match):
        x, y = float(match.group('x')), float(match.group('y'))
        # On the 760-unit source wheel, even 3-letter labels need ~29 units.
        options = [(0,0),(0,-19),(0,19),(-25,0),(25,0),(-28,-18),(28,18),(-28,18),(28,-18)]
        dx, dy = next(((dx,dy) for dx,dy in options if all(
            abs(x+dx-px) >= 34 or abs(y+dy-py) >= 16 for px,py in placed)), options[-1])
        placed.append((x+dx,y+dy))
        opening = match.group(1)
        opening = re.sub(r'x="[-\d.]+"', f'x="{x+dx:.1f}"', opening, count=1)
        opening = re.sub(r'y="[-\d.]+"', f'y="{y+dy:.1f}"', opening, count=1)
        return opening + match.group('label').title() + match.group(5)
    return pattern.sub(place, svg)


def build_yearly_print_html(*, snapshot: Any, packet: dict, editorial: Any, label: str, main_focus: str = '', personal_question: str = '', order_reference: str = '') -> str:
    from monthly_report_pdf_home_v3 import FONT_IMPORT, _font_face_css
    from natal_snapshot import natal_wheel_svg
    games=[g for g in packet.get('games',[]) if isinstance(g,dict)]
    rounds=[r for r in packet.get('monthly_rounds',[]) if isinstance(r,dict)]
    game_by_number={int(g.get('number') or 0):g for g in games}
    game_colors={int(g.get('number') or i+1):c for i,(g,c) in enumerate(zip(games,("#765577", "#51758a", "#a0783d", "#597762", "#8c5c50")))}
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
    def annual_phase_markup():
        phases = tuple(getattr(editorial, 'annual_phases', ()) or ())
        if len(phases) == 4:
            return ''.join(
                '<div class="year-phase"><h3 class="year-phase-heading">'
                + f'<span>Phase {index}</span><small>{e(d(start))} – {e(d(end))}</small></h3>'
                + para((prose,)) + '</div>'
                for index, (start, end, prose) in enumerate(phases, 1)
            )
        return para(getattr(editorial,'read_year',()) or ())
    def para(xs): return ''.join(f'<p>{e(s)}</p>' for s in (xs or []) if str(s).strip())
    try: chart=_print_reflow_natal_labels(natal_wheel_svg(snapshot,size=760))
    except Exception: chart=''
    if not chart: raise ValueError('Year Ahead print export requires its natal chart; no PDF generated without it')
    positions={str(getattr(p,'planet','')):str(getattr(p,'sign','')) for p in (getattr(snapshot,'positions',()) or ())}
    signature=''.join(f'<div><span>{name}</span><strong>{e(value)}</strong></div>' for name,value in [('Sun',positions.get('Sun','Not calculated')),('Moon',positions.get('Moon','Not calculated')),('Rising',getattr(getattr(snapshot,'ascendant',None),'sign','Not calculated'))])
    # Snapshot attributes vary between versions; use documented dict/signatures where available.
    portrait = para(getattr(editorial, 'natal_portrait', ()) or ())
    strengths=''
    for signature in list(getattr(snapshot,'signatures',()) or ())[:6]:
        # Paid Year Ahead-only language correction to Python-written natal
        # evidence. Shared Natal Snapshot and Paid Monthly remain untouched.
        strength_title = str(getattr(signature, 'title', '') or '')
        strength_evidence = str(getattr(signature, 'evidence', '') or '')
        strength_text = str(getattr(signature, 'text', '') or '')
        if (strength_title == 'Two instincts arrive together'
                and 'Moon' in strength_evidence and 'Mercury' in strength_evidence):
            strength_text = ('Feelings and thoughts often arrive together. You may notice a detail '
                             'before you can explain why it matters. Give your first impression '
                             'room, then check it against what you can actually verify.')
        strengths += (f'<article class="block"><h3>{e(strength_title)}</h3><p>{e(strength_text)}</p>'
                      + (f'<p class="quiet strength-evidence">{e(strength_evidence)}</p>'
                         if strength_evidence else '') + '</article>')
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
            f'<h2>{e(theme.title())}</h2><p class="meta">{e(row["phase"] if row["phase"].casefold() == row["story"].casefold() else row["phase"] + " · " + row["story"].replace(" And "," and "))}</p>'
            f'<h3>What this month brings into focus</h3><p>{e(scenario)}</p>'
            + (f'<h3>Your decision</h3><p>{e(decision)}</p>' if decision else '')
            + (f'<div class="callout"><strong>Key moment</strong><p>{e(row["strongest"])}</p></div>'
                if row.get('strongest') else '')
            + (f'<div class="month-data"><h3>Personal transits this period</h3>{_transit_timeline(round_,focused,color=game_colors.get(int(focused.get("number") or 0), "#765577"),natal_longitudes=_natal_longitudes(snapshot))}'
               f'<ul class="contacts">{contacts}</ul>' if focused else
               '<p class="quiet">A quieter period to consolidate what is already underway.</p>')
            + ('<div class="chart-reading"><strong>How to read your monthly transits</strong><p>Each coloured curve follows the calculated orb through this month: higher means closer to exact. A dot marks a verified exact contact. Where orb data is unavailable, a bar shows only the active window.</p><p>Compare overlapping curves, then read <em>Your decision</em> for Luna&apos;s practical question. The chart describes angular exactness, not guaranteed events.</p></div>' if i == 0 and focused else '')
            + (f'</div><div class="month-activation"><h3>Your natal activation</h3>{_month_activation_svg(snapshot, transit_rows, round_.get("start"), round_.get("end"))}' if focused else '')
            + ('<div class="chart-reading"><strong>How to read your natal activation</strong><p>Your natal chart describes the planetary positions at birth. This smaller wheel highlights the natal positions contacted by this month&apos;s selected transits.</p><p>Purple markers identify those natal positions. Orange markers show transiting positions when verified coordinates are available.</p><p></p></div>' if i == 0 and focused else '')
             + ('</div>' if focused else '')
            + '</section>'
        )
    from game_decision_model import build_game_decision_boards, render_game_decision_board, GAME_DECISION_CSS
    decision_boards = {row["number"]:row for row in build_game_decision_boards(packet)}
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
        issue_cards.append(f'<section class="issue page"><div class="eyebrow">Major story {i+1:02d}</div><h2>{e(title.title())}</h2><div class="story-timing"><h3>Timing and evidence</h3><p>{e(primary.get("technical_label") or primary.get("label") or primary.get("name") or "")}</p><ul>{evidence}</ul></div>{para(paragraphs)}{render_game_decision_board(decision_boards[int(g.get("number") or i+1)]) if int(g.get("number") or i+1) in decision_boards else ""}</section>')
    appendix = _evidence_appendix(games)
    if order_reference:
        appendix = appendix.rsplit("</section>", 1)[0] + f'<p class="technical-reference">Document reference: {e(order_reference)}</p></section>'
    closing=para(getattr(editorial,'closing',()) or ())
    css='''
@page {size:A4;margin:17mm 17mm 18mm}
*{box-sizing:border-box}body{font-family:'Josefin Sans',Arial,sans-serif;color:#141414;font-size:11pt;line-height:1.48;margin:0}
h1,h2{font-family:'Bodoni Moda',Georgia,serif;font-weight:500;line-height:1.15}h1{font-size:33pt;margin:0 0 10mm}h2{font-size:25pt;margin:0 0 5mm}h3{font-size:12pt;margin:6mm 0 2mm}p{margin:0 0 4mm}small,.quiet{color:#666}.eyebrow{font-size:8pt;text-transform:uppercase;letter-spacing:.12em;font-weight:700;margin-bottom:9mm}
.page{break-before:page}.cover{padding-top:16mm}.deck{font-size:13pt;max-width:160mm}.meta{color:#555}.block,.callout,.lane,.natal-svg,.signature{break-inside:avoid;page-break-inside:avoid}.signature{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;margin:7mm 0}.signature>div,.callout{padding:4mm;border:1px solid #ddd}.signature span{display:block;font-size:8pt;text-transform:uppercase}.signature strong{display:block;margin-top:2mm}.natal-svg{width:100%;height:108mm;break-before:page;break-inside:avoid;text-align:center;padding-top:4mm}.strength-list{break-inside:auto;page-break-inside:auto}.natal-svg svg text{font-family:"Bodoni Moda",Georgia,serif!important;text-transform:none}.natal-svg svg{display:block;width:96mm!important;height:96mm!important;margin:0 auto}.divider{border-top:1px solid #aaa;margin:7mm 0}.lanes{margin:7mm 0}.lane{display:grid;grid-template-columns:44mm 1fr;gap:4mm;align-items:center;margin:4mm 0}.lane strong{font-size:9pt;display:block}.lane small{font-size:7pt;display:block}.track{height:12mm;background:#f3f3f3;border-radius:2mm;position:relative}.track span{position:absolute;top:5mm;height:2mm;background:#333;border-radius:2mm}svg text{font:9px Arial,sans-serif;fill:#777}.rhythm-dot{fill:#111}.callout{background:#f6f5f3;margin:7mm 0}.month,.issue{padding-top:3mm}.month{min-height:0}footer{margin-top:10mm;border-top:1px solid #ddd;padding-top:3mm;font-size:8pt;color:#777}
@media screen{body{max-width:820px;margin:auto;padding:25px}.page{padding-top:30px;border-top:1px solid #ddd;margin-top:50px}}

.annual-timeline{display:block;width:100%;height:auto;margin:5mm 0 7mm;break-inside:avoid}.annual-timeline text{font-family:Josefin Sans,Arial,sans-serif}.month-timeline{display:block;width:100%;height:auto;margin:4mm 0 3mm}
.month-timeline text{font:12px 'Josefin Sans',Arial,sans-serif;fill:#444}
.chart-reading p{margin:1.5mm 0}.chart-reading strong{display:block;font-size:9pt;color:#222;margin-bottom:2mm}.chart-reading{font-size:8.5pt;color:#595959;line-height:1.35;margin:2mm 0 4mm}.month-timeline circle{stroke:#fff;stroke-width:1.5}
.activation-layout{display:grid;grid-template-columns:106mm 1fr;gap:4mm;align-items:center;break-inside:avoid;page-break-inside:avoid}.activation-wheel{display:block;width:100%;max-width:106mm;height:auto}.activation-wheel .zodiac-label{font:13px "DejaVu Sans","Noto Sans Symbols 2","Segoe UI Symbol",sans-serif;fill:#444}.activation-wheel .planet-label{font:500 14px "Bodoni Moda",Georgia,serif;fill:#382a76}.activation-wheel .natal-label-leader{stroke:#725aca;stroke-width:.65;opacity:.7}.activation-wheel .chart-centre{font:500 18px "Bodoni Moda",Georgia,serif;fill:#333}.activation-wheel .chart-centre-small{font:500 14px "Bodoni Moda",Georgia,serif;fill:#555}.activation-wheel .natal-marker{fill:#725aca;stroke:white;stroke-width:1}.activation-wheel .transit-marker{fill:#e58b40;stroke:white;stroke-width:1}.activation-wheel .aspect-line{stroke:#ae9a6b;stroke-width:1.5}.activation-contacts{font-size:8pt;padding-left:5mm}.activation-contacts li{margin-bottom:2mm}.contacts{font-size:9pt;padding-left:5mm}.contacts li{margin:2mm 0}
.evidence-group,.keydate{break-inside:avoid}
.keydate{display:grid;grid-template-columns:32mm 1fr;gap:5mm;padding:1.8mm 0;border-bottom:1px solid #ddd;font-size:9pt;break-inside:avoid}
.transit-fact{padding:2mm 0;border-bottom:1px solid #eee;font-size:9pt}
.smallfact{margin-top:2mm;font-size:8pt;color:#555}
.year-phase{margin:0 0 6mm;break-inside:auto}.year-phase-heading{display:flex;justify-content:space-between;align-items:baseline;gap:5mm;border-top:1px solid #bbb;padding-top:2mm;margin:5mm 0 2mm;break-after:avoid}.year-phase-heading small{font:8pt 'Josefin Sans',Arial,sans-serif;color:#555}.natal-portrait{font-size:10pt;line-height:1.42;max-width:164mm}.natal-portrait p{margin-bottom:3mm;orphans:3;widows:3}.year-phase p{orphans:3;widows:3}.year-report-disclaimer{margin-top:12mm;padding-top:3mm;border-top:1px solid #d5d5d5;font-size:8pt;color:#555;break-inside:avoid}@media print{.page{break-before:page}.month,.issue{break-before:page}.month h2,.month h3{break-after:avoid}.activation-layout,.month-timeline,.callout{break-inside:avoid}.natal-svg{break-before:auto}.cover{break-after:page}.month{font-size:9.5pt;line-height:1.3}.month h2{font-size:21pt}.month h3{margin:3mm 0 1mm}.month .activation-contacts{font-size:7.5pt}.month .contacts{font-size:8pt;margin:2mm 0}.month .activation-layout{margin:1mm 0;grid-template-columns:84mm 1fr;gap:3mm;align-items:center}.month .activation-wheel{max-width:84mm}.month .activation-contacts{font-size:7pt}.month .chart-reading{font-size:7.5pt;line-height:1.23;margin:.5mm 0 1mm}.month .month-timeline{margin:1mm 0}.month .contacts{font-size:7.5pt}.month .callout{margin:3mm 0;padding:2.5mm}.month .eyebrow{margin-bottom:2.5mm}.month p{margin-bottom:1.4mm}.month>p.quiet:last-child{font-size:7pt;line-height:1.2;margin:1mm 0 0;break-after:avoid}.month h3{break-after:avoid}.keydate{padding:1.8mm 0}.evidence-group{break-inside:auto}.transit-fact{break-inside:avoid;padding:1.8mm 0}}

/* Book-quality A4 folios: print page furniture and controlled technical plates. */
@page {
  size: A4;
  margin: 17mm 17mm 18mm;
  @bottom-left {content: "LUNA CONVERGENCE  /  YOUR YEAR AHEAD"; font: 7pt "Josefin Sans",Arial,sans-serif; letter-spacing: .12em; color: #777;}
  @bottom-right {content: counter(page); font: 9pt Georgia,serif; color: #777;}
}
@media print {
  .cover {break-after:page;}
  .natal-study {break-before:page; display:grid; grid-template-columns:1fr 60mm; align-items:center; gap:5mm; min-height:125mm; break-inside:avoid;}
  .natal-study .natal-svg {height:auto; padding:3mm 0; margin:0; break-before:auto;}
  .natal-study .natal-svg svg {width:109mm!important;height:109mm!important;max-width:100%;}
  .natal-study .chart-reading {font-size:9pt;line-height:1.43; padding-left:4mm; border-left:1px solid #c9b28b;}
  .month {break-before:page; padding-top:2mm;}
  .month-data {break-inside:auto; margin-top:3mm;}
  .month-activation {break-inside:auto; margin-top:4mm; padding:3mm 0 2mm; border-top:1px solid #c7b08a;}
  .month-activation h3 {margin-top:1mm;}
  .month .activation-layout {grid-template-columns:88mm 1fr; gap:5mm;}
  .month .activation-wheel {max-width:77mm;}
  .month .activation-layout {grid-template-columns:77mm 1fr;}
  .month .activation-description {line-height:1.3;}
  .month .activation-contacts {font-size:7.8pt;}
  .month .chart-reading {margin:2mm 0;}
  .month .month-timeline {margin:1mm 0 2mm;}
  .month .contacts {margin:1mm 0 2mm;}
  .month .contacts li {margin:1mm 0;}
  .keydate {padding:1mm 0; font-size:8.6pt;}
  .evidence-group {break-inside:auto;}
  .transit-fact {padding:1.2mm 0;}
  .strength-list .block {break-inside:auto;}
  .story-timing {break-inside:auto; margin-top:3mm;}
  .story-timing h3 {break-after:avoid;}
  .story-timing li {break-inside:avoid;}
  .issue {break-inside:auto;}
  .issue p {orphans:3; widows:3; font-size:9.8pt;line-height:1.38;margin-bottom:2.7mm;}
  .issue .story-timing {font-size:8pt;margin:2mm 0 5mm;border-top:1px solid #c9b28b;padding-top:2mm;}
  .issue .story-timing h3 {font-size:9pt;margin:1mm 0;}
  .issue .story-timing p {font-size:8pt;margin:1mm 0;}
  .issue .story-timing ul {margin:1mm 0;padding-left:5mm;}
  .technical-reference {font-size:6.5pt;color:#777;overflow-wrap:anywhere; margin-top:9mm;}
  .month-activation .activation-layout {break-inside:avoid;page-break-inside:avoid;}
  .month-activation {margin-top:2mm;padding-top:1.5mm;padding-bottom:0;}
  .month-activation h3 {margin-top:0;}
  .month .chart-reading {margin:0 0 1mm;font-size:7pt;line-height:1.16;}
  .month-activation .activation-wheel {width:77mm;max-width:77mm;}
  h2,h3 {break-after:avoid;}
  p {orphans:3;widows:3;}
  .activation-wheel .planet-label {font:500 14px "Bodoni Moda",Georgia,serif; fill:#27204d;}
  .activation-wheel .natal-label-leader {stroke-width:.9;}
  .activation-wheel circle, .activation-wheel path {shape-rendering:geometricPrecision;}
}
'''
    intro=f'<section class="cover"><div class="eyebrow">Luna Convergence · Your Year Ahead</div><h1>{print_headline(getattr(editorial,"headline",None))}</h1><p class="deck">{e(label)}</p><div class="divider"></div><p><b>Focus:</b> {e(main_focus)}</p><h2>Your natal signature</h2><div class="signature">{signature}</div><div class="natal-study"><div class="natal-svg">{chart}</div><div class="chart-reading"><strong>How to read your natal chart</strong><p>This is your starting pattern: the calculated positions of the planets at your birth. The zodiac signs describe their placement, while the connecting lines show selected relationships between them.</p><p>Read this alongside <em>Your strengths</em> and the natal portrait below. It provides the personal foundation for understanding why certain yearly transits may be particularly relevant to you.</p></div></div><h2>Read the pattern</h2><div class="natal-portrait">{portrait}</div><h2>Your strengths</h2><div class="strength-list">{strengths}</div></section>'
    overview=f'<section class="page"><div class="eyebrow">The big picture</div><h2>Read the year</h2>{annual_phase_markup()}<h2>How your year unfolds</h2><p>Luna calls a related set of calculated transits a Game: a strategic period in which competing pressures, choices and trade-offs converge. A Game is an interpretive decision framework, not a prediction or a mathematically proven optimal move. Each coloured curve shows activity from the verified transits in that Game, with dots at exact contacts. The black curve combines those same contacts. Peaks reflect calculated orb closeness where positions are available, otherwise verified exact-pass timing; they do not predict outcomes. Use overlapping peaks to see which stories may warrant closer attention, then refer to their monthly decisions.</p>{_annual_timeline(packet, _natal_longitudes(snapshot))}</section>'
    outro=f'<section class="page"><h2>What the year leaves you with</h2>{closing}<footer class="year-report-disclaimer">Calculated planetary evidence is interpreted symbolically and is not professional advice.</footer></section>'
    css += GAME_DECISION_CSS + """
@media print {
 .issue {font-size:9pt;line-height:1.28}
 .issue p {font-size:9pt;line-height:1.27;margin-bottom:1.6mm}
 .issue h2 {font-size:22pt;margin-bottom:3mm}
 .issue .eyebrow {margin-bottom:4mm}
 .game-decision-board {margin:3mm 0;padding:2mm 0;font-size:8.1pt}
 .game-decision-board h3 {font-size:11pt;margin:1mm 0}
 .game-decision-row {grid-template-columns:35mm minmax(0,1fr);padding:.75mm 0;gap:3mm;line-height:1.18}
 .game-decision-dates {font-size:7.1pt;margin:.5mm 0}
 .game-decision-dates li {padding:.2mm 0;break-inside:avoid}
 .checkpoint-role {font-size:6.9pt;margin-left:2mm;line-height:1.12}
 .game-decision-board .game-decision-note {font-size:7pt;line-height:1.17;margin:1mm 0}
 .game-decision-board h4 {font-size:8pt;margin:1mm 0}
 .annual-timeline {max-height:110mm}
}
"""
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Luna Convergence · Your Year Ahead</title><style>{FONT_IMPORT}{_font_face_css()}{css}</style></head><body>{intro}{overview}{"".join(month_cards)}{"".join(issue_cards)}{outro}{appendix}</body></html>'


def render_yearly_html_pdf(html: str) -> bytes:
    from weasyprint import HTML
    result=HTML(string=html).write_pdf()
    if not result.startswith(b'%PDF') or len(result)<10000: raise RuntimeError('PDF rendering did not complete')
    return result
