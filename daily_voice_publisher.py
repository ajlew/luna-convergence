from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
from typing import Any

from luna_guided_voice import facts_hash, validate_guided_voice_copy


DAILY_VOICE_SCHEMA_VERSION = "1.0"
DEFAULT_DAILY_ROOT = Path(__file__).parent / "generated" / "daily"


def daily_candidate_path(
    reading_date: date,
    timezone_name: str,
    *,
    root: Path | None = None,
) -> Path:
    safe_timezone = timezone_name.replace("/", "-").replace("\\", "-")
    return (root or DEFAULT_DAILY_ROOT) / f"{reading_date.isoformat()}_{safe_timezone}.json"


def load_daily_voice_candidate(
    sign: str,
    reading_date: date,
    timezone_name: str,
    facts: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any] | None:
    path = daily_candidate_path(reading_date, timezone_name, root=root)
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if document.get("schema_version") != DAILY_VOICE_SCHEMA_VERSION:
        return None
    if document.get("date") != reading_date.isoformat():
        return None
    if document.get("timezone") != timezone_name:
        return None
    copy = (document.get("signs") or {}).get(sign)
    valid, _errors = validate_guided_voice_copy("daily", copy, facts)
    return copy if valid else None


def make_daily_voice_document(
    reading_date: date,
    timezone_name: str,
    copies: dict[str, dict[str, Any]],
    *,
    status: dict[str, str] | None = None,
    diagnostics: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": DAILY_VOICE_SCHEMA_VERSION,
        "date": reading_date.isoformat(),
        "timezone": timezone_name,
        "signs": copies,
        "status": status or {sign: "current" for sign in copies},
        "diagnostics": diagnostics or {},
    }


def write_daily_voice_document(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def expected_daily_hash(facts: dict[str, Any]) -> str:
    return facts_hash("daily", facts)
