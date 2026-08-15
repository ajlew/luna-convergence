from __future__ import annotations

import re

from luna_first_principles import methodology_metadata
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
    html = html.replace("&amp;", "&").replace("&#x27;", "'")
    return re.sub(r"\s+", " ", html).strip()


def test_first_principles_include_plain_language_evidence_proximity_and_single_chronology():
    metadata = methodology_metadata()
    assert metadata["customer_language_policy"] == "plain_life_areas_no_internal_house_ids"
    assert metadata["evidence_proximity_policy"] == "verified_claim_count_planets_aspects_near_interpretation"
    assert metadata["chronology_policy"] == "single_authoritative_how_the_month_unfolds"


def test_monthly_customer_report_has_one_authoritative_chronology():
    narrative, result = _report(2017)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    assert "How September unfolds" in text
    assert "Dates worth circling" not in text
    assert "Key dates and planetary timing" not in text
    # Data is preserved for other workflows even though duplicate customer renderers are gone.
    assert narrative.key_dates


def test_2017_customer_chronology_keeps_signal_and_moves_dense_proof_to_evidence_layer():
    narrative, result = _report(2017)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    how = text.split("How September unfolds", 1)[1].split("Where the story lands", 1)[0]
    assert "Influence:" in how
    assert "Luna's move" in how
    assert "5 planets are involved in 3 exact pressure contacts" not in how
    assert "Why Luna says this" not in how
    # The evidence-rich source narrative remains available internally.
    assert narrative.luna_says
    assert result.get("events")


def test_customer_rendering_uses_life_areas_instead_of_house_number_codes():
    narrative, result = _report(2026)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    assert not re.search(r"\bH(?:1[0-2]|[1-9])\b", text)
    assert not re.search(r"\bhouse\s+(?:1[0-2]|[1-9])\b", text, flags=re.I)
    assert "career, reputation, authority and visible results" in text
    assert "friends, networks, audiences and future plans" in text


def test_2026_opening_signal_is_directly_connected_without_reprinting_house_proof():
    narrative, result = _report(2026)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    how = text.split("How September unfolds", 1)[1].split("Where the story lands", 1)[0]
    assert "Mercury sextile Mars" in how
    assert "For Sagittarius, Virgo describes career, reputation, authority and visible results" not in how
    assert "career, reputation, authority and visible results" in text


def test_solar_customer_copy_translates_internal_house_numbers():
    narrative, _ = _report(2026)
    solar = " ".join(narrative.solar_paragraphs) + " " + narrative.solar_opportunity + " " + narrative.solar_action
    assert "house 10" not in solar.lower()
    assert "house 11" not in solar.lower()
    assert any(label == "Solar life-area movement" for label, _ in narrative.solar_rows)
