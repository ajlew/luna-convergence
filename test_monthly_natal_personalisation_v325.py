from datetime import date, time
from pathlib import Path

from monthly_natal_overlay import build_monthly_natal_overlay
from monthly_report_pipeline import build_production_monthly_report
from natal_snapshot import build_natal_snapshot, encode_natal_profile, natal_profile_summary
from stripe_checkout import order_metadata


def _snapshot():
    return build_natal_snapshot(
        birth_date=date(1965, 12, 1),
        birth_time_known=True,
        birth_time=time(2, 0),
        timezone_name="UTC",
        location_name="Alotau, Papua New Guinea",
        latitude=-10.3167,
        longitude=150.4667,
    )


def test_free_natal_uses_one_interpretive_layer():
    app_source = Path("app.py").read_text(encoding="utf-8")
    assert 'st.markdown("## Three patterns that keep repeating")' not in app_source
    assert 'st.markdown("## Your strongest signatures")' in app_source


def test_compact_profile_contains_derived_geometry_not_raw_birth_details():
    snapshot = _snapshot()
    profile = encode_natal_profile(snapshot)
    assert len(profile) < 450
    assert "1965" not in profile
    assert "Alotau" not in profile
    assert "02:00" not in profile
    assert "Emotionally reserved" in profile
    assert natal_profile_summary(snapshot) == "Sun Sagittarius · Moon Pisces · Rising Pisces"


def test_stripe_metadata_carries_natal_profile_without_raw_birth_fields():
    snapshot = _snapshot()
    metadata = order_metadata(
        {
            "product_code": "MONTHLY",
            "report_name": "Monthly Strategic Report",
            "sign": "Sagittarius",
            "period": "August 2026",
            "period_code": "2026-08",
            "timezone": "Australia/Sydney",
            "nearest_city": "Sydney",
            "location_basis": "city",
            "main_focus": "General overview",
            "personal_question": "",
            "reference": "TEST",
            "natal_profile": encode_natal_profile(snapshot),
            "natal_summary": natal_profile_summary(snapshot),
            "natal_precision": "Exact birth time supplied · Ascendant and houses calculated",
            # These values must never be passed through order_metadata.
            "birth_date": "1965-12-01",
            "birth_time": "02:00",
            "birthplace": "Alotau, Papua New Guinea",
        }
    )
    assert metadata["natal_profile"]
    assert metadata["natal_summary"] == "Sun Sagittarius · Moon Pisces · Rising Pisces"
    assert "birth_date" not in metadata
    assert "birth_time" not in metadata
    assert "birthplace" not in metadata


def test_paid_monthly_overlay_finds_personal_contacts():
    snapshot = _snapshot()
    _, result = build_production_monthly_report(
        sign="Sagittarius",
        year=2026,
        month=8,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
        main_focus="General overview",
    )
    overlay = build_monthly_natal_overlay(encode_natal_profile(snapshot), result)
    assert overlay["activations"]
    assert len(overlay["activations"]) <= 3
    assert any(item.get("signature") for item in overlay["activations"])
    assert all("natal" in item["signal"].lower() for item in overlay["activations"])
