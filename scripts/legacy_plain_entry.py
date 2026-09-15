"""Translate earlier command-line dates without invoking legacy JSON generation."""
import argparse
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from scripts.generate_plain_readings import main as generate


def main(product, argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--week")
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--next-month", action="store_true")
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument("--sign")
    args = parser.parse_args(argv)
    today = datetime.now(ZoneInfo(args.timezone)).date()
    target = args.date or args.week
    if target is None:
        target_date = today
        if args.next_month:
            target_date = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
        if product == "monthly":
            target_date = date(args.year or target_date.year, args.month or target_date.month, 1)
        target = target_date.isoformat()
    forwarded = ["--product", product, "--date", target, "--timezone", args.timezone]
    if args.sign:
        forwarded.extend(["--sign", args.sign])
    return generate(forwarded)
