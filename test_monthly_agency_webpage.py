from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
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
    html = build_monthly_experience_html(
        narrative,
        result,
        show_print=True,
        preview=False,
        order_reference="LC-TEST",
    )

    for required in (
        "Luna says",
        "Your spark wants a passport—and proof",
        "Shift from applicant to gatekeeper.",
        "Romance and validation",
        "Why Luna sees this",
        "Solar Convergence",
        "Key dates and planetary timing",
        "Full technical evidence",
        "Print or save report",
        "Include evidence",
        "A4",
        "A3",
        "Portrait",
        "Landscape",
        "window.print()",
        "@media print",
    ):
        assert required in html, required

    for removed in (
        "Concrete possibilities",
        "You remain the main character",
        "The month in three acts",
        "Your move</span>",
        "You are not waiting to be selected",
    ):
        assert removed not in html, removed

    assert html.count("Your move") == 1
    assert 'data-print-orientation="portrait"' in html
    assert "FOOTER" not in html

    print("Monthly agency webpage tests passed.")


if __name__ == "__main__":
    main()
