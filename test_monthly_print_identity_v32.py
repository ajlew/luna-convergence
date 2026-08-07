from datetime import date
import re

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Aries",
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
    assert 'class="luna-report-identity"' in html
    assert re.search(r"Aries \d{1,2}:\d{2}(?:am|pm) August 2026", html)
    assert "Australia/Sydney" in html
    assert 'data-print-file-title="Aries ' in html
    assert re.search(r'data-print-file-title="Aries \d{1,2}\.\d{2}(?:am|pm) August 2026"', html)
    assert "document.title = printTitle" in html
    assert "prePrintDocumentTitle" in html
    assert "preparePrint();" in html
    assert "cloneNode(true)" in html

    print("Monthly print identity v3.2 tests passed.")


if __name__ == "__main__":
    main()
