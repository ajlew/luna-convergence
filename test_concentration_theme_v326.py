from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from concentration_theme import build_monthly_concentration_theme
from monthly_report_pipeline import build_production_monthly_report
from natal_snapshot import build_natal_snapshot
from solar_year_wave import solar_year_wave_svg


def test_natal_forest_detects_three_personal_sign_environments():
    snapshot = build_natal_snapshot(
        birth_date=date(1965, 12, 1),
        birth_time_known=True,
        birth_time=time(2, 0),
        timezone_name="UTC",
        location_name="Alotau, Papua New Guinea",
        latitude=-10.3167,
        longitude=150.4667,
    )
    clusters = snapshot.concentration_theme["clusters"]
    by_sign = {row["sign"]: set(row["planets"]) for row in clusters}
    assert by_sign["Sagittarius"] == {"Sun", "Mercury"}
    assert by_sign["Pisces"] == {"Moon", "Saturn"}
    assert by_sign["Capricorn"] == {"Venus", "Mars"}
    assert "Read the aspects below" in snapshot.concentration_theme["summary"]


def test_august_2026_sagittarius_monthly_forest_is_leo_ninth_house():
    _narrative, result = build_production_monthly_report(
        sign="Sagittarius",
        year=2026,
        month=8,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
    )
    theme = build_monthly_concentration_theme(result)
    assert theme["sign"] == "Leo"
    assert theme["house"] == 9
    assert {"Sun", "Mercury", "Jupiter"}.issubset(set(theme["planets"]))
    assert theme["headline"] == "Visibility wants a larger stage"


def test_compact_solar_wave_keeps_clock_without_repeating_labels():
    now = datetime(2026, 8, 15, 13, 26, tzinfo=ZoneInfo("Australia/Sydney"))
    compact = solar_year_wave_svg(now, "Australia/Sydney", compact=True)
    full = solar_year_wave_svg(now, "Australia/Sydney")
    assert 'viewBox="0 0 760 72"' in compact
    assert 'solar-year-wave-wrap compact' in compact
    assert "TROPIC OF CANCER" not in compact
    assert "MAR EQUINOX" not in compact
    assert "SUN · LEO" in compact
    assert "TROPIC OF CANCER" in full
    assert "MAR EQUINOX" in full


def test_solar_wave_is_shared_site_chrome_not_duplicated_inside_daily():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "def _render_site_solar_wave" in source
    assert "_render_site_solar_wave(current_page.url_path)" in source
    daily_block = source[source.index("def _render_lean_daily"):source.index("def _render_site_solar_wave")]
    assert "solar_year_wave_svg(" not in daily_block
