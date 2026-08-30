from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from collections import defaultdict, Counter
from math import isfinite
from typing import Iterable
from zoneinfo import ZoneInfo

import swisseph as swe


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "True Node": swe.TRUE_NODE,
}

PLANET_WEIGHTS = {
    "Sun": 1.7, "Moon": 1.0, "Mercury": 1.1, "Venus": 1.2, "Mars": 1.4,
    "Jupiter": 1.8, "Saturn": 1.9, "Uranus": 1.9, "Neptune": 1.8,
    "Pluto": 2.0, "True Node": 1.1,
}

ASPECTS = {
    "conjunction": (0.0, 7.0),
    "sextile": (60.0, 4.0),
    "square": (90.0, 6.0),
    "trine": (120.0, 6.0),
    "opposition": (180.0, 7.0),
}

HOUSE_NAMES = {
    1: "identity, energy and personal direction",
    2: "income, possessions and self-worth",
    3: "communication, sales, learning and local movement",
    4: "home, family and private foundations",
    5: "creativity, romance, pleasure and entrepreneurship",
    6: "work routines, health, service and operations",
    7: "relationships, clients, contracts and competitors",
    8: "shared money, debt, tax, trust and obligations",
    9: "travel, publishing, law, education and foreign markets",
    10: "career, reputation, authority and public results",
    11: "networks, audiences, alliances and long-term goals",
    12: "rest, hidden matters, closure and psychological patterns",
}

HARD_ASPECTS = {"square", "opposition"}
FLOW_ASPECTS = {"trine", "sextile"}


@dataclass(frozen=True)
class Position:
    planet: str
    longitude: float
    sign_index: int
    sign: str
    degree: float
    speed: float
    retrograde: bool

    def label(self) -> str:
        degree = int(self.degree)
        minute = int(round((self.degree - degree) * 60))
        if minute == 60:
            degree += 1
            minute = 0
        suffix = " R" if self.retrograde else ""
        return f"{degree}°{minute:02d}′ {self.sign}{suffix}"


@dataclass(frozen=True)
class Aspect:
    planet1: str
    planet2: str
    name: str
    orb: float
    strength: float


@dataclass(frozen=True)
class Event:
    event_date: date
    kind: str
    title: str
    detail: str
    importance: float
    planets: tuple[str, ...]
    houses: tuple[int, ...]
    polarity: str
    orb: float | None = None
    aspect_name: str = ""
    applying_state: str = ""


@dataclass(frozen=True)
class RetrogradeCycle:
    planet: str
    retrograde_start: date
    direct_date: date
    shadow_start: date | None
    shadow_end: date | None
    signs: tuple[str, ...]
    houses: tuple[int, ...]
    retrograde_longitude: float
    direct_longitude: float


@dataclass(frozen=True)
class Convergence:
    start_date: date
    end_date: date
    title: str
    score: float
    events: tuple[Event, ...]
    planets: tuple[str, ...]
    houses: tuple[int, ...]
    polarity: str


def angular_distance(a: float, b: float) -> float:
    value = abs((a - b) % 360.0)
    return min(value, 360.0 - value)


def sign_index(longitude: float) -> int:
    return int((longitude % 360.0) // 30.0)


def whole_sign_house(planet_sign_index: int, native_sign_index: int) -> int:
    return ((planet_sign_index - native_sign_index) % 12) + 1


def _local_to_jd(d: date, timezone_name: str, local_hour: int = 12) -> float:
    local_dt = datetime(d.year, d.month, d.day, local_hour, tzinfo=ZoneInfo(timezone_name))
    utc_dt = local_dt.astimezone(timezone.utc)
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)


def _calc_ut(jd: float, planet_id: int):
    try:
        return swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    except swe.Error:
        return swe.calc_ut(jd, planet_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0]


@lru_cache(maxsize=120000)
def position_for_local_minute(
    iso_date: str,
    timezone_name: str,
    minute_of_day: int,
    planet: str,
) -> Position:
    """Return one planetary position for an exact local minute.

    Daily and weekly products use this narrow helper to find the closest orb
    reached anywhere inside a reader's local day.  The older date-level helper
    intentionally remains noon-based for broad period scoring.
    """
    if planet not in PLANETS:
        raise ValueError(f"Unknown planet: {planet}")
    minute = int(minute_of_day)
    if not 0 <= minute <= 1439:
        raise ValueError("minute_of_day must be between 0 and 1439")

    d = date.fromisoformat(iso_date)
    local_dt = datetime(
        d.year,
        d.month,
        d.day,
        minute // 60,
        minute % 60,
        tzinfo=ZoneInfo(timezone_name),
    )
    utc_dt = local_dt.astimezone(timezone.utc)
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)
    values = _calc_ut(jd, PLANETS[planet])
    longitude = values[0] % 360.0
    speed = values[3]
    idx = sign_index(longitude)
    return Position(
        planet=planet,
        longitude=longitude,
        sign_index=idx,
        sign=SIGNS[idx],
        degree=longitude % 30.0,
        speed=speed,
        retrograde=speed < 0,
    )


@lru_cache(maxsize=30000)
def positions_for_iso(
    iso_date: str,
    timezone_name: str = "Australia/Sydney",
    local_hour: int = 12,
) -> tuple[Position, ...]:
    d = date.fromisoformat(iso_date)
    jd = _local_to_jd(d, timezone_name, local_hour)
    result = []
    for planet, planet_id in PLANETS.items():
        values = _calc_ut(jd, planet_id)
        longitude = values[0] % 360.0
        speed = values[3]
        idx = sign_index(longitude)
        result.append(
            Position(
                planet=planet,
                longitude=longitude,
                sign_index=idx,
                sign=SIGNS[idx],
                degree=longitude % 30.0,
                speed=speed,
                retrograde=speed < 0,
            )
        )
    return tuple(result)


def positions_for_date(
    d: date,
    timezone_name: str = "Australia/Sydney",
    local_hour: int = 12,
) -> dict[str, Position]:
    return {
        item.planet: item
        for item in positions_for_iso(d.isoformat(), timezone_name, local_hour)
    }


def house_map(positions: dict[str, Position], native_sign: str) -> dict[str, int]:
    native_index = SIGNS.index(native_sign)
    return {
        planet: whole_sign_house(position.sign_index, native_index)
        for planet, position in positions.items()
    }


def detect_aspects(
    positions: dict[str, Position],
    include_moon: bool = True,
    maximum: int | None = None,
) -> list[Aspect]:
    names = list(positions)
    result = []
    for index, p1 in enumerate(names):
        if not include_moon and p1 == "Moon":
            continue
        for p2 in names[index + 1:]:
            if not include_moon and p2 == "Moon":
                continue
            distance = angular_distance(positions[p1].longitude, positions[p2].longitude)
            for name, (target, allowed_orb) in ASPECTS.items():
                orb = abs(distance - target)
                if orb <= allowed_orb:
                    closeness = max(0.0, 1.0 - orb / allowed_orb)
                    strength = closeness * (PLANET_WEIGHTS[p1] + PLANET_WEIGHTS[p2]) / 2
                    if name in {"conjunction", "opposition"}:
                        strength *= 1.12
                    result.append(Aspect(p1, p2, name, orb, strength))
                    break
    result.sort(key=lambda item: (-item.strength, item.orb))
    return result[:maximum] if maximum else result


def _event_polarity(aspect_name: str | None = None, planets: Iterable[str] = ()) -> str:
    planets = set(planets)
    if aspect_name in FLOW_ASPECTS:
        return "opportunity"
    if aspect_name in HARD_ASPECTS:
        return "pressure"
    if "Jupiter" in planets and not planets & {"Saturn", "Pluto", "Mars"}:
        return "opportunity"
    if planets & {"Saturn", "Pluto", "Mars"}:
        return "pressure"
    if planets & {"Uranus", "Neptune"}:
        return "mixed"
    return "neutral"


def _aspect_events(
    start: date,
    end: date,
    native_sign: str,
    timezone_name: str,
) -> list[Event]:
    native_index = SIGNS.index(native_sign)
    daily: dict[tuple[str, str, str], dict[date, tuple[float, float]]] = defaultdict(dict)
    cursor = start - timedelta(days=1)
    while cursor <= end + timedelta(days=1):
        positions = positions_for_date(cursor, timezone_name)
        for aspect in detect_aspects(positions, include_moon=False):
            daily[(aspect.planet1, aspect.planet2, aspect.name)][cursor] = (
                aspect.orb, aspect.strength
            )
        cursor += timedelta(days=1)

    result = []
    for (p1, p2, aspect_name), values in daily.items():
        for d, (orb, strength) in values.items():
            if not (start <= d <= end) or orb > 1.0:
                continue
            before = values.get(d - timedelta(days=1), (99.0, 0.0))[0]
            after = values.get(d + timedelta(days=1), (99.0, 0.0))[0]
            if orb <= before and orb <= after:
                positions = positions_for_date(d, timezone_name)
                houses = (
                    whole_sign_house(positions[p1].sign_index, native_index),
                    whole_sign_house(positions[p2].sign_index, native_index),
                )
                slow = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
                pair = {p1, p2}
                if pair <= slow:
                    importance = min(10.0, 7.4 + strength * 1.25)
                elif pair & slow:
                    importance = min(7.6, 4.8 + strength * 1.15)
                else:
                    importance = min(6.6, 4.2 + strength)
                result.append(
                    Event(
                        event_date=d,
                        kind="aspect",
                        title=f"{p1} {aspect_name} {p2}",
                        detail=f"Exact within approximately {orb:.2f}°.",
                        importance=importance,
                        planets=(p1, p2),
                        houses=houses,
                        polarity=_event_polarity(aspect_name, (p1, p2)),
                        orb=orb,
                        aspect_name=aspect_name,
                        applying_state="exact",
                    )
                )
    return result


def _eclipse_type(flag: int, solar: bool) -> str:
    if flag & swe.ECL_TOTAL:
        return "Total"
    if solar and flag & swe.ECL_ANNULAR:
        return "Annular"
    if solar and flag & swe.ECL_ANNULAR_TOTAL:
        return "Hybrid"
    if flag & swe.ECL_PARTIAL:
        return "Partial"
    if not solar and flag & swe.ECL_PENUMBRAL:
        return "Penumbral"
    return "Eclipse"


def _jd_to_utc_datetime(jd: float) -> datetime:
    year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
    whole_hour = int(hour)
    minute_float = (hour - whole_hour) * 60
    minute = int(minute_float)
    second = int(round((minute_float - minute) * 60))
    if second == 60:
        second = 59
    return datetime(year, month, day, whole_hour, minute, second, tzinfo=timezone.utc)


def eclipse_events(
    start: date,
    end: date,
    native_sign: str,
    timezone_name: str = "Australia/Sydney",
) -> list[Event]:
    native_index = SIGNS.index(native_sign)
    start_jd = swe.julday(start.year, start.month, start.day, 0.0)
    end_jd = swe.julday(end.year, end.month, end.day, 23.99)
    result = []

    for solar, finder in ((True, swe.sol_eclipse_when_glob), (False, swe.lun_eclipse_when)):
        cursor_jd = start_jd - 2
        while True:
            try:
                flag, times = finder(cursor_jd, swe.FLG_MOSEPH)
            except swe.Error:
                break
            maximum_jd = times[0]
            if maximum_jd > end_jd:
                break
            maximum_utc = _jd_to_utc_datetime(maximum_jd)
            local_dt = maximum_utc.astimezone(ZoneInfo(timezone_name))
            event_date = local_dt.date()
            if event_date >= start:
                positions = positions_for_date(event_date, timezone_name)
                body = "Sun" if solar else "Moon"
                position = positions[body]
                house = whole_sign_house(position.sign_index, native_index)
                eclipse_name = _eclipse_type(flag, solar)
                result.append(
                    Event(
                        event_date=event_date,
                        kind="eclipse",
                        title=f"{eclipse_name} {'Solar' if solar else 'Lunar'} Eclipse in {position.sign}",
                        detail=f"Activates house {house}: {HOUSE_NAMES[house]}.",
                        importance=9.2,
                        planets=("Sun", "Moon", "True Node"),
                        houses=(house,),
                        polarity="turning point",
                    )
                )
            cursor_jd = maximum_jd + 20
    return result


def period_events(
    start: date,
    end: date,
    native_sign: str,
    timezone_name: str = "Australia/Sydney",
) -> list[Event]:
    native_index = SIGNS.index(native_sign)
    result = []
    previous = positions_for_date(start - timedelta(days=1), timezone_name)
    cursor = start

    while cursor <= end:
        current = positions_for_date(cursor, timezone_name)

        for planet in PLANETS:
            if previous[planet].sign_index != current[planet].sign_index:
                house = whole_sign_house(current[planet].sign_index, native_index)
                importance = {
                    "Pluto": 10.0, "Neptune": 9.8, "Uranus": 9.7,
                    "Saturn": 9.2, "Jupiter": 8.8, "Mars": 6.8,
                    "Venus": 6.2, "Mercury": 5.8, "Sun": 5.0,
                    "Moon": 1.6, "True Node": 7.5,
                }[planet]
                result.append(
                    Event(
                        event_date=cursor,
                        kind="ingress",
                        title=f"{planet} enters {current[planet].sign}",
                        detail=f"Moves into house {house}: {HOUSE_NAMES[house]}.",
                        importance=importance,
                        planets=(planet,),
                        houses=(house,),
                        polarity=_event_polarity(planets=(planet,)),
                    )
                )

            station = None
            if previous[planet].speed < 0 <= current[planet].speed:
                station = "direct"
            elif previous[planet].speed >= 0 > current[planet].speed:
                station = "retrograde"

            if station and planet not in {"Sun", "Moon", "True Node"}:
                house = whole_sign_house(current[planet].sign_index, native_index)
                importance = 8.2 if planet in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"} else 6.8
                result.append(
                    Event(
                        event_date=cursor,
                        kind="station",
                        title=f"{planet} stations {station}",
                        detail=f"Intensifies house {house}: {HOUSE_NAMES[house]}.",
                        importance=importance,
                        planets=(planet,),
                        houses=(house,),
                        polarity="review" if station == "retrograde" else "release",
                    )
                )

        # Lunations at daily resolution.
        separation = angular_distance(current["Sun"].longitude, current["Moon"].longitude)
        next_positions = positions_for_date(cursor + timedelta(days=1), timezone_name)
        previous_sep = angular_distance(previous["Sun"].longitude, previous["Moon"].longitude)
        next_sep = angular_distance(next_positions["Sun"].longitude, next_positions["Moon"].longitude)

        if separation <= 7 and separation <= previous_sep and separation <= next_sep:
            house = whole_sign_house(current["Sun"].sign_index, native_index)
            result.append(
                Event(
                    event_date=cursor,
                    kind="lunation",
                    title=f"New Moon in {current['Sun'].sign}",
                    detail=f"Seeds a cycle in house {house}: {HOUSE_NAMES[house]}.",
                    importance=6.5,
                    planets=("Sun", "Moon"),
                    houses=(house,),
                    polarity="new cycle",
                )
            )

        full_distance = abs(separation - 180)
        if (
            full_distance <= 7
            and full_distance <= abs(previous_sep - 180)
            and full_distance <= abs(next_sep - 180)
        ):
            house = whole_sign_house(current["Moon"].sign_index, native_index)
            result.append(
                Event(
                    event_date=cursor,
                    kind="lunation",
                    title=f"Full Moon in {current['Moon'].sign}",
                    detail=f"Brings visibility or culmination in house {house}: {HOUSE_NAMES[house]}.",
                    importance=6.5,
                    planets=("Sun", "Moon"),
                    houses=(house,),
                    polarity="culmination",
                )
            )

        previous = current
        cursor += timedelta(days=1)

    result.extend(_aspect_events(start, end, native_sign, timezone_name))
    result.extend(eclipse_events(start, end, native_sign, timezone_name))

    unique: dict[tuple[date, str], Event] = {}
    for event in result:
        key = (event.event_date, event.title)
        if key not in unique or event.importance > unique[key].importance:
            unique[key] = event

    return sorted(unique.values(), key=lambda item: (item.event_date, -item.importance))


def _nearest_longitude_date(
    target_longitude: float,
    start: date,
    end: date,
    planet: str,
    timezone_name: str,
) -> date | None:
    cursor = start
    best_date = None
    best_distance = 999.0
    while cursor <= end:
        position = positions_for_date(cursor, timezone_name)[planet]
        distance = angular_distance(position.longitude, target_longitude)
        if distance < best_distance:
            best_distance = distance
            best_date = cursor
        cursor += timedelta(days=1)
    return best_date if best_distance <= 1.5 else None


def retrograde_cycles(
    start: date,
    end: date,
    native_sign: str,
    timezone_name: str = "Australia/Sydney",
) -> list[RetrogradeCycle]:
    native_index = SIGNS.index(native_sign)
    planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    search_start = start - timedelta(days=220)
    search_end = end + timedelta(days=220)
    result = []

    for planet in planets:
        stations = []
        previous = positions_for_date(search_start, timezone_name)[planet]
        cursor = search_start + timedelta(days=1)
        while cursor <= search_end:
            current = positions_for_date(cursor, timezone_name)[planet]
            if previous.speed >= 0 > current.speed:
                stations.append(("retrograde", cursor, current.longitude))
            elif previous.speed < 0 <= current.speed:
                stations.append(("direct", cursor, current.longitude))
            previous = current
            cursor += timedelta(days=1)

        for index, item in enumerate(stations):
            kind, retro_date, retro_lon = item
            if kind != "retrograde":
                continue
            direct = next((entry for entry in stations[index + 1:] if entry[0] == "direct"), None)
            if not direct:
                continue
            _, direct_date, direct_lon = direct
            if direct_date < start or retro_date > end:
                continue

            shadow_start = _nearest_longitude_date(
                direct_lon,
                retro_date - timedelta(days=220),
                retro_date - timedelta(days=1),
                planet,
                timezone_name,
            )
            shadow_end = _nearest_longitude_date(
                retro_lon,
                direct_date + timedelta(days=1),
                direct_date + timedelta(days=220),
                planet,
                timezone_name,
            )

            signs = []
            houses = []
            sample = retro_date
            while sample <= direct_date:
                position = positions_for_date(sample, timezone_name)[planet]
                if position.sign not in signs:
                    signs.append(position.sign)
                house = whole_sign_house(position.sign_index, native_index)
                if house not in houses:
                    houses.append(house)
                sample += timedelta(days=3)

            result.append(
                RetrogradeCycle(
                    planet=planet,
                    retrograde_start=retro_date,
                    direct_date=direct_date,
                    shadow_start=shadow_start,
                    shadow_end=shadow_end,
                    signs=tuple(signs),
                    houses=tuple(houses),
                    retrograde_longitude=retro_lon,
                    direct_longitude=direct_lon,
                )
            )

    return sorted(result, key=lambda item: item.retrograde_start)


def _convergence_title(planets: set[str], polarities: Counter, houses: list[int]) -> str:
    if {"Saturn", "Neptune"} <= planets:
        return "Dream versus reality"
    if {"Jupiter", "Pluto"} <= planets:
        return "Expansion versus control"
    if {"Jupiter", "Saturn"} <= planets:
        return "Controlled expansion"
    if {"Uranus", "Pluto"} <= planets:
        return "Structural breakthrough"
    if {"Jupiter", "Uranus"} <= planets:
        return "Rapid opening"
    if polarities["pressure"] > polarities["opportunity"]:
        return "Pressure convergence"
    if polarities["opportunity"] > polarities["pressure"]:
        return "Opportunity convergence"
    if len(set(houses)) >= 4:
        return "Multi-house turning point"
    return "Strategic convergence"


def convergence_points(
    events: list[Event],
    window_days: int = 6,
    maximum: int = 9,
) -> list[Convergence]:
    """
    Build clusters around high-importance anchor events.

    Fast-planet contacts may describe how a convergence is triggered, but a cluster
    must contain at least one structural anchor such as an eclipse, station,
    important ingress or slow-planet aspect.
    """
    anchors = [
        event for event in events
        if event.importance >= 8.0
        or event.kind == "eclipse"
        or (
            event.kind in {"ingress", "station"}
            and any(planet in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"} for planet in event.planets)
        )
    ]

    candidates = []
    for anchor in anchors:
        members = [
            event for event in events
            if abs((event.event_date - anchor.event_date).days) <= window_days
            and event.importance >= 5.7
        ]
        unique_members = {(event.event_date, event.title): event for event in members}
        members = list(unique_members.values())
        if len(members) < 3:
            continue

        structural_members = [
            event for event in members
            if event.importance >= 8.0
            or event.kind == "eclipse"
            or (
                event.kind in {"ingress", "station"}
                and any(planet in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"} for planet in event.planets)
            )
        ]
        if not structural_members:
            continue

        planets = sorted({planet for event in members for planet in event.planets})
        houses = [house for event in members for house in event.houses]
        polarities = Counter(event.polarity for event in members)
        diversity = len({event.kind for event in members})
        score = (
            sum(event.importance for event in structural_members) * 1.35
            + sum(event.importance for event in members if event not in structural_members) * 0.35
            + diversity * 2.0
            + len(set(planets)) * 0.5
            + len(set(houses)) * 0.5
        )

        title = _convergence_title(
            {planet for event in structural_members for planet in event.planets},
            polarities,
            houses,
        )
        dominant_polarity = polarities.most_common(1)[0][0]
        candidates.append(
            Convergence(
                start_date=min(event.event_date for event in members),
                end_date=max(event.event_date for event in members),
                title=title,
                score=score,
                events=tuple(sorted(members, key=lambda item: item.event_date)),
                planets=tuple(planets),
                houses=tuple(sorted(set(houses))),
                polarity=dominant_polarity,
            )
        )

    candidates.sort(key=lambda item: -item.score)
    selected = []
    fingerprints = set()
    for candidate in candidates:
        fingerprint = tuple((event.event_date, event.title) for event in candidate.events)
        if fingerprint in fingerprints:
            continue
        if any(
            not (
                candidate.end_date < existing.start_date - timedelta(days=3)
                or candidate.start_date > existing.end_date + timedelta(days=3)
            )
            for existing in selected
        ):
            continue
        selected.append(candidate)
        fingerprints.add(fingerprint)
        if len(selected) >= maximum:
            break

    return sorted(selected, key=lambda item: item.start_date)


def dominant_houses(
    start: date,
    end: date,
    native_sign: str,
    timezone_name: str,
    step_days: int = 3,
) -> list[tuple[int, float]]:
    native_index = SIGNS.index(native_sign)
    counter = Counter()
    cursor = start
    while cursor <= end:
        positions = positions_for_date(cursor, timezone_name)
        for planet, position in positions.items():
            weight = PLANET_WEIGHTS[planet]
            if planet == "Moon":
                weight *= 0.2
            counter[whole_sign_house(position.sign_index, native_index)] += weight
        cursor += timedelta(days=step_days)
    return counter.most_common(6)


def serialize(value):
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        payload = asdict(value)
        return {key: serialize(item) for key, item in payload.items()}
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    return value
