from __future__ import annotations
MONTHLY_VOICE_STANDARD = "Brutalist Oracle v2.1"

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Iterable

from date_display import human_date, human_date_range
from scenario_engine import FOCUS_HOUSES, rank_scenarios
from monthly_strategy_alignment import climate_aware_hook, climate_aware_storyline, strategy_do_dont, strategy_rule
from solar_cycle import solar_gate_label, SOLAR_CYCLE_COMPACT

from luna_editorial_system import (
    GATEKEEPER_LINE,
    VALIDATION_LINE,
    luna_do_dont,
)


NO_QUESTION_VALUES = {
    "",
    "none",
    "none supplied",
    "no question",
    "no optional question",
    "no optional question supplied",
    "not supplied",
    "n/a",
    "na",
}

HOUSE_DISPLAY = {
    1: "Identity & direction",
    2: "Money & security",
    3: "Communication & decisions",
    4: "Home & family",
    5: "Romance & creativity",
    6: "Work & wellbeing",
    7: "Relationships & agreements",
    8: "Trust & shared money",
    9: "Travel & learning",
    10: "Career & reputation",
    11: "Friends & future",
    12: "Rest & inner life",
}

HOUSE_PROSE = {
    1: "how you show up and what you are willing to carry",
    2: "the price, payment or purchase in front of you",
    3: "the message, document or conversation that needs an answer",
    4: "home and the arrangement you live with every day",
    5: "the date, attraction or creative project pulling your attention",
    6: "the roster, workload and ordinary week you actually have to live",
    7: "the person across the table and what each of you is actually promising",
    8: "the money, trust and responsibility you share with someone else",
    9: "the trip, course, application or outside opportunity in front of you",
    10: "the job, role or public responsibility with your name on it",
    11: "the people and plan you are trying to build with",
    12: "what needs privacy, rest or a clean ending",
}

HOUSE_NATURAL = {
    1: "how you are choosing to show up",
    2: "what the choice costs",
    3: "the message or decision that needs an answer",
    4: "what home and private life can actually hold",
    5: "who or what you genuinely want",
    6: "what the ordinary week can sustain",
    7: "what the other person is prepared to carry",
    8: "what you share, owe or trust to someone else",
    9: "the outside opportunity and its real logistics",
    10: "the role, responsibility and result attached to your name",
    11: "who helps turn the next plan into something real",
    12: "what needs rest, privacy or closure",
}


def _plain_customer_astrology(value: object) -> str:
    """Translate internal house-number notation into customer life-area language."""
    text = str(value or "")
    # Prefer removing the technical number when the upstream text already supplies
    # a plain-English gloss: "house 10 - career..." -> "career...".
    for house in range(1, 13):
        text = re.sub(rf"\bhouse\s+{house}\s*[-–—:]\s*", "", text, flags=re.I)
    for house, label in HOUSE_PROSE.items():
        text = re.sub(rf"\bhouse\s+{house}\b", label, text, flags=re.I)
        text = re.sub(rf"\bH{house}\b", label, text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()



HOUSE_SCENARIOS = {
    1: (
        "a personal reinvention",
        "a boundary you are ready to state",
        "a new direction that reflects who you are becoming",
    ),
    2: (
        "a pay or pricing conversation",
        "a purchase or financial limit",
        "a decision about what your time is worth",
    ),
    3: (
        "a message or introduction",
        "an application or interview",
        "a conversation that needs a direct answer",
    ),
    4: (
        "a move or property decision",
        "a family conversation",
        "a private boundary at home",
    ),
    5: (
        "a flirtation or date",
        "a creative launch",
        "an invitation that makes you feel more alive",
    ),
    6: (
        "a workload or schedule change",
        "a wellbeing routine",
        "a practical commitment that needs to be sustainable",
    ),
    7: (
        "a relationship conversation",
        "a client or partnership offer",
        "someone asking for more of your time",
    ),
    8: (
        "an intimacy or trust question",
        "a shared cost, loan or debt",
        "a promise that needs clearer terms",
    ),
    9: (
        "a trip or international connection",
        "a course, application or publication",
        "an opportunity beyond your usual world",
    ),
    10: (
        "a job offer or promotion",
        "a public result",
        "a leadership or reputation decision",
    ),
    11: (
        "a friendship or group invitation",
        "a new audience",
        "a future plan that depends on the right people",
    ),
    12: (
        "a private ending",
        "a recovery period",
        "a need for space before making a decision",
    ),
}

ROMANCE_HOUSES = {5, 7, 8, 11}
VALIDATION_HOUSES = {1, 2, 5, 7, 10, 11}

HOUSE_DO = {
    1: "Choose the version of you that can last.",
    2: "Put a real number on the decision.",
    3: "Ask the direct question.",
    4: "Name the private issue calmly.",
    5: "Let one promising opening become real.",
    6: "Fix the routine before adding more.",
    7: "Make the terms mutual and clear.",
    8: "Put every shared expectation in view.",
    9: "Take one proven idea further.",
    10: "Finish one result others can see.",
    11: "Choose the people who support the future.",
    12: "Pause before turning a feeling into a decision.",
}

HOUSE_DONT = {
    1: "Perform for approval.",
    2: "Confuse attention with value.",
    3: "Write the imaginary sequel.",
    4: "Call avoidance keeping the peace.",
    5: "Mistake excitement for evidence.",
    6: "Turn care into unpaid overtime.",
    7: "Accept hints instead of terms.",
    8: "Let chemistry cancel the fine print.",
    9: "Expand before checking the facts.",
    10: "Chase visibility without a result.",
    11: "Give everyone backstage access.",
    12: "Give fantasy unlimited screen time.",
}

MONTHLY_PAIR_HOOKS = {
    frozenset({5, 9}): "Your spark wants a passport—and proof",
    frozenset({4, 7}): "The elephant in the living room wants a date",
    frozenset({3, 5}): "The message is cute. The follow-through matters more",
    frozenset({7, 10}): "Chemistry is not a career strategy",
    frozenset({2, 4}): "Love is priceless. The household budget is not",
    frozenset({8, 11}): "Not everyone cheering belongs in the inner circle",
    frozenset({2, 12}): "Your coping mechanism has sent another invoice",
    frozenset({1, 3}): "The personal press conference is officially cancelled",
    frozenset({5, 7}): "The slow burn still needs actual fire",
    frozenset({8, 10}): "Keep the receipts - emotional and otherwise",
    frozenset({6, 9}): "The escape plan needs annual leave",
    frozenset({4, 10}): "Success still has to live somewhere",
    frozenset({2, 7}): "Attention is flattering. Effort is evidence",
}

MONTHLY_HOUSE_HOOKS = {
    1: "Your next move has stopped asking permission",
    2: "Your standards just found a price tag",
    3: "The message arrives before the full story",
    4: "The private issue wants daylight",
    5: "The spark arrives before the plan",
    6: "The routine is exposing what actually works",
    7: "Mixed signals are losing their charm",
    8: "The fine print is part of the chemistry",
    9: "A bigger world is flirting with you",
    10: "The spotlight wants an actual result",
    11: "The right people make the future feel possible",
    12: "The answer starts in the quiet",
}

HOUSE_ACTION = {
    1: "Make one decision that reflects who you are becoming, not the approval you hope to receive.",
    2: "Put a clear value, price or limit on the issue before giving it more time or money.",
    3: "Ask the direct question, verify the information and write down the next step.",
    4: "Strengthen the private foundation before demanding more from public life.",
    5: "Express the interest or idea clearly, then let the response provide the evidence.",
    6: "Change one routine or boundary that makes the month easier to sustain.",
    7: "State the terms of the relationship or agreement instead of relying on assumptions.",
    8: "Make every shared cost, expectation and obligation visible.",
    9: "Take one proven idea into a larger territory without outrunning the facts.",
    10: "Finish one result that can be seen, evaluated and credited correctly.",
    11: "Choose the few relationships and communities that genuinely support the future you want.",
    12: "Step back long enough to distinguish intuition from fatigue, fear or fantasy.",
}

FOCUS_TITLES = {
    "General overview": "Your month in balance",
    "Love and relationships": "Love, attraction and mutual effort",
    "Career and work": "Work, visibility and practical direction",
    "Money and security": "Money, obligations and lasting security",
    "Home and family": "Home, family and the private foundation",
    "Personal growth": "Identity, confidence and personal direction",
}


@dataclass(frozen=True)
class MonthlyChapter:
    label: str
    date_range: str
    hook: str
    title: str
    paragraphs: tuple[str, ...]
    action: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class KeyDate:
    date_label: str
    consequence: str
    response: str
    evidence: str


@dataclass(frozen=True)
class MonthlyNarrative:
    sign: str
    label: str
    main_focus: str
    personal_question: str
    hook_headline: str
    convergence_axis: str
    headline: str
    subtitle: str
    central_storyline: str
    luna_says: tuple[str, ...]
    agency_rule: str
    validation_rule: str
    scenario_examples: tuple[str, ...]
    romance_active: str
    romance_quiet: str
    relationship_test: tuple[str, ...]
    decision_truth: str
    strategic_posture: str
    strategic_rationale: str
    portfolio_posture: str
    portfolio_rationale: str
    romance_relevance: str
    romance_title: str
    romance_note: str
    at_glance: tuple[str, ...]
    focus_title: str
    focus_answer: tuple[str, ...]
    chapters: tuple[MonthlyChapter, ...]
    love_story: tuple[str, ...]
    work_story: tuple[str, ...]
    money_story: tuple[str, ...]
    do_line: str
    dont_line: str
    love_hook: str
    work_hook: str
    money_hook: str
    hidden_opportunity: str
    watch_out: str
    action_plan: tuple[str, ...]
    key_dates: tuple[KeyDate, ...]
    snapshot_rows: tuple[tuple[str, str], ...]
    solar_title: str
    solar_paragraphs: tuple[str, ...]
    solar_rows: tuple[tuple[str, str], ...]
    solar_opportunity: str
    solar_risk: str
    solar_action: str
    solar_rule: str
    solar_equation: str
    problem_horizon: dict
    technical_appendix_markdown: str


def normalise_personal_question(value: str | None) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    if text.lower() in NO_QUESTION_VALUES:
        return ""
    return text


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_label(value: str) -> str:
    """Return a Windows-safe customer date such as '1 August 2026'."""
    return human_date(value)


def _date_range(start: str, end: str) -> str:
    return human_date_range(start, end)


def _dominant_house(result: dict, index: int, default: int) -> int:
    items = result.get("dominant_houses") or []
    if len(items) > index:
        try:
            return int(items[index]["house"])
        except (KeyError, TypeError, ValueError):
            pass
    return default


def _events(result: dict) -> list[dict]:
    return sorted(
        list(result.get("major_transitions") or []),
        key=lambda item: item.get("event_date", ""),
    )


def _all_events(result: dict) -> list[dict]:
    return sorted(
        list(result.get("events") or []),
        key=lambda item: item.get("event_date", ""),
    )


def _convergences(result: dict) -> list[dict]:
    return sorted(
        list(result.get("convergences") or []),
        key=lambda item: item.get("start_date", ""),
    )


def _retrogrades(result: dict) -> list[dict]:
    return list(result.get("retrograde_cycles") or [])


def _event_house(event: dict, fallback: int = 1) -> int:
    houses = event.get("houses") or []
    return int(houses[0]) if houses else fallback


def _event_customer_consequence(event: dict) -> str:
    title = str(event.get("title", "A transition"))
    kind = str(event.get("kind", ""))
    house = _event_house(event)
    area = HOUSE_PROSE.get(house, "the active area of life")
    planets = set(event.get("planets") or [])
    polarity = event.get("polarity", "neutral")

    if kind == "eclipse":
        return f"A larger turning point begins around {area}; its consequences may develop for months rather than one day."
    if kind == "lunation":
        if "Full Moon" in title:
            return f"A result, decision or emotional truth becomes harder to ignore around {area}."
        return f"A new chapter begins around {area}, but it needs a practical first step."
    if kind == "ingress":
        if "Venus" in planets:
            return f"Relationships, attraction and value begin to move through {area}."
        if "Mercury" in planets:
            return f"Conversations, information and decisions move into {area}."
        if "Mars" in planets:
            return f"Action and pressure increase around {area}, making delay harder to sustain."
        if "Sun" in planets:
            return f"Visibility and conscious direction move toward {area}."
        if "Jupiter" in planets:
            return f"Opportunity and excess both grow around {area}."
        if "Saturn" in planets:
            return f"Responsibility, proof and structure become more important around {area}."
    if kind == "station":
        planet = next(iter(planets), "A planet")
        return f"{planet} changes direction, bringing a review or decision point to {area}."
    if kind == "aspect":
        if polarity == "opportunity":
            return f"A supportive opening links {area} with another active part of the month."
        if polarity == "pressure":
            return f"Friction or incomplete information makes {area} harder to handle through instinct alone."
        return f"A meaningful connection develops around {area}."
    return f"The month changes emphasis around {area}."


def _event_response(event: dict) -> str:
    house = _event_house(event)
    return HOUSE_ACTION.get(house, "Take one practical step and verify the result before expanding.")


def _chapter_events(result: dict, start_day: int, end_day: int) -> list[dict]:
    """Use meaningful monthly evidence, not every fast lunar movement."""
    candidates: list[dict] = []
    candidates.extend(_events(result))
    for convergence in _convergences(result):
        candidates.extend(convergence.get("events") or [])

    unique: dict[tuple[str, str], dict] = {}
    for event in candidates:
        event_date = _parse_date(event["event_date"])
        if not (start_day <= event_date.day <= end_day):
            continue
        planets = set(event.get("planets") or [])
        if planets == {"Moon"} and event.get("kind") not in {"lunation", "eclipse"}:
            continue
        if float(event.get("importance", 0.0)) < 5.5:
            continue
        key = (event.get("event_date", ""), event.get("title", ""))
        previous = unique.get(key)
        if previous is None or float(event.get("importance", 0.0)) > float(previous.get("importance", 0.0)):
            unique[key] = event
    return sorted(unique.values(), key=lambda item: item.get("event_date", ""))


def _select_chapter_evidence(events: Iterable[dict], maximum: int = 4) -> tuple[str, ...]:
    ranked = sorted(
        events,
        key=lambda item: (-float(item.get("importance", 0.0)), item.get("event_date", "")),
    )
    selected = sorted(ranked[:maximum], key=lambda item: item.get("event_date", ""))
    return tuple(
        f"{_date_label(item['event_date'])}: {item.get('title', 'Transition')}"
        for item in selected
    )



def _natural_house(house: int) -> str:
    return HOUSE_NATURAL.get(house, HOUSE_PROSE.get(house, "the active area of life"))


def _monthly_hook(focus: str, primary_house: int, secondary_house: int) -> str:
    pair = frozenset({primary_house, secondary_house})
    if pair == frozenset({5, 9}):
        return "Your spark wants a passport—and proof"
    return MONTHLY_PAIR_HOOKS.get(pair, MONTHLY_HOUSE_HOOKS[primary_house])


def _chapter_hook(segment: str, main_house: int, second_house: int) -> str:
    pair = frozenset({main_house, second_house})
    if segment == "early":
        if 11 in pair:
            return "The right people make the month feel bigger"
        if 5 in pair:
            return "The invitation is real. The future is not decided"
        if 9 in pair:
            return "The door opens before the itinerary is finished"
        return MONTHLY_HOUSE_HOOKS.get(main_house, "The month opens with a useful clue")
    if segment == "middle":
        if 9 in pair:
            return "Adventure now needs supporting documents"
        if 7 in pair:
            return "The connection now needs clear terms"
        if 8 in pair:
            return "The chemistry has reached the fine print"
        return "The exciting part now needs proof"
    if 4 in pair or 10 in pair:
        return "Success still has to live somewhere"
    if 9 in pair:
        return "The idea is ready for an audience"
    return "The ending decides what deserves another month"


def _house_weight_map(result: dict) -> dict[int, float]:
    values: dict[int, float] = {}
    for item in result.get("dominant_houses") or []:
        try:
            values[int(item.get("house"))] = float(item.get("weight", 0.0))
        except (TypeError, ValueError):
            continue
    return values


def _domain_scenarios(
    result: dict,
    focus: str,
    maximum: int = 4,
    *,
    required_houses: set[int] | None = None,
):
    house_weights = _house_weight_map(result)
    focus_houses = FOCUS_HOUSES.get(focus)
    selected_houses = set(required_houses) if required_houses else None
    if selected_houses is None and focus_houses and house_weights:
        ranked_relevant = [
            house
            for house, _weight in sorted(house_weights.items(), key=lambda item: -item[1])
            if house in focus_houses
        ]
        if ranked_relevant:
            # Fallback only: when the convergent story has not supplied a domain
            # house, use that domain's strongest monthly house.
            selected_houses = {ranked_relevant[0]}
    return rank_scenarios(
        _all_events(result),
        str(result.get("sign", "")),
        focus,
        maximum=maximum,
        house_weights=house_weights,
        required_houses=selected_houses,
    )


DOMAIN_HOOKS = {
    "identity_direction": "A new direction asks to be taken seriously",
    "earned_income": "The number matters because the choice has a real price",
    "communication_contracts": "The conversation changes once the important fact is visible",
    "property_home": "Home decides what the larger plan can hold",
    "romance_creativity": "The spark needs a second move",
    "work_wellbeing": "The week has to carry the promise",
    "partnership_commitment": "Mutual effort turns interest into a real agreement",
    "external_money": "Shared resources need clear ownership",
    "travel": "The wider path moves from possibility to decision",
    "career_interview": "The result matters once other people can see it",
    "networks_audience": "The right people change what can grow",
    "closure_private": "The quiet ending changes what comes next",
    "financial_shock": "The surprise is in the number, not the whole future",
    "funding_application": "The opportunity needs proof before it needs speed",
    "paperwork_verification": "The detail that looks boring may unlock the next move",
    "publishing_media": "The idea gets stronger when it reaches a real audience",
    "visa_legal_study": "The wider plan needs an official path",
    "relationship_opening": "Chemistry opens the door. Follow-through decides what stays",
    "contracts_agreements": "The promise becomes useful when the terms are visible",
}


def _domain_hook(
    result: dict,
    focus: str,
    fallback: str,
    *,
    required_houses: set[int] | None = None,
) -> str:
    ranked = _domain_scenarios(result, focus, maximum=2, required_houses=required_houses)
    if not ranked:
        return fallback
    return DOMAIN_HOOKS.get(ranked[0].key, fallback)


def _narrative_domain_house(primary_house: int, secondary_house: int, allowed: set[int]) -> int | None:
    if primary_house in allowed:
        return primary_house
    if secondary_house in allowed:
        return secondary_house
    return None


def _life_area_hooks(result: dict, primary_house: int, secondary_house: int) -> tuple[str, str, str]:
    love_house = _narrative_domain_house(primary_house, secondary_house, {5, 7})
    work_house = _narrative_domain_house(primary_house, secondary_house, {6, 10})
    money_house = _narrative_domain_house(primary_house, secondary_house, {2, 8})
    return (
        _domain_hook(result, "Love and relationships", "Attention is flattering. Consistency is evidence", required_houses={love_house} if love_house else None),
        _domain_hook(result, "Career and work", "Busy is not the same as visible", required_houses={work_house} if work_house else None),
        _domain_hook(result, "Money and security", "The numbers deserve their own conversation", required_houses={money_house} if money_house else None),
    )


def _scenario_examples(primary_house: int, secondary_house: int) -> tuple[str, ...]:
    values = []
    for house in (primary_house, secondary_house):
        for item in HOUSE_SCENARIOS[house]:
            if item not in values:
                values.append(item)
    return tuple(values[:6])


def _central_storyline(
    result: dict,
    primary_house: int,
    secondary_house: int,
) -> str:
    month = str(result.get("label", "This month")).split()[0]
    pair = frozenset({primary_house, secondary_house})
    if pair == frozenset({5, 9}):
        return (
            f"{month} opens a larger door. The rest of the month decides "
            "what can walk through it."
        )
    return (
        f"{month} brings a person, choice or opportunity closer, then asks "
        "whether it supports the life you are choosing."
    )


def _luna_voice(
    result: dict,
    primary_house: int,
    secondary_house: int,
) -> tuple[str, ...]:
    month = str(result.get("label", "This month")).split()[0]
    pair = frozenset({primary_house, secondary_house})
    key_dates = _key_dates(result)
    first_date = key_dates[0].date_label if key_dates else f"early {month}"
    middle_date = (
        key_dates[len(key_dates) // 2].date_label
        if key_dates
        else f"the middle of {month}"
    )
    final_date = key_dates[-1].date_label if key_dates else f"late {month}"

    if pair == frozenset({5, 9}):
        return (
            f"{month} opens with a larger world knocking at the door. A message, "
            "invitation, flirtation, trip, course, creative launch or publishing "
            "opportunity may make you feel more desired, more curious or more "
            "certain that life is moving again. The opening matters, but it is "
            "not the whole story.",
            f"Around {first_date}, people and possibilities begin to gather. A "
            "friend may introduce someone interesting, an audience may respond to "
            "your work, or an invitation may connect romance with travel, study "
            "or a different social world. Enjoy being noticed. Then watch whether "
            "the interest becomes a plan.",
            f"Near {middle_date}, the month reaches its loudest turning point. "
            "Chemistry, confidence or demand can rise quickly, but a shared cost, "
            "distance, deadline or private responsibility may also appear. This "
            "does not cancel the opportunity. It shows what the opportunity needs "
            "in order to become real.",
            f"By {final_date}, the story moves from possibility to placement. "
            "Career, visibility, home and emotional security ask where you "
            "or opportunity actually fits. A real connection can discuss timing, "
            "money and expectations without losing warmth. What continues has "
            "earned its place; what fades has still given you useful information.",
        )

    scenarios = _scenario_examples(primary_house, secondary_house)
    first_examples = ", ".join(scenarios[:3])
    later_examples = ", ".join(scenarios[3:6])
    return (
        f"{month} opens through {_natural_house(primary_house)}. This may arrive "
        f"as {first_examples}. The first movement shows where your confidence, "
        "desire or practical momentum is returning.",
        f"Around {first_date}, attention gathers around the strongest opening. "
        "Enjoy the response, but notice who follows through and what the next "
        "step actually requires.",
        f"Near {middle_date}, {_natural_house(secondary_house)} enters the story "
        f"through {later_examples}. Timing, cost or responsibility turns a vague "
        "possibility into a decision you can evaluate.",
        f"By {final_date}, the month becomes selective. Keep the person, plan or "
        "opportunity that strengthens the life you want. Let everything else "
        "become information rather than unfinished emotional business.",
    )



def _romance_copy(
    primary_house: int,
    secondary_house: int,
) -> tuple[str, str]:
    houses = {primary_house, secondary_house}
    validation_area = _natural_house(
        primary_house if primary_house in VALIDATION_HOUSES else secondary_house
    )

    if houses & ROMANCE_HOUSES:
        active = (
            "If romance or flirting is active, enjoy the chemistry. Then watch "
            "for clear intention, consistent effort and a believable next step."
        )
    else:
        active = (
            "If someone shows interest, judge the behaviour—not the attention. "
            "Choose what matches your standards and future."
        )

    quiet = (
        "If romance is quiet, validation may arrive through creative work, "
        "friendship, travel or visible recognition. Let it confirm your range, "
        "not make the decision for you."
    )
    return active, quiet

def _chapter_title(events: list[dict], primary_house: int, segment: str) -> str:
    titles = " ".join(str(item.get("title", "")) for item in events)
    houses = {_event_house(item) for item in events}
    if segment == "early":
        if "Venus" in titles or 11 in houses:
            return "Connections open the door"
        if 9 in houses:
            return "The larger plan begins to move"
        return "The month reveals its first priority"
    if segment == "middle":
        if "Eclipse" in titles:
            return "The central turning point arrives"
        if 8 in houses:
            return "Desire and obligation need clearer terms"
        return "The strongest pressure becomes visible"
    if "Eclipse" in titles or 4 in houses or 10 in houses:
        return "Public direction meets the private foundation"
    return "The month asks for consolidation"


def _build_chapter(
    result: dict,
    label: str,
    start_day: int,
    end_day: int,
    segment: str,
    primary_house: int,
    secondary_house: int,
) -> MonthlyChapter:
    events = _chapter_events(result, start_day, end_day)
    evidence = _select_chapter_evidence(events)
    houses = [_event_house(item, primary_house) for item in events]
    main_house = max(set(houses), key=houses.count) if houses else primary_house
    second_house = next((house for house in houses if house != main_house), secondary_house)
    title = _chapter_title(events, primary_house, segment)
    hook = _chapter_hook(segment, main_house, second_house)

    if events:
        first = events[0]
        strongest = max(events, key=lambda item: float(item.get("importance", 0.0)))
        first_story = _event_customer_consequence(first)
        strongest_story = _event_customer_consequence(strongest)
    else:
        first_story = f"Attention stays on {HOUSE_PROSE[main_house]}."
        strongest_story = f"The useful progress comes from linking this with {HOUSE_PROSE[second_house]}."

    if segment == "early":
        paragraphs = (
            f"The month opens through {_natural_house(main_house)}. A message, "
            "introduction or invitation may create lift. In romance, someone may "
            "become more curious or available; elsewhere, a plan, application or "
            "creative idea may finally receive a response.",
            f"{strongest_story} Do not force the ending from the first scene. "
            "Notice what happens after the initial enthusiasm.",
        )
    elif segment == "middle":
        paragraphs = (
            f"This is the strongest stretch for {_natural_house(main_house)}. "
            "Attention, chemistry, visibility or demand can rise. The opportunity "
            "may look larger because it is larger—but it may also reveal a price, "
            "distance or responsibility.",
            f"{strongest_story} Ask one clear question. Specific answers build "
            "trust; vagueness is also an answer.",
        )
    else:
        paragraphs = (
            f"Late in the month, {_natural_house(second_house)} becomes the "
            "reality check. Work, money, timing, home or shared obligations expose "
            "what can continue.",
            f"{first_story} A real connection can survive practical conversation. "
            "A viable opportunity can name the cost and next step.",
        )

    return MonthlyChapter(
        label=label,
        date_range=f"{start_day}-{end_day}",
        hook=hook,
        title=title,
        paragraphs=paragraphs,
        action=HOUSE_ACTION[main_house],
        evidence=evidence,
    )


def _focus_answer(
    result: dict,
    focus: str,
    question: str,
    primary_house: int,
    secondary_house: int,
) -> tuple[str, ...]:
    sign = result.get("sign", "Your sign")
    convergences = _convergences(result)
    strongest = max(convergences, key=lambda item: float(item.get("score", 0.0)), default=None)
    strongest_window = _date_range(strongest["start_date"], strongest["end_date"]) if strongest else "the middle of the month"

    if focus == "Love and relationships":
        paragraphs = [
            f"For {sign}, love is not separate from the larger direction of the month. The strongest emphasis links {HOUSE_PROSE[primary_house]} with {HOUSE_PROSE[secondary_house]}, so attraction may feel exciting precisely because it opens a different future, audience or way of living.",
            f"The most important relationship window is {strongest_window}. This can increase contact, attraction or possibility, but it also asks whether the connection has enough honesty, practical capacity and mutual effort to survive beyond the first emotional high.",
            "The useful standard is behaviour. Trust the person who communicates clearly, respects boundaries and contributes to the practical reality of the connection. Mystery, attention or intensity are not substitutes for shared direction.",
        ]
    elif focus in {"Career and work", "Career or business"}:
        paragraphs = [
            f"Work develops through the interaction between {HOUSE_PROSE[primary_house]} and {HOUSE_PROSE[secondary_house]}. A visible opportunity may be real, but it needs systems, ownership and a result that can be evaluated.",
            f"The strongest window is {strongest_window}. Use it to complete, publish, apply, negotiate or clarify responsibility rather than multiplying unfinished options.",
            "Professional progress is most reliable when the private workload, cost and support structure are visible. Do not confuse attention with achievement.",
        ]
    elif focus == "Money and security":
        paragraphs = [
            f"Money this month is shaped by {HOUSE_PROSE[primary_house]} and {HOUSE_PROSE[secondary_house]}. Opportunity and pressure may arrive together, especially where enthusiasm creates a new cost, obligation or expectation.",
            f"The strongest window is {strongest_window}. Separate income, cash received, debt, shared costs and future promises before deciding what is genuinely affordable.",
            "Security grows through clear ownership and repeatable decisions, not through borrowing capacity, attention or optimistic assumptions.",
        ]
    elif focus == "Home and family":
        paragraphs = [
            f"Home and family are affected by the larger movement between {HOUSE_PROSE[primary_house]} and {HOUSE_PROSE[secondary_house]}. A public or future-facing opportunity may expose what the private foundation now needs.",
            f"The strongest window is {strongest_window}. Use it to clarify responsibilities, property decisions, family expectations or the practical conditions required for a change.",
            "The month works best when expansion does not depend on ignoring the emotional or financial base supporting it.",
        ]
    elif focus == "Personal growth":
        paragraphs = [
            f"Personal growth comes from linking {HOUSE_PROSE[primary_house]} with {HOUSE_PROSE[secondary_house]}. The month is less about becoming a different person and more about making one current desire or ability easier to use consistently.",
            f"The strongest window is {strongest_window}. Choose one experience, conversation or commitment that changes what you can actually do, not only what you imagine.",
            "Growth becomes real when a new identity is supported by repeatable behaviour, better boundaries and evidence from daily life.",
        ]
    else:
        scenarios = _scenario_examples(primary_house, secondary_house)
        paragraphs = [
            f"Luna sees one central story: {_central_storyline(result, primary_house, secondary_house)}",
            f"Around {strongest_window}, this may appear as {', '.join(scenarios[:4])}. "
            "You may receive more attention, interest or encouragement, but you "
            "remain the person who decides what moves forward.",
            "The month rewards evidence over fantasy. Notice who follows through, "
            "what the opportunity costs and whether it supports the life you are choosing.",
        ]

    if question:
        paragraphs.append(
            f"Your question - \"{question}\" - is best answered by watching where words and actions agree. The report cannot guarantee an event, but it can show when the issue is most active and what evidence would make the next decision more trustworthy."
        )
    return tuple(paragraphs)


def _domain_story(
    result: dict,
    focus: str,
    *,
    fallback_first: str,
    fallback_move: str,
    required_houses: set[int] | None = None,
    posture: str = "",
) -> tuple[str, ...]:
    ranked = _domain_scenarios(result, focus, maximum=3, required_houses=required_houses)
    if not ranked:
        return (fallback_first, "No single event family dominates this area.", fallback_move)

    top = ranked[0]
    examples = list(top.examples[:3])
    if examples:
        if len(examples) == 1:
            example_text = examples[0]
        elif len(examples) == 2:
            example_text = f"{examples[0]} or {examples[1]}"
        else:
            example_text = f"{examples[0]}, {examples[1]} or {examples[2]}"
    else:
        example_text = top.label

    supports = list(top.supporting_events[:3])
    evidence_text = "; ".join(
        f"{human_date(item.event_date)} — {item.title}" for item in supports
    )
    polarity_line = (
        "The constructive version becomes more believable when the response is repeatable and the practical terms stay visible."
        if top.dominant_polarity == "positive"
        else "Treat the friction as information about timing, cost, capacity or boundaries rather than as a verdict on the whole month."
        if top.dominant_polarity == "friction"
        else "Use behaviour and practical evidence to decide which version of the scenario is actually developing."
    )
    posture = str(posture or "").upper()
    if posture == "PASS":
        first_line = (
            f"The strongest {focus.lower()} pattern centres on {top.label}. Even if it appears through {example_text}, "
            "the headline alone is not a reason to chase it; the present risk/reward does not justify extra exposure."
        )
    elif posture == "HOLD":
        first_line = (
            f"The strongest {focus.lower()} pattern centres on {top.label}. If it appears through {example_text}, "
            "keep the position reversible while timing, responsibility and capacity are still moving."
        )
    elif posture == "NEGOTIATE":
        first_line = (
            f"The strongest {focus.lower()} pattern centres on {top.label}. If it appears through {example_text}, "
            "the opportunity is not the whole answer; improve the amount, timing, ownership or obligation before agreeing."
        )
    elif posture == "QUESTION":
        first_line = (
            f"The strongest {focus.lower()} pattern centres on {top.label}. If it appears through {example_text}, "
            "verify the missing fact before turning the signal into a commitment."
        )
    else:
        first_line = f"The strongest {focus.lower()} pattern centres on {top.label}. It may show up through {example_text}."

    return (
        first_line,
        f"The supporting evidence concentrates around {evidence_text}." if evidence_text else polarity_line,
        polarity_line if evidence_text else fallback_move,
    )


def _love_story(result: dict, primary_house: int, secondary_house: int) -> tuple[str, ...]:
    decision = dict(result.get("monthly_decision") or {})
    romance = dict((decision.get("domain_decisions") or {}).get("romance") or {})
    relevance = str(romance.get("relevance", ""))
    luna_line = str(romance.get("luna_line", "")).strip()
    if relevance == "NOT MATERIAL" and luna_line:
        return (
            luna_line,
            "Romance remains in the report, but it is not promoted above the convergent monthly hierarchy.",
            "If something interesting appears anyway, treat it as a cameo until the evidence earns a larger role.",
        )

    love_house = _narrative_domain_house(primary_house, secondary_house, {5, 7})
    love_posture = str(romance.get("posture", ""))
    base = _domain_story(
        result,
        "Love and relationships",
        fallback_first="A spark can open the door, but behaviour decides whether it stays open.",
        fallback_move="Judge the connection by mutual effort after the exciting moment.",
        required_houses={love_house} if love_house else None,
        posture=love_posture,
    )
    if luna_line:
        return (luna_line, *base[:2])
    return base


def _work_story(result: dict, primary_house: int, secondary_house: int) -> tuple[str, ...]:
    work_house = _narrative_domain_house(primary_house, secondary_house, {6, 10})
    decision = dict(((result.get("monthly_decision") or {}).get("domain_decisions") or {}).get("work") or {})
    base = _domain_story(
        result,
        "Career and work",
        fallback_first="A professional opening gains value when the result, responsibility and next step are visible.",
        fallback_move="Finish one supported result before opening another direction.",
        required_houses={work_house} if work_house else None,
        posture=str(decision.get("posture", "")),
    )
    line = str(decision.get("luna_line", "")).strip()
    return (f"{base[0]} {line}".strip(), *base[1:]) if line else base


def _money_story(result: dict, primary_house: int, secondary_house: int) -> tuple[str, ...]:
    money_house = _narrative_domain_house(primary_house, secondary_house, {2, 8})
    decision = dict(((result.get("monthly_decision") or {}).get("domain_decisions") or {}).get("money") or {})
    base = _domain_story(
        result,
        "Money and security",
        fallback_first="Money becomes easier to judge when price, ownership and obligations are separated from excitement.",
        fallback_move="Choose from visible numbers and enough room to live, not pressure or fantasy.",
        required_houses={money_house} if money_house else None,
        posture=str(decision.get("posture", "")),
    )
    line = str(decision.get("luna_line", "")).strip()
    return (f"{base[0]} {line}".strip(), *base[1:]) if line else base


def _headline(focus: str, primary_house: int, secondary_house: int) -> tuple[str, str]:
    if focus == "Love and relationships":
        if primary_house == 5 and secondary_house == 9:
            return (
                "Love wants a wider horizon - but the future needs proof",
                "Attraction, creativity and expansion can reinforce one another when mutual effort is visible.",
            )
        if primary_house in {5, 7, 8, 11}:
            return (
                "A connection is asking for a more believable future",
                "The month rewards chemistry that can survive clear terms, practical timing and shared effort.",
            )
        return (
            "Love becomes clearer when the larger direction is honest",
            "Attraction matters, but the decision depends on where the relationship can realistically go.",
        )
    if focus in {"Career and work", "Career or business"}:
        return (
            "Visibility grows when one result becomes undeniable",
            "The month rewards completed work, clear ownership and a professional direction that can be evaluated.",
        )
    if focus == "Money and security":
        return (
            "Opportunity needs a number, a limit and a clear owner",
            "Security grows when excitement is separated from cash, cost and obligation.",
        )
    if focus == "Home and family":
        return (
            "The private foundation decides how far the month can expand",
            "Home, family and emotional security need to support the larger change rather than absorb its hidden cost.",
        )
    if focus == "Personal growth":
        return (
            "A larger life begins with one repeatable decision",
            "Growth becomes real when the new direction changes what you do consistently.",
        )
    return (
        f"{HOUSE_DISPLAY[primary_house]} sets the month's direction",
        f"{HOUSE_DISPLAY[secondary_house]} tests what can become real.",
    )


def _key_dates(result: dict, maximum: int = 7) -> tuple[KeyDate, ...]:
    events = _events(result)
    selected = []
    seen_days = set()
    for event in sorted(
        events,
        key=lambda item: (-float(item.get("importance", 0.0)), item.get("event_date", "")),
    ):
        day = event.get("event_date")
        if not day or day in seen_days:
            continue
        selected.append(event)
        seen_days.add(day)
        if len(selected) >= maximum:
            break
    selected.sort(key=lambda item: item.get("event_date", ""))
    return tuple(
        KeyDate(
            date_label=_date_label(item["event_date"]),
            consequence=_event_customer_consequence(item),
            response=_event_response(item),
            evidence=str(item.get("title", "Transition")),
        )
        for item in selected
    )


def _monthly_arc(result: dict) -> dict:
    return dict(result.get("monthly_arc") or {})


def _arc_beats(arc: dict) -> list[dict]:
    return list(arc.get("beats") or [])


def _arc_beat(arc: dict, role: str) -> dict | None:
    return next((item for item in _arc_beats(arc) if item.get("role") == role), None)


def _arc_date_label(beat: dict | None, fallback: str) -> str:
    if not beat:
        return fallback
    start = str(beat.get("start_date", ""))
    end = str(beat.get("end_date", start))
    if not start:
        return fallback
    return _date_range(start, end)


def _arc_scenario_examples(arc: dict, maximum: int = 6) -> tuple[str, ...]:
    values: list[str] = []
    for scenario in arc.get("ranked_scenarios") or []:
        for example in scenario.get("examples") or []:
            text = str(example).strip()
            if text and text not in values:
                values.append(text)
            if len(values) >= maximum:
                return tuple(values)
    return tuple(values)


def _arc_key_dates(arc: dict, maximum: int = 6) -> tuple[KeyDate, ...]:
    selected: list[KeyDate] = []
    deferred_inciting: list[KeyDate] = []
    for beat in _arc_beats(arc):
        role = beat.get("role")
        if role in {"inherited state", "relationship test"}:
            continue
        start = str(beat.get("start_date", ""))
        end = str(beat.get("end_date", start))
        if not start:
            continue
        item = KeyDate(
            date_label=_date_range(start, end),
            consequence=str(beat.get("summary", "A turning point develops.")),
            response=str(beat.get("response", "Use the new information deliberately.")),
            evidence=str(beat.get("title", "Convergence")),
        )
        if role == "inciting event":
            deferred_inciting.append(item)
        else:
            selected.append(item)

    # Keep the opening out of a dense month, but use it when the arc would
    # otherwise provide fewer than four visible dates.
    if len(selected) < 4:
        selected = deferred_inciting + selected

    return tuple(selected[:maximum])


def _beat_hook(beat: dict | None, fallback: str) -> str:
    if not beat:
        return fallback
    scenarios = " ".join(str(value).lower() for value in (beat.get("scenarios") or []))
    title = str(beat.get("title", ""))
    if "eclipse" in title.lower():
        if "home" in scenarios or "property" in scenarios:
            return "The eclipse brings the private foundation into the decision"
        if "money" in scenarios or "funding" in scenarios or "cost" in scenarios:
            return "The eclipse makes the real price impossible to ignore"
        if "travel" in scenarios or "wider-world" in scenarios or "visa" in scenarios:
            return "The eclipse opens a larger path and asks for a real answer"
        if "romantic" in scenarios or "romance" in scenarios:
            return "The eclipse turns the spark into a consequential choice"
        if "career" in scenarios or "professional" in scenarios:
            return "The eclipse moves the result into public view"
        return "The eclipse changes the terms of the month"
    if "travel" in scenarios or "wider-world" in scenarios:
        return "The wider path moves from possibility to decision"
    if "personal direction" in scenarios or "change of role" in scenarios:
        return "A new direction asks to be taken seriously"
    if "shared" in scenarios or "funding" in scenarios or "cost" in scenarios:
        return "The numbers change the terms"
    if "home" in scenarios or "property" in scenarios:
        return "Home decides what the larger plan can hold"
    if "relationship" in scenarios or "romantic" in scenarios:
        return "The second move tells you more than the first spark"
    if "career" in scenarios or "professional" in scenarios:
        return "The result moves into public view"
    if "workload" in scenarios or "wellbeing" in scenarios:
        return "The week has to carry the promise"
    if "closure" in scenarios or "behind-the-scenes" in scenarios:
        return "The quiet ending changes what comes next"
    return fallback


def _beat_date_range(*beats: dict | None, fallback: str) -> str:
    present = [beat for beat in beats if beat and beat.get("start_date")]
    if not present:
        return fallback
    starts = [str(beat.get("start_date")) for beat in present]
    ends = [str(beat.get("end_date") or beat.get("start_date")) for beat in present]
    return _date_range(min(starts), max(ends))


def _arc_chapters(arc: dict) -> tuple[MonthlyChapter, ...]:
    beats = {item.get("role"): item for item in _arc_beats(arc)}
    opening = tuple(str(item) for item in (arc.get("opening") or ()))
    complication = tuple(str(item) for item in (arc.get("complication") or ()))
    pivot = tuple(str(item) for item in (arc.get("pivot") or ()))
    climax = tuple(str(item) for item in (arc.get("climax") or ()))
    resolution = tuple(str(item) for item in (arc.get("resolution") or ()))

    inherited = beats.get("inherited state")
    inciting = beats.get("inciting event")
    complication_beat = beats.get("complication")
    pivot_beat = beats.get("pivot")
    relationship_beat = beats.get("relationship test")
    climax_beat = beats.get("climax")
    resolution_beat = beats.get("resolution")

    chapters: list[MonthlyChapter] = []
    opening_evidence = tuple((inherited or {}).get("evidence") or ()) + tuple((inciting or {}).get("evidence") or ())
    chapters.append(
        MonthlyChapter(
            label="Act I",
            date_range=_beat_date_range(inherited, inciting, fallback="Opening"),
            hook=_beat_hook(inciting or inherited, "The opening establishes the plot"),
            title=str((inciting or inherited or {}).get("title", "Opening and carryover")),
            paragraphs=opening or (str((inherited or inciting or {}).get("summary", "The month reveals its starting condition.")),),
            action=str((inciting or inherited or {}).get("response", "Identify the first real condition before deciding what it means.")),
            evidence=tuple(dict.fromkeys(opening_evidence)),
        )
    )

    chapters.append(
        MonthlyChapter(
            label="Act II",
            date_range=_beat_date_range(complication_beat, fallback="Mid-month"),
            hook=_beat_hook(complication_beat, "The central condition changes the stakes"),
            title=str((complication_beat or {}).get("title", "The main turning point")),
            paragraphs=complication or (str((complication_beat or {}).get("summary", "The strongest condition becomes visible.")),),
            action=str((complication_beat or {}).get("response", "Make the practical condition visible before expanding the plan.")),
            evidence=tuple(dict.fromkeys(tuple((complication_beat or {}).get("evidence") or ()))),
        )
    )

    act_three_beat = pivot_beat or relationship_beat
    act_three_paragraphs = pivot if pivot_beat else tuple(str(item) for item in (arc.get("relationship_test") or ()))
    if act_three_beat and act_three_paragraphs:
        chapters.append(
            MonthlyChapter(
                label="Act III",
                date_range=_beat_date_range(act_three_beat, fallback="Later in the month"),
                hook=_beat_hook(act_three_beat, "The response reveals what can keep moving"),
                title=str(act_three_beat.get("title", "The response")),
                paragraphs=act_three_paragraphs,
                action=str(act_three_beat.get("response", "Let the next move provide the evidence.")),
                evidence=tuple(dict.fromkeys(tuple(act_three_beat.get("evidence") or ()))),
            )
        )

    closing_evidence = tuple((climax_beat or {}).get("evidence") or ()) + tuple((resolution_beat or {}).get("evidence") or ())
    chapters.append(
        MonthlyChapter(
            label="Act IV" if len(chapters) == 3 else "Act III",
            date_range=_beat_date_range(climax_beat, resolution_beat, fallback="Month-end"),
            hook=_beat_hook(resolution_beat or climax_beat, "The strongest late convergence delivers the answer"),
            title=str((resolution_beat or climax_beat or {}).get("title", "Climax and resolution")),
            paragraphs=climax + resolution,
            action=str((climax_beat or resolution_beat or {}).get("response", "Act on the result that survives both excitement and practical reality.")),
            evidence=tuple(dict.fromkeys(closing_evidence)),
        )
    )

    return tuple(chapters)


def _strength_label(score: float) -> str:
    if score >= 75:
        return f"High concentration ({score:.0f}/100)"
    if score >= 50:
        return f"Medium concentration ({score:.0f}/100)"
    return f"Background concentration ({score:.0f}/100)"


def _retrograde_climate(result: dict) -> str:
    cycles = _retrogrades(result)
    if not cycles:
        return "No major retrograde cycle overlaps the selected month."
    selected = cycles[:3]
    parts = []
    for cycle in selected:
        planet = cycle.get("planet", "Planet")
        houses = cycle.get("houses") or []
        area = HOUSE_DISPLAY.get(int(houses[0]), "an active life area") if houses else "an active life area"
        parts.append(f"{planet} reviews {area.lower()}")
    return "; ".join(parts) + "."


def _technical_appendix(result: dict, order_reference: str) -> str:
    def area_list(values) -> str:
        labels = []
        for value in values or []:
            try:
                label = HOUSE_PROSE[int(value)]
            except (KeyError, TypeError, ValueError):
                continue
            if label not in labels:
                labels.append(label)
        return "; ".join(labels) or "n/a"

    dominant_rows = ["| Rank | Life area | Weight |", "|---:|---|---:|"]
    for rank, item in enumerate((result.get("dominant_houses") or [])[:6], 1):
        house = int(item.get("house", 1))
        dominant_rows.append(
            f"| {rank} | {HOUSE_PROSE[house]} | {float(item.get('weight', 0.0)):.1f} |"
        )

    convergence_rows = ["| Window | Type | Strength | Dominant life areas |", "|---|---|---:|---|"]
    for item in _convergences(result)[:4]:
        houses = sorted({int(h) for event in item.get("events", []) for h in event.get("houses", [])})[:3]
        convergence_rows.append(
            f"| {_date_range(item['start_date'], item['end_date'])} | {item.get('title', 'Convergence')} | {float(item.get('score', 0.0)):.0f}/100 | {area_list(houses)} |"
        )

    event_rows = ["| Date | Evidence | Life areas |", "|---|---|---|"]
    for item in _events(result):
        event_rows.append(
            f"| {_date_label(item['event_date'])} | {item.get('title', 'Transition')} | {area_list(item.get('houses') or [])} |"
        )

    retro_rows = ["| Planet | Retrograde | Direct | Life areas |", "|---|---|---|---|"]
    for item in _retrogrades(result):
        retro_rows.append(
            f"| {item.get('planet', '')} | {_date_label(item['retrograde_start'])} | {_date_label(item['direct_date'])} | {area_list(item.get('houses') or [])} |"
        )

    solar = result.get("solar_convergence") or {}
    activated_house = solar.get("activated_house")
    solar_rows = [
        "| Solar evidence | Calculated value |",
        "|---|---|",
        f"| Tropical Sun | {solar.get('solar_longitude', 'n/a')}° {solar.get('solar_sign', '')} |",
        f"| Solar quarter | {solar.get('solar_quarter', 'n/a')} |",
        f"| Local light | {solar.get('light_direction', 'n/a')} from {solar.get('city', 'timezone estimate')} |",
        f"| Activated life area | {HOUSE_PROSE.get(int(activated_house), solar.get('activated_house_name', 'n/a')) if activated_house not in (None, '') else solar.get('activated_house_name', 'n/a')} |",
        f"| Next solar gate | {solar.get('next_solar_gate', 'n/a')} - {human_date(solar.get('next_gate_date')) if solar.get('next_gate_date') else 'n/a'} |",
        f"| Location basis | {solar.get('location_basis', 'n/a')} |",
    ]

    arc = _monthly_arc(result)
    qa = dict(result.get("monthly_qa") or {})
    decision = dict(result.get("monthly_decision") or {})
    decision_qa = dict(result.get("monthly_decision_qa") or {})
    domain_decisions = dict(decision.get("domain_decisions") or {})
    romance_decision = dict(domain_decisions.get("romance") or {})
    decision_rows = [
        "| Decision evidence | Value |",
        "|---|---|",
        f"| Truth gate | {decision.get('action_truth', 'n/a')} |",
        f"| Strategic posture | {decision.get('posture', 'n/a')} |",
        f"| Portfolio strategy | {decision.get('portfolio_posture', 'n/a')} |",
        f"| Overall climate | {decision.get('climate_label', 'n/a')} |",
        f"| Support share | {float(decision.get('support_score', 0.0)):.1f} |",
        f"| Friction share | {float(decision.get('friction_score', 0.0)):.1f} |",
        f"| Uncertainty share | {float(decision.get('uncertainty_score', 0.0)):.1f} |",
        f"| Support minus friction | {float(decision.get('evidence_balance', 0.0)):+.1f} |",
        f"| Volatility index | {float(decision.get('volatility_score', 0.0)):.1f} |",
        f"| Capacity | {decision.get('capacity_label', 'n/a')} ({float(decision.get('capacity_pressure', 0.0)):.1f}/100) |",
        f"| Romance hierarchy | {romance_decision.get('relevance', 'n/a')} |",
        f"| Romance posture | {romance_decision.get('posture', 'n/a')} |",
        f"| First-principles contract | v{decision.get('first_principles_version', 'n/a')} |",
    ]
    scenario_rows = ["| Rank | Scenario family | Symbolic support | Examples |", "|---:|---|---|---|"]
    for rank, item in enumerate((arc.get("ranked_scenarios") or [])[:8], 1):
        examples = "; ".join(str(value) for value in (item.get("examples") or [])[:2])
        scenario_rows.append(
            f"| {rank} | {item.get('label', '')} | {item.get('confidence', '')} | {examples} |"
        )

    inherited_rows = ["| Carryover date | Evidence | Life areas |", "|---|---|---|"]
    for item in arc.get("inherited_events") or []:
        inherited_rows.append(
            f"| {_date_label(item['event_date'])} | {item.get('title', '')} | {area_list(item.get('houses') or [])} |"
        )

    order_line = f"\n\n**Order reference:** `{order_reference}`" if order_reference else ""
    return "\n".join(
        [
            "# Technical appendix",
            "",
            "This appendix contains the calculation trail supporting the customer narrative. Planetary events remain exact; internal house numbers are translated into the life areas they represent.",
            "",
            "## Narrative selection",
            "",
            f"**Event-led selection:** {_plain_customer_astrology(arc.get('selection_rationale', 'The strongest event clusters determine the public story.'))} ",
            f"**Dates shown in:** {result.get('timezone_name', 'selected local timezone')}",
            f"**Narrative QA:** {qa.get('status', 'not run')}" + (f" — {'; '.join(qa.get('warnings') or [])}" if qa.get('warnings') else ""),
            f"**Decision QA:** {decision_qa.get('status', 'not run')}" + (f" — {'; '.join(decision_qa.get('warnings') or [])}" if decision_qa.get('warnings') else ""),
            "",
            "## Strategic truth gate",
            "",
            *decision_rows,
            "",
            "Support, friction and uncertainty are normalized symbolic evidence shares, not probabilities. Capacity pressure is a separate 0-100 decision-load index.",
            "",
            f"**Decision rationale:** {_plain_customer_astrology(decision.get('rationale', 'n/a'))}",
            "",
            "## Luna first-principles contract",
            "",
            "**Method:** Nature → Pattern → Convergence → Meaning → Choice → Experience → Learning.",
            f"**Interpretive boundary:** {decision.get('correspondence_note', 'Astrological scenarios are symbolic correspondences, not guaranteed literal events.')}",
            "**Authority rule:** the narrator may explain the calculation but may not overrule the calculated evidence or strategic posture.",
            "**Evidence rule:** when Luna states a strong pattern, the count, planets and aspects must sit beside the interpretation rather than being hidden elsewhere.",
            "**Calibration rule:** historical tests remain blind; mismatches are studied as calibration evidence rather than repaired with year/sign hard-codes.",
            "",
            "## Ranked scenario families",
            "",
            *scenario_rows,
            "",
            "## Carryover evidence",
            "",
            *inherited_rows,
            "",
            "The scenario labels are ranked symbolic event families, not measured probabilities or guaranteed events.",
            "",
            "## Solar clock evidence",
            "",
            *solar_rows,
            "",
            "## Monthly background weight",
            "",
            *dominant_rows,
            "",
            "## Convergence windows",
            "",
            *convergence_rows,
            "",
            "## Major transitions",
            "",
            *event_rows,
            "",
            "## Retrograde climate",
            "",
            *retro_rows,
            "",
            "## Method",
            "",
            "Tropical geocentric planetary positions are calculated with Swiss Ephemeris and interpreted using whole-sign houses internally. The customer report translates that structure into ordinary life areas. Strength labels describe concentration in the astrological pattern; they are not probabilities or guarantees of events.",
            order_line,
        ]
    )




# v3.27 — the public chronology must read like one month actually unfolding.
# The decision engine may still score support/friction internally, but the customer
# sees a concrete life-area development rather than the scoring vocabulary.
_TRAJECTORY_OPENING_HOOKS = {
    1: "A personal decision begins to feel harder to postpone",
    2: "A number begins to clarify what is and is not worth it",
    3: "A message or decision starts moving before every fact is in",
    4: "A private matter starts setting the terms",
    5: "A spark becomes easier to test in real life",
    6: "A workable routine begins to prove itself",
    7: "An agreement starts revealing whether the terms are mutual",
    8: "A financial or trust issue becomes easier to define",
    9: "The wider road gets its first piece of proof",
    10: "A visible result begins separating promise from performance",
    11: "A future plan starts revealing who actually belongs in it",
    12: "The quiet begins to show what needs to end or recover",
}

_TRAJECTORY_MIDDLE_HOOKS = {
    1: "The personal reset stops being theoretical",
    2: "The value question becomes impossible to price vaguely",
    3: "The conversation stops being a one-off",
    4: "The private issue stops staying in the background",
    5: "The spark asks for a real response",
    6: "The routine stops being temporary",
    7: "The agreement needs actual terms",
    8: "The real price of the agreement becomes visible",
    9: "The wider road demands a real commitment",
    10: "Visibility starts carrying consequences",
    11: "The future plan needs the right people, not more people",
    12: "The need for closure becomes harder to postpone",
}

_TRAJECTORY_OPENING_BODY = {
    1: "A choice about identity, energy or direction begins to show whether the new version of the plan can hold up outside your head.",
    2: "A pay, pricing, purchase or security question begins to reveal the number that makes the decision real.",
    3: "A message, application, conversation or local decision begins to move. Treat the response as information rather than a complete answer.",
    4: "A home, family or private-life matter begins to show which condition must be settled before the rest of the month can move cleanly.",
    5: "A romantic, creative or pleasure-led opening becomes easier to test. Interest is useful; follow-through is the evidence.",
    6: "A workload, schedule, health routine or practical system begins to show what can actually be repeated without draining you.",
    7: "A partner, client or agreement begins to reveal whether interest and responsibility are genuinely mutual.",
    8: "A shared expense, repayment, trust question or obligation begins to acquire clearer boundaries. The useful part is seeing what can actually be carried.",
    9: "A trip, course, publication, legal matter or international opening gains practical support. One part of the wider possibility begins to look buildable.",
    10: "A role, public result or leadership question begins to separate visible promise from work that can actually be credited and sustained.",
    11: "A friendship, audience, group or future plan begins to show which people add momentum and which merely add noise.",
    12: "A private ending, recovery need or unfinished matter begins to clarify in the quiet. Space is giving you information that activity could hide.",
}

_TRAJECTORY_MIDDLE_BODY = {
    1: "What began as a personal adjustment now asks for a more durable choice about who you are becoming and what you will no longer perform for approval.",
    2: "The money or value question is no longer background detail. Price, cost, worth or security now needs a number or boundary you can act on.",
    3: "The same message, decision or conversation keeps returning because it now needs a clear answer, not another round of interpretation.",
    4: "The home or private-life issue can no longer be managed around the edges. A boundary, responsibility or living arrangement needs a more lasting form.",
    5: "A date, creative project or something you enjoy now needs a response that can survive beyond the initial spark.",
    6: "The workload, roster or routine now needs a more lasting arrangement. Change the system, not merely today's schedule.",
    7: "The relationship or agreement stops being defined by tone and starts being defined by terms, reciprocity and what each person is actually willing to carry.",
    8: "A shared cost, debt or responsibility stops being background detail. Name what is owed and what continuing the arrangement will require.",
    9: "A trip, course, application, publication or overseas plan moves from possibility toward commitment. Check the booking, deadline, paperwork and real cost.",
    10: "A job, title or public responsibility becomes harder to keep hypothetical. Put the result, authority and workload into concrete terms.",
    11: "The future plan becomes more selective. A group, friendship, audience or alliance now has to prove that it supports the direction rather than merely applauding it.",
    12: "Rest, closure or a private emotional process becomes harder to postpone. What needs to end, heal or be released is asking for actual space.",
}

_TRAJECTORY_OPENING_ACTIONS = {
    1: "Make the smallest decision that proves the new direction in practice.",
    2: "Put a real number on the decision before giving it more time or money.",
    3: "Ask the direct question and keep the next step written and specific.",
    4: "Stabilise the private condition before promising more elsewhere.",
    5: "Let the response, not the fantasy, tell you whether the opening is real.",
    6: "Keep what works; do not increase the load until the routine has survived ordinary days.",
    7: "Clarify one term that proves the effort is mutual.",
    8: "Put the workable financial or trust terms in view before goodwill substitutes for clarity.",
    9: "Secure the part that makes the wider opportunity real; keep the rest reversible.",
    10: "Finish the result that can be seen before chasing more visibility.",
    11: "Invest in the people already helping the future take shape.",
    12: "Protect enough quiet to tell recovery from avoidance.",
}

_TRAJECTORY_MIDDLE_ACTIONS = {
    1: "Choose the version of the decision you could still respect after the excitement passes.",
    2: "Set the price, limit or minimum standard now; do not leave it implied.",
    3: "Give the conversation a decision point instead of another sequel.",
    4: "Change the private arrangement that keeps recreating the same problem.",
    5: "Make the interest concrete enough that reality can answer back.",
    6: "Redesign the workload or routine around what can actually be sustained.",
    7: "State the terms clearly enough that both sides can agree or refuse them.",
    8: "Name the obligation before agreeing to extend it.",
    9: "Identify the one practical condition that determines whether you can say yes.",
    10: "Take responsibility for the visible result, but do not accept a title without workable authority.",
    11: "Choose the few people who can actually carry the next stage with you.",
    12: "Give the ending or recovery process a boundary in time and attention.",
}

_TRAJECTORY_SECONDARY_SHORT = {
    1: "how you show up",
    2: "the price and payment",
    3: "the message and decision",
    4: "home and private life",
    5: "the person or project you want",
    6: "the workload and routine",
    7: "the other person and the promise",
    8: "shared money, trust and responsibility",
    9: "the trip, course or outside opportunity",
    10: "the role and visible result",
    11: "the people helping build what comes next",
    12: "what needs rest or closure",
}

_TRAJECTORY_LATE_PAIR_HOOKS = {
    (6, 1): "The cost of the routine becomes personal",
    (8, 3): "What was financial now forces a decision",
    (9, 4): "The wider road reaches your front door",
    (4, 10): "The private foundation starts affecting the public result",
    (10, 4): "The visible result comes home",
    (7, 2): "The relationship terms acquire a price",
    (2, 7): "The money question reaches the relationship",
    (5, 11): "The spark starts changing the future plan",
    (11, 5): "The future plan starts changing what brings you alive",
}

_TRAJECTORY_LATE_HOOKS = {
    1: "The personal choice starts affecting the rest of the board",
    2: "The money question starts reaching beyond money",
    3: "What was a conversation now changes the next move",
    4: "The private issue starts affecting the outside world",
    5: "What began as desire now carries a consequence",
    6: "The routine starts charging a wider price",
    7: "The relationship terms start affecting another part of life",
    8: "The obligation starts forcing movement elsewhere",
    9: "The wider opportunity starts changing the life around it",
    10: "The visible result starts changing the private equation",
    11: "The future plan starts testing another priority",
    12: "What was private starts reaching the rest of life",
}

_TRAJECTORY_LATE_BODY = {
    1: "The useful test now is whether the choice still fits once its effect on another part of life is visible.",
    2: "The decision is no longer only about affordability; it is about what the financial choice now permits or constrains elsewhere.",
    3: "The message or decision has moved beyond words. The consequence now shows whether the information was sufficient to act on.",
    4: "The private arrangement now has an external cost or benefit. Protect the foundation that still supports the rest of the month.",
    5: "Desire, creativity or pleasure now has to coexist with another priority. Keep what is alive without making the rest of life subsidise it.",
    6: "The routine has stopped being a private scheduling issue. Energy, identity or another priority is now showing the real cost of how the system is built.",
    7: "The relationship or agreement is now affecting another practical area. Reciprocity has to survive outside the conversation itself.",
    8: "Money, trust or obligation has become a decision problem. What looked containable now changes what you can say yes to elsewhere.",
    9: "The wider opportunity now asks something of the life you already have. Expansion is only useful if the foundation can carry it.",
    10: "The visible result now has a private consequence. Achievement is useful only if the role, authority and cost still belong together.",
    11: "The future plan reaches ordinary life now. The right people make the next stage more possible; the wrong people only make it more crowded.",
    12: "The private process is now affecting ordinary life. Closure or recovery needs enough room that it stops becoming an invisible tax on everything else.",
}


def _trajectory_action(posture: str) -> str:
    """Legacy fallback used outside the richer chronology."""
    return {
        "ADVANCE": "Use the clean support while it is present, but keep timing and terms visible.",
        "QUESTION": "Enjoy what opens, but verify the missing fact before increasing commitment.",
        "NEGOTIATE": "Keep the essential part, but change the terms before accepting more exposure.",
        "HOLD": "Do what must be done. Keep everything else reversible while the situation is still moving.",
        "PASS": "Let the optional demand pass; protect time, money and freedom of movement.",
    }.get(str(posture).upper(), "Let the evidence determine the next move.")


def _trajectory_public_condition(balance: float) -> str:
    """Only surface a balance note when the evidence is genuinely mixed.

    Strong positive/negative balances are already expressed in the house-specific
    story and action. Repeating a generic score translation across every sign
    would recreate the template feel v3.27 is intended to remove.
    """
    if -10 < balance < 10:
        return "The evidence is mixed enough that timing and terms matter more than speed."
    return ""


def _trajectory_event_role(chapter: MonthlyChapter) -> str:
    text = " ".join([chapter.title, *chapter.evidence]).lower()
    if "eclipse" in text or "new moon" in text:
        return "This is a reset point rather than another ordinary day in the story."
    if "full moon" in text:
        return "This is a culmination point: something that has been developing becomes easier to see in full."
    if "station" in text or "turns direct" in text or "direct station" in text:
        return "The timing changes here: a matter that was stalled, reviewed or uncertain can start behaving differently."
    if "retrograde" in text:
        return "The event asks for review before expansion; old information, terms or assumptions may need another pass."
    return "The event gives the month a concrete checkpoint rather than another general mood."


def _trajectory_house_action(house: int, stage: int, posture: str, secondary_house: int) -> str:
    if stage == 0:
        base = _TRAJECTORY_OPENING_ACTIONS.get(house, HOUSE_ACTION.get(house, _trajectory_action(posture)))
    elif stage == 1:
        base = _TRAJECTORY_MIDDLE_ACTIONS.get(house, HOUSE_ACTION.get(house, _trajectory_action(posture)))
    else:
        secondary = _TRAJECTORY_SECONDARY_SHORT.get(secondary_house, "the area now being affected")
        late = {
            1: f"Keep the decision that still fits who you are becoming, and cut the part now draining {secondary}.",
            2: f"Let the numbers decide what can continue before the cost spreads into {secondary}.",
            3: f"Make the decision the information now requires; do not let ambiguity keep disrupting {secondary}.",
            4: f"Protect the private foundation that {secondary} now depends upon.",
            5: f"Keep the desire that still has evidence behind it; do not make {secondary} pay for the rest.",
            6: f"Drop the routine or obligation that now costs more energy than it returns, especially where it is affecting {secondary}.",
            7: f"Keep the relationship or agreement only on terms that still make sense once {secondary} is included.",
            8: f"Make the decision the financial or trust facts now require before they keep distorting {secondary}.",
            9: f"Protect the foundation the wider opportunity depends upon, especially {secondary}.",
            10: f"Keep the visible responsibility that is genuinely yours; do not let it consume {secondary}.",
            11: f"Keep the plan only if the people involved help carry {secondary}.",
            12: f"Give the private ending or recovery enough space that it stops leaking into {secondary}.",
        }.get(house, _trajectory_action(posture))
        base = late

    # Preserve the strategic posture without returning to generic engine language.
    posture = str(posture).upper()
    if posture == "PASS" and stage < 2:
        return base + " Let the optional part wait."
    if posture == "NEGOTIATE" and stage < 2:
        return base + " Renegotiate before adding exposure."
    if posture == "QUESTION" and stage < 2:
        return base + " Verify the missing fact before enlarging the commitment."
    return base


def _trajectory_window_date_range(trajectory: dict, window: dict, fallback: str) -> str:
    start_raw = str(trajectory.get("period_start") or "")
    if len(start_raw) < 7:
        return fallback
    year_month = start_raw[:7]
    try:
        start_iso = f"{year_month}-{int(window.get('start_day') or 1):02d}"
        end_iso = f"{year_month}-{int(window.get('end_day') or window.get('start_day') or 1):02d}"
        return human_date_range(start_iso, end_iso)
    except Exception:
        return fallback


def _trajectory_aligned_chapters(
    chapters: tuple[MonthlyChapter, ...],
    trajectory: dict,
) -> tuple[MonthlyChapter, ...]:
    """Turn evidence anchors into a sign-specific three-act chronology.

    Astronomy remains untouched. The public layer now has distinct jobs:
      Act I  — opening evidence / first proof
      Act II — reset, commitment or concentration
      Act III — consequence / spillover into another life area

    Internal support/friction scores remain available in the technical evidence,
    but are no longer repeated as customer-facing prose.
    """
    windows = list(trajectory.get("windows") or [])
    if not chapters or not windows:
        return chapters

    if len(chapters) >= 3:
        sources = [chapters[0], chapters[1], chapters[-1]]
    else:
        sources = list(chapters)

    primary_house = int(trajectory.get("primary_house") or 0)
    secondary_house = int(trajectory.get("secondary_house") or 0)
    primary_area = str(trajectory.get("primary_area", "the main area"))
    secondary_area = str(trajectory.get("secondary_area", "the later consequence"))
    trajectory_kind = str(trajectory.get("trajectory", "oscillating"))
    countercurrent = dict(trajectory.get("countercurrent") or {})
    counter_window = str(countercurrent.get("window_label", ""))
    aligned: list[MonthlyChapter] = []

    for index, chapter in enumerate(sources):
        window = windows[min(index, len(windows) - 1)]
        support = float(window.get("support", 0.0))
        friction = float(window.get("friction", 0.0))
        balance = support - friction
        posture = str(window.get("posture", "QUESTION"))
        condition = _trajectory_public_condition(balance)

        if index == 0:
            hook = _TRAJECTORY_OPENING_HOOKS.get(primary_house, "The first useful evidence arrives")
            if trajectory_kind in {"recovery", "easing"} and balance < 0:
                hook = f"{hook} — but the opening still needs room to change"
            paragraphs = [
                _TRAJECTORY_OPENING_BODY.get(
                    primary_house,
                    f"The month first becomes concrete through {primary_area}. Treat the first development as evidence rather than a final verdict.",
                )
            ]
            if condition:
                paragraphs.append(condition)

        elif index == len(sources) - 1:
            hook = _TRAJECTORY_LATE_PAIR_HOOKS.get(
                (primary_house, secondary_house),
                _TRAJECTORY_LATE_HOOKS.get(primary_house, "The earlier story now has a wider consequence"),
            )
            secondary_short = _TRAJECTORY_SECONDARY_SHORT.get(secondary_house, secondary_area)
            if primary_house == 11 and secondary_house == 6:
                paragraphs = [
                    "By late month, the future plan reaches the ordinary week. "
                    "Who has to work more, travel further, reorganise home or carry the practical load?"
                ]
            else:
                paragraphs = [
                    f"By late month, the earlier decision reaches {secondary_short}. "
                    "Judge the plan by the practical consequence it creates there."
                ]
            if condition:
                paragraphs.append(condition)
            if trajectory_kind in {"late_storm", "pressure_builds"}:
                paragraphs.append(
                    _TRAJECTORY_LATE_BODY.get(
                        primary_house,
                        "The original issue now has a wider consequence. Protect only the commitments that still make sense once that cost is visible.",
                    )
                )
            elif trajectory_kind in {"recovery", "easing"}:
                paragraphs.append(
                    "The later conditions give you more room than the opening did. Do not carry an early defensive posture forward after the evidence has changed."
                )
            else:
                paragraphs.append(
                    "Judge the later consequence on its own terms rather than allowing the month's opening mood to make the decision for you."
                )

        else:
            hook = _TRAJECTORY_MIDDLE_HOOKS.get(primary_house, "The main issue becomes concrete")
            if trajectory_kind in {"recovery", "easing"} and balance >= 10:
                hook = f"{hook} — and the conditions begin to improve"
            paragraphs = [
                _TRAJECTORY_MIDDLE_BODY.get(
                    primary_house,
                    f"Mid-month keeps returning attention to {primary_area}, but now the issue needs a more durable decision rather than another temporary response.",
                ),
                _trajectory_event_role(chapter),
            ]
            if condition:
                paragraphs.append(condition)
            if countercurrent and str(window.get("label", "")) == counter_window:
                evidence = "; ".join(str(item) for item in (countercurrent.get("support_evidence") or [])[:3])
                relief = f"At the same time, {countercurrent.get('label', 'another part of life')} provide genuine relief"
                if evidence:
                    relief += f", supported by {evidence}"
                relief += ". Use that relief for perspective; do not make it responsible for solving the main problem."
                paragraphs.append(relief)

        aligned.append(MonthlyChapter(
            label=("Act I" if index == 0 else "Act II" if index == 1 else "Act III"),
            date_range=_trajectory_window_date_range(trajectory, window, chapter.date_range),
            hook=hook,
            title=chapter.title,
            paragraphs=tuple(paragraphs),
            action=_trajectory_house_action(primary_house, index, posture, secondary_house),
            evidence=chapter.evidence,
        ))
    return tuple(aligned)

def _countercurrent_love_story(result: dict, trajectory: dict) -> tuple[str, ...] | None:
    counter = dict(trajectory.get("countercurrent") or {})
    if str(counter.get("domain", "")) != "romance":
        return None
    support = "; ".join(str(item) for item in (counter.get("support_evidence") or [])[:3])
    late = "; ".join(str(item) for item in (counter.get("late_pressure_evidence") or [])[:3])
    first = "Use the lighter window for a date, creative project or something you actually enjoy. Let it give you room to breathe without asking it to solve the main problem."
    second = (f"The relief has real sky support: {support}." if support else "The relief is supported by direct relationship or creative evidence in the sky.")
    third = (f"Late-month pressure changes the terms — {late}. Enjoy the lift, but keep commitments reversible." if late else "Use the relief without asking it to make the month's larger decision for you.")
    return (first, second, third)


def build_monthly_narrative(
    result: dict,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> MonthlyNarrative:
    if result.get("period") != "monthly":
        raise ValueError("Monthly Narrative Engine requires a monthly period result")

    question = normalise_personal_question(personal_question)
    arc = _monthly_arc(result)
    trajectory = dict(result.get("monthly_trajectory") or {})
    monthly_decision = dict(result.get("monthly_decision") or {})
    domain_decisions = dict(monthly_decision.get("domain_decisions") or {})
    romance_decision = dict(domain_decisions.get("romance") or {})

    if arc:
        primary_house = int(arc.get("primary_house", _dominant_house(result, 0, 1)))
        secondary_house = int(arc.get("secondary_house", _dominant_house(result, 1, primary_house)))
        tertiary_raw = arc.get("tertiary_house")
        tertiary_house = int(tertiary_raw) if tertiary_raw not in (None, "") else None
        hook_headline = str(arc.get("headline", _monthly_hook(main_focus, primary_house, secondary_house)))
        convergence_axis = str(
            arc.get(
                "theme_axis",
                f"{HOUSE_DISPLAY[primary_house]} x {HOUSE_DISPLAY[secondary_house]}",
            )
        )
        central_storyline = str(
            arc.get(
                "central_storyline",
                _central_storyline(result, primary_house, secondary_house),
            )
        )
        headline = convergence_axis
        subtitle = central_storyline
        luna_says = tuple(
            str(item)
            for section in ("opening", "complication", "pivot", "climax", "resolution")
            for item in (arc.get(section) or ())
            if str(item).strip()
        )
        scenario_examples = _arc_scenario_examples(arc) or _scenario_examples(
            primary_house,
            secondary_house,
        )
        chapters = _arc_chapters(arc)
        key_dates = _arc_key_dates(arc) or _key_dates(result)
        complication_beat = _arc_beat(arc, "complication")
        climax_beat = _arc_beat(arc, "climax")
        inherited_beat = _arc_beat(arc, "inherited state")
        first_window = _arc_date_label(complication_beat, "the middle of the month")
        second_window = _arc_date_label(climax_beat, "the final week")
        opening_text = str((arc.get("opening") or (central_storyline,))[0])
        complication_text = str((arc.get("complication") or (central_storyline,))[0])
        climax_text = str((arc.get("climax") or (central_storyline,))[0])
        relationship_test = tuple(
            str(item) for item in (arc.get("relationship_test") or ()) if str(item).strip()
        )
        at_glance = (
            opening_text,
            complication_text,
            climax_text,
        )
        do_line = str(arc.get("do_line", "Follow the evidence in sequence."))
        dont_line = str(arc.get("dont_line", "Force the ending before the terms arrive."))
        action_plan = (
            str(
                (inherited_beat or {}).get(
                    "response",
                    "Identify the real amount, condition or expectation before reacting.",
                )
            ),
            str(
                (complication_beat or {}).get(
                    "response",
                    "Complete the document, cost or practical requirement that changes the decision.",
                )
            ),
            str(
                (climax_beat or {}).get(
                    "response",
                    "Use the strongest supported opening once the evidence becomes visible.",
                )
            ),
        )
        if str(romance_decision.get("relevance", "")) == "NOT MATERIAL":
            relationship_test = ()
        decision_plan = tuple(str(item) for item in (monthly_decision.get("action_plan") or ()) if str(item).strip())
        if decision_plan:
            action_plan = decision_plan
    else:
        primary_house = _dominant_house(result, 0, 1)
        secondary_house = _dominant_house(result, 1, primary_house)
        tertiary_house = None
        headline, subtitle = _headline(main_focus, primary_house, secondary_house)
        hook_headline = _monthly_hook(main_focus, primary_house, secondary_house)
        convergence_axis = f"{HOUSE_DISPLAY[primary_house]} x {HOUSE_DISPLAY[secondary_house]}"
        central_storyline = _central_storyline(result, primary_house, secondary_house)
        luna_says = _luna_voice(result, primary_house, secondary_house)
        scenario_examples = _scenario_examples(primary_house, secondary_house)
        convergences = _convergences(result)
        first_convergence = convergences[0] if convergences else None
        second_convergence = convergences[1] if len(convergences) > 1 else None
        first_window = _date_range(first_convergence["start_date"], first_convergence["end_date"]) if first_convergence else "the middle of the month"
        second_window = _date_range(second_convergence["start_date"], second_convergence["end_date"]) if second_convergence else "the final week"
        at_glance = (
            central_storyline,
            f"From {first_window}, a message, invitation, introduction or offer may make life feel larger. Enjoy the opening, but check the timing, cost and who is actually following through.",
            f"Around {second_window}, the month becomes more selective. Choose what has earned a lasting place in your life.",
        )
        chapters = (
            _build_chapter(result, "Chapter 1", 1, 10, "early", primary_house, secondary_house),
            _build_chapter(result, "Chapter 2", 11, 20, "middle", primary_house, secondary_house),
            _build_chapter(result, "Chapter 3", 21, 31, "late", primary_house, secondary_house),
        )
        key_dates = _key_dates(result)
        do_line, dont_line = luna_do_dont(primary_house, secondary_house)
        relationship_test = ()
        action_plan = (
            "State the interest or idea. Let the response provide evidence.",
            "Expand one proven option.",
            "Keep only what survives the reality check.",
        )
        decision_plan = tuple(str(item) for item in (monthly_decision.get("action_plan") or ()) if str(item).strip())
        if decision_plan:
            action_plan = decision_plan

    # Nature-led authority: once the trajectory layer has compared the month's
    # chronological windows, it supplies the master story. The older arc remains
    # intact as evidence/provenance, but it no longer gets to force a bridge or
    # subplot that Nature did not strongly support.
    if trajectory:
        hook_headline = str(trajectory.get("headline") or hook_headline)
        central_storyline = str(trajectory.get("central_storyline") or central_storyline)
        subtitle = central_storyline
        trajectory_story = tuple(str(item) for item in (trajectory.get("story_paragraphs") or ()) if str(item).strip())
        if trajectory_story:
            luna_says = trajectory_story
            at_glance = trajectory_story[:3]
        chapters = _trajectory_aligned_chapters(chapters, trajectory)

    if not trajectory:
        central_storyline = climate_aware_storyline(
            central_storyline,
            monthly_decision,
            primary_house=primary_house,
            secondary_house=secondary_house,
        )
    if not trajectory:
        hook_headline = climate_aware_hook(
            hook_headline,
            monthly_decision,
            primary_house=primary_house,
            secondary_house=secondary_house,
        )
    subtitle = central_storyline

    romance_active, romance_quiet = _romance_copy(primary_house, secondary_house)
    romance_relevance = str(romance_decision.get("relevance", "BACKGROUND"))
    romance_note = str(romance_decision.get("luna_line", "")).strip()
    romance_posture = str(romance_decision.get("posture", monthly_decision.get("posture", "QUESTION")))
    romance_truth = str(romance_decision.get("action_truth", "NOT ACT" if romance_posture != "ADVANCE" else "ACT"))
    if romance_relevance == "COUNTERCURRENT":
        romance_title = f"Romance & creativity · RELIEF · {romance_truth} / {romance_posture}"
        if romance_note:
            romance_active = romance_note
        romance_quiet = "Relief is useful precisely because it does not have to solve the main problem. Enjoy what is supportive and keep the timing honest."
    elif romance_relevance == "NOT MATERIAL":
        romance_title = "Romance is not running this month's meeting"
        romance_active = romance_note or romance_active
        romance_quiet = "That does not mean 'no romance'. It means the relationship evidence did not clear the convergent hierarchy strongly enough to become a main plot."
    elif romance_relevance == "BACKGROUND":
        romance_title = f"Romance stays in the background · {romance_truth} / {romance_posture}"
        if romance_note:
            romance_active = romance_note
    else:
        romance_title = f"Romance · {romance_relevance} · {romance_truth} / {romance_posture}"
        if romance_note:
            romance_active = romance_note
    agency_rule = GATEKEEPER_LINE
    decision_truth = str(monthly_decision.get("action_truth", "ACT"))
    strategic_posture = str(monthly_decision.get("posture", "ADVANCE"))
    strategic_rationale = str(monthly_decision.get("rationale", "Follow the evidence before choosing the move."))
    portfolio_posture = str(monthly_decision.get("portfolio_posture", ""))
    portfolio_rationale = str(monthly_decision.get("portfolio_rationale", ""))
    portfolio_plan = tuple(str(item) for item in (monthly_decision.get("portfolio_action_plan") or ()) if str(item).strip())
    if portfolio_plan:
        action_plan = portfolio_plan
    validation_rule = strategy_rule(monthly_decision)
    do_line, dont_line = strategy_do_dont(do_line, dont_line, monthly_decision)
    love_hook, work_hook, money_hook = _life_area_hooks(result, primary_house, secondary_house)
    convergences = _convergences(result)

    solar = result.get("solar_convergence") or {}
    solar_paragraphs = tuple(
        _plain_customer_astrology(item)
        for item in (solar.get("meaning") or ())
        if str(item).strip()
    )
    solar_gate_convergence = dict(solar.get("gate_convergence") or {})
    if solar_gate_convergence.get("material") and solar_gate_convergence.get("customer_line"):
        solar_paragraphs = solar_paragraphs + (_plain_customer_astrology(solar_gate_convergence.get("customer_line")),)
    solar_rows = (
        ("Your Sun", str(result.get("sign", "Sun sign"))),
        ("Current Sun", f"{solar.get('start_solar_sign', solar.get('solar_sign', 'Unavailable'))} → {solar.get('end_solar_sign', solar.get('solar_sign', 'Unavailable'))}"),
        ("Solar clock", SOLAR_CYCLE_COMPACT),
        ("Local light", f"{solar.get('light_direction', 'Unavailable')} from {solar.get('city', 'timezone estimate')}"),
        ("Solar gate", f"{solar_gate_label(solar.get('next_solar_gate', 'Unavailable'))} - {human_date(solar.get('next_gate_date')) if solar.get('next_gate_date') else 'Unavailable'}"),
        (
            "Solar life-area movement",
            f"{HOUSE_DISPLAY.get(int(solar.get('start_house', 1) or 1), 'Starting area')} → {HOUSE_DISPLAY.get(int(solar.get('end_house', 1) or 1), 'Next area')}",
        ),
        ("Solar convergence", str(solar_gate_convergence.get("status", "BACKGROUND"))),
    )

    scores = [float(item.get("score", 0.0)) for item in convergences]
    top_score = max(scores, default=0.0)
    relationship_current = (
        relationship_test[0]
        if relationship_test
        else (
            "Attraction expands through networks, unfamiliar territory or a creative opening; mutual effort matters more than fantasy."
            if main_focus == "Love and relationships"
            else "Relationship decisions need explicit terms and behaviour that matches the promise."
        )
    )
    arc_scenarios = list(arc.get("ranked_scenarios") or []) if arc else []
    top_scenario_text = "; ".join(
        f"{item.get('label', '')} ({item.get('confidence', '')})"
        for item in arc_scenarios[:3]
    ) or "No single scenario family dominates."
    countercurrent = dict(trajectory.get("countercurrent") or {})
    narrative_structure = (
        "Two-house convergence + relief" if countercurrent and not tertiary_house
        else "Three-house convergence" if tertiary_house
        else "Two-house convergence"
    )
    bridge_label = (
        HOUSE_DISPLAY.get(tertiary_house, f"House {tertiary_house}")
        if tertiary_house
        else "No third house cleared the convergence gate"
    )
    snapshot_rows = (
        ("Primary story", convergence_axis),
        ("Truth gate", f"{decision_truth} · {strategic_posture}"),
        ("Portfolio strategy", portfolio_posture or strategic_posture),
        ("Romance hierarchy", romance_relevance),
        ("Narrative structure", narrative_structure),
        ("Trajectory", str(trajectory.get("trajectory_reason", "Event-led sequence")) if trajectory else "Event-led sequence"),
        ("Bridge current", bridge_label),
        ("Relief", str(countercurrent.get("summary", "None verified")) if countercurrent else "None verified"),
        ("Personal focus", main_focus),
        ("Relationship current", relationship_current),
        ("Ranked scenario families", top_scenario_text),
        ("Narrative selection", str(arc.get("selection_rationale", "Event-led story graph")) if arc else "Dominant-house fallback"),
        ("Dates", f"Local dates in {result.get('timezone_name', 'selected timezone')}"),
        ("Complication window", first_window),
        ("Climax window", second_window),
        ("Monthly concentration", _strength_label(top_score)),
        ("Long-term climate", _retrograde_climate(result)),
        ("Your Sun", str(result.get("sign", "Sun sign"))),
        ("Current Sun", f"{solar.get('start_solar_sign', solar.get('solar_sign', 'Unavailable'))} → {solar.get('end_solar_sign', solar.get('solar_sign', 'Unavailable'))}"),
        ("Local light", f"{solar.get('light_direction', 'Unavailable')} - {solar.get('city', 'timezone estimate')}"),
        ("Solar gate", f"{solar_gate_label(solar.get('next_solar_gate', 'Unavailable'))} - {human_date(solar.get('next_gate_date')) if solar.get('next_gate_date') else 'Unavailable'}"),
        ("Solar convergence", str((solar.get("gate_convergence") or {}).get("status", "BACKGROUND"))),
    )

    counter_love_story = _countercurrent_love_story(result, trajectory)

    return MonthlyNarrative(
        sign=str(result.get("sign", "")),
        label=str(result.get("label", "Monthly Report")),
        main_focus=main_focus,
        personal_question=question,
        hook_headline=hook_headline,
        convergence_axis=convergence_axis,
        headline=headline,
        subtitle=subtitle,
        central_storyline=central_storyline,
        luna_says=luna_says,
        agency_rule=agency_rule,
        validation_rule=validation_rule,
        scenario_examples=scenario_examples,
        romance_active=romance_active,
        romance_quiet=romance_quiet,
        relationship_test=relationship_test,
        decision_truth=decision_truth,
        strategic_posture=strategic_posture,
        strategic_rationale=strategic_rationale,
        portfolio_posture=portfolio_posture,
        portfolio_rationale=portfolio_rationale,
        romance_relevance=romance_relevance,
        romance_title=romance_title,
        romance_note=romance_note,
        at_glance=at_glance,
        focus_title=FOCUS_TITLES.get(main_focus, FOCUS_TITLES["General overview"]),
        focus_answer=_focus_answer(result, main_focus, question, primary_house, secondary_house),
        chapters=chapters,
        love_story=counter_love_story or _love_story(result, primary_house, secondary_house),
        work_story=_work_story(result, primary_house, secondary_house),
        money_story=_money_story(result, primary_house, secondary_house),
        do_line=do_line,
        dont_line=dont_line,
        love_hook=love_hook,
        work_hook=work_hook,
        money_hook=money_hook,
        hidden_opportunity=(
            str((arc.get("climax") or (f"Use the strongest opening in {second_window} deliberately.",))[0])
            if arc
            else f"Use the strongest opening in {first_window} to make one relationship, creative or strategic possibility more concrete."
        ),
        watch_out=(
            str((arc.get("complication") or (f"Do not let the practical terms remain vague around {first_window}.",))[0])
            if arc
            else f"Do not let excitement around {HOUSE_PROSE[secondary_house]} outrun facts, cost, timing or operational capacity."
        ),
        action_plan=action_plan,
        key_dates=key_dates,
        snapshot_rows=snapshot_rows,
        solar_title="Solar clock evidence",
        solar_paragraphs=solar_paragraphs,
        solar_rows=solar_rows,
        solar_opportunity=_plain_customer_astrology(solar.get("opportunity", "Use the current solar phase deliberately.")),
        solar_risk=_plain_customer_astrology(solar.get("risk", "Do not force a phase that the evidence does not support.")),
        solar_action=_plain_customer_astrology(solar.get("action", "Match the action to the current solar phase.")),
        solar_rule=_plain_customer_astrology(solar.get("solar_rule", "Begin, develop, evaluate and consolidate in sequence.")),
        solar_equation=_plain_customer_astrology(solar.get("equation", "Tropical Sun + local light + activated life area = Solar Convergence")),
        problem_horizon=dict(result.get("problem_horizon") or {}),
        technical_appendix_markdown=_technical_appendix(result, order_reference),
    )


def monthly_narrative_markdown(narrative: MonthlyNarrative) -> str:
    lines: list[str] = []
    lines.extend([
        f"# {narrative.hook_headline}",
        "",
        f"**Monthly convergence:** {narrative.convergence_axis}",
        "",
        f"**Serious theme:** {narrative.headline}",
        "",
        narrative.subtitle,
        "",
        "## What matters now",
        "",
        *narrative.luna_says,
        "",
        f"> {narrative.central_storyline}",
        "",
        f"**Agency rule:** {narrative.agency_rule}",
        "",
        f"**Validation rule:** {narrative.validation_rule}",
        "",
        f"**Do:** {narrative.do_line}",
        "",
        f"**Don't:** {narrative.dont_line}",
        "",
    ])

    horizon = narrative.problem_horizon or {}
    if horizon:
        lines.extend([
            "# The problem",
            "",
            str(horizon.get("problem", "")),
            "",
            "## If you ignore it",
            "",
            str(horizon.get("if_ignored", "")),
            "",
            "## Your move",
            "",
            str(horizon.get("highest_leverage_move", "")),
            "",
            "## How long this stays live",
            "",
            str(horizon.get("timing", "")),
            "",
            "## What keeps this active",
            "",
        ])
        for force in horizon.get("forces") or []:
            lines.extend([
                f"### {force.get('planet', '')} · {force.get('area', '')}",
                "",
                str(force.get("problem", "")),
                "",
                f"**If left alone:** {force.get('if_ignored', '')}",
                "",
                f"**Your move:** {force.get('leverage', '')}",
                "",
                f"**Active since:** {force.get('active_since', '')}",
                "",
                f"**Current phase:** {force.get('current_phase', '')}",
                "",
                f"**Peak:** {force.get('peak', '')}",
                "",
                f"**Next change:** {force.get('changes', '')}",
                "",
                f"**Long shift:** {force.get('structural_shift', '')}",
                "",
            ])

    lines.extend([
        "# Your month at a glance",
        "",
    ])
    for paragraph in narrative.at_glance:
        lines.extend([paragraph, ""])

    if narrative.relationship_test:
        lines.extend([
            "# Luna's relationship test",
            "",
            *narrative.relationship_test,
            "",
        ])

    lines.extend([f"# {narrative.focus_title}", ""])
    if narrative.personal_question:
        lines.extend([
            f"**Your question:** {narrative.personal_question}",
            "",
        ])
    for paragraph in narrative.focus_answer:
        lines.extend([paragraph, ""])

    lines.extend([
        "[[PAGEBREAK]]",
        "",
        "# Your Solar Clock",
        "",
        f"## {narrative.solar_title}",
        "",
    ])
    for paragraph in narrative.solar_paragraphs:
        lines.extend([paragraph, ""])
    lines.extend([
        "| Solar evidence | This month |",
        "|---|---|",
    ])
    for label, value in narrative.solar_rows:
        lines.append(f"| {label} | {value} |")
    lines.extend([
        "",
        f"**The solar reference:** {narrative.solar_equation}",
        "",
        f"**Opportunity:** {narrative.solar_opportunity}",
        "",
        f"**Risk:** {narrative.solar_risk}",
        "",
        f"**Strategic response:** {narrative.solar_action}",
        "",
        f"**Solar rule for the month:** {narrative.solar_rule}",
        "",
        "[[PAGEBREAK]]",
        "",
        "# The month in three chapters",
        "",
    ])
    for chapter_index, chapter in enumerate(narrative.chapters, 1):
        if chapter_index == 3:
            lines.extend(["[[PAGEBREAK]]", ""])
        lines.extend([
            f"## {chapter.hook}",
            f"**{chapter.label} / {chapter.date_range}:** {chapter.title}",
            "",
        ])
        for paragraph in chapter.paragraphs:
            lines.extend([paragraph, ""])
        lines.extend([
            f"**Action:** {chapter.action}",
            "",
            "**Evidence underneath:**",
        ])
        for item in chapter.evidence:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["[[PAGEBREAK]]", ""])
    sections = [
        ("Love and relationships", narrative.love_hook, narrative.love_story),
        ("Work and direction", narrative.work_hook, narrative.work_story),
        ("Money and security", narrative.money_hook, narrative.money_story),
    ]
    for title, hook, paragraphs in sections:
        lines.extend([f"# {title}", "", f"## {hook}", ""])
        for paragraph in paragraphs:
            lines.extend([paragraph, ""])

    lines.extend([
        "[[PAGEBREAK]]",
        "",
        "# Your monthly strategy",
        "",
        f"## Hidden opportunity",
        narrative.hidden_opportunity,
        "",
        "## Watch out",
        narrative.watch_out,
        "",
        "## Action plan",
    ])
    for index, action in enumerate(narrative.action_plan, 1):
        lines.append(f"{index}. {action}")
    lines.append("")

    lines.extend([
        "# Key dates",
        "",
        "| Date | What may become important | Best response | Evidence |",
        "|---|---|---|---|",
    ])
    for item in narrative.key_dates:
        lines.append(
            f"| {item.date_label} | {item.consequence} | {item.response} | {item.evidence} |"
        )
    lines.append("")

    lines.extend([
        "[[PAGEBREAK]]",
        "",
        "# Monthly Sky Snapshot",
        "",
        "| Monthly evidence | Interpretation |",
        "|---|---|",
    ])
    for label, value in narrative.snapshot_rows:
        lines.append(f"| {label} | {value} |")
    lines.extend([
        "",
        "The concentration score measures how strongly one astrological pattern dominates the month. It is not the probability that a predicted event will occur.",
        "",
        "[[PAGEBREAK]]",
        "",
        narrative.technical_appendix_markdown,
    ])
    return "\n".join(lines)
