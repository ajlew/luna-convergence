from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from timing_map import TransitHit, TransitPeriod, TransitStory, TimingMapReport
from year_ahead import build_year_games, build_year_packet, _serialize_story
from year_ahead_voice import _voice_source, generate_year_ahead_voice


def _story(index: int) -> TransitStory:
    start = date(2026, 10, 10) + timedelta(days=index * 40)
    hit_day = start + timedelta(days=7)
    end = start + timedelta(days=24)
    planets = ("Saturn", "Pluto", "Jupiter", "Uranus", "Neptune")
    targets = ("Venus", "Mercury", "Mars", "Sun", "Moon", "Saturn", "Jupiter", "Venus")
    planet = planets[index % len(planets)]
    target = targets[index % len(targets)]
    polarity = "opportunity" if planet == "Jupiter" else ("pressure" if index % 2 == 0 else "structural")
    hit = TransitHit(
        exact_date=hit_day,
        orb=0.01,
        retrograde=False,
        exact_time="12:30",
        pass_number=1,
        pass_label="Initial activation",
        transit_longitude=42.5 + index,
        transit_sign="Taurus",
        transit_degree=12.5 + (index % 10),
    )
    return TransitStory(
        transit_planet=planet,
        natal_target=target,
        aspect="square" if index % 2 == 0 else "trine",
        natal_house=None,
        score=5.0 - index * 0.2,
        polarity=polarity,
        headline=f"GAME SIGNAL {index + 1}",
        summary="A calculated annual theme.",
        scenarios=("A deterministic scenario.",),
        insight="A deterministic insight.",
        question="What changes now?",
        move="Make the next condition explicit.",
        watch="Do not over-carry the old arrangement.",
        periods=(TransitPeriod(start, end),),
        hits=(hit,),
        natal_longitude=300.0 + index,
        natal_sign="Aquarius",
        natal_degree=10.0 + index,
    )


def _report() -> TimingMapReport:
    stories = tuple(_story(i) for i in range(8))
    return TimingMapReport(
        start_date=date(2026, 10, 10),
        end_date=date(2027, 10, 9),
        timezone_name="Australia/Sydney",
        stories=stories,
        major_games=3,
        turning_points=sum(len(story.hits) for story in stories),
        rule_changes=2,
    )


def _unknown_time_snapshot():
    return SimpleNamespace(
        positions=(),
        signatures=(),
        birth_time_known=False,
        dominant_element="",
        dominant_modality="",
        concentration_theme={},
        ascendant=None,
        midheaven=None,
    )


def test_definition_of_done_core_packet():
    report = _report()
    packet = build_year_packet(_unknown_time_snapshot(), report)

    assert (packet.end_date - packet.start_date).days == 364
    assert len(report.stories) == 8
    assert 3 <= len(packet.games) <= 5
    assert packet.year_strip
    assert all("phase" in item for item in packet.year_strip)
    assert "ascendant" not in packet.natal_fingerprint
    assert "midheaven" not in packet.natal_fingerprint


def test_exact_position_evidence_is_preserved():
    story = _story(0)
    row = _serialize_story(story)

    assert row["natal_position"]["sign"] == "Aquarius"
    assert row["natal_position"]["longitude"] is not None
    assert row["passes"][0]["transit_position"]["sign"] == "Taurus"
    assert row["passes"][0]["transit_position"]["longitude"] is not None
    assert row["passes"][0]["orb"] == pytest.approx(0.01)


def test_voice_packet_is_compact_and_has_no_rank_internals():
    packet = build_year_packet(_unknown_time_snapshot(), _report())
    source = _voice_source(packet)
    text = repr(source)

    assert "base_score" not in text
    assert "exactness_bonus" not in text
    assert "overlap_count" not in text
    assert source["games"]


def test_voice_makes_exactly_one_plain_prose_provider_call(monkeypatch):
    packet = build_year_packet(_unknown_time_snapshot(), _report())
    calls = []

    class Response:
        status_code = 200
        text = ""

        def json(self):
            return {
                "choices": [
                    {
                        "message": {"content": "Your year moves through a clear sequence of choices."},
                        "finish_reason": "stop",
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return Response()

    monkeypatch.setattr("year_ahead_voice.requests.post", fake_post)

    prose = generate_year_ahead_voice(
        packet,
        base_url="https://example.invalid/openai/v1",
        model="openai/gpt-oss-120b",
        api_key="test-key",
    )

    assert prose
    assert len(calls) == 1
    payload = calls[0][1]["json"]
    assert "response_format" not in payload


def test_app_uses_new_year_ahead_path_only():
    app = Path("app.py").read_text(encoding="utf-8")
    start = app.index("def timing_map_page() -> None:")
    end = app.index("def solar_year_page() -> None:")
    block = app[start:end]

    assert "from year_ahead import build_year_packet" in app
    assert "from year_ahead_view import render_year_ahead" in app
    assert "year_packet = build_year_packet(timing_snapshot, report)" in block
    assert "render_year_ahead(" in block

    # Old multi-call Year Ahead architecture must stay removed.
    assert "yearly_facts = {" not in block
    assert '_guided_luna_collection("yearly_transits"' not in block
    assert 'st.session_state["yearly-voice-bundle-v336"]' not in block

    # year_ahead_view owns the final year strip; app.py should not render a duplicate.
    assert "_timing_strip_html(report)" not in block
    assert "_timing_signal_strip(report)" not in block


def test_source_invariants_for_selection_and_voice():
    timing = Path("timing_map.py").read_text(encoding="utf-8")
    voice = Path("year_ahead_voice.py").read_text(encoding="utf-8")

    assert 'FAST_TRIGGER_PLANETS = ("Sun", "Mercury", "Venus", "Mars")' in timing
    assert 'end_date = start_date + timedelta(days=364)' in timing
    assert 'for offset in range(365)' in timing
    assert 'max_stories = min(int(max_stories), 12)' in timing

    assert "TARGET_TOTAL_TOKENS" in voice
    assert "def _prepare_request(" in voice
    assert "response_format" not in voice
    assert "for _attempt" not in voice
