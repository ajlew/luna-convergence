from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
from typing import Any

from luna_guided_voice import (
    validate_guided_collection_copy,
    validate_guided_voice_copy,
)
MONTHLY_VOICE_SCHEMA_VERSION = "1.0"
DEFAULT_MONTHLY_ROOT = Path(__file__).parent / "generated" / "monthly"


def _period_key(result: dict) -> str:
    start = date.fromisoformat(str(result.get("start")))
    return f"{start.year:04d}-{start.month:02d}"


def monthly_candidate_path(
    year: int,
    month: int,
    timezone_name: str,
    *,
    root: Path | None = None,
) -> Path:
    safe_timezone = timezone_name.replace("/", "-").replace("\\", "-")
    return (root or DEFAULT_MONTHLY_ROOT) / f"{int(year):04d}-{int(month):02d}_{safe_timezone}.json"


def build_public_monthly_facts(narrative, result: dict, sign: str, timezone_name: str) -> dict[str, Any]:
    """Build the closed sign-only packet used by both publishing and display."""
    from monthly_experience_v1 import build_monthly_reader_chronology

    rows = build_monthly_reader_chronology(narrative, result)
    return {
        "sign": sign,
        "period": _period_key(result),
        "timezone": timezone_name,
        "forecast_basis": "sun_sign_whole_sign_houses",
        "dominant_houses": list(result.get("dominant_houses") or []),
        "events": [
            {
                "date": row.get("date_label"),
                "transit": row.get("technical"),
                "signal": row.get("badge"),
                "influence": row.get("influence"),
                "also_active": list(row.get("also") or []),
            }
            for row in rows
        ],
    }


def build_public_monthly_event_facts(
    narrative,
    result: dict,
    sign: str,
    timezone_name: str,
) -> dict[str, Any]:
    from monthly_experience_v1 import build_monthly_reader_chronology

    rows = build_monthly_reader_chronology(narrative, result)
    return {
        "sign": sign,
        "period": _period_key(result),
        "timezone": timezone_name,
        "items": [
            {
                "source_id": f"{row.get('date_label', index)}:{index}",
                "date": row.get("date_label"),
                "badge": row.get("badge"),
                "technical": row.get("technical"),
                "influence": row.get("influence"),
                "also_active": list(row.get("also") or []),
            }
            for index, row in enumerate(rows)
        ],
    }


def load_monthly_voice_candidate(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    main_facts: dict[str, Any],
    event_facts: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any] | None:
    path = monthly_candidate_path(year, month, timezone_name, root=root)
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if document.get("schema_version") != MONTHLY_VOICE_SCHEMA_VERSION:
        return None
    if document.get("period") != f"{int(year):04d}-{int(month):02d}":
        return None
    if document.get("timezone") != timezone_name:
        return None

    payload = (document.get("signs") or {}).get(sign)
    if not isinstance(payload, dict):
        return None
    main = payload.get("main")
    dated_events = payload.get("dated_events")
    main_valid, _ = validate_guided_voice_copy("monthly", main, main_facts)
    events_valid, _ = validate_guided_collection_copy(
        "monthly_events", dated_events, event_facts
    )
    return {
        "main": main if main_valid else None,
        "dated_events": dated_events if events_valid else None,
        "diagnostic": str((document.get("diagnostics") or {}).get(sign) or ""),
    }


def make_monthly_voice_document(
    year: int,
    month: int,
    timezone_name: str,
    signs: dict[str, dict[str, Any]],
    *,
    status: dict[str, str] | None = None,
    diagnostics: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": MONTHLY_VOICE_SCHEMA_VERSION,
        "period": f"{int(year):04d}-{int(month):02d}",
        "timezone": timezone_name,
        "signs": signs,
        "status": status or {sign: "current" for sign in signs},
        "diagnostics": diagnostics or {},
    }


def write_monthly_voice_document(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)
