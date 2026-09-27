"""Regression tests for Monthly must-surface event survival."""

from datetime import date

from synthesis import period_report


def test_monthly_must_surface_events_survive_without_protecting_opportunities():
    """Protection guarantees survival; opportunity priority does not imply protection."""
    report = period_report(
        sign="Libra",
        start=date(2026, 9, 1),
        end=date(2026, 9, 30),
        timezone_name="Australia/Sydney",
        period_name="September 2026",
    )

    arc = report["monthly_arc"]
    protected = arc["protected_evidence"]

    identities = {
        (
            str(event.get("event_date")),
            str(event.get("kind")),
            str(event.get("title")),
        )
        for event in protected
    }

    # Seasonal-anchor presentation is backed by the calculated ingress.
    assert (
        "2026-09-23",
        "ingress",
        "Sun enters Libra",
    ) in identities

    # Known must-surface events for this regression period survive.
    assert (
        "2026-09-11",
        "station",
        "Uranus stations retrograde",
    ) in identities

    assert (
        "2026-09-11",
        "lunation",
        "New Moon in Virgo",
    ) in identities

    assert (
        "2026-09-27",
        "lunation",
        "Full Moon in Aries",
    ) in identities

    # Opportunity priority is not protection.
    protected_titles = {identity[2] for identity in identities}

    assert "Jupiter trine Saturn" not in protected_titles
    assert "Mercury sextile Jupiter" not in protected_titles

def test_monthly_arc_inherited_events_preserve_event_id():
    """Carry-in evidence must retain its original calculated identity."""
    from datetime import date

    from astrology_engine import Event
    from event_identity import event_identity
    from monthly_arc_engine import _event_dict

    inherited = Event(
        event_date=date(2026, 8, 28),
        kind="eclipse",
        title="Partial Lunar Eclipse in Pisces",
        detail="",
        importance=10.0,
        planets=("Sun", "Moon"),
        houses=(4, 10),
        polarity="turning point",
        orb=None,
        aspect_name="",
        applying_state="",
    )

    serialized = _event_dict(inherited)

    assert serialized["event_id"] == event_identity(inherited)
    assert serialized["event_date"] == "2026-08-28"


def test_monthly_arc_protected_evidence_preserves_event_id():
    """Protected evidence must not lose identity when serialized."""
    from datetime import date

    from astrology_engine import Event
    from event_identity import event_identity
    from monthly_arc_engine import _event_dict

    protected = Event(
        event_date=date(2026, 9, 23),
        kind="ingress",
        title="Sun enters Libra",
        detail="",
        importance=8.0,
        planets=("Sun",),
        houses=(11,),
        polarity="new cycle",
        orb=None,
        aspect_name="",
        applying_state="",
    )

    serialized = _event_dict(protected)

    assert serialized["event_id"] == event_identity(protected)
    assert serialized["title"] == "Sun enters Libra"

