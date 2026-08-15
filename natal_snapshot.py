from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Iterable
import json
import math
from zoneinfo import ZoneInfo

import swisseph as swe

from astrology_engine import ASPECTS, PLANET_WEIGHTS, SIGNS, angular_distance, sign_index
from concentration_theme import build_natal_concentration_theme



NATAL_PROFILE_ORDER = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)

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
class NatalSignature:
    title: str
    text: str
    strength: str
    watch: str
    evidence: str
    question: str | None = None


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
    signatures: tuple[NatalSignature, ...]
    concentration_theme: dict
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




def _aspect_pair(aspect: NatalAspect) -> frozenset[str]:
    return frozenset((aspect.planet1, aspect.planet2))


def _signature_priority(aspect: NatalAspect) -> float:
    """Rank aspects by human interpretive value, not mathematical tightness alone.

    Personal-planet combinations that readers can recognise in everyday behaviour
    outrank tight generational contacts. Orb/strength still matters inside that
    hierarchy.
    """
    pair = _aspect_pair(aspect)
    pair_bonus = {
        frozenset(("Moon", "Saturn")): 12.0,
        frozenset(("Sun", "Moon")): 11.6,
        frozenset(("Moon", "Mercury")): 11.2,
        frozenset(("Sun", "Saturn")): 11.0,
        frozenset(("Sun", "Mercury")): 10.7,
        frozenset(("Venus", "Saturn")): 10.4,
        frozenset(("Venus", "Pluto")): 10.1,
        frozenset(("Mars", "Saturn")): 9.9,
        frozenset(("Moon", "Pluto")): 9.7,
        frozenset(("Moon", "Neptune")): 9.4,
        frozenset(("Sun", "Pluto")): 9.2,
        frozenset(("Venus", "Mars")): 8.8,
        frozenset(("Mercury", "Saturn")): 8.7,
        frozenset(("Mercury", "Pluto")): 8.5,
        frozenset(("Sun", "Jupiter")): 8.4,
        frozenset(("Moon", "Jupiter")): 8.3,
    }.get(pair, 6.0)
    aspect_bonus = {
        "conjunction": 1.25,
        "square": 1.15,
        "opposition": 1.10,
        "trine": 0.65,
        "sextile": 0.50,
    }.get(aspect.name, 0.0)
    if pair.issubset({"Uranus", "Neptune", "Pluto"}):
        pair_bonus -= 5.5
    return pair_bonus + aspect_bonus + min(1.5, aspect.strength * 0.45) - min(1.0, aspect.orb * 0.04)


def _signature_for_aspect(aspect: NatalAspect) -> NatalSignature:
    pair = _aspect_pair(aspect)
    hard = aspect.name in {"square", "opposition"}
    conjunction = aspect.name == "conjunction"

    if pair == frozenset(("Moon", "Saturn")):
        if hard or conjunction:
            return NatalSignature(
                title="Emotionally reserved",
                text=(
                    "You may feel considerably more than you show. Emotional disclosure tends to follow trust rather than create it: "
                    "until you know where you stand, the instinct can be to contain the feeling and deal with the practical situation first. "
                    "That restraint can look like distance to people who do not yet know you well."
                ),
                strength="Emotional endurance, loyalty and self-command.",
                watch="Carrying everything privately until independence becomes isolation.",
                evidence=aspect.label(),
                question="Are you protecting something valuable, or protecting yourself from being known?",
            )
        return NatalSignature(
            title="Feelings have structure",
            text="Emotion and responsibility can work together naturally. You often become steadier when other people become reactive, and reliability can be one of the ways you show care.",
            strength="Consistency under emotional pressure.",
            watch="Assuming you must always be the composed one.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Sun", "Moon")):
        if hard:
            return NatalSignature(
                title="What you want and what you need can pull apart",
                text=(
                    "A decision can make complete sense to the part of you moving forward while another part does not feel safe, satisfied or ready. "
                    "This is not necessarily indecision; it is a recurring negotiation between conscious direction and emotional need."
                ),
                strength="You can see more than one truth inside the same decision.",
                watch="Letting one side overrule the other until the conflict returns elsewhere.",
                evidence=aspect.label(),
                question="Which part of you is asking to be heard before you decide?",
            )

    if pair == frozenset(("Sun", "Mercury")) and conjunction:
        return NatalSignature(
            title="Your ideas become personal",
            text=(
                "Thinking and identity sit close together. This can give your words conviction and make it natural to communicate a coherent point of view. "
                "The complication is that disagreement may sometimes feel more personal than it actually is."
            ),
            strength="Clarity, conviction and the ability to communicate an idea as a whole.",
            watch="Confusing certainty with evidence, or criticism of an idea with criticism of you.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Moon", "Mercury")) and hard:
        return NatalSignature(
            title="Your head and feelings do not always vote together",
            text=(
                "You may understand something logically before you have emotionally accepted it, or feel something strongly before you can explain why. "
                "Under pressure, words can arrive before the feeling underneath them has been fully understood."
            ),
            strength="You can translate emotion into language once you give yourself enough processing time.",
            watch="Trying to solve a feeling before you have named it.",
            evidence=aspect.label(),
            question="What changes if you name the feeling before arguing the case?",
        )

    if pair == frozenset(("Sun", "Saturn")) and (hard or conjunction):
        return NatalSignature(
            title="Achievement asks for patience",
            text=(
                "Part of you wants movement and possibility while another part keeps asking whether the structure can actually hold. "
                "Progress can therefore feel slower or more conditional than you would prefer, but the same pattern can produce unusual staying power."
            ),
            strength="Endurance, discipline and the ability to build rather than merely begin.",
            watch="Treating every delay as proof that you should stop, or setting standards no human can meet.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Venus", "Saturn")) and (hard or conjunction):
        return NatalSignature(
            title="Affection needs proof",
            text="Warmth matters, but reliability matters more. You may take time to trust what another person feels and notice quickly when words, effort and responsibility do not match.",
            strength="Loyalty and a serious approach to commitments that matter.",
            watch="Testing love so thoroughly that spontaneity has nowhere to breathe.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Venus", "Pluto")) and (hard or conjunction):
        return NatalSignature(
            title="Attachment runs deep",
            text="Attraction and values are rarely entirely casual once they matter to you. Relationships can expose questions of trust, power, loyalty and what you are unwilling to lose.",
            strength="Depth, devotion and the capacity to transform through close bonds.",
            watch="Mistaking intensity for compatibility or control for security.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Mars", "Saturn")) and hard:
        return NatalSignature(
            title="Drive meets resistance",
            text="The impulse to act can repeatedly meet limits, duties or timing constraints. Frustrating as that can be, it can also teach you how to use force selectively rather than wasting it against every obstacle.",
            strength="Controlled effort and persistence under pressure.",
            watch="Bottling frustration until it becomes rigidity or abrupt anger.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Moon", "Pluto")) and (hard or conjunction):
        return NatalSignature(
            title="You feel beneath the surface",
            text="Emotional situations rarely stay superficial for long. You can be highly alert to subtext, loyalty and shifts in trust, even when nobody has named them directly.",
            strength="Emotional depth and strong instincts about what is really happening.",
            watch="Reading danger into ambiguity or holding on after the situation has already changed.",
            evidence=aspect.label(),
        )

    if pair == frozenset(("Moon", "Neptune")):
        return NatalSignature(
            title="Sensitive to atmosphere",
            text="You can absorb the tone of a room before anyone explains it. Imagination and empathy are strong, but boundaries become important when other people's moods are difficult to separate from your own.",
            strength="Imagination, empathy and sensitivity to nuance.",
            watch="Letting atmosphere become evidence when facts are still incomplete.",
            evidence=aspect.label(),
        )

    p1, p2 = aspect.planet1, aspect.planet2
    roles = f"{PLANET_ROLE.get(p1, p1.lower())} and {PLANET_ROLE.get(p2, p2.lower())}"
    if hard:
        return NatalSignature(
            title="Two parts of you can compete for the wheel",
            text=f"This {aspect.name} links {roles} through friction. The pattern becomes most useful when you notice which function is over-correcting and restore some choice before acting.",
            strength="Pressure can become a source of self-knowledge and deliberate skill.",
            watch="Repeating the same reaction simply because it is familiar.",
            evidence=aspect.label(),
        )
    if conjunction:
        return NatalSignature(
            title="Two instincts arrive together",
            text=f"This conjunction fuses {roles}. The combination can become a distinctive part of how you operate because one function tends to trigger the other automatically.",
            strength="Concentration and a recognisable personal style.",
            watch="Forgetting that the two functions can occasionally be separated.",
            evidence=aspect.label(),
        )
    return NatalSignature(
        title="A strength that can become automatic",
        text=f"This {aspect.name} links {roles} with relatively little friction. Because the capacity can feel natural, it becomes more valuable when you use it deliberately rather than assuming it will carry every situation.",
        strength="A cooperative connection between two parts of the chart.",
        watch="Underestimating a talent simply because it feels easy.",
        evidence=aspect.label(),
    )


def _build_signatures(aspects: list[NatalAspect], limit: int = 4) -> tuple[NatalSignature, ...]:
    if not aspects:
        return ()
    ranked = sorted(aspects, key=lambda item: (-_signature_priority(item), item.orb))
    result: list[NatalSignature] = []
    seen_titles: set[str] = set()
    for aspect in ranked:
        signature = _signature_for_aspect(aspect)
        if signature.title in seen_titles:
            continue
        result.append(signature)
        seen_titles.add(signature.title)
        if len(result) >= limit:
            break
    return tuple(result)


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
    signatures = _build_signatures(aspects)
    concentration_theme = build_natal_concentration_theme(positions)
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
        signatures=signatures,
        concentration_theme=concentration_theme,
        dominant_element=dominant_element,
        dominant_modality=dominant_modality,
    )



def encode_natal_profile(snapshot: NatalSnapshot) -> str:
    """Serialize only the derived natal geometry needed for paid personalisation.

    Raw birth date, time and birthplace are deliberately excluded. The payload is
    compact enough for Stripe metadata and can be used to reproduce natal-to-transit
    comparisons after payment without storing birth details in Stripe.
    """
    by_planet = {item.planet: item for item in snapshot.positions}
    planet_values = [round(float(by_planet[name].longitude), 3) for name in NATAL_PROFILE_ORDER]
    houses = [int(by_planet[name].house or 0) for name in NATAL_PROFILE_ORDER]
    angles = [
        round(float(snapshot.ascendant.longitude), 3) if snapshot.ascendant else None,
        round(float(snapshot.midheaven.longitude), 3) if snapshot.midheaven else None,
    ]
    signature_rows = []
    aspect_by_label = {item.label(): item for item in snapshot.aspects}
    for signature in snapshot.signatures[:4]:
        aspect = aspect_by_label.get(signature.evidence)
        if aspect:
            signature_rows.append([aspect.planet1, aspect.planet2, signature.title])
    payload = {
        "v": 1,
        "p": planet_values,
        "h": houses,
        "a": angles,
        "s": signature_rows,
        "t": 1 if snapshot.birth_time_known else 0,
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def decode_natal_profile(value: str) -> dict:
    try:
        payload = json.loads(str(value or ""))
    except Exception:
        return {}
    if not isinstance(payload, dict) or payload.get("v") != 1:
        return {}
    planets = payload.get("p")
    if not isinstance(planets, list) or len(planets) != len(NATAL_PROFILE_ORDER):
        return {}
    return payload


def natal_profile_summary(snapshot: NatalSnapshot) -> str:
    by_planet = {item.planet: item for item in snapshot.positions}
    bits = [f"Sun {by_planet['Sun'].sign}", f"Moon {by_planet['Moon'].sign}"]
    if snapshot.ascendant:
        bits.append(f"Rising {snapshot.ascendant.sign}")
    else:
        bits.append("Rising not calculated")
    return " · ".join(bits)


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
        'style="width:100%;max-width:760px;height:auto;display:block;margin:1rem auto 2.2rem;">',
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
