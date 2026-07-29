from datetime import date, timedelta

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    build_daily_narrative,
    reading_comparison_text,
)


CARDINAL_SIGNS = ("Aries", "Cancer", "Libra", "Capricorn")


def narrative_for(sign: str):
    target = date(2026, 7, 29)
    reading = free_daily_reading(
        sign,
        target,
        "Australia/Sydney",
    )
    previous = [
        reading_comparison_text(
            free_daily_reading(
                sign,
                target - timedelta(days=offset),
                "Australia/Sydney",
            )
        )
        for offset in range(1, 5)
    ]
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=target,
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )


def main() -> None:
    narratives = {
        sign: narrative_for(sign)
        for sign in CARDINAL_SIGNS
    }

    aspect_questions = [
        item.reflection_questions[-1]
        for item in narratives.values()
    ]
    relationship_copy = [
        item.relationship_story
        for item in narratives.values()
    ]
    first_paragraphs = [
        item.today_story[0]
        for item in narratives.values()
    ]

    assert len(set(aspect_questions)) == 4
    assert len(set(relationship_copy)) == 4
    assert len(set(first_paragraphs)) == 4
    assert all(
        "chemistry and direct desire" not in text.lower()
        for text in relationship_copy
    )

    libra = narratives["Libra"]
    assert not (
        libra.evidence.convergence_label.startswith("Current")
        and libra.evidence.convergence_window == "July 16–July 27"
    )
    assert libra.evidence.convergence_label.startswith(
        ("Current", "Approaching", "Recent", "No wider")
    )

    print("Cardinal refinement tests passed.")
    for sign, item in narratives.items():
        print()
        print(sign)
        print(item.today_story[0])
        print(item.relationship_story)
        print(item.reflection_questions[-1])
        print(
            item.evidence.convergence_label,
            item.evidence.convergence_window,
        )


if __name__ == "__main__":
    main()
