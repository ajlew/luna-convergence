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

from plain_readings import (ROOT, generation_current, make_reading, read_document,
                            reading_path, write_document)
from plain_voice_generator import GenerationError, RateLimitError, generate_text


def run_signs(product, target, timezone, signs, *, build, generate=generate_text,
              root=ROOT, pause=30.0, refresh=False, check_only=False):
    failures = 0
    ready = 0
    for index, sign in enumerate(signs):
        period = target.strftime("%Y-%m") if product == "monthly" else target.isoformat()
        path = reading_path(product, period, timezone, root)
        document = read_document(path)
        copies = document.setdefault("signs", {})
        statuses = document.setdefault("jobs", {})
        stop_batch = False
        try:
            packet = build(product, target, sign, timezone)
            # Only current facts and the current writing revision can skip generation.
            if generation_current(copies.get(sign), packet) and not refresh:
                ready += 1
                statuses[sign] = "published"
                print(f"{sign}: already current")
                if not check_only:
                    write_document(path, document)
                continue
            if check_only:
                failures += 1
                print(f"{product} {period} {sign}: missing or needs writing refresh", file=sys.stderr)
                continue
            # Replace only after the new draft passes; a failed retry must not erase saved text.
            copies[sign] = make_reading(packet, generate(packet))
            ready += 1
            statuses[sign] = "published"
            print(f"{product} {period} {sign}: published", flush=True)
            warnings = copies[sign].get("editorial_warnings", [])
            if warnings:
                report_editorial_warnings(product, period, sign, warnings)
        except Exception as exc:
            failures += 1
            stop_batch = isinstance(exc, RateLimitError)
            # Do not store exception strings which might contain credentials.
            statuses[sign] = "failed"
            detail = str(exc) if isinstance(exc, GenerationError) else type(exc).__name__
            print(f"{sign}: failed ({detail})", file=sys.stderr)
        if not check_only:
            write_document(path, document)
        if stop_batch:
            print("Batch paused by provider limit; rerun to resume incomplete readings.", file=sys.stderr)
            report_coverage(product, period, ready, len(signs))
            return 2
        if pause and index < len(signs) - 1:
            time.sleep(pause)
    report_coverage(product, period, ready, len(signs))
    return 1 if failures else 0


def report_coverage(product, period, ready, total):
    line = f"{product} {period}: {ready}/{total} current readings"
    print(line, flush=True)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as stream:
            stream.write(f"- {line}\n")


def report_editorial_warnings(product, period, sign, warnings):
    """Surface concise QA notes without changing a successful job's status."""
    detail = '; '.join(warnings)
    line = f"{product} {period} {sign}: editorial warning — {detail}"
    print(line, file=sys.stderr, flush=True)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as stream:
            stream.write(f"- ⚠️ {line}\n")


def main(argv=None):
    from astrology_engine import SIGNS
    from reading_facts import build_packet
    from site_config import DEFAULT_TIMEZONE
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=("daily", "weekly", "monthly", "studio", "all", "maintain"), required=True)
    parser.add_argument("--date", help="Explicit period date for manual runs")
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--pause", type=float, default=30.0)
    parser.add_argument('--refresh', action='store_true', help='Regenerate the selected product/sign even when current')
    parser.add_argument('--check-only', action='store_true', help='Check completeness without any LLM calls or writes')
    args = parser.parse_args(argv)
    flags = (['--refresh'] if args.refresh else []) + (['--check-only'] if args.check_only else [])
    today = datetime.now(ZoneInfo(args.timezone)).date()
    if args.product == "maintain":
        from weekly_view import default_week_start
        live_week = default_week_start(today)
        result = 0
        for product, day in [('daily', today), ('weekly', live_week), ('monthly', today),
                             ('studio', live_week), ('daily', today + timedelta(days=1))]:
            status = main(['--product', product, '--date', day.isoformat(),
                           '--timezone', args.timezone, '--pause', str(args.pause)] + flags)
            result = max(result, status)
            if status == 2:
                break
            if args.pause and not args.check_only:
                time.sleep(args.pause)
        return result
    if args.product == "all":
        chosen = args.date or today.isoformat()
        result = 0
        for product in ("daily", "weekly", "monthly", "studio"):
            forwarded = ["--product", product, "--date", chosen,
                         "--timezone", args.timezone, "--pause", str(args.pause)]
            if args.sign:
                forwarded += ["--sign", args.sign]
            status = main(forwarded + flags)
            result = max(result, status)
            if status == 2:
                break
            if args.pause and not args.check_only and product != "studio":
                time.sleep(args.pause)
        return result
    # Scheduled Daily repairs today first, then prepares tomorrow. Cached signs cost no calls.
    if args.product == "daily" and not args.date:
        result = 0
        for day in (today, today + timedelta(days=1)):
            status = main(["--product", "daily", "--date", day.isoformat(),
                           "--timezone", args.timezone, "--pause", str(args.pause)]
                          + (["--sign", args.sign] if args.sign else []) + flags)
            result = max(result, status)
            if status == 2:
                break
        return result
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
                           build=build_packet, pause=args.pause, refresh=args.refresh, check_only=args.check_only)
    if args.product == "studio":
        from studio_readings import studio_packet, COLLECTIVE
        for product, day in [("studio_weekly", target)] + [
                (kind, target + timedelta(days=i))
                for i in range(7) for kind in ("studio_meaning", "studio_daily")]:
            if args.pause and not args.check_only:
                time.sleep(args.pause)
            status = run_signs(product, day, args.timezone, [COLLECTIVE],
                               build=studio_packet, pause=0, refresh=args.refresh, check_only=args.check_only)
            result = max(result, status)
            if status == 2:
                break
    return result


if __name__ == "__main__":
    raise SystemExit(main())
