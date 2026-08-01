from __future__ import annotations

from dataclasses import dataclass
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

TRIGGER_MULTIPLIERS: dict[str, float] = {
    "eclipse": 1.60,
    "lunation": 1.40,
    "station": 1.30,
    "aspect": 1.00,
    "ingress": 0.90,
}

FOCUS_HOUSES: dict[str, frozenset[int]] = {
    "General overview": frozenset(range(1, 13)),
    "Love and relationships": frozenset({5, 7, 8, 11}),
    "Career and work": frozenset({3, 6, 9, 10, 11}),
    "Money and security": frozenset({2, 4, 8, 10, 11}),
    "Home and family": frozenset({2, 4, 8, 10}),
    "Personal growth": frozenset({1, 3, 5, 9, 12}),
    "General year ahead": frozenset(range(1, 13)),
}


@dataclass(frozen=True)
class ScenarioDefinition:
    key: str
    label: str
    houses: frozenset[int]
    planets: frozenset[str]
    event_kinds: frozenset[str]
    examples: tuple[str, ...]
    tension_bias: float = 1.0
    opportunity_bias: float = 1.0


@dataclass(frozen=True)
class ScenarioSupport:
    event_date: str
    title: str
    houses: tuple[int, ...]
    planets: tuple[str, ...]
    contribution: float


@dataclass(frozen=True)
class ScenarioResult:
    key: str
    label: str
    score: float
    confidence: str
    examples: tuple[str, ...]
    supporting_events: tuple[ScenarioSupport, ...]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "score": round(self.score, 2),
            "confidence": self.confidence,
            "examples": list(self.examples),
            "supporting_events": [
                {
                    "event_date": item.event_date,
                    "title": item.title,
                    "houses": list(item.houses),
                    "planets": list(item.planets),
                    "contribution": round(item.contribution, 2),
                }
                for item in self.supporting_events
            ],
        }


SCENARIO_DEFINITIONS: tuple[ScenarioDefinition, ...] = (
    ScenarioDefinition(
        "financial_shock",
        "unexpected cost or disappointing amount",
        frozenset({2, 8}),
        frozenset({"Moon", "Saturn", "Neptune", "Uranus", "Mars", "Mercury"}),
        frozenset({"lunation", "eclipse", "aspect", "station"}),
        (
            "a large or misunderstood bill",
            "a wage freeze or lower-than-expected offer",
            "a shared cost that becomes visible",
        ),
        tension_bias=1.35,
    ),
    ScenarioDefinition(
        "external_money",
        "promised or institutional money",
        frozenset({2, 8, 11}),
        frozenset({"Jupiter", "Venus", "Mercury", "Neptune", "Pluto", "Saturn"}),
        frozenset({"lunation", "station", "aspect", "ingress"}),
        (
            "a grant, investment or financial-aid payment",
            "inheritance or money connected to another person",
            "an insurance, tax or compensation payment",
        ),
        tension_bias=1.10,
        opportunity_bias=1.15,
    ),
    ScenarioDefinition(
        "funding_application",
        "loan, mortgage or formal funding process",
        frozenset({2, 4, 8, 10, 11}),
        frozenset({"Mercury", "Saturn", "Jupiter", "Venus", "Moon"}),
        frozenset({"lunation", "station", "aspect", "eclipse"}),
        (
            "a mortgage or bank-loan application",
            "business finance, venture capital or a line of credit",
            "a formal request for funding or shared resources",
        ),
        tension_bias=1.20,
    ),
    ScenarioDefinition(
        "paperwork_verification",
        "paperwork, verification and revised terms",
        frozenset({3, 6, 8, 9, 10}),
        frozenset({"Mercury", "Saturn", "Jupiter", "Sun"}),
        frozenset({"station", "aspect", "lunation", "ingress"}),
        (
            "forms, supporting documents or repeated corrections",
            "a contract, application or estimate that needs verification",
            "a delayed decision waiting on accurate information",
        ),
        tension_bias=1.20,
    ),
    ScenarioDefinition(
        "publishing_media",
        "writing, publishing or audience response",
        frozenset({3, 5, 9, 10, 11}),
        frozenset({"Mercury", "Jupiter", "Sun", "Venus", "Uranus"}),
        frozenset({"lunation", "station", "aspect", "ingress", "eclipse"}),
        (
            "a manuscript, proposal or creative submission",
            "publisher, agent, audience or media interest",
            "a launch, presentation or broadcast opportunity",
        ),
        opportunity_bias=1.25,
    ),
    ScenarioDefinition(
        "visa_legal_study",
        "visa, legal or higher-education progress",
        frozenset({3, 4, 9, 10}),
        frozenset({"Jupiter", "Mercury", "Saturn", "Sun"}),
        frozenset({"lunation", "station", "aspect", "ingress", "eclipse"}),
        (
            "a visa, residency or passport matter",
            "a legal filing or official approval",
            "a university, course or qualification process",
        ),
        opportunity_bias=1.15,
    ),
    ScenarioDefinition(
        "travel",
        "travel or a wider-world opportunity",
        frozenset({3, 9}),
        frozenset({"Jupiter", "Mercury", "Sun", "Moon", "Uranus", "Venus"}),
        frozenset({"lunation", "station", "aspect", "ingress", "eclipse"}),
        (
            "an overseas or long-distance trip",
            "a spontaneous short journey",
            "an international contact or foreign-market opening",
        ),
        opportunity_bias=1.30,
    ),
    ScenarioDefinition(
        "career_interview",
        "interview, offer or professional visibility",
        frozenset({3, 6, 10, 11}),
        frozenset({"Mercury", "Sun", "Venus", "Jupiter", "Saturn"}),
        frozenset({"station", "aspect", "lunation", "ingress", "eclipse"}),
        (
            "a job interview or salary conversation",
            "a promotion, public result or leadership decision",
            "recognition from a manager, client or decision-maker",
        ),
        opportunity_bias=1.10,
    ),
    ScenarioDefinition(
        "relationship_opening",
        "romantic or relationship opening",
        frozenset({5, 7, 8, 11}),
        frozenset({"Venus", "Mars", "Moon", "Jupiter", "Uranus", "Neptune"}),
        frozenset({"lunation", "aspect", "ingress", "eclipse", "station"}),
        (
            "a first date or flirtation",
            "an introduction through friends or a group",
            "a relationship conversation about the next step",
        ),
        opportunity_bias=1.20,
    ),
    ScenarioDefinition(
        "property_home",
        "property, home or family decision",
        frozenset({2, 3, 4, 8, 10}),
        frozenset({"Moon", "Saturn", "Venus", "Mercury", "Jupiter", "Sun"}),
        frozenset({"lunation", "eclipse", "station", "aspect"}),
        (
            "closing on a house or signing a lease",
            "a move, renovation or family decision",
            "a home-versus-career choice",
        ),
    ),
    ScenarioDefinition(
        "contracts_agreements",
        "contract, lease or formal agreement",
        frozenset({3, 7, 8, 9, 10}),
        frozenset({"Mercury", "Saturn", "Venus", "Jupiter", "Sun"}),
        frozenset({"station", "aspect", "lunation", "ingress"}),
        (
            "a contract, lease or formal agreement",
            "terms negotiated with a client or partner",
            "a signature after delayed information clears",
        ),
        opportunity_bias=1.05,
    ),
)


def _value(event: object, key: str, default: object = None) -> object:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _polarity_multiplier(polarity: str, definition: ScenarioDefinition) -> float:
    if polarity in {"pressure", "review"}:
        return definition.tension_bias
    if polarity in {"opportunity", "release", "new cycle", "culmination"}:
        return definition.opportunity_bias
    return 1.0


def _focus_multiplier(event_houses: set[int], main_focus: str) -> float:
    focus_houses = FOCUS_HOUSES.get(main_focus, FOCUS_HOUSES["General overview"])
    return 1.12 if event_houses & focus_houses else 1.0


def event_scenario_contribution(
    event: object,
    definition: ScenarioDefinition,
    sign: str,
    main_focus: str = "General overview",
) -> float:
    kind = str(_value(event, "kind", ""))
    importance = float(_value(event, "importance", 0.0) or 0.0)
    planets = set(_value(event, "planets", ()) or ())
    houses = {int(item) for item in (_value(event, "houses", ()) or ())}
    polarity = str(_value(event, "polarity", "neutral"))

    if kind not in definition.event_kinds:
        return 0.0
    if planets == {"Moon"} and kind not in {"lunation", "eclipse"}:
        return 0.0

    house_overlap = len(houses & definition.houses)
    planet_overlap = len(planets & definition.planets)
    if house_overlap == 0:
        return 0.0
    if planet_overlap == 0 and kind not in {"lunation", "eclipse"}:
        return 0.0

    trigger = TRIGGER_MULTIPLIERS.get(kind, 0.75)
    strength = max(0.35, min(1.35, importance / 8.0))
    house_match = 1.0 + min(0.55, house_overlap * 0.24)
    planet_match = 1.0 + min(0.45, planet_overlap * 0.18)
    ruler_bonus = 1.0
    if planets & set(SIGN_RULERS.get(sign, ())):
        ruler_bonus = 1.25
        if houses & definition.houses:
            ruler_bonus += 0.05

    return (
        trigger
        * strength
        * house_match
        * planet_match
        * ruler_bonus
        * _polarity_multiplier(polarity, definition)
        * _focus_multiplier(houses, main_focus)
    )


def _confidence_ratio(ratio: float) -> str:
    if ratio >= 0.80:
        return "strong event family"
    if ratio >= 0.55:
        return "supported event family"
    if ratio >= 0.35:
        return "plausible manifestation"
    return "illustrative possibility"


def rank_scenarios(
    events: Sequence[object],
    sign: str,
    main_focus: str = "General overview",
    maximum: int = 8,
) -> tuple[ScenarioResult, ...]:
    results: list[ScenarioResult] = []
    for definition in SCENARIO_DEFINITIONS:
        supports: list[ScenarioSupport] = []
        total = 0.0
        for event in events:
            contribution = event_scenario_contribution(
                event,
                definition,
                sign,
                main_focus,
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
                    contribution=contribution,
                )
            )

        if total <= 0:
            continue
        supports.sort(key=lambda item: (-item.contribution, item.event_date))
        # Independent supporting signals matter more than a single repeated theme.
        diversity_bonus = min(2.0, len({item.title for item in supports}) * 0.22)
        score = total + diversity_bonus
        results.append(
            ScenarioResult(
                key=definition.key,
                label=definition.label,
                score=score,
                confidence="",
                examples=definition.examples,
                supporting_events=tuple(supports[:5]),
            )
        )

    results.sort(key=lambda item: (-item.score, item.label))
    maximum_score = max((item.score for item in results), default=1.0)
    calibrated = [
        ScenarioResult(
            key=item.key,
            label=item.label,
            score=item.score,
            confidence=_confidence_ratio(item.score / maximum_score),
            examples=item.examples,
            supporting_events=item.supporting_events,
        )
        for item in results
    ]
    return tuple(calibrated[:maximum])


def scenario_by_key(results: Iterable[ScenarioResult], key: str) -> ScenarioResult | None:
    return next((item for item in results if item.key == key), None)
