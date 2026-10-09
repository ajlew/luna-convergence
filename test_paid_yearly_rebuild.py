from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from year_ahead_pdf import build_year_ahead_pdf, year_ahead_filename
import year_ahead_voice


def _packet() -> dict:
    primary = {
        "technical_label": "Saturn square natal Venus",
        "natal_target": "Venus",
        "natal_house": 7,
        "natal_position": {"longitude": 312.5, "sign": "Aquarius", "degree": 12.5},
        "summary": "Commitment and reciprocity require clearer terms.",
        "start": "2026-10-14",
        "end": "2027-03-22",
        "passes": [
            {
                "pass_number": 1,
                "pass_label": "Initial activation",
                "date": "2026-10-14",
                "time": "09:42",
                "retrograde": False,
                "orb": 0.01,
                "transit_position": {"longitude": 42.5, "sign": "Taurus", "degree": 12.5},
            },
            {
                "pass_number": 2,
                "pass_label": "Retrograde return",
                "date": "2027-01-07",
                "time": "16:18",
                "retrograde": True,
                "orb": 0.02,
                "transit_position": {"longitude": 42.48, "sign": "Taurus", "degree": 12.48},
            },
            {
                "pass_number": 3,
                "pass_label": "Final pass",
                "date": "2027-03-22",
                "time": "03:11",
                "retrograde": False,
                "orb": 0.01,
                "transit_position": {"longitude": 42.5, "sign": "Taurus", "degree": 12.5},
            },
        ],
        "triggers": [],
    }
    return {
        "version": "1.0",
        "period": {"start": "2026-10-10", "end": "2027-10-09", "timezone": "Australia/Sydney"},
        "natal_fingerprint": {
            "birth_time_known": True,
            "sun": {"sign": "Sagittarius", "degree": 9.1},
            "moon": {"sign": "Pisces", "degree": 12.4},
            "ascendant": {"sign": "Libra", "degree": 4.2},
            "dominant_element": "Fire",
            "dominant_modality": "Mutable",
            "strongest_signatures": [],
        },
        "year_statistics": {"major_games": 1, "turning_points": 3, "rule_changes": 1},
        "year_strip": [{"month": "OCT", "intensity": 0.8, "phase": "PRESSURE"}],
        "games": [
            {
                "number": 1,
                "title": "THE AGREEMENT GETS TESTED",
                "strategic_frame": "Make the agreement explicit.",
                "start_date": "2026-10-14",
                "end_date": "2027-03-22",
                "human_life_area": "relationships, money and value",
                "polarity": "pressure",
                "primary_transit": primary,
                "supporting_transits": [],
                "advantage": "Clarity improves your position.",
                "risk": "Ambiguity transfers cost to you.",
                "move": "Name the terms and stopping point.",
                "dont": "Do not reward vagueness with more commitment.",
            }
        ],
        "packet_hash": "paid-year-test",
    }


def test_paid_app_uses_new_year_ahead_architecture_only():
    source = Path("app.py").read_text(encoding="utf-8")
    payment_start = source.index("def payment_success_page() -> None:")
    payment_end = source.index("def _natal_input_fields(", payment_start)
    payment = source[payment_start:payment_end]
    owner_start = source.index("def _owner_report_output(")
    owner_end = source.index("def report_cta(", owner_start)
    owner = source[owner_start:owner_end]

    assert "return start_date + timedelta(days=364)" in source
    assert "_build_paid_year_ahead_product(" in payment
    assert "build_year_ahead_pdf(" in payment
    assert "_render_paid_year_ahead_product(" in payment
    assert "_build_paid_year_ahead_product(" in owner
    assert "build_year_ahead_pdf(" in owner
    assert "_render_paid_year_ahead_product(" in owner

    # The old paid Yearly architecture is no longer a customer path.
    assert "_prepare_paid_yearly_personal_layer" not in source
    assert "def _render_snapshot_yearly_report" not in source


def test_paid_voice_is_one_plain_prose_call_with_reader_context(monkeypatch):
    calls = []

    class Response:
        status_code = 200
        text = ""

        def json(self):
            return {
                "choices": [
                    {
                        "message": {"content": "Your year asks for clearer terms."},
                        "finish_reason": "stop",
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        calls.append(kwargs["json"])
        return Response()

    monkeypatch.setattr(year_ahead_voice.requests, "post", fake_post)
    prose = year_ahead_voice.generate_year_ahead_voice(
        _packet(),
        base_url="https://example.invalid/v1",
        model="openai/gpt-oss-120b",
        api_key="test",
        reader_context={
            "main_priority": "Relationships",
            "personal_question": "What should I commit to?",
        },
    )

    assert prose
    assert len(calls) == 1
    assert "Relationships" in calls[0]["messages"][1]["content"]
    assert "What should I commit to?" in calls[0]["messages"][1]["content"]
    assert "response_format" not in calls[0]


def test_paid_pdf_uses_finished_packet_and_same_voice():
    pdf = build_year_ahead_pdf(
        _packet(),
        voice_prose="Your year asks for clearer terms.",
        sign="Sagittarius",
        label="10 Oct 2026 - 9 Oct 2027",
        main_focus="Relationships",
        personal_question="What should I commit to?",
        order_reference="TEST-YEAR",
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 5000
    assert year_ahead_filename("Sagittarius", "2026-10-10", "2027-10-09") == (
        "2026-10-10_to_2027-10-09_Sagittarius_Year_Ahead.pdf"
    )
