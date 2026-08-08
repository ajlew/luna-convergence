from __future__ import annotations

"""Single production pathway for every Luna monthly report.

Both the normal Monthly Preview and Ephemeris Admin historical tests MUST call
this module. This prevents historical tests from drifting into a shortened or
special-case renderer and guarantees like-for-like comparison across years.
"""

from calendar import month_name
from datetime import date, timedelta
from typing import Any

from monthly_experience_v1 import render_monthly_experience
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report

MONTHLY_PIPELINE_VERSION = "1.0"


def month_date_range(year: int, month: int) -> tuple[date, date]:
    year = int(year)
    month = int(month)
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")

    start = date(year, month, 1)
    if month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def build_production_monthly_report(
    *,
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    nearest_city: str,
    main_focus: str = "General overview",
) -> tuple[Any, dict]:
    """Run the exact calculation+narrative pipeline used for full monthlys."""
    start_date, end_date = month_date_range(year, month)
    result = period_report(
        sign,
        start_date,
        end_date,
        timezone_name,
        f"{month_name[int(month)]} {int(year)}",
        transition_count=9,
        nearest_city=nearest_city,
        main_focus=main_focus,
    )
    narrative = build_monthly_narrative(result, main_focus=main_focus)
    return narrative, result


def render_production_monthly_report(
    narrative: Any,
    result: dict,
    *,
    show_print: bool = True,
    order_reference: str = "",
) -> None:
    """Render the complete customer-style monthly product, never the short preview."""
    render_monthly_experience(
        narrative,
        result,
        show_print=show_print,
        preview=False,
        order_reference=order_reference,
    )
