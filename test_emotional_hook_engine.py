from datetime import date, timedelta
import re

from astrology_engine import SIGNS
from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    HOOK_TONE_FAMILIES,
    PAIR_HOOK_OVERRIDES,
    build_daily_narrative,
    reading_comparison_text,
)


TARGET = date(2026, 8, 1)
TIMEZONE = "Australia/Sydney"
TECHNICAL = {
    "aspect", "orb", "sextile", "trine", "square",
    "opposition", "conjunction", "retrograde", "house",
}
UNSUPPORTED = (
    "they love you",
    "they secretly love",
    "will definitely",
    "guaranteed",
)


def narrative_for(sign: str, target: date):
    reading = free_daily_reading(sign, target, TIMEZONE)
    previous = [
        reading_comparison_text(
            free_daily_reading(
                sign,
                target - timedelta(days=offset),
                TIMEZONE,
            )
        )
        for offset in range(1, 5)
    ]
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=target,
        timezone_name=TIMEZONE,
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )


def main() -> None:
    narratives = {
        sign: narrative_for(sign, TARGET)
        for sign in SIGNS
    }

    hooks = [item.hook_headline for item in narratives.values()]
    assert len(set(hooks)) == 12

    for sign, item in narratives.items():
        words = re.findall(
            r"[A-Za-z]+(?:'[A-Za-z]+)?",
            item.hook_headline,
        )
        assert 4 <= len(words) <= 14, (sign, item.hook_headline)
        assert item.hook_headline != item.headline, sign
        assert item.hook_subline == item.headline, sign
        assert item.tone_family in HOOK_TONE_FAMILIES, sign

        lowered = item.hook_headline.lower()
        assert not any(phrase in lowered for phrase in UNSUPPORTED), sign
        assert not (set(word.lower() for word in words) & TECHNICAL), sign

        repeated = narrative_for(sign, TARGET)
        assert repeated.hook_headline == item.hook_headline, sign
        assert repeated.tone_family == item.tone_family, sign

    # The priority pair banks requested for the commercial tone exist.
    for pair in (
        frozenset({4, 7}),
        frozenset({3, 5}),
        frozenset({7, 10}),
        frozenset({2, 4}),
        frozenset({8, 11}),
        frozenset({2, 12}),
    ):
        assert pair in PAIR_HOOK_OVERRIDES
        assert set(PAIR_HOOK_OVERRIDES[pair]) == set(
            HOOK_TONE_FAMILIES
        )

    # One sign should move through several editorial families across a week.
    weekly = [
        narrative_for("Sagittarius", TARGET + timedelta(days=offset))
        for offset in range(7)
    ]
    assert len({item.tone_family for item in weekly}) >= 3
    assert len({item.hook_headline for item in weekly}) >= 4

    print("Emotional Hook Engine tests passed.")
    for sign in SIGNS:
        item = narratives[sign]
        print(
            f"{sign}: [{item.tone_family}] "
            f"{item.hook_headline} / {item.headline}"
        )


if __name__ == "__main__":
    main()
