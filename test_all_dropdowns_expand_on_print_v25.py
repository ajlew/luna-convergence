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


def check_monthly(html: str) -> None:
    # Monthly browser printing was retired in v2.9.7.3. Evidence remains
    # collapsed on the page and the searchable server-generated PDF is used.
    assert "Print or save report" not in html
    assert "luna-print-report" not in html
    assert "isolatedReportClone" not in html
    assert 'document.createElement("iframe")' not in html
    assert "<details>" in html
    assert "<details open" not in html


def check_yearly(html: str) -> None:
    assert 'querySelectorAll("details")' in html
    assert "detail.open = true" in html or "detail.open=true" in html
    assert 'detail.setAttribute("open", "")' in html or 'detail.setAttribute("open","")' in html
    assert 'window.addEventListener("beforeprint"' in html
    assert 'window.addEventListener("afterprint"' in html
    assert "cloneNode(true)" in html
    assert "<details>" in html
    assert "<details open" not in html


def main() -> None:
    monthly = monthly_result()
    monthly_html = build_monthly_experience_html(
        build_monthly_narrative(monthly),
        monthly,
        show_print=True,
        preview=False,
    )
    yearly_html = build_yearly_experience_html(
        yearly_result(),
        show_print=True,
    )

    check_monthly(monthly_html)
    check_yearly(yearly_html)

    print("All Monthly and Yearly print dropdowns expand automatically.")


if __name__ == "__main__":
    main()
