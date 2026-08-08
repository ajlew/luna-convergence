from datetime import date

from luna_first_principles import (
    CORRESPONDENCE_NOTE,
    LUNA_FIRST_PRINCIPLES_VERSION,
    PIPELINE,
    build_calibration_record,
    capacity_label,
    climate_label,
    methodology_metadata,
    validate_first_principles_contract,
)
from monthly_decision_engine import evaluate_monthly_decision
from synthesis import period_report


def test_permanent_pipeline_and_methodology_metadata():
    metadata = methodology_metadata()
    assert metadata["version"] == LUNA_FIRST_PRINCIPLES_VERSION
    assert metadata["pipeline"] == list(PIPELINE)
    assert metadata["narrator_authority"] == "explain_only_never_override_calculation"
    assert metadata["historical_test_policy"] == "blind_no_expected_answer_hardcodes"
    assert len(metadata["principles"]) >= 15


def test_plain_english_climate_and_capacity_labels():
    assert climate_label(49, 40, 10) == "Supportive but mixed"
    assert climate_label(42, 49, 9) == "Friction slightly dominates"
    assert capacity_label(41) == "Manageable pressure"
    assert capacity_label(70) == "High pressure"


def test_calibration_record_never_auto_reweights():
    record = build_calibration_record(
        forecast_id="Sagittarius-2017-09",
        calculation_snapshot={"support": 42, "friction": 49},
        observed_outcome="",
    )
    assert record["auto_reweight"] is False
    assert "never_rewrite_astronomy" in record["learning_policy"]


def test_monthly_decision_carries_first_principles_contract():
    report = period_report(
        "Sagittarius",
        date(2026, 9, 1),
        date(2026, 9, 30),
        "Australia/Sydney",
        "September 2026",
        nearest_city="Sydney",
        main_focus="General overview",
    )
    decision = report["monthly_decision"]
    assert decision["first_principles_version"] == LUNA_FIRST_PRINCIPLES_VERSION
    assert decision["correspondence_note"] == CORRESPONDENCE_NOTE
    assert decision["climate_label"]
    assert decision["capacity_label"]
    assert decision["first_principles_trace"]["choice"]
    assert report["luna_first_principles"]["version"] == LUNA_FIRST_PRINCIPLES_VERSION
    qa = validate_first_principles_contract(decision)
    assert qa["status"] == "pass"
