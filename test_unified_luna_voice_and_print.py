from datetime import date
from pathlib import Path

from luna_editorial_system import (
    DO_LABEL,
    DONT_LABEL,
    GATEKEEPER_LINE,
    LUNA_SAYS_LABEL,
    TECHNICAL_LABEL,
    WHY_LUNA_LABEL,
)
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report
from yearly_experience_v1 import build_yearly_experience_html


def main() -> None:
    root = Path(__file__).parent
    daily = (root / "daily_narrative_v3.py").read_text(encoding="utf-8")

    for shared in (
        "LUNA_SAYS_LABEL",
        "DO_LABEL",
        "DONT_LABEL",
        "WHY_LUNA_LABEL",
        "TECHNICAL_LABEL",
    ):
        assert shared in daily

    monthly_result = period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        nearest_city="Sydney",
        main_focus="General overview",
    )
    monthly_html = build_monthly_experience_html(
        build_monthly_narrative(monthly_result),
        monthly_result,
    )

    yearly_result = period_report(
        "Sagittarius",
        date(2027, 1, 1),
        date(2027, 12, 31),
        "Australia/Sydney",
        "2027",
        nearest_city="Sydney",
        main_focus="General year ahead",
    )
    yearly_html = build_yearly_experience_html(yearly_result)

    for html in (monthly_html, yearly_html):
        assert LUNA_SAYS_LABEL in html
        assert DO_LABEL in html
        assert (DONT_LABEL in html) or ('Don&#x27;t' in html)
        assert WHY_LUNA_LABEL in html
        assert TECHNICAL_LABEL in html
        assert GATEKEEPER_LINE in html
        assert "luna-print-paper" in html
        assert "luna-print-orientation" in html
        assert "@page" in html

    print("Unified Luna voice and print tests passed.")


if __name__ == "__main__":
    main()
