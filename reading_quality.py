"""Prompt grounding and lightweight event coverage; never an LLM JSON schema."""
import re

WRITING_REVISION = 'event-grounding-2'


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
    return ['Explain the supplied event: '+label for label in required_events(packet)
            if not event_present(label, body)]


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
    brief['required_turning_points'] = required_events(packet)
    # Includes Daily supporting influences which previously disappeared from the prompt.
    brief['calculated_labels'] = packet.get('calculation_header', [])
    return brief
