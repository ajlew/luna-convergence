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
        order_reference="LC-TEST-AGENCY",
    )

    for required in (
        "Luna says",
        "Your spark wants a passport—and proof",
        "You are not waiting to be selected",
        "Romance, flirting and validation",
        "When romance is active",
        "When romance is quiet",
        "Why Luna sees this",
        "Solar Convergence",
        "Key dates and planetary timing",
        "Full technical evidence",
        "Print or save report",
        "Include evidence in print",
        "window.print()",
        "@media print",
    ):
        assert required in html, required

    assert 'class="luna-monthly-report"' in html
    assert "Bodoni Moda" in html
    assert "Josefin Sans" in html
    assert "IBM Plex Mono" in html

    print("Monthly agency webpage tests passed.")


if __name__ == "__main__":
    main()
