"""Text-only 9:16 social-card voice from verified Weekly Studio sky cards.

Python owns event selection, date, and technical sky facts. The LLM supplies prose
only. No editorial post-processing, length gate, rewrite or automatic retry.
"""
from __future__ import annotations

import requests


def social_card_prompt(card: dict) -> str:
    if not isinstance(card, dict) or not card.get('date') or not card.get('event'):
        raise ValueError('A dated, calculated sky event is required before using Groq.')
    evidence = '\n'.join(f'{field}: {card[field]}' for field in ('date', 'event', 'timing', 'technical', 'timezone_label') if card.get(field))
    return ("LUNA CONVERGENCE — INSTAGRAM STORY SOCIAL CARD (1080 × 1920; 9:16)\n"
            "Write TEXT ONLY. The publisher creates the photographic background separately in Canva.\n"
            "Python has already selected the event and calculated the technical data. Do not calculate or invent any dates, astronomical facts, or aspects.\n"
            "Return exactly four short stanzas, each 2–3 short lines; aim for 40–65 words overall.\n"
            "Stanza 1: The Sky — vivid mythic opening grounded in the event.\n"
            "Stanza 2: The Meaning — the symbolic tension or transformation.\n"
            "Stanza 3: The Opportunity — an actionable possibility without promising an outcome.\n"
            "Stanza 4: The Move — a memorable invitation to deliberate action.\n"
            "Homeric in spirit, contemporary and understandable, unrhymed, concise and emotionally specific.\n"
            "No titles, headers, hashtags, emojis, Markdown, layout advice or background descriptions.\n"
            "Astrology is symbolic interpretation, not an assured prediction. Output only the poem.\n\n"
            "VERIFIED PYTHON EVIDENCE:\n" + evidence)


def generate_social_card(card: dict, *, base_url: str, model: str, api_key: str, post=None) -> str:
    prompt = social_card_prompt(card)
    if not all((base_url, model, api_key)):
        raise ValueError('Configure LUNA_VOICE_BASE_URL, LUNA_VOICE_MODEL and LUNA_VOICE_API_KEY.')
    post = post or requests.post
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are Luna. Write mythic poetic voice only from the supplied calculated sky evidence.'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.65,
        'max_completion_tokens': 420,
    }
    if str(model).startswith('openai/gpt-oss'):
        payload['reasoning_effort'] = 'low'
        payload['include_reasoning'] = False
    response = post(f'{base_url.rstrip("/")}/chat/completions',
                    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                    json=payload, timeout=90)
    response.raise_for_status()
    choice = response.json()['choices'][0]
    if choice.get('finish_reason') == 'length':
        raise RuntimeError('Provider truncated the social-card response. No automatic retry.')
    text = choice['message'].get('content')
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError('Provider returned no social-card text. No automatic retry.')
    return text  # unchanged, no post-LLM editorial gate or rewriting
