from __future__ import annotations

from collections import Counter
from datetime import date
import re
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
        [
            *(str(value) for beat in beats for value in (beat.get("evidence") or [])),
            *(str(value) for value in (arc.get("primary_plot_evidence") or [])),
            *(str(value) for value in (arc.get("secondary_plot_evidence") or [])),
        ]
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
        for key in ("primary_house", "secondary_house", "tertiary_house")
        for value in [arc.get(key)]
        if value not in (None, "")
    }
    background_houses = {
        int(value)
        for value in [arc.get("supporting_house")]
        if value not in (None, "")
    }
    beat_houses = {
        int(value)
        for beat in beats
        for value in (beat.get("houses") or [])
    }
    primary_plot_houses = {int(value) for value in (arc.get("primary_plot_houses") or [])}
    secondary_plot_houses = {int(value) for value in (arc.get("secondary_plot_houses") or [])}
    traceable_houses = beat_houses | primary_plot_houses | secondary_plot_houses
    for house in {
        int(arc.get("primary_house", 0) or 0),
        int(arc.get("secondary_house", 0) or 0),
        int(arc.get("tertiary_house", 0) or 0),
    } - {0}:
        if house not in traceable_houses:
            critical.append(f"Narrative house {house} is not traceable to the selected event graph")

    if house_weights:
        top_house = max(house_weights.items(), key=lambda item: item[1])[0]
        if int(top_house) not in story_houses | background_houses:
            warnings.append(
                f"Top weighted house {top_house} is outside the narrative houses and retained background house"
            )

    roles = [str(beat.get("role", "")) for beat in beats]
    role_counts = Counter(roles)
    duplicates = [role for role, count in role_counts.items() if role and count > 1]
    if duplicates:
        warnings.append(f"Duplicate narrative roles: {', '.join(duplicates)}")

    # Paid-report hygiene: a narrative window can never run backwards.
    for beat in beats:
        start_value = beat.get("start_date")
        end_value = beat.get("end_date") or start_value
        if not start_value or not end_value:
            continue
        try:
            if date.fromisoformat(str(start_value)) > date.fromisoformat(str(end_value)):
                critical.append(
                    f"Narrative window runs backwards for {beat.get('role', 'beat')}: {start_value} > {end_value}"
                )
        except ValueError:
            critical.append(f"Invalid narrative date in {beat.get('role', 'beat')}: {start_value} / {end_value}")

    ranked = list(arc.get("ranked_scenarios") or [])
    if not ranked:
        warnings.append("No ranked scenario families were produced")
    elif not any(item.get("examples") for item in ranked[:5]):
        warnings.append("Top scenario families contain no concrete examples")

    primary_house = int(arc.get("primary_house", 0) or 0)
    secondary_house = int(arc.get("secondary_house", 0) or 0)
    tertiary_house = int(arc.get("tertiary_house", 0) or 0)
    complication = _beat_by_role(beats, "complication")
    climax = _beat_by_role(beats, "climax")
    resolution = _beat_by_role(beats, "resolution")
    relationship = _beat_by_role(beats, "relationship test")

    # Circuit breaker: public scenario provenance must follow the houses selected
    # by the event-led story engine. Use the strict plot-level provenance stored
    # by the engine rather than assuming a conventional beat (for example the
    # "complication" beat) always owns the primary plot.
    def _arc_provenance_houses(key: str) -> set[int]:
        return {
            int(house)
            for item in (arc.get(key) or [])
            for house in (item.get("matched_houses") or [])
        }

    primary_provenance = _arc_provenance_houses("primary_scenario_provenance")
    secondary_provenance = _arc_provenance_houses("secondary_scenario_provenance")
    tertiary_provenance = _arc_provenance_houses("tertiary_scenario_provenance")
    if primary_house and arc.get("primary_scenario_provenance") and primary_house not in primary_provenance:
        critical.append(
            f"Primary scenario provenance does not include story house {primary_house}"
        )
    if secondary_house and arc.get("secondary_scenario_provenance") and secondary_house not in secondary_provenance:
        critical.append(
            f"Secondary scenario provenance does not include story house {secondary_house}"
        )
    if tertiary_house and arc.get("tertiary_scenario_provenance") and tertiary_house not in tertiary_provenance:
        critical.append(
            f"Tertiary scenario provenance does not include bridge house {tertiary_house}"
        )

    # A tertiary house is a bridge, not a third independent forecast. It must
    # be present in both major story clusters and clear the convergence gate.
    if tertiary_house:
        if tertiary_house in {primary_house, secondary_house}:
            critical.append("Tertiary house duplicates a primary or secondary narrative house")
        if float(arc.get("convergence_score", 0.0) or 0.0) < 0.58:
            critical.append("Tertiary house was promoted below the convergence threshold")
        if tertiary_house not in primary_plot_houses:
            critical.append(
                f"Tertiary house {tertiary_house} is not supported by the primary plot cluster"
            )
        if tertiary_house not in secondary_plot_houses:
            critical.append(
                f"Tertiary house {tertiary_house} is not supported by the secondary plot cluster"
            )
        axis = str(arc.get("theme_axis", ""))
        if "Bridge:" not in axis:
            critical.append("Three-house narrative does not label the tertiary house as a bridge")

    # House 2 and House 8 are both financial, but they are not interchangeable.
    # H2 = earned/personal money. H8 = shared/external money and funding. Check
    # the strict plot-level provenance, not whichever conventional beat happens
    # to sit nearest the same date.
    h8_only = {"external_money", "shared_finance_opportunity", "funding_application"}
    primary_keys = {str(item.get("key", "")) for item in (arc.get("primary_scenario_provenance") or [])}
    secondary_keys = {str(item.get("key", "")) for item in (arc.get("secondary_scenario_provenance") or [])}
    if primary_house == 2 and primary_keys & h8_only:
        critical.append("House 2 story incorrectly contains House 8 funding/shared-money scenarios")
    if secondary_house == 2 and secondary_keys & h8_only:
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

    repeated_word = re.search(r"\b([A-Za-z]{3,})\s+\1\b", customer_text, flags=re.IGNORECASE)
    if repeated_word:
        critical.append(f"Repeated customer word survived in monthly narrative: {repeated_word.group(0)}")

    return {
        "status": "pass" if not critical else "review",
        "sign": sign,
        "critical": critical,
        "warnings": warnings,
        "checks": {
            "eclipse_coverage": len(eclipses),
            "story_houses": sorted(story_houses),
            "background_houses": sorted(background_houses),
            "tertiary_house": tertiary_house or None,
            "convergence_score": round(float(arc.get("convergence_score", 0.0) or 0.0), 3),
            "beat_houses": sorted(beat_houses),
            "primary_plot_houses": sorted(primary_plot_houses),
            "secondary_plot_houses": sorted(secondary_plot_houses),
            "scenario_families": len(ranked),
            "primary_scenario_houses": sorted(primary_provenance),
            "secondary_scenario_houses": sorted(secondary_provenance),
            "tertiary_scenario_houses": sorted(tertiary_provenance),
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
