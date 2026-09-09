from pathlib import Path
import re

from luna_guided_voice import (
    build_guided_collection_prompt,
    collection_facts_hash,
    validate_guided_collection_copy,
)


def _facts():
    return {
        "items": [
            {
                "source_id": "2026-09-08",
                "technical_label": "Uranus stations retrograde",
                "supporting_events": ["Moon sextile Uranus"],
            },
            {
                "source_id": "2026-09-09",
                "technical_label": "Mercury opposite Neptune",
                "orb": 0.19,
                "supporting_events": ["Mercury trine Pluto"],
            },
        ]
    }


def _copy():
    facts = _facts()
    return {
        "items": [
            {
                "source_id": "2026-09-08",
                "headline": "CHANGE THE RULE WITHOUT BURNING THE MAP.",
                "story": "Uranus turns the pressure inward while the Moon supplies a usable opening. Notice what suddenly feels too small, then separate a real need for freedom from a passing refusal to be told anything.",
                "affirmation": "You can revise the rule without wrecking the structure.",
                "your_move": "Name the stale rule. Test one cleaner alternative.",
            },
            {
                "source_id": "2026-09-09",
                "headline": "CHECK THE BEAUTIFUL EXPLANATION.",
                "story": "Mercury opposite Neptune can make a polished story feel true before it has earned the privilege. Mercury trine Pluto supports a deeper check, so follow the detail that survives scrutiny.",
                "affirmation": "Uncertainty can sharpen your judgement.",
                "your_move": "Verify the message. Then answer the evidence.",
            },
        ],
        "facts_hash": collection_facts_hash("weekly_days", facts),
    }


def test_guided_collection_preserves_all_sources_and_validates():
    valid, errors = validate_guided_collection_copy("weekly_days", _copy(), _facts())
    assert valid, errors


def test_guided_collection_rejects_source_and_numeric_invention():
    copy = _copy()
    copy["items"][0]["source_id"] = "invented"
    copy["items"][1]["story"] += " It becomes exact at 9:99."
    valid, errors = validate_guided_collection_copy("weekly_days", copy, _facts())
    joined = " ".join(errors).lower()
    assert not valid
    assert "source ids" in joined
    assert "invented numeric" in joined


def test_voice_prompt_requires_human_story_and_earned_hope():
    prompt = build_guided_collection_prompt("weekly_days", _facts()).lower()
    for phrase in ("emotional", "earned hope", "dryly cheeky", "ordinary language", "your_move"):
        assert phrase in prompt


def test_customer_pages_do_not_call_legacy_interpretation_fallbacks():
    app = Path("app.py").read_text(encoding="utf-8")
    assert 'headline = "CALCULATIONS READY. LUNA\'S VOICE IS PAUSED."' in app
    assert '_guided_luna_collection("weekly_days"' in app
    assert '"weekly_signs"' in app
    assert re.search(r'_guided_luna_collection\(\s*"monthly_events"', app)
    assert re.search(r'_guided_luna_collection\(\s*"natal_signatures"', app)
    assert re.search(r'_guided_luna_collection\(\s*"yearly_transits"', app)
    assert '_guided_luna_copy("solar"' in app


def test_build_label_is_v335():
    config = Path("site_config.py").read_text(encoding="utf-8")
    assert "Luna v3.35 — LLM First" in config
