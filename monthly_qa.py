from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence


def _event_value(event: object, key: str, default=None):
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _beat_by_role(beats: Sequence[Mapping[str, object]], role: str) -> Mapping[str, object] | None:
    return next((beat for beat in beats if str(beat.get("role", "")) == role), None)


def _scenario_provenance_houses(beat: Mapping[str, object] | None) -> set[int]:
    if not beat:
        return set()
    houses: set[int] = set()
    for item in beat.get("scenario_provenance") or []:
        for value in item.get("matched_houses") or []:
            try:
                houses.add(int(value))
            except (TypeError, ValueError):
                continue
    return houses


def _scenario_keys(beat: Mapping[str, object] | None) -> set[str]:
    if not beat:
        return set()
    return {
        str(item.get("key", ""))
        for item in beat.get("scenario_provenance") or []
        if item.get("key")
    }


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
    traceable to evidence, and every concrete scenario used by a major story
    beat must be supported by that beat's assigned house.
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

    primary_house = int(arc.get("primary_house", 0) or 0)
    secondary_house = int(arc.get("secondary_house", 0) or 0)
    complication = _beat_by_role(beats, "complication")
    climax = _beat_by_role(beats, "climax")
    resolution = _beat_by_role(beats, "resolution")
    relationship = _beat_by_role(beats, "relationship test")

    # Circuit breaker: scenario provenance must follow the house selected by the
    # event-led story engine. This is what prevents H9 visa scenarios leaking into
    # a H10 career eclipse, or H8 funding language taking over a H2 income story.
    if complication and primary_house:
        matched = _scenario_provenance_houses(complication)
        if complication.get("scenario_provenance") and primary_house not in matched:
            critical.append(
                f"Primary scenario provenance does not include story house {primary_house}"
            )

    for beat in (climax, resolution):
        if beat and secondary_house:
            matched = _scenario_provenance_houses(beat)
            if beat.get("scenario_provenance") and secondary_house not in matched:
                critical.append(
                    f"Secondary scenario provenance does not include story house {secondary_house}"
                )

    # House 2 and House 8 are both financial, but they are not interchangeable.
    # H2 = earned/personal money. H8 = shared/external money and funding.
    h8_only = {"external_money", "shared_finance_opportunity", "funding_application"}
    if primary_house == 2 and complication and _scenario_keys(complication) & h8_only:
        critical.append("House 2 story incorrectly contains House 8 funding/shared-money scenarios")
    if secondary_house == 2:
        for beat in (climax, resolution):
            if beat and _scenario_keys(beat) & h8_only:
                critical.append("House 2 ending incorrectly contains House 8 funding/shared-money scenarios")

    # A relationship beat is optional. If it exists it must have direct H5/H7
    # evidence, otherwise Love belongs only in the dedicated Love section.
    if relationship:
        relationship_houses = {int(value) for value in relationship.get("houses") or []}
        if not (relationship_houses & {5, 7}):
            critical.append("Relationship beat lacks direct House 5 or House 7 evidence")
        if house_weights:
            top_weight = max((float(value) for value in house_weights.values()), default=0.0)
            relationship_weight = max(
                (float(house_weights.get(house, 0.0)) for house in (5, 7)),
                default=0.0,
            )
            if relationship_weight < max(45.0, top_weight * 0.70):
                critical.append(
                    "Relationship beat was promoted despite weak House 5/7 monthly support"
                )

    legacy_phrases = (
        "Follow the sequence. The first scene is not the whole plot.",
        "Force a happy ending before the practical terms arrive.",
        "The direction changes around the middle of the month. a person",
        "are they here for you - or just for the fun of it?",
    )
    customer_text = " ".join(
        str(value)
        for key in ("opening", "complication", "pivot", "climax", "resolution", "relationship_test")
        for value in (arc.get(key) or [])
    )
    for phrase in legacy_phrases:
        if phrase.lower() in customer_text.lower():
            critical.append(f"Legacy fixed copy survived in monthly narrative: {phrase}")

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
            "primary_scenario_houses": sorted(_scenario_provenance_houses(complication)),
            "secondary_scenario_houses": sorted(
                _scenario_provenance_houses(climax) | _scenario_provenance_houses(resolution)
            ),
            "relationship_promoted": bool(relationship),
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


def audit_batch_repetition(reports: Sequence[Mapping[str, object]]) -> dict:
    """Flag repeated customer-facing story sentences across a 12-sign batch."""
    sentences: list[str] = []
    for report in reports:
        arc = report.get("monthly_arc") or {}
        for key in ("opening", "complication", "pivot", "climax", "resolution", "relationship_test"):
            for value in arc.get(key) or []:
                text = " ".join(str(value).split()).strip()
                if len(text) >= 45:
                    sentences.append(text)
    counts = Counter(sentences)
    duplicates = {text: count for text, count in counts.items() if count > 3}
    return {
        "status": "pass" if not duplicates else "review",
        "total_sentences": len(sentences),
        "duplicate_sentences": duplicates,
    }
