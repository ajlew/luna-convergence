from datetime import date

import pytest

from monthly_arc_engine import _clusters
from monthly_trajectory_engine import (
    _major_primary_movements,
    _top_aspects,
)
from universal_monthly_evidence import _event_identity_value


def _aspect(event_id: str, title: str) -> dict:
    return {
        "event_id": event_id,
        "event_date": "2026-09-26",
        "kind": "aspect",
        "title": title,
        "importance": 8.0,
        "houses": [10],
        "planets": ["Sun", "Pluto"],
        "polarity": "opportunity",
        "orb": 0.5,
    }


def _movement(event_id: str, title: str) -> dict:
    return {
        "event_id": event_id,
        "event_date": "2026-09-23",
        "kind": "ingress",
        "title": title,
        "importance": 8.0,
        "houses": [10],
        "planets": ["Sun"],
        "polarity": "neutral",
    }


def test_monthly_trajectory_deduplicates_aspects_by_event_id():
    """Different presentation titles must not split one calculated aspect."""
    event_id = "2026-09-26|aspect|pluto|sun|trine"

    events = [
        _aspect(event_id, "Sun trine Pluto"),
        _aspect(event_id, "Sun–Pluto opening"),
    ]

    values = _top_aspects(
        events,
        "Sagittarius",
        {},
        pressure=False,
        maximum=5,
    )

    assert len(values) == 1


def test_monthly_trajectory_deduplicates_primary_movements_by_event_id():
    """Rendered movement text must not define astronomical sameness."""
    event_id = "2026-09-23|ingress|sun-enters-libra"

    events = [
        _movement(event_id, "Sun enters Libra"),
        _movement(event_id, "September Equinox"),
    ]

    values = _major_primary_movements(
        events,
        10,
        "Sagittarius",
        {},
        maximum=5,
    )

    assert len(values) == 1


def test_monthly_arc_cluster_fingerprint_uses_canonical_event_identity():
    """One raw calculated event must not become multiple clusters through labels."""
    from astrology_engine import Event

    first = Event(
        event_date=date(2026, 9, 26),
        kind="aspect",
        title="Sun trine Pluto",
        detail="",
        importance=8.0,
        planets=("Sun", "Pluto"),
        houses=(10,),
        polarity="opportunity",
        orb=0.5,
        aspect_name="trine",
        applying_state="applying",
    )

    second = Event(
        event_date=date(2026, 9, 26),
        kind="aspect",
        title="Pluto trine Sun",
        detail="",
        importance=8.0,
        planets=("Pluto", "Sun"),
        houses=(10,),
        polarity="opportunity",
        orb=0.5,
        aspect_name="trine",
        applying_state="applying",
    )

    clusters = _clusters(
        [first, second],
        "Sagittarius",
        window_days=0,
        house_weights={},
    )

    assert len(clusters) == 1


def test_serialized_monthly_evidence_requires_event_id():
    """Serialized evidence must never reconstruct identity from date/title."""
    value = _movement(
        "2026-09-23|ingress|sun-enters-libra",
        "Sun enters Libra",
    )
    value.pop("event_id")

    with pytest.raises(
        ValueError,
        match="canonical event_id",
    ):
        _event_identity_value(value)

def test_scenario_support_serializes_canonical_event_id():
    """Scenario evidence must retain the calculated event's canonical identity."""
    from datetime import date

    from astrology_engine import Event
    from event_identity import event_identity
    from scenario_engine import rank_scenarios

    event = Event(
        event_date=date(2026, 9, 1),
        kind="aspect",
        title="Jupiter trine Saturn",
        detail="",
        importance=8.0,
        planets=("Jupiter", "Saturn"),
        houses=(1, 10),
        polarity="opportunity",
        orb=0.2,
        aspect_name="trine",
        applying_state="applying",
    )

    ranked = rank_scenarios(
        [event],
        "Sagittarius",
        maximum=20,
    )

    supports = [
        support
        for scenario in ranked
        for support in scenario.to_dict()["supporting_events"]
    ]

    assert supports
    assert all(
        support["event_id"] == event_identity(event)
        for support in supports
    )


def test_scenario_diversity_uses_event_identity_not_title():
    """A second presentation title must not manufacture another event."""
    from scenario_engine import ScenarioSupport

    source_id = "2026-09-01|aspect|jupiter|saturn|trine"

    supports = (
        ScenarioSupport(
            event_date="2026-09-01",
            event_id=source_id,
            title="Jupiter trine Saturn",
            houses=(1, 10),
            planets=("Jupiter", "Saturn"),
            polarity="opportunity",
            contribution=4.0,
        ),
        ScenarioSupport(
            event_date="2026-09-01",
            event_id=source_id,
            title="Controlled expansion",
            houses=(1, 10),
            planets=("Jupiter", "Saturn"),
            polarity="opportunity",
            contribution=4.0,
        ),
    )

    independent_dates = len({item.event_date for item in supports})
    independent_events = len({item.event_id for item in supports})

    assert independent_dates == 1
    assert independent_events == 1
    assert len({item.title for item in supports}) == 2

