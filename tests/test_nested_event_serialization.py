from datetime import date

from astrology_engine import Convergence, Event, serialize
from event_identity import event_identity


def test_nested_event_serialization_preserves_canonical_identity():
    event = Event(
        event_date=date(2026, 9, 15),
        kind="aspect",
        title="Sun sextile Mars",
        detail="Regression fixture",
        importance=8.0,
        planets=("Sun", "Mars"),
        houses=(),
        polarity="opportunity",
        orb=0.1,
        aspect_name="sextile",
        applying_state="applying",
    )

    convergence = Convergence(
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 15),
        title="Regression convergence",
        score=10.0,
        events=(event,),
        planets=("Sun", "Mars"),
        houses=(),
        polarity="opportunity",
    )

    payload = serialize(convergence)

    assert len(payload["events"]) == 1
    assert payload["events"][0]["event_id"] == event_identity(event)
    assert payload["events"][0]["event_id"] == (
        "2026-09-15|aspect|mars|sun|sextile"
    )


def test_convergence_container_does_not_become_an_event():
    event = Event(
        event_date=date(2026, 9, 15),
        kind="aspect",
        title="Sun sextile Mars",
        detail="Regression fixture",
        importance=8.0,
        planets=("Sun", "Mars"),
        houses=(),
        polarity="opportunity",
        orb=0.1,
        aspect_name="sextile",
        applying_state="applying",
    )

    convergence = Convergence(
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 15),
        title="Regression convergence",
        score=10.0,
        events=(event,),
        planets=("Sun", "Mars"),
        houses=(),
        polarity="opportunity",
    )

    payload = serialize(convergence)

    assert "event_id" not in payload
    assert "source_event_id" not in payload
