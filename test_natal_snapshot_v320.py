from datetime import date, time

from natal_snapshot import build_natal_snapshot, natal_wheel_svg


def test_unknown_birth_time_never_invents_angles_or_houses():
    snapshot = build_natal_snapshot(
        birth_date=date(1990, 1, 1),
        birth_time_known=False,
    )
    assert snapshot.ascendant is None
    assert snapshot.midheaven is None
    assert all(item.house is None for item in snapshot.positions)
    assert snapshot.moon_uncertain
    assert len(snapshot.themes) == 3


def test_exact_time_and_supported_coordinates_create_angles_and_whole_sign_houses():
    snapshot = build_natal_snapshot(
        birth_date=date(1990, 1, 1),
        birth_time_known=True,
        birth_time=time(12, 0),
        timezone_name="Australia/Sydney",
        location_name="Sydney, Australia",
        latitude=-33.8688,
        longitude=151.2093,
    )
    assert snapshot.ascendant is not None
    assert snapshot.midheaven is not None
    assert snapshot.ascendant.house == 1
    houses = [item.house for item in snapshot.positions]
    assert all(isinstance(item, int) and 1 <= item <= 12 for item in houses)
    assert len(snapshot.aspects) > 0
    assert len(snapshot.themes) == 3


def test_snapshot_has_core_planets_and_descriptive_signature():
    snapshot = build_natal_snapshot(
        birth_date=date(2000, 1, 1),
        birth_time_known=False,
    )
    planets = {item.planet for item in snapshot.positions}
    assert {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"} <= planets
    assert snapshot.dominant_element in {"Fire", "Earth", "Air", "Water"}
    assert snapshot.dominant_modality in {"Cardinal", "Fixed", "Mutable"}


def test_natal_wheel_is_self_contained_svg():
    snapshot = build_natal_snapshot(
        birth_date=date(2000, 1, 1),
        birth_time_known=False,
    )
    svg = natal_wheel_svg(snapshot)
    assert svg.startswith('<svg')
    assert 'NATAL SNAPSHOT' in svg
    assert 'SUN' in svg
    assert 'SAG' in svg
    assert svg.endswith('</svg>')
