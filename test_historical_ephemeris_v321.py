from datetime import date

import historical_ephemeris as hist


def test_archive_contract_and_daily_positions():
    stats = hist.archive_stats()
    assert stats["available"] is True
    assert stats["start_year"] == 1950
    assert stats["end_year"] == 2050
    assert stats["frame"] == "geocentric"
    assert stats["zodiac"] == "tropical"
    assert stats["node"] == "True Node"
    assert stats["positions"] == 405790
    assert stats["days"] == 36890
    assert stats["bodies"] == 11
    rows = hist.positions_on(date(2026, 8, 15))
    assert len(rows) == 11
    mercury = next(row for row in rows if row["body"] == "Mercury")
    jupiter = next(row for row in rows if row["body"] == "Jupiter")
    assert mercury["sign"] == "Leo"
    assert jupiter["sign"] == "Leo"


def test_mercury_jupiter_leo_historical_recurrence():
    rows = hist.aspect_events(
        "Mercury", "Jupiter", "conjunction", sign="Leo", ascending=True, limit=50
    )
    dates = [row["exact_utc"][:10] for row in rows]
    assert "2014-08-02" in dates
    assert "2015-08-07" in dates
    assert "2026-08-15" in dates
    previous = hist.previous_aspect(
        "Mercury", "Jupiter", "conjunction", "2026-08-15", sign="Leo"
    )
    assert previous is not None and previous["exact_utc"].startswith("2015-08-07")
    following = hist.next_aspect(
        "Mercury", "Jupiter", "conjunction", "2026-08-16", sign="Leo"
    )
    assert following is not None and following["exact_utc"].startswith("2038-")
