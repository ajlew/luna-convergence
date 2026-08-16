from datetime import date, timedelta

from weekly_view import (
    all_video_copy,
    build_weekly_view,
    default_week_start,
    monday_for,
    week_label,
)


def test_week_helpers_are_monday_first():
    assert monday_for(date(2026, 8, 16)) == date(2026, 8, 10)
    assert monday_for(date(2026, 8, 19)) == date(2026, 8, 17)
    assert default_week_start(date(2026, 8, 16)) == date(2026, 8, 17)
    assert default_week_start(date(2026, 8, 19)) == date(2026, 8, 17)
    assert week_label(date(2026, 8, 31)) == "31 August–6 September 2026"


def test_weekly_view_builds_seven_evidenced_canva_scripts():
    monday = date(2026, 8, 17)
    days = build_weekly_view(monday, "Australia/Sydney")

    assert len(days) == 7
    assert [item.reading_date for item in days] == [
        monday + timedelta(days=offset) for offset in range(7)
    ]
    assert days[0].weekday == "Monday"
    assert days[-1].weekday == "Sunday"
    assert all(item.headline and item.evidence and item.action for item in days)
    assert all("° orb" in item.evidence for item in days)
    assert all("YOUR MOVE" in item.video_copy() for item in days)
    assert all(item.video_copy().endswith("LUNA CONVERGENCE") for item in days)
    assert all(days[index].planets != days[index - 1].planets for index in range(1, 7))
    assert len({item.headline for item in days}) == 7

    combined = all_video_copy(days)
    assert combined.count("LUNA CONVERGENCE") == 7


def test_weekly_view_rejects_non_monday_start():
    try:
        build_weekly_view(date(2026, 8, 18), "Australia/Sydney")
    except ValueError as exc:
        assert "Monday" in str(exc)
    else:
        raise AssertionError("A Tuesday start must be rejected.")
