from __future__ import annotations

"""Nature-led monthly trajectory engine for Luna Convergence.

This layer sits between raw monthly evidence and the narrator.  It asks a
question the event-led engine alone cannot answer:

    What is the sky *doing over time*?

Events remain authoritative.  The trajectory engine does not invent a plot; it
compares chronological windows, identifies where pressure/support strengthens
or weakens, and may identify genuine Relief (for example romance or creativity providing
room to breathe while work pressure builds).
"""

from calendar import month_name
from datetime import date
import re
from typing import Mapping, Sequence

from monthly_decision_engine import calculate_climate_components, choose_posture
from scenario_engine import event_importance_score

TRAJECTORY_VERSION = "1.2"

LIFE_AREAS = {
    1: "how you show up and what you are willing to carry",
    2: "the price, payment or purchase in front of you",
    3: "the message, document or conversation that needs an answer",
    4: "home and the arrangement you live with every day",
    5: "the person, pleasure or creative project pulling your attention",
    6: "the workload and routine your ordinary week has to sustain",
    7: "the person across the table and the promises between you",
    8: "money, trust and responsibility you share with someone else",
    9: "the trip, course, application or outside opportunity in front of you",
    10: "the job, role or public responsibility with your name on it",
    11: "the friends, groups and plans shaping what you build next",
    12: "what needs privacy, rest or a clean ending",
}

SHORT_AREAS = {
    1: "how you show up",
    2: "money and price",
    3: "the message and decision",
    4: "home and family",
    5: "the person or project you want",
    6: "workload and routine",
    7: "the other person and the promise",
    8: "shared money and responsibility",
    9: "the trip or outside opportunity",
    10: "the role and responsibility",
    11: "friends and the next plan",
    12: "rest and closure",
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


def _top_aspects(events: Sequence[object], sign: str, house_weights: Mapping[int, float], *, pressure: bool, maximum: int = 5) -> list[str]:
    """Return the strongest unique aspects for a window.

    The evidence sentence and the counted contacts must refer to the same unique
    events.  Duplicate aspect rows can appear upstream when an event contributes
    to more than one cluster; customer evidence must never count the same aspect
    twice.
    """
    predicate = _is_pressure_aspect if pressure else _is_support_aspect
    selected = sorted(
        (event for event in events if predicate(event)),
        key=lambda event: (-_importance(event, sign, house_weights), str(_value(event, "event_date", ""))),
    )
    values: list[str] = []
    seen: set[tuple[str, str]] = set()
    for event in selected:
        key = str(_value(event, "title", "")).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        values.append(_aspect_label(event))
        if len(values) >= maximum:
            break
    return values


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
    best_later = max(middle_balance, late_balance)

    if late_friction >= 60 and late_balance <= -20 and late_balance <= min(first_balance, middle_balance) - 20:
        return "late_storm", "Conditions deteriorate sharply late in the month; the final window carries the month's clearest pressure concentration."
    if first_balance <= -15 and best_later >= 10 and late_balance >= first_balance + 15 and late_friction < 55:
        return "recovery", "The month opens under pressure, then materially improves; timing matters because the cleaner opportunity arrives after the difficult start."
    if first_balance <= -10 and late_balance >= 0 and late_balance >= first_balance + 10:
        return "easing", "Pressure is strongest early and eases as the month develops; later choices have more room than the opening did."
    if first_balance >= 10 and middle_balance >= 10 and late_balance >= 10:
        return "support_builds", "Support remains stronger than friction across the month."
    if late_balance <= -10 and late_balance < first_balance - 10:
        return "pressure_builds", "Pressure strengthens as the month progresses."
    if late_balance >= 10 and late_balance > first_balance + 10:
        return "support_strengthens", "Support strengthens as the month progresses."
    if first_balance * late_balance < 0:
        return "reversal", "The balance reverses during the month; the correct move changes with the timing rather than with the monthly average."
    return "oscillating", "The month changes polarity rather than moving in one straight line; timing matters more than an average score."



def _window_posture(trajectory: str, windows: Sequence[Mapping[str, object]], index: int) -> str:
    """Choose the move for a window using both present conditions and direction of travel.

    A strong current window is not treated identically when a storm is clearly
    approaching, and a difficult opening is not allowed to dictate the whole
    month when the evidence is materially improving.
    """
    window = windows[index]
    balance = float(window.get("balance", 0.0))
    support = float(window.get("support", 0.0))
    friction = float(window.get("friction", 0.0))

    if trajectory == "late_storm":
        if index == len(windows) - 1:
            return "HOLD" if support >= 15 else "PASS"
        return "HOLD"
    if trajectory == "pressure_builds":
        return "NEGOTIATE" if index == 0 and balance > -10 else "HOLD"
    if trajectory in {"recovery", "easing"}:
        if index == 0 and balance < 0:
            return "NEGOTIATE" if friction < 70 else "HOLD"
        if balance >= 10:
            return "ADVANCE"
        if balance >= 0:
            return "QUESTION"
        return "HOLD"
    if trajectory in {"support_builds", "support_strengthens"}:
        return "ADVANCE" if balance >= 0 else "QUESTION"
    if trajectory == "reversal":
        if balance >= 10:
            return "ADVANCE"
        if balance <= -10:
            return "HOLD"
        return "QUESTION"
    return str(window.get("posture") or "QUESTION")


def _trajectory_portfolio(trajectory: str) -> tuple[str, str, tuple[str, ...]]:
    if trajectory in {"recovery", "easing"}:
        return (
            "TIMED ADVANCE",
            "Do not let the difficult opening dictate the whole month. Keep the early choice reversible. Move when the evidence improves.",
            (
                "Keep the opening reversible while the pressure is still dominant.",
                "Reassess when the evidence improves; advance only in the window that has earned it.",
                "Do not carry an early defensive posture forward after Nature has changed the conditions.",
            ),
        )
    if trajectory == "late_storm":
        return (
            "DEFENSIVE HOLD",
            "Do the essential thing while the window is cleaner. Stop adding commitments before the late-month pressure builds.",
            (
                "Finish the essential move before the late-month pressure builds.",
                "Renegotiate the commitment you cannot remove. Put the new term in writing.",
                "Let the non-essential demand pass until the immediate pressure eases.",
            ),
        )
    if trajectory == "pressure_builds":
        return (
            "DEFENSIVE HOLD",
            "Keep room to move. Stop adding commitments while the month is getting harder to carry.",
            (
                "Use the early information. Keep the hard-to-reverse decision open.",
                "Tighten the terms when the cost rises.",
                "Protect your time, money and energy near the hardest window.",
            ),
        )
    if trajectory in {"support_builds", "support_strengthens"}:
        return (
            "SELECTIVE ADVANCE",
            "Use the cleanest opening. Do not turn one good signal into permission to say yes to everything.",
            (
                "Make the cleanest supported move.",
                "Keep the cost, date and owner visible as momentum grows.",
                "Keep the unsupported part reversible.",
            ),
        )
    if trajectory == "reversal":
        return (
            "PROBE",
            "Let the month change your answer. Test each window before you increase commitment.",
            (
                "Make the smallest move that gives you better information.",
                "Change the plan when the evidence changes. Stop defending an old answer.",
                "Commit only after the new direction survives ordinary life.",
            ),
        )
    return (
        "PROBE",
        "Let each window earn its own answer. Stop forcing one rule across the whole month.",
        (
            "Treat each major window as a new decision.",
            "Move only where the support is clear.",
            "Keep the rest easy to change until the pattern settles.",
        ),
    )

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
            "public_role": "RELIEF",
            "phase": phase,
            "window_label": str(windows[relief_idx].get("label", "middle of the month")),
            "support": round(float(relief_local.get("support", 0.0)), 1),
            "friction": round(float(relief_local.get("friction", 0.0)), 1),
            "support_evidence": support_events,
            "late_pressure_evidence": late_pressure_events,
            "recommended_posture": posture,
            "summary": (
                "Romance, creativity or pleasure offers genuine relief from the main pressure, but the late-month evidence becomes less stable; use the relief without making it carry the whole decision."
                if late_reversal
                else "Romance, creativity or pleasure provides genuine relief from the main monthly pressure."
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
    for index, window in enumerate(windows):
        window["raw_posture"] = str(window.get("posture") or "QUESTION")
        window["posture"] = _window_posture(trajectory, windows, index)
    trajectory_portfolio, trajectory_portfolio_reason, trajectory_portfolio_plan = _trajectory_portfolio(trajectory)
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

    tertiary_house_raw = arc.get("tertiary_house")
    tertiary_house = int(tertiary_house_raw) if tertiary_house_raw not in (None, "") else None
    bridge = None
    if tertiary_house and tertiary_house not in {primary_house, secondary_house}:
        bridge_area = LIFE_AREAS.get(tertiary_house, "the connecting life area")
        bridge_short = SHORT_AREAS.get(tertiary_house, bridge_area)
        bridge_events = [
            event for event in events
            if tertiary_house in _event_houses(event)
            and str(_value(event, "kind", "")).lower() in {"ingress", "lunation", "eclipse", "station"}
            and float(_value(event, "importance", 0.0) or 0.0) >= 4.8
        ]
        bridge_events.sort(key=lambda event: (str(_value(event, "event_date", "")), -float(_value(event, "importance", 0.0) or 0.0)))
        bridge_movements = []
        for event in bridge_events:
            event_date = str(_value(event, "event_date", ""))
            try:
                month_label = month_name[int(event_date[5:7])]
            except Exception:
                month_label = ""
            text = f"{_value(event, 'title', 'Event')} on {_event_day(event)} {month_label}".strip()
            if text not in bridge_movements:
                bridge_movements.append(text)
            if len(bridge_movements) >= 4:
                break
        movement_text = "; ".join(bridge_movements[:3])
        bridge_summary = (
            f"{bridge_short.capitalize()} form the bridge between {primary_area} and {secondary_area}."
        )
        if movement_text:
            bridge_summary += f" The bridge is visible in Nature: {movement_text}."
        bridge = {
            "house": tertiary_house,
            "area": bridge_area,
            "short": bridge_short,
            "movements": bridge_movements,
            "summary": bridge_summary,
        }

    # Make the portfolio strategy name the life area and the timing it applies to.
    # This avoids outputs such as "TIMED ADVANCE" without telling the reader what
    # is actually safe to advance.
    if trajectory in {"recovery", "easing"}:
        trajectory_portfolio_reason = (
            f"Keep the early {primary_short} problem reversible; use the mid-month improvement to advance the part that has become workable, then judge later developments involving {secondary_area} on their own evidence."
        )
        trajectory_portfolio_plan = (
            f"Negotiate {primary_short} conditions while the difficult opening is still dominant.",
            f"Advance the workable part of {primary_short} once support materially improves.",
            f"Question later developments involving {secondary_area} before increasing commitment.",
        )
    elif trajectory in {"support_builds", "support_strengthens"}:
        bridge_phrase = f" Use {bridge['short']} as the route between the opening and the later result." if bridge else ""
        trajectory_portfolio_reason = (
            f"Support strengthens around {primary_short}; advance the clean professional or practical opening without generalising that permission to every domain.{bridge_phrase}"
        )
        trajectory_portfolio_plan = (
            f"Use the strongest supported move around {primary_short}.",
            (f"Let {bridge['short']} carry information and introductions between the opening and the later result." if bridge else "Keep the cost, date and owner visible as momentum grows."),
            f"Keep {secondary_area} selective where its own terms remain mixed.",
        )
    elif trajectory in {"late_storm", "pressure_builds"}:
        trajectory_portfolio_reason = (
            f"Use the cleaner early or middle window for essential {primary_short} decisions, then reduce exposure before late pressure spreads into {secondary_area}."
        )
        trajectory_portfolio_plan = (
            f"Complete essential {primary_short} moves before the pressure peak where possible.",
            "Renegotiate the commitment you cannot remove. Put the new term in writing.",
            f"Let optional exposure pass when late pressure spreads into {secondary_area}.",
        )

    if trajectory == "late_storm" and countercurrent:
        headline = f"{primary_short.capitalize()} pressure tightens late; romance and creativity offer somewhere to breathe"
    elif trajectory in {"late_storm", "pressure_builds"}:
        headline = f"Pressure builds around {primary_short}; protect room to move before the peak"
    elif trajectory in {"support_builds", "support_strengthens"}:
        headline = f"Support gathers around {primary_short}; use the cleanest opening first"
    elif trajectory == "recovery":
        headline = f"A difficult opening around {primary_short} begins to loosen; the second half gives you more room to move"
    elif trajectory == "easing":
        headline = f"The pressure around {primary_short} begins to ease as the month develops"
    elif trajectory == "reversal":
        headline = f"The balance around {primary_short} reverses; timing matters more than the monthly average"
    else:
        headline = f"The month changes gear around {primary_short}; timing matters more than momentum"

    if trajectory == "late_storm" and countercurrent:
        central_storyline = (
            f"{primary_short.capitalize()} pressure is the main weather. Romance, creativity and pleasure offer real relief earlier, "
            f"but late-month pressure spreads the consequences into {secondary_area}."
        )
    elif trajectory in {"late_storm", "pressure_builds"}:
        central_storyline = (
            f"{primary_short.capitalize()} carry the main pressure, and the consequences become harder to contain as the month moves toward {secondary_area}."
        )
    elif trajectory in {"support_builds", "support_strengthens"}:
        if bridge:
            central_storyline = (
                f"Support gathers around {primary_short}; {bridge['short']} carry the opening toward {secondary_area}, where the later result becomes clearer."
            )
        else:
            central_storyline = (
                f"Support gathers around {primary_short}, with {secondary_area} showing where the opening can become useful."
            )
    elif trajectory in {"recovery", "easing"}:
        central_storyline = (
            f"{primary_short.capitalize()} carry the difficult opening, but the balance improves as the month develops; later conditions give {secondary_area} more room than the opening did."
        )
    elif trajectory == "reversal":
        central_storyline = (
            f"The balance around {primary_short} changes direction during the month, so {secondary_area} must be judged by the window in which it arrives rather than by the monthly average."
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

    early_balance = float(early.get("balance", 0.0))
    early_phrase = (
        "support is cleaner than friction" if early_balance >= 10
        else "friction is stronger than support" if early_balance <= -10
        else "support and friction are still competing"
    )
    paragraphs.append(
        f"{month} is not one flat condition. The main story concentrates around {primary_area}. "
        f"Early in the month {early_phrase}, so movement is information before it is a verdict."
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

    if bridge:
        paragraphs.append(bridge["summary"] + " It is not a separate third story; it is the route through which the opening reaches the later result.")

    if countercurrent:
        support_evidence = "; ".join(countercurrent.get("support_evidence") or [])
        counter_text = (
            f"Relief appears through {countercurrent['label']}. "
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
            "Late month is the decisive part of the story. Friction rises to a clearly dominant level while support falls away. "
            + (f"The pressure is explicit: {pressure_late}. " if pressure_late else "")
            + f"The original {primary_short} issue can now spill into {secondary_area}. The task is not to answer every demand; it is to protect the position that still makes sense when the pressure peaks."
        )

    if trajectory == "late_storm":
        strategy = "Protect essentials, renegotiate what cannot be avoided, and let optional exposure pass. No clean easing appears inside the final window, so preserving room to move is part of the strategy."
    elif trajectory == "pressure_builds":
        strategy = "Reduce optional exposure as pressure strengthens; negotiate the essential parts and keep the rest reversible."
    elif trajectory in {"recovery", "easing"}:
        strategy = "Do not let the difficult opening dictate the whole month. Keep the early choice reversible. Move when the evidence improves."
    elif trajectory in {"support_builds", "support_strengthens"}:
        strategy = "Advance where support remains clean, but keep terms visible so momentum does not outrun evidence."
    elif trajectory == "reversal":
        strategy = "The correct move changes with the timing. Keep early decisions reversible and change posture when the sky has genuinely changed direction."
    else:
        strategy = "Treat timing as part of the decision. Move when support is real. Keep the hard-to-reverse part open when it is not."
    paragraphs.append(strategy)

    return {
        "version": TRAJECTORY_VERSION,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
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
        "relief": countercurrent,
        "bridge": bridge,
        "portfolio_posture": trajectory_portfolio,
        "portfolio_rationale": trajectory_portfolio_reason,
        "portfolio_action_plan": trajectory_portfolio_plan,
        "story_paragraphs": paragraphs,
        "nature_rule": "The narrator follows the changing astronomical conditions; it does not force a bridge, subplot or positive ending that the evidence does not support.",
    }
