"""Saved collective video copy; no provider calls and no sign-specific houses."""
from datetime import timedelta
from plain_readings import load_reading, split_move

COLLECTIVE = 'All signs'


def studio_packet(product, target, sign, timezone):
    from reading_facts import shared_week
    from weekly_view import monday_for
    monday = monday_for(target)
    days = shared_week(monday, timezone)
    selected = days if product == 'studio_weekly' else [d for d in days if d.reading_date == target]
    rows = [{'date': d.reading_date.isoformat(), 'event': d.evidence,
             'planets': list(d.planets), 'phase': d.phase, 'exact_time': d.exact_time_label,
             'supporting_events': list(d.supporting_events)} for d in selected]
    # Registry contains all seasonal gates and eclipses; discard the sign-house projection.
    from major_event_registry import major_sky_events
    end = monday + timedelta(days=6) if product == 'studio_weekly' else target
    start = monday if product == 'studio_weekly' else target
    major = [{'date': e.event_date.isoformat(), 'event': e.display_label,
              'technical': e.technical_label, 'planets': list(e.planets)}
             for e in major_sky_events(start, end, timezone_name=timezone)]
    return {'product': product, 'period': start.isoformat(), 'sign': COLLECTIVE,
            'timezone': timezone, 'calculation_header': [f"{r['date']} · {r['event']}" for r in rows],
            'life_areas': [], 'events': rows, 'major_events': major,
            'audience': 'Collective sky for all signs. Do not invent personal houses or select a Sun sign.'}


def publishing_copy(monday, body, public_url):
    end = monday + timedelta(days=6)
    label = f'{monday:%d %B}–{end:%d %B %Y}'
    url = public_url.rstrip('/') + '/weekly-view'
    tags = 'astrology, weekly horoscope, week ahead, Luna Convergence'
    return {'YouTube title': f'Week Ahead Astrology | {label}',
            'YouTube description': f'{body}\n\nYour full week: {url}\n\n#astrology #weeklyhoroscope #LunaConvergence',
            'Instagram Reel caption': f'{body}\n\n{url}\n\n#astrology #weeklyhoroscope #LunaConvergence',
            'YouTube comma-separated tags': tags}


def sign_card(sign, monday, body):
    _, move = split_move(body)
    return f'{sign.upper()}\n{monday:%d %b}–{monday + timedelta(days=6):%d %b %Y}\n\n{move}\n\nLuna Convergence'
