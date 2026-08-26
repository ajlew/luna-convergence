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
    1: "The old identity no longer fits the direction opening ahead.",
    2: "Money is forcing a decision about what you will pay, charge or protect.",
    3: "A message, agreement or decision has reached the point where vagueness costs you.",
    4: "Home or family pressure is setting the limit on everything else.",
    5: "Attraction, pleasure or creative risk is asking for proof before commitment.",
    6: "The workload has reached the point where something must give.",
    7: "A relationship or agreement needs terms, not hints.",
    8: "Shared money, trust or obligation is exposing who carries the risk.",
    9: "A wider opportunity is becoming expensive before it is secure.",
    10: "Responsibility is rising faster than authority or reward.",
    11: "Old alliances are occupying space needed by the next direction.",
    12: "Something unfinished is draining capacity behind the scenes.",
}

HOUSE_IF_IGNORED = {
    1: "Leave this untouched and other people keep defining a version of you that the next phase has already outgrown.",
    2: "Leave it alone and extra value gets absorbed by extra cost, obligation or under-pricing.",
    3: "Leave it vague and the silence becomes the decision.",
    4: "Ignore the private strain and it keeps setting the ceiling on public progress.",
    5: "Leave it untested and excitement gets mistaken for proof.",
    6: "Carry everything and overload becomes the new normal.",
    7: "Leave the terms undefined and the temporary arrangement hardens into the relationship or contract you actually have.",
    8: "Leave the dependence hidden and someone else gains more leverage over the outcome.",
    9: "Commit too early and the bigger possibility starts costing money, time or freedom before it has earned the investment.",
    10: "Accept the load unchanged and extra responsibility becomes permanent before authority, recognition or compensation catches up.",
    11: "Keep every old alliance and they consume the space needed by the next direction.",
    12: "Ignore the hidden drain and fatigue, fear or unfinished business keeps making decisions from the shadows.",
}

HOUSE_MOVE = {
    1: "Choose the direction first. Let approval catch up later.",
    2: "Name the number. Keep the gain only if it buys more security or control.",
    3: "Get the fact, answer or agreement into writing. Then act.",
    4: "Fix the private base before expanding the public load.",
    5: "Make behaviour prove the promise before you enlarge the commitment.",
    6: "Cut the unsustainable part before you accept another responsibility.",
    7: "State the terms. Judge the response, not the charm.",
    8: "Put ownership, debt, trust and exit conditions on the table before committing.",
    9: "Price the larger possibility before you build your life around it.",
    10: "Tie every new responsibility to authority, compensation, ownership or a visible result.",
    11: "Back the people and plans that widen the future. Reduce access for the rest.",
    12: "Remove the hidden drain before forcing a visible answer.",
}

PLANET_ROLE = {
    "Jupiter": {
        "pressure": "Opportunity is widening in {area}. More is available now, but excess can turn the advantage into a burden.",
        "risk": "Say yes to everything and expansion turns into waste, cost or overload.",
        "leverage": "Take the opening that increases resources, reach or future options. Refuse the cost that does not improve your position.",
    },
    "Saturn": {
        "pressure": "The terms are hardening in {area}. What looked temporary is becoming measurable and binding.",
        "risk": "Responsibility can become permanent before the reward, authority or exit terms are settled.",
        "leverage": "Set scope, cost, authority, timing and exit conditions before the structure hardens.",
    },
    "Uranus": {
        "pressure": "The old arrangement is losing stability in {area}. A different route is opening.",
        "risk": "A sudden reaction can destroy useful options before the replacement is ready.",
        "leverage": "Keep the exit open, test the alternative and move when the new route proves itself.",
    },
    "Neptune": {
        "pressure": "Important facts remain blurred in {area}. The story is moving faster than the proof.",
        "risk": "Hope, fear or idealisation can hide the real cost until commitment narrows the exit.",
        "leverage": "Verify the number, date, promise, ownership and obligation before you bind yourself.",
    },
    "Pluto": {
        "pressure": "Control is shifting in {area}. Dependence and leverage now matter more than appearances.",
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
    timing: str
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
    force_meta: dict[str, dict[str, object]] = {}

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

        station_date = next_station[0] if next_station else None
        station_kind = next_station[1] if next_station else ""
        ingress_is_first = bool(next_ingress and (station_date is None or next_ingress <= station_date))

        if cycle:
            current_phase = (
                f"The review phase intensified when {planet} turned retrograde on "
                f"{human_date(cycle.retrograde_start)} and changes direction on {human_date(cycle.direct_date)}."
            )
        elif ingress_is_first and next_ingress:
            current_phase = f"The present phase changes when {planet} leaves this sign on {human_date(next_ingress)}."
        elif next_station:
            current_phase = (
                f"The next review point arrives when {planet} turns {station_kind} on {human_date(station_date)}."
            )
        else:
            current_phase = "This long current holds its direction inside the next 18 months."

        if ingress_is_first and next_ingress:
            next_position = positions_for_date(next_ingress, timezone_name)[planet]
            changes = (
                f"The next phase starts on {human_date(next_ingress)} when {planet} moves into {next_position.sign}."
            )
        elif next_station:
            changes = f"The next phase starts on {human_date(station_date)} when {planet} turns {station_kind}."
        else:
            changes = "No station or durable sign exit changes this long current inside the next 18 months."

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

        force_meta[planet] = {
            "next_station": next_station,
            "next_ingress": next_ingress,
            "next_change_date": next_ingress if ingress_is_first else station_date,
            "next_change_kind": "sign" if ingress_is_first else (station_kind if next_station else ""),
            "house": house,
        }

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
        problem += f" This now reaches {HOUSE_NAMES[secondary_house]}."

    # Month-end never cuts off a live condition. The next station is the first
    # material change; the sign exit is the slower structural shift. We report
    # both so the reader can distinguish an immediate turn from a long background.
    change_candidates: list[tuple[date, str, str]] = []
    related_exit_candidates: list[tuple[date, str]] = []
    related_without_exit: list[str] = []
    selected_planets = {force.planet for force in selected}
    for force in selected:
        meta = force_meta.get(force.planet, {})
        change_date = meta.get("next_change_date")
        change_kind = str(meta.get("next_change_kind") or "")
        if change_date and change_date > end:
            change_candidates.append((change_date, force.planet, change_kind))
        if force.house in {primary_house, secondary_house}:
            ingress = meta.get("next_ingress")
            if ingress:
                related_exit_candidates.append((ingress, force.planet))
            else:
                related_without_exit.append(force.planet)

    timing_parts = [f"Month-end is not the finish line for this condition."]
    if change_candidates:
        change_date, change_planet, change_kind = min(change_candidates, key=lambda item: item[0])
        if change_kind == "sign":
            next_position = positions_for_date(change_date, timezone_name)[change_planet]
            timing_parts.append(
                f"The next material change arrives on {human_date(change_date)} when {change_planet} moves into {next_position.sign}."
            )
        else:
            timing_parts.append(
                f"The next material change arrives on {human_date(change_date)} when {change_planet} turns {change_kind}."
            )
    if related_without_exit:
        names = ", ".join(related_without_exit[:2])
        timing_parts.append(
            f"The wider background carried by {names} remains in the same life area beyond the next three years; the immediate phase changes sooner, but the underlying theme does not fully leave."
        )
    elif related_exit_candidates:
        exit_date, exit_planet = max(related_exit_candidates, key=lambda item: item[0])
        timing_parts.append(
            f"The longer structure does not fully leave this area before {human_date(exit_date)}, when {exit_planet} makes its durable sign exit."
        )
    else:
        timing_parts.append("The immediate trigger can pass before the larger background does; judge the next station before calling the problem finished.")

    return ProblemHorizon(
        problem=problem,
        if_ignored=HOUSE_IF_IGNORED[primary_house],
        highest_leverage_move=HOUSE_MOVE[primary_house],
        timing=" ".join(timing_parts),
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
        return "This trigger is short-lived. Judge it by what remains after the immediate pressure passes."
    position = positions_for_date(reference, timezone_name)[planet]
    house = _native_house(sign, position.sign_index)
    area = HOUSE_NAMES[house]
    next_station = _find_next_station(planet, reference, timezone_name)
    next_ingress = _find_final_exit(planet, reference, timezone_name)

    parts = [f"{planet} keeps {area} in the long cycle."]
    station_date = next_station[0] if next_station else None
    if next_ingress and (station_date is None or next_ingress <= station_date):
        next_position = positions_for_date(next_ingress, timezone_name)[planet]
        parts.append(f"The next change arrives {human_date(next_ingress)} when {planet} moves into {next_position.sign}.")
    elif next_station:
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
