from __future__ import annotations

"""Nature-led monthly trajectory engine for Luna Convergence.

This layer sits between raw monthly evidence and the narrator.  It asks a
question the event-led engine alone cannot answer:

    What is the sky *doing over time*?

Events remain authoritative.  The trajectory engine does not invent a plot; it
compares chronological windows, identifies where pressure/support strengthens
or weakens, and may identify a genuine countercurrent (for example romance or
creativity providing relief while work pressure builds).
"""

from calendar import month_name
from datetime import date
import re
from typing import Mapping, Sequence

from monthly_decision_engine import calculate_climate_components, choose_posture
from scenario_engine import event_importance_score

TRAJECTORY_VERSION = "1.0"

LIFE_AREAS = {
    1: "identity, energy and personal direction",
    2: "income, pricing and personal security",
    3: "communication, decisions and everyday movement",
    4: "home, family and private foundations",
    5: "romance, creativity, children and pleasure",
    6: "work, routines and wellbeing",
    7: "relationships, clients and agreements",
    8: "shared money, trust and obligations",
    9: "travel, education, publishing and the wider world",
    10: "career, reputation, authority and visible results",
    11: "friends, networks, audiences and future plans",
    12: "rest, closure and private renewal",
}

SHORT_AREAS = {
    1: "personal direction",
    2: "money and security",
    3: "communication and decisions",
    4: "home and family",
    5: "romance and creativity",
    6: "work and wellbeing",
    7: "relationships and agreements",
    8: "shared money and obligations",
    9: "travel and wider horizons",
    10: "work and career",
    11: "friends and future plans",
    12: "rest and private life",
}

COUNTERCURRENT_DOMAINS = {
    "romance": {5, 7},
}


def _value(event: object, key: str, default=None):
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _event_day(event: object) -> int:
    raw = str(_value(event, "event_date", ""))
    try:
        return int(raw[-2:])
    except Exception:
        return 0


def _event_houses(event: object) -> set[int]:
    return {int(value) for value in (_value(event, "houses", ()) or ())}


def _event_planets(event: object) -> set[str]:
    return {str(value) for value in (_value(event, "planets", ()) or ())}


def _importance(event: object, sign: str, house_weights: Mapping[int, float]) -> float:
    try:
        return float(event_importance_score(event, sign, house_weights))
    except Exception:
        return float(_value(event, "importance", 0.0) or 0.0)


def _orb(event: object) -> str:
    detail = str(_value(event, "detail", ""))
    match = re.search(r"approximately\s+([0-9.]+)°", detail, flags=re.I)
    return f"~{match.group(1)}°" if match else ""


def _aspect_label(event: object) -> str:
    title = str(_value(event, "title", ""))
    orb = _orb(event)
    return f"{title} ({orb})" if orb else title


def _is_pressure_aspect(event: object) -> bool:
    title = str(_value(event, "title", "")).lower()
    return (
        str(_value(event, "kind", "")).lower() == "aspect"
        and (" square " in f" {title} " or " opposition " in f" {title} " or str(_value(event, "polarity", "")).lower() == "pressure")
    )


def _is_support_aspect(event: object) -> bool:
    title = str(_value(event, "title", "")).lower()
    return (
        str(_value(event, "kind", "")).lower() == "aspect"
        and (" trine " in f" {title} " or " sextile " in f" {title} " or str(_value(event, "polarity", "")).lower() == "opportunity")
    )


def _top_aspects(events: Sequence[object], sign: str, house_weights: Mapping[int, float], *, pressure: bool, maximum: int = 4) -> list[str]:
    predicate = _is_pressure_aspect if pressure else _is_support_aspect
    selected = sorted(
        (event for event in events if predicate(event)),
        key=lambda event: (-_importance(event, sign, house_weights), str(_value(event, "event_date", ""))),
    )
    return [_aspect_label(event) for event in selected[:maximum]]


def _major_primary_movements(events: Sequence[object], primary_house: int, sign: str, house_weights: Mapping[int, float], maximum: int = 5) -> list[str]:
    selected = [
        event for event in events
        if primary_house in _event_houses(event)
        and str(_value(event, "kind", "")).lower() in {"ingress", "lunation", "eclipse", "station"}
        and _importance(event, sign, house_weights) >= 4.8
    ]
    selected.sort(key=lambda event: (str(_value(event, "event_date", "")), -_importance(event, sign, house_weights)))
    values: list[str] = []
    for event in selected:
        text = f"{_value(event, 'title', 'Event')} on {int(_event_day(event))} {month_name[int(str(_value(event, 'event_date'))[5:7])]}"
        if text not in values:
            values.append(text)
        if len(values) >= maximum:
            break
    return values


def _window_record(
    *,
    sign: str,
    events: Sequence[object],
    inherited_events: Sequence[object],
    monthly_arc: Mapping[str, object],
    house_weights: Mapping[int, float],
    start_day: int,
    end_day: int,
    label: str,
    include_inherited: bool = False,
) -> dict:
    selected = [event for event in events if start_day <= _event_day(event) <= end_day]
    inherited = list(inherited_events) if include_inherited else []
    components = calculate_climate_components(
        sign,
        selected,
        inherited,
        monthly_arc,
        house_weights,
    )
    return {
        "label": label,
        "start_day": start_day,
        "end_day": end_day,
        "support": round(float(components["support"]), 1),
        "friction": round(float(components["friction"]), 1),
        "uncertainty": round(float(components["uncertainty"]), 1),
        "volatility": round(float(components["volatility"]), 1),
        "capacity": round(float(components["capacity"]), 1),
        "balance": round(float(components["support"]) - float(components["friction"]), 1),
        "posture": choose_posture(components),
        "pressure_aspects": _top_aspects(selected, sign, house_weights, pressure=True),
        "support_aspects": _top_aspects(selected, sign, house_weights, pressure=False),
        "events": [dict(event) if isinstance(event, Mapping) else event for event in selected],
    }


def _trajectory_label(windows: Sequence[Mapping[str, object]]) -> tuple[str, str]:
    if not windows:
        return "mixed", "No clear chronological trajectory was available."
    first = windows[0]
    middle = windows[1] if len(windows) > 1 else windows[0]
    late = windows[-1]
    late_friction = float(late.get("friction", 0.0))
    late_balance = float(late.get("balance", 0.0))
    first_balance = float(first.get("balance", 0.0))
    middle_balance = float(middle.get("balance", 0.0))

    if late_friction >= 60 and late_balance <= -20 and late_balance <= min(first_balance, middle_balance) - 20:
        return "late_storm", "Conditions deteriorate sharply late in the month; the final window carries the month's clearest pressure concentration."
    if first_balance <= -15 and late_balance >= 10:
        return "easing", "Pressure is strongest early and improves as the month develops."
    if first_balance >= 10 and middle_balance >= 10 and late_balance >= 10:
        return "support_builds", "Support remains stronger than friction across the month."
    if late_balance <= -10 and late_balance < first_balance - 10:
        return "pressure_builds", "Pressure strengthens as the month progresses."
    if late_balance >= 10 and late_balance > first_balance + 10:
        return "support_strengthens", "Support strengthens as the month progresses."
    return "oscillating", "The month changes polarity rather than moving in one straight line; timing matters more than an average score."


def _countercurrent(
    *,
    sign: str,
    events: Sequence[object],
    windows: Sequence[Mapping[str, object]],
    house_weights: Mapping[int, float],
    primary_house: int,
    secondary_house: int,
) -> dict | None:
    # A countercurrent must be supported by direct domain evidence.  It is not a
    # bridge and does not need to cause or resolve the main story.
    for domain, houses in COUNTERCURRENT_DOMAINS.items():
        if primary_house in houses or secondary_house in houses:
            # If the domain is already a primary/secondary plot, it is not a
            # countercurrent; it belongs to the main arc in its own right.
            continue
        local_windows: list[dict] = []
        for window in windows:
            start_day = int(window["start_day"])
            end_day = int(window["end_day"])
            domain_events = [
                event for event in events
                if start_day <= _event_day(event) <= end_day and bool(_event_houses(event) & houses)
            ]
            if not domain_events:
                local_windows.append({"support": 0.0, "friction": 0.0, "balance": 0.0, "events": []})
                continue
            local_arc = {"primary_house": min(houses), "secondary_house": max(houses), "tertiary_house": None}
            components = calculate_climate_components(sign, domain_events, (), local_arc, house_weights)
            local_windows.append({
                "support": float(components["support"]),
                "friction": float(components["friction"]),
                "balance": float(components["support"]) - float(components["friction"]),
                "events": domain_events,
            })

        # Relief must have at least one material supportive aspect in early/mid month.
        relief_candidates: list[tuple[float, int, object]] = []
        for idx, local in enumerate(local_windows[:-1] or local_windows):
            for event in local.get("events", []):
                if _is_support_aspect(event) and _importance(event, sign, house_weights) >= 5.2:
                    relief_candidates.append((_importance(event, sign, house_weights), idx, event))
        if not relief_candidates:
            continue

        # Prefer the latest supportive window before the main pressure peak so
        # the countercurrent reads as part of the evolving story rather than a
        # detached early cameo. Within that window, rank by event importance.
        relief_idx = max(item[1] for item in relief_candidates)
        relief_candidates.sort(key=lambda item: (item[1] != relief_idx, -item[0]))
        relief_local = local_windows[relief_idx]
        if float(relief_local.get("support", 0.0)) < 50:
            continue

        late_local = local_windows[-1]
        late_reversal = float(late_local.get("friction", 0.0)) >= 55 and float(late_local.get("balance", 0.0)) <= -20
        support_events = [
            _aspect_label(event)
            for _, idx, event in sorted(
                (item for item in relief_candidates if item[1] <= relief_idx),
                key=lambda item: (item[1] != relief_idx, -item[0]),
            )
        ][:3]
        late_pressure_events = [
            _aspect_label(event)
            for event in late_local.get("events", [])
            if _is_pressure_aspect(event)
        ][:3]
        posture = "QUESTION" if late_reversal else "ADVANCE"
        phase = "relief_then_test" if late_reversal else "sustained_relief"
        return {
            "domain": domain,
            "label": "romance, creativity and pleasure",
            "role": "COUNTERCURRENT",
            "phase": phase,
            "window_label": str(windows[relief_idx].get("label", "middle of the month")),
            "support": round(float(relief_local.get("support", 0.0)), 1),
            "friction": round(float(relief_local.get("friction", 0.0)), 1),
            "support_evidence": support_events,
            "late_pressure_evidence": late_pressure_events,
            "recommended_posture": posture,
            "summary": (
                "Romance, creativity or pleasure offers a genuine countercurrent to the main pressure, but the late-month evidence becomes less stable; use the relief without making it carry the whole decision."
                if late_reversal
                else "Romance, creativity or pleasure provides a genuine supportive countercurrent to the main monthly pressure."
            ),
        }
    return None


def build_monthly_trajectory(
    *,
    sign: str,
    start: date,
    end: date,
    events: Sequence[object],
    inherited_events: Sequence[object] = (),
    monthly_arc: Mapping[str, object] | None = None,
    house_weights: Mapping[int, float] | None = None,
) -> dict:
    arc = dict(monthly_arc or {})
    weights = {int(key): float(value) for key, value in (house_weights or {}).items()}
    primary_house = int(arc.get("primary_house") or 1)
    secondary_house = int(arc.get("secondary_house") or primary_house)
    days = (end - start).days + 1
    first_end = min(10, days)
    middle_start = first_end + 1
    middle_end = min(20, days)
    late_start = middle_end + 1

    windows = [
        _window_record(
            sign=sign, events=events, inherited_events=inherited_events,
            monthly_arc=arc, house_weights=weights,
            start_day=1, end_day=first_end, label="early month", include_inherited=True,
        )
    ]
    if middle_start <= middle_end:
        windows.append(_window_record(
            sign=sign, events=events, inherited_events=(), monthly_arc=arc, house_weights=weights,
            start_day=middle_start, end_day=middle_end, label="mid-month",
        ))
    if late_start <= days:
        windows.append(_window_record(
            sign=sign, events=events, inherited_events=(), monthly_arc=arc, house_weights=weights,
            start_day=late_start, end_day=days, label="late month",
        ))

    trajectory, trajectory_reason = _trajectory_label(windows)
    peak = max(windows, key=lambda item: (float(item.get("friction", 0.0)), float(item.get("capacity", 0.0))))
    countercurrent = _countercurrent(
        sign=sign,
        events=events,
        windows=windows,
        house_weights=weights,
        primary_house=primary_house,
        secondary_house=secondary_house,
    )

    primary_area = LIFE_AREAS.get(primary_house, "the main life area")
    secondary_area = LIFE_AREAS.get(secondary_house, "the later consequence")
    primary_short = SHORT_AREAS.get(primary_house, primary_area)

    if trajectory == "late_storm" and countercurrent:
        headline = f"{primary_short.capitalize()} pressure tightens late; romance and creativity offer somewhere to breathe"
    elif trajectory in {"late_storm", "pressure_builds"}:
        headline = f"Pressure builds around {primary_short}; protect room to move before the peak"
    elif trajectory in {"support_builds", "support_strengthens"}:
        headline = f"Support gathers around {primary_short}; use the cleanest opening first"
    elif trajectory == "easing":
        headline = f"The pressure around {primary_short} begins to ease as the month develops"
    else:
        headline = f"The month changes gear around {primary_short}; timing matters more than momentum"

    if trajectory == "late_storm" and countercurrent:
        central_storyline = (
            f"{primary_short.capitalize()} pressure is the main weather. Romance, creativity and pleasure offer a real countercurrent earlier, "
            f"but late-month pressure spreads the consequences into {secondary_area}."
        )
    elif trajectory in {"late_storm", "pressure_builds"}:
        central_storyline = (
            f"{primary_short.capitalize()} carry the main pressure, and the consequences become harder to contain as the month moves toward {secondary_area}."
        )
    elif trajectory in {"support_builds", "support_strengthens"}:
        central_storyline = (
            f"Support gathers around {primary_short}, with {secondary_area} showing where the opening can become useful."
        )
    else:
        central_storyline = (
            f"The balance around {primary_short} changes through the month, so timing determines how {secondary_area} should be handled."
        )

    month = month_name[start.month]
    paragraphs: list[str] = []
    early = windows[0]
    middle = windows[1] if len(windows) > 1 else windows[0]
    late = windows[-1]

    paragraphs.append(
        f"{month} is not one flat condition. The main story concentrates around {primary_area}. "
        f"Early in the month support and friction are still competing ({early['support']:.0f} support / {early['friction']:.0f} friction), so movement is information before it is a verdict."
    )

    primary_movements = _major_primary_movements(events, primary_house, sign, weights)
    pressure_mid = list(middle.get("pressure_aspects") or [])
    support_mid = list(middle.get("support_aspects") or [])
    if primary_movements:
        nature = "; ".join(primary_movements[:4])
        pressure_text = f" Hard pressure is visible too: {'; '.join(pressure_mid[:3])}." if pressure_mid else ""
        support_text = f" Support is not absent: {'; '.join(support_mid[:2])}." if support_mid else ""
        paragraphs.append(
            f"By mid-month the pattern is easier to see in Nature itself: {nature}. "
            f"Those movements keep returning attention to {primary_area}.{pressure_text}{support_text} "
            "The practical question is no longer whether something is happening, but what the situation is asking you to carry."
        )

    if countercurrent:
        support_evidence = "; ".join(countercurrent.get("support_evidence") or [])
        counter_text = (
            f"A countercurrent appears through {countercurrent['label']}. "
            + (f"The supportive evidence includes {support_evidence}. " if support_evidence else "")
            + "It can provide genuine relief from the main pressure without having to solve it."
        )
        if countercurrent.get("phase") == "relief_then_test":
            late_evidence = "; ".join(countercurrent.get("late_pressure_evidence") or [])
            counter_text += (
                f" Later, that same area becomes less stable{': ' + late_evidence if late_evidence else ''}. "
                "Enjoy the relief, but keep commitments reversible."
            )
        paragraphs.append(counter_text)

    pressure_late = "; ".join(list(late.get("pressure_aspects") or [])[:4])
    if trajectory in {"late_storm", "pressure_builds"}:
        paragraphs.append(
            f"Late month is the decisive part of the story. Friction rises to {late['friction']:.0f} while support falls to {late['support']:.0f}. "
            + (f"The pressure is explicit: {pressure_late}. " if pressure_late else "")
            + f"The original {primary_short} issue can now spill into {secondary_area}. The task is not to answer every demand; it is to protect the position that still makes sense when the pressure peaks."
        )

    if trajectory == "late_storm":
        strategy = "Protect essentials, renegotiate what cannot be avoided, and let optional exposure pass. No clean easing appears inside the final September window, so preserving room to move is part of the strategy."
    elif trajectory == "pressure_builds":
        strategy = "Reduce optional exposure as pressure strengthens; negotiate the essential parts and keep the rest reversible."
    elif trajectory in {"support_builds", "support_strengthens"}:
        strategy = "Advance where support remains clean, but keep terms visible so momentum does not outrun evidence."
    else:
        strategy = "Treat timing as part of the decision: act in supportive windows and preserve optionality when the balance turns against you."
    paragraphs.append(strategy)

    return {
        "version": TRAJECTORY_VERSION,
        "trajectory": trajectory,
        "trajectory_reason": trajectory_reason,
        "headline": headline,
        "central_storyline": central_storyline,
        "primary_house": primary_house,
        "secondary_house": secondary_house,
        "primary_area": primary_area,
        "secondary_area": secondary_area,
        "windows": windows,
        "peak_window": {key: value for key, value in peak.items() if key != "events"},
        "countercurrent": countercurrent,
        "story_paragraphs": paragraphs,
        "nature_rule": "The narrator follows the changing astronomical conditions; it does not force a bridge, subplot or positive ending that the evidence does not support.",
    }
