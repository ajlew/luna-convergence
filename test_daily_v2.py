from datetime import date

from astrology_engine import SIGNS
from customer_experience import free_daily_reading


def word_count(reading) -> int:
    return sum(
        len(paragraph.replace("—", " ").split())
        for paragraph in reading.forecast_paragraphs
    )


def main() -> None:
    sagittarius = free_daily_reading(
        "Sagittarius",
        date(2026, 7, 27),
        "Australia/Sydney",
    )

    assert sagittarius.headline == "Listen before you expand"
    assert sagittarius.sun_house == 9
    assert sagittarius.moon_house == 2
    assert sagittarius.anchor_aspect is not None
    assert sagittarius.anchor_aspect.label == "Sun opposition Pluto"
    assert sagittarius.anchor_aspect.houses == frozenset({3, 9})
    assert "conversation" in sagittarius.forecast_paragraphs[0].lower()
    assert "money" in sagittarius.forecast_paragraphs[1].lower()
    assert len(sagittarius.reflection_questions) == 4
    assert len(set(sagittarius.reflection_questions)) == 4
    assert 105 <= word_count(sagittarius) <= 230
    assert "**" not in sagittarius.headline
    assert "**" not in sagittarius.forecast_paragraphs[0]
    assert "**" not in sagittarius.forecast_paragraphs[1]

    for sign in SIGNS:
        reading = free_daily_reading(
            sign,
            date(2026, 7, 27),
            "Australia/Sydney",
        )
        assert reading.headline
        assert len(reading.forecast_paragraphs) == 2
        assert len(reading.reflection_questions) == 4
        assert reading.best_move.endswith(".")
        assert reading.love_note
        assert reading.work_note
        assert reading.money_note
        assert 90 <= word_count(reading) <= 250

    print("Daily Reading Version 2 tests passed.")
    print(sagittarius.headline)
    print()
    print(*sagittarius.forecast_paragraphs, sep="\n\n")
    print()
    for question in sagittarius.reflection_questions:
        print("-", question)


if __name__ == "__main__":
    main()
