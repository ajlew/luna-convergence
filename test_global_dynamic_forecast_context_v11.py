from pathlib import Path

import pytest

from astrology_engine import SIGNS
from monthly_experience_v1 import build_monthly_reader_chronology
from monthly_report_pipeline import build_production_monthly_report
from site_config import DEFAULT_SIGN


APP = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
ALL_SIGN_PERIODS = tuple(
    (sign, 2026 + (index % 3), ((index * 5) % 12) + 1)
    for index, sign in enumerate(SIGNS)
)


def test_public_sign_selection_starts_neutral_globally():
    assert DEFAULT_SIGN is None
    assert 'DEFAULT_SIGN = "Sagittarius"' not in Path(__file__).with_name("site_config.py").read_text(encoding="utf-8")
    assert "SIGNS.index(DEFAULT_SIGN)" not in APP
    assert 'placeholder="Select your star sign"' in APP


def test_monthly_page_has_selected_period_controls_and_no_campaign_period_globals():
    assert '"Forecast month"' in APP
    assert '"Forecast year"' in APP
    assert "SEO_YEAR =" not in APP
    assert "SEO_MONTH =" not in APP
    assert "AUGUST_2026_PREVIEW_HOOKS" not in APP
    assert "_MONTHLY_CANONICAL_EVENTS" not in APP


@pytest.mark.parametrize(
    ("sign", "year", "month"),
    ALL_SIGN_PERIODS + (
        ("Aries", 2026, 8),
        ("Libra", 2026, 9),
        ("Pisces", 2027, 2),
        ("Gemini", 2031, 12),
    ),
)
def test_selected_sign_month_and_year_drive_the_calculated_chronology(sign, year, month):
    narrative, result = build_production_monthly_report(
        sign=sign,
        year=year,
        month=month,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
    )
    rows = build_monthly_reader_chronology(narrative, result)

    assert sign in SIGNS
    assert narrative.sign == sign
    assert rows
    assert all(row["date"].startswith(f"{year:04d}-{month:02d}-") for row in rows)


def test_old_campaign_urls_are_compatibility_redirects_only():
    assert 'url_path="august-2026-horoscopes"' in APP
    assert 'url_path=f"august-2026-{sign_slug(sign)}"' in APP
    assert "_legacy_monthly_redirect(sign)" in APP
    assert 'title=f"{sign} Monthly (legacy link)"' in APP
