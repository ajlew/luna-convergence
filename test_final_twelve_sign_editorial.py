from datetime import date, timedelta

from astrology_engine import SIGNS
from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    build_daily_narrative,
    reading_comparison_text,
)


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
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=TARGET,
        timezone_name=TIMEZONE,
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )


def main() -> None:
    items = {sign: narrative_for(sign) for sign in SIGNS}

    assert len({item.headline for item in items.values()}) == 12
    assert len({" ".join(item.today_story) for item in items.values()}) == 12
    assert len({item.why_today_points[2] for item in items.values()}) == 12

    forbidden_labels = (
        "work & wellbeing",
        "friends & future",
        "travel & learning",
        "trust & shared money",
        "rest & inner life",
    )

    for sign, item in items.items():
        assert len(item.today_story) == 3, sign
        assert len(item.reflection_questions) == 4, sign
        assert len(set(item.reflection_questions)) == 4, sign
        assert item.why_today_points[2].startswith(f"For {sign},"), sign
        story = " ".join(item.today_story).lower()
        for label in forbidden_labels:
            assert label not in story, (sign, label)

    assert "emotional safety matters" not in " ".join(
        items["Gemini"].today_story
    ).lower()
    assert "banter" not in " ".join(
        items["Cancer"].today_story
    ).lower()
    assert "equally valued" not in " ".join(
        items["Leo"].today_story
    ).lower()
    assert "meet your bold attraction" not in " ".join(
        items["Virgo"].today_story
    ).lower()
    assert "same future" not in " ".join(
        items["Scorpio"].today_story
    ).lower()
    assert "sequence the response carefully" not in " ".join(
        items["Pisces"].today_story
    ).lower()

    aries = " ".join(items["Aries"].reflection_questions).lower()
    assert aries.count("daily life") <= 1
    assert aries.count("everyday life") <= 1

    print("Final twelve-sign editorial quality tests passed.")
    for sign, item in items.items():
        print(f"{sign}: {item.headline}")


if __name__ == "__main__":
    main()
