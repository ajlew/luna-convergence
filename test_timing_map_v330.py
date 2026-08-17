from datetime import date, time

from natal_snapshot import build_natal_snapshot
from timing_map import build_timing_map, month_intensity, TRANSIT_PLANETS


def _snapshot(time_known: bool = True):
    return build_natal_snapshot(
        birth_date=date(1990, 1, 1),
        birth_time_known=time_known,
        birth_time=time(12, 0) if time_known else None,
        timezone_name="Australia/Sydney" if time_known else "UTC",
        location_name="Sydney, Australia" if time_known else None,
        latitude=-33.8688 if time_known else None,
        longitude=151.2093 if time_known else None,
    )


def test_timing_map_builds_ranked_personal_year():
    report = build_timing_map(
        _snapshot(),
        start_date=date(2026, 8, 17),
        timezone_name="Australia/Sydney",
        max_stories=10,
    )
    assert report.end_date == date(2027, 8, 16)
    assert 3 <= len(report.stories) <= 10
    assert report.turning_points >= len(report.stories)
    assert all(story.transit_planet in TRANSIT_PLANETS for story in report.stories)
    assert all(story.hits for story in report.stories)
    assert all(
        report.start_date <= hit.exact_date <= report.end_date
        for story in report.stories
        for hit in story.hits
    )


def test_date_only_profile_still_generates_without_fake_angles():
    snapshot = _snapshot(time_known=False)
    assert snapshot.ascendant is None
    assert snapshot.midheaven is None
    report = build_timing_map(
        snapshot,
        start_date=date(2026, 8, 17),
        timezone_name="UTC",
        max_stories=8,
    )
    assert report.stories
    assert all(story.natal_target not in {"Ascendant", "Midheaven"} for story in report.stories)


def test_month_strip_has_twelve_normalised_values():
    report = build_timing_map(
        _snapshot(),
        start_date=date(2026, 8, 17),
        timezone_name="Australia/Sydney",
        max_stories=8,
    )
    strip = month_intensity(report)
    assert 12 <= len(strip) <= 13
    assert strip[-1][0].startswith("AUG")
    assert all(0.0 <= value <= 1.0 for _, value in strip)
    assert max(value for _, value in strip) == 1.0
