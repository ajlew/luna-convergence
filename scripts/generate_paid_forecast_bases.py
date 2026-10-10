"""Pre-generate reusable calculation bases for Luna paid reports.

Monthly:
    One deterministic sign/month skeleton per zodiac sign. Existing behaviour
    is preserved.

Yearly:
    One reusable 400-day shared-sky horizon per zodiac sign and calendar month.
    A paid rolling year can start on any date in that month; runtime attaches
    the customer's Natal Player and exact personal transit map.

The Yearly generator makes no LLM calls.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import hashlib
import json
import sys
from zoneinfo import ZoneInfo
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astrology_engine import SIGNS
from major_event_registry import major_sky_events
from monthly_report_pipeline import build_production_monthly_report
from paid_forecast_context import (
    DEFAULT_BASE_ROOT,
    monthly_base_path,
    monthly_calculation_base,
    monthly_required_story_anchors,
    yearly_base_path,
    write_forecast_base,
)
from site_config import DEFAULT_TIMEZONE


YEARLY_HORIZON_DAYS = 400


def rolling_year_end(start_date: date) -> date:
    """Locked Paid Yearly rule: selected start date + 364 days."""
    return start_date + timedelta(days=364)


def yearly_horizon_bounds(target: date) -> tuple[date, date]:
    """One monthly cache safely covers every 365-day start inside that month."""
    anchor = target.replace(day=1)
    return anchor, anchor + timedelta(days=YEARLY_HORIZON_DAYS - 1)


def _stable_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_monthly(
    target: date,
    timezone_name: str,
    city: str,
    signs: list[str],
    root: Path,
) -> list[Path]:
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
        print(
            f"monthly base: {sign} {target:%Y-%m} -> "
            f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}"
        )
    return written


def generate_yearly(
    target: date,
    timezone_name: str,
    city: str,
    signs: list[str],
    root: Path,
    *,
    force: bool = False,
) -> list[Path]:
    anchor, horizon_end = yearly_horizon_bounds(target)
    written: list[Path] = []

    for sign in signs:
        path = yearly_base_path(sign, anchor, timezone_name, root=root)
        if path.is_file() and not force:
            written.append(path)
            print(
                f"yearly base current: {sign} {anchor:%Y-%m} -> "
                f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}"
            )
            continue

        signals = [
            signal.to_dict()
            for signal in major_sky_events(
                anchor,
                horizon_end,
                sign,
                timezone_name,
            )
        ]
        base = {
            "schema_version": "2.0",
            "base_schema_version": "yearly-shared-horizon-1",
            "product": "paid_year_ahead",
            "shared_sky": {
                "sign": sign,
                "label": f"{anchor.isoformat()} to {horizon_end.isoformat()}",
                "start": anchor.isoformat(),
                "end": horizon_end.isoformat(),
                "timezone": timezone_name,
                "nearest_city": city,
                "horizon_days": YEARLY_HORIZON_DAYS,
                "timing_major_signals": signals,
            },
        }
        base["base_hash"] = _stable_hash(base)
        write_forecast_base(base, path)
        written.append(path)
        print(
            f"yearly horizon: {sign} {anchor:%Y-%m} -> "
            f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}"
        )

    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=("monthly", "yearly"), default="monthly")
    parser.add_argument(
        "--date",
        help=(
            "Monthly: any date in target month. "
            "Yearly: any date in the target start month; the cached horizon anchors to day 1."
        ),
    )
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--city", default="Sydney")
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument("--root", default=str(DEFAULT_BASE_ROOT))
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite an existing Yearly horizon instead of using the current stored base.",
    )
    args = parser.parse_args(argv)

    ZoneInfo(args.timezone)
    today = datetime.now(ZoneInfo(args.timezone)).date()
    if args.date:
        target = date.fromisoformat(args.date)
    elif args.product == "monthly":
        target = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        target = today

    signs = [args.sign] if args.sign else list(SIGNS)
    root = Path(args.root)

    if args.product == "monthly":
        written = generate_monthly(target, args.timezone, args.city, signs, root)
    else:
        written = generate_yearly(
            target,
            args.timezone,
            args.city,
            signs,
            root,
            force=bool(args.force),
        )

    print(f"generated/verified {len(written)} {args.product} base file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
