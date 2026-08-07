from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SIGN_RULERS: dict[str, tuple[str, ...]] = {
    "Aries": ("Mars",),
    "Taurus": ("Venus",),
    "Gemini": ("Mercury",),
    "Cancer": ("Moon",),
    "Leo": ("Sun",),
    "Virgo": ("Mercury",),
    "Libra": ("Venus",),
    "Scorpio": ("Pluto", "Mars"),
    "Sagittarius": ("Jupiter",),
    "Capricorn": ("Saturn",),
    "Aquarius": ("Uranus", "Saturn"),
    "Pisces": ("Neptune", "Jupiter"),
}

# Event class is deliberately normalized rather than multiplied by the raw
# astronomical importance. This prevents an eclipse from being counted several
# times simply because the same event already receives a high base importance.
EVENT_CLASS_SCORE: dict[str, float] = {
    "eclipse": 1.00,
    "lunation": 0.82,
    "station": 0.80,
    "aspect": 0.60,
    "ingress": 0.45,
}

FOCUS_HOUSES: dict[str, frozenset[int]] = {
    "General overview": frozenset(range(1, 13)),
    "Love and relationships": frozenset({5, 7, 8}),
    "Career and work": frozenset({3, 6, 9, 10, 11}),
    "Money and security": frozenset({2, 8}),
    "Home and family": frozenset({2, 4, 8, 10}),
    "Personal growth": frozenset({1, 3, 5, 9, 12}),
    "General year ahead": frozenset(range(1, 13)),
}

FOCUS_DOMAINS: dict[str, frozenset[str]] = {
    "Love and relationships": frozenset({"love"}),
    "Career and work": frozenset({"work", "communication", "expansion", "networks", "identity"}),
    "Money and security": frozenset({"money"}),
    "Home and family": frozenset({"home", "private", "money"}),
    "Personal growth": frozenset({"identity", "private", "love", "expansion"}),
}

LIBRARY_PATH = Path(__file__).with_name("scenario_library.json")


@dataclass(frozen=True)
class ScenarioDefinition:
    key: str
    label: str
    domain: str
    houses: frozenset[int]
    planets: frozenset[str]
    event_kinds: frozenset[str]
    positive_examples: tuple[str, ...]
    friction_examples: tuple[str, ...]
    neutral_examples: tuple[str, ...]
    tension_bias: float = 1.0
    opportunity_bias: float = 1.0
    calibration: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioSupport:
    event_date: str
    title: str
    houses: tuple[int, ...]
    planets: tuple[str, ...]
    polarity: str
    contribution: float


@dataclass(frozen=True)
class ScenarioResult:
    key: str
    label: str
    score: float
    confidence: str
    examples: tuple[str, ...]
    supporting_events: tuple[ScenarioSupport, ...]
    domain: str = "general"
    dominant_polarity: str = "neutral"
    scenario_houses: tuple[int, ...] = ()
    matched_houses: tuple[int, ...] = ()

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "domain": self.domain,
            "score": round(self.score, 2),
            "confidence": self.confidence,
            "dominant_polarity": self.dominant_polarity,
            "scenario_houses": list(self.scenario_houses),
            "matched_houses": list(self.matched_houses),
            "examples": list(self.examples),
            "supporting_events": [
                {
                    "event_date": item.event_date,
                    "title": item.title,
                    "houses": list(item.houses),
                    "planets": list(item.planets),
                    "polarity": item.polarity,
                    "contribution": round(item.contribution, 2),
                }
                for item in self.supporting_events
            ],
        }


def _load_library() -> tuple[ScenarioDefinition, ...]:
    try:
        payload = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
        records = payload.get("scenario_families") or []
    except Exception:
        records = []

    definitions: list[ScenarioDefinition] = []
    for item in records:
        try:
            definitions.append(
                ScenarioDefinition(
                    key=str(item["key"]),
                    label=str(item["label"]),
                    domain=str(item.get("domain", "general")),
                    houses=frozenset(int(value) for value in item.get("houses", [])),
                    planets=frozenset(str(value) for value in item.get("planets", [])),
                    event_kinds=frozenset(str(value) for value in item.get("event_kinds", [])),
                    positive_examples=tuple(str(value) for value in item.get("positive_examples", [])),
                    friction_examples=tuple(str(value) for value in item.get("friction_examples", [])),
                    neutral_examples=tuple(str(value) for value in item.get("neutral_examples", [])),
                    tension_bias=float(item.get("tension_bias", 1.0)),
                    opportunity_bias=float(item.get("opportunity_bias", 1.0)),
                    calibration=tuple(str(value) for value in item.get("calibration", [])),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue

    if definitions:
        return tuple(definitions)

    # Defensive fallback so Luna can still start if the JSON file is omitted
    # during a manual deployment. The full production library lives in JSON.
    return (
        ScenarioDefinition(
            key="travel",
            label="travel or a wider-world opportunity",
            domain="expansion",
            houses=frozenset({9}),
            planets=frozenset({"Jupiter", "Mercury", "Sun", "Moon"}),
            event_kinds=frozenset(EVENT_CLASS_SCORE),
            positive_examples=("a trip, course or international opening",),
            friction_examples=("a travel, legal or study delay",),
            neutral_examples=("travel, study or publishing",),
        ),
        ScenarioDefinition(
            key="relationship_opening",
            label="romantic or relationship opening",
            domain="love",
            houses=frozenset({5, 7, 8, 11}),
            planets=frozenset({"Venus", "Mars", "Moon", "Jupiter"}),
            event_kinds=frozenset(EVENT_CLASS_SCORE),
            positive_examples=("a romantic or relationship opening",),
            friction_examples=("a relationship boundary requiring clearer terms",),
            neutral_examples=("a relationship conversation",),
        ),
    )


SCENARIO_DEFINITIONS: tuple[ScenarioDefinition, ...] = _load_library()


def _value(event: object, key: str, default: object = None) -> object:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _normalized_importance(event: object) -> float:
    importance = float(_value(event, "importance", 0.0) or 0.0)
    # 9.2 is the current engine's eclipse ceiling. Clamp so future changes do
    # not blow up the narrative score.
    return max(0.0, min(1.0, importance / 9.2))


def _configuration_score(event: object) -> float:
    title = str(_value(event, "title", "")).lower()
    planets = set(_value(event, "planets", ()) or ())
    kind = str(_value(event, "kind", ""))
    if kind == "eclipse":
        return 1.0
    if "conjunction" in title and ({"Sun", "Jupiter"} <= planets or "Jupiter" in planets):
        return 0.95
    if "conjunction" in title:
        return 0.80
    if any(token in title for token in ("trine", "opposition", "square")):
        return 0.65
    if "sextile" in title:
        return 0.55
    if kind in {"station", "lunation"}:
        return 0.70
    return 0.35


def event_importance_score(
    event: object,
    sign: str,
    house_weights: Mapping[int, float] | None = None,
) -> float:
    """Return a deterministic 0-10 event score used by the narrative graph.

    The components are additive and normalized: astronomical exactness/base
    importance, event class, house relevance, sign-ruler relevance and special
    configuration. This avoids double-counting high-impact events.
    """
    kind = str(_value(event, "kind", ""))
    planets = set(str(value) for value in (_value(event, "planets", ()) or ()))
    houses = {int(value) for value in (_value(event, "houses", ()) or ())}

    if planets == {"Moon"} and kind not in {"lunation", "eclipse"}:
        return 0.0

    astronomy = _normalized_importance(event)
    event_class = EVENT_CLASS_SCORE.get(kind, 0.30)

    if house_weights and houses:
        maximum = max((float(value) for value in house_weights.values()), default=1.0) or 1.0
        house_relevance = max(
            (float(house_weights.get(house, 0.0)) / maximum for house in houses),
            default=0.0,
        )
    else:
        house_relevance = 0.50 if houses else 0.25

    rulers = set(SIGN_RULERS.get(sign, ()))
    ruler_relevance = 1.0 if planets & rulers else 0.0
    configuration = _configuration_score(event)

    score = 10.0 * (
        0.30 * astronomy
        + 0.24 * event_class
        + 0.16 * house_relevance
        + 0.20 * ruler_relevance
        + 0.10 * configuration
    )

    # Ruler contacts should feel structurally louder, especially when they are
    # exact or attached to a major event. The small multiplier increases
    # prominence without turning ordinary ruler transits into eclipse-level
    # events.
    if ruler_relevance and configuration >= 0.70:
        score *= 1.06

    polarity = str(_value(event, "polarity", "neutral"))
    # Polarity changes urgency slightly, but never overrules event hierarchy.
    if polarity in {"pressure", "turning point"}:
        score *= 1.04
    elif polarity in {"opportunity", "release", "culmination", "new cycle"}:
        score *= 1.02
    return round(max(0.0, min(10.0, score)), 4)


def _polarity_multiplier(polarity: str, definition: ScenarioDefinition) -> float:
    if polarity in {"pressure", "review", "turning point"}:
        return definition.tension_bias
    if polarity in {"opportunity", "release", "new cycle", "culmination"}:
        return definition.opportunity_bias
    return 1.0


def _focus_multiplier(event_houses: set[int], main_focus: str) -> float:
    if main_focus in {"General overview", "General year ahead"}:
        return 1.0
    focus_houses = FOCUS_HOUSES.get(main_focus, FOCUS_HOUSES["General overview"])
    return 1.12 if event_houses & focus_houses else 0.55


def event_scenario_contribution(
    event: object,
    definition: ScenarioDefinition,
    sign: str,
    main_focus: str = "General overview",
    house_weights: Mapping[int, float] | None = None,
    required_houses: frozenset[int] | None = None,
) -> float:
    kind = str(_value(event, "kind", ""))
    planets = set(str(value) for value in (_value(event, "planets", ()) or ()))
    houses = {int(item) for item in (_value(event, "houses", ()) or ())}
    polarity = str(_value(event, "polarity", "neutral"))

    if kind not in definition.event_kinds:
        return 0.0
    if planets == {"Moon"} and kind not in {"lunation", "eclipse"}:
        return 0.0

    # Narrative provenance rule: when a story beat has already been assigned to
    # a house, a scenario may only qualify if BOTH the scenario definition and
    # the supporting astronomical event touch that house. This prevents a
    # nearby House 9 event from supplying visa/travel examples to a House 10
    # eclipse simply because both events sit in the same date cluster.
    if required_houses:
        if not (definition.houses & required_houses):
            return 0.0
        if not (houses & required_houses):
            return 0.0

    house_overlap = houses & definition.houses
    planet_overlap = planets & definition.planets
    if not house_overlap:
        return 0.0
    if not planet_overlap and kind not in {"lunation", "eclipse"}:
        return 0.0

    event_score = event_importance_score(event, sign, house_weights) / 10.0

    # Scenario families that span many houses are useful as secondary pattern
    # recognizers, but they must not outrank a precise one-house interpretation
    # merely because they can match almost anything. Reward coverage and apply a
    # modest breadth penalty. This keeps the scenario database specific without
    # removing cross-house families such as funding or contracts.
    house_coverage = len(house_overlap) / max(1, len(definition.houses))
    house_match = min(1.0, 0.70 + 0.15 * len(house_overlap))
    house_match *= 0.72 + 0.28 * house_coverage
    breadth_factor = max(0.64, 1.0 - 0.08 * max(0, len(definition.houses) - 1))
    if definition.planets:
        planet_match = min(1.0, len(planet_overlap) / max(1, min(2, len(definition.planets))))
    else:
        planet_match = 0.5
    if kind in {"lunation", "eclipse"} and not planet_overlap:
        planet_match = max(planet_match, 0.45)

    rulers = set(SIGN_RULERS.get(sign, ()))
    ruler_match = 1.0 if planets & rulers else 0.0
    class_score = EVENT_CLASS_SCORE.get(kind, 0.30)

    score = 10.0 * (
        0.42 * event_score
        + 0.22 * house_match
        + 0.16 * planet_match
        + 0.10 * ruler_match
        + 0.10 * class_score
    )
    exact_house_factor = 1.0
    if required_houses:
        matched_required = definition.houses & required_houses
        if matched_required:
            # Prefer a precise one-house family over a broad cross-house family
            # when both are supported by the same event.
            exact_house_factor = 1.16 if len(definition.houses) == 1 else 1.04

    return (
        score
        * breadth_factor
        * exact_house_factor
        * _polarity_multiplier(polarity, definition)
        * _focus_multiplier(houses, main_focus)
    )


def _confidence_ratio(ratio: float) -> str:
    if ratio >= 0.82:
        return "strong event family"
    if ratio >= 0.60:
        return "supported event family"
    if ratio >= 0.40:
        return "plausible manifestation"
    return "illustrative possibility"


def _dominant_polarity(supports: Sequence[ScenarioSupport]) -> str:
    totals: dict[str, float] = {"positive": 0.0, "friction": 0.0, "neutral": 0.0}
    for item in supports:
        if item.polarity in {"pressure", "review", "turning point"}:
            totals["friction"] += item.contribution
        elif item.polarity in {"opportunity", "release", "new cycle", "culmination"}:
            totals["positive"] += item.contribution
        else:
            totals["neutral"] += item.contribution
    return max(totals, key=totals.get)


def _examples_for(definition: ScenarioDefinition, polarity: str) -> tuple[str, ...]:
    if polarity == "friction" and definition.friction_examples:
        primary = definition.friction_examples
        secondary = definition.neutral_examples + definition.positive_examples
    elif polarity == "positive" and definition.positive_examples:
        primary = definition.positive_examples
        secondary = definition.neutral_examples + definition.friction_examples
    else:
        primary = definition.neutral_examples or definition.positive_examples or definition.friction_examples
        secondary = definition.positive_examples + definition.friction_examples

    values: list[str] = []
    for value in primary + secondary:
        if value and value not in values:
            values.append(value)
        if len(values) >= 3:
            break
    return tuple(values)


def rank_scenarios(
    events: Sequence[object],
    sign: str,
    main_focus: str = "General overview",
    maximum: int = 8,
    house_weights: Mapping[int, float] | None = None,
    required_houses: Iterable[int] | None = None,
) -> tuple[ScenarioResult, ...]:
    results: list[ScenarioResult] = []
    allowed_domains = FOCUS_DOMAINS.get(main_focus)
    required_house_set = frozenset(int(value) for value in (required_houses or ()))
    context_planets = {
        str(planet)
        for event in events
        for planet in (_value(event, "planets", ()) or ())
    }
    context_polarities = {str(_value(event, "polarity", "neutral")) for event in events}
    pressure_context = bool(context_polarities & {"pressure", "review", "turning point"})
    opportunity_context = bool(context_polarities & {"opportunity", "release", "new cycle", "culmination"})
    for definition in SCENARIO_DEFINITIONS:
        if required_house_set and not (definition.houses & required_house_set):
            continue
        if allowed_domains is not None and definition.domain not in allowed_domains:
            continue
        supports: list[ScenarioSupport] = []
        total = 0.0
        for event in events:
            contribution = event_scenario_contribution(
                event,
                definition,
                sign,
                main_focus,
                house_weights,
                required_house_set or None,
            )
            if contribution <= 0:
                continue
            total += contribution
            supports.append(
                ScenarioSupport(
                    event_date=str(_value(event, "event_date", "")),
                    title=str(_value(event, "title", "Transition")),
                    houses=tuple(int(item) for item in (_value(event, "houses", ()) or ())),
                    planets=tuple(str(item) for item in (_value(event, "planets", ()) or ())),
                    polarity=str(_value(event, "polarity", "neutral")),
                    contribution=contribution,
                )
            )

        if total <= 0:
            continue
        supports.sort(key=lambda item: (-item.contribution, item.event_date, item.title))
        # Independent supporting dates/phenomena increase confidence without
        # changing the actual scenario wording.
        independent_dates = len({item.event_date for item in supports})
        independent_titles = len({item.title for item in supports})
        diversity_bonus = min(3.0, independent_dates * 0.20 + independent_titles * 0.12)
        score = total + diversity_bonus

        # Aspect-conditioned scenario modifier. A planet in a neighbouring house
        # may modify the eclipse/lunation that owns the story beat. The scenario
        # still needs strict provenance in the required house, but the surrounding
        # configuration can decide which manifestation within that house rises.
        if pressure_context and "Uranus" in context_planets and "Uranus" in definition.planets:
            score *= 1.30
        elif pressure_context and "Saturn" in context_planets and "Saturn" in definition.planets:
            score *= 1.08
        if opportunity_context and "Jupiter" in context_planets and "Jupiter" in definition.planets:
            score *= 1.08
        if opportunity_context and "Venus" in context_planets and "Venus" in definition.planets:
            score *= 1.04

        polarity = _dominant_polarity(supports)
        results.append(
            ScenarioResult(
                key=definition.key,
                label=definition.label,
                domain=definition.domain,
                score=score,
                confidence="",
                dominant_polarity=polarity,
                examples=_examples_for(definition, polarity),
                supporting_events=tuple(supports[:5]),
                scenario_houses=tuple(sorted(definition.houses)),
                matched_houses=tuple(sorted({
                    house
                    for support in supports
                    for house in support.houses
                    if house in definition.houses
                })),
            )
        )

    results.sort(key=lambda item: (-item.score, item.label))
    maximum_score = max((item.score for item in results), default=1.0)
    calibrated = [
        ScenarioResult(
            key=item.key,
            label=item.label,
            domain=item.domain,
            score=item.score,
            confidence=_confidence_ratio(item.score / maximum_score),
            dominant_polarity=item.dominant_polarity,
            examples=item.examples,
            supporting_events=item.supporting_events,
            scenario_houses=item.scenario_houses,
            matched_houses=item.matched_houses,
        )
        for item in results
    ]
    return tuple(calibrated[:maximum])


def scenario_by_key(results: Iterable[ScenarioResult], key: str) -> ScenarioResult | None:
    return next((item for item in results if item.key == key), None)
