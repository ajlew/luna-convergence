from monthly_experience_v1 import build_monthly_experience_html
from monthly_report_pipeline import build_production_monthly_report


def _build():
    return build_production_monthly_report(
        sign="Sagittarius", year=2026, month=8,
        timezone_name="Australia/Sydney", nearest_city="Sydney"
    )


def test_monthly_removes_redundant_luna_says_block_but_keeps_source_narrative():
    narrative, result = _build()
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    assert narrative.luna_says
    assert narrative.luna_says[0] not in html
    assert ">Luna says<" not in html
    assert "Why Luna says this" not in html


def test_monthly_uses_newspaper_dates_and_compact_signal_lines():
    narrative, result = _build()
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    assert "Monthly briefing" in html
    assert "How August unfolds" in html
    assert "07 AUG" in html
    assert "13 AUG" in html
    assert "28 AUG" in html
    assert "Sun trine Saturn (~0.03°)" in html
    assert "Influence: 1-10 August 2026" in html
    assert "5 planets are involved in 3 exact pressure contacts" not in html.split("How August unfolds", 1)[1].split("Where the story lands", 1)[0]


def test_monthly_keeps_actions_and_evidence_but_hides_internal_posture_labels():
    narrative, result = _build()
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    assert "Where the story lands" in html
    assert "From reading the future to writing it." in html
    assert "Why Luna sees this" in html
    assert "Solar clock evidence" in html
    assert "Full technical evidence" in html
    assert "NOT ACT · PASS" not in html
    assert 'class="luna-strategy-badge"' not in html
