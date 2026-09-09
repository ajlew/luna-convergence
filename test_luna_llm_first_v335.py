from pathlib import Path
import re

from luna_guided_voice import (
    build_guided_collection_prompt,
    collection_facts_hash,
    generate_guided_collection_copy,
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


def test_build_label_is_v3352():
    config = Path("site_config.py").read_text(encoding="utf-8")
    assert "Luna v3.35.2 — Sign Feed Recovery" in config


def test_shared_week_context_is_valid_evidence_for_each_sign():
    facts = {
        "shared_context": {
            "events": [
                {
                    "technical_label": "Mercury opposite Neptune",
                    "planets": ["Mercury", "Neptune"],
                    "orb_degrees": 0.19,
                }
            ]
        },
        "items": [
            {
                "source_id": "Libra",
                "sign": "Libra",
                "houses": [1, 7],
                "life_areas": ["identity", "relationships"],
            }
        ],
    }
    copy = {
        "items": [
            {
                "source_id": "Libra",
                "headline": "CHECK THE MESSAGE BEFORE YOU REACT.",
                "story": "Mercury opposite Neptune puts a 0.19 degree blur around messages affecting identity and relationships. Verification gives you room to respond cleanly.",
                "affirmation": "You can trust yourself enough to check the evidence.",
                "your_move": "Verify the message. Then state the clean answer.",
            }
        ],
        "facts_hash": collection_facts_hash("weekly_signs", facts),
    }
    valid, errors = validate_guided_collection_copy("weekly_signs", copy, facts)
    assert valid, errors


def test_invalid_full_batch_recovers_each_item_independently(monkeypatch):
    facts = _facts()

    def fake_provider(prompt, **_kwargs):
        payload = __import__("json").loads(prompt.split("CALCULATED COLLECTION:\n", 1)[1].split("\n\nCORRECTION REPORT:", 1)[0])
        supplied = payload["facts"]["items"]
        items = [
            {
                "source_id": item["source_id"],
                "headline": "USE THE SIGNAL WITHOUT INVENTING A STORY.",
                "story": f"For {item['source_id']}, the calculated pattern names a real pressure point. Stay close to the supplied evidence and make the practical choice available now.",
                "affirmation": "You can meet clear evidence with a clear response.",
                "your_move": "Check the evidence. Choose the useful next step.",
            }
            for item in supplied
        ]
        if len(items) > 1:
            items.reverse()
        return {"items": items, "facts_hash": payload["facts_hash"]}

    monkeypatch.setattr("luna_guided_voice.generate_openai_compatible_json", fake_provider)
    copy = generate_guided_collection_copy(
        "weekly_days",
        facts,
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-key",
    )
    assert [item["source_id"] for item in copy["items"]] == [
        item["source_id"] for item in facts["items"]
    ]
    valid, errors = validate_guided_collection_copy("weekly_days", copy, facts)
    assert valid, errors


def test_public_weekly_page_requests_only_the_selected_sign():
    app = Path("app.py").read_text(encoding="utf-8")
    match = re.search(
        r"def _render_weekly_sign_layer\([\s\S]+?(?=\ndef _weekly_choice_options)",
        app,
    )
    assert match
    body = match.group(0)
    assert "_weekly_single_sign_voice" in body
    assert "_weekly_sign_voice_collection" not in body
