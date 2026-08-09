from datetime import date
from io import BytesIO

from pypdf import PdfReader

from monthly_experience_v1 import _arc_evidence_path, build_monthly_experience_html
from monthly_report_pdf_home_v3 import build_monthly_homepage_html
from monthly_report_pdf_v2 import build_monthly_editorial_pdf
from monthly_report_pipeline import build_production_monthly_report


def test_three_cancer_septembers_get_problem_consequence_move_and_horizon():
    for year in (1995, 2017, 2026):
        narrative, result = build_production_monthly_report(
            sign="Cancer", year=year, month=9, timezone_name="America/Mexico_City", nearest_city="Mexico City"
        )
        horizon = narrative.problem_horizon
        assert horizon.get("problem")
        assert horizon.get("if_ignored")
        assert horizon.get("highest_leverage_move")
        assert "Month-end is not the finish line" in horizon.get("timing", "")
        html = build_monthly_experience_html(narrative, result, show_print=False)
        for phrase in ("The problem", "If you ignore it", "How long this stays live", "What keeps this active", "Next change", "Long shift"):
            assert phrase in html


def test_2017_evidence_path_never_runs_backwards():
    narrative, result = build_production_monthly_report(
        sign="Cancer", year=2017, month=9, timezone_name="America/Mexico_City", nearest_city="Mexico City"
    )
    html = _arc_evidence_path(result)
    assert "29-24 September" not in html
    assert "20-30 September 2017" in html


def test_both_pdf_paths_include_problem_layer():
    narrative, result = build_production_monthly_report(
        sign="Cancer", year=2026, month=9, timezone_name="America/Mexico_City", nearest_city="Mexico City"
    )
    home_html = build_monthly_homepage_html(result)
    assert "What needs attention now" in home_html
    assert "How long this stays live" in home_html

    pdf = build_monthly_editorial_pdf(result)
    reader = PdfReader(BytesIO(pdf))
    text = " ".join((page.extract_text() or "") for page in reader.pages)
    assert "What needs attention now" in text
    assert "how long this stays live" in text.lower()
