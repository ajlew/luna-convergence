from __future__ import annotations

"""Luna monthly truth-table and asymmetric strategy engine.

This module is deliberately separate from the narrator and report renderer.
It answers two deterministic questions before Luna writes customer copy:

1. Does a domain materially belong to the convergent monthly hierarchy?
2. Is the best strategic posture ACT or NOT ACT?

NOT ACT is resolved into QUESTION, NEGOTIATE, HOLD or PASS.
The narrator may explain the result, but it must not override it.
"""

from dataclasses import dataclass
from typing import Mapping, Sequence

from scenario_engine import SIGN_RULERS, event_importance_score
from luna_first_principles import (
    CORRESPONDENCE_NOTE,
    LUNA_FIRST_PRINCIPLES_VERSION,
    build_decision_trace,
    capacity_label,
    climate_label,
    evidence_balance,
    validate_first_principles_contract,
)


POSTURES = ("ADVANCE", "QUESTION", "NEGOTIATE", "HOLD", "PASS")

# Direct domain houses. Romance is deliberately strict: H8 can colour intimacy
# and shared stakes, but it cannot by itself make romance a main plot.
DOMAIN_HOUSES = {
    "romance": frozenset({5, 7}),
    "work": frozenset({6, 10}),
    "money": frozenset({2, 8}),
    "home": frozenset({4}),
}

HOUSE_LABELS = {
    1: "identity and direction",
    2: "income and personal money",
    3: "communication and decisions",
    4: "home and private life",
    5: "romance and creativity",
    6: "work and wellbeing",
    7: "relationships and agreements",
    8: "shared resources and obligations",
    9: "travel and wider horizons",
    10: "career and visibility",
    11: "friends, networks and future plans",
    12: "rest, closure and private renewal",
}

ROMANCE_NOT_COPY = {
    1: "Romance has not been given the lead role this month. The main relationship is with the version of you making the next decision. Romance can audition next month.",
    2: "Romance is not running this month's meeting. Venus can wait; the numbers have requested the chair. Maybe next month.",
    3: "Romance has not made the convergent shortlist. Your inbox may have more chemistry than the chart is promising. Maybe next month.",
    4: "Romance is not the main plot. Cupid may need to knock; home has the floor this month. Maybe next month.",
    5: "Romance is technically in the building, but it has not cleared the evidence gate strongly enough to run the month. Enjoy the cameo; maybe next month gets the sequel.",
    6: "Romance has not been given the lead role. The great love affair may be with a calendar that finally behaves. Maybe next month.",
    7: "Relationship evidence is present but not strong enough to outrank the convergent story. No need to draft the vows from the trailer. Maybe next month.",
    8: "Romance is not running the month. Shared stakes and practical terms have taken the table for two. Maybe next month.",
    9: "Romance has not made the main plot. The horizon is doing more flirting than anyone else. Maybe next month.",
    10: "Romance has not been given the lead role. Work has apparently booked the table for two. Maybe next month.",
    11: "Romance is not the main plot. The group chat has the script this month. Cupid can ask for a rewrite next month.",
    12: "Romance is not running the month. The most committed relationship may be with eight hours of sleep. Maybe next month.",
}


@dataclass(frozen=True)
class DomainDecision:
    domain: str
    relevance: str
    relevance_score: float
    hierarchy_role: str
    posture: str
    action_truth: str
    rationale: str
    luna_line: str

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "relevance": self.relevance,
            "relevance_score": round(self.relevance_score, 1),
            "hierarchy_role": self.hierarchy_role,
            "posture": self.posture,
            "action_truth": self.action_truth,
            "rationale": self.rationale,
            "luna_line": self.luna_line,
        }


@dataclass(frozen=True)
class MonthlyDecision:
    action_truth: str
    posture: str
    support_score: float
    friction_score: float
    uncertainty_score: float
    volatility_score: float
    capacity_pressure: float
    rationale: str
    action_plan: tuple[str, ...]
    domain_decisions: tuple[DomainDecision, ...]
    equation: str
    climate_label: str = ""
    capacity_label: str = ""
    evidence_balance: float = 0.0
    first_principles_version: str = LUNA_FIRST_PRINCIPLES_VERSION
    correspondence_note: str = CORRESPONDENCE_NOTE
    first_principles_trace: Mapping[str, object] | None = None

    def to_dict(self) -> dict:
        return {
            "action_truth": self.action_truth,
            "posture": self.posture,
            "support_score": round(self.support_score, 1),
            "friction_score": round(self.friction_score, 1),
            "uncertainty_score": round(self.uncertainty_score, 1),
            "volatility_score": round(self.volatility_score, 1),
            "capacity_pressure": round(self.capacity_pressure, 1),
            "rationale": self.rationale,
            "action_plan": list(self.action_plan),
            "domain_decisions": {item.domain: item.to_dict() for item in self.domain_decisions},
            "equation": self.equation,
            "climate_label": self.climate_label,
            "capacity_label": self.capacity_label,
            "evidence_balance": round(self.evidence_balance, 1),
            "first_principles_version": self.first_principles_version,
            "correspondence_note": self.correspondence_note,
            "first_principles_trace": dict(self.first_principles_trace or {}),
        }


def _value(event: object, key: str, default: object = None) -> object:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _event_houses(event: object) -> set[int]:
    return {int(value) for value in (_value(event, "houses", ()) or ())}


def _event_planets(event: object) -> set[str]:
    return {str(value) for value in (_value(event, "planets", ()) or ())}


def _event_score(event: object, sign: str, house_weights: Mapping[int, float]) -> float:
    return max(0.0, float(event_importance_score(event, sign, house_weights)))


def _narrative_houses(monthly_arc: Mapping[str, object] | None) -> tuple[int, ...]:
    arc = monthly_arc or {}
    values = [
        arc.get("primary_house"),
        arc.get("secondary_house"),
        arc.get("tertiary_house"),
    ]
    return tuple(dict.fromkeys(int(value) for value in values if value not in (None, "")))


def _climate_components(
    sign: str,
    events: Sequence[object],
    inherited_events: Sequence[object],
    monthly_arc: Mapping[str, object] | None,
    house_weights: Mapping[int, float],
) -> dict[str, float]:
    narrative_houses = set(_narrative_houses(monthly_arc))
    rulers = set(SIGN_RULERS.get(sign, ()))

    support = 0.0
    friction = 0.0
    uncertainty = 0.0
    volatility = 0.0
    demand = 0.0
    total_base = 0.0
    pressure_events = 0
    ruler_pressure = 0.0

    tagged_events = [(event, 1.0) for event in events] + [(event, 0.65) for event in inherited_events]
    seen: set[tuple[str, str]] = set()
    for event, carry_factor in tagged_events:
        event_date = str(_value(event, "event_date", ""))
        title = str(_value(event, "title", ""))
        fingerprint = (event_date, title)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)

        base = _event_score(event, sign, house_weights) * carry_factor
        if base <= 0:
            continue
        houses = _event_houses(event)
        planets = _event_planets(event)
        polarity = str(_value(event, "polarity", "neutral")).lower()
        kind = str(_value(event, "kind", "")).lower()
        title_lower = title.lower()

        if houses & narrative_houses:
            base *= 1.15
        if planets & rulers:
            base *= 1.15

        total_base += base

        if polarity == "opportunity":
            support += 1.00 * base
        elif polarity == "release":
            support += 0.65 * base
            uncertainty += 0.12 * base
        elif polarity == "new cycle":
            support += 0.50 * base
            uncertainty += 0.22 * base
        elif polarity == "pressure":
            friction += 1.00 * base
            demand += 0.45 * base
            pressure_events += 1
            if planets & rulers:
                ruler_pressure += 0.35 * base
        elif polarity == "review":
            friction += 0.48 * base
            uncertainty += 0.78 * base
            demand += 0.28 * base
            pressure_events += 1
            if planets & rulers:
                ruler_pressure += 0.25 * base
        elif polarity in {"mixed", "turning point"}:
            support += 0.18 * base
            friction += 0.30 * base
            uncertainty += 0.52 * base
            volatility += 0.28 * base
        elif polarity == "culmination":
            support += 0.20 * base
            friction += 0.20 * base
            uncertainty += 0.22 * base
        else:
            uncertainty += 0.16 * base

        # Actual aspect geometry modifies the polarity score; it does not replace it.
        if " opposition " in f" {title_lower} " or " square " in f" {title_lower} ":
            friction += 0.28 * base
            volatility += 0.18 * base
            demand += 0.12 * base
        elif " trine " in f" {title_lower} " or " sextile " in f" {title_lower} ":
            support += 0.20 * base

        if "Uranus" in planets:
            volatility += 0.26 * base
        if "Neptune" in planets:
            uncertainty += 0.24 * base
        if "Saturn" in planets:
            friction += 0.14 * base
            demand += 0.22 * base
        if "Mars" in planets:
            friction += 0.08 * base
            demand += 0.12 * base
        if "Pluto" in planets:
            volatility += 0.10 * base
        if kind == "eclipse":
            volatility += 0.18 * base
            uncertainty += 0.10 * base

    denominator = max(1.0, support + friction + uncertainty)
    support_pct = 100.0 * support / denominator
    friction_pct = 100.0 * friction / denominator
    uncertainty_pct = 100.0 * uncertainty / denominator
    volatility_pct = min(100.0, 100.0 * volatility / max(1.0, total_base))

    pressure_density = min(1.0, max(0, pressure_events - 1) / 5.0)
    demand_ratio = min(1.0, demand / max(1.0, total_base))
    ruler_ratio = min(1.0, ruler_pressure / max(1.0, total_base))
    capacity_pressure = min(
        100.0,
        40.0 * (friction_pct / 100.0)
        + 26.0 * demand_ratio
        + 18.0 * pressure_density
        + 10.0 * ruler_ratio
        + 6.0 * (volatility_pct / 100.0),
    )

    return {
        "support": support_pct,
        "friction": friction_pct,
        "uncertainty": uncertainty_pct,
        "volatility": volatility_pct,
        "capacity": capacity_pressure,
        "total_base": total_base,
    }


def _choose_posture(components: Mapping[str, float]) -> str:
    support = float(components["support"])
    friction = float(components["friction"])
    uncertainty = float(components["uncertainty"])
    volatility = float(components["volatility"])
    capacity = float(components["capacity"])

    # Truth table: only ADVANCE resolves to ACT. Every other state preserves
    # optionality because the present game is not yet good enough to accept as-is.
    if friction >= 58 and support <= 27 and (capacity >= 50 or volatility >= 32):
        return "PASS"
    if friction - support >= 14 or capacity >= 58:
        return "HOLD"
    if uncertainty >= 18 and abs(support - friction) <= 12:
        return "QUESTION"
    if support - friction >= 12 and capacity < 50:
        return "ADVANCE"
    if friction >= 32 and support >= 28:
        return "NEGOTIATE"
    if support >= 52 and friction <= 35 and capacity < 48:
        return "ADVANCE"
    if uncertainty > max(support, friction) * 0.55:
        return "QUESTION"
    return "HOLD" if friction > support else "NEGOTIATE"


def _posture_plan(posture: str) -> tuple[str, ...]:
    plans = {
        "ADVANCE": (
            "Make the strongest supported move concrete rather than merely discussing it.",
            "Name the timing, cost and owner before adding more exposure.",
            "Commit only to the version that remains supported after the first response arrives.",
        ),
        "QUESTION": (
            "Ask the question that would materially change the decision before you commit.",
            "Verify the number, document, timing or other person's actual capacity.",
            "Keep the move reversible until the missing information becomes usable.",
        ),
        "NEGOTIATE": (
            "Do not accept the current terms as the only game available.",
            "Name the cost, timing, ownership or responsibility that needs to change.",
            "Proceed only if the revised terms improve the risk/reward rather than merely reduce discomfort.",
        ),
        "HOLD": (
            "Protect optionality while the pressure and information are still moving.",
            "Do what is essential, but do not expand exposure simply because a decision is being demanded.",
            "Reassess when the pressure separates or new information changes the balance.",
        ),
        "PASS": (
            "Let the non-essential demand pass through to the keeper; not every ball needs a shot.",
            "Do not chase approval, explanation or commitment when the downside is larger than the likely gain.",
            "Preserve time, money and freedom of movement for the cleaner opening that follows.",
        ),
    }
    return plans[posture]


def _posture_rationale(posture: str, components: Mapping[str, float], narrative_houses: Sequence[int]) -> str:
    support = float(components["support"])
    friction = float(components["friction"])
    uncertainty = float(components["uncertainty"])
    capacity = float(components["capacity"])
    axis = " → ".join(f"H{house}" for house in narrative_houses) or "the dominant convergence"
    phrases = {
        "ADVANCE": "Support outweighs friction cleanly enough for a committed move.",
        "QUESTION": "Missing or unstable information has enough weight to make verification more valuable than commitment.",
        "NEGOTIATE": "Both upside and friction are material, so changing the terms has better asymmetry than accepting them as offered.",
        "HOLD": "Pressure and uncertainty are concentrated enough that preserving optionality has more value than forcing progress.",
        "PASS": "The downside concentration is materially larger than the clean upside, so declining the optional contest preserves the better position.",
    }
    return (
        f"{phrases[posture]} Convergent axis: {axis}. "
        f"Evidence balance — support {support:.0f}, friction {friction:.0f}, uncertainty {uncertainty:.0f}; "
        f"capacity pressure {capacity:.0f}/100."
    )


def _domain_role(domain: str, monthly_arc: Mapping[str, object] | None) -> tuple[str, float]:
    houses = DOMAIN_HOUSES[domain]
    arc = monthly_arc or {}
    primary = int(arc.get("primary_house") or 0)
    secondary = int(arc.get("secondary_house") or 0)
    tertiary = int(arc.get("tertiary_house") or 0)
    if primary in houses:
        return "PRIMARY", 100.0
    if secondary in houses:
        return "SECONDARY", 86.0
    if tertiary in houses:
        return "BRIDGE", 72.0
    return "BACKGROUND", 0.0


def _domain_relevance(
    domain: str,
    sign: str,
    events: Sequence[object],
    monthly_arc: Mapping[str, object] | None,
    house_weights: Mapping[int, float],
) -> tuple[str, float, str]:
    domain_houses = DOMAIN_HOUSES[domain]
    role, hierarchy_score = _domain_role(domain, monthly_arc)
    top_weight = max((float(value) for value in house_weights.values()), default=1.0) or 1.0
    weight_ratio = max((float(house_weights.get(house, 0.0)) for house in domain_houses), default=0.0) / top_weight
    direct_event_support = sum(
        _event_score(event, sign, house_weights)
        for event in events
        if _event_houses(event) & domain_houses
    )
    event_ratio = min(1.0, direct_event_support / 24.0)
    score = 0.52 * hierarchy_score + 28.0 * weight_ratio + 20.0 * event_ratio

    if role in {"PRIMARY", "SECONDARY", "BRIDGE"}:
        relevance = role
    elif score >= 60:
        relevance = "ACTIVE"
    elif score >= 45:
        relevance = "BACKGROUND"
    else:
        relevance = "NOT MATERIAL"

    rationale = (
        f"{domain.title()} relevance {score:.0f}/100: hierarchy {role.lower()}, "
        f"house weight {weight_ratio:.2f}, direct event support {event_ratio:.2f}."
    )
    return relevance, score, rationale


def _domain_posture(
    domain: str,
    overall_posture: str,
    sign: str,
    events: Sequence[object],
    house_weights: Mapping[int, float],
) -> str:
    domain_houses = DOMAIN_HOUSES[domain]
    domain_events = [event for event in events if _event_houses(event) & domain_houses]
    if not domain_events:
        return overall_posture
    components = _climate_components(
        sign,
        domain_events,
        (),
        {"primary_house": next(iter(domain_houses)), "secondary_house": next(iter(domain_houses)), "tertiary_house": None},
        house_weights,
    )
    return _choose_posture(components)


def _domain_luna_line(
    domain: str,
    relevance: str,
    posture: str,
    monthly_arc: Mapping[str, object] | None,
) -> str:
    arc = monthly_arc or {}
    dominant_house = int(arc.get("primary_house") or 1)
    if domain == "romance" and relevance == "NOT MATERIAL":
        return ROMANCE_NOT_COPY.get(dominant_house, ROMANCE_NOT_COPY[1])

    romance_lines = {
        "ADVANCE": "The evidence is strong enough to make a real move; let behaviour, not excitement alone, carry it forward.",
        "QUESTION": "The signal is active, but one missing answer matters more than the first impression. Ask before you attach meaning.",
        "NEGOTIATE": "The connection may be real, but the present terms are not the only terms available. Let reciprocity improve the deal.",
        "HOLD": "There is enough signal to pay attention, but not enough clean advantage to force the next step. Let consistency do the proving.",
        "PASS": "Attraction is not the same as a favourable game. If the effort stays one-sided or costly, let this one pass.",
    }
    generic_lines = {
        "ADVANCE": "This domain has enough support to justify a concrete move, provided the terms stay visible.",
        "QUESTION": "The domain is active, but one missing fact can still change the decision. Verify before committing.",
        "NEGOTIATE": "The domain matters, but the present terms are not the only terms available. Improve the deal before accepting the game.",
        "HOLD": "The domain is active, but preserving optionality is currently more valuable than forcing progress.",
        "PASS": "This domain does not currently offer favourable enough asymmetry to justify extra exposure. Let the optional demand pass.",
    }
    return romance_lines[posture] if domain == "romance" else generic_lines[posture]


def evaluate_monthly_decision(
    *,
    sign: str,
    events: Sequence[object],
    inherited_events: Sequence[object] = (),
    monthly_arc: Mapping[str, object] | None = None,
    house_weights: Mapping[int, float] | None = None,
) -> MonthlyDecision:
    weights = {int(key): float(value) for key, value in (house_weights or {}).items()}
    components = _climate_components(sign, events, inherited_events, monthly_arc, weights)
    posture = _choose_posture(components)
    action_truth = "ACT" if posture == "ADVANCE" else "NOT ACT"
    narrative_houses = _narrative_houses(monthly_arc)

    domains: list[DomainDecision] = []
    for domain in ("romance", "work", "money", "home"):
        relevance, relevance_score, relevance_reason = _domain_relevance(
            domain, sign, events, monthly_arc, weights
        )
        if relevance == "NOT MATERIAL":
            domain_posture = "PASS"
        else:
            domain_posture = _domain_posture(domain, posture, sign, events, weights)
        domain_truth = "ACT" if domain_posture == "ADVANCE" else "NOT ACT"
        domains.append(
            DomainDecision(
                domain=domain,
                relevance=relevance,
                relevance_score=relevance_score,
                hierarchy_role=_domain_role(domain, monthly_arc)[0],
                posture=domain_posture,
                action_truth=domain_truth,
                rationale=relevance_reason,
                luna_line=_domain_luna_line(domain, relevance, domain_posture, monthly_arc),
            )
        )

    return MonthlyDecision(
        action_truth=action_truth,
        posture=posture,
        support_score=components["support"],
        friction_score=components["friction"],
        uncertainty_score=components["uncertainty"],
        volatility_score=components["volatility"],
        capacity_pressure=components["capacity"],
        rationale=_posture_rationale(posture, components, narrative_houses),
        action_plan=_posture_plan(posture),
        domain_decisions=tuple(domains),
        equation=(
            "Nature -> pattern -> convergence -> symbolic meaning -> capacity-aware choice -> "
            "ACT or NOT ACT truth gate -> ADVANCE / QUESTION / NEGOTIATE / HOLD / PASS"
        ),
        climate_label=climate_label(components["support"], components["friction"], components["uncertainty"]),
        capacity_label=capacity_label(components["capacity"]),
        evidence_balance=evidence_balance(components["support"], components["friction"]),
        first_principles_version=LUNA_FIRST_PRINCIPLES_VERSION,
        correspondence_note=CORRESPONDENCE_NOTE,
        first_principles_trace=build_decision_trace(
            narrative_houses=narrative_houses,
            support=components["support"],
            friction=components["friction"],
            uncertainty=components["uncertainty"],
            capacity_pressure=components["capacity"],
            posture=posture,
            action_truth=action_truth,
        ),
    )


def validate_monthly_decision(decision: Mapping[str, object]) -> dict:
    warnings: list[str] = []
    critical: list[str] = []
    posture = str(decision.get("posture", ""))
    truth = str(decision.get("action_truth", ""))
    if posture not in POSTURES:
        critical.append("Unknown strategic posture")
    expected_truth = "ACT" if posture == "ADVANCE" else "NOT ACT"
    if truth != expected_truth:
        critical.append("ACT/NOT ACT truth gate disagrees with posture")

    domains = dict(decision.get("domain_decisions") or {})
    romance = dict(domains.get("romance") or {})
    if romance.get("relevance") == "NOT MATERIAL" and romance.get("posture") != "PASS":
        critical.append("Romance marked NOT MATERIAL must not be promoted into action")
    if romance.get("relevance") == "NOT MATERIAL" and "Maybe next month" not in str(romance.get("luna_line", "")):
        warnings.append("Romance NOT state is missing the light Luna close")

    principle_qa = validate_first_principles_contract(decision)
    critical.extend(str(item) for item in principle_qa.get("critical", ()))
    warnings.extend(str(item) for item in principle_qa.get("warnings", ()))

    return {
        "status": "fail" if critical else ("warning" if warnings else "pass"),
        "critical": critical,
        "warnings": warnings,
        "first_principles": principle_qa,
    }
