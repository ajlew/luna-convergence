from datetime import date
from pathlib import Path

from major_event_registry import event_presentation_group, major_sky_events, signals_for_day
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from natal_snapshot import build_natal_snapshot
from solar_cycle import solar_anchor_dates
from synthesis import period_report
from timing_map import build_timing_map
from weekly_view import build_weekly_view

TZ = "Australia/Sydney"


def test_2026_solar_anchor_dates_are_foundational():
    rows = solar_anchor_dates(date(2026, 1, 1), date(2026, 12, 31), TZ)
    assert [(d.isoformat(), name, sign) for d, name, sign, _ in rows] == [
        ("2026-03-21", "March Equinox", "Aries"),
        ("2026-06-22", "June Solstice", "Cancer"),
        ("2026-09-23", "September Equinox", "Libra"),
        ("2026-12-22", "December Solstice", "Capricorn"),
    ]

    signals = major_sky_events(date(2026, 1, 1), date(2026, 12, 31), "Libra", TZ)
    anchors = [item for item in signals if item.event_class == "solar_anchor"]
    assert len(anchors) == 4
    assert all(item.tier == "FOUNDATION" for item in anchors)
    assert all(item.must_surface_products == {"daily", "weekly", "monthly", "yearly", "timing"} for item in anchors)
    assert all(event_presentation_group(item, "monthly") == "SOLAR ANCHOR" for item in anchors)
    # Sun-sign whole-sign frame: Libra is House 1, so Aries/Cancer/Libra/Capricorn are 7/10/1/4.
    assert [item.houses for item in anchors] == [(7,), (10,), (1,), (4,)]


def test_daily_and_weekly_cannot_rank_away_september_equinox():
    primary, supporting = signals_for_day(
        date(2026, 9, 23), native_sign="Libra", timezone_name=TZ, product="daily"
    )
    assert primary is not None
    assert primary.event_class == "solar_anchor"
    assert primary.display_label == "September Equinox · Sun enters Libra"

    week = build_weekly_view(date(2026, 9, 21), TZ)
    equinox_day = next(item for item in week if item.reading_date == date(2026, 9, 23))
    assert equinox_day.major_event_label == "September Equinox · Sun enters Libra"
    assert "SOLAR YEAR REBALANCES" in equinox_day.headline


def test_monthly_registry_and_preview_expose_solar_clock_and_anchor():
    result = period_report(
        "Libra",
        date(2026, 9, 1),
        date(2026, 9, 30),
        TZ,
        "September 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    assert any(
        item.get("event_class") == "solar_anchor"
        and item.get("display_label") == "September Equinox · Sun enters Libra"
        for item in result.get("major_sky_events", [])
    )
    assert result["solar_convergence"]["next_solar_gate"] == "September Equinox"

    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=True)
    assert "First principle · The Sun is Luna's primary natural clock" in html
    assert "Your Sun / House 1" in html
    assert "September Equinox" in html
    assert "SOLAR ANCHOR" in html
    assert "--rail:clamp(1rem,4vw,3.2rem)" in html
    assert "padding:clamp(1.8rem,4vw,3rem) var(--rail)" in html


def test_yearly_contains_all_four_solar_anchors():
    result = period_report(
        "Libra",
        date(2026, 1, 1),
        date(2026, 12, 31),
        TZ,
        "2026",
        transition_count=16,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    anchors = [item for item in result.get("major_sky_events", []) if item.get("event_class") == "solar_anchor"]
    assert [item["display_label"] for item in anchors] == [
        "March Equinox · Sun enters Aries",
        "June Solstice · Sun enters Cancer",
        "September Equinox · Sun enters Libra",
        "December Solstice · Sun enters Capricorn",
    ]


def test_timing_shared_sky_uses_reader_sun_sign_and_keeps_solar_anchors():
    snapshot = build_natal_snapshot(
        birth_date=date(1998, 10, 22),
        birth_time_known=False,
        timezone_name="UTC",
    )
    report = build_timing_map(
        snapshot,
        start_date=date(2026, 8, 29),
        timezone_name=TZ,
        max_stories=10,
    )
    anchors = [item for item in report.major_sky_events if item.get("event_class") == "solar_anchor"]
    assert len(anchors) == 4
    assert anchors[0]["display_label"] == "September Equinox · Sun enters Libra"
    # 1998-10-22 is Libra; September Equinox Sun-in-Libra is House 1 in the primary solar frame.
    assert tuple(anchors[0]["houses"]) == (1,)


def test_app_customer_forecast_entry_points_use_sun_sign_first_wording():
    source = Path("app.py").read_text(encoding="utf-8")
    assert source.count("What is your Sun sign (star sign)?") >= 8
    assert "Use your Sun sign unless you know and prefer your rising sign" not in source
    assert "YOUR SUN / HOUSE 1" in source
