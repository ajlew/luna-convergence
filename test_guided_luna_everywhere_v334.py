from pathlib import Path
import re

from luna_guided_voice import facts_hash, validate_guided_voice_copy


def _facts():
    return {
        "sign": "Virgo",
        "aspect": "Mercury opposite Neptune",
        "orb": 0.19,
        "phase": "applying",
        "houses": [1, 7],
        "support": "Mercury trine Pluto",
    }


def _copy(product="daily"):
    facts = _facts()
    story = [
        "Mercury opposite Neptune makes the first explanation less reliable than it looks. Let uncertainty slow the reply without letting it own the day.",
        "Mercury trine Pluto supports a deeper check. Look beneath the obvious wording and give the useful fact time to emerge.",
    ]
    if product in {"monthly", "natal", "yearly"}:
        story.append("The pressure and support belong to one pattern: clarity grows when attention becomes more deliberate.")
    if product == "yearly":
        story.append("Treat the longer cycle as a strategy problem and revise the plan when the evidence changes.")
    return {
        "headline": "CHECK THE MESSAGE BEFORE BELIEVING THE MOOD.",
        "opening": "The signal matters, but your first interpretation may not be the final one.",
        "story": story,
        "affirmation": "You can pause without losing momentum.",
        "your_move": "Verify the fact. Then answer what is actually there.",
        "facts_hash": facts_hash(product, facts),
    }


def test_guided_voice_validates_closed_calculated_facts():
    valid, errors = validate_guided_voice_copy("daily", _copy(), _facts())
    assert valid, errors


def test_guided_voice_rejects_wrong_fact_packet_and_invention():
    copy = _copy()
    copy["facts_hash"] = "wrong"
    copy["story"][0] += " Jupiter guarantees success at 9:99."
    valid, errors = validate_guided_voice_copy("daily", copy, _facts())
    joined = " ".join(errors).lower()
    assert not valid
    assert "does not belong" in joined
    assert "unsupplied planet" in joined
    assert "prohibited certainty" in joined
    assert "invented numeric" in joined


def test_customer_forecast_pages_prefer_guided_luna_with_fallbacks():
    app = Path("app.py").read_text(encoding="utf-8")
    for product in ("daily", "monthly", "natal", "yearly"):
        assert re.search(rf'_guided_luna_copy\(\s*"{product}"', app)
    assert "_render_weekly_public_story" in app
    assert "if guided" in app
    assert "load_monthly_voice_candidate" in app
    assert 'elif LUNA_VOICE_MODE == "live"' in app
    assert "if guided_natal" in app
    assert 'if year_bundle["complete"]' in app


def test_personal_packets_do_not_send_raw_birth_identity():
    app = Path("app.py").read_text(encoding="utf-8")
    natal_start = app.index("natal_facts = {")
    natal_end = app.index("guided_natal =", natal_start)
    natal_packet = app[natal_start:natal_end]
    assert '"birth_date"' not in natal_packet
    assert '"birth_time"' not in natal_packet
    assert '"location_name"' not in natal_packet
    assert '"email"' not in natal_packet
