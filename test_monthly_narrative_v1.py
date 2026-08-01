from datetime import date

from monthly_narrative_v1 import (
    build_monthly_narrative,
    monthly_narrative_markdown,
    normalise_personal_question,
)
from synthesis import period_report


ORDER_REFERENCE = (
    "LC-MONTHLY-SAGITTARIUS-2026-07-AUSTRALIA-SYDNEY-"
    "F-GENERAL-Q-NONE-ARC26"
)


def build_result():
    return period_report(
        "Sagittarius",
        date(2026, 7, 1),
        date(2026, 7, 31),
        "Australia/Sydney",
        "July 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General overview",
    )


def main() -> None:
    assert normalise_personal_question("No optional question supplied") == ""
    assert normalise_personal_question("None supplied") == ""
    assert normalise_personal_question("What should I do?") == "What should I do?"

    narrative = build_monthly_narrative(
        build_result(),
        main_focus="General overview",
        personal_question="No optional question supplied",
        order_reference=ORDER_REFERENCE,
    )
    markdown = monthly_narrative_markdown(narrative)

    assert narrative.headline == (
        "Money & obligations x Travel, publishing & opportunity"
    )
    assert narrative.personal_question == ""
    assert len(narrative.at_glance) == 3
    assert narrative.hook_headline == (
        "July checks the bank balance before it upgrades the itinerary"
    )
    assert narrative.central_storyline == (
        "The month starts with the price. It ends with the possibility."
    )
    assert len(narrative.chapters) == 3
    assert len(narrative.key_dates) == 4
    assert "Monthly arc equation" in narrative.technical_appendix_markdown
    assert "Ranked scenario families" in narrative.technical_appendix_markdown
    assert "Carryover evidence" in narrative.technical_appendix_markdown
    assert "Your month at a glance" in markdown
    assert "Monthly convergence" in markdown
    assert narrative.hook_headline in markdown
    assert "The month in three chapters" in markdown
    assert "Monthly Sky Snapshot" in markdown
    assert "Technical appendix" in markdown
    assert "No optional question supplied" not in markdown
    assert ORDER_REFERENCE in markdown

    print("Monthly Narrative Engine with Arc v2.6 tests passed.")


if __name__ == "__main__":
    main()
