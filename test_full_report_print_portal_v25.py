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

    for html, portal_id, body_class in (
        (
            monthly_html,
            "luna-print-portal",
            "luna-print-active",
        ),
        (
            yearly_html,
            "luna-year-print-portal",
            "luna-year-print-active",
        ),
    ):
        assert portal_id in html
        assert body_class in html
        assert "cloneNode(true)" in html
        assert "document.body.appendChild(printPortal)" in html
        assert 'querySelectorAll("details")' in html
        assert 'detail.setAttribute("open","")' in html or (
            'detail.setAttribute("open", "")' in html
        )
        assert 'querySelectorAll(".luna-print-controls")' in html
        assert "node.remove()" in html
        assert "window.addEventListener(\"beforeprint\"" in html
        assert "window.addEventListener(\"afterprint\"" in html
        assert "height:auto !important" in html
        assert "max-height:none !important" in html
        assert "overflow:visible !important" in html
        assert "window.print()" in html

    assert (
        "body.luna-print-active > *:not(#luna-print-portal)"
        in monthly_html
    )
    assert (
        "body.luna-year-print-active > *:not(#luna-year-print-portal)"
        in yearly_html
    )

    print("Full Report Print Portal v2.5 tests passed.")


if __name__ == "__main__":
    main()
