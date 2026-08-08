from __future__ import annotations

"""Permanent first-principles contract for Luna Convergence.

This module is intentionally small, dependency-light, and separate from the
narrator. It exists so future editorial or product updates can change wording
without silently changing Luna's underlying method.

The contract is structural rather than theological:

    Nature -> Pattern -> Convergence -> Meaning -> Choice -> Experience -> Learning

The astronomical state remains authoritative. Interpretive prose is a symbolic
translation of that state, not a literal guarantee. The narrator may explain a
calculated strategy but must never overrule it.
"""

from typing import Mapping, Sequence


LUNA_FIRST_PRINCIPLES_VERSION = "1.1"

PIPELINE = (
    "Nature",
    "Pattern",
    "Convergence",
    "Meaning",
    "Choice",
    "Experience",
    "Learning",
)

FIRST_PRINCIPLES = (
    "Nature before narrative.",
    "Observation before interpretation.",
    "Pattern before prediction.",
    "Convergence before scenario.",
    "Correspondence, not literal determinism.",
    "Prominence does not equal chronology.",
    "Convergence does not imply positivity.",
    "Inaction is a legitimate move.",
    "Unknown is a legitimate answer.",
    "Cycles repeat structurally, never identically.",
    "The narrator may explain the calculation but never overrule it.",
    "Evidence may recur; interpretation must advance.",
    "Choice preserves domain asymmetry; the monthly synthesis must not flatten distinct domain moves.",
    "Every public claim must trace back to evidence.",
    "Engineering errors are corrected; interpretive errors are studied.",
    "Historical tests remain blind; expected answers are never hard-coded.",
    "The purpose is better observation and choice, not dependence on Luna.",
)


NARRATIVE_PROGRESSION_RULE = (
    "State a scenario family once.",
    "Do not repeat its full manifestation list in later narrative roles.",
    "Every subsequent paragraph must add new evidence, a new domain, a changed condition, a changed polarity, or a changed strategic implication.",
    "If a paragraph adds none of those, delete or compress it.",
)

CORRESPONDENCE_NOTE = (
    "Astrological scenarios are symbolic correspondences derived from the calculated "
    "sky pattern. They are possible manifestations, not measured probabilities or "
    "guaranteed literal events."
)

LEARNING_NOTE = (
    "A mismatch between a symbolic scenario and lived experience is calibration evidence. "
    "It should be studied without altering astronomical facts or hard-coding the expected answer."
)


def climate_label(support: float, friction: float, uncertainty: float) -> str:
    """Translate normalized evidence shares into a plain-English climate label."""
    support = float(support)
    friction = float(friction)
    uncertainty = float(uncertainty)
    if uncertainty >= 35:
        return "Unsettled / information-led"
    difference = round(support - friction, 1)
    if difference >= 15:
        return "Supportive"
    if difference >= 5:
        return "Supportive but mixed"
    if difference <= -15:
        return "Friction-dominant"
    if difference <= -5:
        return "Friction slightly dominates"
    return "Mixed / balanced"


def capacity_label(capacity_pressure: float) -> str:
    """Human-readable label for the separate 0-100 capacity-pressure index."""
    value = max(0.0, min(100.0, float(capacity_pressure)))
    if value <= 25:
        return "Low pressure / room to move"
    if value <= 45:
        return "Manageable pressure"
    if value <= 65:
        return "Selective capacity"
    if value <= 80:
        return "High pressure"
    return "Protect capacity"


def evidence_share_total(support: float, friction: float, uncertainty: float) -> float:
    return float(support) + float(friction) + float(uncertainty)


def evidence_balance(support: float, friction: float) -> float:
    """Positive means support outweighs friction; negative means friction dominates."""
    return float(support) - float(friction)


def methodology_metadata() -> dict:
    """Stable metadata that can be attached to every Luna report."""
    return {
        "version": LUNA_FIRST_PRINCIPLES_VERSION,
        "pipeline": list(PIPELINE),
        "principles": list(FIRST_PRINCIPLES),
        "correspondence_note": CORRESPONDENCE_NOTE,
        "learning_note": LEARNING_NOTE,
        "historical_test_policy": "blind_no_expected_answer_hardcodes",
        "narrator_authority": "explain_only_never_override_calculation",
        "narrative_progression_rule": list(NARRATIVE_PROGRESSION_RULE),
        "portfolio_policy": "preserve_domain_asymmetry_before_monthly_synthesis",
    }


def build_decision_trace(
    *,
    narrative_houses: Sequence[int] = (),
    support: float,
    friction: float,
    uncertainty: float,
    capacity_pressure: float,
    posture: str,
    action_truth: str,
) -> dict:
    axis = [int(house) for house in narrative_houses]
    return {
        "nature": "calculated astronomical events",
        "pattern": f"houses {axis}" if axis else "calculated event pattern",
        "convergence": " -> ".join(f"H{house}" for house in axis) if axis else "dominant connected evidence",
        "meaning": climate_label(support, friction, uncertainty),
        "choice": f"{action_truth} / {posture}",
        "capacity": capacity_label(capacity_pressure),
        "experience": "possible manifestation; not a guaranteed literal event",
        "learning": "calibrate interpretation without rewriting the sky",
    }


def validate_first_principles_contract(
    decision: Mapping[str, object],
    *,
    require_version: bool = True,
) -> dict:
    """Non-destructive QA guardrail for the permanent Luna method contract."""
    warnings: list[str] = []
    critical: list[str] = []

    version = str(decision.get("first_principles_version", ""))
    if require_version and version != LUNA_FIRST_PRINCIPLES_VERSION:
        critical.append("First-principles contract version is missing or unexpected")

    support = float(decision.get("support_score", 0.0) or 0.0)
    friction = float(decision.get("friction_score", 0.0) or 0.0)
    uncertainty = float(decision.get("uncertainty_score", 0.0) or 0.0)
    total = evidence_share_total(support, friction, uncertainty)
    if total and not 98.0 <= total <= 102.0:
        warnings.append("Support/friction/uncertainty should be normalized evidence shares near 100")

    posture = str(decision.get("posture", ""))
    truth = str(decision.get("action_truth", ""))
    expected_truth = "ACT" if posture == "ADVANCE" else "NOT ACT"
    if posture and truth != expected_truth:
        critical.append("Narrative truth gate disagrees with calculated posture")

    if str(decision.get("correspondence_note", "")) != CORRESPONDENCE_NOTE:
        warnings.append("Correspondence-not-determinism note is missing from the decision record")

    return {
        "status": "fail" if critical else ("warning" if warnings else "pass"),
        "critical": critical,
        "warnings": warnings,
    }


def build_calibration_record(
    *,
    forecast_id: str,
    calculation_snapshot: Mapping[str, object],
    observed_outcome: str = "",
    mismatch_type: str = "unreviewed",
    notes: str = "",
) -> dict:
    """Create a non-self-modifying calibration record.

    Luna does not silently rewrite weights from a single lived outcome. The record
    preserves what was calculated, what was later observed, and what kind of
    mismatch (if any) needs human review.
    """
    return {
        "first_principles_version": LUNA_FIRST_PRINCIPLES_VERSION,
        "forecast_id": str(forecast_id),
        "calculation_snapshot": dict(calculation_snapshot),
        "observed_outcome": str(observed_outcome),
        "mismatch_type": str(mismatch_type),
        "notes": str(notes),
        "learning_policy": "review_then_refine_never_rewrite_astronomy",
        "auto_reweight": False,
    }
