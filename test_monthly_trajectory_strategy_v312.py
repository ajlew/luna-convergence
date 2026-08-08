from __future__ import annotations

import re

from luna_first_principles import LUNA_FIRST_PRINCIPLES_VERSION, methodology_metadata
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


def test_first_principles_v14_makes_choice_time_sensitive():
    assert LUNA_FIRST_PRINCIPLES_VERSION == "1.6"
    meta = methodology_metadata()
    assert meta["time_sensitive_choice_policy"] == "window_strategy_then_monthly_synthesis_never_average_only"
    assert meta["evidence_count_policy"] == "deduplicated_claim_count_must_match_visible_contacts"


def test_1995_recovers_and_uses_timed_advance_instead_of_flat_hold():
    narrative, result = _report(1995)
    trajectory = result["monthly_trajectory"]
    decision = result["monthly_decision"]
    arc = result["monthly_arc"]

    assert trajectory["trajectory"] == "recovery"
    windows = trajectory["windows"]
    assert windows[0]["balance"] < -15
    assert windows[1]["balance"] > 10
    assert windows[-1]["balance"] > windows[0]["balance"] + 15
    assert [window["posture"] for window in windows] == ["NEGOTIATE", "ADVANCE", "QUESTION"]
    assert decision["portfolio_posture"] == "TIMED ADVANCE"
    assert arc["tertiary_house"] is None  # 0.7 is not enough to force a bridge anymore.
    assert "begins to loosen" in narrative.hook_headline.lower()


def test_2017_still_reads_as_late_storm_and_defensive_hold():
    narrative, result = _report(2017)
    trajectory = result["monthly_trajectory"]
    decision = result["monthly_decision"]

    assert trajectory["trajectory"] == "late_storm"
    assert trajectory["windows"][-1]["friction"] >= 60
    assert trajectory["windows"][-1]["balance"] <= -20
    assert decision["portfolio_posture"] == "DEFENSIVE HOLD"
    assert "pressure tightens late" in narrative.hook_headline.lower()


def test_2026_strong_bridge_survives_higher_causality_gate():
    _narrative, result = _report(2026)
    assert result["monthly_arc"]["tertiary_house"] == 11
    assert float(result["monthly_arc"]["convergence_score"]) >= 0.75


def test_customer_evidence_deduplicates_aspects_and_matches_counts():
    narrative, result = _report(1995)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    # The old report printed Uranus square True Node twice in the same late-window claim.
    late = text[text.find("21-30 September 1995"):text.find("Where the story lands")]
    assert "Uranus square True Node (~0.01°); Uranus square True Node (~0.01°)" not in late


def test_solar_background_keeps_nature_and_drops_generic_mini_forecast():
    narrative, result = _report(1995)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    assert "The Sun is Luna's primary natural clock" in text
    assert "Local season" not in text
    assert "Libra Gate · September Equinox" in text
    assert "Nature note:" in text
    assert "Opportunity: Use career" not in text
    assert "Risk: Watch for confusing popularity" not in text
    assert "Response: During the Virgo phase" not in text


def test_money_copy_respects_non_advance_strategy():
    narrative_2017, result_2017 = _report(2017)
    assert result_2017["monthly_decision"]["domain_decisions"]["money"]["posture"] == "PASS"
    assert "headline alone is not a reason to chase it" in narrative_2017.money_story[0]

    narrative_1995, result_1995 = _report(1995)
    assert result_1995["monthly_decision"]["domain_decisions"]["money"]["posture"] == "NEGOTIATE"
    assert "improve the amount, timing, ownership or obligation" in narrative_1995.money_story[0]
