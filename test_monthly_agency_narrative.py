from datetime import date

from luna_editorial_system import GATEKEEPER_LINE, VALIDATION_LINE
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
    narrative = build_monthly_narrative(result)

    assert narrative.agency_rule == GATEKEEPER_LINE
    assert narrative.validation_rule == VALIDATION_LINE
    assert result.get("monthly_arc")
    assert len(narrative.chapters) == 4
    assert [chapter.label for chapter in narrative.chapters] == [
        "Act I", "Act II", "Act III", "Act IV"
    ]
    assert narrative.chapters[2].title == "Relationship test"
    assert all(chapter.paragraphs for chapter in narrative.chapters)
    assert narrative.do_line
    assert narrative.dont_line
    assert "not waiting to be selected" not in (
        " ".join(narrative.luna_says)
        + narrative.agency_rule
        + " ".join(narrative.love_story)
    ).lower()

    print("Monthly four-act agency narrative tests passed.")


if __name__ == "__main__":
    main()
