from __future__ import annotations

from datetime import date, timedelta
from calendar import month_name
from collections import Counter
from typing import Iterable

from astrology_engine import (
    SIGNS, HOUSE_NAMES, HARD_ASPECTS, FLOW_ASPECTS,
    Position, Aspect, Event, RetrogradeCycle, Convergence,
    positions_for_date, house_map, detect_aspects, period_events,
    retrograde_cycles, convergence_points, dominant_houses, serialize,
)
from interpretation_library import (
    PLANET_MEANINGS, HOUSE_STRATEGY, RETROGRADE_MEANINGS, COMBINATION_MEANINGS,
)
from solar_cycle import (
    monthly_solar_convergence,
    yearly_solar_chapters,
    yearly_solar_markdown,
)
from monthly_arc_engine import build_monthly_arc


HOUSE_LABELS = {
    1: "identity, body, energy and personal direction",
    2: "personal income, pricing, possessions and self-worth",
    3: "communication, selling, learning and local movement",
    4: "home, family, property and emotional foundations",
    5: "creativity, pleasure, romance, children and enterprise",
    6: "work routines, health, service and operations",
    7: "partners, customers, contracts and competitors",
    8: "shared money, debt, tax, insurance and trust",
    9: "travel, publishing, higher education, law and foreign markets",
    10: "career, status, authority and public reputation",
    11: "networks, audiences, friends, alliances and future goals",
    12: "rest, hidden matters, endings and private psychology",
}


def house_reference_matrix(sign: str, emphasise: set[int] | None = None) -> str:
    emphasise = emphasise or set()
    native_index = SIGNS.index(sign)
    rows = [
        "| House | Sign | Life area | Current role |",
        "|---:|---|---|---|",
    ]
    for house in range(1, 13):
        sign_name = SIGNS[(native_index + house - 1) % 12]
        role = "**Active focus**" if house in emphasise else ""
        rows.append(
            f"| {house} | {sign_name} | {HOUSE_LABELS[house]} | {role} |"
        )
    return "\n".join(rows)


def house_aware_conclusion(sign: str, action_house: int, caution_house: int) -> str:
    action_topic = HOUSE_LABELS[action_house]
    caution_topic = HOUSE_LABELS[caution_house]
    action = HOUSE_STRATEGY[action_house]["action"]
    risk = HOUSE_STRATEGY[caution_house]["risk"]

    return (
        f"House {action_house} governs **{action_topic}**, so the best strategy for "
        f"{sign} is to {action}. "
        f"House {caution_house} governs **{caution_topic}**, so short-term pressure "
        f"in this area—especially {risk}—should not derail the larger transition."
    )


def _date_range_label(start: date, end: date) -> str:
    if start == end:
        return start.strftime("%B %d")
    if start.month == end.month:
        return f"{start.strftime('%B %d')}–{end.strftime('%d')}"
    return f"{start.strftime('%B %d')}–{end.strftime('%B %d')}"


def _combination_match(planets: set[str]):
    matches = []
    for combination, material in COMBINATION_MEANINGS.items():
        if combination <= planets:
            matches.append((combination, material))
    return matches


def _convergence_combinations(convergence: Convergence):
    """
    Count a named planetary combination only when it is directly represented
    by an aspect event, or both planets are structural anchors in the window.
    """
    direct_pairs = {
        frozenset(event.planets)
        for event in convergence.events
        if event.kind == "aspect" and len(event.planets) == 2
    }
    structural_planets = {
        planet
        for event in convergence.events
        if event.importance >= 8.0 or event.kind in {"eclipse", "station"}
        for planet in event.planets
    }
    matches = []
    for combination, material in COMBINATION_MEANINGS.items():
        if combination in direct_pairs or combination <= structural_planets:
            matches.append((combination, material))
    return matches


def event_interpretation(event: Event) -> dict:
    houses = list(event.houses)
    planets = list(event.planets)
    primary_house = houses[0] if houses else 1
    house_material = HOUSE_STRATEGY[primary_house]

    if event.kind == "aspect" and len(planets) == 2:
        combinations = _combination_match(set(planets))
        if combinations:
            material = combinations[0][1]
            meaning = material["meaning"]
            opportunity = material["opportunity"]
            risk = material["risk"]
        else:
            p1 = PLANET_MEANINGS[planets[0]]
            p2 = PLANET_MEANINGS[planets[1]]
            meaning = (
                f"{p1['core'].capitalize()} interact with {p2['core']}. "
                f"The result must be expressed through houses {', '.join(map(str, houses))}."
            )
            if event.polarity == "opportunity":
                opportunity = f"{p1['opportunity']}; also {p2['opportunity']}"
                risk = f"taking the easy flow for granted while ignoring {p1['risk']}"
            elif event.polarity == "pressure":
                opportunity = f"use the friction to improve method, boundaries and sequence"
                risk = f"{p1['risk']}; also {p2['risk']}"
            else:
                opportunity = p1["opportunity"]
                risk = p2["risk"]
    elif event.kind == "ingress":
        planet = planets[0]
        material = PLANET_MEANINGS[planet]
        meaning = (
            f"{planet} begins a new phase in house {primary_house}, shifting "
            f"{material['core']} into {HOUSE_NAMES[primary_house]}."
        )
        opportunity = f"{material['opportunity']}; {house_material['opportunity']}"
        risk = f"{material['risk']}; {house_material['risk']}"
    elif event.kind == "station":
        planet = planets[0]
        material = PLANET_MEANINGS[planet]
        meaning = (
            f"{planet}'s station concentrates attention in house {primary_house}. "
            f"What was moving normally becomes a review, delay, release or decision point."
        )
        opportunity = f"{material['opportunity']}; {house_material['action']}"
        risk = material["risk"]
    elif event.kind == "eclipse":
        meaning = (
            f"A high-amplitude turning point activates house {primary_house}: "
            f"{HOUSE_NAMES[primary_house]}. Results may unfold over months rather than one day."
        )
        opportunity = house_material["opportunity"]
        risk = house_material["risk"]
    elif event.kind == "lunation":
        meaning = (
            f"The lunar cycle activates house {primary_house}: {HOUSE_NAMES[primary_house]}."
        )
        opportunity = house_material["opportunity"]
        risk = house_material["risk"]
    else:
        meaning = event.detail
        opportunity = house_material["opportunity"]
        risk = house_material["risk"]

    return {
        "meaning": meaning,
        "opportunity": opportunity,
        "risk": risk,
        "strategy": house_material["action"],
    }


def convergence_interpretation(convergence: Convergence) -> dict:
    planets = set(convergence.planets)
    houses = list(convergence.houses)
    house_counts = Counter(house for event in convergence.events for house in event.houses)
    dominant_houses = [house for house, _ in house_counts.most_common(3)]
    combination_matches = _convergence_combinations(convergence)

    if combination_matches:
        title = " + ".join(match[1]["title"] for match in combination_matches[:2])
        meaning_parts = [match[1]["meaning"] for match in combination_matches[:2]]
        opportunity_parts = [match[1]["opportunity"] for match in combination_matches[:2]]
        risk_parts = [match[1]["risk"] for match in combination_matches[:2]]
    else:
        title = convergence.title
        meaning_parts = [
            "Several high-importance events overlap, so no single transit should be interpreted in isolation."
        ]
        opportunity_parts = []
        risk_parts = []

    house_text = "; ".join(
        f"house {house} ({HOUSE_NAMES[house]})" for house in dominant_houses
    )
    meaning_parts.append(
        f"The repeated pressure falls mainly on {house_text}. "
        "The meaning comes from the interaction between these fields, not from a simple good-or-bad label."
    )

    opportunity_parts.extend(HOUSE_STRATEGY[house]["opportunity"] for house in dominant_houses[:2])
    risk_parts.extend(HOUSE_STRATEGY[house]["risk"] for house in dominant_houses[:2])

    # Strategic sequence uses event chronology.
    ordered = sorted(convergence.events, key=lambda event: event.event_date)
    first = ordered[0]
    strongest = max(ordered, key=lambda event: event.importance)
    last = ordered[-1]

    strategy = (
        f"First respond to {first.title}; then use the peak around {strongest.title}; "
        f"finally consolidate after {last.title}. "
        f"The practical rule is: {HOUSE_STRATEGY[dominant_houses[0]]['action']}."
    )

    return {
        "title": title,
        "meaning": " ".join(meaning_parts),
        "opportunity": "; ".join(dict.fromkeys(opportunity_parts)),
        "risk": "; ".join(dict.fromkeys(risk_parts)),
        "strategy": strategy,
        "dominant_houses": dominant_houses,
    }


def retrograde_interpretation(cycle: RetrogradeCycle) -> dict:
    material = RETROGRADE_MEANINGS[cycle.planet]
    house_materials = [HOUSE_STRATEGY[house] for house in cycle.houses]
    houses_text = ", ".join(
        f"house {house} ({HOUSE_NAMES[house]})" for house in cycle.houses
    )
    return {
        "meaning": (
            f"{cycle.planet} reverses through {houses_text}. "
            f"The cycle reviews {material['review']}."
        ),
        "risk": (
            f"{material['risk']}. "
            + " ".join(item["risk"] for item in house_materials[:2])
        ),
        "best_use": (
            f"{material['best_use']}. "
            + " ".join(item["action"] for item in house_materials[:2])
        ),
        "implementation": (
            "Use the pre-shadow to identify the issue, the retrograde to revise it, "
            "the direct station to decide, and the post-shadow to implement the corrected version."
        ),
    }


def sky_table(positions: dict[str, Position], houses: dict[str, int]) -> str:
    lines = ["| Body | Position | House |", "|---|---:|---:|"]
    for planet in [
        "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
        "Saturn", "Uranus", "Neptune", "Pluto", "True Node",
    ]:
        lines.append(f"| {planet} | {positions[planet].label()} | {houses[planet]} |")
    return "\n".join(lines)


def daily_report(
    sign: str,
    d: date,
    timezone_name: str,
    source_note: str | None = None,
) -> dict:
    positions = positions_for_date(d, timezone_name)
    houses = house_map(positions, sign)
    aspects = detect_aspects(positions, include_moon=True)
    daily_events = period_events(d, d, sign, timezone_name)

    year_events = period_events(date(d.year, 1, 1), date(d.year, 12, 31), sign, timezone_name)
    year_convergences = convergence_points(year_events, maximum=9)
    active_year_convergence = next(
        (
            convergence for convergence in year_convergences
            if convergence.start_date - timedelta(days=14) <= d <= convergence.end_date + timedelta(days=14)
        ),
        None,
    )

    month_start = date(d.year, d.month, 1)
    if d.month == 12:
        month_end = date(d.year, 12, 31)
    else:
        month_end = date(d.year, d.month + 1, 1) - timedelta(days=1)
    month_events = period_events(month_start, month_end, sign, timezone_name)
    month_convergences = convergence_points(month_events, maximum=4)
    active_month_convergence = next(
        (
            convergence for convergence in month_convergences
            if convergence.start_date - timedelta(days=5) <= d <= convergence.end_date + timedelta(days=5)
        ),
        None,
    )

    top_aspects = aspects[:5]
    sun_house = houses["Sun"]
    moon_house = houses["Moon"]

    aspect_lines = []
    for aspect in top_aspects:
        aspect_lines.append(
            f"- **{aspect.planet1} {aspect.name} {aspect.planet2}** "
            f"(orb {aspect.orb:.2f}°): houses {houses[aspect.planet1]} and {houses[aspect.planet2]}."
        )

    context_parts = []
    if active_year_convergence:
        material = convergence_interpretation(active_year_convergence)
        context_parts.append(
            f"**Annual background:** {material['title']}. {material['meaning']}"
        )
    if active_month_convergence:
        material = convergence_interpretation(active_month_convergence)
        context_parts.append(
            f"**Monthly background:** {material['title']}. {material['strategy']}"
        )
    if not context_parts:
        context_parts.append(
            f"The wider period is dominated by house {sun_house}: {HOUSE_NAMES[sun_house]}."
        )

    dominant_aspect = top_aspects[0] if top_aspects else None
    if dominant_aspect:
        p1 = PLANET_MEANINGS[dominant_aspect.planet1]
        p2 = PLANET_MEANINGS[dominant_aspect.planet2]
        theme = (
            f"{dominant_aspect.planet1} {dominant_aspect.name} {dominant_aspect.planet2} "
            f"combines {p1['core']} with {p2['core']}."
        )
    else:
        theme = "No single major aspect dominates, so house emphasis matters more than exact timing."

    best_action = HOUSE_STRATEGY[sun_house]["action"]
    main_risk = HOUSE_STRATEGY[moon_house]["risk"]

    markdown = f"""# {sign} — {d.strftime('%A, %B %d, %Y')}

**Daily theme:** Advance {HOUSE_NAMES[sun_house]}, but manage {HOUSE_NAMES[moon_house]} consciously.

{source_note or ""}

## Wider context

{chr(10).join(context_parts)}

## House reference matrix

The selected sign becomes house 1 under the whole-sign method. The two houses most active today are marked below.

{house_reference_matrix(sign, {sun_house, moon_house})}

## Sky snapshot

{sky_table(positions, houses)}

## Dominant aspects

{chr(10).join(aspect_lines) if aspect_lines else "No major aspect is exact enough to dominate the day."}

## Interpretation

{theme}

The Sun places deliberate effort in house {sun_house}: **{HOUSE_NAMES[sun_house]}**.  
The Moon makes house {moon_house} more reactive: **{HOUSE_NAMES[moon_house]}**.

The day should therefore be read as a trigger inside the wider monthly and yearly pattern. A small conversation, payment, disagreement or opportunity may carry more meaning because it activates an already developing transition.

## Work and business

Use the strongest house emphasis to produce one finished, visible result. Do not substitute browsing, argument or planning for completion.

## Money

Keep revenue, cash received, fees, tax, debt and shared obligations separate. A promise, credit limit or pending payment is not secured cash.

## Relationships

State the practical issue directly. Written expectations are stronger than assumed expectations, especially when Mars, Uranus or Mercury activate relationship houses.

## Best move

{best_action.capitalize()}.

## Avoid

{main_risk.capitalize()}.

**Two-sentence horoscope:**  
{house_aware_conclusion(sign, sun_house, moon_house)}
"""
    return {
        "period": "daily",
        "sign": sign,
        "date": d.isoformat(),
        "markdown": markdown,
        "positions": serialize(positions),
        "aspects": serialize(aspects),
        "daily_events": serialize(daily_events),
        "active_year_convergence": serialize(active_year_convergence) if active_year_convergence else None,
        "active_month_convergence": serialize(active_month_convergence) if active_month_convergence else None,
    }


def _transition_section(index: int, event: Event) -> str:
    material = event_interpretation(event)
    house_text = ", ".join(
        f"{house} ({HOUSE_NAMES[house]})" for house in event.houses
    )
    return f"""## {index}. {event.title}

**Date:** {event.event_date.strftime('%B %d, %Y')}  
**Activated houses:** {house_text}

**Meaning:** {material['meaning']}

**Opportunity:** {material['opportunity']}

**Risk:** {material['risk']}

**Strategic response:** {material['strategy']}
"""


def _convergence_section(index: int, convergence: Convergence) -> str:
    material = convergence_interpretation(convergence)
    display_events = sorted(
        convergence.events,
        key=lambda event: (-event.importance, event.event_date),
    )[:12]
    display_events = sorted(display_events, key=lambda event: event.event_date)
    event_list = "\n".join(
        f"- {event.event_date.strftime('%b %d')}: {event.title}"
        for event in display_events
    )
    houses = ", ".join(
        f"{house} ({HOUSE_NAMES[house]})" for house in material["dominant_houses"]
    )
    return f"""## Convergence {index}: {material['title']}

**Window:** {_date_range_label(convergence.start_date, convergence.end_date)}  
**Dominant houses:** {houses}

{event_list}

**Combined meaning:** {material['meaning']}

**Opportunity:** {material['opportunity']}

**Risk:** {material['risk']}

**Sequence:** {material['strategy']}
"""


def _retrograde_section(cycle: RetrogradeCycle) -> str:
    material = retrograde_interpretation(cycle)
    shadow_start = cycle.shadow_start.strftime("%b %d %Y") if cycle.shadow_start else "not detected"
    shadow_end = cycle.shadow_end.strftime("%b %d %Y") if cycle.shadow_end else "not detected"
    return f"""### {cycle.planet} retrograde

- **Pre-shadow:** {shadow_start}
- **Retrograde station:** {cycle.retrograde_start.strftime('%b %d %Y')}
- **Direct station:** {cycle.direct_date.strftime('%b %d %Y')}
- **Post-shadow:** {shadow_end}
- **Signs:** {", ".join(cycle.signs)}
- **Houses:** {", ".join(map(str, cycle.houses))}

**Meaning:** {material['meaning']}

**Risk:** {material['risk']}

**Best use:** {material['best_use']}

**Cycle rule:** {material['implementation']}
"""



def _transition_priority(event: Event) -> float:
    slow = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    planets = set(event.planets)

    if event.kind == "eclipse":
        return 120 + event.importance
    if event.kind == "ingress":
        if planets & {"Pluto", "Neptune", "Uranus"}:
            return 115 + event.importance
        if planets & {"Saturn", "Jupiter"}:
            return 108 + event.importance
        return 65 + event.importance
    if event.kind == "station":
        if planets & slow:
            return 100 + event.importance
        return 70 + event.importance
    if event.kind == "aspect":
        if planets <= slow:
            return 110 + event.importance
        if planets & slow:
            return 60 + event.importance
        return 40 + event.importance
    if event.kind == "lunation":
        return 75 + event.importance
    return event.importance



def _yearly_strategic_chapters(
    sign: str,
    start: date,
    end: date,
    timezone_name: str,
    events: list[Event],
    cycles: list[RetrogradeCycle],
    convergences: list[Convergence],
) -> tuple[str, list[dict]]:
    """
    Produce nine connected strategic chapters. These are thematic, not merely
    the nine highest-scoring isolated events.
    """
    start_positions = positions_for_date(start, timezone_name)
    start_houses = house_map(start_positions, sign)
    chapters = []

    # 1. Opening Jupiter phase.
    jupiter_house = start_houses["Jupiter"]
    chapters.append({
        "title": "Opening growth phase",
        "meaning": (
            f"Jupiter begins the year in house {jupiter_house}: {HOUSE_NAMES[jupiter_house]}. "
            f"This is where confidence, opportunity and excess initially concentrate."
        ),
        "opportunity": HOUSE_STRATEGY[jupiter_house]["opportunity"],
        "risk": HOUSE_STRATEGY[jupiter_house]["risk"],
        "strategy": HOUSE_STRATEGY[jupiter_house]["action"],
    })

    # 2. Jupiter's most important change.
    jupiter_events = [
        event for event in events
        if "Jupiter" in event.planets and event.kind in {"ingress", "station", "aspect"}
    ]
    jupiter_ingress = next((event for event in jupiter_events if event.kind == "ingress"), None)
    chosen_jupiter = jupiter_ingress or (max(jupiter_events, key=_transition_priority) if jupiter_events else None)
    if chosen_jupiter:
        material = event_interpretation(chosen_jupiter)
        chapters.append({
            "title": chosen_jupiter.title,
            "meaning": material["meaning"],
            "opportunity": material["opportunity"],
            "risk": material["risk"],
            "strategy": material["strategy"],
            "date": chosen_jupiter.event_date.isoformat(),
        })
    else:
        chapters.append({
            "title": "Jupiter continuity",
            "meaning": "Jupiter does not make a major detected transition in the selected year.",
            "opportunity": PLANET_MEANINGS["Jupiter"]["opportunity"],
            "risk": PLANET_MEANINGS["Jupiter"]["risk"],
            "strategy": HOUSE_STRATEGY[jupiter_house]["action"],
        })

    # 3. Saturn-Neptune reality test, or Saturn's main structural chapter.
    saturn_neptune = next(
        (
            event for event in events
            if event.kind == "aspect"
            and set(event.planets) == {"Saturn", "Neptune"}
        ),
        None,
    )
    if saturn_neptune:
        material = event_interpretation(saturn_neptune)
        chapters.append({
            "title": "Saturn–Neptune reality test",
            "meaning": material["meaning"],
            "opportunity": material["opportunity"],
            "risk": material["risk"],
            "strategy": material["strategy"],
            "date": saturn_neptune.event_date.isoformat(),
        })
    else:
        saturn_event = max(
            (event for event in events if "Saturn" in event.planets),
            key=_transition_priority,
            default=None,
        )
        if saturn_event:
            material = event_interpretation(saturn_event)
            chapters.append({
                "title": saturn_event.title,
                "meaning": material["meaning"],
                "opportunity": material["opportunity"],
                "risk": material["risk"],
                "strategy": material["strategy"],
                "date": saturn_event.event_date.isoformat(),
            })

    # 4. Uranus disruption chapter.
    uranus_event = next(
        (event for event in events if event.kind == "ingress" and "Uranus" in event.planets),
        None,
    ) or max(
        (event for event in events if "Uranus" in event.planets),
        key=_transition_priority,
        default=None,
    )
    if uranus_event:
        material = event_interpretation(uranus_event)
        chapters.append({
            "title": uranus_event.title,
            "meaning": material["meaning"],
            "opportunity": material["opportunity"],
            "risk": material["risk"],
            "strategy": material["strategy"],
            "date": uranus_event.event_date.isoformat(),
        })

    # 5. Pluto's long-term pressure.
    midpoint = start + (end - start) // 2
    mid_positions = positions_for_date(midpoint, timezone_name)
    mid_houses = house_map(mid_positions, sign)
    pluto_house = mid_houses["Pluto"]
    pluto_event = max(
        (event for event in events if "Pluto" in event.planets and event.importance >= 7.0),
        key=_transition_priority,
        default=None,
    )
    pluto_extra = f" The strongest dated Pluto trigger is {pluto_event.title} on {pluto_event.event_date.strftime('%B %d')}." if pluto_event else ""
    chapters.append({
        "title": "Pluto’s long-term transformation",
        "meaning": (
            f"Pluto occupies house {pluto_house}: {HOUSE_NAMES[pluto_house]}. "
            f"This is where power, elimination and irreversible change operate beneath shorter cycles.{pluto_extra}"
        ),
        "opportunity": HOUSE_STRATEGY[pluto_house]["opportunity"],
        "risk": HOUSE_STRATEGY[pluto_house]["risk"],
        "strategy": HOUSE_STRATEGY[pluto_house]["action"],
    })

    # 6. Eclipse axis.
    eclipses = [event for event in events if event.kind == "eclipse"]
    eclipse_houses = sorted({house for event in eclipses for house in event.houses})
    if eclipses:
        eclipse_list = "; ".join(
            f"{event.event_date.strftime('%b %d')} {event.title} (house {event.houses[0]})"
            for event in eclipses
        )
        chapters.append({
            "title": "Eclipse turning points",
            "meaning": (
                f"The eclipse sequence activates houses {', '.join(map(str, eclipse_houses))}. "
                f"The dated turning points are: {eclipse_list}."
            ),
            "opportunity": "recognise which developments have consequences beyond the immediate week",
            "risk": "forcing certainty before the longer eclipse story has unfolded",
            "strategy": HOUSE_STRATEGY[eclipse_houses[0]]["action"],
        })

    # 7. Strongest convergence.
    if convergences:
        strongest_convergence = max(convergences, key=lambda item: item.score)
        material = convergence_interpretation(strongest_convergence)
        chapters.append({
            "title": f"Strongest convergence: {material['title']}",
            "meaning": material["meaning"],
            "opportunity": material["opportunity"],
            "risk": material["risk"],
            "strategy": material["strategy"],
            "window": f"{strongest_convergence.start_date.isoformat()} to {strongest_convergence.end_date.isoformat()}",
        })

    # 8. Constructive consolidation aspect.
    slow = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    constructive = [
        event for event in events
        if event.kind == "aspect"
        and event.polarity == "opportunity"
        and set(event.planets) <= slow
    ]
    chosen_constructive = max(constructive, key=_transition_priority, default=None)
    if chosen_constructive:
        material = event_interpretation(chosen_constructive)
        chapters.append({
            "title": f"Consolidation point: {chosen_constructive.title}",
            "meaning": material["meaning"],
            "opportunity": material["opportunity"],
            "risk": material["risk"],
            "strategy": material["strategy"],
            "date": chosen_constructive.event_date.isoformat(),
        })
    else:
        chapters.append({
            "title": "Consolidation strategy",
            "meaning": "No single slow-planet flow aspect dominates, so consolidation depends on sequence rather than one ideal date.",
            "opportunity": "stabilise the strongest development after its first results appear",
            "risk": "treating the opening as proof that the system is already durable",
            "strategy": "document the process, cost and responsibility before increasing scale",
        })

    # 9. Retrograde cycle strategy.
    if cycles:
        cycle_summary = "; ".join(
            f"{cycle.planet} {cycle.retrograde_start.strftime('%b %d %Y')}–{cycle.direct_date.strftime('%b %d %Y')} "
            f"(houses {','.join(map(str, cycle.houses))})"
            for cycle in cycles
        )
        chapters.append({
            "title": "Retrograde review periods",
            "meaning": f"The year contains these review cycles: {cycle_summary}.",
            "opportunity": "use each cycle to retrieve information, revise structure and correct direction",
            "risk": "treating every delay as disaster, or repeating the original action without revision",
            "strategy": "identify in pre-shadow, revise during retrograde, decide at the direct station and implement in post-shadow",
        })

    # Keep exactly nine when enough material exists.
    chapters = chapters[:9]
    while len(chapters) < 9:
        chapters.append({
            "title": f"Supporting chapter {len(chapters) + 1}",
            "meaning": "This supporting chapter is governed by the year's dominant house pattern.",
            "opportunity": HOUSE_STRATEGY[start_houses["Sun"]]["opportunity"],
            "risk": HOUSE_STRATEGY[start_houses["Moon"]]["risk"],
            "strategy": HOUSE_STRATEGY[start_houses["Sun"]]["action"],
        })

    sections = []
    for index, chapter in enumerate(chapters, 1):
        metadata = ""
        if chapter.get("date"):
            metadata = f"**Date:** {date.fromisoformat(chapter['date']).strftime('%B %d, %Y')}  \n"
        elif chapter.get("window"):
            metadata = f"**Window:** {chapter['window']}  \n"
        sections.append(
            f"""## Chapter {index}: {chapter['title']}

{metadata}**Meaning:** {chapter['meaning']}

**Opportunity:** {chapter['opportunity']}

**Risk:** {chapter['risk']}

**Strategic response:** {chapter['strategy']}
"""
        )

    return "\n".join(sections), chapters


def period_report(
    sign: str,
    start: date,
    end: date,
    timezone_name: str,
    period_name: str,
    source_note: str | None = None,
    transition_count: int = 9,
    nearest_city: str = "",
    main_focus: str = "General overview",
) -> dict:
    events = period_events(start, end, sign, timezone_name)
    cycles = retrograde_cycles(start, end, sign, timezone_name)
    convergences = convergence_points(events, maximum=9)
    houses = dominant_houses(start, end, sign, timezone_name, step_days=1 if (end-start).days < 50 else 4)

    strategic_chapter_markdown = ""
    strategic_chapters = []
    solar_convergence = None
    solar_year_chapters = []
    solar_year_section = ""
    monthly_arc = None
    inherited_events = []

    if (end - start).days < 50:
        solar_convergence = monthly_solar_convergence(
            sign,
            start.year,
            start.month,
            timezone_name,
            nearest_city=nearest_city,
            main_focus=main_focus,
        ).to_dict()
        inherited_events = period_events(
            start - timedelta(days=7),
            start - timedelta(days=1),
            sign,
            timezone_name,
        )
        monthly_arc = build_monthly_arc(
            sign=sign,
            start=start,
            end=end,
            label=period_name,
            events=events,
            inherited_events=inherited_events,
            retrograde_cycles=cycles,
            main_focus=main_focus,
        ).to_dict()
    else:
        year_chapters = yearly_solar_chapters(
            sign,
            start.year,
            timezone_name,
            nearest_city=nearest_city,
            main_focus=main_focus,
        )
        solar_year_chapters = [item.to_dict() for item in year_chapters]
        solar_year_section = yearly_solar_markdown(year_chapters)
        strategic_chapter_markdown, strategic_chapters = _yearly_strategic_chapters(
            sign, start, end, timezone_name, events, cycles, convergences
        )

    ranked_events = sorted(events, key=lambda event: (-_transition_priority(event), event.event_date))
    selected_events = []
    for event in ranked_events:
        if event.kind == "lunation" and sum(1 for item in selected_events if item.kind == "lunation") >= 2:
            continue
        if any(
            abs((event.event_date - item.event_date).days) <= 1 and set(event.planets) == set(item.planets)
            for item in selected_events
        ):
            continue
        selected_events.append(event)
        if len(selected_events) >= transition_count:
            break
    selected_events.sort(key=lambda event: event.event_date)

    primary_house = houses[0][0] if houses else 1
    secondary_house = houses[1][0] if len(houses) > 1 else primary_house

    transition_sections = "\n".join(
        _transition_section(index, event)
        for index, event in enumerate(selected_events, 1)
    )
    convergence_sections = "\n".join(
        _convergence_section(index, convergence)
        for index, convergence in enumerate(convergences, 1)
    )
    retrograde_sections = "\n".join(_retrograde_section(cycle) for cycle in cycles)

    strategic_chapters_section = (
        "# Nine strategic chapters\n\n" + strategic_chapter_markdown
        if strategic_chapter_markdown
        else ""
    )

    house_rows = ["| Rank | House | Main field |", "|---:|---:|---|"]
    for rank, (house, weight) in enumerate(houses, 1):
        house_rows.append(f"| {rank} | {house} | {HOUSE_NAMES[house]} |")

    markdown = f"""# {sign} — {period_name}

{source_note or ""}

## Core theme

House {primary_house} dominates: **{HOUSE_NAMES[primary_house]}**.  
House {secondary_house} is the secondary pressure point: **{HOUSE_NAMES[secondary_house]}**.

The period is not interpreted as a collection of isolated transits. The engine ranks major transitions, groups overlapping events into convergence points and carries the annual background into shorter forecasts.

## House reference matrix

The selected sign becomes house 1 under the whole-sign method. The dominant and secondary houses are marked below.

{house_reference_matrix(sign, {primary_house, secondary_house})}

## Dominant house matrix

{chr(10).join(house_rows)}

{solar_year_section}

{strategic_chapters_section}

# Major transitions

{transition_sections or "No major transition was detected."}

# Convergence points

{convergence_sections or "No high-density convergence met the threshold."}

# Retrograde cycles

{retrograde_sections or "No retrograde cycle overlaps the selected period."}

# Strategic conclusion

The winning sequence is:

1. build around house {primary_house}: {HOUSE_STRATEGY[primary_house]['opportunity']};
2. protect against house {secondary_house}: {HOUSE_STRATEGY[secondary_house]['risk']};
3. use convergence windows only after their shared financial, contractual and operational implications are visible;
4. treat retrogrades as revision cycles rather than automatic disaster;
5. consolidate the strongest opening after the relevant direct station or stabilising aspect.

**Two-sentence interpretation:**  
{house_aware_conclusion(sign, primary_house, secondary_house)}
"""

    return {
        "period": "monthly" if (end-start).days < 50 else "yearly",
        "sign": sign,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "label": period_name,
        "markdown": markdown,
        "events": serialize(events),
        "strategic_chapters": serialize(strategic_chapters),
        "major_transitions": serialize(selected_events),
        "retrograde_cycles": serialize(cycles),
        "convergences": serialize(convergences),
        "dominant_houses": [
            {"house": house, "topic": HOUSE_NAMES[house], "weight": weight}
            for house, weight in houses
        ],
        "solar_convergence": solar_convergence,
        "solar_year_chapters": solar_year_chapters,
        "monthly_arc": monthly_arc,
        "inherited_events": serialize(inherited_events),
        "nearest_city": nearest_city,
        "main_focus": main_focus,
    }
