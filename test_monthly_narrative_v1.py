from datetime import date

from monthly_narrative_v1 import (
    build_monthly_narrative,
    monthly_narrative_markdown,
    normalise_personal_question,
)
from synthesis import period_report


ORDER_REFERENCE = (
    "LC-MONTHLY-SAGITTARIUS-2026-08-AUSTRALIA-SYDNEY-"
    "F-LOVE-Q-NONE-AD0B4520"
)


def build_result():
    return period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=9,
    )


def main() -> None:
    assert normalise_personal_question("No optional question supplied") == ""
    assert normalise_personal_question("None supplied") == ""
    assert normalise_personal_question("What should I do?") == "What should I do?"

    narrative = build_monthly_narrative(
        build_result(),
        main_focus="Love and relationships",
        personal_question="No optional question supplied",
        order_reference=ORDER_REFERENCE,
    )
    markdown = monthly_narrative_markdown(narrative)

    assert narrative.headline == "Love wants a wider horizon - but the future needs proof"
    assert narrative.personal_question == ""
    assert len(narrative.at_glance) == 3
    assert narrative.hook_headline == "Your spark wants a passport—and proof"
    assert narrative.convergence_axis == "Romance & creativity x Travel & learning"
    assert narrative.do_line
    assert narrative.dont_line
    assert len(narrative.chapters) == 3
    assert len(narrative.key_dates) >= 5
    assert "Your month at a glance" in markdown
    assert "Monthly convergence" in markdown
    assert narrative.hook_headline in markdown
    assert "Love, attraction and mutual effort" in markdown
    assert "The month in three chapters" in markdown
    assert "Love and relationships" in markdown
    assert "Work and direction" in markdown
    assert "Money and security" in markdown
    assert "Monthly Sky Snapshot" in markdown
    assert "Technical appendix" in markdown
    assert "No optional question supplied" not in markdown
    assert "YOUR QUESTION" not in markdown
    assert ORDER_REFERENCE in markdown
    assert markdown.index("Your month at a glance") < markdown.index("Technical appendix")

    print("Monthly Narrative Engine v1 tests passed.")


if __name__ == "__main__":
    main()
