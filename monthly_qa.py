from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence


def _event_value(event: object, key: str, default=None):
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def validate_monthly_arc(
    *,
    sign: str,
    events: Sequence[object],
    monthly_arc: Mapping[str, object] | None,
    house_weights: Mapping[int, float] | None = None,
) -> dict:
    """Run deterministic editorial sanity checks on one monthly arc.

    The validator does not claim astrological truth. It checks internal
    consistency: major events should be represented, story houses should be
    traceable to evidence, and the raw house ranking should not silently vanish.
    """
    arc = dict(monthly_arc or {})
    critical: list[str] = []
    warnings: list[str] = []

    beats = list(arc.get("beats") or [])
    evidence_text = " ".join(
        str(value)
        for beat in beats
        for value in (beat.get("evidence") or [])
    ).lower()

    eclipses = [
        event for event in events
        if str(_event_value(event, "kind", "")) == "eclipse"
    ]
    for eclipse in eclipses:
        title = str(_event_value(eclipse, "title", "eclipse"))
        if title.lower() not in evidence_text:
            critical.append(f"Major eclipse missing from narrative evidence: {title}")

    story_houses = {
        int(value)
        for key in ("primary_house", "secondary_house", "supporting_house")
        for value in [arc.get(key)]
        if value not in (None, "")
    }
    beat_houses = {
        int(value)
        for beat in beats
        for value in (beat.get("houses") or [])
    }
    for house in {int(arc.get("primary_house", 0) or 0), int(arc.get("secondary_house", 0) or 0)} - {0}:
        if house not in beat_houses:
            critical.append(f"Story house {house} is not traceable to a narrative beat")

    if house_weights:
        top_house = max(house_weights.items(), key=lambda item: item[1])[0]
        if int(top_house) not in story_houses:
            warnings.append(
                f"Top weighted house {top_house} is outside the primary, secondary and supporting story houses"
            )

    roles = [str(beat.get("role", "")) for beat in beats]
    role_counts = Counter(roles)
    duplicates = [role for role, count in role_counts.items() if role and count > 1]
    if duplicates:
        warnings.append(f"Duplicate narrative roles: {', '.join(duplicates)}")

    ranked = list(arc.get("ranked_scenarios") or [])
    if not ranked:
        warnings.append("No ranked scenario families were produced")
    elif not any(item.get("examples") for item in ranked[:5]):
        warnings.append("Top scenario families contain no concrete examples")

    return {
        "status": "pass" if not critical else "review",
        "sign": sign,
        "critical": critical,
        "warnings": warnings,
        "checks": {
            "eclipse_coverage": len(eclipses),
            "story_houses": sorted(story_houses),
            "beat_houses": sorted(beat_houses),
            "scenario_families": len(ranked),
        },
    }


def audit_batch_headlines(reports: Sequence[Mapping[str, object]]) -> dict:
    headlines = [
        str((report.get("monthly_arc") or {}).get("headline", "")).strip()
        for report in reports
    ]
    nonempty = [value for value in headlines if value]
    counts = Counter(nonempty)
    duplicates = {headline: count for headline, count in counts.items() if count > 1}
    return {
        "status": "pass" if not duplicates else "review",
        "total": len(nonempty),
        "unique": len(counts),
        "duplicates": duplicates,
    }
