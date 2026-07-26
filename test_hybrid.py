from datetime import date
from pathlib import Path

from astrology_engine import (
    positions_for_date, house_map, period_events,
    retrograde_cycles, convergence_points, eclipse_events,
)
from synthesis import daily_report, period_report
from ephemeris_upload import inspect_ephemeris_pdf


def main():
    timezone_name = "Australia/Sydney"
    sign = "Sagittarius"

    positions = positions_for_date(date(2026, 7, 26), timezone_name)
    assert positions["Sun"].sign == "Leo"
    houses = house_map(positions, sign)
    assert houses["Sun"] == 9

    events = period_events(date(2026, 1, 1), date(2026, 12, 31), sign, timezone_name)
    assert any("Jupiter enters Leo" in event.title for event in events)
    assert any(event.kind == "eclipse" for event in events)

    cycles = retrograde_cycles(date(2026, 1, 1), date(2026, 12, 31), sign, timezone_name)
    assert any(cycle.planet == "Mercury" for cycle in cycles)

    convergences = convergence_points(events, maximum=9)
    assert convergences

    daily = daily_report(sign, date(2026, 7, 26), timezone_name)
    assert "Wider context" in daily["markdown"]
    assert "House reference matrix" in daily["markdown"]
    assert "Two-sentence horoscope" in daily["markdown"]
    assert "House 9 governs" in daily["markdown"]

    yearly = period_report(
        sign,
        date(2026, 1, 1),
        date(2026, 12, 31),
        timezone_name,
        "2026",
    )
    assert "Major transitions" in yearly["markdown"]
    assert "Convergence points" in yearly["markdown"]
    assert len(yearly["major_transitions"]) == 9
    assert len(yearly["strategic_chapters"]) == 9
    assert "Nine strategic chapters" in yearly["markdown"]
    assert "House reference matrix" in yearly["markdown"]
    assert "Two-sentence interpretation" in yearly["markdown"]

    sample_pdf = Path("/mnt/data/ae_2026.pdf")
    if sample_pdf.exists():
        profile = inspect_ephemeris_pdf(sample_pdf.read_bytes(), sample_pdf.name)
        assert profile.year == 2026
        assert profile.perspective == "geocentric"
        assert profile.zodiac == "tropical"

    print("All hybrid-system tests passed.")
    print("Events:", len(events))
    print("Retrograde cycles:", len(cycles))
    print("Convergence points:", len(convergences))
    print("Top convergence:", convergences[0].title, convergences[0].start_date, convergences[0].end_date)


if __name__ == "__main__":
    main()
