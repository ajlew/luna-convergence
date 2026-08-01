from datetime import date
import re

from date_display import human_date, human_date_range
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report
from yearly_experience_v1 import build_yearly_experience_html


def monthly_result() -> dict:
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


def yearly_result() -> dict:
    return period_report(
        "Sagittarius",
        date(2027, 1, 1),
        date(2027, 12, 31),
        "Australia/Sydney",
        "2027",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General year ahead",
    )


def main() -> None:
    result = monthly_result()
    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(
        narrative,
        result,
        show_print=True,
        preview=False,
    )

    assert "Evidence path" in html
    assert "Starting condition" in html
    assert "Midmonth test" in html
    assert "Release and result" in html

    # The full narrative-role cards and equation repeated the story and are gone.
    assert "Monthly arc equation" not in html
    assert "Inherited state + trigger hierarchy" not in html
    assert "luna-arc-card" not in html
    assert "luna-arc-grid" not in html

    # Scenario families remain available only in the technical evidence section.
    assert html.count("Ranked scenario families") == 1
    assert html.index("Ranked scenario families") > html.index("Full technical evidence")

    # ISO dates must not leak into customer-facing monthly output.
    for raw in (
        "2026-06-30",
        "2026-07-01",
        "2026-07-14",
        "2026-07-24",
        "2026-07-30",
    ):
        assert raw not in html, raw

    for label in (
        "30 June 2026",
        "14 July 2026",
        "24 July 2026",
        "30 July 2026",
    ):
        assert label in html, label

    yearly_html = build_yearly_experience_html(
        yearly_result(),
        show_print=True,
    )
    assert re.search(r"\b20\d{2}-\d{2}-\d{2}\b", yearly_html) is None

    assert human_date("2026-07-01") == "1 July 2026"
    assert human_date_range("2026-07-23", "2026-07-30") == "23-30 July 2026"

    print("Monthly Arc Evidence Cleanup v2.7 tests passed.")


if __name__ == "__main__":
    main()
