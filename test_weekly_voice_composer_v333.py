from __future__ import annotations

import ast
from datetime import date
import json
from pathlib import Path

from weekly_view import build_weekly_view
from weekly_voice_composer import (
    build_weekly_voice_packet,
    build_weekly_voice_prompt,
    candidate_path,
    load_weekly_voice_candidate,
    make_candidate_document,
    validate_weekly_voice_copy,
)


MONDAY = date(2026, 8, 31)
TZ = "Australia/Sydney"


def _days():
    return build_weekly_view(MONDAY, TZ)


def _copy(packet: dict) -> dict:
    return {
        "headline": "BUILD THE OPENING TO LAST.",
        "opening": (
            "This week asks for steadiness without emotional self-punishment. "
            "You do not need to become harder to become clearer."
        ),
        "story": [
            (
                "Moon conjunct Saturn makes responsibility feel personal, but a temporary weight is not a permanent verdict. "
                "Name what is actually yours to carry and put the rest back where it belongs."
            ),
            (
                "Jupiter trine Saturn gives growth a frame strong enough to hold it. Mars square Saturn supplies the useful warning: "
                "more force will only make the wall feel important. Change the method and keep the ambition."
            ),
            (
                "Sun trine Moon restores cooperation between direction and feeling, while the later lunar shifts expose what needs a cleaner message. "
                "Use the opening deliberately; ease is an invitation to act, not permission to drift."
            ),
        ],
        "affirmation": "You can respect the pressure without allowing it to define your possibilities.",
        "your_move": "Choose one worthwhile expansion. Give it a boundary, a budget and one visible next step.",
        "evidence_ids": [event["source_id"] for event in packet["events"]],
    }


def test_packet_is_closed_hashed_and_contains_no_legacy_or_natal_prose():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)

    assert packet["schema_version"] == "2.0"
    assert len(packet["source_hash"]) == 64
    assert len(packet["events"]) == 7
    assert "interpretation" in packet["guardrails"]["model_role"]
    assert packet["calculated_pattern"]["controlling_planet"] == "Saturn"
    assert packet["events"][1]["aspect"] == "trine"
    assert packet["events"][1]["role"] == "opening"
    assert len(packet["deduplicated_sky_events"]) == len(
        {label.lower() for label in packet["deduplicated_sky_events"]}
    )
    serialized = json.dumps(packet).lower()
    assert "approved_experience" not in serialized
    assert "existing_weekly_synthesis" not in serialized
    assert "birth_time" not in serialized
    assert "birth_place" not in serialized
    assert "email" not in serialized


def test_prompt_demands_one_connected_reading_and_earned_hope():
    prompt = build_weekly_voice_prompt(build_weekly_voice_packet(_days(), MONDAY, TZ))

    assert "not seven transit summaries" in prompt
    assert "earned hope" in prompt
    assert "emotional recognition" in prompt
    assert "evidence_ids" in prompt


def test_valid_connected_copy_passes_and_accounts_for_every_event():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)
    copy = _copy(packet)

    result = validate_weekly_voice_copy(copy, packet)

    assert result.valid, result.errors
    assert copy["evidence_ids"] == [event["source_id"] for event in packet["events"]]
    assert "sections" not in copy


def test_validator_rejects_missing_evidence_invented_fact_and_question():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)
    copy = _copy(packet)
    copy["evidence_ids"] = copy["evidence_ids"][:-1]
    copy["opening"] += " Pluto guarantees the worst is over. What could go wrong at 9:99?"

    result = validate_weekly_voice_copy(copy, packet)
    joined = " ".join(result.errors).lower()

    assert not result.valid
    assert "source ids" in joined
    assert "unsupplied planet" in joined
    assert "prohibited certainty" in joined
    assert "question" in joined
    assert "invented numeric evidence" in joined


def test_old_mechanical_seven_section_schema_is_rejected():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)
    old_copy = {
        "headline": "A HEADLINE",
        "thesis": "A thesis",
        "sections": [],
        "closing_rule": "A rule",
    }

    result = validate_weekly_voice_copy(old_copy, packet)

    assert not result.valid
    assert "connected weekly voice schema" in " ".join(result.errors)


def test_loader_rejects_candidate_when_calculated_source_hash_changes(tmp_path: Path):
    days = _days()
    packet = build_weekly_voice_packet(days, MONDAY, TZ)
    document = make_candidate_document(_copy(packet), packet, provider="test", model="test-model")
    document["source_hash"] = "0" * 64
    path = candidate_path(MONDAY, TZ, tmp_path)
    path.write_text(json.dumps(document), encoding="utf-8")

    loaded = load_weekly_voice_candidate(days, MONDAY, TZ, tmp_path)

    assert loaded.copy is None
    assert "Calculated evidence changed" in " ".join(loaded.validation.errors)


def test_loader_accepts_only_a_matching_validated_candidate(tmp_path: Path):
    days = _days()
    packet = build_weekly_voice_packet(days, MONDAY, TZ)
    document = make_candidate_document(_copy(packet), packet, provider="test", model="test-model")
    path = candidate_path(MONDAY, TZ, tmp_path)
    path.write_text(json.dumps(document), encoding="utf-8")

    loaded = load_weekly_voice_candidate(days, MONDAY, TZ, tmp_path)

    assert loaded.validation.valid
    assert loaded.copy == document["copy"]


def test_missing_candidate_returns_safe_fallback_status(tmp_path: Path):
    loaded = load_weekly_voice_candidate(_days(), MONDAY, TZ, tmp_path)

    assert loaded.copy is None
    assert not loaded.validation.valid
    assert "No generated candidate" in loaded.validation.errors[0]


def test_public_weekly_page_prefers_llm_voice_and_uses_factual_fallback():
    source = Path("app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: ast.get_source_segment(source, node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "_render_weekly_public_story" in functions["weekly_page"]
    assert "_render_weekly_synthesis" not in functions["weekly_page"]
    assert "_render_voice_unavailable" in functions["weekly_page"]
    assert "_weekly_llm_copy" in functions["_render_weekly_public_story"]
    assert 'secret("LUNA_VOICE_MODE", "published")' in source
