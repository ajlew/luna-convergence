from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report
from yearly_experience_v1 import build_yearly_experience_html


def monthly_result() -> dict:
    return period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
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
    monthly = monthly_result()
    monthly_html = build_monthly_experience_html(
        build_monthly_narrative(monthly),
        monthly,
        show_print=True,
        preview=False,
    )

    yearly = yearly_result()
    yearly_html = build_yearly_experience_html(
        yearly,
        show_print=True,
    )

    assert "Print or save report" not in monthly_html
    assert "isolatedReportClone" not in monthly_html
    assert 'document.createElement("iframe")' not in monthly_html
    assert "luna-print-report" not in monthly_html
    assert "<details>" in monthly_html

    assert "luna-year-print-portal" in yearly_html
    assert "luna-year-print-active" in yearly_html
    assert "cloneNode(true)" in yearly_html
    assert "document.body.appendChild(printPortal)" in yearly_html
    assert 'querySelectorAll("details")' in yearly_html
    assert 'window.addEventListener("beforeprint"' in yearly_html
    assert 'window.addEventListener("afterprint"' in yearly_html


    print("Full Report Print Portal v2.5 tests passed.")


if __name__ == "__main__":
    main()
