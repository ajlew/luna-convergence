"""Saved collective video copy; no provider calls and no sign-specific houses."""
from datetime import timedelta
from plain_readings import load_reading, split_move, clean_prose
from unified_period_system import packet_timeline, daily_sky_cards, deduplicated_caption, canonical_event_id

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
              'technical': e.technical_label, 'planets': list(e.planets), 'tier': e.tier}
             for e in major_sky_events(start, end, timezone_name=timezone)]
    packet = {'product': product, 'period': start.isoformat(), 'sign': COLLECTIVE,
              'timezone': timezone, 'calculation_header': [f"{r['date']} · {r['event']}" for r in rows],
              'life_areas': [], 'events': rows, 'major_events': major,
              'audience': 'Collective sky for all signs. Do not invent personal houses or select a Sun sign.'}
    packet['timeline'] = packet_timeline(packet, timezone)
    if product == 'studio_weekly':
        packet['sky_cards'] = weekly_sky_cards(monday, timezone)
    return packet



def weekly_sky_cards(monday, timezone):
    """Build seven Sky Cards from the authoritative studio_daily ranking.

    The Daily product chooses the primary event. Sky Cards inherit that
    choice rather than independently ranking the same day's sky.
    All calculated timeline events remain available for convergence.
    """
    cards = []

    for offset in range(7):
        day = monday + timedelta(days=offset)

        daily = studio_packet(
            'studio_daily',
            day,
            COLLECTIVE,
            timezone,
        )

        events = daily.get('events', [])
        timeline = daily.get('timeline', [])
        major_events = daily.get('major_events', [])

        primary = events[0] if events else None

        if not primary:
            cards.append({
                'date': day.isoformat(),
                'weekday': day.strftime('%A'),
                'has_event': False,
                'event': '',
                'primary_event': '',
                'technical': '',
                'phase': '',
                'timing': '',
                'timezone': timezone,
                'timezone_label': '',
                'protected': False,
                'supporting_events': timeline,
                'all_events': timeline,
            })
            continue

        primary_label = str(primary.get('event') or '').strip()
        primary_id = canonical_event_id(primary, timezone)

        selected = next(
            (
                candidate
                for candidate in timeline
                if str(candidate.get('event_id') or '').casefold()
                == primary_id.casefold()
            ),
            None,
        )
        supporting = [
            candidate
            for candidate in timeline
            if candidate is not selected
        ]

        cards.append({
            'date': day.isoformat(),
            'weekday': day.strftime('%A'),
            'has_event': True,
            'event': primary_label,
            'primary_event': primary_label,
            'technical': (
                str(selected.get('technical_label') or '').strip()
                if selected else primary_label
            ),
            'phase': (
                str(selected.get('phase') or '').strip()
                if selected else ''
            ),
            'timing': (
                str(
                    selected.get('exact_time_label')
                    or selected.get('timing')
                    or ''
                ).strip()
                if selected else ''
            ),
            'timezone': timezone,
            'timezone_label': (
                str(selected.get('timezone_label') or '').strip()
                if selected else ''
            ),
            'protected': (
                bool(selected.get('protected'))
                if selected else False
            ),
            'supporting_events': supporting,
            'all_events': timeline,
        })

    return cards

def publishing_copy(monday, body, public_url):
    body = clean_prose(body)
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








