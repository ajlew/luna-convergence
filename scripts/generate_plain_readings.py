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
from plain_voice_generator import GenerationError, generate_text


def run_signs(product, target, timezone, signs, *, build, generate=generate_text,
              root=ROOT, pause=8.0):
    failures = 0
    for index, sign in enumerate(signs):
        period = target.strftime("%Y-%m") if product == "monthly" else target.isoformat()
        path = reading_path(product, period, timezone, root)
        document = read_document(path)
        copies = document.setdefault("signs", {})
        statuses = document.setdefault("jobs", {})
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
        except Exception as exc:
            failures += 1
            # Do not store exception strings which might contain credentials.
            statuses[sign] = "failed"
            detail = str(exc) if isinstance(exc, GenerationError) else type(exc).__name__
            print(f"{sign}: failed ({detail})", file=sys.stderr)
        write_document(path, document)
        if pause and index < len(signs) - 1:
            time.sleep(pause)
    return 1 if failures else 0


def main(argv=None):
    from astrology_engine import SIGNS
    from reading_facts import build_packet
    from site_config import DEFAULT_TIMEZONE
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=("daily", "weekly", "monthly"), required=True)
    parser.add_argument("--date", help="Explicit period date for manual runs")
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--pause", type=float, default=8.0)
    args = parser.parse_args(argv)
    today = datetime.now(ZoneInfo(args.timezone)).date()
    if args.date:
        target = date.fromisoformat(args.date)
    elif args.product == "monthly":
        if today.day != 25:
            return 0
        target = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    elif args.product == "weekly":
        target = today + timedelta(days=(7 - today.weekday()) % 7)
    else:
        target = today + timedelta(days=1)
    if args.product == "weekly":
        target -= timedelta(days=target.weekday())
    elif args.product == "monthly":
        target = target.replace(day=1)
    return run_signs(args.product, target, args.timezone, [args.sign] if args.sign else SIGNS,
                     build=build_packet, pause=args.pause)


if __name__ == "__main__":
    raise SystemExit(main())
