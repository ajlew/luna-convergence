"""Allow-listed calculation data shared by the scheduled writer and public pages."""
from __future__ import annotations

from calendar import monthrange
from collections import Counter
from datetime import date, timedelta
from functools import lru_cache

from astrology_engine import HOUSE_NAMES, SIGNS, dominant_houses, period_events
from major_event_registry import major_sky_events
from weekly_view import build_weekly_view, monday_for, _event_houses


@lru_cache(maxsize=48)
def shared_week(monday: date, timezone: str):
    return build_weekly_view(monday, timezone)


def _major_rows(start: date, end: date, sign: str, timezone: str) -> list[dict]:
    return [{"date": s.event_date.isoformat(), "event": s.display_label,
             "technical": s.technical_label, "tier": s.tier,
             "planets": list(s.planets), "houses": list(s.houses)}
            for s in major_sky_events(start, end, sign, timezone)]


def build_packet(product: str, period_date: date, sign: str, timezone: str) -> dict:
    if sign not in SIGNS:
        raise ValueError("Choose a valid Sun sign")
    if product == "daily":
        # Preserve the existing Daily ranking and calculations. Only extract
        # factual fields; its legacy headlines, stories and advice are discarded.
        from customer_experience import free_daily_reading
        from daily_narrative_v3 import _evidence_snapshot
        from major_event_registry import signals_for_day
        reading = free_daily_reading(sign, period_date, timezone)
        evidence = _evidence_snapshot(reading, sign, period_date, timezone)
        primary, supporting = signals_for_day(
            period_date, native_sign=sign, timezone_name=timezone, product="daily")
        supporting_labels = tuple(item.display_label for item in supporting)
        use_major = bool(primary and (primary.must_surface_in("daily")
                         or primary.opportunity or primary.sky_score >= 80.0))
        if primary and not use_major and primary.sky_score >= 72.0:
            supporting_labels = (primary.display_label,) + supporting_labels
        supporting_labels = tuple(dict.fromkeys(supporting_labels))
        start = end = period_date
        major = _major_rows(start, end, sign, timezone)
        ranked_houses = list(evidence.activated_houses)
        header = [str(evidence.aspect_label), str(evidence.phase)]
        if evidence.orb is not None:
            header.append(f"Orb · {evidence.orb:.2f}°")
        header.extend(str(s) for s in supporting_labels)
        rows = [{"date": period_date.isoformat(), "aspect": evidence.aspect_label,
                 "planets": list(evidence.active_planets), "phase": evidence.phase,
                 "orb": evidence.orb, "houses": ranked_houses,
                 "house_meanings": list(evidence.house_meanings),
                 "technical_aspects": list(reading.aspects)}]
    elif product == "weekly":
        monday = monday_for(period_date)
        days = shared_week(monday, timezone)
        if product == "daily":
            days = tuple(day for day in days if day.reading_date == period_date)
        start = period_date if product == "daily" else monday
        end = start if product == "daily" else monday + timedelta(days=6)
        rows = []
        house_counts = Counter()
        header = []
        for day in days:
            houses = _event_houses(day, sign, timezone)
            house_counts.update(h for _, h in houses)
            rows.append({"date": day.reading_date.isoformat(), "event": day.evidence,
                         "planets": list(day.planets), "aspect": day.aspect_name,
                         "phase": day.phase,
                         # Registry major events do not carry a measured zero orb.
                         "orb": None if day.major_event_label else day.orb,
                         "exact_time": day.exact_time_label,
                         "planet_houses": list(houses),
                         "supporting_events": list(day.supporting_events)})
            header.append(f"{day.weekday} · {day.evidence}")
            header.extend(f"Also active · {s}" for s in day.supporting_events)
        major = _major_rows(start, end, sign, timezone)
        house_counts.update(h for event in major for h in event["houses"])
        ranked_houses = [h for h, _ in house_counts.most_common(4)]
    elif product == "monthly":
        start = period_date.replace(day=1)
        end = start.replace(day=monthrange(start.year, start.month)[1])
        events = period_events(start, end, sign, timezone)
        # Registry includes every eclipse and all seasonal gates; never truncate it.
        major = _major_rows(start, end, sign, timezone)
        selected = sorted(events, key=lambda e: e.importance, reverse=True)[:12]
        rows = [{"date": e.event_date.isoformat(), "event": e.title,
                 "planets": list(e.planets), "houses": list(e.houses),
                 "aspect": e.aspect_name, "orb": e.orb, "phase": e.applying_state}
                for e in sorted(selected, key=lambda e: e.event_date)]
        header = [f"{e['date']} · {e['event']}" for e in rows]
        ranked_houses = [h for h, _ in dominant_houses(start, end, sign, timezone, step_days=1)][:4]
    else:
        raise ValueError("Only free Daily, Weekly and Monthly are in scope")
    for event in major:
        line = f"{event['date']} · {event['event']}"
        if not any(event["event"] in existing for existing in header):
            header.append(line)
    return {"product": product, "period": start.strftime("%Y-%m") if product == "monthly" else start.isoformat(),
            "sign": sign, "timezone": timezone, "calculation_header": header,
            "life_areas": [HOUSE_NAMES[h] for h in ranked_houses],
            "events": rows, "major_events": major}
