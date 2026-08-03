from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
import math
import re
from typing import Iterable, Mapping, Sequence

from scenario_engine import (
    FOCUS_HOUSES,
    SCENARIO_DEFINITIONS,
    SIGN_RULERS,
    ScenarioResult,
    rank_scenarios,
)


FORMULA_VERSION = "2.9.7"

TRIGGER_FACTOR: dict[str, float] = {
    "eclipse": 1.65,
    "lunation": 1.42,
    "station": 1.34,
    "aspect": 1.00,
    "ingress": 0.92,
}

POLARITY_FACTOR: dict[str, float] = {
    "turning point": 1.18,
    "pressure": 1.10,
    "review": 1.08,
    "release": 1.10,
    "opportunity": 1.06,
    "new cycle": 1.08,
    "culmination": 1.10,
    "mixed": 1.02,
    "neutral": 1.00,
}

ASPECT_ORB_LIMITS: dict[str, float] = {
    "conjunction": 8.0,
    "opposition": 8.0,
    "trine": 6.0,
    "square": 6.0,
    "sextile": 4.0,
}

SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

SIGN_META: dict[str, dict[str, str]] = {
    "Aries": {"element": "fire", "modality": "cardinal"},
    "Taurus": {"element": "earth", "modality": "fixed"},
    "Gemini": {"element": "air", "modality": "mutable"},
    "Cancer": {"element": "water", "modality": "cardinal"},
    "Leo": {"element": "fire", "modality": "fixed"},
    "Virgo": {"element": "earth", "modality": "mutable"},
    "Libra": {"element": "air", "modality": "cardinal"},
    "Scorpio": {"element": "water", "modality": "fixed"},
    "Sagittarius": {"element": "fire", "modality": "mutable"},
    "Capricorn": {"element": "earth", "modality": "cardinal"},
    "Aquarius": {"element": "air", "modality": "fixed"},
    "Pisces": {"element": "water", "modality": "mutable"},
}

HOUSE_FALLBACK_SCENARIOS: dict[int, tuple[str, str]] = {
    1: ("identity_direction", "identity, confidence or personal direction"),
    2: ("financial_shock", "money, value or security decision"),
    3: ("paperwork_verification", "communication, documents or decisions"),
    4: ("property_home", "home, property or family decision"),
    5: ("creative_development", "creative, romantic or entrepreneurial development"),
    6: ("routine_wellbeing", "workload, routine or wellbeing adjustment"),
    7: ("contracts_agreements", "relationship, client or formal agreement"),
    8: ("shared_trust", "trust, intimacy or shared-resource decision"),
    9: ("travel", "travel, study, publishing or wider-world opportunity"),
    10: ("career_interview", "interview, offer or professional visibility"),
    11: ("community_future", "friends, audience or future-plan development"),
    12: ("private_closure", "rest, closure or private preparation"),
}


@dataclass(frozen=True)
class EvidenceScore:
    trigger: float
    exactness: float
    phase: float
    house_relevance: float
    ruler_involvement: float
    independent_support: float
    duration: float
    focus: float
    polarity: float
    total: float

    def to_dict(self) -> dict[str, float]:
        return {
            "trigger": round(self.trigger, 4),
            "exactness": round(self.exactness, 4),
            "phase": round(self.phase, 4),
            "house_relevance": round(self.house_relevance, 4),
            "ruler_involvement": round(self.ruler_involvement, 4),
            "independent_support": round(self.independent_support, 4),
            "duration": round(self.duration, 4),
            "focus": round(self.focus, 4),
            "polarity": round(self.polarity, 4),
            "total": round(self.total, 4),
        }


@dataclass(frozen=True)
class StoryContext:
    opening_scenario_key: str = ""
    opening_scenario_label: str = ""
    complication_scenario_key: str = ""
    complication_scenario_label: str = ""
    relationship_scenario_key: str = ""
    relationship_scenario_label: str = ""
    climax_scenario_key: str = ""
    climax_scenario_label: str = ""
    opening_house: int = 1
    complication_house: int = 1
    relationship_house: int = 7
    climax_house: int = 1
    opening_evidence: tuple[str, ...] = ()
    complication_evidence: tuple[str, ...] = ()
    relationship_evidence: tuple[str, ...] = ()
    climax_evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "opening_scenario_key": self.opening_scenario_key,
            "opening_scenario_label": self.opening_scenario_label,
            "complication_scenario_key": self.complication_scenario_key,
            "complication_scenario_label": self.complication_scenario_label,
            "relationship_scenario_key": self.relationship_scenario_key,
            "relationship_scenario_label": self.relationship_scenario_label,
            "climax_scenario_key": self.climax_scenario_key,
            "climax_scenario_label": self.climax_scenario_label,
            "opening_house": self.opening_house,
            "complication_house": self.complication_house,
            "relationship_house": self.relationship_house,
            "climax_house": self.climax_house,
            "opening_evidence": list(self.opening_evidence),
            "complication_evidence": list(self.complication_evidence),
            "relationship_evidence": list(self.relationship_evidence),
            "climax_evidence": list(self.climax_evidence),
        }


def _value(event: object, key: str, default: object = None) -> object:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _event_date(event: object) -> date | None:
    value = _value(event, "event_date")
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None
    return None


def _aspect_name(event: object) -> str:
    value = str(_value(event, "aspect_name", "") or "").strip().lower()
    if value:
        return value
    title = str(_value(event, "title", "") or "").lower()
    for name in ASPECT_ORB_LIMITS:
        if f" {name} " in f" {title} ":
            return name
    return ""


def _orb(event: object) -> float | None:
    value = _value(event, "orb")
    if value is not None:
        try:
            return abs(float(value))
        except (TypeError, ValueError):
            return None
    detail = str(_value(event, "detail", "") or "")
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*°", detail)
    return float(match.group(1)) if match else None


def _phase_factor(event: object) -> float:
    phase = str(_value(event, "applying_state", "") or "").casefold()
    if phase == "applying":
        return 1.06
    if phase == "exact":
        return 1.10
    if phase == "separating":
        return 0.92
    # Events are recorded at their strongest detected date, so the unknown
    # state remains close to exact without pretending it was measured.
    return 1.00


def _exactness_factor(event: object) -> float:
    kind = str(_value(event, "kind", "") or "")
    if kind != "aspect":
        return 1.00
    orb = _orb(event)
    aspect = _aspect_name(event)
    if orb is None:
        return 0.92
    limit = ASPECT_ORB_LIMITS.get(aspect, 6.0)
    closeness = max(0.0, min(1.0, 1.0 - orb / max(limit, 0.1)))
    return 0.72 + 0.38 * closeness


def _house_rulers(sign: str, houses: Iterable[int]) -> set[str]:
    try:
        native_index = SIGNS.index(sign)
    except ValueError:
        return set()
    rulers: set[str] = set()
    for house in houses:
        try:
            house_index = (native_index + int(house) - 1) % 12
        except (TypeError, ValueError):
            continue
        rulers.update(SIGN_RULERS.get(SIGNS[house_index], ()))
    return rulers


def event_evidence_score(
    event: object,
    sign: str,
    main_focus: str = "General overview",
    *,
    support_count: int = 1,
    carryover: bool = False,
) -> EvidenceScore:
    """Universal Luna convergence score.

    The factors are symbolic relevance weights, not measured probabilities.
    Every sign and month uses the same formula; only the sky state, houses,
    rulers, focus and supporting evidence change.
    """

    kind = str(_value(event, "kind", "") or "")
    importance = max(0.1, float(_value(event, "importance", 0.0) or 0.0))
    planets = {str(item) for item in (_value(event, "planets", ()) or ())}
    houses = {int(item) for item in (_value(event, "houses", ()) or ())}
    polarity_name = str(_value(event, "polarity", "neutral") or "neutral")

    trigger = TRIGGER_FACTOR.get(kind, 0.78) * (0.72 + min(0.68, importance / 16.0))
    exactness = _exactness_factor(event)
    phase = _phase_factor(event)

    # House relevance is highest when the event is specific and activates a
    # selected customer focus. Multiple houses add context, not unlimited score.
    house_relevance = 1.0 + min(0.24, max(0, len(houses) - 1) * 0.08)
    focus_houses = FOCUS_HOUSES.get(main_focus, FOCUS_HOUSES["General overview"])
    focus = 1.10 if houses & set(focus_houses) else 0.94

    native_rulers = set(SIGN_RULERS.get(sign, ()))
    activated_rulers = _house_rulers(sign, houses)
    ruler_involvement = 1.0
    if planets & native_rulers:
        ruler_involvement += 0.16
    if planets & activated_rulers:
        ruler_involvement += 0.10

    independent_support = 1.0 + min(0.24, math.log2(max(1, support_count)) * 0.08)
    duration = 1.0
    if kind in {"eclipse", "station"}:
        duration += 0.10
    if carryover:
        duration += 0.08

    polarity = POLARITY_FACTOR.get(polarity_name, 1.0)
    total = (
        trigger
        * exactness
        * phase
        * house_relevance
        * ruler_involvement
        * independent_support
        * duration
        * focus
        * polarity
    )
    return EvidenceScore(
        trigger=trigger,
        exactness=exactness,
        phase=phase,
        house_relevance=house_relevance,
        ruler_involvement=ruler_involvement,
        independent_support=independent_support,
        duration=duration,
        focus=focus,
        polarity=polarity,
        total=total,
    )


def cluster_score(
    events: Sequence[object],
    sign: str,
    main_focus: str = "General overview",
    *,
    carryover: bool = False,
) -> float:
    meaningful = [item for item in events if _value(item, "houses", ())]
    if not meaningful:
        return 0.0
    support_count = len({str(_value(item, "title", "")) for item in meaningful})
    raw = sum(
        event_evidence_score(
            item,
            sign,
            main_focus,
            support_count=support_count,
            carryover=carryover,
        ).total
        for item in meaningful
    )
    kind_diversity = len({str(_value(item, "kind", "")) for item in meaningful})
    house_diversity = len({int(house) for item in meaningful for house in (_value(item, "houses", ()) or ())})
    return raw * (1.0 + min(0.18, kind_diversity * 0.035 + house_diversity * 0.02))


def rank_house_path(
    sign: str,
    start: date,
    end: date,
    early_events: Sequence[object],
    late_events: Sequence[object],
    main_focus: str = "General overview",
) -> tuple[int, int, dict[str, object]]:
    """Select the source and destination houses with one universal rule.

    Event strength matters, but a Monthly story also needs continuity. The
    Sun's monthly ingress supplies a universal source-to-destination spine;
    eclipses, stations and other clusters can become complications or
    resolutions without automatically replacing that spine.
    """

    def unique(events: Sequence[object]) -> list[object]:
        selected: list[object] = []
        seen: set[tuple[str, str]] = set()
        for event in events:
            d = _event_date(event)
            fingerprint = (d.isoformat() if d else "", str(_value(event, "title", "")))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            selected.append(event)
        return selected

    early_unique = unique(early_events)
    late_unique = unique(late_events)

    def scores(events: Sequence[object], carryover: bool = False) -> tuple[Counter[int], dict[int, set[str]], dict[int, set[str]]]:
        result: Counter[int] = Counter()
        titles_by_house: dict[int, set[str]] = defaultdict(set)
        kinds_by_house: dict[int, set[str]] = defaultdict(set)
        support_count = len({str(_value(item, "title", "")) for item in events})
        for event in events:
            score = event_evidence_score(
                event,
                sign,
                main_focus,
                support_count=support_count,
                carryover=carryover,
            ).total
            event_houses = [int(value) for value in (_value(event, "houses", ()) or ())]
            if not event_houses:
                continue
            share = score / len(event_houses)
            title = str(_value(event, "title", ""))
            kind = str(_value(event, "kind", ""))
            for house in event_houses:
                result[house] += share
                titles_by_house[house].add(title)
                kinds_by_house[house].add(kind)
        for house in list(result):
            # Independent events and mixed trigger types make a house more
            # suitable as a monthly spine than one isolated dramatic event.
            result[house] *= 1.0 + min(0.30, len(titles_by_house[house]) * 0.035 + len(kinds_by_house[house]) * 0.045)
        return result, titles_by_house, kinds_by_house

    early, early_titles, early_kinds = scores(early_unique, carryover=True)
    late, late_titles, late_kinds = scores(late_unique)

    solar_ingresses = [
        event for event in late_unique
        if str(_value(event, "kind", "")) == "ingress"
        and tuple(_value(event, "planets", ()) or ()) == ("Sun",)
        and (_value(event, "houses", ()) or ())
    ]
    solar_destination = int((_value(solar_ingresses[-1], "houses", ()) or (1,))[0]) if solar_ingresses else None
    solar_source = ((solar_destination - 2) % 12) + 1 if solar_destination else None

    early_raw = Counter(early)
    late_raw = Counter(late)

    combined = early + late
    primary = early.most_common(1)[0][0] if early else (combined.most_common(1)[0][0] if combined else 1)

    late_candidates = [item for item in late.most_common() if item[0] != primary]
    if late_candidates:
        secondary = late_candidates[0][0]
    elif late:
        secondary = late.most_common(1)[0][0]
    else:
        combined_candidates = [item for item in combined.most_common() if item[0] != primary]
        secondary = combined_candidates[0][0] if combined_candidates else primary

    audit = {
        "formula_version": FORMULA_VERSION,
        "primary_house": primary,
        "secondary_house": secondary,
        "solar_source_house": solar_source,
        "solar_destination_house": solar_destination,
        "early_house_scores": {str(key): round(value, 3) for key, value in early.most_common()},
        "late_house_scores": {str(key): round(value, 3) for key, value in late.most_common()},
        "raw_early_house_scores": {str(key): round(value, 3) for key, value in early_raw.most_common()},
        "raw_late_house_scores": {str(key): round(value, 3) for key, value in late_raw.most_common()},
        "early_support_counts": {str(key): len(value) for key, value in early_titles.items()},
        "late_support_counts": {str(key): len(value) for key, value in late_titles.items()},
        "early_trigger_diversity": {str(key): len(value) for key, value in early_kinds.items()},
        "late_trigger_diversity": {str(key): len(value) for key, value in late_kinds.items()},
        "period": {"start": start.isoformat(), "end": end.isoformat()},
    }
    return primary, secondary, audit


def _cluster_events(cluster: Mapping[str, object] | None) -> tuple[object, ...]:
    if not cluster:
        return ()
    return tuple(cluster.get("events", ()) or ())


def _dominant_house(cluster: Mapping[str, object] | None, fallback: int) -> int:
    if not cluster:
        return fallback
    houses = [int(value) for value in (cluster.get("houses", ()) or ())]
    return Counter(houses).most_common(1)[0][0] if houses else fallback


_SCENARIO_DEFINITION_BY_KEY = {item.key: item for item in SCENARIO_DEFINITIONS}


def _top_scenario(
    cluster: Mapping[str, object] | None,
    sign: str,
    main_focus: str,
    preferred_house: int,
    *,
    role: str = "",
) -> ScenarioResult | None:
    """Choose the best supported scenario for one narrative role.

    Broad scenario families are useful, but they must not displace a more
    precise house-specific family merely because they contain more eligible
    houses. The same rule applies to every sign and month: evidence strength
    first, then activated-house specificity, then role fit.
    """

    events = _cluster_events(cluster)
    if not events:
        return None
    ranked = rank_scenarios(
        events,
        sign,
        main_focus,
        maximum=len(SCENARIO_DEFINITIONS),
    )
    fallback_key = HOUSE_FALLBACK_SCENARIOS.get(preferred_house, ("", ""))[0]
    candidates: list[tuple[float, ScenarioResult]] = []
    for item in ranked:
        preferred_support = [
            support
            for support in item.supporting_events
            if preferred_house in support.houses
        ]
        if not preferred_support:
            continue
        definition = _SCENARIO_DEFINITION_BY_KEY.get(item.key)
        house_count = max(1, len(definition.houses) if definition else 12)
        preferred_contribution = sum(support.contribution for support in preferred_support)
        total_contribution = max(
            preferred_contribution,
            sum(support.contribution for support in item.supporting_events),
        )
        support_purity = preferred_contribution / total_contribution

        # Narrow families receive a modest specificity advantage. A family
        # dedicated to the activated house should beat a broad umbrella family
        # when both are supported at comparable strength.
        specificity = 1.0 + 0.52 / house_count
        if definition and definition.houses == frozenset({preferred_house}):
            specificity += 0.22
        if item.key == fallback_key:
            specificity += 0.14

        role_fit = 1.0
        if role == "relationship" and item.key in {
            "relationship_opening",
            "shared_trust",
            "contracts_agreements",
        }:
            role_fit = 1.22

        adjusted = item.score * (0.78 + 0.22 * support_purity) * specificity * role_fit
        candidates.append((adjusted, item))

    if not candidates:
        # Do not attach a strong but unrelated scenario to the role. The
        # profile generator will fall back to activated-house language.
        return None
    candidates.sort(key=lambda pair: (-pair[0], pair[1].label))

    # A role labelled as the relationship current must remain a relationship
    # interpretation when the evidence genuinely supports one. This is a
    # universal narrative-role rule, not a sign- or month-specific override.
    if role == "relationship":
        relational = [
            pair
            for pair in candidates
            if pair[1].key in {
                "relationship_opening",
                "shared_trust",
                "contracts_agreements",
            }
        ]
        if relational and relational[0][0] >= candidates[0][0] * 0.55:
            return relational[0][1]
    return candidates[0][1]


def build_story_context(
    sign: str,
    main_focus: str,
    primary_house: int,
    secondary_house: int,
    *,
    opening_cluster: Mapping[str, object] | None,
    complication_cluster: Mapping[str, object] | None,
    relationship_cluster: Mapping[str, object] | None,
    climax_cluster: Mapping[str, object] | None,
) -> StoryContext:
    opening_house = _dominant_house(opening_cluster, primary_house)
    complication_house = _dominant_house(complication_cluster, primary_house)
    relationship_house = _dominant_house(relationship_cluster, 7)
    climax_house = _dominant_house(climax_cluster, secondary_house)

    # Each narrative role is translated from the house actually activated by
    # its own evidence cluster. The source/destination axis organises the
    # month, but it must not overwrite the local meaning of an individual act.
    opening = _top_scenario(opening_cluster, sign, main_focus, opening_house)
    complication = _top_scenario(complication_cluster, sign, main_focus, complication_house)
    relationship = _top_scenario(
        relationship_cluster,
        sign,
        main_focus,
        relationship_house,
        role="relationship",
    )
    climax = _top_scenario(climax_cluster, sign, main_focus, climax_house)

    def evidence(cluster: Mapping[str, object] | None) -> tuple[str, ...]:
        return tuple(
            str(_value(item, "title", ""))
            for item in _cluster_events(cluster)
            if str(_value(item, "title", "")).strip()
        )[:4]

    opening_key, opening_label = (
        (opening.key, opening.label) if opening else HOUSE_FALLBACK_SCENARIOS.get(primary_house, ("", ""))
    )
    complication_key, complication_label = (
        (complication.key, complication.label)
        if complication
        else HOUSE_FALLBACK_SCENARIOS.get(complication_house, ("", ""))
    )
    relationship_key, relationship_label = (
        (relationship.key, relationship.label)
        if relationship
        else HOUSE_FALLBACK_SCENARIOS.get(relationship_house, ("", ""))
    )
    climax_key, climax_label = (
        (climax.key, climax.label) if climax else HOUSE_FALLBACK_SCENARIOS.get(climax_house, ("", ""))
    )

    return StoryContext(
        opening_scenario_key=opening_key,
        opening_scenario_label=opening_label,
        complication_scenario_key=complication_key,
        complication_scenario_label=complication_label,
        relationship_scenario_key=relationship_key,
        relationship_scenario_label=relationship_label,
        climax_scenario_key=climax_key,
        climax_scenario_label=climax_label,
        opening_house=opening_house,
        complication_house=complication_house,
        relationship_house=relationship_house,
        climax_house=climax_house,
        opening_evidence=evidence(opening_cluster),
        complication_evidence=evidence(complication_cluster),
        relationship_evidence=evidence(relationship_cluster),
        climax_evidence=evidence(climax_cluster),
    )


def mapping_audit(
    context: StoryContext,
    primary_house: int,
    secondary_house: int,
) -> tuple[dict[str, object], ...]:
    return (
        {
            "role": "opening",
            "house": context.opening_house or primary_house,
            "scenario_key": context.opening_scenario_key,
            "scenario_label": context.opening_scenario_label,
            "evidence": list(context.opening_evidence),
        },
        {
            "role": "complication",
            "house": context.complication_house or primary_house,
            "scenario_key": context.complication_scenario_key,
            "scenario_label": context.complication_scenario_label,
            "evidence": list(context.complication_evidence),
        },
        {
            "role": "relationship test",
            "house": context.relationship_house,
            "scenario_key": context.relationship_scenario_key,
            "scenario_label": context.relationship_scenario_label,
            "evidence": list(context.relationship_evidence),
        },
        {
            "role": "climax",
            "house": context.climax_house or secondary_house,
            "scenario_key": context.climax_scenario_key,
            "scenario_label": context.climax_scenario_label,
            "evidence": list(context.climax_evidence),
        },
    )
