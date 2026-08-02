from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Sagittarius",
        date(2026, 7, 1),
        date(2026, 7, 31),
        "Australia/Sydney",
        "July 2026",
        nearest_city="Sydney",
        main_focus="General overview",
    )
    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(
        narrative,
        result,
        show_print=True,
        preview=False,
    )

    for required in (
        "July checks the bank balance before it upgrades the itinerary",
        "The month starts with the price. It ends with the possibility.",
        "The opening acquires structure",
        "The opportunity reveals its terms",
        "Attention meets the evidence test",
        "The public result must fit private life",
        "Decision calendar",
        "Evidence path",
        "Ranked scenario families",
        "Carryover evidence",
        "Full Moon in Capricorn",
        "New Moon in Cancer",
        "Mercury stations direct",
        "Sun conjunction Jupiter",
        "Full Moon in Aquarius",
        "luna-evidence-path",
        "luna-print-portal",
        "cloneNode(true)",
        "requestAnimationFrame(expandAllPrintDetails)",
    ):
        assert required in html, required

    assert html.count('class="luna-story-act"') == 4
    assert html.count('class="luna-story-date-card"') == 4
    assert "Include evidence" not in html
    assert "Monthly arc equation" not in html
    assert "luna-arc-card" not in html

    print("Monthly Arc Engine webpage tests passed.")


if __name__ == "__main__":
    main()
