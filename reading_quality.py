"""Prompt grounding plus the single hard editorial gate: chronology."""
import re

WRITING_REVISION = 'chronology-only-1'


def writing_revision(product):
    # Plain free and Studio copy share the same global evidence rules.
    return WRITING_REVISION


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
    if packet['product'] in ('studio_daily', 'studio_meaning'):
        return []  # Short Studio clips are not the full overview.
    result = []
    if packet['product'] == 'daily':
        for row in packet.get('events', [])[:1]:
            for label in [row.get('event', ''), *row.get('supporting_events', [])]:
                if label and label not in result:
                    result.append(label)
        return result
    for row in packet.get('major_events', []):
        label = row.get('event', '')
        if (row.get('tier') == 'FOUNDATION' or
                re.search(r'eclipse|equinox|solstice|new moon|full moon', label, re.I)):
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
    keys = aspect_keys(label)
    if keys:
        return bool(keys & aspect_keys(body))
    planets = re.findall(r'\b(?:sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto)\b', label)
    return bool(planets) and all(re.search(r'\b'+p+r'\b', body) for p in planets)


def content_errors(packet, body):
    """Reject only chronology errors; all other editorial rules stay in the prompt."""
    if not isinstance(body, str) or not body.strip():
        return []  # text_errors handles this.
    return chronology_errors(packet, body)


def editorial_warnings(packet, body):
    """Return internal quality notes that never block or unpublish a reading."""
    if not isinstance(body, str) or not body.strip():
        return []  # Hard validity checks handle unusable output.
    from plain_readings import WORD_RANGES
    product = packet.get('product')
    target = WORD_RANGES.get(product)
    warnings = []
    word_count = len(re.findall(r"\b[\w’'-]+\b", body))
    if target:
        low, high = target
        if word_count > high:
            warnings.append(f'above soft word target: {word_count} words (aim {low}-{high})')
        elif word_count < low:
            warnings.append(f'below soft word target: {word_count} words (aim {low}-{high})')

    sentences = [re.sub(r'\s+', ' ', sentence).strip().casefold()
                 for sentence in re.split(r'(?<=[.!?])\s+', body) if sentence.strip()]
    if len(sentences) != len(set(sentences)):
        warnings.append('repeated sentence; tighten before the next editorial pass')

    for verb in ('write', 'jot', 'draft', 'list', 'notice'):
        uses = len(re.findall(rf'\b{verb}(?:s|d|ing)?\b', body, re.I))
        if uses > 1:
            warnings.append(f"repeated action verb '{verb}' ({uses} uses)")
    return warnings


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
