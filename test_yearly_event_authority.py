"""Regression tests for Yearly event calculation authority."""

from datetime import date

import yearly_game_engine as yge


def test_supplied_annual_events_prevent_monthly_event_recalculation(monkeypatch):
    """Yearly monthly arcs inherit annual authority rather than recalculating it."""
    original = yge.period_events
    calls = []

    def watched_period_events(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(yge, "period_events", watched_period_events)

    yge.build_yearly_game_map(
        "Sagittarius",
        2027,
        "Australia/Sydney",
        "Sydney",
        "General year ahead",
        annual_events=[],
    )

    assert len(calls) == 1

    start, end, sign, timezone = calls[0][:4]

    assert start == date(2026, 12, 25)
    assert end == date(2026, 12, 31)
    assert sign == "Sagittarius"
    assert timezone == "Australia/Sydney"


def test_explicit_empty_annual_authority_is_not_treated_as_missing(monkeypatch):
    """An explicitly supplied empty annual set must remain authoritative."""
    original = yge.period_events
    calls = []

    def watched_period_events(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(yge, "period_events", watched_period_events)

    yge.build_yearly_game_map(
        "Sagittarius",
        2027,
        "Australia/Sydney",
        annual_events=[],
    )

    annual_calls = [
        call
        for call in calls
        if call[0] == date(2027, 1, 1)
        and call[1] == date(2027, 12, 31)
    ]

    assert annual_calls == []
