"""One independent job per sign. Successful readings survive other sign failures."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plain_readings import (ROOT, current_reading, make_reading, read_document,
                            reading_path, write_document)
from plain_voice_generator import GenerationError, RateLimitError, generate_text


def run_signs(product, target, timezone, signs, *, build, generate=generate_text,
              root=ROOT, pause=30.0):
    failures = 0
    for index, sign in enumerate(signs):
        period = target.strftime("%Y-%m") if product == "monthly" else target.isoformat()
        path = reading_path(product, period, timezone, root)
        document = read_document(path)
        copies = document.setdefault("signs", {})
        statuses = document.setdefault("jobs", {})
        stop_batch = False
        try:
            packet = build(product, target, sign, timezone)
            # A new calculation must not retain stale prose after a failed refresh.
            if current_reading(copies.get(sign), packet):
                statuses[sign] = "published"
                print(f"{sign}: already current")
                write_document(path, document)
                continue
            copies.pop(sign, None)
            copies[sign] = make_reading(packet, generate(packet))
            statuses[sign] = "published"
            print(f"{product} {period} {sign}: published", flush=True)
        except Exception as exc:
            failures += 1
            stop_batch = isinstance(exc, RateLimitError)
            # Do not store exception strings which might contain credentials.
            statuses[sign] = "failed"
            detail = str(exc) if isinstance(exc, GenerationError) else type(exc).__name__
            print(f"{sign}: failed ({detail})", file=sys.stderr)
        write_document(path, document)
        if stop_batch:
            print("Batch paused by provider limit; rerun to resume incomplete readings.", file=sys.stderr)
            return 2
        if pause and index < len(signs) - 1:
            time.sleep(pause)
    return 1 if failures else 0


def main(argv=None):
    from astrology_engine import SIGNS
    from reading_facts import build_packet
    from site_config import DEFAULT_TIMEZONE
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=("daily", "weekly", "monthly", "studio"), required=True)
    parser.add_argument("--date", help="Explicit period date for manual runs")
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--pause", type=float, default=30.0)
    args = parser.parse_args(argv)
    today = datetime.now(ZoneInfo(args.timezone)).date()
    if args.date:
        target = date.fromisoformat(args.date)
    elif args.product == "monthly":
        if today.day != 25:
            return 0
        target = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    elif args.product in ("weekly", "studio"):
        target = today + timedelta(days=(7 - today.weekday()) % 7)
    else:
        target = today + timedelta(days=1)
    if args.product in ("weekly", "studio"):
        target -= timedelta(days=target.weekday())
    elif args.product == "monthly":
        target = target.replace(day=1)
    print(f"Requested {args.product} for {target} ({args.timezone}); "
          f"signs: {args.sign or 'all'}", flush=True)
    result = 0
    if args.product != "studio":
        result = run_signs(args.product, target, args.timezone, [args.sign] if args.sign else SIGNS,
                           build=build_packet, pause=args.pause)
    if args.product == "studio":
        from studio_readings import studio_packet, COLLECTIVE
        for product, day in [("studio_weekly", target)] + [
                ("studio_daily", target + timedelta(days=i)) for i in range(7)]:
            if args.pause:
                time.sleep(args.pause)
            status = run_signs(product, day, args.timezone, [COLLECTIVE],
                               build=studio_packet, pause=0)
            result = max(result, status)
            if status == 2:
                break
    return result


if __name__ == "__main__":
    raise SystemExit(main())
