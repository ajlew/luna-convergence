from __future__ import annotations

import argparse
from datetime import date, datetime
import os
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from astrology_engine import SIGNS  # noqa: E402
from customer_experience import HOUSE_VOICE, free_daily_reading  # noqa: E402
from daily_narrative_v3 import build_daily_narrative  # noqa: E402
from daily_voice_publisher import (  # noqa: E402
    daily_candidate_path,
    make_daily_voice_document,
    write_daily_voice_document,
)
from luna_guided_voice import generate_guided_voice_copy  # noqa: E402


def _facts(sign: str, reading_date: date, timezone_name: str) -> dict:
    reading = free_daily_reading(sign, reading_date, timezone_name)
    narrative = build_daily_narrative(
        reading,
        sign=sign,
        reading_date=reading_date,
        timezone_name=timezone_name,
        house_voice=HOUSE_VOICE,
        previous_texts=[],
    )
    evidence = narrative.evidence
    return {
        "sign": sign,
        "date": reading_date.isoformat(),
        "timezone": timezone_name,
        "major_event": getattr(narrative, "major_event_label", ""),
        "supporting_events": list(getattr(narrative, "supporting_events", ()) or ()),
        "active_planets": list(evidence.active_planets),
        "aspect": evidence.aspect_label,
        "aspect_type": evidence.aspect_type,
        "orb": evidence.orb,
        "configured_orb": evidence.configured_orb,
        "phase": evidence.phase,
        "activated_houses": list(evidence.activated_houses),
        "house_meanings": list(evidence.house_meanings),
        "strongest_influence": evidence.strongest_influence,
        "active_window": evidence.active_window,
        "strength_score": evidence.strength_score,
        "confidence": evidence.confidence_label,
        "convergence": evidence.convergence_label,
        "convergence_score": evidence.convergence_score,
        "convergence_window": evidence.convergence_window,
        "technical_aspects": list(narrative.technical_aspects),
        "sun_house": narrative.sun_house,
        "moon_house": narrative.moon_house,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate all 12 published Daily Luna readings.")
    parser.add_argument(
        "--date",
        help="Reading date in YYYY-MM-DD format. Defaults to today in --timezone.",
    )
    parser.add_argument("--timezone", default="Australia/Sydney")
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=8.0,
        help="Pause between signs to stay inside provider token-per-minute limits.",
    )
    args = parser.parse_args()
    try:
        timezone = ZoneInfo(args.timezone)
    except Exception as exc:
        raise SystemExit(f"Invalid IANA timezone: {args.timezone}") from exc
    reading_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(timezone).date()
    )
    base_url = os.environ["LUNA_VOICE_BASE_URL"]
    model = os.environ["LUNA_VOICE_MODEL"]
    api_key = os.environ["LUNA_VOICE_API_KEY"]
    copies = {}
    for index, sign in enumerate(SIGNS):
        facts = _facts(sign, reading_date, args.timezone)
        copies[sign] = generate_guided_voice_copy(
            "daily", facts, base_url=base_url, model=model, api_key=api_key
        )
        print(f"Validated {sign}")
        if index < len(SIGNS) - 1 and args.pause_seconds > 0:
            time.sleep(args.pause_seconds)
    output = daily_candidate_path(reading_date, args.timezone)
    write_daily_voice_document(
        output,
        make_daily_voice_document(reading_date, args.timezone, copies),
    )
    print(f"Published Daily document written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
