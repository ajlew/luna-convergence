"""Pre-generate reusable calculation bases for Luna paid reports.

Monthly: one deterministic sign/month skeleton per zodiac sign. These files
contain no customer birth data and make no LLM calls. Paid Personal Monthly
loads the matching base and attaches the customer's natal context at runtime.

Yearly: the same contract can be generated manually for any rolling start date.
Because Year Ahead may start on any day, yearly generation is manual/on-demand
rather than a fixed twelve-file monthly schedule.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astrology_engine import SIGNS
from monthly_report_pipeline import build_production_monthly_report
from paid_forecast_context import (
    DEFAULT_BASE_ROOT,
    monthly_base_path,
    monthly_calculation_base,
    monthly_required_story_anchors,
    yearly_base_path,
    yearly_calculation_base,
    write_forecast_base,
)
from site_config import DEFAULT_TIMEZONE
from synthesis import period_report


def rolling_year_end(start_date: date) -> date:
    try:
        anniversary = start_date.replace(year=start_date.year + 1)
    except ValueError:
        anniversary = date(start_date.year + 1, 3, 1)
    return anniversary - timedelta(days=1)


def generate_monthly(target: date, timezone_name: str, city: str, signs: list[str], root: Path) -> list[Path]:
    target = target.replace(day=1)
    written: list[Path] = []
    for sign in signs:
        narrative, result = build_production_monthly_report(
            sign=sign,
            year=target.year,
            month=target.month,
            timezone_name=timezone_name,
            nearest_city=city,
            main_focus="General overview",
            personal_question="",
        )
        base = monthly_calculation_base(
            narrative,
            result,
            required_story_anchors=monthly_required_story_anchors(narrative, result),
        )
        path = monthly_base_path(sign, target.year, target.month, timezone_name, root=root)
        write_forecast_base(base, path)
        written.append(path)
        print(f"monthly base: {sign} {target:%Y-%m} -> {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return written


def generate_yearly(start_date: date, timezone_name: str, city: str, signs: list[str], root: Path) -> list[Path]:
    end_date = rolling_year_end(start_date)
    written: list[Path] = []
    for sign in signs:
        result = period_report(
            sign,
            start_date,
            end_date,
            timezone_name,
            f"{start_date.isoformat()} to {end_date.isoformat()}",
            transition_count=12,
            nearest_city=city,
            main_focus="General overview",
        )
        base = yearly_calculation_base(result)
        path = yearly_base_path(sign, start_date, timezone_name, root=root)
        write_forecast_base(base, path)
        written.append(path)
        print(f"yearly base: {sign} {start_date} -> {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=("monthly", "yearly"), default="monthly")
    parser.add_argument("--date", help="Monthly: any date in target month. Yearly: exact rolling start date.")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--city", default="Sydney")
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument("--root", default=str(DEFAULT_BASE_ROOT))
    args = parser.parse_args(argv)

    ZoneInfo(args.timezone)  # validate
    today = datetime.now(ZoneInfo(args.timezone)).date()
    if args.date:
        target = date.fromisoformat(args.date)
    elif args.product == "monthly":
        # Default manual/scheduled run builds next month.
        target = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        target = today

    signs = [args.sign] if args.sign else list(SIGNS)
    root = Path(args.root)
    if args.product == "monthly":
        written = generate_monthly(target, args.timezone, args.city, signs, root)
    else:
        written = generate_yearly(target, args.timezone, args.city, signs, root)
    print(f"generated {len(written)} {args.product} base file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
