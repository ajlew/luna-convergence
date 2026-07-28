from datetime import date

from astrology_engine import SIGNS
from customer_experience import free_daily_reading


def main() -> None:
    for sign in SIGNS:
        reading = free_daily_reading(
            sign,
            date(2026, 7, 29),
            "Australia/Sydney",
        )
        assert reading.headline
        assert len(reading.forecast_paragraphs) == 2
        assert len(reading.reflection_questions) == 4
        assert reading.love_note
        assert reading.anchor_aspect is not None

    print("Daily-reading compatibility tests passed.")


if __name__ == "__main__":
    main()
