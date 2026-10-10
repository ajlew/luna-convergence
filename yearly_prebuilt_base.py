from __future__ import annotations

"""Reusable pre-generated shared-sky layer for Paid Yearly.

GitHub Actions builds one 400-day horizon per Sun sign from the first day of
each calendar month. A customer may then start the paid rolling year on any
date in that month; the exact natal-to-transit work remains personal and is
still calculated at runtime.

This module intentionally does not calculate natal transits and does not call
the LLM.
"""

from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any

from paid_forecast_context import DEFAULT_BASE_ROOT, yearly_base_path


CANONICAL_YEARLY_PREBUILT_TIMEZONE = "Australia/Sydney"


def load_prebuilt_yearly_horizon(
    sign: str,
    start_date: date,
    timezone_name: str,
    *,
    root: Path | str = DEFAULT_BASE_ROOT,
) -> dict[str, Any] | None:
    """Load a monthly 400-day shared-sky horizon covering the requested 365 days."""
    requested_timezone = str(timezone_name or "")
    anchor = start_date.replace(day=1)
    requested_end = start_date + timedelta(days=364)

    candidates = [requested_timezone]
    if CANONICAL_YEARLY_PREBUILT_TIMEZONE not in candidates:
        candidates.append(CANONICAL_YEARLY_PREBUILT_TIMEZONE)

    for stored_timezone in candidates:
        path = yearly_base_path(sign, anchor, stored_timezone, root=root)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(value, dict):
            continue

        shared = dict(value.get("shared_sky") or {})
        try:
            source_start = date.fromisoformat(str(shared.get("start") or "")[:10])
            source_end = date.fromisoformat(str(shared.get("end") or "")[:10])
        except ValueError:
            continue

        if (
            str(shared.get("sign") or "").casefold() != str(sign).casefold()
            or str(shared.get("timezone") or "") != stored_timezone
            or source_start > start_date
            or source_end < requested_end
        ):
            continue

        signals = [
            dict(row)
            for row in list(shared.get("timing_major_signals") or [])
            if isinstance(row, dict)
        ]
        if not signals:
            continue

        shared["prebuilt_timezone"] = stored_timezone
        shared["reader_timezone"] = requested_timezone
        shared["requested_start"] = start_date.isoformat()
        shared["requested_end"] = requested_end.isoformat()

        output = dict(value)
        output["shared_sky"] = shared
        return output

    return None


def compact_yearly_shared_context(
    base: dict[str, Any],
    *,
    start_date: date,
    end_date: date,
    limit: int = 8,
) -> dict[str, Any]:
    """Small collective context for Luna; personal transits remain the main story."""
    shared = dict((base or {}).get("shared_sky") or {})
    rows = []
    for row in list(shared.get("timing_major_signals") or []):
        if not isinstance(row, dict):
            continue
        try:
            event_day = date.fromisoformat(str(row.get("event_date") or "")[:10])
        except ValueError:
            continue
        if not (start_date <= event_day <= end_date):
            continue
        rows.append(
            {
                "date": event_day.isoformat(),
                "label": str(row.get("display_label") or row.get("technical_label") or ""),
                "class": str(row.get("event_class") or ""),
                "tier": str(row.get("tier") or ""),
                "opportunity": bool(row.get("opportunity")),
                "action": " ".join(str(row.get("action") or "").split())[:180],
            }
        )

    tier_rank = {"FOUNDATION": 7, "S": 6, "A+": 5, "A": 4, "A-": 3, "B+": 2, "B": 1}
    rows.sort(
        key=lambda row: (
            -tier_rank.get(str(row.get("tier") or ""), 0),
            -int(bool(row.get("opportunity"))),
            str(row.get("date") or ""),
        )
    )
    selected = rows[: max(1, int(limit))]
    selected.sort(key=lambda row: (str(row.get("date") or ""), str(row.get("label") or "")))

    return {
        "source": "github-prebuilt-yearly-horizon",
        "base_hash": str((base or {}).get("base_hash") or ""),
        "prebuilt_timezone": str(shared.get("prebuilt_timezone") or shared.get("timezone") or ""),
        "reader_timezone": str(shared.get("reader_timezone") or ""),
        "events": selected,
    }
