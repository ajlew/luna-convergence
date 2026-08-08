from __future__ import annotations

from luna_first_principles import NARRATIVE_PROGRESSION_RULE, methodology_metadata
from monthly_report_pipeline import build_production_monthly_report


def _report(year: int):
    return build_production_monthly_report(
        sign="Sagittarius",
        year=year,
        month=9,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
    )


def test_first_principles_now_include_narrative_progression_and_domain_asymmetry():
    metadata = methodology_metadata()
    assert "Evidence may recur; interpretation must advance." in metadata["principles"]
    assert metadata["narrative_progression_rule"] == list(NARRATIVE_PROGRESSION_RULE)
    assert metadata["portfolio_policy"] == "preserve_domain_asymmetry_before_monthly_synthesis"


def test_2017_main_story_advances_instead_of_repeating_full_manifestation_list():
    narrative, result = _report(2017)
    main = " ".join(narrative.luna_says).lower()
    repeated_phrase = "a manager, leader or key colleague leaving unexpectedly"
    assert main.count(repeated_phrase) <= 1
    assert "that professional shift becomes concrete" in main
    assert "the closing decision is therefore" in main
    assert "act on the strongest supported opportunity" not in main
    assert "act on the strongest supported opportunity" not in " ".join(item.response.lower() for item in narrative.key_dates)


def test_strategy_authority_aligns_public_advice_and_preserves_asymmetry():
    n2017, r2017 = _report(2017)
    n2026, r2026 = _report(2026)

    d17 = r2017["monthly_decision"]
    d26 = r2026["monthly_decision"]

    assert d17["portfolio_posture"] in {"RENEGOTIATE", "DEFENSIVE HOLD", "PASS", "PROBE"}
    assert d26["portfolio_posture"] == "SELECTIVE ADVANCE"
    assert d26["domain_decisions"]["work"]["posture"] == "ADVANCE"
    assert d26["domain_decisions"]["romance"]["posture"] == "NEGOTIATE"
    assert d26["domain_decisions"]["money"]["posture"] == "PASS"
    assert n2026.portfolio_posture == "SELECTIVE ADVANCE"
    assert "Advance where support is clean" in n2026.validation_rule


def test_primary_work_card_inherits_the_h10_story_in_2026():
    narrative, _ = _report(2026)
    text = narrative.work_story[0].lower()
    assert any(token in text for token in ("promotion", "new position", "leadership", "recognition", "prestigious client"))


def test_public_evidence_beats_have_traceable_house_provenance():
    _, result = _report(2026)
    beats = [item for item in result["monthly_arc"]["beats"] if float(item.get("score", 0.0)) > 0]
    assert beats
    for beat in beats:
        assert "direct_houses" in beat
        assert "connected_houses" in beat
        assert "narrative_house" in beat
        assert "connection_reason" in beat
    new_moon = next(item for item in beats if item.get("title") == "New Moon in Virgo")
    assert 10 in new_moon["direct_houses"]
    assert new_moon["narrative_house"] == 10


def test_strategy_aligned_beat_responses_do_not_contradict_domain_posture():
    _, result = _report(2026)
    domains = result["monthly_decision"]["domain_decisions"]
    for beat in result["monthly_arc"]["beats"]:
        if float(beat.get("score", 0.0)) <= 0:
            continue
        posture = str(beat.get("strategy_posture", ""))
        response = str(beat.get("response", "")).lower()
        if posture in {"NEGOTIATE", "HOLD", "PASS", "QUESTION"}:
            assert "act on the strongest supported opportunity" not in response
