from datetime import date

from astrology_engine import period_events
from event_identity import canonical_event_identity, event_identity
from major_event_registry import major_sky_events


def test_aspect_identity_is_independent_of_planet_order():
    """An aspect is the same calculated event regardless of body ordering."""
    first = canonical_event_identity(
        date(2026, 9, 26),
        "aspect",
        "Sun trine Pluto",
        ("Sun", "Pluto"),
        "trine",
    )
    second = canonical_event_identity(
        date(2026, 9, 26),
        "aspect",
        "Pluto trine Sun",
        ("Pluto", "Sun"),
        "trine",
    )

    assert first == second
    assert first == "2026-09-26|aspect|pluto|sun|trine"


def test_solar_anchor_points_to_underlying_calculated_ingress():
    """Presentation/classification must not create a second event identity."""
    timezone_name = "Australia/Sydney"

    events = period_events(
        date(2026, 9, 23),
        date(2026, 9, 23),
        "Libra",
        timezone_name,
    )

    ingress = next(
        event
        for event in events
        if event.kind == "ingress"
        and event.title == "Sun enters Libra"
    )

    signals = major_sky_events(
        date(2026, 9, 23),
        date(2026, 9, 23),
        "Libra",
        timezone_name,
    )

    anchor = next(
        signal
        for signal in signals
        if signal.event_class == "solar_anchor"
    )

    assert anchor.source_title != ingress.title
    assert anchor.technical_label == ingress.title
    assert anchor.source_event_id == event_identity(ingress)
    assert anchor.source_event_id == (
        "2026-09-23|ingress|sun-enters-libra"
    )


def test_registry_has_only_one_signal_for_solar_anchor_source_identity():
    """One calculated source identity must not survive twice in the registry."""
    signals = major_sky_events(
        date(2026, 9, 23),
        date(2026, 9, 23),
        "Libra",
        "Australia/Sydney",
    )

    target_id = "2026-09-23|ingress|sun-enters-libra"

    matching = [
        signal
        for signal in signals
        if signal.source_event_id == target_id
    ]

    assert len(matching) == 1
    assert matching[0].event_class == "solar_anchor"

def test_non_cardinal_sun_ingresses_are_calculated_but_not_solar_anchors():
    """Ordinary Sun ingresses exist without receiving seasonal-anchor protection."""
    from datetime import date

    from astrology_engine import period_events
    from event_identity import event_identity
    from major_event_registry import major_sky_events

    timezone_name = "Australia/Sydney"
    sign = "Sagittarius"

    cases = (
        (
            date(2026, 8, 20),
            date(2026, 8, 26),
            "Sun enters Virgo",
            "2026-08-24|ingress|sun-enters-virgo",
        ),
        (
            date(2026, 10, 20),
            date(2026, 10, 27),
            "Sun enters Scorpio",
            "2026-10-24|ingress|sun-enters-scorpio",
        ),
    )

    for start, end, expected_title, expected_id in cases:
        events = period_events(start, end, sign, timezone_name)

        ingress = next(
            event
            for event in events
            if event.kind == "ingress"
            and event.title == expected_title
            and "Sun" in event.planets
        )

        assert event_identity(ingress) == expected_id

        registry = major_sky_events(
            start,
            end,
            sign,
            timezone_name,
        )

        linked = [
            signal
            for signal in registry
            if signal.source_event_id == expected_id
        ]

        assert not any(
            signal.event_class == "solar_anchor"
            for signal in linked
        )

        assert not any(
            signal.must_surface_in("weekly")
            or signal.must_surface_in("monthly")
            for signal in linked
        )


def test_cardinal_sun_ingress_can_become_protected_solar_anchor():
    """A seasonal Sun ingress keeps ingress identity while gaining anchor classification."""
    from datetime import date

    from astrology_engine import period_events
    from event_identity import event_identity
    from major_event_registry import major_sky_events

    timezone_name = "Australia/Sydney"
    sign = "Sagittarius"
    start = date(2026, 9, 20)
    end = date(2026, 9, 25)

    events = period_events(start, end, sign, timezone_name)

    ingress = next(
        event
        for event in events
        if event.kind == "ingress"
        and event.title == "Sun enters Libra"
        and "Sun" in event.planets
    )

    ingress_id = event_identity(ingress)

    assert ingress_id == "2026-09-23|ingress|sun-enters-libra"

    registry = major_sky_events(
        start,
        end,
        sign,
        timezone_name,
    )

    linked = [
        signal
        for signal in registry
        if signal.source_event_id == ingress_id
    ]

    assert len(linked) == 1

    anchor = linked[0]

    assert anchor.event_class == "solar_anchor"
    assert anchor.source_kind == "solar_anchor"
    assert anchor.source_event_id == ingress_id
    assert anchor.must_surface_in("weekly")
    assert anchor.must_surface_in("monthly")
