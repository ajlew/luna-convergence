from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Iterable
import math
from zoneinfo import ZoneInfo

import swisseph as swe

from astrology_engine import ASPECTS, PLANET_WEIGHTS, SIGNS, angular_distance, sign_index

NATAL_PLANETS = {
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

ELEMENT = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

MODALITY = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable",
}

SIGN_LANGUAGE = {
    "Aries": ("initiative", "acting before the path is fully proven"),
    "Taurus": ("stability and value", "building slowly enough that the result can last"),
    "Gemini": ("curiosity and exchange", "testing reality through questions, language and movement"),
    "Cancer": ("belonging and protection", "knowing what deserves care and what has become over-protected"),
    "Leo": ("expression and creative visibility", "letting your work be seen without making applause the measure"),
    "Virgo": ("discernment and usefulness", "improving what matters without turning refinement into self-criticism"),
    "Libra": ("relationship and balance", "measuring reciprocity instead of keeping peace at any price"),
    "Scorpio": ("depth, trust and transformation", "staying close to what is true when control would feel easier"),
    "Sagittarius": ("exploration and meaning", "going further without losing contact with evidence"),
    "Capricorn": ("structure and mastery", "turning pressure into something durable rather than carrying everything indefinitely"),
    "Aquarius": ("independence and systems", "changing the pattern without disconnecting from the people inside it"),
    "Pisces": ("sensitivity and imagination", "using intuition without letting uncertainty write the whole story"),
}

PLANET_ROLE = {
    "Sun": "identity and direction",
    "Moon": "emotional needs and habits",
    "Mercury": "thinking and communication",
    "Venus": "attachment, values and attraction",
    "Mars": "drive, assertion and conflict",
    "Jupiter": "growth, confidence and belief",
    "Saturn": "standards, limits and responsibility",
    "Uranus": "freedom, disruption and reinvention",
    "Neptune": "imagination, ideals and ambiguity",
    "Pluto": "power, trust and deep change",
    "True Node": "developmental direction",
}


@dataclass(frozen=True)
class NatalPosition:
    planet: str
    longitude: float
    sign: str
    degree: float
    retrograde: bool
    house: int | None = None

    def label(self) -> str:
        degree = int(self.degree)
        minute = int(round((self.degree - degree) * 60))
        if minute == 60:
            degree += 1
            minute = 0
        suffix = " R" if self.retrograde else ""
        return f"{degree}°{minute:02d}′ {self.sign}{suffix}"


@dataclass(frozen=True)
class NatalAspect:
    planet1: str
    planet2: str
    name: str
    orb: float
    strength: float

    def label(self) -> str:
        return f"{self.planet1} {self.name} {self.planet2} · {self.orb:.1f}° orb"


@dataclass(frozen=True)
class NatalTheme:
    title: str
    text: str
    evidence: str


@dataclass(frozen=True)
class NatalSnapshot:
    birth_date: date
    birth_time_known: bool
    timezone_name: str
    location_name: str | None
    positions: tuple[NatalPosition, ...]
    aspects: tuple[NatalAspect, ...]
    ascendant: NatalPosition | None
    midheaven: NatalPosition | None
    moon_uncertain: tuple[str, ...]
    themes: tuple[NatalTheme, ...]
    dominant_element: str
    dominant_modality: str


def _calc_ut(jd: float, planet_id: int):
    try:
        return swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    except swe.Error:
        return swe.calc_ut(jd, planet_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0]


def _jd_from_local(birth_date: date, birth_time: time, timezone_name: str) -> float:
    local_dt = datetime.combine(birth_date, birth_time, tzinfo=ZoneInfo(timezone_name))
    utc_dt = local_dt.astimezone(timezone.utc)
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)


def _jd_utc(birth_date: date, hour: float) -> float:
    return swe.julday(birth_date.year, birth_date.month, birth_date.day, hour)


def _planet_positions(jd: float) -> list[NatalPosition]:
    result: list[NatalPosition] = []
    for planet, planet_id in NATAL_PLANETS.items():
        values = _calc_ut(jd, planet_id)
        longitude = values[0] % 360.0
        idx = sign_index(longitude)
        result.append(
            NatalPosition(
                planet=planet,
                longitude=longitude,
                sign=SIGNS[idx],
                degree=longitude % 30.0,
                retrograde=values[3] < 0,
            )
        )
    return result


def _whole_sign_house(longitude: float, ascendant_longitude: float) -> int:
    return ((sign_index(longitude) - sign_index(ascendant_longitude)) % 12) + 1


def _angles(jd: float, latitude: float, longitude: float) -> tuple[NatalPosition, NatalPosition]:
    # Swiss Ephemeris supplies the tropical Ascendant and MC. Luna then uses
    # the Ascendant sign as House 1 for its whole-sign house framework.
    _cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b"P", swe.FLG_SWIEPH)
    asc_lon = ascmc[0] % 360.0
    mc_lon = ascmc[1] % 360.0
    asc_idx = sign_index(asc_lon)
    mc_idx = sign_index(mc_lon)
    return (
        NatalPosition("Ascendant", asc_lon, SIGNS[asc_idx], asc_lon % 30.0, False, 1),
        NatalPosition("Midheaven", mc_lon, SIGNS[mc_idx], mc_lon % 30.0, False, None),
    )


def detect_natal_aspects(positions: Iterable[NatalPosition]) -> list[NatalAspect]:
    positions = list(positions)
    result: list[NatalAspect] = []
    for index, first in enumerate(positions):
        for second in positions[index + 1 :]:
            # The Node is kept in evidence, but the free snapshot prioritises
            # planet-to-planet aspects for cleaner interpretation.
            if "True Node" in {first.planet, second.planet}:
                continue
            distance = angular_distance(first.longitude, second.longitude)
            for name, (target, allowed_orb) in ASPECTS.items():
                orb = abs(distance - target)
                if orb <= allowed_orb:
                    closeness = max(0.0, 1.0 - orb / allowed_orb)
                    weight1 = PLANET_WEIGHTS.get(first.planet, 1.0)
                    weight2 = PLANET_WEIGHTS.get(second.planet, 1.0)
                    strength = closeness * (weight1 + weight2) / 2.0
                    if name in {"conjunction", "opposition"}:
                        strength *= 1.12
                    result.append(NatalAspect(first.planet, second.planet, name, orb, strength))
                    break
    return sorted(result, key=lambda item: (-item.strength, item.orb))


def _aspect_sentence(aspect: NatalAspect) -> tuple[str, str]:
    p1, p2 = aspect.planet1, aspect.planet2
    roles = f"{PLANET_ROLE.get(p1, p1.lower())} and {PLANET_ROLE.get(p2, p2.lower())}"
    if aspect.name in {"square", "opposition"}:
        title = "A tension that asks for integration"
        text = (
            f"{p1} and {p2} form a {aspect.name}. This can make {roles} pull in different directions. "
            "The useful expression is not choosing one side permanently, but noticing when one function has taken over and restoring choice."
        )
    elif aspect.name == "conjunction":
        title = "Two functions operate as one"
        text = (
            f"{p1} and {p2} are conjunct, so {roles} tend to arrive together. "
            "That concentration can become a recognisable strength once you learn when to amplify it and when to create distance."
        )
    else:
        title = "A capacity that can be used deliberately"
        text = (
            f"{p1} and {p2} form a {aspect.name}, linking {roles} with relatively little friction. "
            "Because it can feel natural, the advantage is strongest when you use it consciously rather than assuming it will carry every situation."
        )
    return title, text


def _build_themes(positions: list[NatalPosition], aspects: list[NatalAspect], moon_uncertain: tuple[str, ...] = ()) -> tuple[NatalTheme, ...]:
    by_planet = {item.planet: item for item in positions}
    sun = by_planet["Sun"]
    moon = by_planet["Moon"]
    sun_focus, sun_edge = SIGN_LANGUAGE[sun.sign]
    moon_focus, moon_edge = SIGN_LANGUAGE[moon.sign]

    themes: list[NatalTheme] = [
        NatalTheme(
            title=f"Your core direction: {sun_focus}",
            text=(
                f"With the Sun in {sun.sign}, your chart repeatedly returns to {sun_focus}. "
                f"A productive edge is {sun_edge}. This describes a recurring orientation, not a fixed personality verdict."
            ),
            evidence=f"Sun · {sun.label()}",
        )
    ]
    if len(moon_uncertain) > 1:
        themes.append(
            NatalTheme(
                title="Your emotional pattern needs a birth time",
                text=(
                    f"The Moon moved from {moon_uncertain[0]} to {moon_uncertain[1]} during this birth date. "
                    "Luna will not choose one emotional interpretation without a reliable time."
                ),
                evidence=f"Moon · {moon_uncertain[0]} / {moon_uncertain[1]} on this date",
            )
        )
    else:
        themes.append(
            NatalTheme(
                title=f"Your emotional compass: {moon_focus}",
                text=(
                    f"The Moon in {moon.sign} describes an instinctive pull toward {moon_focus}. "
                    f"Under pressure, the useful question is whether you are {moon_edge}."
                ),
                evidence=f"Moon · {moon.label()}",
            )
        )

    # Prefer one high-value aspect touching a personal planet or Saturn/Pluto.
    preferred = [
        item for item in aspects
        if {item.planet1, item.planet2} & {"Sun", "Moon", "Mercury", "Venus", "Mars"}
        and {item.planet1, item.planet2} & {"Saturn", "Jupiter", "Uranus", "Neptune", "Pluto", "Sun", "Moon"}
    ]
    aspect = (preferred or aspects)[0] if (preferred or aspects) else None
    if aspect:
        title, text = _aspect_sentence(aspect)
        themes.append(NatalTheme(title=title, text=text, evidence=aspect.label()))

    return tuple(themes[:3])


def _dominance(positions: list[NatalPosition]) -> tuple[str, str]:
    # Weight personal planets a little more heavily while keeping the outer
    # planets in the signature. This is descriptive only, not a predictive score.
    weights = {
        "Sun": 2.0, "Moon": 2.0, "Mercury": 1.4, "Venus": 1.4, "Mars": 1.4,
        "Jupiter": 1.0, "Saturn": 1.0, "Uranus": 0.7, "Neptune": 0.7, "Pluto": 0.7,
        "True Node": 0.5,
    }
    elements = {key: 0.0 for key in {"Fire", "Earth", "Air", "Water"}}
    modalities = {key: 0.0 for key in {"Cardinal", "Fixed", "Mutable"}}
    for item in positions:
        weight = weights.get(item.planet, 1.0)
        elements[ELEMENT[item.sign]] += weight
        modalities[MODALITY[item.sign]] += weight
    return max(elements, key=elements.get), max(modalities, key=modalities.get)


def _moon_uncertainty(birth_date: date) -> tuple[str, ...]:
    early = _planet_positions(_jd_utc(birth_date, 0.0))
    late = _planet_positions(_jd_utc(birth_date, 23.999))
    early_moon = next(item for item in early if item.planet == "Moon")
    late_moon = next(item for item in late if item.planet == "Moon")
    if early_moon.sign == late_moon.sign:
        return (early_moon.sign,)
    return (early_moon.sign, late_moon.sign)


def build_natal_snapshot(
    *,
    birth_date: date,
    birth_time_known: bool,
    birth_time: time | None = None,
    timezone_name: str = "UTC",
    location_name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> NatalSnapshot:
    if birth_time_known:
        if birth_time is None:
            raise ValueError("birth_time is required when birth_time_known=True")
        jd = _jd_from_local(birth_date, birth_time, timezone_name)
    else:
        # Noon UT is a neutral calculation point for a date-only snapshot. The
        # app separately flags the Moon if it changes sign during the day and
        # never computes Ascendant, MC or houses from an unknown time.
        jd = _jd_utc(birth_date, 12.0)

    positions = _planet_positions(jd)
    ascendant = None
    midheaven = None

    if birth_time_known and latitude is not None and longitude is not None:
        ascendant, midheaven = _angles(jd, latitude, longitude)
        positions = [
            NatalPosition(
                planet=item.planet,
                longitude=item.longitude,
                sign=item.sign,
                degree=item.degree,
                retrograde=item.retrograde,
                house=_whole_sign_house(item.longitude, ascendant.longitude),
            )
            for item in positions
        ]

    aspects = detect_natal_aspects(positions)
    moon_uncertain = () if birth_time_known else _moon_uncertainty(birth_date)
    themes = _build_themes(positions, aspects, moon_uncertain=moon_uncertain)
    dominant_element, dominant_modality = _dominance(positions)

    return NatalSnapshot(
        birth_date=birth_date,
        birth_time_known=birth_time_known,
        timezone_name=timezone_name,
        location_name=location_name,
        positions=tuple(positions),
        aspects=tuple(aspects),
        ascendant=ascendant,
        midheaven=midheaven,
        moon_uncertain=moon_uncertain,
        themes=themes,
        dominant_element=dominant_element,
        dominant_modality=dominant_modality,
    )



def natal_wheel_svg(snapshot: NatalSnapshot, size: int = 640) -> str:
    """Return a restrained black-and-white SVG natal wheel.

    The wheel is evidence, not the primary interpretation. Aries is fixed at
    the left-hand horizon so a date-only chart remains comparable; when an
    exact Ascendant exists it is marked explicitly rather than silently
    rotating the whole chart.
    """
    center = size / 2.0
    outer = size * 0.375
    inner = size * 0.275
    planet_r = size * 0.305
    label_r = size * 0.415

    def xy(longitude: float, radius: float) -> tuple[float, float]:
        # 0 Aries at the left, zodiac increases counter-clockwise visually.
        angle = math.radians(180.0 - (longitude % 360.0))
        return center + radius * math.cos(angle), center + radius * math.sin(angle)

    pieces = [
        f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="Luna natal wheel" '
        'style="width:100%;max-width:680px;height:auto;display:block;margin:1rem auto 2rem;">',
        f'<circle cx="{center:.1f}" cy="{center:.1f}" r="{outer:.1f}" fill="none" stroke="#111" stroke-width="1.4"/>',
        f'<circle cx="{center:.1f}" cy="{center:.1f}" r="{inner:.1f}" fill="none" stroke="#bbb" stroke-width="1"/>',
    ]

    for index, sign in enumerate(SIGNS):
        longitude = index * 30.0
        x1, y1 = xy(longitude, inner)
        x2, y2 = xy(longitude, outer)
        pieces.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#bbb" stroke-width="1"/>'
        )
        lx, ly = xy(longitude + 15.0, label_r)
        pieces.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" '
            'font-family="monospace" font-size="11" fill="#555">'
            f'{sign[:3].upper()}</text>'
        )

    # Add a simple inner aspect web for the strongest aspects.
    by_planet = {item.planet: item for item in snapshot.positions}
    for aspect in snapshot.aspects[:8]:
        p1 = by_planet.get(aspect.planet1)
        p2 = by_planet.get(aspect.planet2)
        if not p1 or not p2:
            continue
        x1, y1 = xy(p1.longitude, inner * 0.88)
        x2, y2 = xy(p2.longitude, inner * 0.88)
        dash = ' stroke-dasharray="4 4"' if aspect.name in {"square", "opposition"} else ''
        opacity = max(0.18, min(0.55, 0.18 + aspect.strength * 0.18))
        pieces.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#333" stroke-width="1" opacity="{opacity:.2f}"{dash}/>'
        )

    short = {
        "Sun": "SUN", "Moon": "MOON", "Mercury": "MER", "Venus": "VEN",
        "Mars": "MAR", "Jupiter": "JUP", "Saturn": "SAT", "Uranus": "URA",
        "Neptune": "NEP", "Pluto": "PLU", "True Node": "NODE",
    }
    ordered = sorted(snapshot.positions, key=lambda item: item.longitude)
    last_longitude = None
    close_count = 0
    for item in ordered:
        if last_longitude is not None and angular_distance(item.longitude, last_longitude) < 8.0:
            close_count += 1
        else:
            close_count = 0
        radius = planet_r - min(close_count, 2) * 22
        px, py = xy(item.longitude, radius)
        pieces.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="#111"/>')
        pieces.append(
            f'<text x="{px:.1f}" y="{py - 9:.1f}" text-anchor="middle" '
            'font-family="monospace" font-size="10" font-weight="600" fill="#111">'
            f'{short.get(item.planet, item.planet[:4].upper())}</text>'
        )
        last_longitude = item.longitude

    if snapshot.ascendant:
        ax1, ay1 = xy(snapshot.ascendant.longitude, inner - 10)
        ax2, ay2 = xy(snapshot.ascendant.longitude, outer + 14)
        pieces.append(
            f'<line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}" stroke="#111" stroke-width="2"/>'
        )
        tx, ty = xy(snapshot.ascendant.longitude, outer + 32)
        pieces.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" '
            'font-family="monospace" font-size="11" font-weight="700">ASC</text>'
        )

    pieces.append(
        f'<text x="{center:.1f}" y="{center - 5:.1f}" text-anchor="middle" '
        'font-family="Georgia,serif" font-size="22" fill="#111">LUNA</text>'
    )
    pieces.append(
        f'<text x="{center:.1f}" y="{center + 18:.1f}" text-anchor="middle" '
        'font-family="monospace" font-size="9" letter-spacing="1.2" fill="#777">NATAL SNAPSHOT</text>'
    )
    pieces.append('</svg>')
    return ''.join(pieces)
