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
    headline: str
    subtitle: str
    at_glance: tuple[str, ...]
    focus_title: str
    focus_answer: tuple[str, ...]
    chapters: tuple[MonthlyChapter, ...]
    love_story: tuple[str, ...]
    work_story: tuple[str, ...]
    money_story: tuple[str, ...]
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
    return _parse_date(value).strftime("%B %-d")


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
            f"The opening part of the month begins with {first_story[0].lower() + first_story[1:]} This is the point to notice which people, ideas or opportunities create genuine movement rather than simply more activity.",
            f"{strongest_story} Keep the response measured: the first opening is information, not yet a final outcome.",
        )
    elif segment == "middle":
        paragraphs = (
            f"The middle of the month carries the greatest concentration of events. {strongest_story} What appears exciting may also expose a cost, obligation or missing fact that needs to be made visible.",
            f"The practical test is whether progress in {HOUSE_PROSE[main_house]} can be sustained without destabilising {HOUSE_PROSE[second_house]}. Use the strongest days to make one credible move, not several speculative ones.",
        )
    else:
        paragraphs = (
            f"Late in the month, {first_story[0].lower() + first_story[1:]} The focus shifts from possibility toward consequences, ownership and what can actually be maintained.",
            f"The month closes by asking you to reconcile {HOUSE_PROSE[main_house]} with {HOUSE_PROSE[second_house]}. A visible result matters, but so does the private structure supporting it.",
        )

    return MonthlyChapter(
        label=label,
        date_range=f"{start_day}-{end_day}",
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
        paragraphs = [
            f"The month is dominated by {HOUSE_PROSE[primary_house]}, with {HOUSE_PROSE[secondary_house]} acting as the second major pressure point.",
            f"The strongest concentration falls in {strongest_window}. Use this period for one clear advance, then protect the structure that allows it to last.",
            "The month rewards evidence, sequence and ownership more than speed or emotional certainty.",
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
    return (
        f"Love and relationships are shaped by {HOUSE_PROSE[primary_house]} and {HOUSE_PROSE[secondary_house]}. This can bring attraction through creativity, travel, work, friendship or a larger plan, depending on where the opportunity appears in real life.",
        f"The evidence is concentrated around {evidence_text}. Enjoy the opening, but judge the connection by consistency, direct communication and whether both people can share responsibility as well as excitement.",
        "Best relationship move: state the practical truth early. A clear boundary does not reduce romance; it reveals whether the connection can hold something real.",
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
        f"{HOUSE_DISPLAY[primary_house]} leads the month",
        f"Progress depends on how well it is integrated with {HOUSE_DISPLAY[secondary_house].lower()}.",
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
    convergences = _convergences(result)
    first_convergence = convergences[0] if convergences else None
    second_convergence = convergences[1] if len(convergences) > 1 else None

    first_window = _date_range(first_convergence["start_date"], first_convergence["end_date"]) if first_convergence else "the middle of the month"
    second_window = _date_range(second_convergence["start_date"], second_convergence["end_date"]) if second_convergence else "the final week"

    at_glance = (
        f"{result['label']} is led by {HOUSE_PROSE[primary_house]}, while {HOUSE_PROSE[secondary_house]} supplies the second major pressure point. The opportunity is not simply to experience more; it is to turn one desire, idea or opening into something credible and repeatable.",
        f"The first major concentration runs through {first_window}. Connections, information and possibility can gather quickly, but the strongest choice is the one that remains useful after the excitement settles.",
        f"A second turning point develops in {second_window}. Career, home, relationships or obligations may compete for attention, making clear ownership and sequence more important than speed.",
        f"The month's rule is simple: {HOUSE_ACTION[primary_house]} Protect the month from the main distortion of {HOUSE_PROSE[secondary_house]} by checking facts, capacity and consequences before expansion.",
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
        headline=headline,
        subtitle=subtitle,
        at_glance=at_glance,
        focus_title=FOCUS_TITLES.get(main_focus, FOCUS_TITLES["General overview"]),
        focus_answer=_focus_answer(result, main_focus, question, primary_house, secondary_house),
        chapters=chapters,
        love_story=_love_story(result, primary_house, secondary_house),
        work_story=_work_story(result, primary_house, secondary_house),
        money_story=_money_story(result, primary_house, secondary_house),
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
        f"# {narrative.headline}",
        "",
        narrative.subtitle,
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
            f"## {chapter.label}: {chapter.title}",
            f"**Window:** {chapter.date_range}",
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
        ("Love and relationships", narrative.love_story),
        ("Work and direction", narrative.work_story),
        ("Money and security", narrative.money_story),
    ]
    for title, paragraphs in sections:
        lines.extend([f"# {title}", ""])
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
