from __future__ import annotations
from luna_life_scenes import domain_command, human_focus, life_scene_line

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Iterable

from astrology_engine import HOUSE_NAMES, position_for_local_minute, positions_for_date
from natal_snapshot import NatalSnapshot, NatalPosition
from timing_insight import build_story_language
from major_event_registry import major_sky_events, period_priority_signals, personalize_major_signals


TRANSIT_PLANETS = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")

# Fast planets never become top-level annual stories. They can only reinforce a
# selected slow-planet arc as a short-lived supporting trigger. The Moon is
# deliberately excluded from the annual trigger layer.
FAST_TRIGGER_PLANETS = ("Sun", "Mercury", "Venus", "Mars")
FAST_TRIGGER_WEIGHTS = {
    "Sun": 1.15,
    "Mercury": 1.00,
    "Venus": 1.08,
    "Mars": 1.22,
}
FAST_TRIGGER_ASPECT_WEIGHTS = {
    "conjunction": 1.25,
    "opposition": 1.18,
    "square": 1.15,
    "trine": 1.05,
    "sextile": 1.00,
}
MAX_SUPPORTING_TRIGGERS = 3
ASPECT_ANGLES = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

# Deliberately tighter than Luna's daily inter-planet aspect orbs. This product
# is a personal timing map, so it favours fewer, cleaner natal activations.
TRANSIT_ORBS = {
    "Jupiter": 2.5,
    "Saturn": 2.2,
    "Uranus": 1.8,
    "Neptune": 1.6,
    "Pluto": 1.5,
}

TRANSIT_WEIGHTS = {
    "Jupiter": 1.8,
    "Saturn": 2.3,
    "Uranus": 2.5,
    "Neptune": 2.3,
    "Pluto": 2.7,
}

TARGET_WEIGHTS = {
    "Sun": 1.55,
    "Moon": 1.45,
    "Mercury": 1.05,
    "Venus": 1.25,
    "Mars": 1.2,
    "Jupiter": 0.95,
    "Saturn": 1.0,
    "Uranus": 0.82,
    "Neptune": 0.82,
    "Pluto": 0.9,
    "Ascendant": 1.65,
    "Midheaven": 1.7,
}

ASPECT_WEIGHTS = {
    "conjunction": 1.20,
    "opposition": 1.16,
    "square": 1.12,
    "trine": 1.00,
    "sextile": 0.86,
}

TARGET_DOMAINS = {
    "Sun": "identity, direction and visibility",
    "Moon": "home, belonging and emotional security",
    "Mercury": "decisions, communication, learning and agreements",
    "Venus": "relationships, money, value and attraction",
    "Mars": "action, conflict, energy and pursuit",
    "Jupiter": "growth, confidence, opportunity and belief",
    "Saturn": "commitment, standards, responsibility and limits",
    "Uranus": "freedom, independence and reinvention",
    "Neptune": "ideals, imagination, sensitivity and uncertainty",
    "Pluto": "power, trust, control and deep change",
    "Ascendant": "identity, presentation and personal direction",
    "Midheaven": "career, reputation, authority and public direction",
}

TRANSIT_FUNCTION = {
    "Jupiter": "expands the available space and tests whether growth is actually supportable",
    "Saturn": "adds weight, terms, limits and consequences until the structure becomes explicit",
    "Uranus": "breaks stale patterns and makes freedom, flexibility or reinvention harder to postpone",
    "Neptune": "softens certainty, enlarges imagination and tests whether the story survives verification",
    "Pluto": "concentrates power and exposes what can no longer be managed by keeping the old arrangement intact",
}

TRANSIT_MOVE = {
    "Jupiter": "Take the opening, but price the downside before expanding.",
    "Saturn": "Define the terms, responsibility and stopping point.",
    "Uranus": "Protect flexibility. Change the structure before the structure changes you.",
    "Neptune": "Slow interpretation down. Verify the evidence before acting on the story.",
    "Pluto": "Stop bargaining with the part of the situation that has already changed.",
}

TRANSIT_WATCH = {
    "Jupiter": "More can quietly become too much.",
    "Saturn": "Carrying an arrangement merely because it has history.",
    "Uranus": "Burning the bridge just to prove you are free.",
    "Neptune": "Confusing intensity, hope or fear with evidence.",
    "Pluto": "Trying to restore control by gripping harder.",
}

HEADLINE_OVERRIDES = {
    ("Jupiter", "Sun"): "THE HORIZON EXPANDS",
    ("Jupiter", "Moon"): "MORE SPACE CHANGES HOME",
    ("Jupiter", "Mercury"): "THE MESSAGE TRAVELS FURTHER",
    ("Jupiter", "Venus"): "VALUE WANTS MORE ROOM",
    ("Jupiter", "Mars"): "MOMENTUM GETS BACKING",
    ("Jupiter", "Jupiter"): "THE BET GETS BIGGER",
    ("Jupiter", "Saturn"): "THE STRUCTURE CAN GROW",
    ("Jupiter", "Uranus"): "THE FUTURE OPENS SIDEWAYS",
    ("Jupiter", "Neptune"): "BELIEF GETS A LONGER LEASH",
    ("Jupiter", "Pluto"): "POWER ATTRACTS SCALE",
    ("Jupiter", "Ascendant"): "THE WORLD MEETS A BIGGER VERSION",
    ("Jupiter", "Midheaven"): "THE DOOR GETS BIGGER",
    ("Saturn", "Sun"): "THE STANDARD GETS REAL",
    ("Saturn", "Moon"): "WHAT YOU CARRY GETS HEAVIER",
    ("Saturn", "Mercury"): "THE DECISION NEEDS TERMS",
    ("Saturn", "Venus"): "THE AGREEMENT GETS TESTED",
    ("Saturn", "Mars"): "DISCIPLINE BECOMES LEVERAGE",
    ("Saturn", "Jupiter"): "GROWTH MEETS THE LIMIT",
    ("Saturn", "Saturn"): "THE STRUCTURE AUDITS ITSELF",
    ("Saturn", "Uranus"): "FREEDOM MEETS THE RULE",
    ("Saturn", "Neptune"): "THE DREAM MEETS THE DEADLINE",
    ("Saturn", "Pluto"): "CONTROL MEETS CONSEQUENCE",
    ("Saturn", "Ascendant"): "THE OUTER SHELL HARDENS",
    ("Saturn", "Midheaven"): "AUTHORITY HAS A PRICE",
    ("Uranus", "Sun"): "THE OLD VERSION STOPS FITTING",
    ("Uranus", "Moon"): "HOME NEEDS MORE AIR",
    ("Uranus", "Mercury"): "THE OLD EXPLANATION BREAKS",
    ("Uranus", "Venus"): "ATTRACTION CHANGES FREQUENCY",
    ("Uranus", "Mars"): "ACTION BREAKS PATTERN",
    ("Uranus", "Jupiter"): "THE FUTURE JUMPS TRACKS",
    ("Uranus", "Saturn"): "THE RULEBOOK BREAKS",
    ("Uranus", "Uranus"): "FREEDOM RESETS ITSELF",
    ("Uranus", "Neptune"): "THE SIGNAL CHANGES",
    ("Uranus", "Pluto"): "POWER GETS DISRUPTED",
    ("Uranus", "Ascendant"): "YOUR NEXT VERSION BREAKS COVER",
    ("Uranus", "Midheaven"): "THE CAREER SCRIPT BREAKS OPEN",
    ("Neptune", "Sun"): "IDENTITY LOSES ITS HARD EDGE",
    ("Neptune", "Moon"): "FEELING FLOODS THE SIGNAL",
    ("Neptune", "Mercury"): "THE STORY NEEDS PROOF",
    ("Neptune", "Venus"): "CHEMISTRY IS NOT EVIDENCE",
    ("Neptune", "Mars"): "MOTIVE GETS HARDER TO READ",
    ("Neptune", "Jupiter"): "BELIEF OUTRUNS EVIDENCE",
    ("Neptune", "Saturn"): "THE BOUNDARY GETS POROUS",
    ("Neptune", "Uranus"): "THE FUTURE LOOKS STRANGER",
    ("Neptune", "Neptune"): "THE DREAM DOUBLES DOWN",
    ("Neptune", "Pluto"): "POWER HIDES IN THE FOG",
    ("Neptune", "Ascendant"): "THE IMAGE BLURS",
    ("Neptune", "Midheaven"): "THE CAREER STORY NEEDS PROOF",
    ("Pluto", "Sun"): "POWER CHANGES THE TERMS",
    ("Pluto", "Moon"): "WHAT YOU PROTECT CHANGES",
    ("Pluto", "Mercury"): "WORDS BECOME LEVERAGE",
    ("Pluto", "Venus"): "THE PRICE OF ATTACHMENT CHANGES",
    ("Pluto", "Mars"): "FORCE MEETS FORCE",
    ("Pluto", "Jupiter"): "THE STAKES GET BIGGER",
    ("Pluto", "Saturn"): "THE OLD STRUCTURE MEETS POWER",
    ("Pluto", "Uranus"): "DISRUPTION GOES DEEPER",
    ("Pluto", "Neptune"): "THE FOG HIDES A POWER MOVE",
    ("Pluto", "Pluto"): "THE DEEP PATTERN RETURNS",
    ("Pluto", "Ascendant"): "IDENTITY SHEDS A SKIN",
    ("Pluto", "Midheaven"): "THE POWER STRUCTURE MOVES",
}

GENERIC_HEADLINES = {
    "Jupiter": "THE FIELD GETS WIDER",
    "Saturn": "THE TERMS GET CLEARER",
    "Uranus": "THE PATTERN BREAKS OPEN",
    "Neptune": "CERTAINTY GETS THINNER",
    "Pluto": "THE POWER BALANCE CHANGES",
}


@dataclass(frozen=True)
class TransitHit:
    exact_date: date
    orb: float
    retrograde: bool
    exact_time: str | None = None
    pass_number: int = 1
    pass_label: str = "Initial activation"
    transit_longitude: float | None = None
    transit_sign: str = ""
    transit_degree: float | None = None


@dataclass(frozen=True)
class TransitPeriod:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class SupportingTrigger:
    trigger_planet: str
    aspect: str
    natal_target: str
    exact_date: date
    orb: float
    retrograde: bool
    exact_time: str | None = None
    activates_pass_number: int | None = None
    transit_longitude: float | None = None
    transit_sign: str = ""
    transit_degree: float | None = None

    @property
    def technical_label(self) -> str:
        return f"{self.trigger_planet} {self.aspect} natal {self.natal_target}"

    @property
    def activation_label(self) -> str:
        return f"{self.trigger_planet} activates the pattern"


@dataclass(frozen=True)
class TransitStory:
    transit_planet: str
    natal_target: str
    aspect: str
    natal_house: int | None
    score: float
    polarity: str
    headline: str
    summary: str
    scenarios: tuple[str, ...]
    insight: str
    question: str
    move: str
    watch: str
    periods: tuple[TransitPeriod, ...]
    hits: tuple[TransitHit, ...]
    supporting_triggers: tuple[SupportingTrigger, ...] = ()
    base_score: float | None = None
    exactness_bonus: float = 0.0
    overlap_count: int = 0
    natal_longitude: float | None = None
    natal_sign: str = ""
    natal_degree: float | None = None

    @property
    def first_date(self) -> date:
        return min(period.start_date for period in self.periods)

    @property
    def last_date(self) -> date:
        return max(period.end_date for period in self.periods)

    @property
    def pass_count(self) -> int:
        return len(self.hits)

    @property
    def is_multi_pass(self) -> bool:
        return len(self.hits) > 1


@dataclass(frozen=True)
class TimingMapReport:
    start_date: date
    end_date: date
    timezone_name: str
    stories: tuple[TransitStory, ...]
    major_games: int
    turning_points: int
    rule_changes: int
    major_sky_events: tuple[dict, ...] = ()
    personal_major_events: tuple[dict, ...] = ()


def _wrap180(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def _target_longitudes(natal_longitude: float, aspect: str) -> tuple[float, ...]:
    angle = ASPECT_ANGLES[aspect]
    first = (natal_longitude + angle) % 360.0
    second = (natal_longitude - angle) % 360.0
    if abs(_wrap180(first - second)) < 1e-7:
        return (first,)
    return (first, second)


def _refine_hit(
    *,
    transit_planet: str,
    target_longitude: float,
    timezone_name: str,
    start_day: date,
    start_minute: int,
    end_day: date,
    end_minute: int,
) -> TransitHit:
    """Refine a detected contact to the closest practical local minute.

    The 365-day scan stays daily for speed. Only a small window around a
    detected crossing or near-station minimum is resampled with Luna's existing
    Swiss-Ephemeris-backed minute helper.
    """
    day_span = (end_day - start_day).days
    first_offset = int(start_minute)
    last_offset = day_span * 1440 + int(end_minute)
    if last_offset < first_offset:
        raise ValueError("end of refinement window must not precede start")

    def sample(offset: int):
        local_day = start_day + timedelta(days=offset // 1440)
        minute_of_day = offset % 1440
        position = position_for_local_minute(
            local_day.isoformat(),
            timezone_name,
            minute_of_day,
            transit_planet,
        )
        error = abs(_wrap180(position.longitude - target_longitude))
        return error, local_day, minute_of_day, position

    coarse_offsets = list(range(first_offset, last_offset + 1, 30))
    if not coarse_offsets or coarse_offsets[-1] != last_offset:
        coarse_offsets.append(last_offset)

    coarse_candidates = [(sample(offset), offset) for offset in coarse_offsets]
    (_, best_offset) = min(coarse_candidates, key=lambda item: item[0][0])

    fine_start = max(first_offset, best_offset - 45)
    fine_end = min(last_offset, best_offset + 45)
    fine_candidates = [
        (sample(offset), offset)
        for offset in range(fine_start, fine_end + 1)
    ]
    (orb, local_day, minute_of_day, position), _ = min(
        fine_candidates,
        key=lambda item: item[0][0],
    )

    return TransitHit(
        exact_date=local_day,
        orb=round(orb, 4),
        retrograde=bool(position.retrograde),
        exact_time=f"{minute_of_day // 60:02d}:{minute_of_day % 60:02d}",
        transit_longitude=round(float(position.longitude), 6),
        transit_sign=str(getattr(position, "sign", "") or ""),
        transit_degree=round(float(getattr(position, "degree", 0.0) or 0.0), 6),
    )


def _periods_from_active(days: list[date], active: list[bool]) -> list[TransitPeriod]:
    periods: list[TransitPeriod] = []
    start: date | None = None
    last: date | None = None
    for day, is_active in zip(days, active):
        if is_active and start is None:
            start = day
        if is_active:
            last = day
        elif start is not None and last is not None:
            periods.append(TransitPeriod(start, last))
            start = None
            last = None
    if start is not None and last is not None:
        periods.append(TransitPeriod(start, last))
    return periods


def _merge_periods(periods: Iterable[TransitPeriod], gap_days: int = 2) -> tuple[TransitPeriod, ...]:
    ordered = sorted(periods, key=lambda item: item.start_date)
    if not ordered:
        return ()
    result = [ordered[0]]
    for item in ordered[1:]:
        previous = result[-1]
        if item.start_date <= previous.end_date + timedelta(days=gap_days + 1):
            result[-1] = TransitPeriod(previous.start_date, max(previous.end_date, item.end_date))
        else:
            result.append(item)
    return tuple(result)


def _dedupe_hits(hits: Iterable[TransitHit], minimum_gap_days: int = 3) -> tuple[TransitHit, ...]:
    ordered = sorted(
        hits,
        key=lambda item: (item.exact_date, item.exact_time or ""),
    )
    result: list[TransitHit] = []
    for hit in ordered:
        if result and abs((hit.exact_date - result[-1].exact_date).days) <= minimum_gap_days:
            if hit.orb < result[-1].orb:
                result[-1] = hit
            continue
        result.append(hit)
    return tuple(result)


def _label_transit_passes(hits: Iterable[TransitHit]) -> tuple[TransitHit, ...]:
    """Order and label repeated exact hits as one transit arc.

    The common three-pass sequence is:
      direct     -> Initial activation
      retrograde -> Retrograde return
      direct     -> Final pass

    A rolling 365-day report can begin or end in the middle of that sequence.
    Therefore the labels are derived from the motion actually visible in the
    calculated hits rather than inventing a missing pass outside the report.
    """
    ordered = sorted(
        hits,
        key=lambda item: (item.exact_date, item.exact_time or ""),
    )
    if not ordered:
        return ()

    labelled: list[TransitHit] = []
    for index, hit in enumerate(ordered):
        previous_hits = ordered[:index]
        is_last = index == len(ordered) - 1

        if index == 0:
            label = "Retrograde return" if hit.retrograde else "Initial activation"
        elif hit.retrograde:
            label = "Retrograde return"
        elif any(previous.retrograde for previous in previous_hits):
            label = "Final pass" if is_last else "Direct return"
        elif is_last:
            label = "Final pass"
        else:
            label = "Return pass"

        labelled.append(
            replace(
                hit,
                pass_number=index + 1,
                pass_label=label,
            )
        )
    return tuple(labelled)



def _date_in_periods(day: date, periods: Iterable[TransitPeriod]) -> bool:
    return any(period.start_date <= day <= period.end_date for period in periods)


def _dedupe_supporting_triggers(
    triggers: Iterable[SupportingTrigger],
    minimum_gap_days: int = 2,
) -> tuple[SupportingTrigger, ...]:
    """Remove duplicate detections of the same fast-planet contact."""
    ordered = sorted(
        triggers,
        key=lambda item: (
            item.trigger_planet,
            item.aspect,
            item.exact_date,
            item.exact_time or "",
        ),
    )
    result: list[SupportingTrigger] = []
    for trigger in ordered:
        comparable = next(
            (
                index
                for index in range(len(result) - 1, -1, -1)
                if result[index].trigger_planet == trigger.trigger_planet
                and result[index].aspect == trigger.aspect
                and abs((trigger.exact_date - result[index].exact_date).days) <= minimum_gap_days
            ),
            None,
        )
        if comparable is not None:
            if trigger.orb < result[comparable].orb:
                result[comparable] = trigger
            continue
        result.append(trigger)
    return tuple(sorted(result, key=lambda item: (item.exact_date, item.exact_time or "")))


def _select_supporting_triggers(
    story: TransitStory,
    triggers: Iterable[SupportingTrigger],
    maximum: int = MAX_SUPPORTING_TRIGGERS,
) -> tuple[SupportingTrigger, ...]:
    """Keep only the strongest short-lived activators of one main transit arc.

    Proximity to the main arc's exact passes leads the ranking. Planet/aspect
    weights then break ties. We prefer different fast planets so Mercury does
    not fill the card with several similar hits while Sun, Venus or Mars vanish.
    """
    if maximum <= 0 or not story.hits:
        return ()

    ranked: list[tuple[tuple, SupportingTrigger]] = []
    for trigger in triggers:
        if not _date_in_periods(trigger.exact_date, story.periods):
            continue
        nearest_hit = min(
            story.hits,
            key=lambda hit: abs((trigger.exact_date - hit.exact_date).days),
        )
        distance = abs((trigger.exact_date - nearest_hit.exact_date).days)
        attached = replace(
            trigger,
            activates_pass_number=getattr(nearest_hit, "pass_number", None),
        )
        rank = (
            distance,
            -FAST_TRIGGER_WEIGHTS.get(trigger.trigger_planet, 0.0),
            -FAST_TRIGGER_ASPECT_WEIGHTS.get(trigger.aspect, 0.0),
            trigger.orb,
            trigger.exact_date,
            trigger.exact_time or "",
        )
        ranked.append((rank, attached))

    ranked.sort(key=lambda item: item[0])
    selected: list[SupportingTrigger] = []
    used_planets: set[str] = set()

    # First pass: diversity across Sun / Mercury / Venus / Mars.
    for _, trigger in ranked:
        if trigger.trigger_planet in used_planets:
            continue
        selected.append(trigger)
        used_planets.add(trigger.trigger_planet)
        if len(selected) >= maximum:
            return tuple(sorted(selected, key=lambda item: (item.exact_date, item.exact_time or "")))

    # Second pass: fill any remaining slots with the next strongest trigger.
    for _, trigger in ranked:
        if trigger in selected:
            continue
        selected.append(trigger)
        if len(selected) >= maximum:
            break

    return tuple(sorted(selected, key=lambda item: (item.exact_date, item.exact_time or "")))


def _supporting_triggers_for_story(
    *,
    story: TransitStory,
    target: NatalPosition,
    days: list[date],
    trigger_positions: dict[str, list],
    timezone_name: str,
    maximum: int = MAX_SUPPORTING_TRIGGERS,
) -> tuple[SupportingTrigger, ...]:
    """Calculate fast-planet activators only inside one selected main arc.

    This deliberately does not create Sun/Mercury/Venus/Mars annual stories.
    The same five aspect geometries are scanned against the main arc's natal
    target, but minute refinement is only performed when the daily crossing is
    inside an active slow-planet window.
    """
    candidates: list[SupportingTrigger] = []

    for trigger_planet in FAST_TRIGGER_PLANETS:
        positions = trigger_positions[trigger_planet]
        for aspect in ASPECT_ANGLES:
            for target_longitude in _target_longitudes(target.longitude, aspect):
                errors = [_wrap180(position.longitude - target_longitude) for position in positions]

                for index in range(len(days) - 1):
                    if not (
                        _date_in_periods(days[index], story.periods)
                        or _date_in_periods(days[index + 1], story.periods)
                    ):
                        continue
                    e0, e1 = errors[index], errors[index + 1]
                    if abs(e0) > 20 or abs(e1) > 20:
                        continue
                    crossed = e0 == 0.0 or e1 == 0.0 or (e0 < 0 < e1) or (e1 < 0 < e0)
                    if not crossed:
                        continue
                    hit = _refine_hit(
                        transit_planet=trigger_planet,
                        target_longitude=target_longitude,
                        timezone_name=timezone_name,
                        start_day=days[index],
                        start_minute=12 * 60,
                        end_day=days[index + 1],
                        end_minute=12 * 60,
                    )
                    if _date_in_periods(hit.exact_date, story.periods):
                        candidates.append(
                            SupportingTrigger(
                                trigger_planet=trigger_planet,
                                aspect=aspect,
                                natal_target=target.planet,
                                exact_date=hit.exact_date,
                                orb=hit.orb,
                                retrograde=hit.retrograde,
                                exact_time=hit.exact_time,
                                transit_longitude=hit.transit_longitude,
                                transit_sign=hit.transit_sign,
                                transit_degree=hit.transit_degree,
                            )
                        )

                # Fast planets can also turn just short of exact. Preserve a
                # very close local minimum, mirroring the main transit scan.
                for index in range(1, len(days) - 1):
                    if not _date_in_periods(days[index], story.periods):
                        continue
                    current = abs(errors[index])
                    if not (
                        current <= 0.12
                        and current <= abs(errors[index - 1])
                        and current <= abs(errors[index + 1])
                    ):
                        continue
                    hit = _refine_hit(
                        transit_planet=trigger_planet,
                        target_longitude=target_longitude,
                        timezone_name=timezone_name,
                        start_day=days[index - 1],
                        start_minute=12 * 60,
                        end_day=days[index + 1],
                        end_minute=12 * 60,
                    )
                    if _date_in_periods(hit.exact_date, story.periods):
                        candidates.append(
                            SupportingTrigger(
                                trigger_planet=trigger_planet,
                                aspect=aspect,
                                natal_target=target.planet,
                                exact_date=hit.exact_date,
                                orb=hit.orb,
                                retrograde=hit.retrograde,
                                exact_time=hit.exact_time,
                                transit_longitude=hit.transit_longitude,
                                transit_sign=hit.transit_sign,
                                transit_degree=hit.transit_degree,
                            )
                        )

    return _select_supporting_triggers(
        story,
        _dedupe_supporting_triggers(candidates),
        maximum=maximum,
    )

def _polarity(transit_planet: str, aspect: str) -> str:
    if aspect in {"square", "opposition"}:
        return "pressure"
    if aspect in {"trine", "sextile"}:
        return "opportunity"
    if transit_planet == "Jupiter":
        return "opportunity"
    if transit_planet in {"Saturn", "Pluto"}:
        return "structural"
    return "mixed"


def _scenario_lines(target: NatalPosition, transit_planet: str, aspect: str) -> tuple[str, ...]:
    raw_domain = HOUSE_NAMES.get(target.house or 0, TARGET_DOMAINS.get(target.planet, target.planet.lower()))
    seed = f"{transit_planet}-{target.planet}-{aspect}-{target.house}"
    first = domain_command(raw_domain, seed)
    second = life_scene_line(raw_domain, seed_text=seed, count=1)

    if transit_planet == "Neptune":
        third = "Verify the promise, impression or fear before you let it make the decision."
    elif transit_planet == "Uranus":
        third = "Test more freedom before you destroy the structure that currently contains it."
    elif transit_planet == "Saturn":
        third = "Count the cost. Put the responsibility, deadline or boundary into explicit terms."
    elif transit_planet == "Jupiter":
        third = "Take the larger option only if it gives you more usable capacity, not just more activity."
    else:
        third = "Name the real power structure. Stop pretending neutrality will keep the old balance intact."
    return (first, second, third)


def _summary(target: NatalPosition, transit_planet: str, aspect: str) -> str:
    raw_domain = HOUSE_NAMES.get(target.house or 0, TARGET_DOMAINS.get(target.planet, target.planet.lower()))
    seed = f"summary-{transit_planet}-{target.planet}-{aspect}-{target.house}"

    if aspect in {"square", "opposition"}:
        relation = "Use the friction. Name the condition you can no longer leave vague."
    elif aspect in {"trine", "sextile"}:
        relation = "Use the support before it becomes background."
    else:
        relation = "Stop treating the issue as background noise."

    transit_line = {
        "Jupiter": "Use the extra room.",
        "Saturn": "Put the cost and responsibility into terms.",
        "Uranus": "Make more room before you break the structure.",
        "Neptune": "Make the story survive the facts.",
        "Pluto": "Name where the power actually sits.",
    }[transit_planet]
    return f"{transit_line} {domain_command(raw_domain, seed)} {relation}"


def _story_score(transit_planet: str, target: NatalPosition, aspect: str, hit_count: int) -> float:
    score = TRANSIT_WEIGHTS[transit_planet]
    score *= TARGET_WEIGHTS.get(target.planet, 1.0)
    score *= ASPECT_WEIGHTS[aspect]
    if target.planet in {"Ascendant", "Midheaven"}:
        score *= 1.12
    if target.house in {1, 4, 7, 10}:
        score *= 1.06
    score *= 1.0 + min(max(hit_count - 1, 0), 2) * 0.12
    return round(score, 3)


def _exactness_bonus(hits: Iterable[TransitHit]) -> float:
    """Small ranking lift for genuinely exact contacts.

    Step 3 refines hits to the closest practical local minute. Most true
    crossings therefore land extremely close to 0°, while station-near misses
    can remain a little wider. Exactness is a tie-breaker, not a replacement
    for planet/target/aspect importance.
    """
    values = [abs(float(hit.orb)) for hit in hits]
    if not values:
        return 0.0
    best = min(values)
    closeness = max(0.0, 1.0 - min(best, 0.12) / 0.12)
    return round(0.08 * closeness, 4)


def _stories_cluster(left: TransitStory, right: TransitStory, window_days: int = 21) -> bool:
    """Return True when two transit arcs peak in the same strategic window.

    We use exact-pass proximity rather than broad active-window overlap because
    slow-planet windows can last months. A 21-day peak window identifies a real
    concentration without making the whole year one permanent cluster.
    """
    return any(
        abs((left_hit.exact_date - right_hit.exact_date).days) <= window_days
        for left_hit in left.hits
        for right_hit in right.hits
    )


def _apply_step6_ranking_bonuses(stories: Iterable[TransitStory]) -> tuple[TransitStory, ...]:
    """Finish Python-owned annual ranking before any LLM sees the year.

    Base scoring already weights transit planet, natal target, aspect, angular
    emphasis and repeated passes. Step 6 adds the two remaining build-plan
    signals: exactness and overlapping peak clusters. Both are intentionally
    modest so they refine the ranking rather than overpower the natal geometry.
    """
    source = tuple(stories)
    ranked: list[TransitStory] = []
    for story in source:
        exact_bonus = _exactness_bonus(story.hits)
        overlap_count = sum(
            1
            for other in source
            if other is not story and _stories_cluster(story, other)
        )
        overlap_bonus = min(overlap_count, 3) * 0.04
        base = float(story.score)
        final_score = round(base * (1.0 + exact_bonus + overlap_bonus), 3)
        ranked.append(
            replace(
                story,
                score=final_score,
                base_score=round(base, 3),
                exactness_bonus=round(exact_bonus, 4),
                overlap_count=overlap_count,
            )
        )
    return tuple(ranked)


def _milestone_headline(transit_planet: str, target_planet: str, aspect: str) -> str | None:
    if transit_planet == target_planet and aspect == "conjunction":
        return f"{transit_planet.upper()} RETURN"
    if transit_planet == "Saturn" and target_planet == "Saturn" and aspect in {"square", "opposition"}:
        return f"SATURN {aspect.upper()}"
    if transit_planet == "Uranus" and target_planet == "Uranus" and aspect in {"square", "opposition"}:
        return f"URANUS {aspect.upper()}"
    if transit_planet == "Neptune" and target_planet == "Neptune" and aspect == "square":
        return "NEPTUNE SQUARE"
    return None


def _scan_story(
    *,
    transit_planet: str,
    target: NatalPosition,
    aspect: str,
    days: list[date],
    transit_positions: dict[str, list],
    timezone_name: str,
) -> TransitStory | None:
    allowed_orb = TRANSIT_ORBS[transit_planet]
    all_periods: list[TransitPeriod] = []
    all_hits: list[TransitHit] = []

    positions = transit_positions[transit_planet]
    for target_longitude in _target_longitudes(target.longitude, aspect):
        errors = [_wrap180(position.longitude - target_longitude) for position in positions]
        active = [abs(error) <= allowed_orb for error in errors]
        all_periods.extend(_periods_from_active(days, active))

        # A sign change around the exact target captures direct and retrograde
        # passes. The daily scan identifies the small interval; the contact is
        # then refined to the closest practical local minute.
        for index in range(len(days) - 1):
            e0, e1 = errors[index], errors[index + 1]
            if abs(e0) > 20 or abs(e1) > 20:
                # Avoid false sign flips across the +/-180 wrap boundary.
                continue
            crossed = e0 == 0.0 or e1 == 0.0 or (e0 < 0 < e1) or (e1 < 0 < e0)
            if crossed:
                all_hits.append(
                    _refine_hit(
                        transit_planet=transit_planet,
                        target_longitude=target_longitude,
                        timezone_name=timezone_name,
                        start_day=days[index],
                        start_minute=12 * 60,
                        end_day=days[index + 1],
                        end_minute=12 * 60,
                    )
                )

        # A station can turn just short of a mathematical crossing. Retain a
        # very close local minimum so the timing map does not hide that peak.
        # The daily sample is at noon, so search noon-before to noon-after to
        # avoid losing a closest approach that falls near a midnight boundary.
        for index in range(1, len(days) - 1):
            current = abs(errors[index])
            if current <= 0.12 and current <= abs(errors[index - 1]) and current <= abs(errors[index + 1]):
                all_hits.append(
                    _refine_hit(
                        transit_planet=transit_planet,
                        target_longitude=target_longitude,
                        timezone_name=timezone_name,
                        start_day=days[index - 1],
                        start_minute=12 * 60,
                        end_day=days[index + 1],
                        end_minute=12 * 60,
                    )
                )

    hits = _label_transit_passes(_dedupe_hits(all_hits))
    periods = _merge_periods(all_periods)
    if not hits or not periods:
        return None

    score = _story_score(transit_planet, target, aspect, len(hits))
    language = build_story_language(
        transit_planet=transit_planet,
        target_planet=target.planet,
        aspect=aspect,
        natal_house=target.house,
    )
    return TransitStory(
        transit_planet=transit_planet,
        natal_target=target.planet,
        aspect=aspect,
        natal_house=target.house,
        score=score,
        polarity=_polarity(transit_planet, aspect),
        headline=(
            _milestone_headline(transit_planet, target.planet, aspect)
            or HEADLINE_OVERRIDES.get((transit_planet, target.planet), GENERIC_HEADLINES[transit_planet])
        ),
        summary=language.summary,
        scenarios=language.scenarios,
        insight=language.insight,
        question=language.question,
        move=language.move,
        watch=language.watch,
        periods=periods,
        hits=hits,
        natal_longitude=round(float(target.longitude), 6),
        natal_sign=str(getattr(target, "sign", "") or ""),
        natal_degree=round(float(getattr(target, "degree", 0.0) or 0.0), 6),
    )



BOUNDARY_GAP_DAYS = 2
BOUNDARY_SCAN_LIMIT_DAYS = 900


def _story_active_on_day(
    story: TransitStory,
    target: NatalPosition,
    day: date,
    timezone_name: str,
    cache: dict[date, dict],
) -> bool:
    """Return whether the slow transit is inside its allowed natal orb on one day."""
    positions = cache.get(day)
    if positions is None:
        positions = positions_for_date(day, timezone_name)
        cache[day] = positions

    position = positions.get(story.transit_planet)
    if position is None:
        return False

    allowed_orb = TRANSIT_ORBS[story.transit_planet]
    return any(
        abs(_wrap180(float(position.longitude) - target_longitude)) <= allowed_orb
        for target_longitude in _target_longitudes(target.longitude, story.aspect)
    )


def _extend_boundary_period(
    *,
    story: TransitStory,
    target: NatalPosition,
    timezone_name: str,
    report_start: date,
    report_end: date,
    cache: dict[date, dict],
) -> TransitStory:
    """Recover the true active-window edges when a 365-day scan clips a transit.

    The customer still receives exactly the selected rolling 365-day product.
    This helper only looks outside that display window far enough to determine
    whether a selected slow-planet transit was already active or continues after
    the report. Gaps of up to two days are treated the same way as _merge_periods.
    """
    periods = list(story.periods or ())
    if not periods:
        return story

    first = periods[0]
    last = periods[-1]

    extended_first = first
    if first.start_date == report_start:
        earliest_active = report_start
        inactive_streak = 0
        cursor = report_start - timedelta(days=1)

        for _ in range(BOUNDARY_SCAN_LIMIT_DAYS):
            if _story_active_on_day(
                story,
                target,
                cursor,
                timezone_name,
                cache,
            ):
                earliest_active = cursor
                inactive_streak = 0
            else:
                inactive_streak += 1
                if inactive_streak > BOUNDARY_GAP_DAYS:
                    break
            cursor -= timedelta(days=1)

        extended_first = TransitPeriod(
            earliest_active,
            first.end_date,
        )

    extended_last = last
    if last.end_date == report_end:
        latest_active = report_end
        inactive_streak = 0
        cursor = report_end + timedelta(days=1)

        for _ in range(BOUNDARY_SCAN_LIMIT_DAYS):
            if _story_active_on_day(
                story,
                target,
                cursor,
                timezone_name,
                cache,
            ):
                latest_active = cursor
                inactive_streak = 0
            else:
                inactive_streak += 1
                if inactive_streak > BOUNDARY_GAP_DAYS:
                    break
            cursor += timedelta(days=1)

        extended_last = TransitPeriod(
            last.start_date,
            latest_active,
        )

    if len(periods) == 1:
        periods = [
            TransitPeriod(
                extended_first.start_date,
                extended_last.end_date,
            )
        ]
    else:
        periods[0] = extended_first
        periods[-1] = extended_last

    return replace(
        story,
        periods=tuple(periods),
    )


def _extend_selected_story_boundaries(
    stories: Iterable[TransitStory],
    *,
    targets_by_name: dict[str, NatalPosition],
    timezone_name: str,
    report_start: date,
    report_end: date,
) -> tuple[TransitStory, ...]:
    """Extend only selected slow-planet arcs that touch a report edge."""
    cache: dict[date, dict] = {}
    extended: list[TransitStory] = []

    for story in stories:
        target = targets_by_name.get(story.natal_target)
        if (
            target is None
            or (
                story.first_date != report_start
                and story.last_date != report_end
            )
        ):
            extended.append(story)
            continue

        extended.append(
            _extend_boundary_period(
                story=story,
                target=target,
                timezone_name=timezone_name,
                report_start=report_start,
                report_end=report_end,
                cache=cache,
            )
        )

    return tuple(extended)


def _targets(snapshot: NatalSnapshot) -> tuple[NatalPosition, ...]:
    values = list(snapshot.positions)
    if snapshot.ascendant is not None:
        values.append(snapshot.ascendant)
    if snapshot.midheaven is not None:
        values.append(snapshot.midheaven)
    return tuple(values)


def build_timing_map(
    snapshot: NatalSnapshot,
    *,
    start_date: date,
    timezone_name: str = "Australia/Sydney",
    max_stories: int = 10,
) -> TimingMapReport:
    """Build a ranked 12-month natal-to-transit timing map.

    The calculation is tropical/geocentric because both the NatalSnapshot and
    astrology_engine use Swiss Ephemeris geocentric planetary positions. The
    broad annual scan is daily; detected contacts are then refined to the
    closest practical local minute before the report is returned.
    """
    if max_stories < 3:
        raise ValueError("max_stories must be at least 3")
    # Production is intentionally sparse. Explicit QA calls may request fewer,
    # but no caller can push more than twelve annual transit arcs into the map.
    max_stories = min(int(max_stories), 12)
    end_date = start_date + timedelta(days=364)
    days = [start_date + timedelta(days=offset) for offset in range(365)]

    # One ephemeris pass per day, then reuse it for every natal target/aspect.
    daily_positions = [positions_for_date(day, timezone_name) for day in days]
    transit_positions = {
        planet: [positions[planet] for positions in daily_positions]
        for planet in TRANSIT_PLANETS
    }
    trigger_positions = {
        planet: [positions[planet] for positions in daily_positions]
        for planet in FAST_TRIGGER_PLANETS
    }

    stories: list[TransitStory] = []
    for target in _targets(snapshot):
        for transit_planet in TRANSIT_PLANETS:
            for aspect in ASPECT_ANGLES:
                story = _scan_story(
                    transit_planet=transit_planet,
                    target=target,
                    aspect=aspect,
                    days=days,
                    transit_positions=transit_positions,
                    timezone_name=timezone_name,
                )
                if story is not None:
                    stories.append(story)

    # Step 6: all ranking stays deterministic and Python-owned. The base score
    # already carries planet/target/aspect/angular/repeated-pass importance;
    # refine it with exactness and overlapping peak-cluster evidence before
    # selecting the 8–12-ish arcs that can ever reach Luna Voice.
    stories = list(_apply_step6_ranking_bonuses(stories))

    # Ranking is importance first, but reserve room for opportunity and named
    # life-cycle milestones. A year should not become a catalogue of pressure
    # simply because slow structural contacts score higher than Jupiter.
    stories.sort(key=lambda item: (-item.score, item.first_date, item.transit_planet, item.natal_target))
    selected = list(stories[:max_stories])

    milestones = [
        story for story in stories
        if _milestone_headline(story.transit_planet, story.natal_target, story.aspect)
    ]
    opportunities = sorted(
        (
            story for story in stories
            if story.polarity == "opportunity"
            or (
                story.transit_planet == "Jupiter"
                and story.aspect in {"conjunction", "trine", "sextile"}
            )
        ),
        key=lambda item: (-item.score, item.first_date),
    )[:2]

    protected = []
    for story in milestones + opportunities:
        if story not in protected:
            protected.append(story)

    for story in protected:
        if story in selected:
            continue
        replaceable = sorted(
            (item for item in selected if item not in protected),
            key=lambda item: (item.score, -item.first_date.toordinal()),
        )
        if replaceable:
            selected.remove(replaceable[0])
            selected.append(story)
        elif len(selected) < max_stories:
            selected.append(story)

    selected = list(dict.fromkeys(selected))
    selected.sort(key=lambda item: (item.first_date, -item.score))

    # Paid Year Ahead needs truthful edges. The first 365-day scan deliberately
    # selects/ranks only what belongs to the requested year; after selection we
    # recover the true slow-transit boundary for any chosen arc clipped by the
    # report start/end. This does not widen the customer's report period.
    targets_by_name = {item.planet: item for item in _targets(snapshot)}
    selected = list(
        _extend_selected_story_boundaries(
            selected,
            targets_by_name=targets_by_name,
            timezone_name=timezone_name,
            report_start=start_date,
            report_end=end_date,
        )
    )

    # Step 5: fast planets are calculated only after the main slow-planet arcs
    # survive ranking. They are attached as supporting evidence and can never
    # become top-level annual stories.
    selected_with_triggers: list[TransitStory] = []
    for story in selected:
        target = targets_by_name.get(story.natal_target)
        if target is None:
            selected_with_triggers.append(story)
            continue
        selected_with_triggers.append(
            replace(
                story,
                supporting_triggers=_supporting_triggers_for_story(
                    story=story,
                    target=target,
                    days=days,
                    trigger_positions=trigger_positions,
                    timezone_name=timezone_name,
                ),
            )
        )
    selected = selected_with_triggers

    # Keep Luna's first reference frame solar: the reader's Sun sign is whole-sign
    # House 1 for shared-sky context.  Natal geometry below adds personal precision
    # without replacing that solar frame.
    sun_sign = next(
        (str(getattr(item, "sign", "") or "") for item in snapshot.positions if str(getattr(item, "planet", "")) == "Sun"),
        "Aries",
    )
    all_shared_signals = major_sky_events(
        start_date, end_date, sun_sign or "Aries", timezone_name
    )
    shared_signals = period_priority_signals(
        all_shared_signals,
        "timing",
        limit=10,
        opportunity_slots=2,
    )
    # Personal activation is evaluated against the full registry, not only the
    # public top-ten sky list. A personally exact event must not disappear
    # merely because the collective year is crowded.
    personal_major = personalize_major_signals(
        all_shared_signals,
        snapshot,
        timezone_name,
        limit=24,
    )

    turning_points = sum(len(story.hits) for story in selected)
    rule_changes = sum(
        1
        for story in selected
        if story.transit_planet in {"Saturn", "Uranus", "Pluto"}
        and story.aspect in {"conjunction", "square", "opposition"}
    )
    return TimingMapReport(
        start_date=start_date,
        end_date=end_date,
        timezone_name=timezone_name,
        stories=tuple(selected),
        major_games=min(3, len({story.transit_planet for story in selected})),
        turning_points=turning_points,
        rule_changes=rule_changes,
        major_sky_events=tuple(signal.to_dict() for signal in shared_signals),
        personal_major_events=tuple(item.to_dict() for item in personal_major),
    )


def month_intensity(report: TimingMapReport) -> tuple[tuple[str, float], ...]:
    """Return every calendar month touched by the 365-day map, normalised 0-1.

    A 365-day window usually touches 13 calendar-month labels because the first
    and last months are partial. Keeping both edges prevents the visual strip
    from silently dropping the final days of the report.
    """
    raw: list[tuple[str, float]] = []
    cursor = date(report.start_date.year, report.start_date.month, 1)
    while cursor <= report.end_date:
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)
        month_start = max(report.start_date, cursor)
        month_end = min(report.end_date, next_month - timedelta(days=1))
        value = 0.0
        for story in report.stories:
            if any(period.start_date <= month_end and period.end_date >= month_start for period in story.periods):
                value += story.score
            value += sum(0.35 * story.score for hit in story.hits if month_start <= hit.exact_date <= month_end)
        label = cursor.strftime("%b").upper()
        if cursor.year != report.start_date.year:
            label += f" {str(cursor.year)[-2:]}"
        raw.append((label, value))
        cursor = next_month

    maximum = max((value for _, value in raw), default=0.0)
    if maximum <= 0:
        return tuple((label, 0.0) for label, _ in raw)
    return tuple((label, round(value / maximum, 3)) for label, value in raw)

