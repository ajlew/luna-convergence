from datetime import date, timedelta

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    build_daily_narrative,
    clean_customer_text,
    reading_comparison_text,
)


def narrative_for(day: int):
    d = date(2026, 7, day)
    reading = free_daily_reading("Sagittarius", d, "Australia/Sydney")
    previous = [
        reading_comparison_text(
            free_daily_reading(
                "Sagittarius",
                d - timedelta(days=offset),
                "Australia/Sydney",
            )
        )
        for offset in range(1, 5)
    ]
    return build_daily_narrative(
        reading,
        sign="Sagittarius",
        reading_date=d,
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )


def main() -> None:
    readings = [narrative_for(day) for day in (27, 28, 29, 30)]

    assert len({item.headline for item in readings}) == 4
    for item in readings:
        assert 3 <= len(item.today_story) <= 4
        assert item.convergence_axis
        assert "×" in item.convergence_axis or item.sun_house == item.moon_house
        assert len(item.why_today_points) == 3
        assert item.long_term_current
        assert item.emotional_weather
        assert item.hidden_opportunity
        assert item.watch_out
        assert item.action_today
        assert item.relationship_story
        assert item.evidence.confidence_label in {"High", "Medium", "Low"}
        assert 1 <= item.evidence.strength_score <= 100
        assert item.evidence.active_window
        assert "**" not in " ".join(item.today_story)

    july_29 = readings[2]
    assert july_29.evidence.aspect_label == "Venus square Mars"
    assert "Romance" in july_29.convergence_axis or "Relationships" in july_29.convergence_axis
    assert clean_customer_text("**relationship**") == "relationship"

    print("Explainable Daily Narrative v3 tests passed.")
    for item in readings:
        print(
            item.reading_date,
            item.headline,
            "|",
            item.convergence_axis,
            "|",
            item.evidence.confidence_label,
            item.evidence.strength_score,
        )
        for paragraph in item.today_story:
            print(" -", paragraph)


if __name__ == "__main__":
    main()
