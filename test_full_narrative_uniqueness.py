from datetime import date, timedelta
from pathlib import Path

from astrology_engine import SIGNS
from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    build_daily_narrative,
    reading_comparison_text,
)


MUTABLE_SIGNS = ("Gemini", "Virgo", "Sagittarius", "Pisces")


def narrative_for(sign: str, target: date):
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
    target = date(2026, 7, 29)
    narratives = {
        sign: narrative_for(sign, target)
        for sign in SIGNS
    }

    public_fields = {
        "headline": [item.headline for item in narratives.values()],
        "story": [" ".join(item.today_story) for item in narratives.values()],
        "relationship": [
            item.relationship_story for item in narratives.values()
        ],
        "opportunity": [
            item.hidden_opportunity for item in narratives.values()
        ],
        "watch": [item.watch_out for item in narratives.values()],
        "action": [item.action_today for item in narratives.values()],
        "questions": [
            " | ".join(item.reflection_questions)
            for item in narratives.values()
        ],
    }

    for field_name, values in public_fields.items():
        assert len(values) == 12, field_name
        assert len(set(values)) == 12, field_name

    for sign, item in narratives.items():
        assert len(item.today_story) == 3, sign
        assert len(item.reflection_questions) == 4, sign
        assert len(set(item.reflection_questions)) == 4, sign
        assert item.action_today not in item.today_story, sign

    # Shared astronomical evidence should remain shared.
    assert {
        narratives[sign].evidence.aspect_label
        for sign in MUTABLE_SIGNS
    } == {"Venus square Mars"}
    assert {
        narratives[sign].evidence.strength_score
        for sign in MUTABLE_SIGNS
    } == {92}

    # Customer-facing relationship copy, action and questions must not.
    assert len({
        narratives[sign].relationship_story
        for sign in MUTABLE_SIGNS
    }) == 4
    assert len({
        narratives[sign].action_today
        for sign in MUTABLE_SIGNS
    }) == 4
    assert len({
        tuple(narratives[sign].reflection_questions)
        for sign in MUTABLE_SIGNS
    }) == 4

    app = (Path(__file__).parent / "app.py").read_text(
        encoding="utf-8"
    )
    assert 'context=f"daily-{sign.lower()}"' in app
    assert 'prefill_sign=sign' in app

    print("Full narrative uniqueness and purchase-sign sync tests passed.")
    for sign in MUTABLE_SIGNS:
        item = narratives[sign]
        print()
        print(sign)
        print(item.headline)
        print(item.relationship_story)
        print(item.action_today)
        for question in item.reflection_questions:
            print("-", question)


if __name__ == "__main__":
    main()
