from datetime import date

from solar_cycle import (
    daily_solar_convergence,
    monthly_solar_convergence,
    yearly_solar_chapters,
)


def main() -> None:
    sydney = daily_solar_convergence(
        "Sagittarius",
        date(2026, 8, 15),
        "Australia/Sydney",
        nearest_city="Sydney",
        main_focus="Love and relationships",
    )
    assert sydney.solar_sign == "Leo"
    assert sydney.solar_quarter == "Expression"
    assert sydney.activated_house == 9
    assert sydney.hemisphere == "Southern"
    assert sydney.local_season == "Location-aware light cycle"
    assert sydney.light_direction == "Increasing"
    assert sydney.next_solar_gate == "September Equinox"

    london = daily_solar_convergence(
        "Sagittarius",
        date(2026, 8, 15),
        "Europe/London",
        nearest_city="London",
    )
    assert london.hemisphere == "Northern"
    assert london.local_season == "Location-aware light cycle"
    assert london.light_direction == "Decreasing"

    monthly = monthly_solar_convergence(
        "Sagittarius",
        2026,
        8,
        "Australia/Sydney",
        nearest_city="Sydney",
        main_focus="Love and relationships",
    )
    assert monthly.start_solar_sign == "Leo"
    assert monthly.end_solar_sign == "Virgo"
    assert monthly.start_house == 9
    assert monthly.end_house == 10
    assert monthly.headline == "Returning light becomes visible direction"
    assert "house 9" in monthly.equation.lower()
    assert "house 10" in monthly.equation.lower()
    assert "Let the work be seen" in monthly.solar_rule
    assert "make the visible result dependable" in monthly.solar_rule

    chapters = yearly_solar_chapters(
        "Sagittarius",
        2026,
        "Australia/Sydney",
        nearest_city="Sydney",
        main_focus="Love and relationships",
    )
    assert len(chapters) == 4
    assert [item.name for item in chapters] == [
        "Emergence",
        "Expression",
        "Rebalancing",
        "Gestation",
    ]

    print("Solar Convergence calculation tests passed.")


if __name__ == "__main__":
    main()
