from datetime import date, timedelta

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    _aspect_match,
    build_daily_narrative,
    reading_comparison_text,
)


FIXED_SIGNS = ("Taurus", "Leo", "Scorpio", "Aquarius")
TARGET = date(2026, 7, 29)
TIMEZONE = "Australia/Sydney"


def narrative_for(sign: str):
    reading = free_daily_reading(sign, TARGET, TIMEZONE)
    previous = [
        reading_comparison_text(
            free_daily_reading(
                sign,
                TARGET - timedelta(days=offset),
                TIMEZONE,
            )
        )
        for offset in range(1, 5)
    ]
    narrative = build_daily_narrative(
        reading,
        sign=sign,
        reading_date=TARGET,
        timezone_name=TIMEZONE,
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )
    return reading, narrative


def main() -> None:
    generated = {
        sign: narrative_for(sign)
        for sign in FIXED_SIGNS
    }

    taurus = generated["Taurus"][1]
    leo = generated["Leo"][1]
    scorpio = generated["Scorpio"][1]
    aquarius = generated["Aquarius"][1]

    assert taurus.headline == "The spark is asking for a real choice"
    assert " ".join(taurus.today_story).lower().count("spark") <= 1
    assert any(
        "connection becoming mutual" in question
        for question in taurus.reflection_questions
    )

    assert "prove its value through reciprocity" not in leo.relationship_story
    assert "tested through consistent effort" in leo.relationship_story

    assert len(set(scorpio.reflection_questions)) == 4
    assert any(
        "share responsibility as well as excitement" in question
        for question in scorpio.reflection_questions
    )

    assert "Keep magnetism" not in aquarius.relationship_story
    assert "The pull of magnetism" in aquarius.relationship_story
    assert "should not require surrendering autonomy" in (
        aquarius.relationship_story
    )

    for reading, narrative in generated.values():
        assert narrative.evidence.aspect_label == "Venus square Mars"
        assert narrative.evidence.configured_orb == 6.0
        assert narrative.evidence.active_window == "July 14–August 15"
        anchor = reading.anchor_aspect
        assert anchor is not None
        assert _aspect_match(
            date(2026, 7, 14),
            TIMEZONE,
            anchor.planet1,
            anchor.planet2,
            anchor.name,
        )
        assert not _aspect_match(
            date(2026, 7, 13),
            TIMEZONE,
            anchor.planet1,
            anchor.planet2,
            anchor.name,
        )
        assert _aspect_match(
            date(2026, 8, 15),
            TIMEZONE,
            anchor.planet1,
            anchor.planet2,
            anchor.name,
        )
        assert not _aspect_match(
            date(2026, 8, 16),
            TIMEZONE,
            anchor.planet1,
            anchor.planet2,
            anchor.name,
        )

    print("Fixed-sign editorial and orb-window tests passed.")


if __name__ == "__main__":
    main()
