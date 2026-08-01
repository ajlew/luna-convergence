from datetime import date

from luna_editorial_system import (
    GATEKEEPER_LINE,
    VALIDATION_LINE,
)
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    narrative = build_monthly_narrative(
        result,
        main_focus="General overview",
    )

    assert narrative.hook_headline == (
        "Your spark wants a passport—and proof"
    )
    assert narrative.central_storyline == (
        "Something exciting expands your world. August tests "
        "whether it earns a place in your life."
    )
    assert narrative.agency_rule == GATEKEEPER_LINE
    assert narrative.validation_rule == VALIDATION_LINE
    assert len(narrative.luna_says) == 1
    assert "romance" in narrative.luna_says[0].lower()
    assert "follow" in narrative.luna_says[0].lower()
    assert narrative.do_line == (
        "Follow the effort. Chemistry can book its own flight."
    )
    assert narrative.dont_line == (
        "Mistake attention for value. A boarding pass is not commitment."
    )
    assert "not waiting to be selected" not in (
        " ".join(narrative.luna_says)
        + narrative.agency_rule
        + " ".join(narrative.love_story)
    ).lower()

    print("Monthly agency narrative tests passed.")


if __name__ == "__main__":
    main()
