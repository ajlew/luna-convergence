from __future__ import annotations

"""Personal natal overlay for Luna paid Monthly reports.

The checkout stores only derived natal geometry, never raw birth date/time/place,
so the paid report can compare the month's transits with the customer's natal
chart without exposing birth details in Stripe metadata.
"""

from datetime import date
from typing import Any

import swisseph as swe

from astrology_engine import ASPECTS, SIGNS, angular_distance, sign_index
from natal_snapshot import NATAL_PROFILE_ORDER, decode_natal_profile

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

TARGET_ROLE = {
    "Sun": "identity and direction",
    "Moon": "emotional needs and habits",
    "Mercury": "thinking and communication",
    "Venus": "attachment, values and relationships",
    "Mars": "drive, assertion and conflict",
    "Jupiter": "growth, confidence and belief",
    "Saturn": "standards, limits and responsibility",
    "Ascendant": "self-presentation and the way you meet the world",
    "Midheaven": "career direction, reputation and public life",
}

TARGET_FOCUS = {
    "Sun": "identity and direction",
    "Moon": "emotional footing",
    "Mercury": "thinking and communication",
    "Venus": "relationships and values",
    "Mars": "drive and assertion",
    "Jupiter": "growth pattern",
    "Saturn": "limits and responsibilities",
    "Ascendant": "sense of self",
    "Midheaven": "public direction",
}

TRANSIT_WEIGHT = {
    "Sun": 2.6,
    "Mercury": 2.1,
    "Venus": 2.2,
    "Mars": 2.8,
    "Jupiter": 3.5,
    "Saturn": 4.5,
    "Uranus": 4.4,
    "Neptune": 4.2,
    "Pluto": 4.8,
}

TARGET_WEIGHT = {
    "Sun": 5.0,
    "Moon": 5.0,
    "Mercury": 4.0,
    "Venus": 4.2,
    "Mars": 4.2,
    "Jupiter": 3.2,
    "Saturn": 3.8,
    "Ascendant": 4.8,
    "Midheaven": 4.8,
}

ASPECT_WEIGHT = {
    "conjunction": 2.2,
    "square": 2.0,
    "opposition": 1.9,
    "trine": 1.35,
    "sextile": 1.0,
}

# Tight monthly natal contacts. These are intentionally smaller than the broad
# natal-aspect orbs because the paid overlay is trying to identify material
# activations, not every possible background connection.
OVERLAY_ORB = {
    "conjunction": 1.8,
    "square": 1.8,
    "opposition": 1.8,
    "trine": 1.5,
    "sextile": 1.2,
}


def _calc_lon(day: date, planet_id: int) -> float:
    jd = swe.julday(day.year, day.month, day.day, 12.0)
    try:
        values = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    except swe.Error:
        values = swe.calc_ut(jd, planet_id, swe.FLG_MOSEPH | swe.FLG_SPEED)[0]
    return float(values[0]) % 360.0


def _sign_degree(longitude: float) -> str:
    idx = sign_index(longitude)
    degree = longitude % 30.0
    whole = int(degree)
    minute = int(round((degree - whole) * 60))
    if minute == 60:
        whole += 1
        minute = 0
    return f"{whole}°{minute:02d}′ {SIGNS[idx]}"


def _profile_targets(profile: dict[str, Any]) -> dict[str, float]:
    values = profile.get("p") or []
    targets: dict[str, float] = {}
    for name, longitude in zip(NATAL_PROFILE_ORDER, values):
        # Keep the paid overlay centred on personal/social planets and Saturn.
        # Outer natal planets remain available in the full evidence layer but
        # do not dominate the customer's three headline activations.
        if name in TARGET_WEIGHT:
            targets[name] = float(longitude) % 360.0
    angles = profile.get("a") or []
    if len(angles) >= 2:
        if angles[0] is not None:
            targets["Ascendant"] = float(angles[0]) % 360.0
        if angles[1] is not None:
            targets["Midheaven"] = float(angles[1]) % 360.0
    return targets


def _signature_rows(profile: dict[str, Any]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for row in profile.get("s") or []:
        if isinstance(row, list) and len(row) == 3:
            rows.append((str(row[0]), str(row[1]), str(row[2])))
    return rows


def _signature_for_target(signatures: list[tuple[str, str, str]], target: str) -> str:
    for p1, p2, title in signatures:
        if target in {p1, p2}:
            return title
    return ""


def _aspect_copy(aspect: str, target: str) -> tuple[str, str, str]:
    role = TARGET_ROLE.get(target, target.lower())
    focus = TARGET_FOCUS.get(target, role)
    if aspect == "conjunction":
        return (
            f"Your {focus} moves to the foreground",
            f"This transit lands directly on your natal {target}, so the month's general story becomes more personal here.",
            "Use the extra emphasis deliberately; do not assume intensity by itself is a verdict.",
        )
    if aspect in {"square", "opposition"}:
        return (
            f"Pressure builds around your {focus}",
            f"This transit presses against your natal {target}. The useful question is what the pressure exposes about the way you normally handle this part of life.",
            "Reduce avoidable commitments until the source of the pressure is clearer.",
        )
    if aspect == "trine":
        return (
            f"Support opens around your {focus}",
            f"This transit forms a supportive trine to your natal {target}, making this one of the easier places to use the month's momentum constructively.",
            "Use the opening while it is available; ease is most valuable when it becomes a concrete move.",
        )
    return (
        f"An opening appears around your {focus}",
        f"This transit forms a sextile to your natal {target}. It is an opportunity rather than a guarantee, and it becomes useful when you respond to it.",
        "Give the opening one practical next step rather than waiting for it to develop on its own.",
    )


def build_monthly_natal_overlay(profile_value: str, result: dict, *, limit: int = 3) -> dict:
    profile = decode_natal_profile(profile_value)
    if not profile:
        return {}

    start = result.get("start")
    end = result.get("end")
    if isinstance(start, str):
        start = date.fromisoformat(start)
    if isinstance(end, str):
        end = date.fromisoformat(end)
    if not isinstance(start, date) or not isinstance(end, date):
        return {}

    targets = _profile_targets(profile)
    signatures = _signature_rows(profile)
    if not targets:
        return {}

    candidates: list[dict[str, Any]] = []
    day = start
    while day <= end:
        for transit_name, planet_id in TRANSIT_PLANETS.items():
            transit_lon = _calc_lon(day, planet_id)
            for target_name, natal_lon in targets.items():
                # Avoid same-planet slow returns dominating unless the geometry
                # is genuinely exact and therefore meaningful.
                distance = angular_distance(transit_lon, natal_lon)
                for aspect_name, (angle, _wide_orb) in ASPECTS.items():
                    if aspect_name not in OVERLAY_ORB:
                        continue
                    orb = abs(distance - angle)
                    allowed = OVERLAY_ORB[aspect_name]
                    if orb > allowed:
                        continue
                    signature_title = _signature_for_target(signatures, target_name)
                    closeness = max(0.0, 1.0 - orb / allowed)
                    score = (
                        TRANSIT_WEIGHT.get(transit_name, 2.0)
                        + TARGET_WEIGHT.get(target_name, 3.0)
                        + ASPECT_WEIGHT.get(aspect_name, 1.0)
                        + closeness * 3.0
                        + (1.0 if signature_title else 0.0)
                    )
                    title, text, move = _aspect_copy(aspect_name, target_name)
                    candidates.append(
                        {
                            "date": day.isoformat(),
                            "date_label": f"{day.day:02d} {day.strftime('%b').upper()}",
                            "transit": transit_name,
                            "target": target_name,
                            "aspect": aspect_name,
                            "orb": round(orb, 2),
                            "signal": f"Transit {transit_name} {aspect_name} natal {target_name} · {orb:.1f}°",
                            "natal_position": _sign_degree(natal_lon),
                            "title": title,
                            "text": text,
                            "move": move,
                            "signature": signature_title,
                            "score": score,
                        }
                    )
                    break
        day = date.fromordinal(day.toordinal() + 1)

    if not candidates:
        return {
            "summary": "The month does not form a tight major contact to Luna's highest-priority natal points. The sign-level monthly storyline remains the stronger signal.",
            "activations": [],
            "time_known": bool(profile.get("t")),
        }

    # For each transit/target/aspect keep the closest day only. This turns a
    # multi-day orb into one newspaper-style date rather than repeating it.
    best_by_contact: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in candidates:
        key = (item["transit"], item["target"], item["aspect"])
        current = best_by_contact.get(key)
        if current is None or item["orb"] < current["orb"]:
            best_by_contact[key] = item

    ranked = sorted(best_by_contact.values(), key=lambda item: (-float(item["score"]), float(item["orb"])))
    selected: list[dict[str, Any]] = []
    used_targets: set[str] = set()
    for item in ranked:
        # Encourage breadth across the person's chart. A second contact to the
        # same natal point is allowed only if the first pass cannot fill three.
        if item["target"] in used_targets and len(selected) < limit:
            continue
        selected.append(item)
        used_targets.add(item["target"])
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        for item in ranked:
            if item in selected:
                continue
            selected.append(item)
            if len(selected) >= limit:
                break

    selected.sort(key=lambda item: item["date"])
    return {
        "summary": f"Luna found {len(selected)} tight monthly contacts to the natal chart. These do not replace the sign forecast; they show where the same month becomes personally concentrated.",
        "activations": selected,
        "time_known": bool(profile.get("t")),
    }
