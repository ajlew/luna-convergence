from datetime import date, time

from natal_snapshot import build_natal_snapshot
from timing_map import build_timing_map
from timing_insight import build_major_games, dates_to_remember, strongest_story, year_closing


def _alotau_snapshot():
    return build_natal_snapshot(
        birth_date=date(1965, 12, 1),
        birth_time_known=True,
        birth_time=time(2, 0),
        timezone_name="UTC",
        location_name="Alotau, Papua New Guinea",
        latitude=-10.3167,
        longitude=150.4667,
    )


def _report():
    return build_timing_map(
        _alotau_snapshot(),
        start_date=date(2026, 8, 17),
        timezone_name="Australia/Sydney",
        max_stories=10,
    )


def test_story_language_is_human_and_not_one_planet_template():
    report = _report()
    assert len(report.stories) == 10
    assert all(story.insight and story.question for story in report.stories)
    assert len({story.summary for story in report.stories}) == len(report.stories)
    assert len({story.move for story in report.stories}) == len(report.stories)
    assert len({story.watch for story in report.stories}) == len(report.stories)


def test_repeated_saturn_contacts_become_one_larger_game():
    report = _report()
    games = build_major_games(report.stories)
    assert 1 <= len(games) <= 3
    saturn = next(game for game in games if game.transit_planet == "Saturn")
    assert "one longer argument" in saturn.summary
    assert len(saturn.players) >= 3
    assert "Uranus" in saturn.countercurrent


def test_report_has_hierarchy_and_closing_synthesis():
    report = _report()
    games = build_major_games(report.stories)
    strongest = strongest_story(report.stories)
    remember = dates_to_remember(report.stories)
    closing = year_closing(report.stories, games)
    assert strongest is not None
    assert len(remember) == 3
    assert len({item.exact_date for item in remember}) == 3
    assert "The year keeps returning" in closing
    assert strongest.transit_planet in closing
