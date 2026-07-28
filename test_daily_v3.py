from datetime import date

from astrology_engine import SIGNS
from customer_experience import free_daily_reading


def word_count(reading) -> int:
    return sum(
        len(paragraph.replace("—", " ").split())
        for paragraph in reading.forecast_paragraphs
    )


def main() -> None:
    july_28 = free_daily_reading(
        "Sagittarius",
        date(2026, 7, 28),
        "Australia/Sydney",
    )
    july_29 = free_daily_reading(
        "Sagittarius",
        date(2026, 7, 29),
        "Australia/Sydney",
    )
    july_30 = free_daily_reading(
        "Sagittarius",
        date(2026, 7, 30),
        "Australia/Sydney",
    )

    assert july_28.headline == "Read between the lines"
    assert july_29.headline == "Chemistry wants a reaction"
    assert july_30.headline == "Let consistency seduce you"

    assert july_28.anchor_aspect is not None
    assert july_29.anchor_aspect is not None
    assert july_30.anchor_aspect is not None

    assert july_28.anchor_aspect.label == "Moon opposition Mercury"
    assert july_29.anchor_aspect.label == "Venus square Mars"
    assert july_30.anchor_aspect.label == "Moon sextile Saturn"

    assert len({july_28.headline, july_29.headline, july_30.headline}) == 3
    assert july_28.forecast_paragraphs != july_29.forecast_paragraphs
    assert july_29.forecast_paragraphs != july_30.forecast_paragraphs
    assert "love and relationships" in july_28.forecast_paragraphs[1].lower()
    assert "chemistry" in july_29.love_note.lower()
    assert "older" in july_30.love_note.lower()
    assert "**" not in july_28.forecast_paragraphs[0]
    assert "**" not in july_28.forecast_paragraphs[1]

    for sign in SIGNS:
        reading = free_daily_reading(
            sign,
            date(2026, 7, 29),
            "Australia/Sydney",
        )
        assert reading.headline
        assert len(reading.forecast_paragraphs) == 2
        assert len(reading.reflection_questions) == 4
        assert reading.best_move.endswith(".")
        assert reading.love_note
        assert reading.work_note
        assert reading.money_note
        assert 100 <= word_count(reading) <= 280

    print("Daily Reading Version 3 tests passed.")
    for reading in (july_28, july_29, july_30):
        print()
        print(reading.reading_date, "—", reading.headline)
        print("Trigger:", reading.anchor_aspect.label)
        print(reading.forecast_paragraphs[0])
        print(reading.forecast_paragraphs[1])
        print("Love:", reading.love_note)


if __name__ == "__main__":
    main()
