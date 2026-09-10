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
    validate_guided_collection_copy,
)
from luna_report_bundle import assemble_report_bundle


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


def test_build_label_is_v336():
    config = Path("site_config.py").read_text(encoding="utf-8")
    assert "Luna v3.36 — Atomic Guided Reports" in config
