from datetime import date
from pathlib import Path

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import build_daily_narrative

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _payload(sign: str):
    d = date(2026, 8, 12)
    tz = "Australia/Sydney"
    reading = free_daily_reading(sign, d, tz)
    narrative = build_daily_narrative(
        reading,
        sign=sign,
        reading_date=d,
        timezone_name=tz,
        house_voice=HOUSE_VOICE,
        previous_texts=[],
    )
    return (
        narrative.hook_headline,
        narrative.today_story[0],
        narrative.action_today,
        narrative.reflection_questions[0],
    )


def test_all_twelve_signs_have_distinct_lean_daily_payloads():
    payloads = [_payload(sign) for sign in SIGNS]
    assert len(set(payloads)) == 12
    assert len({p[0] for p in payloads}) == 12
    assert len({p[1] for p in payloads}) == 12
    assert len({p[2] for p in payloads}) == 12
    assert len({p[3] for p in payloads}) == 12


def test_landing_page_does_not_session_cache_one_signs_narrative():
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    start = app.index("def _daily_narrative_for_landing")
    end = app.index("def _render_lean_daily", start)
    block = app[start:end]
    assert "lean_daily_cache_key" not in block
    assert "lean_daily_narrative" not in block
    assert "free_daily_reading(sign, reading_date, timezone_name)" in block
