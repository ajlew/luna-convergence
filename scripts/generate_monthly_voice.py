from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from astrology_engine import SIGNS  # noqa: E402
from luna_guided_voice import (  # noqa: E402
    generate_guided_collection_copy,
    generate_guided_voice_copy,
    validate_guided_collection_copy,
    validate_guided_voice_copy,
)
from monthly_report_pipeline import build_production_monthly_report  # noqa: E402
from monthly_voice_publisher import (  # noqa: E402
    build_public_monthly_event_facts,
    build_public_monthly_facts,
    make_monthly_voice_document,
    monthly_candidate_path,
    write_monthly_voice_document,
)
from solar_cycle import representative_city_name  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the 12 cached public Monthly sign forecasts."
    )
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int, choices=range(1, 13))
    parser.add_argument("--next-month", action="store_true")
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument("--sign", choices=SIGNS)
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=8.0,
        help="Pause between signs; provider-level 429 handling remains active.",
    )
    args = parser.parse_args()

    timezone = ZoneInfo(args.timezone)
    now = datetime.now(timezone)
    year = int(args.year or now.year)
    month = int(args.month or now.month)
    if args.next_month and not args.year and not args.month:
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    output = monthly_candidate_path(year, month, args.timezone)
    signs: dict[str, dict] = {}
    status: dict[str, str] = {}
    diagnostics: dict[str, str] = {}
    if output.exists():
        try:
            existing = json.loads(output.read_text(encoding="utf-8"))
            if (
                existing.get("period") == f"{year:04d}-{month:02d}"
                and existing.get("timezone") == args.timezone
            ):
                signs.update(existing.get("signs") or {})
                status.update(existing.get("status") or {})
                diagnostics.update(existing.get("diagnostics") or {})
        except Exception:
            pass

    base_url = os.environ["LUNA_VOICE_BASE_URL"]
    model = os.environ["LUNA_VOICE_MODEL"]
    api_key = os.environ["LUNA_VOICE_API_KEY"]
    requested = [args.sign] if args.sign else list(SIGNS)
    failures = 0

    for index, sign in enumerate(requested):
        print(f"Preparing {sign} {year:04d}-{month:02d}")
        try:
            narrative, result = build_production_monthly_report(
                sign=sign,
                year=year,
                month=month,
                timezone_name=args.timezone,
                nearest_city=representative_city_name(args.timezone),
                main_focus="General overview",
            )
            main_facts = build_public_monthly_facts(
                narrative, result, sign, args.timezone
            )
            event_facts = build_public_monthly_event_facts(
                narrative, result, sign, args.timezone
            )
            payload = dict(signs.get(sign) or {})
            main_valid, _ = validate_guided_voice_copy(
                "monthly", payload.get("main"), main_facts
            )
            events_valid, _ = validate_guided_collection_copy(
                "monthly_events", payload.get("dated_events"), event_facts
            )

            if not main_valid:
                print(f"Generating {sign} main story")
                payload["main"] = generate_guided_voice_copy(
                    "monthly",
                    main_facts,
                    base_url=base_url,
                    model=model,
                    api_key=api_key,
                )
            if not events_valid:
                print(f"Generating {sign} dated events")
                payload["dated_events"] = generate_guided_collection_copy(
                    "monthly_events",
                    event_facts,
                    base_url=base_url,
                    model=model,
                    api_key=api_key,
                )

            signs[sign] = payload
            status[sign] = "current"
            diagnostics.pop(sign, None)
            print(f"Validated {sign}")
        except Exception as exc:
            failures += 1
            status[sign] = "partial" if signs.get(sign) else "failed"
            diagnostics[sign] = " ".join(str(exc).split())[:700]
            print(f"Failed {sign}: {diagnostics[sign]}", file=sys.stderr)

        write_monthly_voice_document(
            output,
            make_monthly_voice_document(
                year,
                month,
                args.timezone,
                signs,
                status=status,
                diagnostics=diagnostics,
            ),
        )
        if index < len(requested) - 1 and args.pause_seconds > 0:
            time.sleep(args.pause_seconds)

    print(f"Monthly document written to {output}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
