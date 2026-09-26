from datetime import date, datetime, timezone

from unified_period_system import local_metadata, merge_rows, five_day_cards, daily_sky_cards


def test_sydney_dst_is_derived_not_hardcoded():
    winter = local_metadata(datetime(2026, 9, 22, 0, 0, tzinfo=timezone.utc), "Australia/Sydney")
    summer = local_metadata(datetime(2026, 12, 22, 0, 0, tzinfo=timezone.utc), "Australia/Sydney")
    assert winter["timezone_label"] == "AEST"
    assert winter["utc_offset"] == "+10:00"
    assert summer["timezone_label"] == "AEDT"
    assert summer["utc_offset"] == "+11:00"


def test_protected_event_survives_merge():
    normal = [{"date": "2026-09-23", "event": "Mercury trine X", "importance": 99}]
    major = [{"date": "2026-09-23", "event": "September Equinox Â· Sun enters Libra", "tier": 1}]
    events = merge_rows(normal, major, "Australia/Sydney")
    labels = [e.display_label for e in events]
    assert "September Equinox Â· Sun enters Libra" in labels
    assert next(e for e in events if "Equinox" in e.display_label).protected


def test_weekday_card_prefers_protected_event():
    timeline = [
        {"local_date": "2026-09-23", "display_label": "Ordinary aspect", "importance": 100, "protected": False},
        {"local_date": "2026-09-23", "display_label": "September Equinox", "importance": 1, "protected": True},
    ]
    cards = five_day_cards(timeline, date(2026, 9, 23), 1)
    assert cards[0]["event"] == "September Equinox"


def test_weekday_cards_always_return_requested_slots():
    timeline = [
        {
            "local_date": "2026-09-21",
            "display_label": "Monday aspect",
            "importance": 10,
            "protected": False,
        },
        {
            "local_date": "2026-09-23",
            "display_label": "September Equinox",
            "importance": 1,
            "protected": True,
        },
    ]
    cards = five_day_cards(timeline, date(2026, 9, 21), 5)

    assert len(cards) == 5
    assert [card["weekday"] for card in cards] == [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
    ]
    assert cards[0]["has_event"] is True
    assert cards[1]["has_event"] is False
    assert cards[2]["event"] == "September Equinox"


def test_empty_weekday_slot_does_not_invent_event():
    cards = five_day_cards([], date(2026, 9, 21), 5)

    assert len(cards) == 5
    assert all(card["has_event"] is False for card in cards)
    assert all(card["event"] == "" for card in cards)



def test_weekly_sky_cards_cover_monday_through_sunday():
    cards = daily_sky_cards([], date(2026, 9, 21), 7)

    assert len(cards) == 7
    assert [card["weekday"] for card in cards] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    assert cards[0]["date"] == "2026-09-21"
    assert cards[6]["date"] == "2026-09-27"
    assert all(card["has_event"] is False for card in cards)

def test_weekly_sky_cards_inherit_studio_daily_ranking():
    """Sky Cards must inherit studio_daily ranking, never rerank the sky."""
    from datetime import date, timedelta
    from studio_readings import studio_packet, COLLECTIVE

    timezone = "Australia/Sydney"
    monday = date(2026, 9, 21)

    weekly = studio_packet(
        "studio_weekly",
        monday,
        COLLECTIVE,
        timezone,
    )

    assert len(weekly["sky_cards"]) == 7

    for offset in range(7):
        day = monday + timedelta(days=offset)

        daily = studio_packet(
            "studio_daily",
            day,
            COLLECTIVE,
            timezone,
        )

        card = weekly["sky_cards"][offset]
        daily_event = daily["events"][0]["event"] if daily.get("events") else ""

        assert card["event"] == daily_event
        assert card["primary_event"] == daily_event
        assert card["date"] == day.isoformat()
        assert card["weekday"] == day.strftime("%A")




def test_same_aspect_from_presentation_and_registry_merges_once():
    """One calculated aspect represented twice must remain one canonical event."""
    presentation = [{
        "date": "2026-09-26",
        "event": "Sun trine Pluto · opening",
        "planets": ["Sun", "Pluto"],
        "phase": "opening",
        "supporting_events": ["Sun opposite Neptune"],
    }]

    registry = [{
        "date": "2026-09-26",
        "event": "Sun trine Pluto",
        "technical": "Sun trine Pluto",
        "planets": ["Sun", "Pluto"],
        "tier": "A-",
    }]

    events = merge_rows(
        presentation,
        registry,
        "Australia/Sydney",
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_id == "2026-09-26|aspect|pluto|sun|trine"
    assert event.display_label == "Sun trine Pluto · opening"
    assert event.technical_label == "Sun trine Pluto"
    assert event.phase == "opening"
    assert event.supporting_events == ("Sun opposite Neptune",)


def test_different_aspects_on_same_day_remain_separate():
    """Canonical merging must not collapse genuinely different calculated events."""
    rows = [
        {
            "date": "2026-09-26",
            "event": "Sun trine Pluto",
            "technical": "Sun trine Pluto",
            "planets": ["Sun", "Pluto"],
        },
        {
            "date": "2026-09-26",
            "event": "Sun opposite Neptune",
            "technical": "Sun opposite Neptune",
            "planets": ["Sun", "Neptune"],
        },
    ]

    events = merge_rows(rows, [], "Australia/Sydney")

    assert len(events) == 2
    assert {event.event_id for event in events} == {
        "2026-09-26|aspect|pluto|sun|trine",
        "2026-09-26|aspect|neptune|sun|opposition",
    }


def test_presentation_treatment_does_not_change_aspect_identity():
    """Presentation wording must not become part of a calculated aspect's identity."""
    plain = [{
        "date": "2026-09-26",
        "event": "Sun trine Pluto",
        "technical": "Sun trine Pluto",
        "planets": ["Sun", "Pluto"],
    }]

    presented = [{
        "date": "2026-09-26",
        "event": "Sun trine Pluto · opening",
        "planets": ["Sun", "Pluto"],
        "phase": "opening",
    }]

    plain_event = merge_rows(plain, [], "Australia/Sydney")[0]
    presented_event = merge_rows(presented, [], "Australia/Sydney")[0]

    assert plain_event.event_id == presented_event.event_id
    assert plain_event.event_id == "2026-09-26|aspect|pluto|sun|trine"


def test_protected_eclipse_survives_merge_and_card_selection():
    """A protected eclipse cannot be displaced by a higher-scoring ordinary event."""
    rows = [{
        "date": "2026-08-28",
        "event": "Ordinary aspect",
        "importance": 999,
        "protected": False,
    }]

    major_rows = [{
        "date": "2026-08-28",
        "event": "Lunar Eclipse",
        "technical": "Lunar Eclipse",
        "event_type": "eclipse",
        "importance": 1,
        "protected": True,
    }]

    events = merge_rows(
        rows,
        major_rows,
        "Australia/Sydney",
    )

    eclipse = next(
        event for event in events
        if event.event_type == "eclipse"
    )

    assert eclipse.protected is True
    assert len(events) == 2

    timeline = [
        {
            "local_date": event.local_date,
            "display_label": event.display_label,
            "importance": event.importance,
            "protected": event.protected,
        }
        for event in events
    ]

    cards = daily_sky_cards(
        timeline,
        date(2026, 8, 28),
        1,
    )

    assert cards[0]["event"] == "Lunar Eclipse"
    assert cards[0]["protected"] is True


def test_sky_card_preserves_phase_separately_from_protection():
    """Protection is a survival rule; phase is the presentation classification."""
    from sky_card import build_sky_card

    protected_anchor = build_sky_card(
        {
            "date": "2026-09-23",
            "weekday": "Wednesday",
            "has_event": True,
            "event": "Test solar anchor",
            "technical": "Test solar anchor",
            "phase": "solar anchor",
            "timing": "",
            "timezone": "Australia/Sydney",
            "timezone_label": "AEST",
            "protected": True,
        },
        "Regression test copy.",
    )

    ordinary_opening = build_sky_card(
        {
            "date": "2026-09-26",
            "weekday": "Saturday",
            "has_event": True,
            "event": "Test opening",
            "technical": "Test opening",
            "phase": "opening",
            "timing": "",
            "timezone": "Australia/Sydney",
            "timezone_label": "AEST",
            "protected": False,
        },
        "Regression test copy.",
    )

    protected_lunation = build_sky_card(
        {
            "date": "2026-09-27",
            "weekday": "Sunday",
            "has_event": True,
            "event": "Test lunation",
            "technical": "Test lunation",
            "phase": "lunation",
            "timing": "",
            "timezone": "Australia/Sydney",
            "timezone_label": "AEST",
            "protected": True,
        },
        "Regression test copy.",
    )

    assert protected_anchor.phase == "solar anchor"
    assert protected_anchor.protected is True

    assert ordinary_opening.phase == "opening"
    assert ordinary_opening.protected is False

    assert protected_lunation.phase == "lunation"
    assert protected_lunation.protected is True

    # Two protected events may have different classifications.
    assert protected_anchor.phase != protected_lunation.phase


def test_sky_card_renderer_does_not_classify_protected_as_major_sky_event():
    """Renderer must use inherited phase, never protected status as event type."""
    from pathlib import Path

    source = Path("sky_card.py").read_text(encoding="utf-8-sig")

    assert '"MAJOR SKY EVENT"' not in source
    assert "if card.protected:" not in source
    assert "if card.phase:" in source
    assert "card.phase.upper()" in source
