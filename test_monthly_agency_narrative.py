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
        "August opens a larger door. The rest of the month decides "
        "what can walk through it."
    )
    assert narrative.agency_rule == GATEKEEPER_LINE
    assert narrative.validation_rule == VALIDATION_LINE
    assert len(narrative.luna_says) == 4
    assert sum(len(item.split()) for item in narrative.luna_says) >= 170
    assert "flirtation" in narrative.luna_says[0].lower()
    assert "around august" in narrative.luna_says[1].lower()
    assert "shared cost" in narrative.luna_says[2].lower()
    assert "emotional security" in narrative.luna_says[3].lower()
    assert all(len(chapter.paragraphs) == 2 for chapter in narrative.chapters)
    assert sum(
        len(paragraph.split())
        for chapter in narrative.chapters
        for paragraph in chapter.paragraphs
    ) >= 180
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

    print("Monthly story narrative tests passed.")


if __name__ == "__main__":
    main()
