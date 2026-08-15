from __future__ import annotations

"""Luna concentration-theme synthesis.

This module adds the 'forest' layer to Luna's existing aspect and event engines.
It looks for several meaningful planetary functions operating through the same
sign and translates that concentration into one dominant story.  It does not
replace aspects, houses or natal contacts; it sits above them.
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Iterable

import swisseph as swe

from astrology_engine import HOUSE_NAMES, SIGNS, sign_index


TRANSIT_PLANETS = {
    "Sun": swe.SUN,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

# Personal and social planets should lead the monthly story.  Slow-planet pairs
# can describe a background era, but must not automatically outrank a visible
# concentration such as Sun + Mercury + Jupiter in one sign.
MONTHLY_WEIGHT = {
    "Sun": 4.0,
    "Mercury": 3.0,
    "Venus": 3.0,
    "Mars": 3.3,
    "Jupiter": 3.8,
    "Saturn": 3.5,
    "Uranus": 1.8,
    "Neptune": 1.7,
    "Pluto": 1.8,
}

NATAL_WEIGHT = {
    "Sun": 4.2,
    "Moon": 4.2,
    "Mercury": 3.2,
    "Venus": 3.2,
    "Mars": 3.2,
    "Jupiter": 2.6,
    "Saturn": 3.0,
    "Uranus": 1.2,
    "Neptune": 1.2,
    "Pluto": 1.2,
    "True Node": 0.6,
}

PLANET_FUNCTION = {
    "Sun": "identity and visibility",
    "Moon": "emotional needs and instinct",
    "Mercury": "thinking and communication",
    "Venus": "values, attraction and relationships",
    "Mars": "drive and action",
    "Jupiter": "growth and confidence",
    "Saturn": "standards, limits and responsibility",
    "Uranus": "freedom and reinvention",
    "Neptune": "imagination and ideals",
    "Pluto": "power and deep change",
}

SIGN_CORE = {
    "Aries": ("initiative", "something wants to begin rather than wait for perfect conditions"),
    "Taurus": ("stability and value", "the question is what deserves to be made durable"),
    "Gemini": ("movement and exchange", "information, conversation and options multiply"),
    "Cancer": ("protection and belonging", "attention gathers around what must be cared for or defended"),
    "Leo": ("visibility and authorship", "something wants to become visible rather than remain hypothetical"),
    "Virgo": ("refinement and usefulness", "the advantage comes from improving the structure, method or detail"),
    "Libra": ("relationship and reciprocity", "agreements, balance and the response of other people become harder to ignore"),
    "Scorpio": ("trust and transformation", "the deeper terms, loyalties and power dynamics move to the foreground"),
    "Sagittarius": ("expansion and meaning", "the horizon widens through learning, travel, belief or a larger possibility"),
    "Capricorn": ("structure and commitment", "what matters has to prove that it can survive responsibility and time"),
    "Aquarius": ("systems and independence", "the existing pattern is being tested against a different future"),
    "Pisces": ("sensitivity and imagination", "subtle information matters, but boundaries and clarity matter just as much"),
}

MONTHLY_HEADLINE = {
    "Aries": "Momentum gathers around a beginning",
    "Taurus": "What lasts matters more than what merely starts",
    "Gemini": "The month gathers around movement and information",
    "Cancer": "Protection becomes the organising question",
    "Leo": "Visibility wants a larger stage",
    "Virgo": "The month rewards refinement",
    "Libra": "Relationships become the negotiating table",
    "Scorpio": "The deeper terms move into view",
    "Sagittarius": "The horizon is widening",
    "Capricorn": "Commitment has to become concrete",
    "Aquarius": "The system is ready for a different pattern",
    "Pisces": "Sensitivity needs a clearer container",
}


def _calc_longitude(day: date, planet_id: int) -> float:
    jd = swe.julday(day.year, day.month, day.day, 12.0)
    try:
        values = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    except swe.Error:
        values = swe.calc_ut(jd, planet_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0]
    return float(values[0]) % 360.0


def _whole_sign_house(native_sign: str, transit_sign: str) -> int:
    return ((SIGNS.index(transit_sign) - SIGNS.index(native_sign)) % 12) + 1


def _date_label(value: date) -> str:
    return f"{value.day} {value.strftime('%b').upper()}"


def build_monthly_concentration_theme(result: dict) -> dict[str, Any]:
    """Find the strongest same-sign concentration during a monthly period.

    A cluster must contain at least two bodies and at least one personal/social
    body (Sun through Saturn). Persistence is rewarded, so a slow outer-planet
    pairing does not become the customer's headline merely because it lasts all
    month.
    """
    native_sign = str(result.get("sign") or "")
    if native_sign not in SIGNS:
        return {}

    start = result.get("start")
    end = result.get("end")
    if isinstance(start, str):
        start = date.fromisoformat(start)
    if isinstance(end, str):
        end = date.fromisoformat(end)
    if not isinstance(start, date) or not isinstance(end, date):
        return {}

    observations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    day = start
    while day <= end:
        groups: dict[str, list[str]] = defaultdict(list)
        for planet, planet_id in TRANSIT_PLANETS.items():
            longitude = _calc_longitude(day, planet_id)
            groups[SIGNS[sign_index(longitude)]].append(planet)

        for sign, planets in groups.items():
            if len(planets) < 2:
                continue
            important = [p for p in planets if p in {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}]
            if not important:
                continue
            weight = sum(MONTHLY_WEIGHT[p] for p in planets)
            # Three bodies in one sign is a qualitatively stronger story than a
            # simple pair. Reward it explicitly.
            weight += max(0, len(planets) - 2) * 2.4
            # Clusters led only by Saturn plus outer planets are background
            # climate, not normally the main monthly narrative.
            if set(important) == {"Saturn"}:
                weight *= 0.68
            observations[sign].append({"date": day, "planets": tuple(planets), "weight": weight})
        day += timedelta(days=1)

    if not observations:
        return {}

    ranked: list[tuple[float, str, list[dict[str, Any]]]] = []
    for sign, rows in observations.items():
        # Persistent concentration matters, but cap persistence so an outer
        # background does not overwhelm a shorter, much richer personal cluster.
        best = max(rows, key=lambda row: row["weight"])
        active_days = len(rows)
        persistence_bonus = min(5.0, active_days * 0.18)
        score = float(best["weight"]) + persistence_bonus
        ranked.append((score, sign, rows))
    ranked.sort(reverse=True)

    _score, sign, rows = ranked[0]
    peak = max(rows, key=lambda row: row["weight"])
    peak_planets = tuple(peak["planets"])
    active_dates = [row["date"] for row in rows]
    first_active = min(active_dates)
    last_active = max(active_dates)
    house = _whole_sign_house(native_sign, sign)
    house_name = HOUSE_NAMES[house]
    core, consequence = SIGN_CORE[sign]

    functions = [f"{p} ({PLANET_FUNCTION.get(p, p.lower())})" for p in peak_planets]
    if len(functions) > 2:
        function_text = ", ".join(functions[:-1]) + f", and {functions[-1]}"
    else:
        function_text = " and ".join(functions)

    persistence = (
        _date_label(first_active)
        if first_active == last_active
        else f"{_date_label(first_active)}–{_date_label(last_active)}"
    )
    planet_text = " + ".join(peak_planets)

    return {
        "sign": sign,
        "house": house,
        "house_name": house_name,
        "headline": MONTHLY_HEADLINE[sign],
        "signal": f"{planet_text} in {sign}",
        "planets": list(peak_planets),
        "peak_date": peak["date"].isoformat(),
        "active_days": len(rows),
        "active_range": persistence,
        "theme": core,
        "text": (
            f"The sky repeatedly gathers in {sign}, concentrating {function_text}. "
            f"For {native_sign}, that concentration lands in {house_name}. "
            f"The overriding theme is {core}: {consequence}."
        ),
        "move": (
            f"Treat {house_name} as one connected story rather than reacting to each transit separately. "
            "Ask what the cluster is collectively trying to make visible, build, change or complete."
        ),
    }


def build_natal_concentration_theme(positions: Iterable[Any]) -> dict[str, Any]:
    """Synthesize the natal chart's strongest repeated sign environments.

    This is a whole-chart summary, not another aspect interpretation.  It is
    deliberately compact so it does not duplicate 'Your strongest signatures'.
    """
    groups: dict[str, list[Any]] = defaultdict(list)
    for item in positions:
        planet = str(getattr(item, "planet", ""))
        sign = str(getattr(item, "sign", ""))
        if planet not in NATAL_WEIGHT or sign not in SIGNS:
            continue
        groups[sign].append(item)

    candidates: list[tuple[float, str, list[Any]]] = []
    for sign, items in groups.items():
        if len(items) < 2:
            continue
        planets = [str(getattr(item, "planet", "")) for item in items]
        # Require at least one personal/social body so generational pairs do not
        # become the headline of a personal reading.
        if not any(p in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"} for p in planets):
            continue
        score = sum(NATAL_WEIGHT[p] for p in planets) + max(0, len(planets) - 2) * 2.0
        candidates.append((score, sign, items))

    if not candidates:
        return {}
    candidates.sort(reverse=True)
    selected = candidates[:3]

    clusters = []
    for _score, sign, items in selected:
        planets = [str(getattr(item, "planet", "")) for item in items]
        core, consequence = SIGN_CORE[sign]
        clusters.append({
            "sign": sign,
            "planets": planets,
            "theme": core,
            "signal": f"{' + '.join(planets)} in {sign}",
            "text": consequence,
        })

    if len(clusters) == 1:
        first = clusters[0]
        summary = (
            f"{first['signal']} gives several parts of the chart the same operating climate. "
            f"The recurring emphasis is {first['theme']}: {first['text']}."
        )
    else:
        signals = ", ".join(item["signal"] for item in clusters[:-1]) + f" and {clusters[-1]['signal']}"
        themes = "; ".join(f"{item['sign']} concentrates {item['theme']}" for item in clusters)
        summary = (
            f"Several sign environments carry unusual weight: {signals}. "
            f"{themes}. Read the aspects below as the specific ways those broader climates cooperate or pull against one another."
        )

    return {"clusters": clusters, "summary": summary}
