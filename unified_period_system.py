"""Luna v3.55 — one calculated timeline, many presentation windows.

This module does not calculate a second sky.  It normalises the existing
reading_facts / weekly_view / major_event_registry outputs so Daily, Weekly,
Monthly, Year Ahead and admin surfaces can consume the same event contract.

Rule:
    astronomy -> canonical event -> protected-event merge -> localise ->
    convergence/presentation

Never hard-code AEST/AEDT.  ZoneInfo derives the local abbreviation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo
from event_identity import canonical_event_identity

PROTECTED_TYPES = {
    "eclipse", "solar_eclipse", "lunar_eclipse",
    "equinox", "solstice", "solar_anchor",
    "new_moon", "full_moon", "lunation",
    "station", "retrograde_station", "direct_station",
    "ingress", "slow_planet_aspect",
}

@dataclass(frozen=True)
class UnifiedEvent:
    event_id: str
    local_date: str
    display_label: str
    technical_label: str = ""
    event_type: str = "aspect"
    planets: tuple[str, ...] = ()
    phase: str = ""
    orb: float | None = None
    exact_utc: str = ""
    exact_local: str = ""
    timezone: str = ""
    timezone_label: str = ""
    utc_offset: str = ""
    protected: bool = False
    importance: float = 0.0
    supporting_events: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _offset_text(dt: datetime) -> str:
    offset = dt.utcoffset()
    if offset is None:
        return ""
    seconds = int(offset.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def local_metadata(instant_utc: datetime, timezone_name: str) -> dict[str, str]:
    """Convert one astronomical instant to a viewer's IANA timezone."""
    if instant_utc.tzinfo is None:
        instant_utc = instant_utc.replace(tzinfo=timezone.utc)
    else:
        instant_utc = instant_utc.astimezone(timezone.utc)
    local = instant_utc.astimezone(ZoneInfo(timezone_name))
    return {
        "exact_utc": instant_utc.isoformat(),
        "exact_local": local.isoformat(),
        "local_date": local.date().isoformat(),
        "local_time": f"{(local.hour % 12) or 12}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}",
        "timezone": timezone_name,
        "timezone_label": local.tzname() or timezone_name,
        "utc_offset": _offset_text(local),
    }


def _slug(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _event_type(label: str, technical: str = "") -> str:
    text = f"{label} {technical}".lower()
    if "eclipse" in text:
        return "eclipse"
    if "equinox" in text:
        return "equinox"
    if "solstice" in text:
        return "solstice"
    if "new moon" in text:
        return "new_moon"
    if "full moon" in text:
        return "full_moon"
    if "station" in text or "retrograde" in text or "direct" in text:
        return "station"
    if "enters " in text or "ingress" in text:
        return "ingress"
    return "aspect"


def _protected(event_type: str, tier: Any = None) -> bool:
    if event_type in PROTECTED_TYPES:
        return True
    try:
        return float(tier) <= 1
    except Exception:
        return False


_ASPECT_WORDS = (
    "conjunction",
    "conjunct",
    "opposition",
    "opposite",
    "square",
    "trine",
    "sextile",
)


def _canonical_identity(
    day: str,
    event_type: str,
    label: str,
    technical: str,
    planets: tuple[str, ...],
) -> str:
    """Compatibility wrapper around Luna's shared event identity authority."""
    return canonical_event_identity(
        day,
        event_type,
        technical.strip() or label.strip(),
        planets,
    )

def canonical_event_id(row: dict, timezone_name: str) -> str:
    """Return the canonical identity used by the unified event pipeline."""
    return _row_event(dict(row), timezone_name).event_id

def _row_event(row: dict, timezone_name: str) -> UnifiedEvent:
    label = str(row.get("event") or row.get("aspect") or row.get("evidence") or "Sky event")
    technical = str(row.get("technical") or "")
    day = str(row.get("date") or row.get("local_date") or "")
    etype = str(row.get("event_type") or _event_type(label, technical))
    planets = tuple(row.get("planets") or ())
    exact_local = str(row.get("exact_local") or "")
    zone_label = str(row.get("timezone_label") or "")

    # Existing weekly exact_time is already calculated from ZoneInfo.
    if not exact_local and row.get("exact_time"):
        exact_local = str(row["exact_time"])

    event_id = str(
        row.get("event_id")
        or _canonical_identity(day, etype, label, technical, planets)
    )

    return UnifiedEvent(
        event_id=event_id,
        local_date=day,
        display_label=label,
        technical_label=technical,
        event_type=etype,
        planets=planets,
        phase=str(row.get("phase") or ""),
        orb=row.get("orb"),
        exact_utc=str(row.get("exact_utc") or ""),
        exact_local=exact_local,
        timezone=timezone_name,
        timezone_label=zone_label,
        utc_offset=str(row.get("utc_offset") or ""),
        protected=bool(row.get("protected", _protected(etype, row.get("tier")))),
        importance=float(row.get("importance") or row.get("sky_score") or 0.0),
        supporting_events=tuple(row.get("supporting_events") or ()),
    )


def _merge_event_metadata(current: UnifiedEvent, incoming: UnifiedEvent) -> UnifiedEvent:
    """Combine two representations of one calculated event without losing protection."""

    # Presentation rows normally carry phase/supporting context.
    # Registry rows normally carry the cleaner technical label and protection.
    display = (
        incoming.display_label
        if incoming.phase and not current.phase
        else current.display_label
    )

    technical = current.technical_label or incoming.technical_label
    phase = current.phase or incoming.phase

    supporting = tuple(dict.fromkeys(
        current.supporting_events + incoming.supporting_events
    ))

    return UnifiedEvent(
        event_id=current.event_id,
        local_date=current.local_date,
        display_label=display,
        technical_label=technical,
        event_type=current.event_type,
        planets=current.planets or incoming.planets,
        phase=phase,
        orb=current.orb if current.orb is not None else incoming.orb,
        exact_utc=current.exact_utc or incoming.exact_utc,
        exact_local=current.exact_local or incoming.exact_local,
        timezone=current.timezone or incoming.timezone,
        timezone_label=current.timezone_label or incoming.timezone_label,
        utc_offset=current.utc_offset or incoming.utc_offset,
        protected=current.protected or incoming.protected,
        importance=max(current.importance, incoming.importance),
        supporting_events=supporting,
    )


def merge_rows(rows: Iterable[dict], major_rows: Iterable[dict], timezone_name: str) -> list[UnifiedEvent]:
    """Merge normal + registry rows by calculated identity without losing protected events."""
    by_key: dict[str, UnifiedEvent] = {}

    for raw in list(rows or ()) + list(major_rows or ()):
        event = _row_event(dict(raw), timezone_name)
        key = event.event_id.casefold()
        current = by_key.get(key)

        if current is None:
            by_key[key] = event
        else:
            by_key[key] = _merge_event_metadata(current, event)

    return sorted(
        by_key.values(),
        key=lambda e: (
            e.local_date,
            not e.protected,
            -e.importance,
            e.display_label,
        ),
    )


def packet_timeline(packet: dict, timezone_name: str | None = None) -> list[dict]:
    """Normalise an existing reading_facts/studio packet. No second calculation."""
    tz = timezone_name or str(packet.get("timezone") or "Australia/Sydney")
    events = merge_rows(packet.get("events") or (), packet.get("major_events") or (), tz)
    return [event.to_dict() for event in events]


def studio_sections(
    *,
    period_label: str,
    story_heading: str,
    story: str,
    timeline: list[dict],
    action: str = "",
) -> dict[str, Any]:
    """Shared Weekly-Studio grammar used by customer and admin pages."""
    return {
        "period_label": period_label,
        "story_heading": story_heading,
        "story": story,
        "timeline_heading": "In order",
        "timeline": timeline,
        "action": action,
    }


def daily_sky_cards(timeline: list[dict], start: date, count: int = 7) -> list[dict]:
    """Build fixed daily Sky Card slots from the calculated timeline.

    Selection order for each day:
        protected event -> strongest calculated event -> no selected event

    Empty slots are presentation state only. They never invent astronomy.

    Weekly Studio requests seven slots, Monday through Sunday. The function
    remains reusable for Daily and other presentation windows.
    """
    cards = []
    for offset in range(count):
        day = start + timedelta(days=offset)
        iso = day.isoformat()
        candidates = [e for e in timeline if e.get("local_date") == iso]

        candidates.sort(key=lambda e: (
            not bool(e.get("protected")),
            -float(e.get("importance") or 0.0),
            str(e.get("display_label") or ""),
        ))

        event = candidates[0] if candidates else None

        if event:
            timing = event.get("exact_local") or event.get("phase") or ""
            cards.append({
                "date": iso,
                "weekday": day.strftime("%A"),
                "event": event.get("display_label", ""),
                "technical": event.get("technical_label", ""),
                "phase": event.get("phase", ""),
                "timing": timing,
                "timezone": event.get("timezone", ""),
                "timezone_label": event.get("timezone_label", ""),
                "protected": bool(event.get("protected")),
                "has_event": True,
            })
        else:
            cards.append({
                "date": iso,
                "weekday": day.strftime("%A"),
                "event": "",
                "technical": "",
                "phase": "",
                "timing": "",
                "timezone": "",
                "timezone_label": "",
                "protected": False,
                "has_event": False,
            })

    return cards


def five_day_cards(timeline: list[dict], start: date, count: int = 5) -> list[dict]:
    """Compatibility wrapper for callers created before Luna v3.56."""
    return daily_sky_cards(timeline, start, count)


def deduplicated_caption(script: str, event: str, date_label: str, url: str = "") -> str:
    """Caption is deliberately not a copy of the video script."""
    hook = f"{date_label}: {event} changes the emphasis."
    return f"{hook}\n\n{url}".strip()








