from __future__ import annotations

from datetime import date
from pathlib import Path
import json

from daily_voice_publisher import (
    daily_candidate_path,
    load_daily_voice_candidate,
    make_daily_voice_document,
    write_daily_voice_document,
)
from luna_guided_voice import (
    collection_facts_hash,
    facts_hash,
    generate_guided_voice_copy,
    validate_guided_collection_copy,
)
from luna_report_bundle import assemble_report_bundle
from luna_voice_provider import _json_content, generate_openai_compatible_json


def _daily_facts():
    return {
        "sign": "Aries",
        "date": "2026-09-10",
        "timezone": "Australia/Sydney",
        "active_planets": ["Moon", "Uranus"],
        "aspect": "Moon square Uranus",
        "orb": 1.95,
    }


def _daily_copy(facts):
    return {
        "headline": "CHECK THE CHANGE BEFORE CHASING IT.",
        "opening": "A surprise can expose the rule that no longer fits.",
        "story": [
            "The Moon brings the reaction close enough to feel immediate.",
            "Uranus makes the stale arrangement difficult to ignore.",
        ],
        "affirmation": "You can respond without surrendering your judgement.",
        "your_move": "Check the facts. Change one rule deliberately.",
        "facts_hash": facts_hash("daily", facts),
    }


def test_atomic_bundle_blocks_partial_monthly_output():
    bundle = assemble_report_bundle(
        "monthly",
        main=None,
        sections={"dated_events": {"facts_hash": "events"}},
        required_sections=("dated_events",),
    )
    assert bundle["complete"] is False
    assert bundle["status"] == "partial"
    assert bundle["missing_sections"] == ("main",)


def test_atomic_bundle_requires_personal_contacts_when_present():
    bundle = assemble_report_bundle(
        "monthly",
        main={"facts_hash": "main"},
        sections={"dated_events": {"facts_hash": "events"}, "personal_contacts": {}},
        required_sections=("dated_events", "personal_contacts"),
    )
    assert bundle["complete"] is False
    assert bundle["missing_sections"] == ("personal_contacts",)


def test_published_daily_candidate_is_locked_to_facts(tmp_path):
    facts = _daily_facts()
    copy = _daily_copy(facts)
    path = daily_candidate_path(date(2026, 9, 10), "Australia/Sydney", root=tmp_path)
    write_daily_voice_document(
        path,
        make_daily_voice_document(date(2026, 9, 10), "Australia/Sydney", {"Aries": copy}),
    )
    assert load_daily_voice_candidate(
        "Aries", date(2026, 9, 10), "Australia/Sydney", facts, root=tmp_path
    ) == copy
    changed = dict(facts, orb=1.96)
    assert load_daily_voice_candidate(
        "Aries", date(2026, 9, 10), "Australia/Sydney", changed, root=tmp_path
    ) is None


def test_collection_rejects_embedded_move_section():
    facts = {
        "items": [
            {
                "source_id": "Aries",
                "houses": [1, 7],
                "technical": "Moon square Uranus",
            }
        ]
    }
    copy = {
        "items": [
            {
                "source_id": "Aries",
                "headline": "CHANGE THE TERMS.",
                "story": "The agreement needs air. Your move: Check the facts before changing the terms.",
                "affirmation": "You can revise an agreement without losing yourself.",
                "your_move": "Check the facts before changing the terms.",
            }
        ],
        "facts_hash": collection_facts_hash("weekly_signs", facts),
    }
    valid, errors = validate_guided_collection_copy("weekly_signs", copy, facts)
    assert not valid
    assert any("reserved section label" in error for error in errors)
    assert any("repeats its dedicated your_move" in error for error in errors)


def test_natal_driven_forms_do_not_ask_for_sun_sign():
    app = Path("app.py").read_text(encoding="utf-8")
    monthly_form = app.split("def _free_monthly_profile", 1)[1].split(
        "def _monthly_sun_sign_from_snapshot", 1
    )[0]
    timing_form = app.split("def timing_map_page", 1)[1].split("def solar_year_page", 1)[0]
    assert "What is your Sun sign (star sign)?" not in monthly_form
    assert "What is your Sun sign (star sign)?" not in timing_form
    assert "timing-sun-sign-select-v9" not in timing_form
    assert 'st.session_state["timing-calculated-sun-sign-v336"]' in timing_form
    assert "_date_only_sun_sign_is_ambiguous" in timing_form


def test_published_daily_does_not_generate_on_page_visit():
    app = Path("app.py").read_text(encoding="utf-8")
    daily = app.split("def _render_lean_daily", 1)[1].split(
        "def _render_site_solar_wave", 1
    )[0]
    assert "load_daily_voice_candidate" in daily
    assert 'LUNA_VOICE_MODE == "live"' in daily


def test_build_label_is_v3366():
    config = Path("site_config.py").read_text(encoding="utf-8")
    assert "Luna v3.36.6 — Certainty Validation Recovery" in config


def test_footer_always_shows_build_label():
    app = Path("app.py").read_text(encoding="utf-8")
    footer = app.split("def footer()", 1)[1].split("install_css()", 1)[0]
    assert "<strong>Build:</strong> {escape(BUILD_LABEL)}" in footer


def test_daily_workflow_is_scheduled_and_date_is_optional():
    workflow = Path(".github/workflows/generate-daily-voice.yml").read_text(encoding="utf-8")
    assert 'cron: "10 14 * * *"' in workflow
    assert "required: false" in workflow
    script = Path("scripts/generate_daily_voice.py").read_text(encoding="utf-8")
    assert "datetime.now(timezone).date()" in script
    assert "default=8.0" in script


def test_featured_video_requires_week_lock():
    app = Path("app.py").read_text(encoding="utf-8")
    video = app.split("def _render_optional_luna_video", 1)[1].split(
        "def _render_lean_daily", 1
    )[0]
    assert "if not LUNA_YOUTUBE_FEATURED_VIDEO_WEEK_START" in video


def test_live_voice_requests_show_reader_progress():
    app = Path("app.py").read_text(encoding="utf-8")
    assert "_VOICE_LOADING_LABELS" in app
    assert "Keep this page open" in app
    assert "with st.spinner(_voice_loading_label(product))" in app


def test_daily_generation_repairs_single_paragraph_and_non_imperative(monkeypatch):
    facts = _daily_facts()
    calls = 0

    def fake_provider(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return {
            "headline": "CHECK THE CHANGE BEFORE CHASING IT.",
            "opening": "The reaction arrives before the explanation.",
            "story": [
                "The Moon makes the pressure immediate enough to notice. Uranus exposes the rule that no longer fits, so the interruption can become useful information."
            ],
            "affirmation": "You can respond without surrendering your judgement.",
            "your_move": "You should check the facts before reacting.",
            "facts_hash": facts_hash("daily", facts),
        }

    monkeypatch.setattr(
        "luna_guided_voice.generate_openai_compatible_json",
        fake_provider,
    )
    copy = generate_guided_voice_copy(
        "daily",
        facts,
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-key",
    )
    assert len(copy["story"]) == 2
    assert copy["your_move"].startswith("Do this:")
    assert calls == 1


def test_provider_recovers_first_complete_json_object_from_extra_data():
    first = {"headline": "USE THE FIRST COMPLETE OBJECT."}
    assert _json_content(json.dumps(first) + "\n" + json.dumps({"duplicate": True})) == first


def test_provider_keeps_json_mode_after_strict_schema_rejection(monkeypatch):
    payloads = []

    class FakeResponse:
        headers = {}

        def __init__(self, status_code, text="", data=None):
            self.status_code = status_code
            self.text = text
            self._data = data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(self.text)

        def json(self):
            return self._data

    responses = iter(
        [
            FakeResponse(400, '{"error":{"code":"json_validate_failed"}}'),
            FakeResponse(
                200,
                data={
                    "choices": [
                        {
                            "message": {"content": json.dumps({"status": "valid"})},
                            "finish_reason": "stop",
                        }
                    ]
                },
            ),
        ]
    )

    def fake_post(*_args, **kwargs):
        payloads.append(kwargs["json"])
        return next(responses)

    monkeypatch.setattr("luna_voice_provider.requests.post", fake_post)
    result = generate_openai_compatible_json(
        "Return JSON.",
        base_url="https://example.invalid",
        model="openai/gpt-oss-20b",
        api_key="test-key",
        response_format={"type": "json_schema", "json_schema": {"schema": {}}},
    )
    assert result == {"status": "valid"}
    assert payloads[1]["response_format"] == {"type": "json_object"}


def test_negated_guarantee_is_allowed_but_actual_promise_is_blocked():
    facts = _daily_facts()
    safe = _daily_copy(facts)
    safe["affirmation"] = "Nothing is guaranteed, but you can make the careful choice."
    from luna_guided_voice import validate_guided_voice_copy

    valid, errors = validate_guided_voice_copy("daily", safe, facts)
    assert valid, errors

    unsafe = _daily_copy(facts)
    unsafe["affirmation"] = "This guarantees the outcome you want."
    valid, errors = validate_guided_voice_copy("daily", unsafe, facts)
    assert not valid
    assert any("guarantee" in error for error in errors)
