from datetime import date, timedelta

from astrology_engine import SIGNS
from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    _questions_overlap,
    build_daily_narrative,
    reading_comparison_text,
)


TARGET = date(2026, 7, 30)
TIMEZONE = "Australia/Sydney"
FORBIDDEN = "reserve, consistency and emotional restraint"


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
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=TARGET,
        timezone_name=TIMEZONE,
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )


def main() -> None:
    narratives = {
        sign: narrative_for(sign)
        for sign in SIGNS
    }

    final_questions = []
    for sign, narrative in narratives.items():
        assert narrative.evidence.aspect_label == "Moon sextile Saturn"
        assert len(narrative.reflection_questions) == 4, sign
        assert len(set(narrative.reflection_questions)) == 4, sign

        combined = " ".join(narrative.reflection_questions).lower()
        assert FORBIDDEN not in combined, sign

        for index, first in enumerate(narrative.reflection_questions):
            for second in narrative.reflection_questions[index + 1:]:
                assert not _questions_overlap(first, second), (
                    sign,
                    first,
                    second,
                )

        final_questions.append(narrative.reflection_questions[-1])

    assert len(set(final_questions)) == 12

    expected_fragments = {
        "Aries": "build this with me",
        "Taurus": "status or approval",
        "Gemini": "sustained over time",
        "Cancer": "boundaries consistently",
        "Leo": "patient, mutual effort",
        "Virgo": "steady boundary",
        "Libra": "interest is mutual",
        "Scorpio": "steady behaviour",
        "Sagittarius": "patience and consistent effort",
        "Capricorn": "secure and reciprocal",
        "Aquarius": "another person's pace",
        "Pisces": "distance allowing the fantasy",
    }
    for sign, fragment in expected_fragments.items():
        assert fragment in narratives[sign].reflection_questions[-1]

    print("Moon–Saturn twelve-sign question refinement tests passed.")
    for sign in SIGNS:
        print(
            f"{sign}: "
            f"{narratives[sign].reflection_questions[-1]}"
        )


if __name__ == "__main__":
    main()
