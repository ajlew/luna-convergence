from __future__ import annotations

"""Strategy-authority and narrative-alignment helpers for Luna monthly reports.

This module is deliberately separate from the astronomy, convergence engine and
narrator. It enforces the first-principles boundary that calculated choice must
control customer-facing advice, while preserving the underlying report data.
"""

from copy import deepcopy
from typing import Mapping

from monthly_decision_engine import DOMAIN_HOUSES


HOUSE_TO_DOMAIN = {
    house: domain
    for domain, houses in DOMAIN_HOUSES.items()
    for house in houses
}

HOUSE_LABELS = {
    1: "how you show up",
    2: "the price and payment",
    3: "the message and decision",
    4: "home and private reality",
    5: "the person or project you want",
    6: "the workload and routine",
    7: "the other person and the promise",
    8: "shared money, trust and responsibility",
    9: "the trip, course or outside opportunity",
    10: "the role and public responsibility",
    11: "the people helping build what comes next",
    12: "what needs rest or closure",
}


def _domain_for_beat(beat: Mapping[str, object]) -> str | None:
    narrative_house = beat.get("narrative_house")
    if narrative_house not in (None, ""):
        domain = HOUSE_TO_DOMAIN.get(int(narrative_house))
        if domain:
            return domain
    for house in beat.get("direct_houses") or beat.get("houses") or ():
        domain = HOUSE_TO_DOMAIN.get(int(house))
        if domain:
            return domain
    return None


def _response_for(posture: str, role: str) -> str:
    posture = str(posture or "QUESTION").upper()
    role = str(role or "").lower()
    if posture == "ADVANCE":
        return (
            "Advance on the part that has now proved itself; keep timing, cost and ownership visible."
            if role in {"climax", "resolution"}
            else "Make the next supported step concrete, then let the response become further evidence."
        )
    if posture == "QUESTION":
        return "Ask the question this development makes unavoidable and keep the next move reversible until the answer is usable."
    if posture == "NEGOTIATE":
        return "Use this evidence to name the term that must change before you increase commitment."
    if posture == "HOLD":
        return "Do what is essential. Keep the rest reversible until the facts improve."
    if posture == "PASS":
        return "Do not chase this development; let the optional demand pass and protect time, money and freedom of movement."
    return "Let the evidence determine the move rather than the excitement of the moment."


def align_monthly_arc_with_decision(
    monthly_arc: Mapping[str, object] | None,
    decision: Mapping[str, object] | None,
) -> dict:
    """Return a non-destructive arc copy whose advice obeys the calculated strategy."""
    arc = deepcopy(dict(monthly_arc or {}))
    if not arc or not decision:
        return arc

    domains = dict(decision.get("domain_decisions") or {})
    overall_posture = str(decision.get("posture") or "QUESTION")
    aligned = []
    for raw in arc.get("beats") or []:
        beat = deepcopy(dict(raw))
        domain = _domain_for_beat(beat)
        domain_decision = dict(domains.get(domain) or {}) if domain else {}
        posture = str(domain_decision.get("posture") or overall_posture)
        beat["strategy_domain"] = domain or "overall"
        beat["strategy_posture"] = posture
        beat["response"] = _response_for(posture, str(beat.get("role") or ""))
        aligned.append(beat)
    arc["beats"] = aligned
    arc["strategy_aligned"] = True
    return arc


def strategy_rule(decision: Mapping[str, object] | None) -> str:
    decision = dict(decision or {})
    portfolio = str(decision.get("portfolio_posture") or "").upper()
    rules = {
        "FULL ADVANCE": "Follow the evidence that keeps strengthening; increase commitment only where the terms remain visible.",
        "SELECTIVE ADVANCE": "Advance where support is clean. Negotiate mixed terms. Let poor-risk/reward demands pass.",
        "TIMED ADVANCE": "Keep the hard-to-reverse part open. Move when the evidence improves.",
        "PROBE": "Use the month to improve information before you improve commitment.",
        "RENEGOTIATE": "Visibility is leverage, not permission. Change the terms before you change your exposure.",
        "DEFENSIVE HOLD": "Protect capacity. Do only what must be done until the immediate pressure passes.",
        "PASS": "Not every opening deserves a move. Preserve the position when waiting costs less than being wrong.",
    }
    if portfolio in rules:
        return rules[portfolio]

    posture = str(decision.get("posture") or "QUESTION").upper()
    return {
        "ADVANCE": "Make the supported move concrete and let the next response become evidence.",
        "QUESTION": "Ask before committing; the missing answer matters more than the first impression.",
        "NEGOTIATE": "Change the terms before increasing commitment.",
        "HOLD": "Keep the hard-to-reverse part open while the facts are still moving.",
        "PASS": "Let the optional demand pass when the downside is larger than the clean upside.",
    }.get(posture, "Let the evidence determine the move.")


def climate_aware_storyline(
    original: str,
    decision: Mapping[str, object] | None,
    *,
    primary_house: int,
    secondary_house: int,
) -> str:
    """Temper only clearly friction-dominant top-line copy; otherwise preserve it."""
    decision = dict(decision or {})
    climate = str(decision.get("climate_label") or "")
    portfolio = str(decision.get("portfolio_posture") or "").upper()
    needs_tempering = climate.lower().startswith("friction") or portfolio in {"RENEGOTIATE", "DEFENSIVE HOLD", "PASS"}
    if not needs_tempering:
        return original

    primary = HOUSE_LABELS.get(int(primary_house), f"house {primary_house}")
    secondary = HOUSE_LABELS.get(int(secondary_house), f"house {secondary_house}")
    if int(primary_house) == int(secondary_house):
        return f"{primary.capitalize()} moves into view, but the terms matter more than the invitation."
    return f"{primary.capitalize()} moves first; the later test is whether {secondary} can make the result workable."


def climate_aware_hook(
    original: str,
    decision: Mapping[str, object] | None,
    *,
    primary_house: int,
    secondary_house: int,
) -> str:
    decision = dict(decision or {})
    portfolio = str(decision.get("portfolio_posture") or "").upper()
    if portfolio == "PASS":
        return "Not every visible opening deserves a move"
    if portfolio == "DEFENSIVE HOLD":
        return "Visibility rises; capacity decides what deserves a response"
    if portfolio == "RENEGOTIATE":
        return "The opening matters, but the terms decide what is worth keeping"
    if portfolio == "TIMED ADVANCE":
        return "The difficult opening does not own the whole month; wait for the cleaner window"
    if portfolio == "PROBE":
        return "The next answer matters more than the first signal"
    return original


def strategy_do_dont(
    do_line: str,
    dont_line: str,
    decision: Mapping[str, object] | None,
) -> tuple[str, str]:
    decision = dict(decision or {})
    portfolio = str(decision.get("portfolio_posture") or "").upper()
    overrides = {
        "FULL ADVANCE": (
            "Make the strongest supported move concrete and keep the terms visible.",
            "Assume momentum excuses unclear ownership, timing or cost.",
        ),
        "SELECTIVE ADVANCE": (
            "Advance the domain that has earned it; keep the other decisions separate.",
            "Turn one green light into permission everywhere.",
        ),
        "TIMED ADVANCE": (
            "Keep the difficult opening reversible, then use the cleaner window when support has earned it.",
            "Carry an early defensive posture forward after the conditions have materially improved.",
        ),
        "PROBE": (
            "Ask the question that would materially change the decision.",
            "Treat incomplete information as a yes.",
        ),
        "RENEGOTIATE": (
            "Make the terms visible and ask for the version that actually works.",
            "Accept the first offer simply to end uncertainty.",
        ),
        "DEFENSIVE HOLD": (
            "Protect the essential position and keep optional commitments reversible.",
            "Take on extra exposure because pressure is demanding an answer.",
        ),
        "PASS": (
            "Protect time, money and optionality; let the weak contest pass.",
            "Play every ball simply because it arrives.",
        ),
    }
    return overrides.get(portfolio, (do_line, dont_line))
