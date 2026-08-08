from types import SimpleNamespace

from monthly_experience_v1 import _generated_report_details


def _narrative(label="September 2026", sign="Sagittarius"):
    return SimpleNamespace(label=label, sign=sign)


def test_print_filename_appends_london_city():
    result = {
        "timezone_name": "Europe/London",
        "solar_convergence": {"city": "London"},
    }
    details = _generated_report_details(_narrative(), result)
    assert details["file_title"] == "2026-09_Sagittarius_Monthly_London"


def test_print_filename_appends_multiword_city_safely():
    result = {
        "timezone_name": "America/New_York",
        "solar_convergence": {"city": "New York"},
    }
    details = _generated_report_details(_narrative(), result)
    assert details["file_title"] == "2026-09_Sagittarius_Monthly_New_York"


def test_print_filename_preserves_legacy_name_when_city_missing():
    result = {"timezone_name": "UTC"}
    details = _generated_report_details(_narrative(), result)
    assert details["file_title"] == "2026-09_Sagittarius_Monthly"
