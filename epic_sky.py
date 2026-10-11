"""Optional mythic editorial layer. Does not alter or calculate astrological facts."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent / 'generated' / 'epic_sky'

PROMPT = '''LUNA'S EPIC SKY — SEVEN-DAY EDITORIAL PROMPT
Write seven consecutive miniature episodes of Greek-inspired, unrhymed epic free verse (70–110 words each), one for each supplied calculated day.
Use the Greek mythic names Selene (Moon), Ares (Mars), Cronus (Saturn), Helios (Sun), Zeus (Jupiter), Hades (Pluto), Aphrodite (Venus). These are literary analogues, not assertions that planets are gods.
Maintain Monday–Sunday continuity. Applying = tension approaching; exact = culmination; opening = aftermath/new phase; station = pivot. A repeated aspect must advance its earlier episode, not repeat it.
Each day: title, concise encounter, recognizable human trial, ending 'Your move: <one imperative>'.
NO rhymes, fabricated dates/houses/aspects, false guarantees, vague 'universe holds its breath', childlike couplets, or invented astronomical conclusions.
Do not change the supplied aspects or phases. Astrology is symbolic interpretation.
Return plain text, no JSON. Below are authoritative card facts; do not reinterpret technical relationships:
'''


def prompt_from_cards(cards):
    lines = []
    for card in cards:
        lines.append(f"{card.get('date', '')}: {card.get('event', '')} | {card.get('timing', '')} | {card.get('technical', '')}")
    return PROMPT + '\n'.join(lines)


def load_approved(monday: date, cards: list[dict]):
    """Only use pre-approved sample if it matches the seven authoritative cards."""
    path = ROOT / f'{monday.isoformat()}_Australia-Sydney.json'
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        days = value['days']
        if value.get('status') != 'approved' or len(days) != 7 or len(cards) != 7:
            return None
        for day, card in zip(days, cards):
            if day['date'] != card['date'] or day['event'] != card['event']:
                return None
            if not day.get('title') or not day.get('body') or not day.get('move'):
                return None
        return value
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def to_script(data):
    return '\n\n'.join(f"{date.fromisoformat(d['date']):%A %d %B} — {d['title']}\n{d['event']}\n\n{d['body']}\n\nYour move: {d['move']}" for d in data['days'])
