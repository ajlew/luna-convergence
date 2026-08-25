from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from astrology_engine import HOUSE_NAMES, positions_for_date
from natal_snapshot import NatalSnapshot, NatalPosition
from timing_insight import build_story_language


TRANSIT_PLANETS = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
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


@dataclass(frozen=True)
class TransitPeriod:
    start_date: date
    end_date: date


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

    @property
    def first_date(self) -> date:
        return min(period.start_date for period in self.periods)

    @property
    def last_date(self) -> date:
        return max(period.end_date for period in self.periods)


@dataclass(frozen=True)
class TimingMapReport:
    start_date: date
    end_date: date
    timezone_name: str
    stories: tuple[TransitStory, ...]
    major_games: int
    turning_points: int
    rule_changes: int


def _wrap180(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def _target_longitudes(natal_longitude: float, aspect: str) -> tuple[float, ...]:
    angle = ASPECT_ANGLES[aspect]
    first = (natal_longitude + angle) % 360.0
    second = (natal_longitude - angle) % 360.0
    if abs(_wrap180(first - second)) < 1e-7:
        return (first,)
    return (first, second)


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
    ordered = sorted(hits, key=lambda item: item.exact_date)
    result: list[TransitHit] = []
    for hit in ordered:
        if result and abs((hit.exact_date - result[-1].exact_date).days) <= minimum_gap_days:
            if hit.orb < result[-1].orb:
                result[-1] = hit
            continue
        result.append(hit)
    return tuple(result)


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
    domain = TARGET_DOMAINS.get(target.planet, target.planet.lower())
    house_domain = HOUSE_NAMES.get(target.house or 0, "")

    if aspect in {"square", "opposition"}:
        first = f"Stop postponing the choice around {domain}; the tension is already showing you where the weak point is."
    elif aspect in {"trine", "sextile"}:
        first = f"Use the support around {domain} while the opening is active. Make one concrete move."
    else:
        first = f"Treat {domain} as active, not background. The old default is no longer neutral."

    if house_domain:
        second = f"Watch {house_domain}. That is where the consequence is most likely to become visible."
    else:
        second = "Watch the part of life already asking for the clearest decision."

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
    domain = TARGET_DOMAINS.get(target.planet, target.planet.lower())
    if aspect in {"square", "opposition"}:
        relation = "The friction is useful. It exposes the condition you can no longer leave vague."
    elif aspect in {"trine", "sextile"}:
        relation = "The support is real. Use it before it becomes background."
    else:
        relation = "The two themes are concentrated now. Stop treating the issue as background noise."

    transit_line = {
        "Jupiter": "More room is available.",
        "Saturn": "The cost and responsibility need terms.",
        "Uranus": "The old structure has too little room.",
        "Neptune": "The story needs proof.",
        "Pluto": "The real power structure is showing itself.",
    }[transit_planet]
    return f"{transit_line} In your chart this lands on {domain}. {relation}"

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


def _scan_story(
    *,
    transit_planet: str,
    target: NatalPosition,
    aspect: str,
    days: list[date],
    transit_positions: dict[str, list],
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
        # passes. The closer of the two sampled days is used as the exact-date
        # label; Luna deliberately claims day-level, not minute-level, timing.
        for index in range(len(days) - 1):
            e0, e1 = errors[index], errors[index + 1]
            if abs(e0) > 20 or abs(e1) > 20:
                # Avoid false sign flips across the +/-180 wrap boundary.
                continue
            crossed = e0 == 0.0 or e1 == 0.0 or (e0 < 0 < e1) or (e1 < 0 < e0)
            if crossed:
                choose = index if abs(e0) <= abs(e1) else index + 1
                all_hits.append(
                    TransitHit(
                        exact_date=days[choose],
                        orb=round(abs(errors[choose]), 3),
                        retrograde=bool(positions[choose].retrograde),
                    )
                )

        # A station can turn just short of a mathematical crossing. Retain a
        # very close local minimum so the timing map does not hide that peak.
        for index in range(1, len(days) - 1):
            current = abs(errors[index])
            if current <= 0.12 and current <= abs(errors[index - 1]) and current <= abs(errors[index + 1]):
                all_hits.append(
                    TransitHit(
                        exact_date=days[index],
                        orb=round(current, 3),
                        retrograde=bool(positions[index].retrograde),
                    )
                )

    hits = _dedupe_hits(all_hits)
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
        headline=HEADLINE_OVERRIDES.get((transit_planet, target.planet), GENERIC_HEADLINES[transit_planet]),
        summary=language.summary,
        scenarios=language.scenarios,
        insight=language.insight,
        question=language.question,
        move=language.move,
        watch=language.watch,
        periods=periods,
        hits=hits,
    )


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
    report is day-level by design: exact-date labels are the closest local date
    to an exact transit contact, not a claim about minute-level event timing.
    """
    if max_stories < 3:
        raise ValueError("max_stories must be at least 3")
    end_date = start_date + timedelta(days=364)
    days = [start_date + timedelta(days=offset) for offset in range(365)]

    # One ephemeris pass per day, then reuse it for every natal target/aspect.
    daily_positions = [positions_for_date(day, timezone_name) for day in days]
    transit_positions = {
        planet: [positions[planet] for positions in daily_positions]
        for planet in TRANSIT_PLANETS
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
                )
                if story is not None:
                    stories.append(story)

    # Ranking is importance first; chronology breaks close ties. Then cap the
    # report so Luna narrates the year rather than dumping every contact.
    stories.sort(key=lambda item: (-item.score, item.first_date, item.transit_planet, item.natal_target))
    selected = stories[:max_stories]
    selected.sort(key=lambda item: (item.first_date, -item.score))

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

