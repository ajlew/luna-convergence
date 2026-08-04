from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
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
    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(
        narrative,
        result,
        show_print=True,
        preview=False,
        order_reference="LC-TEST",
    )

    for required in (
        "Luna says",
        "July checks the bank balance before it upgrades the itinerary",
        "The month starts with the price. It ends with the possibility.",
        "How July unfolds — four acts",
        "Moments to notice",
        "Write the next move when the story changes",
        "Whether the spark arrives—or the room stays quiet",
        "From reading the future to writing it.",
        "Why Luna sees this",
        "Evidence path",
        "Ranked scenario families",
        "Carryover evidence",
        "Solar Convergence",
        "Key dates and planetary timing",
        "Full technical evidence",
        "Evidence-to-scenario trace",
        "@page",
    ):
        assert required in html, required

    for removed in (
        "Dates worth circling",
        "Concrete possibilities",
        "You remain the main character",
        "The month in three acts",
        "You are not waiting to be selected",
        '<section class="luna-monthly-section luna-relationship-test">',
    ):
        assert removed not in html, removed

    assert html.count("Your move") == 1
    assert html.count('class="luna-story-act"') == 4
    assert html.count('class="luna-story-date-card"') == 4
    assert "Include evidence" not in html
    assert "Monthly arc equation" not in html
    assert "luna-arc-card" not in html
    assert "Print or save report" not in html
    assert "luna-print-report" not in html
    assert "isolatedReportClone" not in html
    assert 'document.createElement("iframe")' not in html
    assert "position:sticky" not in html

    print("Monthly four-act webpage tests passed.")


if __name__ == "__main__":
    main()
