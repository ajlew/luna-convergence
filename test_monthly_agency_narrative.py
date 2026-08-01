from datetime import date

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
        "Something exciting expands your world, but August tests "
        "whether it earns a place in your life."
    )
    assert narrative.agency_rule == (
        "You are not waiting to be selected. "
        "You are deciding what deserves access."
    )
    assert narrative.validation_rule == (
        "Attention gets your notice. Effort earns your interest. "
        "Consistency earns a place in your life."
    )
    assert "relationship" in narrative.luna_says[0].lower()
    assert "flirtation" in narrative.luna_says[0].lower()
    assert "desired" in narrative.luna_says[0].lower()
    assert "who follows through" in narrative.luna_says[1].lower()
    assert "when romance is quiet" not in narrative.romance_quiet.lower()
    assert len(narrative.scenario_examples) >= 5
    assert "Confuse being noticed with being valued" in narrative.dont_line
    assert "shows real effort" in narrative.do_line

    print("Monthly agency narrative tests passed.")


if __name__ == "__main__":
    main()
