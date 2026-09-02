from __future__ import annotations

import ast
from datetime import date
import json
from pathlib import Path

from weekly_view import build_weekly_view
from weekly_voice_composer import (
    build_weekly_voice_packet,
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
    sections = []
    for event in packet["events"]:
        sections.append(
            {
                "source_id": event["source_id"],
                "evidence": event["evidence"],
                "headline": f"HANDLE {event['technical_label'].upper()}.",
                "experience": event["approved_experience"],
                "meaning": event["approved_meaning"],
                "move": event["approved_move"],
            }
        )
    return {
        "headline": "CONTAIN THE PRESSURE. BUILD THE OPENING.",
        "thesis": (
            "Hold the emotional weight without handing it the steering wheel. "
            "Use support where it exists and change the method where resistance persists."
        ),
        "sections": sections,
        "closing_rule": "Contain the pressure. Choose the durable move.",
    }


def test_packet_is_closed_hashed_and_contains_no_natal_details():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)

    assert packet["schema_version"] == "1.0"
    assert len(packet["source_hash"]) == 64
    assert len(packet["events"]) == 7
    assert packet["guardrails"]["model_role"] == "voice and synthesis only"
    assert packet["calculated_pattern"]["controlling_planet"] == "Saturn"
    assert packet["events"][1]["aspect"] == "trine"
    assert packet["events"][1]["role"] == "opening"
    serialized = json.dumps(packet).lower()
    assert "birth_time" not in serialized
    assert "birth_place" not in serialized
    assert "email" not in serialized


def test_valid_copy_passes_and_preserves_every_evidence_line():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)
    copy = _copy(packet)

    result = validate_weekly_voice_copy(copy, packet)

    assert result.valid, result.errors
    assert [item["evidence"] for item in copy["sections"]] == [
        item["evidence"] for item in packet["events"]
    ]


def test_validator_rejects_changed_evidence_invented_fact_and_question():
    packet = build_weekly_voice_packet(_days(), MONDAY, TZ)
    copy = _copy(packet)
    copy["sections"][0]["evidence"] = "Moon conjunct Saturn · exact at 9:99 pm"
    copy["thesis"] += " Pluto guarantees the worst is over. What could go wrong?"

    result = validate_weekly_voice_copy(copy, packet)
    joined = " ".join(result.errors).lower()

    assert not result.valid
    assert "changed its technical evidence" in joined
    assert "unsupplied planet" in joined
    assert "prohibited certainty" in joined
    assert "question" in joined
    assert "invented numeric evidence" in joined


def test_loader_rejects_candidate_when_calculated_source_hash_changes(tmp_path: Path):
    days = _days()
    packet = build_weekly_voice_packet(days, MONDAY, TZ)
    document = make_candidate_document(
        _copy(packet), packet, provider="test", model="test-model"
    )
    document["source_hash"] = "0" * 64
    path = candidate_path(MONDAY, TZ, tmp_path)
    path.write_text(json.dumps(document), encoding="utf-8")

    loaded = load_weekly_voice_candidate(days, MONDAY, TZ, tmp_path)

    assert loaded.copy is None
    assert "Calculated evidence changed" in " ".join(loaded.validation.errors)


def test_loader_accepts_only_a_matching_validated_candidate(tmp_path: Path):
    days = _days()
    packet = build_weekly_voice_packet(days, MONDAY, TZ)
    document = make_candidate_document(
        _copy(packet), packet, provider="test", model="test-model"
    )
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


def test_public_weekly_page_does_not_call_voice_preview():
    tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
    functions = {
        node.name: ast.get_source_segment(Path("app.py").read_text(encoding="utf-8"), node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "_render_weekly_voice_preview" not in functions["weekly_page"]
    assert "_render_weekly_voice_preview" in functions["weekly_studio_page"]
    assert "generate_openai_compatible_json" not in Path("app.py").read_text(encoding="utf-8")
