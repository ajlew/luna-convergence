from datetime import date

from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Sagittarius",
        date(2026, 7, 1),
        date(2026, 7, 31),
        "Australia/Sydney",
        "July 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    arc = result.get("monthly_arc") or {}
    assert arc
    assert arc["headline"] == (
        "July checks the bank balance before it upgrades the itinerary"
    )
    assert arc["central_storyline"] == (
        "The month starts with the price. It ends with the possibility."
    )
    assert arc["theme_axis"] == (
        "Money & obligations x Travel, publishing & opportunity"
    )
    assert arc["primary_house"] == 8
    assert arc["secondary_house"] == 9

    beats = {item["role"]: item for item in arc["beats"]}
    assert beats["inherited state"]["title"] == "Full Moon in Capricorn"
    assert beats["complication"]["title"] == "New Moon in Cancer"
    assert beats["pivot"]["title"] == "Mercury stations direct"
    assert beats["climax"]["title"] == "Sun conjunction Jupiter"
    assert beats["resolution"]["title"] == "Full Moon in Aquarius"

    scenario_keys = [item["key"] for item in arc["ranked_scenarios"]]
    for required in (
        "financial_shock",
        "paperwork_verification",
        "funding_application",
        "publishing_media",
        "travel",
    ):
        assert required in scenario_keys, required

    narrative = build_monthly_narrative(result)
    assert narrative.hook_headline == arc["headline"]
    assert narrative.central_storyline == arc["central_storyline"]
    assert len(narrative.luna_says) == 2
    assert narrative.luna_says[0].startswith("Start with the possibility")
    assert "life you are creating" in narrative.luna_says[1]
    assert "Mercury was only reorganising the filing cabinet" in narrative.dont_line
    assert [chapter.hook for chapter in narrative.chapters] == [
        "You turn possibility into momentum",
        "You bring the details into focus",
        "You see whether the spark can hold",
        "You choose what belongs in your life",
    ]
    assert narrative.chapters[2].title == "Watch what happens next"
    assert [item.evidence for item in narrative.key_dates] == [
        "New Moon in Cancer",
        "Mercury stations direct",
        "Sun conjunction Jupiter",
        "Full Moon in Aquarius",
    ]

    print("Monthly Arc Engine v2.6 tests passed.")


if __name__ == "__main__":
    main()
