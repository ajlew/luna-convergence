"""Read-only presentation helpers for Luna paid monthly transit chapters.

Uses already-calculated TimingMapReport stories or paid Monthly natal overlays.
No ephemeris calculations, ranking changes, or LLM calls occur here.
"""
from __future__ import annotations

from datetime import date
from typing import Any

SLOW_PLANETS = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")


def _date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def overlaps(story: Any, start: date, end: date) -> bool:
    return any(
        period.start_date <= end and period.end_date >= start
        for period in (getattr(story, "periods", ()) or ())
    )


def yearly_month_stories(report: Any, start: Any, end: Any) -> list[Any]:
    start_date, end_date = _date(start), _date(end)
    if report is None or start_date is None or end_date is None:
        return []
    return sorted(
        [story for story in getattr(report, "stories", ()) if overlaps(story, start_date, end_date)],
        key=lambda story: (-float(getattr(story, "score", 0) or 0), str(getattr(story, "transit_planet", ""))),
    )


def yearly_month_rows(stories: list[Any], start: Any, end: Any, limit: int = 8) -> list[dict[str, str]]:
    start_date, end_date = _date(start), _date(end)
    if start_date is None or end_date is None:
        return []
    rows = []
    for story in stories[:limit]:
        hits = [hit for hit in (getattr(story, "hits", ()) or ()) if start_date <= hit.exact_date <= end_date]
        exact_dates = ", ".join(hit.exact_date.strftime("%d %b %Y") for hit in hits)
        rows.append({
            "planet": str(getattr(story, "transit_planet", "") or ""),
            "contact": f'{getattr(story, "transit_planet", "")} {getattr(story, "aspect", "")} natal {getattr(story, "natal_target", "")}',
            "phase": "Exact this period" if hits else "Active background",
            "exact": exact_dates,
            "house": str(getattr(story, "natal_house", "") or ""),
            "summary": str(getattr(story, "summary", "") or ""),
            "move": str(getattr(story, "move", "") or ""),
        })
    return rows


def monthly_overlay_rows(result: dict, limit: int = 12) -> list[dict[str, str]]:
    overlay = result.get("natal_overlay") or {}
    if not isinstance(overlay, dict):
        return []
    rows = []
    seen = set()
    for item in overlay.get("activations") or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("signal") or "").strip()
        day = str(item.get("date_label") or item.get("date") or "").strip()
        if not label or (day, label) in seen:
            continue
        seen.add((day, label))
        rows.append({"date": day, "contact": label})
        if len(rows) >= limit:
            break
    return rows


def slow_planet_summary(rows: list[dict[str, str]]) -> list[tuple[str, list[dict[str, str]]]]:
    return [(p, [row for row in rows if row.get("planet", "").casefold() == p.casefold()]) for p in SLOW_PLANETS]
