"""Optional mythic editorial layer. Does not alter or calculate astrological facts."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent / 'generated' / 'epic_sky'

PROMPT = '''LUNA'S EPIC SKY — SEVEN-DAY EDITORIAL PROMPT
Write seven consecutive miniature episodes of Greek-inspired, unrhymed epic free verse (exactly four very short stanzas per day, 30-40 words total), one for each supplied calculated day.
Use the Greek mythic names Selene (Moon), Ares (Mars), Cronus (Saturn), Helios (Sun), Zeus (Jupiter), Hades (Pluto), Aphrodite (Venus). These are literary analogues, not assertions that planets are gods.
Maintain Monday–Sunday continuity. Applying = tension approaching; exact = culmination; opening = aftermath/new phase; station = pivot. A repeated aspect must advance its earlier episode, not repeat it.
Each day: title, four stanzas of 1–2 short lines each (no more than 9 words per stanza), recognizable human trial, ending 'Your move: <one imperative>'.
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

# On-demand generation. One plain-text provider call; no background job or retries.
import re
import requests


def generation_prompt(cards):
    if len(cards) != 7:
        raise ValueError('Epic Sky requires seven authoritative daily cards.')
    base = prompt_from_cards(cards)
    return (base + '\n\nOUTPUT FORMAT (repeat exactly 7 times, with DAY 1 through DAY 7):\n'
            'DAY 1\nTITLE: A vivid mythic title\nSTORY: Exactly four short stanzas separated by blank lines; 1–2 lines per stanza, 32–48 words total, unrhymed epic verse.\nYOUR MOVE: One short imperative.\n'
            'DAY 2\nTITLE: ...\nSTORY: ...\nYOUR MOVE: ...\n'
            'Continue through DAY 7. Use the dates and aspects only in the authoritative input, '
            'and DO NOT insert dates or technical aspect labels inside the creative STORY. '
            'The application supplies dates and aspect captions from calculations. '
            'Never include markdown tables, extra DAY markers, or a prologue.\n')


def parse_generation(response_text, cards, monday):
    """Accept only seven structurally complete chapters; source all event labels from Python."""
    if len(cards) != 7 or any(not c.get('date') or not c.get('event') for c in cards):
        raise ValueError('Seven fully dated calculated events are required.')
    text = str(response_text or '').strip()
    starts = list(re.finditer(r'(?im)^\s*DAY\s+([1-7])\s*[:.\-]?\s*$', text))
    if len(starts) != 7 or [int(x.group(1)) for x in starts] != list(range(1, 8)):
        raise ValueError('Groq must return exactly DAY 1 through DAY 7. Nothing published.')
    days = []
    for i, heading in enumerate(starts):
        fragment = text[heading.end():starts[i+1].start() if i < 6 else len(text)].strip()
        match = re.fullmatch(r'(?is)TITLE:\s*(.+?)\s*STORY:\s*(.+?)\s*YOUR MOVE:\s*(.+)', fragment)
        if not match:
            raise ValueError(f'DAY {i+1} missing TITLE, STORY or YOUR MOVE.')
        title, body, move = (v.strip() for v in match.groups())
        if not title or not body or not move:
            raise ValueError(f'DAY {i+1} is incomplete.')
        days.append({'date': cards[i]['date'], 'event': cards[i]['event'],
                     'title': title, 'body': body, 'move': move})
    return {'product': 'epic_sky', 'period': monday.isoformat(), 'timezone': 'Australia/Sydney',
            'status': 'generated_draft', 'days': days}


def generate_week(monday, cards, *, base_url, model, api_key, post=None):
    """Explicit button action only. Exactly one Groq-compatible request."""
    if not (base_url and model and api_key):
        raise ValueError('Configure LUNA_VOICE_BASE_URL, LUNA_VOICE_MODEL and LUNA_VOICE_API_KEY.')
    if post is None:
        post = requests.post
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You write mythic prose from verified sky facts. Never calculate astrology. Output exactly the requested seven-section plain-text format.'},
            {'role': 'user', 'content': generation_prompt(cards)},
        ],
        'temperature': 0.6,
        'max_completion_tokens': 2700,
    }
    if str(model).startswith('openai/gpt-oss'):
        payload['reasoning_effort'] = 'low'
        payload['include_reasoning'] = False
    try:
        response = post(f'{base_url.rstrip("/")}/chat/completions',
                        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                        json=payload, timeout=150)
        response.raise_for_status()
        result = response.json()['choices'][0]
        if result.get('finish_reason') == 'length':
            raise ValueError('Groq ended at the token limit; nothing published.')
        data = parse_generation(result['message']['content'], cards, monday)
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(f'Epic Sky generation failed: {exc}') from exc
    return data
