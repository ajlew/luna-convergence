from datetime import date
from pathlib import Path

from monthly_report_pdf_home_v3 import build_monthly_homepage_html, build_monthly_homepage_pdf
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
    html = build_monthly_homepage_html(result, order_reference="LC-TEST-HOMEPAGE-V3")
    for required in (
        "font-family:'Bodoni Moda'",
        "font-family:'Josefin Sans'",
        "font-family:'IBM Plex Mono'",
        'class="brand-row"',
        'class="top-nav"',
        'class="editorial-title"',
        'class="reading-card"',
        'class="trust-strip"',
        "The wider horizon moves into view when the result can stand in public",
    ):
        assert required in html, required

    pdf = build_monthly_homepage_pdf(result, order_reference="LC-TEST-HOMEPAGE-V3")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 10_000
    print("Homepage-style monthly PDF v3 test passed.")


if __name__ == "__main__":
    main()
