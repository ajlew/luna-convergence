"""Regression tests for active retrograde-state detection."""

from datetime import date

from astrology_engine import retrograde_cycles


def test_active_retrogrades_survive_single_day_query():
    """A cycle remains visible after its station date and before direct motion."""
    cycles = retrograde_cycles(
        date(2026, 9, 23),
        date(2026, 9, 23),
        "Libra",
        "Australia/Sydney",
    )

    by_planet = {cycle.planet: cycle for cycle in cycles}

    assert {"Saturn", "Uranus", "Neptune", "Pluto"} <= set(by_planet)

    target = date(2026, 9, 23)

    for planet in ("Saturn", "Uranus", "Neptune", "Pluto"):
        cycle = by_planet[planet]

        assert cycle.retrograde_start <= target
        assert cycle.direct_date >= target


def test_uranus_retrograde_cycle_crosses_year_boundary():
    """Retrograde state must not disappear at the reporting-year boundary."""
    cycles = retrograde_cycles(
        date(2026, 9, 23),
        date(2026, 9, 23),
        "Libra",
        "Australia/Sydney",
    )

    uranus = next(
        cycle for cycle in cycles
        if cycle.planet == "Uranus"
    )

    assert uranus.retrograde_start == date(2026, 9, 11)
    assert uranus.direct_date == date(2027, 2, 9)
