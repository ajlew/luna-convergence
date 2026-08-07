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
    html = build_monthly_experience_html(
        build_monthly_narrative(result),
        result,
        show_print=True,
        preview=True,
    )

    assert 'class="luna-report-details"' in html
    assert "Star sign" in html and "Sagittarius" in html
    assert "Report month" in html and "August 2026" in html
    assert "Generated" in html
    assert "Timezone" in html and "Australia/Sydney" in html
    assert "@media print" in html
    assert ".luna-report-details" in html
    assert "cloneNode(true)" in html  # the metadata is inside the cloned report

    print("Monthly print metadata v3.1 tests passed.")


if __name__ == "__main__":
    main()
