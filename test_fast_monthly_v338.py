from __future__ import annotations

from pathlib import Path

from luna_guided_voice import collection_facts_hash, facts_hash
from monthly_voice_publisher import (
    load_monthly_voice_candidate,
    make_monthly_voice_document,
    monthly_candidate_path,
    write_monthly_voice_document,
)


def _main(facts: dict) -> dict:
    return {
        "headline": "A practical month takes shape",
        "opening": "Use the opening without pretending every detail is settled.",
        "story": [
            "The first movement asks for a clear decision.",
            "The middle of the month tests the terms already chosen.",
            "The final movement rewards deliberate follow-through.",
        ],
        "affirmation": "You can revise a plan without abandoning its purpose.",
        "your_move": "Choose one useful commitment and make its terms explicit.",
        "facts_hash": facts_hash("monthly", facts),
    }


def _events(facts: dict) -> dict:
    return {
        "items": [
            {
                "source_id": "11 SEP:0",
                "headline": "The month turns here",
                "story": "A practical choice becomes visible and asks for a measured response.",
                "affirmation": "You can respond without rushing the outcome.",
                "your_move": "Check the terms before you commit.",
            }
        ],
        "facts_hash": collection_facts_hash("monthly_events", facts),
    }


def test_monthly_candidate_is_locked_to_current_calculations(tmp_path: Path):
    main_facts = {
        "sign": "Libra",
        "period": "2026-09",
        "timezone": "Australia/Sydney",
        "events": [],
    }
    event_facts = {
        "sign": "Libra",
        "period": "2026-09",
        "timezone": "Australia/Sydney",
        "items": [
            {
                "source_id": "11 SEP:0",
                "date": "11 SEP",
                "technical": "New Moon in Virgo",
            }
        ],
    }
    path = monthly_candidate_path(2026, 9, "Australia/Sydney", root=tmp_path)
    document = make_monthly_voice_document(
        2026,
        9,
        "Australia/Sydney",
        {"Libra": {"main": _main(main_facts), "dated_events": _events(event_facts)}},
    )
    write_monthly_voice_document(path, document)

    loaded = load_monthly_voice_candidate(
        "Libra", 2026, 9, "Australia/Sydney", main_facts, event_facts, root=tmp_path
    )
    assert loaded and loaded["main"] and loaded["dated_events"]

    changed = dict(main_facts)
    changed["events"] = [{"date": "12 SEP"}]
    stale = load_monthly_voice_candidate(
        "Libra", 2026, 9, "Australia/Sydney", changed, event_facts, root=tmp_path
    )
    assert stale and stale["main"] is None
    assert stale["dated_events"] is not None


def test_public_monthly_source_has_no_natal_form_or_live_voice_in_published_mode():
    source = Path("app.py").read_text(encoding="utf-8")
    start = source.index("def _free_monthly_profile")
    end = source.index("def _monthly_sun_sign_from_snapshot", start)
    public_form = source[start:end]
    assert "birth_date" not in public_form
    assert "birth_time" not in public_form
    assert "birth_city" not in public_form
    assert 'LUNA_VOICE_MODE == "live"' in source
    assert "load_monthly_voice_candidate" in source

