from datetime import date
import re

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Virgo",
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

    # On-page identity remains human-readable.
    assert re.search(r"Virgo \d{1,2}:\d{2}(?:am|pm) August 2026", html)

    # Print-to-PDF title uses Luna's sortable original filename convention.
    assert 'data-print-file-title="2026-08_Virgo_Monthly"' in html

    # Set both the printable document and outer Streamlit document titles because
    # Chromium may derive the suggested PDF filename from either context.
    assert "document.title = printTitle" in html
    assert "window.parent.document.title = printTitle" in html

    # Do not immediately clear the title when Chromium enters print preview.
    assert "window.setTimeout(restorePrintTitles, 2500)" in html

    print("Monthly print filename v3.3 tests passed.")


if __name__ == "__main__":
    main()
