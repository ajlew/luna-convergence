from __future__ import annotations

import re

from luna_first_principles import PIPELINE, methodology_metadata
from monthly_experience_v1 import build_monthly_experience_html
from monthly_report_pipeline import build_production_monthly_report


def _report(year: int):
    return build_production_monthly_report(
        sign="Sagittarius",
        year=year,
        month=9,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
    )


def _visible_text(html: str) -> str:
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def test_first_principles_put_trajectory_between_pattern_and_convergence():
    assert PIPELINE[:4] == ("Nature", "Pattern", "Trajectory", "Convergence")
    metadata = methodology_metadata()
    assert metadata["trajectory_policy"] == "show_build_peak_ease_or_reversal_before_story_synthesis"
    assert metadata["bridge_policy"] == "optional_only_never_forced"
    assert metadata["countercurrent_policy"] == "supportive_relief_may_offset_main_pressure_without_becoming_main_plot"
    assert metadata["nature_only_editorial_policy"] == "remove_customer_copy_that_adds_neither_evidence_consequence_nor_choice"


def test_2017_weak_bridge_is_not_forced_and_romance_becomes_countercurrent():
    narrative, result = _report(2017)
    arc = result["monthly_arc"]
    trajectory = result["monthly_trajectory"]
    romance = result["monthly_decision"]["domain_decisions"]["romance"]

    assert arc["primary_house"] == 10
    assert arc["secondary_house"] == 11
    assert arc["tertiary_house"] is None
    assert 0.58 < float(arc["convergence_score"]) < 0.68

    assert trajectory["trajectory"] == "late_storm"
    assert trajectory["countercurrent"]["domain"] == "romance"
    assert trajectory["countercurrent"]["phase"] == "relief_then_test"
    assert "Venus trine Uranus" in " ".join(trajectory["countercurrent"]["support_evidence"])
    assert "Jupiter opposition Uranus" in " ".join(trajectory["countercurrent"]["late_pressure_evidence"])

    assert romance["relevance"] == "COUNTERCURRENT"
    assert romance["posture"] == "QUESTION"
    assert result["monthly_decision"]["portfolio_posture"] == "DEFENSIVE HOLD"
    assert "romance and creativity offer somewhere to breathe" in narrative.hook_headline.lower()


def test_2017_story_tracks_nature_from_warning_to_peak_and_keeps_relief_in_context():
    narrative, result = _report(2017)
    text = " ".join(narrative.luna_says)
    assert "Mars enters Virgo" in text
    assert "Mercury enters Virgo" in text
    assert "New Moon in Virgo" in text
    assert "Venus enters Virgo" in text
    assert "Sun square Saturn" in text
    assert "Mercury opposition Neptune" in text
    assert "Venus trine Uranus" in text
    assert "Jupiter opposition Uranus" in text
    assert "Friction rises to" in text
    assert "Protect essentials, renegotiate" in text
    assert len(narrative.chapters) == 3


def test_customer_report_removes_generic_non_nature_blocks_but_preserves_data():
    narrative, result = _report(2017)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    assert "Romance and validation" not in text
    assert "Ranked scenario families" not in text
    assert "Monthly background weight" not in text
    assert "How September unfolds" in text
    assert "Trajectory:" in text
    assert "Countercurrent:" in text
    # Underlying functionality/data remain available for QA and other workflows.
    assert result["monthly_arc"].get("ranked_scenarios")
    assert result.get("dominant_houses")
    assert narrative.key_dates


def test_2026_strong_bridge_survives_and_is_not_misclassified_as_countercurrent():
    narrative, result = _report(2026)
    arc = result["monthly_arc"]
    assert arc["tertiary_house"] == 11
    assert float(arc["convergence_score"]) >= 0.68
    assert result["monthly_trajectory"].get("countercurrent") is None
    assert result["monthly_decision"]["domain_decisions"]["romance"]["relevance"] == "SECONDARY"
    assert result["monthly_decision"]["portfolio_posture"] == "SELECTIVE ADVANCE"
