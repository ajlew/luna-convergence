from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from functools import lru_cache

from astrology_engine import (
    HOUSE_NAMES,
    SIGNS,
    Event,
    RetrogradeCycle,
    positions_for_date,
    whole_sign_house,
)
from date_display import human_date


SLOW_PLANETS = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")

HOUSE_PROBLEM = {
    1: "Your direction is changing faster than the identity built around the old one.",
    2: "Money, price and security are forcing a real value decision.",
    3: "A message, contract or decision cannot stay vague.",
    4: "Home or family pressure is setting the limit on everything else.",
    5: "Desire, romance or creative risk needs proof before commitment.",
    6: "The workload is testing what your system can actually sustain.",
    7: "A relationship or agreement is asking for terms, not hints.",
    8: "Shared money, trust or obligation is exposing who carries the risk.",
    9: "A wider opportunity is demanding a cost, route and destination.",
    10: "Responsibility and visibility are rising together.",
    11: "The future depends on which people and plans still deserve access.",
    12: "Unfinished pressure is consuming capacity behind the scenes.",
}

HOUSE_IF_IGNORED = {
    1: "Do nothing and other people keep defining the version of you that the next phase has already outgrown.",
    2: "Do nothing and extra value gets absorbed by extra cost, obligation or under-pricing.",
    3: "Do nothing and ambiguity becomes the decision by default.",
    4: "Do nothing and the private strain keeps setting the ceiling on public progress.",
    5: "Do nothing and excitement gets mistaken for proof.",
    6: "Do nothing and overload becomes the new normal.",
    7: "Do nothing and an undefined arrangement hardens into the relationship or contract you actually have.",
    8: "Do nothing and dependence gives someone else more leverage over the outcome.",
    9: "Do nothing and the bigger possibility starts costing money, time or freedom before it has earned the investment.",
    10: "Do nothing and extra responsibility becomes permanent before authority, recognition or compensation catches up.",
    11: "Do nothing and old alliances keep consuming space needed by the next direction.",
    12: "Do nothing and private fatigue, fear or unfinished business keeps making decisions from the shadows.",
}

HOUSE_MOVE = {
    1: "Choose the direction first. Make approval secondary.",
    2: "Name the number. Keep the gain only if it improves security or control.",
    3: "Get the fact, answer or agreement into words before acting on assumptions.",
    4: "Repair the private base before expanding the public load.",
    5: "Let behaviour prove the promise before you enlarge the commitment.",
    6: "Cut the unsustainable part before adding another responsibility.",
    7: "State the terms. Judge the response, not the charm.",
    8: "Make ownership, debt, trust and exit conditions visible before committing.",
    9: "Price the larger possibility before you build your life around it.",
    10: "Tie responsibility to authority, compensation, ownership or a visible result.",
    11: "Back the people and plans that increase future options; reduce access for the rest.",
    12: "Remove the hidden drain before forcing a visible answer.",
}

PLANET_ROLE = {
    "Jupiter": {
        "pressure": "Opportunity is expanding in {area}. More is available, but more is not automatically better.",
        "risk": "Expansion turns into waste when every opening receives the same yes.",
        "leverage": "Use the expansion to increase resources, reach or future options without locking in unnecessary cost.",
    },
    "Saturn": {
        "pressure": "The terms are hardening in {area}. What was temporary is becoming measurable and binding.",
        "risk": "Responsibility can become permanent before the reward, authority or exit terms are settled.",
        "leverage": "Define scope, cost, authority, timing and exit conditions before the structure hardens.",
    },
    "Uranus": {
        "pressure": "The old arrangement is losing stability in {area}. A different route is becoming possible.",
        "risk": "A sudden reaction can destroy useful options before the replacement is ready.",
        "leverage": "Keep the exit open, test the alternative and move when the new route proves itself.",
    },
    "Neptune": {
        "pressure": "Important facts remain blurred in {area}. The story is moving faster than the proof.",
        "risk": "Hope, fear or idealisation can hide the real cost until commitment narrows the exit.",
        "leverage": "Verify the number, date, promise, ownership and practical obligation before binding yourself.",
    },
    "Pluto": {
        "pressure": "Control is shifting in {area}. Dependence and leverage matter more than appearances.",
        "risk": "Hidden dependence can give another person, institution or obligation control over the result.",
        "leverage": "Identify who owns the resource, who can say no and what becomes difficult to reverse.",
    },
}


@dataclass(frozen=True)
class StrategicForce:
    planet: str
    house: int
    area: str
    score: float
    problem: str
    if_ignored: str
    leverage: str
    active_since: str
    current_phase: str
    peak: str
    changes: str
    structural_shift: str


@dataclass(frozen=True)
class ProblemHorizon:
    problem: str
    if_ignored: str
    highest_leverage_move: str
    horizon_rule: str
    forces: tuple[StrategicForce, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _native_house(sign: str, planet_sign_index: int) -> int:
    return whole_sign_house(planet_sign_index, SIGNS.index(sign))


@lru_cache(maxsize=2048)
def _find_previous_ingress(
    planet: str,
    reference: date,
    timezone_name: str,
    *,
    maximum_days: int = 1100,
) -> date | None:
    current_sign = positions_for_date(reference, timezone_name)[planet].sign_index
    cursor = reference - timedelta(days=7)
    floor = reference - timedelta(days=maximum_days)
    while cursor >= floor:
        if positions_for_date(cursor, timezone_name)[planet].sign_index != current_sign:
            day = cursor
            while day <= reference:
                if positions_for_date(day, timezone_name)[planet].sign_index == current_sign:
                    return day
                day += timedelta(days=1)
            return None
        cursor -= timedelta(days=7)
    return None


@lru_cache(maxsize=2048)
def _find_next_ingress(
    planet: str,
    reference: date,
    timezone_name: str,
    *,
    maximum_days: int = 1095,
) -> date | None:
    current_sign = positions_for_date(reference, timezone_name)[planet].sign_index
    cursor = reference + timedelta(days=7)
    ceiling = reference + timedelta(days=maximum_days)
    previous = reference
    while cursor <= ceiling:
        if positions_for_date(cursor, timezone_name)[planet].sign_index != current_sign:
            day = previous + timedelta(days=1)
            while day <= cursor:
                if positions_for_date(day, timezone_name)[planet].sign_index != current_sign:
                    return day
                day += timedelta(days=1)
            return None
        previous = cursor
        cursor += timedelta(days=7)
    return None




@lru_cache(maxsize=2048)
def _find_final_exit(
    planet: str,
    reference: date,
    timezone_name: str,
    *,
    maximum_days: int = 1095,
    persistence_days: int = 180,
) -> date | None:
    """Return the first exit from the current sign that stays out for persistence_days."""
    original_sign = positions_for_date(reference, timezone_name)[planet].sign_index
    ceiling = reference + timedelta(days=maximum_days)
    cursor = reference + timedelta(days=7)
    previous = reference
    candidate: date | None = None

    while cursor <= ceiling:
        sign_now = positions_for_date(cursor, timezone_name)[planet].sign_index
        if sign_now == original_sign:
            candidate = None
        else:
            if candidate is None:
                day = previous + timedelta(days=1)
                while day <= cursor:
                    if positions_for_date(day, timezone_name)[planet].sign_index != original_sign:
                        candidate = day
                        break
                    day += timedelta(days=1)
            if candidate and (cursor - candidate).days >= persistence_days:
                return candidate
        previous = cursor
        cursor += timedelta(days=7)
    return None

@lru_cache(maxsize=2048)
def _find_next_station(
    planet: str,
    reference: date,
    timezone_name: str,
    *,
    maximum_days: int = 550,
) -> tuple[date, str] | None:
    previous = positions_for_date(reference, timezone_name)[planet]
    cursor = reference + timedelta(days=1)
    ceiling = reference + timedelta(days=maximum_days)
    while cursor <= ceiling:
        current = positions_for_date(cursor, timezone_name)[planet]
        if previous.speed >= 0 > current.speed:
            return cursor, "retrograde"
        if previous.speed < 0 <= current.speed:
            return cursor, "direct"
        previous = current
        cursor += timedelta(days=1)
    return None


def _cycle_for_planet(
    planet: str,
    cycles: list[RetrogradeCycle],
    reference: date,
) -> RetrogradeCycle | None:
    for cycle in cycles:
        if cycle.planet == planet and cycle.retrograde_start <= reference <= cycle.direct_date:
            return cycle
    return None


def _peak_for_planet(planet: str, events: list[Event]) -> str:
    candidates = [event for event in events if planet in event.planets]
    if not candidates:
        return "No single date owns this pressure; it stays in the background throughout the month."
    chosen = max(candidates, key=lambda event: (event.importance, -abs(len(event.houses) - 1)))
    return f"{human_date(chosen.event_date)} — {chosen.title}."


def _force_score(
    planet: str,
    house: int,
    events: list[Event],
    ranked_houses: list[int],
    primary_house: int,
    secondary_house: int,
) -> float:
    score = 0.0
    if house == primary_house:
        score += 5.0
    elif house == secondary_house:
        score += 3.5
    elif house in ranked_houses[:5]:
        score += max(0.8, 2.5 - ranked_houses.index(house) * 0.35)
    score += min(
        4.0,
        sum(max(0.0, float(event.importance) - 5.0) * 0.35 for event in events if planet in event.planets),
    )
    return round(score, 2)


def build_problem_horizon(
    *,
    sign: str,
    start: date,
    end: date,
    timezone_name: str,
    events: list[Event],
    retrograde_cycles: list[RetrogradeCycle],
    dominant_houses: list[tuple[int, float]],
    monthly_arc: dict | None,
) -> ProblemHorizon:
    arc = monthly_arc or {}
    ranked_houses = [int(house) for house, _ in dominant_houses]
    primary_house = int(arc.get("primary_house") or (ranked_houses[0] if ranked_houses else 1))
    secondary_house = int(
        arc.get("secondary_house")
        or (ranked_houses[1] if len(ranked_houses) > 1 else primary_house)
    )

    midpoint = start + timedelta(days=max(0, (end - start).days // 2))
    midpoint_positions = positions_for_date(midpoint, timezone_name)
    forces: list[StrategicForce] = []

    for planet in SLOW_PLANETS:
        position = midpoint_positions[planet]
        house = _native_house(sign, position.sign_index)
        score = _force_score(
            planet,
            house,
            events,
            ranked_houses,
            primary_house,
            secondary_house,
        )
        if score < 1.25:
            continue

        area = HOUSE_NAMES[house]
        role = PLANET_ROLE[planet]
        previous_ingress = _find_previous_ingress(planet, midpoint, timezone_name)
        next_ingress = _find_final_exit(planet, end, timezone_name)
        next_station = _find_next_station(planet, end, timezone_name)
        cycle = _cycle_for_planet(planet, retrograde_cycles, midpoint)

        active_since = (
            f"{planet} entered this area on {human_date(previous_ingress)}."
            if previous_ingress
            else f"{planet} was already active here before this report window."
        )

        if cycle:
            current_phase = (
                f"The review phase intensified when {planet} turned retrograde on "
                f"{human_date(cycle.retrograde_start)} and changes direction on {human_date(cycle.direct_date)}."
            )
        elif next_station:
            station_date, station_kind = next_station
            current_phase = (
                f"The next review point arrives when {planet} turns {station_kind} on {human_date(station_date)}."
            )
        else:
            current_phase = "No station changes this background inside the next 18 months."

        if next_station:
            station_date, station_kind = next_station
            changes = f"The pressure changes on {human_date(station_date)} when {planet} turns {station_kind}."
        else:
            changes = "No station changes the direction inside the next 18 months."

        if next_ingress:
            new_position = positions_for_date(next_ingress, timezone_name)[planet]
            new_house = _native_house(sign, new_position.sign_index)
            structural_shift = (
                f"The structural emphasis finally leaves this area on {human_date(next_ingress)}, "
                f"when {planet} moves into {new_position.sign} and shifts the long-cycle emphasis to {HOUSE_NAMES[new_house]} without an immediate return pass."
            )
        else:
            structural_shift = (
                f"This background does not leave {area} inside the next three years; "
                "treat it as a long-cycle condition rather than a one-month problem."
            )

        forces.append(
            StrategicForce(
                planet=planet,
                house=house,
                area=area,
                score=score,
                problem=role["pressure"].format(area=area),
                if_ignored=role["risk"],
                leverage=role["leverage"],
                active_since=active_since,
                current_phase=current_phase,
                peak=_peak_for_planet(planet, events),
                changes=changes,
                structural_shift=structural_shift,
            )
        )

    forces.sort(key=lambda item: (-item.score, SLOW_PLANETS.index(item.planet)))
    selected = tuple(forces[:5])

    problem = HOUSE_PROBLEM[primary_house]
    if secondary_house != primary_house:
        problem += f" The consequence is spreading into {HOUSE_NAMES[secondary_house]}."

    return ProblemHorizon(
        problem=problem,
        if_ignored=HOUSE_IF_IGNORED[primary_house],
        highest_leverage_move=HOUSE_MOVE[primary_house],
        horizon_rule=(
            "A warning does not end at the page boundary. Luna follows the active condition until it changes, "
            "even when the next decisive station or structural shift falls next month or next year."
        ),
        forces=selected,
    )


def describe_slow_planet_horizon(
    planet: str,
    sign: str,
    reference: date,
    timezone_name: str,
) -> str:
    """Short customer-facing horizon line for Daily readings."""
    if planet not in SLOW_PLANETS:
        return "This trigger is short-lived; judge it by what remains after the immediate pressure separates."
    position = positions_for_date(reference, timezone_name)[planet]
    house = _native_house(sign, position.sign_index)
    area = HOUSE_NAMES[house]
    next_station = _find_next_station(planet, reference, timezone_name)
    next_ingress = _find_final_exit(planet, reference, timezone_name)

    parts = [f"{planet} keeps {area} in the long cycle."]
    if next_station:
        station_date, station_kind = next_station
        parts.append(f"The next change arrives {human_date(station_date)} when {planet} turns {station_kind}.")
    if next_ingress:
        new_position = positions_for_date(next_ingress, timezone_name)[planet]
        new_house = _native_house(sign, new_position.sign_index)
        parts.append(
            f"The structural emphasis finally leaves this area {human_date(next_ingress)} when {planet} shifts the long-cycle emphasis to {HOUSE_NAMES[new_house]} without an immediate return pass."
        )
    else:
        parts.append("This background does not leave the area inside the next three years.")
    return " ".join(parts)
