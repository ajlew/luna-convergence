from datetime import date, timedelta

from astrology_engine import SIGNS
from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import build_daily_narrative, reading_comparison_text


MUTABLE_SIGNS = ("Gemini", "Virgo", "Sagittarius", "Pisces")


def narrative_for(sign: str, d: date):
    reading = free_daily_reading(sign, d, "Australia/Sydney")
    previous = [
        reading_comparison_text(
            free_daily_reading(
                sign,
                d - timedelta(days=offset),
                "Australia/Sydney",
            )
        )
        for offset in range(1, 5)
    ]
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=d,
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )


def main() -> None:
    for target in (
        date(2026, 7, 27),
        date(2026, 7, 28),
        date(2026, 7, 29),
        date(2026, 7, 30),
    ):
        daily = {sign: narrative_for(sign, target) for sign in SIGNS}
        headlines = [item.headline for item in daily.values()]
        assert len(headlines) == 12
        assert len(set(headlines)) == 12

    target = date(2026, 7, 29)
    narratives = {sign: narrative_for(sign, target) for sign in SIGNS}
    headlines = [item.headline for item in narratives.values()]
    assert "Chemistry wants a reaction" not in headlines

    mutable_headlines = [narratives[sign].headline for sign in MUTABLE_SIGNS]
    assert len(set(mutable_headlines)) == 4

    assert narratives["Gemini"].headline == "A private feeling needs an honest response"
    assert narratives["Virgo"].headline == "What you want is changing who you are ready to be"
    assert narratives["Sagittarius"].headline == "What you want is changing how you are seen"
    assert narratives["Pisces"].headline == "The relationship needs a clearer answer"

    # The evidence remains shared where the sky is shared.
    assert {
        narratives[sign].evidence.aspect_label for sign in MUTABLE_SIGNS
    } == {"Venus square Mars"}

    # The public headline changes because the activated houses differ.
    assert len({
        narratives[sign].convergence_axis for sign in MUTABLE_SIGNS
    }) == 4

    print("Twelve-sign headline uniqueness tests passed.")
    for sign in SIGNS:
        item = narratives[sign]
        print(f"{sign}: {item.headline} | {item.convergence_axis}")


if __name__ == "__main__":
    main()
