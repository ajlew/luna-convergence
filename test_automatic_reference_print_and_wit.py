from datetime import date
from pathlib import Path

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    _other_house,
    _trigger_house,
    build_daily_narrative,
    reading_comparison_text,
)
from luna_editorial_system import luna_do_dont
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report
from yearly_experience_v1 import _top_houses, build_yearly_experience_html


def main() -> None:
    expected = (
        "Follow the effort. Chemistry can book its own flight.",
        "Mistake attention for value. A boarding pass is not commitment.",
    )
    assert luna_do_dont(5, 9) == expected

    monthly_result = period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        nearest_city="Sydney",
        main_focus="General overview",
    )
    monthly = build_monthly_narrative(monthly_result)
    assert (monthly.do_line, monthly.dont_line) == expected
    monthly_html = build_monthly_experience_html(monthly, monthly_result)

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
        assert "Include evidence" not in html
        assert "Print or save report" in html
        assert "document.fonts.ready" in html
        assert "window.setTimeout" in html
        assert "open=true" in html or "open = true" in html
        assert "page-break-before:always" in html
        assert "display:block" in html

    assert expected[0] in monthly_html
    assert expected[1] in monthly_html
    yearly_expected = luna_do_dont(*_top_houses(yearly_result))
    assert yearly_expected[0] in yearly_html
    assert yearly_expected[1] in yearly_html

    target = date(2026, 8, 1)
    reading = free_daily_reading("Sagittarius", target, "Australia/Sydney")
    previous = [
        reading_comparison_text(
            free_daily_reading(
                "Sagittarius",
                date(2026, 7, day),
                "Australia/Sydney",
            )
        )
        for day in (31, 30, 29, 28)
    ]
    daily = build_daily_narrative(
        reading,
        sign="Sagittarius",
        reading_date=target,
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=previous,
    )
    trigger = _trigger_house(reading)
    secondary = _other_house(reading, trigger)
    assert (daily.action_today, daily.watch_out) == luna_do_dont(
        trigger,
        secondary,
    )

    print("Automatic reference print and Luna wit tests passed.")


if __name__ == "__main__":
    main()
