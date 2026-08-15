from datetime import date, time
from pathlib import Path

from natal_snapshot import build_natal_snapshot
from solar_cycle import CITY_LOCATIONS

APP = Path(__file__).with_name("app.py").read_text(encoding="utf-8")


def test_alotau_is_available_offline_with_correct_timezone():
    location = CITY_LOCATIONS["Alotau"]
    assert location.country == "Papua New Guinea"
    assert location.timezone == "Pacific/Port_Moresby"
    assert abs(location.latitude - (-10.3167)) < 0.001
    assert abs(location.longitude - 150.4667) < 0.001


def test_alotau_2am_ut_matches_reference_planet_positions():
    location = CITY_LOCATIONS["Alotau"]
    snapshot = build_natal_snapshot(
        birth_date=date(1965, 12, 1),
        birth_time_known=True,
        birth_time=time(2, 0),
        timezone_name="UTC",
        location_name="Alotau, Papua New Guinea",
        latitude=location.latitude,
        longitude=location.longitude,
    )
    by_planet = {item.planet: item for item in snapshot.positions}
    assert by_planet["Sun"].sign == "Sagittarius"
    assert round(by_planet["Sun"].degree, 1) == 8.7
    assert by_planet["Moon"].sign == "Pisces"
    assert round(by_planet["Moon"].degree, 1) == 7.1
    assert snapshot.ascendant.sign == "Pisces"
    assert round(snapshot.ascendant.degree, 1) == 10.1
    assert snapshot.midheaven.sign == "Sagittarius"
    assert round(snapshot.midheaven.degree, 1) == 11.7


def test_daily_renders_solar_wave_and_natal_ui_exposes_big_three_and_manual_location():
    assert "solar_year_wave_svg(browser_local_now(), browser_timezone_name())" in APP
    assert '("Sun", by_planet["Sun"].sign)' in APP
    assert '("Moon", moon_value)' in APP
    assert '("Rising", snapshot.ascendant.sign if snapshot.ascendant else "Not calculated")' in APP
    assert "Other city — enter manually" in APP
    assert "Universal Time (UTC)" in APP
