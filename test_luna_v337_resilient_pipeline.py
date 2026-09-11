from __future__ import annotations

import json
from pathlib import Path

from luna_guided_voice import facts_hash, generate_guided_voice_copy
from luna_voice_provider import _json_content


def test_provider_unwraps_singleton_object_array():
    assert _json_content('[{"headline":"READY"}]') == {"headline": "READY"}


def test_python_attaches_provenance_instead_of_model(monkeypatch):
    facts = {
        "sign": "Gemini",
        "date": "2026-09-11",
        "active_planets": ["Moon", "Mars"],
        "aspect": "Moon sextile Mars",
        "orb": 2.11,
    }

    def fake_provider(prompt, **kwargs):
        assert '"facts_hash"' not in prompt
        schema = kwargs["response_format"]["json_schema"]["schema"]
        assert "facts_hash" not in schema["properties"]
        return {
            "headline": "MOVE WITHOUT FORCING THE MOMENT.",
            "opening": "The calculated opening is useful when handled deliberately.",
            "story": [
                "The Moon makes the reaction immediate enough to notice.",
                "Mars supplies movement, but judgement still chooses the direction.",
            ],
            "affirmation": "You can act without abandoning your judgement.",
            "your_move": "Check the evidence. Make one deliberate move.",
        }

    monkeypatch.setattr("luna_guided_voice.generate_openai_compatible_json", fake_provider)
    copy = generate_guided_voice_copy(
        "daily",
        facts,
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-key",
    )
    assert copy["facts_hash"] == facts_hash("daily", facts)


def test_daily_workflow_checkpoints_and_can_retry_one_sign():
    script = Path("scripts/generate_daily_voice.py").read_text(encoding="utf-8")
    assert 'parser.add_argument(\n        "--sign"' in script
    assert "except Exception as exc:" in script
    assert "write_daily_voice_document(" in script
    assert 'status[sign] = "failed"' in script
    assert "return 0 if successes or copies else 1" in script


def test_natal_and_year_ahead_derive_sun_sign_from_birth_data():
    app = Path("app.py").read_text(encoding="utf-8")
    natal = app.split("def natal_snapshot_page", 1)[1].split("\ndef ", 1)[0]
    timing = app.split("def timing_map_page", 1)[1].split("def solar_year_page", 1)[0]
    assert "What is your Sun sign (star sign)?" not in natal
    assert "What is your Sun sign (star sign)?" not in timing
    assert "calculated_sign = _monthly_sun_sign_from_snapshot(snapshot)" in natal
    assert "calculated_sign = _monthly_sun_sign_from_snapshot(snapshot)" in timing


def test_daily_workflow_exposes_targeted_retry_input():
    workflow = Path(".github/workflows/generate-daily-voice.yml").read_text(encoding="utf-8")
    assert "Optional sign to retry" in workflow
    assert 'args+=(--sign "$REQUESTED_SIGN")' in workflow


def test_daily_document_manifest_is_serializable():
    from daily_voice_publisher import make_daily_voice_document
    from datetime import date

    document = make_daily_voice_document(
        date(2026, 9, 11),
        "Australia/Sydney",
        {},
        status={"Gemini": "failed"},
        diagnostics={"Gemini": "provider response malformed"},
    )
    encoded = json.dumps(document)
    assert '"Gemini": "failed"' in encoded
