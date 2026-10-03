from __future__ import annotations

"""Shared calculation context for Luna paid Personal Monthly and Year Ahead.

This is not another astrology engine. It packages the outputs of Luna's existing
engines into stable, auditable forecast bases. The shared sky is calculated once;
natal geometry and personal timing are attached later for the paid reader.

Monthly bases may be pre-generated for all twelve Sun signs and stored under
``generated/paid_forecast_bases/monthly``. A paid report can then reuse the
complete sign/month skeleton and ask Luna Voice only to contextualise it against
the customer's natal chart. That keeps LLM requests smaller and prevents a long
single completion from running out of output budget.
"""

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any


PAID_FORECAST_CONTEXT_VERSION = "1.4"
MONTHLY_BASE_SCHEMA_VERSION = "1.3"
YEARLY_BASE_SCHEMA_VERSION = "1.0"
DEFAULT_BASE_ROOT = Path(__file__).parent / "generated" / "paid_forecast_bases"


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    if hasattr(value, "to_dict"):
        try:
            return _json_value(value.to_dict())
        except Exception:
            pass
    return str(value)


def _pick(row: Any, *keys: str) -> dict[str, Any]:
    if not isinstance(row, dict):
        row = _json_value(row)
    if not isinstance(row, dict):
        return {"value": row}
    return {
        key: _json_value(row.get(key))
        for key in keys
        if row.get(key) not in (None, "", [], {}, ())
    }


def _rows(values: Any, *keys: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for value in list(values or []):
        row = _pick(value, *keys)
        if row:
            result.append(row)
    return result


def _date_value(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    # Key-date labels may be "11 October 2026" or "16-17 October 2026".
    match = re.search(
        r"\b(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{4})\b",
        text,
        flags=re.I,
    )
    if not match:
        return None
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
    try:
        return date(int(match.group(3)), months[match.group(2).lower()], int(match.group(1)))
    except ValueError:
        return None


def _month_bounds(start: date, end: date) -> list[tuple[str, str, date, date]]:
    """Three editorial phases. These are containers, not new astrology."""
    opening_end = min(end, start.replace(day=min(10, end.day)))
    middle_start = start.replace(day=min(11, end.day))
    middle_end = min(end, start.replace(day=min(20, end.day)))
    closing_start = start.replace(day=min(21, end.day))
    return [
        ("opening", "Opening", start, opening_end),
        ("middle", "Middle", middle_start, middle_end),
        ("closing", "Closing", closing_start, end),
    ]


def _row_day(row: dict[str, Any]) -> date | None:
    for key in ("event_date", "date", "exact_date", "start_date"):
        resolved = _date_value(row.get(key))
        if resolved is not None:
            return resolved
    return None


def _rows_in_window(rows: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        day = _row_day(row)
        if day is not None and start <= day <= end:
            selected.append(row)
    return selected


def _overlapping_rows(rows: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        row_start = _date_value(row.get("start_date") or row.get("start") or row.get("event_date") or row.get("date"))
        row_end = _date_value(row.get("end_date") or row.get("end") or row.get("event_date") or row.get("date"))
        if row_start is None and row_end is None:
            continue
        row_start = row_start or row_end
        row_end = row_end or row_start
        if row_start <= end and row_end >= start:
            selected.append(row)
    return selected


def _stable_hash(value: Any) -> str:
    payload = json.dumps(_json_value(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _event_title(row: dict[str, Any]) -> str:
    return " ".join(str(
        row.get("title")
        or row.get("display_label")
        or row.get("technical_label")
        or ""
    ).split())


def _event_key(row: dict[str, Any]) -> tuple[str, str]:
    day = str(row.get("event_date") or row.get("date") or "")[:10]
    title = re.sub(r"[^a-z0-9]+", " ", _event_title(row).casefold()).strip()
    return day, title


def _monthly_daily_story_ledger(shared_sky: dict[str, Any]) -> list[dict[str, Any]]:
    """One chronological row per active date. No phase/convergence grouping.

    This is the paid Monthly writing skeleton. Every calculated monthly event is
    preserved exactly once, then Luna Voice interprets one date at a time.
    Convergence and arc calculations remain available in the evidence layer but
    are deliberately not used to group the narrative.
    """
    event_rows = [row for row in list(shared_sky.get("events") or []) if isinstance(row, dict)]
    registry_rows = [row for row in list(shared_sky.get("major_sky_registry") or []) if isinstance(row, dict)]

    registry_by_key = {_event_key(row): row for row in registry_rows if _event_title(row)}
    registry_by_day: dict[str, list[dict[str, Any]]] = {}
    for row in registry_rows:
        day = str(row.get("event_date") or row.get("date") or "")[:10]
        if day:
            registry_by_day.setdefault(day, []).append(row)

    by_day: dict[str, list[dict[str, Any]]] = {}
    seen_event_keys: set[tuple[str, str]] = set()
    for source in sorted(event_rows, key=lambda row: (str(row.get("event_date") or row.get("date") or ""), _event_title(row))):
        day = str(source.get("event_date") or source.get("date") or "")[:10]
        title = _event_title(source)
        if not day or not title:
            continue
        key = _event_key(source)
        if key in seen_event_keys:
            continue
        seen_event_keys.add(key)
        row = dict(source)
        registry = registry_by_key.get(key)
        if registry:
            for field in ("tier", "action", "interpretation", "opportunity", "must_surface", "technical_label"):
                value = registry.get(field)
                if value not in (None, "", [], {}, ()):
                    row[f"registry_{field}"] = _json_value(value)
        by_day.setdefault(day, []).append(row)

    # A registry event should not disappear merely because a lower-level event
    # serializer omitted it. Add only genuinely missing title/date pairs.
    for day, rows in registry_by_day.items():
        for source in rows:
            key = _event_key(source)
            if key in seen_event_keys or not _event_title(source):
                continue
            seen_event_keys.add(key)
            by_day.setdefault(day, []).append(dict(source))

    ledger: list[dict[str, Any]] = []
    for day in sorted(by_day):
        try:
            resolved = date.fromisoformat(day)
            date_label = resolved.strftime("%d %B %Y").lstrip("0")
        except ValueError:
            date_label = day
        ledger.append({
            "source_id": f"monthly-day:{day}",
            "date": day,
            "date_label": date_label,
            "events": by_day[day],
        })
    return ledger




def _daily_style_briefs(sign: str, start: date, end: date, timezone_name: str) -> list[dict[str, Any]]:
    """Build the same calculation briefs used by Luna's free Daily, for every day.

    Paid Monthly does not invent a second daily calculation path.  It reuses
    ``reading_facts.build_packet('daily', ...)`` and ``reading_quality.grounded_brief``
    so the monthly writer sees the same primary aspect, supporting influences
    and life-area translation that produced the public Daily.
    """
    from reading_facts import build_packet
    from reading_quality import grounded_brief

    rows: list[dict[str, Any]] = []
    current = start
    while current <= end:
        packet = build_packet("daily", current, sign, timezone_name)
        brief = grounded_brief(packet)
        rows.append({
            "source_id": f"daily-brief:{current.isoformat()}",
            "date": current.isoformat(),
            "brief": _json_value(brief),
        })
        current = date.fromordinal(current.toordinal() + 1)
    return rows


def _free_monthly_scaffold(sign: str, month_start: date, timezone_name: str) -> dict[str, Any]:
    """Read the already-generated Free Monthly arc and its grounded monthly facts.

    This makes the paid sign/month base genuinely partially complete: the
    collective month is understood once in GitHub, while customer-specific
    natal context is attached later at runtime.  No LLM call is made here.
    """
    from reading_facts import build_packet
    from reading_quality import grounded_brief
    from plain_readings import load_reading

    packet = build_packet("monthly", month_start.replace(day=1), sign, timezone_name)
    brief = grounded_brief(packet)
    reading = load_reading(packet) or {}

    monthly_events: list[dict[str, Any]] = []
    for event in list(brief.get("events") or []):
        if not isinstance(event, dict):
            continue
        monthly_events.append({
            "date": str(event.get("date") or ""),
            "event": str(event.get("event") or event.get("aspect") or ""),
            "aspect": str(event.get("aspect") or ""),
            "phase": event.get("phase"),
            "orb": event.get("orb"),
            "life_areas": [
                str(item.get("life_area"))
                for item in (event.get("event_life_areas") or [])
                if isinstance(item, dict) and item.get("life_area")
            ],
        })

    major_events: list[dict[str, Any]] = []
    for event in list(brief.get("major_events") or []):
        if not isinstance(event, dict):
            continue
        major_events.append({
            "date": str(event.get("date") or ""),
            "event": str(event.get("event") or event.get("technical") or ""),
            "technical": str(event.get("technical") or ""),
            "tier": event.get("tier"),
            "life_areas": [
                str(item.get("life_area"))
                for item in (event.get("event_life_areas") or [])
                if isinstance(item, dict) and item.get("life_area")
            ],
        })

    return {
        "collective_story": " ".join(str(reading.get("voice_body") or "").split()),
        "collective_story_status": "published" if reading.get("voice_body") else "missing",
        "monthly_events": monthly_events,
        "major_events": major_events,
        "dominant_life_areas": list(packet.get("life_areas") or []),
        "required_turning_points": _json_value(brief.get("required_turning_points") or []),
    }


def _thread_label(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    lower = text.casefold()
    if lower.startswith("orb ") or lower.startswith("orb ·"):
        return ""
    if lower in {"exact", "applying", "separating", "closest to exact today"}:
        return ""
    if re.fullmatch(r"(?:orb\s*[·:]?\s*)?\d+(?:\.\d+)?°?", lower):
        return ""
    return text


def _daily_transit_threads(daily_briefs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find repeated calculated labels across neighbouring Daily briefs.

    A repeated aspect later in the month is a new pass, not one month-long
    transit.  Runs are therefore split whenever appearances are more than two
    days apart.  This prevents, for example, two Mercury-Mars exact hits weeks
    apart from being described as continuously active between them.
    """
    occurrences: dict[str, list[str]] = {}
    display: dict[str, str] = {}
    for row in daily_briefs:
        day = str(row.get("date") or "")[:10]
        brief = row.get("brief") or {}
        labels = list(brief.get("calculated_labels") or [])
        for event in list(brief.get("major_events") or []):
            if isinstance(event, dict):
                labels.append(event.get("event") or event.get("technical") or "")
        for raw in labels:
            label = _thread_label(raw)
            if not label:
                continue
            key = re.sub(r"[^a-z0-9]+", " ", label.casefold()).strip()
            if not key:
                continue
            display.setdefault(key, label)
            occurrences.setdefault(key, []).append(day)

    threads: list[dict[str, Any]] = []
    for key, date_values in occurrences.items():
        parsed = []
        for value in sorted(dict.fromkeys(d for d in date_values if d)):
            try:
                parsed.append(date.fromisoformat(value))
            except ValueError:
                pass
        if not parsed:
            continue
        runs: list[list[date]] = [[parsed[0]]]
        for current in parsed[1:]:
            if (current - runs[-1][-1]).days <= 2:
                runs[-1].append(current)
            else:
                runs.append([current])
        structural = any(token in key for token in ("retrograde", "station", "eclipse", "new moon", "full moon", "equinox", "solstice"))
        for run in runs:
            if len(run) < 2 and not structural:
                continue
            threads.append({
                "label": display.get(key, key),
                "start": run[0].isoformat(),
                "end": run[-1].isoformat(),
                "days_seen": len(run),
            })
    threads.sort(key=lambda row: (str(row.get("start") or ""), str(row.get("label") or "")))
    return threads


def _timezone_slug(timezone_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", str(timezone_name or "UTC")).strip("-") or "UTC"


def monthly_base_path(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    *,
    root: Path | str = DEFAULT_BASE_ROOT,
) -> Path:
    return Path(root) / "monthly" / f"{int(year):04d}-{int(month):02d}" / _timezone_slug(timezone_name) / f"{str(sign).lower()}.json"


def yearly_base_path(
    sign: str,
    start_date: date,
    timezone_name: str,
    *,
    root: Path | str = DEFAULT_BASE_ROOT,
) -> Path:
    return Path(root) / "yearly" / start_date.isoformat() / _timezone_slug(timezone_name) / f"{str(sign).lower()}.json"


def write_forecast_base(base: dict[str, Any], path: Path | str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(_json_value(base), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def load_monthly_calculation_base(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    *,
    root: Path | str = DEFAULT_BASE_ROOT,
) -> dict[str, Any] | None:
    path = monthly_base_path(sign, year, month, timezone_name, root=root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    shared = value.get("shared_sky") or {}
    if (
        str(shared.get("sign") or "").casefold() != str(sign).casefold()
        or str(shared.get("start") or "")[:7] != f"{int(year):04d}-{int(month):02d}"
        or str(shared.get("timezone") or "") != str(timezone_name or "")
    ):
        return None
    return value


def load_yearly_calculation_base(
    sign: str,
    start_date: date,
    timezone_name: str,
    *,
    root: Path | str = DEFAULT_BASE_ROOT,
) -> dict[str, Any] | None:
    path = yearly_base_path(sign, start_date, timezone_name, root=root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    shared = value.get("shared_sky") or {}
    if (
        str(shared.get("sign") or "").casefold() != str(sign).casefold()
        or str(shared.get("start") or "") != start_date.isoformat()
        or str(shared.get("timezone") or "") != str(timezone_name or "")
    ):
        return None
    return value


def natal_context(snapshot: Any) -> dict[str, Any]:
    """Derived natal geometry/interpretation only; never raw birth inputs."""
    if snapshot is None:
        return {}
    return {
        "positions": [
            {
                "planet": str(getattr(item, "planet", "")),
                "sign": str(getattr(item, "sign", "")),
                "degree": round(float(getattr(item, "degree", 0.0) or 0.0), 3),
                "house": getattr(item, "house", None),
                "retrograde": bool(getattr(item, "retrograde", False)),
            }
            for item in (getattr(snapshot, "positions", ()) or ())
        ],
        "aspects": [
            {
                "planet_1": str(getattr(item, "planet1", "")),
                "aspect": str(getattr(item, "name", "")),
                "planet_2": str(getattr(item, "planet2", "")),
                "orb": round(float(getattr(item, "orb", 0.0) or 0.0), 3),
                "strength": round(float(getattr(item, "strength", 0.0) or 0.0), 3),
            }
            for item in (getattr(snapshot, "aspects", ()) or ())
        ],
        "strengths": [
            {
                "title": str(getattr(item, "title", "")),
                "interpretation": str(getattr(item, "text", "")),
                "strength": str(getattr(item, "strength", "")),
                "watch": str(getattr(item, "watch", "")),
                "evidence": str(getattr(item, "evidence", "")),
            }
            for item in (getattr(snapshot, "signatures", ()) or ())
        ],
        "dominant_element": str(getattr(snapshot, "dominant_element", "") or ""),
        "dominant_modality": str(getattr(snapshot, "dominant_modality", "") or ""),
        "birth_time_known": bool(getattr(snapshot, "birth_time_known", False)),
    }


def monthly_required_story_anchors(narrative: Any, result: dict[str, Any]) -> list[dict[str, Any]]:
    """Structural monthly events that a paid story must not silently lose."""
    anchors: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(title: Any, date_label: Any = "", detail: Any = "") -> None:
        clean_title = " ".join(str(title or "").split())
        if not clean_title:
            return
        lowered = clean_title.casefold()
        if not any(token in lowered for token in (
            "retrograde", "station", "eclipse", "new moon", "full moon", "equinox", "solstice"
        )):
            return
        key = re.sub(r"[^a-z0-9]+", " ", lowered).strip()
        if not key or key in seen:
            return
        seen.add(key)
        anchors.append({
            "title": clean_title,
            "date_label": " ".join(str(date_label or "").split()),
            "detail": " ".join(str(detail or "").split()),
        })

    for chapter in list(getattr(narrative, "chapters", ()) or ()):
        paragraphs = [
            " ".join(str(item or "").split())
            for item in (getattr(chapter, "paragraphs", ()) or ())
            if str(item or "").strip()
        ]
        add(
            getattr(chapter, "title", "") or getattr(chapter, "hook", ""),
            getattr(chapter, "date_range", "") or getattr(chapter, "label", ""),
            paragraphs[0] if paragraphs else "",
        )

    for item in list(result.get("major_sky_registry") or []) + list(result.get("major_sky_events") or []) + list(result.get("major_transitions") or []):
        if not isinstance(item, dict):
            continue
        add(
            item.get("display_label") or item.get("technical_label") or item.get("title"),
            item.get("event_date") or item.get("date") or "",
            item.get("interpretation") or item.get("detail") or "",
        )
    return anchors


def _chapter_rows(narrative: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chapter in list(getattr(narrative, "chapters", ()) or ()):
        rows.append({
            "label": str(getattr(chapter, "label", "") or ""),
            "date_range": str(getattr(chapter, "date_range", "") or ""),
            "hook": str(getattr(chapter, "hook", "") or ""),
            "title": str(getattr(chapter, "title", "") or ""),
            "paragraphs": [str(value) for value in (getattr(chapter, "paragraphs", ()) or ())],
            "action": str(getattr(chapter, "action", "") or ""),
            "evidence": [str(value) for value in (getattr(chapter, "evidence", ()) or ())],
        })
    return rows


def _key_date_rows(narrative: Any) -> list[dict[str, Any]]:
    return [
        {
            "date_label": str(getattr(item, "date_label", "") or ""),
            "consequence": str(getattr(item, "consequence", "") or ""),
            "response": str(getattr(item, "response", "") or ""),
            "evidence": str(getattr(item, "evidence", "") or ""),
        }
        for item in (getattr(narrative, "key_dates", ()) or ())
    ]


def _monthly_story_skeleton(shared_sky: dict[str, Any]) -> list[dict[str, Any]]:
    start = _date_value(shared_sky.get("start"))
    end = _date_value(shared_sky.get("end"))
    if start is None or end is None:
        return []

    events = list(shared_sky.get("events") or [])
    registry = list(shared_sky.get("major_sky_registry") or [])
    transitions = list(shared_sky.get("major_transitions") or [])
    convergences = [row for row in list(shared_sky.get("convergences") or []) if isinstance(row, dict)]
    inherited = list(shared_sky.get("inherited_events") or [])
    anchors = list(shared_sky.get("required_story_anchors") or [])
    key_dates = list(shared_sky.get("key_dates") or [])
    source_chapters = list(shared_sky.get("calculated_chronology") or [])

    phases: list[dict[str, Any]] = []
    for phase_id, label, phase_start, phase_end in _month_bounds(start, end):
        phase_chapters = []
        for row in source_chapters:
            row_day = _date_value(row.get("date_range") or row.get("label"))
            if row_day is None:
                # Existing Monthly chapters are already ordered opening/middle/closing.
                continue
            if phase_start <= row_day <= phase_end:
                phase_chapters.append(row)
        phases.append({
            "id": phase_id,
            "label": label,
            "start": phase_start.isoformat(),
            "end": phase_end.isoformat(),
            "events": _rows_in_window(events, phase_start, phase_end),
            "major_sky": _rows_in_window(registry, phase_start, phase_end),
            "major_transitions": _rows_in_window(transitions, phase_start, phase_end),
            "convergences": _overlapping_rows(convergences, phase_start, phase_end),
            "inherited_context": inherited if phase_id == "opening" else [],
            "required_story_anchors": [
                row for row in anchors
                if (lambda day: day is not None and phase_start <= day <= phase_end)(
                    _date_value(row.get("date_label"))
                )
            ],
            "key_dates": [
                row for row in key_dates
                if (lambda day: day is not None and phase_start <= day <= phase_end)(
                    _date_value(row.get("date_label"))
                )
            ],
            "source_chapters": phase_chapters,
        })

    # If the source narrative's chapter labels are not machine-parseable, preserve
    # them by position rather than silently dropping useful deterministic work.
    if source_chapters:
        if not phases[0]["source_chapters"]:
            phases[0]["source_chapters"] = source_chapters[:1]
        if len(source_chapters) > 1 and not phases[1]["source_chapters"]:
            phases[1]["source_chapters"] = source_chapters[1:-1] or source_chapters[1:2]
        if len(source_chapters) > 2 and not phases[2]["source_chapters"]:
            phases[2]["source_chapters"] = source_chapters[-1:]

    return phases


def monthly_calculation_base(
    narrative: Any,
    result: dict[str, Any],
    *,
    required_story_anchors: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    include_story_background: bool = True,
) -> dict[str, Any]:
    """Complete deterministic sign/month before natal personalisation.

    ``include_story_background`` is True for the GitHub pre-generation job, so
    each stored base contains the Free Monthly macro arc plus all Free-Daily
    grounded briefs. Runtime callers can set it False when they only need a
    light reader-specific overlay and should not rebuild the month.
    """
    chronology = _chapter_rows(narrative)
    key_dates = _key_date_rows(narrative)
    anchors = list(required_story_anchors or monthly_required_story_anchors(narrative, result))
    start_date = _date_value(result.get("start"))
    end_date = _date_value(result.get("end"))
    sign = str(result.get("sign") or "")
    timezone_name = str(result.get("timezone_name") or "")
    story_background_ready = bool(
        include_story_background
        and start_date is not None and end_date is not None and sign and timezone_name
    )
    daily_briefs = (
        _daily_style_briefs(sign, start_date, end_date, timezone_name)
        if story_background_ready
        else []
    )
    collective_month = (
        _free_monthly_scaffold(sign, start_date, timezone_name)
        if story_background_ready
        else {}
    )
    shared_sky = {
        "sign": str(result.get("sign") or ""),
        "label": str(result.get("label") or getattr(narrative, "label", "") or ""),
        "start": str(result.get("start") or ""),
        "end": str(result.get("end") or ""),
        "timezone": str(result.get("timezone_name") or ""),
        "nearest_city": str(result.get("nearest_city") or ""),
        "events": _rows(
            result.get("events"),
            "event_date", "date", "title", "kind", "planets", "houses",
            "aspect_name", "aspect", "orb", "applying_state", "phase",
            "polarity", "importance", "detail",
        ),
        "major_sky_registry": _rows(
            result.get("major_sky_registry"),
            "event_date", "display_label", "technical_label", "tier", "planets",
            "houses", "aspect", "phase", "orb", "action", "interpretation",
            "opportunity", "must_surface",
        ),
        "major_sky_events": _rows(
            result.get("major_sky_events"),
            "event_date", "display_label", "technical_label", "tier", "planets",
            "houses", "aspect", "phase", "orb", "action", "interpretation",
            "opportunity", "must_surface",
        ),
        "major_transitions": _rows(
            result.get("major_transitions"),
            "event_date", "date", "title", "kind", "planets", "houses",
            "aspect_name", "aspect", "orb", "phase", "polarity", "importance", "detail",
        ),
        "retrograde_cycles": _json_value(result.get("retrograde_cycles") or []),
        "convergences": _json_value(result.get("convergences") or []),
        "inherited_events": _rows(
            result.get("inherited_events"),
            "event_date", "date", "title", "kind", "planets", "houses",
            "aspect_name", "aspect", "orb", "phase", "polarity", "importance", "detail",
        ),
        "dominant_houses": _json_value(result.get("dominant_houses") or []),
        "solar_convergence": _json_value(result.get("solar_convergence") or {}),
        "monthly_arc": _json_value(result.get("monthly_arc") or {}),
        "monthly_trajectory": _json_value(result.get("monthly_trajectory") or {}),
        "monthly_decision": _json_value(result.get("monthly_decision") or {}),
        "calculated_chronology": chronology,
        "key_dates": key_dates,
        "required_story_anchors": _json_value(anchors),
        "collective_month": _json_value(collective_month),
        "daily_briefs": _json_value(daily_briefs),
        "transit_threads": _json_value(_daily_transit_threads(daily_briefs)),
        "story_background_ready": bool(story_background_ready and daily_briefs),
    }
    shared_sky["daily_story_ledger"] = _monthly_daily_story_ledger(shared_sky)
    # Retain the older three-phase skeleton for backward compatibility only.
    # Paid Monthly voice no longer consumes it.
    shared_sky["story_skeleton"] = _monthly_story_skeleton(shared_sky)
    base = {
        "schema_version": PAID_FORECAST_CONTEXT_VERSION,
        "base_schema_version": MONTHLY_BASE_SCHEMA_VERSION,
        "product": "paid_personal_monthly",
        "shared_sky": shared_sky,
    }
    base["base_hash"] = _stable_hash(base)
    return base


def contextualize_monthly(
    base: dict[str, Any],
    *,
    snapshot: Any,
    natal_overlay: dict[str, Any] | None,
    reader_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the Natal Player to an already-calculated sign/month base."""
    overlay = dict(natal_overlay or {})
    context = {
        **_json_value(base),
        "natal_player": natal_context(snapshot),
        "personal_month": {
            "summary": str(overlay.get("summary") or ""),
            "activations": _json_value(overlay.get("activations") or []),
            "time_known": overlay.get("time_known"),
        },
        "reader_context": _json_value(reader_context or {}),
    }
    context["context_hash"] = _stable_hash(context)
    return context


def monthly_voice_days(context: dict[str, Any]) -> dict[str, Any]:
    """LLM-ready paid Monthly built from the same briefs as Luna's free Daily.

    The daily briefs are intermediate evidence, not customer-facing sections.
    Luna first writes Daily-style micro-stories from them, then a second pass
    weaves those stories into one month-long narrative with the reader as the
    protagonist.
    """
    shared = dict(context.get("shared_sky") or {})
    natal = dict(context.get("natal_player") or {})
    personal = dict(context.get("personal_month") or {})
    reader_context = dict(context.get("reader_context") or {})
    activations = [row for row in list(personal.get("activations") or []) if isinstance(row, dict)]

    daily_briefs = [row for row in list(shared.get("daily_briefs") or []) if isinstance(row, dict)]
    if not daily_briefs:
        start = _date_value(shared.get("start"))
        end = _date_value(shared.get("end"))
        sign = str(shared.get("sign") or "")
        timezone_name = str(shared.get("timezone") or "")
        if start is not None and end is not None and sign and timezone_name:
            daily_briefs = _daily_style_briefs(sign, start, end, timezone_name)

    activations_by_day: dict[str, list[dict[str, Any]]] = {}
    for row in activations:
        day = str(row.get("date") or "")[:10]
        if day:
            activations_by_day.setdefault(day, []).append(row)

    days: list[dict[str, Any]] = []
    for row in daily_briefs:
        day = str(row.get("date") or "")[:10]
        if not day:
            continue
        days.append({
            "source_id": str(row.get("source_id") or f"daily-brief:{day}"),
            "date": day,
            "daily_brief": _json_value(row.get("brief") or {}),
            "personal_activations": _json_value(activations_by_day.get(day, [])),
        })
    days.sort(key=lambda item: str(item.get("date") or ""))

    shared_context = {
        "sign": shared.get("sign"),
        "label": shared.get("label"),
        "start": shared.get("start"),
        "end": shared.get("end"),
        "transit_threads": shared.get("transit_threads") or _daily_transit_threads(daily_briefs),
        "retrograde_cycles": shared.get("retrograde_cycles"),
        "required_story_anchors": shared.get("required_story_anchors"),
        "natal_strengths": list(natal.get("strengths") or []),
        "natal_element": natal.get("dominant_element"),
        "natal_mode": natal.get("dominant_modality"),
        "personal_activations": _json_value(activations),
        "reader_context": reader_context,
    }
    return {"shared_context": shared_context, "days": days}


def monthly_voice_sections(context: dict[str, Any]) -> dict[str, Any]:
    """Small LLM-ready slices: one lead plus three chronological chapters."""
    shared = dict(context.get("shared_sky") or {})
    natal = dict(context.get("natal_player") or {})
    personal = dict(context.get("personal_month") or {})
    activations = [row for row in list(personal.get("activations") or []) if isinstance(row, dict)]
    reader_context = dict(context.get("reader_context") or {})

    chapters: list[dict[str, Any]] = []
    for chapter in list(shared.get("story_skeleton") or []):
        if not isinstance(chapter, dict):
            continue
        start = _date_value(chapter.get("start"))
        end = _date_value(chapter.get("end"))
        chapter_activations = []
        if start is not None and end is not None:
            for row in activations:
                day = _date_value(row.get("date"))
                if day is not None and start <= day <= end:
                    chapter_activations.append(row)
        chapters.append({
            "id": chapter.get("id"),
            "label": chapter.get("label"),
            "start": chapter.get("start"),
            "end": chapter.get("end"),
            "calculated_story": chapter,
            "personal_activations": chapter_activations,
            "natal_strengths": list(natal.get("strengths") or []),
            "reader_context": reader_context,
        })

    lead = {
        "sign": shared.get("sign"),
        "label": shared.get("label"),
        "start": shared.get("start"),
        "end": shared.get("end"),
        "dominant_houses": shared.get("dominant_houses"),
        "monthly_decision": shared.get("monthly_decision"),
        "monthly_trajectory": shared.get("monthly_trajectory"),
        "required_story_anchors": shared.get("required_story_anchors"),
        "chapter_map": [
            {
                "id": item.get("id"), "label": item.get("label"),
                "start": item.get("start"), "end": item.get("end"),
                "major_sky": item.get("major_sky"),
            }
            for item in list(shared.get("story_skeleton") or []) if isinstance(item, dict)
        ],
        "natal_strengths": list(natal.get("strengths") or []),
        "personal_activations": activations,
        "reader_context": reader_context,
    }
    return {"lead": lead, "chapters": chapters}


def yearly_calculation_base(result: dict[str, Any]) -> dict[str, Any]:
    """Shared rolling-year calculations before natal transits are attached."""
    shared_sky = {
        "sign": str(result.get("sign") or ""),
        "label": str(result.get("label") or ""),
        "start": str(result.get("start") or ""),
        "end": str(result.get("end") or ""),
        "timezone": str(result.get("timezone_name") or ""),
        "nearest_city": str(result.get("nearest_city") or ""),
        "events": _rows(
            result.get("events"),
            "event_date", "date", "title", "kind", "planets", "houses",
            "aspect_name", "aspect", "orb", "phase", "polarity", "importance", "detail",
        ),
        "major_sky_registry": _rows(
            result.get("major_sky_registry"),
            "event_date", "display_label", "technical_label", "tier", "planets",
            "houses", "aspect", "phase", "orb", "action", "interpretation", "opportunity",
        ),
        "major_sky_events": _rows(
            result.get("major_sky_events"),
            "event_date", "display_label", "technical_label", "tier", "planets",
            "houses", "aspect", "phase", "orb", "action", "interpretation", "opportunity",
        ),
        "major_transitions": _rows(
            result.get("major_transitions"),
            "event_date", "date", "title", "kind", "planets", "houses",
            "aspect_name", "aspect", "orb", "phase", "polarity", "importance", "detail",
        ),
        "retrograde_cycles": _json_value(result.get("retrograde_cycles") or []),
        "convergences": _json_value(result.get("convergences") or []),
        "dominant_houses": _json_value(result.get("dominant_houses") or []),
        "solar_year_chapters": _json_value(result.get("solar_year_chapters") or []),
        "yearly_game_map": _json_value(result.get("yearly_game_map") or {}),
        "yearly_protected_evidence": _json_value(result.get("yearly_protected_evidence") or []),
    }
    base = {
        "schema_version": PAID_FORECAST_CONTEXT_VERSION,
        "base_schema_version": YEARLY_BASE_SCHEMA_VERSION,
        "product": "paid_year_ahead",
        "shared_sky": shared_sky,
    }
    base["base_hash"] = _stable_hash(base)
    return base


def _timing_story(story: Any) -> dict[str, Any]:
    return {
        "transiting_planet": str(getattr(story, "transit_planet", "")),
        "natal_target": str(getattr(story, "natal_target", "")),
        "aspect": str(getattr(story, "aspect", "")),
        "natal_house": getattr(story, "natal_house", None),
        "score": round(float(getattr(story, "score", 0.0) or 0.0), 3),
        "polarity": str(getattr(story, "polarity", "")),
        "headline": str(getattr(story, "headline", "")),
        "summary": str(getattr(story, "summary", "")),
        "move": str(getattr(story, "move", "")),
        "active_periods": [
            {"start": period.start_date.isoformat(), "end": period.end_date.isoformat()}
            for period in (getattr(story, "periods", ()) or ())
        ],
        "exact_hits": [
            {
                "date": hit.exact_date.isoformat(),
                "orb": round(float(getattr(hit, "orb", 0.0) or 0.0), 3),
                "retrograde": bool(getattr(hit, "retrograde", False)),
            }
            for hit in (getattr(story, "hits", ()) or ())
        ],
    }


def contextualize_yearly(
    base: dict[str, Any],
    *,
    snapshot: Any,
    timing_report: Any,
    reader_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the Natal Player + personal timing map to the rolling-year base."""
    if timing_report is None:
        personal = {}
    else:
        personal = {
            "start_date": timing_report.start_date.isoformat(),
            "end_date": timing_report.end_date.isoformat(),
            "timezone": str(timing_report.timezone_name),
            "recurring_themes": _json_value(getattr(timing_report, "major_games", ()) or ()),
            "turning_points": _json_value(getattr(timing_report, "turning_points", ()) or ()),
            "rule_changes": _json_value(getattr(timing_report, "rule_changes", ()) or ()),
            "transits": [_timing_story(story) for story in (getattr(timing_report, "stories", ()) or ())],
            "major_sky_events": _json_value(getattr(timing_report, "major_sky_events", ()) or ()),
            "personal_major_contacts": _json_value(getattr(timing_report, "personal_major_events", ()) or ()),
        }
    context = {
        **_json_value(base),
        "natal_player": natal_context(snapshot),
        "personal_year": personal,
        "reader_context": _json_value(reader_context or {}),
    }
    context["context_hash"] = _stable_hash(context)
    return context
