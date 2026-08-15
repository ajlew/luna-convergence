from datetime import datetime
from zoneinfo import ZoneInfo

from solar_year_wave import solar_gates, solar_year_wave_svg, sun_state


def test_wave_contains_tropics_equator_gates_and_current_sun():
    now = datetime(2026, 8, 15, 13, 26, tzinfo=ZoneInfo("Australia/Sydney"))
    svg = solar_year_wave_svg(now, "Australia/Sydney")
    assert "TROPIC OF CANCER" in svg
    assert "EQUATOR" in svg
    assert "TROPIC OF CAPRICORN" in svg
    assert "MAR EQUINOX" in svg
    assert "JUN SOLSTICE" in svg
    assert "SEP EQUINOX" in svg
    assert "DEC SOLSTICE" in svg
    assert "SUN · 22.3° LEO" in svg


def test_2026_gate_order_and_current_declination():
    gates = solar_gates(2026, "Australia/Sydney")
    assert [item[0] for item in gates] == [
        "MAR EQUINOX", "JUN SOLSTICE", "SEP EQUINOX", "DEC SOLSTICE"
    ]
    state = sun_state(datetime(2026, 8, 15, 13, 26, tzinfo=ZoneInfo("Australia/Sydney")))
    assert state["sign"] == "Leo"
    assert 13.5 < state["declination"] < 14.5
