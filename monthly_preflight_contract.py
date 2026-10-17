"""Deterministic, pre-provider checks for Luna's paid Monthly prose request.

This module never receives or examines generated prose.
"""
from __future__ import annotations

from datetime import date
from calendar import monthrange

class MonthlyPreflightError(ValueError):
    pass


def validate_monthly_facts(facts: dict) -> None:
    """Validate the small set of indispensable facts before a chargeable request."""
    if not isinstance(facts, dict):
        raise MonthlyPreflightError("Monthly preflight: missing calculation packet")
    subject = facts.get("subject") or {}
    month = facts.get("month_context") or {}
    collective = facts.get("collective_month") or {}
    core = subject.get("core_positions") or {}
    for planet in ("Sun", "Moon"):
        position = core.get(planet)
        if not isinstance(position, dict) or not str(position.get("sign") or "").strip():
            raise MonthlyPreflightError(f"Monthly preflight: missing verified natal {planet} sign")
    try:
        start = date.fromisoformat(str(month.get("start") or "")[:10])
        end = date.fromisoformat(str(month.get("end") or "")[:10])
    except ValueError as exc:
        raise MonthlyPreflightError("Monthly preflight: invalid report period") from exc
    if (start.year, start.month) != (end.year, end.month) or start.day != 1 or end.day != monthrange(start.year, start.month)[1]:
        raise MonthlyPreflightError("Monthly preflight: expected a complete calendar month")
    if not str(collective.get("collective_story") or "").strip():
        raise MonthlyPreflightError("Monthly preflight: missing published monthly background")
    days = facts.get("daily_signals") or []
    if not isinstance(days, list) or len(days) != monthrange(start.year, start.month)[1]:
        raise MonthlyPreflightError("Monthly preflight: daily signal count does not match calendar")


def validate_prompt_budget(input_tokens: int, completion_tokens: int, *, total_ceiling: int = 5350) -> None:
    if input_tokens < 1 or completion_tokens < 1 or input_tokens + completion_tokens > total_ceiling:
        raise MonthlyPreflightError(
            f"Monthly preflight: request exceeds configured token budget "
            f"({input_tokens} input + {completion_tokens} output > {total_ceiling})"
        )
