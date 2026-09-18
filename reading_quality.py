"""Prompt grounding and lightweight event coverage; never an LLM JSON schema."""
import re

WRITING_REVISION = 'event-grounding-2'


def writing_revision(product):
    # Only these outputs need replacement; retain unrelated paid generations.
    return 'weekly-chronology-1' if product in ('weekly', 'studio_weekly') else WRITING_REVISION


WEEKDAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
DAY_PATTERN = re.compile(r'\b(' + '|'.join(WEEKDAYS) + r')\b', re.I)
ASPECT_PATTERN = re.compile(
    r'\b(sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto)'
    r"(?:[’']s)?[\s–—-]+(conjunct(?:ion)?|sextile|square|trine|opposit(?:e|ion))"
    r'[\s–—-]+(sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto)\b', re.I)


def aspect_keys(text):
    result = set()
    for a, aspect, b in ASPECT_PATTERN.findall(str(text)):
        aspect = aspect.lower()
        if aspect.startswith('opposit'): aspect = 'opposition'
        if aspect.startswith('conjunct'): aspect = 'conjunction'
        result.add((tuple(sorted((a.lower(), b.lower()))), aspect))
    return result


def weekly_timeline(packet):
    from datetime import date
    timeline = []
    for source in sorted(packet.get('events', []), key=lambda row: row.get('date', '')):
        row = dict(source)
        try:
            row['weekday'] = WEEKDAYS[date.fromisoformat(row['date']).weekday()]
        except (KeyError, TypeError, ValueError):
            continue
        timeline.append(row)
    return timeline


def chronology_errors(packet, body):
    if packet.get('product') not in ('weekly', 'studio_weekly'):
        return []
    timeline = weekly_timeline(packet)
    if not timeline:
        return []
    errors = []
    mentions = list(DAY_PATTERN.finditer(body))
    order = [WEEKDAYS.index(m.group().capitalize()) for m in mentions]
    if any(b < a for a, b in zip(order, order[1:])):
        errors.append('Keep named weekdays in Monday-to-Sunday order; do not jump backwards.')
    allowed = {}
    for row in timeline:
        labels = [row.get('event', ''), *row.get('supporting_events', [])]
        allowed.setdefault(row['weekday'], set()).update(aspect_keys(' '.join(map(str, labels))))
    # Check explicit aspect names in single-day clauses only. Do not guess at
    # pronouns, multi-day ranges or unnamed symbolic meanings.
    known = set().union(*allowed.values()) if allowed else set()
    for clause in re.split(r'[.!?;\n]+', body):
        days = {m.group().capitalize() for m in DAY_PATTERN.finditer(clause)}
        if len(days) != 1:
            continue
        day = next(iter(days))
        for key in aspect_keys(clause) & known:
            if key not in allowed.get(day, set()):
                correct = ', '.join(d for d in WEEKDAYS if key in allowed.get(d, set()))
                errors.append(f'Attach {key[0][0]} {key[1]} {key[0][1]} to its supplied day(s): {correct}, not {day}.')
    return list(dict.fromkeys(errors))


def required_events(packet):
    """Require named turning points, not every minor transit or a word count."""
    if packet['product'] == 'studio_daily':
        return []  # A short clip is not the full overview.
    result = []
    for row in packet.get('major_events', []):
        label = row.get('event', '')
        if (row.get('tier') == 'FOUNDATION' or
                re.search(r'eclipse|equinox|solstice|new moon|full moon', label, re.I) or
                row.get('tier') == 'A+'):
            if label not in result:
                result.append(label)
    return result


def event_present(label, body):
    label, body = label.casefold(), body.casefold()
    body = re.sub(r"[-–—]", " ", body)
    body = re.sub(r"\s+", " ", body)
    for phrase in ('equinox', 'solstice', 'eclipse', 'new moon', 'full moon'):
        if phrase in label:
            # An eclipse type matters when two occur in the same period.
            qualifier = next((v for v in ('solar', 'lunar') if v in label), '') if phrase == 'eclipse' else ''
            return phrase in body and (not qualifier or qualifier in body)
    planets = re.findall(r'\b(?:sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto)\b', label)
    return bool(planets) and all(re.search(r'\b'+p+r'\b', body) for p in planets)


def content_errors(packet, body):
    """Only explicit omissions. This is not a claim of full semantic verification."""
    if not isinstance(body, str) or not body.strip():
        return []  # text_errors handles this.
    return (['Explain the supplied event: '+label for label in required_events(packet)
             if not event_present(label, body)] + chronology_errors(packet, body))


def grounded_brief(packet):
    from astrology_engine import HOUSE_NAMES
    brief = {k: v for k, v in packet.items() if k not in ('calculation_header', 'life_areas')}
    for field in ('events', 'major_events'):
        rows = []
        for source in packet.get(field, []):
            row = dict(source)
            pairs = source.get('planet_houses', [])
            houses = source.get('houses', [])
            if pairs:
                row['planet_life_areas'] = [dict(planet=p, house=h, life_area=HOUSE_NAMES[h]) for p, h in pairs]
                houses = [h for _, h in pairs]
            row['event_life_areas'] = [dict(house=h, life_area=HOUSE_NAMES[h]) for h in dict.fromkeys(houses) if h in HOUSE_NAMES]
            rows.append(row)
        brief[field] = rows
    if packet['product'] in ('weekly', 'studio_weekly'):
        brief['chronological_day_map'] = weekly_timeline(packet)
    brief['required_turning_points'] = required_events(packet)
    # Includes Daily supporting influences which previously disappeared from the prompt.
    brief['calculated_labels'] = packet.get('calculation_header', [])
    return brief
