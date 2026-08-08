from ephemeris_repository import inspect_ephemeris_text


def test_2017_geocentric_tropical_header_is_usable():
    meta = inspect_ephemeris_text(
        "Astrodienst Ephemeris Tables for the year 2017 tropical geocentric zodiac based on Swiss Ephemeris"
    )
    assert meta.year == 2017
    assert meta.zodiac == "tropical"
    assert meta.frame == "geocentric"
    assert meta.usable_by_luna is True


def test_heliocentric_header_is_rejected_for_luna_calculation_reference():
    meta = inspect_ephemeris_text(
        "Astrodienst Swiss Ephemeris Tables for the year 2026 tropical heliocentric zodiac based on Swiss Ephemeris"
    )
    assert meta.year == 2026
    assert meta.frame == "heliocentric"
    assert meta.usable_by_luna is False
    assert "expected geocentric" in meta.validation_message
