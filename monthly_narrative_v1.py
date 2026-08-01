from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Iterable


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
    1: "identity, confidence and personal direction",
    2: "income, value, possessions and security",
    3: "messages, decisions, learning and everyday movement",
    4: "home, family and emotional foundations",
    5: "romance, pleasure, children and creative expression",
    6: "workload, health, routines and practical systems",
    7: "partners, clients, agreements and significant relationships",
    8: "trust, intimacy, debt and shared financial responsibilities",
    9: "travel, education, publishing and a wider world",
    10: "career, visibility, authority and public direction",
    11: "friends, audiences, communities and future plans",
    12: "rest, closure, private feelings and unfinished matters",
}

HOUSE_NATURAL = {
    1: "who you are becoming",
    2: "money, value and security",
    3: "messages, decisions and everyday movement",
    4: "home and private life",
    5: "love, creativity and what brings you alive",
    6: "work, wellbeing and daily rhythm",
    7: "relationships and agreements",
    8: "trust, intimacy and shared money",
    9: "new horizons, learning and expansion",
    10: "work, reputation and visible results",
    11: "your circle and future plans",
    12: "rest, closure and private feelings",
}


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
    1: "The main character has stopped asking permission",
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
    technical_appendix_markdown: str


def normalise_personal_question(value: str | None) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    if text.lower() in NO_QUESTION_VALUES:
        return ""
    return text


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _date_label(value: str) -> str:
    """Return a platform-independent customer date such as 'August 1'."""
    parsed = _parse_date(value)
    return f"{parsed.strftime('%B')} {parsed.day}"


def _date_range(start: str, end: str) -> str:
    first = _parse_date(start)
    last = _parse_date(end)
    if first.month == last.month:
        return f"{first.strftime('%B')} {first.day}-{last.day}"
    return f"{first.strftime('%B')} {first.day}-{last.strftime('%B')} {last.day}"


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


def _life_area_hooks(primary_house: int, secondary_house: int) -> tuple[str, str, str]:
    pair = frozenset({primary_house, secondary_house})
    love = (
        "A spark is easy. Shared direction is the test"
        if 5 in pair or 9 in pair
        else "Attention is flattering. Consistency is evidence"
    )
    work = (
        "The idea is ready to leave the group chat"
        if 9 in pair or 10 in pair
        else "Busy is not the same as visible"
    )
    money = (
        "The opportunity looks exciting. Ask who is paying"
        if 5 in pair or 9 in pair
        else "The numbers deserve their own conversation"
    )
    return love, work, money


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
            f"Something exciting expands your world, but {month} tests "
            "whether it earns a place in your life."
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
    scenarios = _scenario_examples(primary_house, secondary_house)
    first_examples = ", ".join(scenarios[:3])
    second_examples = ", ".join(scenarios[3:])

    if frozenset({primary_house, secondary_house}) == frozenset({5, 9}):
        return (
            f"{month} brings a bigger world closer. A relationship, flirtation, "
            "trip, course, creative project or visible opportunity could make "
            "you feel more desired, noticed and alive.",
            "Enjoy the attention—but notice who follows through, what the "
            "opportunity asks of you and whether it fits the life you actually "
            "want. You are not waiting to be selected. You are deciding what "
            "deserves access.",
        )

    return (
        f"{month} may bring {first_examples}. Any of these can make you feel "
        "more visible, wanted or certain that change is beginning.",
        f"Luna's question is what happens next. Watch the evidence around "
        f"{second_examples}: effort, clarity and practical follow-through decide "
        "what earns more of your time.",
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
            "If romance or flirting is active, interest may become more visible. "
            "Enjoy the chemistry, but let consistency, intention and effort show "
            "whether the connection deserves more access to your life."
        )
    else:
        active = (
            "If someone is showing interest, the real question is not whether "
            "you can attract attention. It is whether their behaviour matches "
            "the future and standards you are choosing."
        )

    quiet = (
        "If romance is quiet, the same validation can arrive through "
        f"{validation_area}: being invited, trusted, praised, chosen for an "
        "opportunity or recognised for what you bring. Let the attention remind "
        "you of your range without allowing it to make the decision for you."
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
            f"The month opens through {_natural_house(main_house)}. A person, message or invitation may make you feel noticed, but you decide what deserves access to your time.",
            f"{strongest_story} Treat the first opening as information. Interest may begin the story; effort decides whether you continue it.",
        )
    elif segment == "middle":
        paragraphs = (
            f"The middle of the month carries the strongest concentration. {strongest_story} Attention, chemistry or possibility may increase, but so should your standards.",
            f"The test is whether progress in {_natural_house(main_house)} supports {_natural_house(second_house)}. Choose the person or opportunity that matches your energy with practical follow-through.",
        )
    else:
        paragraphs = (
            f"Late in the month, {first_story[0].lower() + first_story[1:]} The fantasy meets the calendar, the cost and the amount of effort each person is willing to make.",
            f"The closing question is how to reconcile {_natural_house(main_house)} with {_natural_house(second_house)}. You keep what strengthens your life; the rest does not earn another month.",
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


def _love_story(result: dict, primary_house: int, secondary_house: int) -> tuple[str, ...]:
    relevant = [
        item for item in _all_events(result)
        if set(item.get("planets") or []) & {"Venus", "Mars", "Neptune", "Saturn", "Moon"}
        or set(item.get("houses") or []) & {5, 7, 8, 11}
    ]
    evidence = _select_chapter_evidence(relevant, maximum=3)
    evidence_text = "; ".join(evidence) if evidence else "the month's relationship-sensitive transitions"
    active, quiet = _romance_copy(primary_house, secondary_house)
    return (
        active,
        quiet,
        f"The relationship evidence concentrates around {evidence_text}. "
        "Attention gets your notice. Effort earns your interest. Consistency "
        "earns a place in your life.",
        "Best relationship move: observe what the person does after the exciting "
        "moment. You are not waiting to be selected; you are deciding whether "
        "their behaviour deserves your time.",
    )

def _work_story(result: dict, primary_house: int, secondary_house: int) -> tuple[str, ...]:
    career_events = [
        item for item in _all_events(result)
        if set(item.get("houses") or []) & {6, 10, 11, 3, 9}
        or set(item.get("planets") or []) & {"Sun", "Mercury", "Jupiter", "Saturn"}
    ]
    evidence = _select_chapter_evidence(career_events, maximum=3)
    evidence_text = "; ".join(evidence) if evidence else "the month's work-sensitive transitions"
    return (
        f"Work gains momentum when {HOUSE_PROSE[primary_house]} produces something visible, teachable or repeatable. The secondary pressure from {HOUSE_PROSE[secondary_house]} means expansion must be matched by facts, capacity and a clear owner.",
        f"Important work evidence includes {evidence_text}. Use the later part of the month to finish one result that can be seen and evaluated rather than trying to look busy in several directions.",
        "Best work move: define the deliverable, the deadline and who is responsible before enthusiasm creates additional work.",
    )


def _money_story(result: dict, primary_house: int, secondary_house: int) -> tuple[str, ...]:
    money_events = [
        item for item in _all_events(result)
        if set(item.get("houses") or []) & {2, 8, 10}
        or set(item.get("planets") or []) & {"Venus", "Mars", "Jupiter", "Saturn"}
    ]
    evidence = _select_chapter_evidence(money_events, maximum=3)
    evidence_text = "; ".join(evidence) if evidence else "the month's money-sensitive transitions"
    return (
        f"Money needs to be separated into what is earned, what is received, what is owed and what is merely expected. The interaction between {HOUSE_PROSE[primary_house]} and {HOUSE_PROSE[secondary_house]} can make an exciting opportunity look more secure than it is.",
        f"Important financial evidence includes {evidence_text}. Shared costs, tax, debt, pricing or obligations should be written down before a commitment is enlarged.",
        "Best money move: make every cost and responsibility visible, then decide from available cash and proven demand rather than hope.",
    )


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
    dominant_rows = ["| Rank | House | Customer life area | Weight |", "|---:|---:|---|---:|"]
    for rank, item in enumerate((result.get("dominant_houses") or [])[:6], 1):
        house = int(item.get("house", 1))
        dominant_rows.append(
            f"| {rank} | {house} | {HOUSE_PROSE[house]} | {float(item.get('weight', 0.0)):.1f} |"
        )

    convergence_rows = ["| Window | Type | Strength | Dominant houses |", "|---|---|---:|---|"]
    for item in _convergences(result)[:4]:
        houses = sorted({int(h) for event in item.get("events", []) for h in event.get("houses", [])})[:3]
        convergence_rows.append(
            f"| {_date_range(item['start_date'], item['end_date'])} | {item.get('title', 'Convergence')} | {float(item.get('score', 0.0)):.0f}/100 | {', '.join(map(str, houses)) or 'n/a'} |"
        )

    event_rows = ["| Date | Evidence | Houses |", "|---|---|---|"]
    for item in _events(result):
        event_rows.append(
            f"| {_date_label(item['event_date'])} | {item.get('title', 'Transition')} | {', '.join(map(str, item.get('houses') or []))} |"
        )

    retro_rows = ["| Planet | Retrograde | Direct | Houses |", "|---|---|---|---|"]
    for item in _retrogrades(result):
        retro_rows.append(
            f"| {item.get('planet', '')} | {_date_label(item['retrograde_start'])} | {_date_label(item['direct_date'])} | {', '.join(map(str, item.get('houses') or []))} |"
        )

    solar = result.get("solar_convergence") or {}
    solar_rows = [
        "| Solar evidence | Calculated value |",
        "|---|---|",
        f"| Tropical Sun | {solar.get('solar_longitude', 'n/a')}° {solar.get('solar_sign', '')} |",
        f"| Solar quarter | {solar.get('solar_quarter', 'n/a')} |",
        f"| Local light | {solar.get('light_direction', 'n/a')} from {solar.get('city', 'timezone estimate')} |",
        f"| Activated house | {solar.get('activated_house', 'n/a')} - {solar.get('activated_house_name', '')} |",
        f"| Next solar gate | {solar.get('next_solar_gate', 'n/a')} - {solar.get('next_gate_date', '')} |",
        f"| Location basis | {solar.get('location_basis', 'n/a')} |",
    ]

    order_line = f"\n\n**Order reference:** `{order_reference}`" if order_reference else ""
    return "\n".join(
        [
            "# Technical appendix",
            "",
            "This appendix contains the calculation trail supporting the customer narrative. House numbers and event names are evidence; the main report above translates them into consequences, timing and practical decisions.",
            "",
            "## Solar Convergence evidence",
            "",
            *solar_rows,
            "",
            "## Dominant house evidence",
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
            "Tropical geocentric planetary positions are calculated with Swiss Ephemeris and interpreted using whole-sign houses. Strength labels describe the concentration of the internal astrological pattern; they are not probabilities or guarantees of events.",
            order_line,
        ]
    )


def build_monthly_narrative(
    result: dict,
    main_focus: str = "General overview",
    personal_question: str = "",
    order_reference: str = "",
) -> MonthlyNarrative:
    if result.get("period") != "monthly":
        raise ValueError("Monthly Narrative Engine requires a monthly period result")

    question = normalise_personal_question(personal_question)
    primary_house = _dominant_house(result, 0, 1)
    secondary_house = _dominant_house(result, 1, primary_house)
    headline, subtitle = _headline(main_focus, primary_house, secondary_house)
    hook_headline = _monthly_hook(main_focus, primary_house, secondary_house)
    convergence_axis = f"{HOUSE_DISPLAY[primary_house]} x {HOUSE_DISPLAY[secondary_house]}"
    central_storyline = _central_storyline(result, primary_house, secondary_house)
    luna_says = _luna_voice(result, primary_house, secondary_house)
    scenario_examples = _scenario_examples(primary_house, secondary_house)
    romance_active, romance_quiet = _romance_copy(primary_house, secondary_house)
    agency_rule = (
        "You are not waiting to be selected. You are deciding what deserves access."
    )
    validation_rule = (
        "Attention gets your notice. Effort earns your interest. "
        "Consistency earns a place in your life."
    )
    love_hook, work_hook, money_hook = _life_area_hooks(primary_house, secondary_house)
    convergences = _convergences(result)
    first_convergence = convergences[0] if convergences else None
    second_convergence = convergences[1] if len(convergences) > 1 else None

    first_window = _date_range(first_convergence["start_date"], first_convergence["end_date"]) if first_convergence else "the middle of the month"
    second_window = _date_range(second_convergence["start_date"], second_convergence["end_date"]) if second_convergence else "the final week"

    at_glance = (
        central_storyline,
        f"From {first_window}, a message, invitation, introduction or offer may "
        "make life feel larger. Enjoy the opening, but check the timing, cost and "
        "who is actually following through.",
        f"Around {second_window}, the month becomes more selective. You are not "
        "trying to keep every possibility alive; you are choosing what has earned "
        "a lasting place in your life.",
    )

    chapters = (
        _build_chapter(result, "Chapter 1", 1, 10, "early", primary_house, secondary_house),
        _build_chapter(result, "Chapter 2", 11, 20, "middle", primary_house, secondary_house),
        _build_chapter(result, "Chapter 3", 21, 31, "late", primary_house, secondary_house),
    )

    solar = result.get("solar_convergence") or {}
    solar_paragraphs = tuple(
        str(item)
        for item in (solar.get("meaning") or ())
        if str(item).strip()
    )
    solar_rows = (
        ("Solar phase", f"{solar.get('solar_quarter', 'Unavailable')} / {solar.get('solar_process', '')}"),
        ("Local light movement", f"{solar.get('light_direction', 'Unavailable')} from {solar.get('city', 'timezone estimate')}"),
        ("Local season", str(solar.get("local_season", "Unavailable"))),
        ("Next solar gate", f"{solar.get('next_solar_gate', 'Unavailable')} - {solar.get('next_gate_date', '')}"),
        ("Solar house movement", f"House {solar.get('start_house', '?')} to house {solar.get('end_house', '?')}"),
        ("Customer focus", str(solar.get("focus_meaning", "Unavailable"))),
    )

    scores = [float(item.get("score", 0.0)) for item in convergences]
    top_score = max(scores, default=0.0)
    relationship_current = (
        "Attraction expands through networks, unfamiliar territory or a creative opening; mutual effort matters more than fantasy."
        if main_focus == "Love and relationships"
        else "Relationship decisions need explicit terms and behaviour that matches the promise."
    )
    snapshot_rows = (
        ("Primary theme", f"{HOUSE_DISPLAY[primary_house]} x {HOUSE_DISPLAY[secondary_house]}"),
        ("Personal focus", main_focus),
        ("Relationship current", relationship_current),
        ("Work current", "Visibility and professional decisions strengthen later in the month."),
        ("Money pressure", "Shared costs, obligations and ownership need to be visible before commitment."),
        ("Strongest window", first_window),
        ("Second turning point", second_window),
        ("Monthly concentration", _strength_label(top_score)),
        ("Long-term climate", _retrograde_climate(result)),
        ("Solar phase", f"{solar.get('solar_quarter', 'Unavailable')} / {solar.get('solar_process', '')}"),
        ("Local light", f"{solar.get('light_direction', 'Unavailable')} - {solar.get('city', 'timezone estimate')}"),
        ("Next solar gate", f"{solar.get('next_solar_gate', 'Unavailable')} - {solar.get('next_gate_date', '')}"),
    )

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
        at_glance=at_glance,
        focus_title=FOCUS_TITLES.get(main_focus, FOCUS_TITLES["General overview"]),
        focus_answer=_focus_answer(result, main_focus, question, primary_house, secondary_house),
        chapters=chapters,
        love_story=_love_story(result, primary_house, secondary_house),
        work_story=_work_story(result, primary_house, secondary_house),
        money_story=_money_story(result, primary_house, secondary_house),
        do_line=(
            "Follow the person or opportunity that shows real effort."
            if frozenset({primary_house, secondary_house}) == frozenset({5, 9})
            else HOUSE_DO[primary_house]
        ),
        dont_line=(
            "Confuse being noticed with being valued."
            if frozenset({primary_house, secondary_house}) == frozenset({5, 9})
            else HOUSE_DONT[secondary_house]
        ),
        love_hook=love_hook,
        work_hook=work_hook,
        money_hook=money_hook,
        hidden_opportunity=f"Use the strongest opening in {first_window} to make one relationship, creative or strategic possibility more concrete.",
        watch_out=f"Do not let excitement around {HOUSE_PROSE[secondary_house]} outrun facts, cost, timing or operational capacity.",
        action_plan=(
            HOUSE_ACTION[primary_house],
            HOUSE_ACTION[secondary_house],
            "Review the result after the second turning point and keep only what can be sustained.",
        ),
        key_dates=_key_dates(result),
        snapshot_rows=snapshot_rows,
        solar_title=str(solar.get("headline", "Your Solar Convergence")),
        solar_paragraphs=solar_paragraphs,
        solar_rows=solar_rows,
        solar_opportunity=str(solar.get("opportunity", "Use the current solar phase deliberately.")),
        solar_risk=str(solar.get("risk", "Do not force a phase that the evidence does not support.")),
        solar_action=str(solar.get("action", "Match the action to the current solar phase.")),
        solar_rule=str(solar.get("solar_rule", "Begin, develop, evaluate and consolidate in sequence.")),
        solar_equation=str(solar.get("equation", "Tropical Sun + local light + activated house = Solar Convergence")),
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
        "## Luna says",
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
        "# Your month at a glance",
        "",
    ])
    for paragraph in narrative.at_glance:
        lines.extend([paragraph, ""])

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
        "# Your Solar Convergence",
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
        f"**The convergence:** {narrative.solar_equation}",
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
