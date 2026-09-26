from datetime import date

from solar_cycle import monthly_solar_gate_convergence


def _solar():
    return {
        "next_gate_date": "2026-09-23",
        "next_solar_gate": "September Equinox",
        "end_house": 10,
        "activated_house": 10,
        "end_solar_sign": "Libra",
        "solar_sign": "Libra",
    }


def _trajectory():
    # primary role requires two distinct supporting events to become MATERIAL.
    return {
        "primary_house": 10,
        "secondary_house": 0,
        "bridge": {},
    }


def _event(event_id: str, title: str) -> dict:
    return {
        "event_id": event_id,
        "event_date": "2026-09-23",
        "title": title,
        "houses": [10],
        "importance": 8.0,
    }


def test_duplicate_canonical_event_counts_once_for_solar_gate_convergence():
    """Two representations of one sky event must not create false convergence."""

    source_id = "2026-09-23|ingress|sun-enters-libra"

    events = [
        _event(source_id, "Sun enters Libra"),
        # Deliberately different presentation title, same astronomical identity.
        _event(source_id, "September Equinox · Sun enters Libra"),
    ]

    result = monthly_solar_gate_convergence(
        solar=_solar(),
        trajectory=_trajectory(),
        events=events,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
    )

    # Primary-house convergence needs two distinct events.
    # One canonical event represented twice must therefore remain background.
    assert result["status"] == "BACKGROUND"
    assert result["material"] is False


def test_distinct_canonical_events_count_separately_for_solar_gate_convergence():
    """Different astronomical identities remain separate convergence evidence."""

    events = [
        _event(
            "2026-09-23|ingress|sun-enters-libra",
            "Sun enters Libra",
        ),
        _event(
            "2026-09-23|aspect|jupiter|mercury|sextile",
            "Mercury sextile Jupiter",
        ),
    ]

    result = monthly_solar_gate_convergence(
        solar=_solar(),
        trajectory=_trajectory(),
        events=events,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
    )

    # Primary-house convergence with two genuinely distinct events is material.
    assert result["status"] == "MATERIAL"
    assert result["material"] is True
