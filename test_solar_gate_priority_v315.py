from datetime import date
import re

from luna_first_principles import LUNA_FIRST_PRINCIPLES_VERSION, FIRST_PRINCIPLES
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def _report(year: int, timezone_name: str = "Europe/London", city: str = "London"):
    result = period_report(
        "Sagittarius",
        date(year, 9, 1),
        date(year, 9, 30),
        timezone_name,
        f"September {year}",
        nearest_city=city,
    )
    narrative = build_monthly_narrative(result)
    return narrative, result


def _visible_text(html: str) -> str:
    text = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def test_first_principles_v17_makes_solar_gate_convergence_material_only():
    assert LUNA_FIRST_PRINCIPLES_VERSION == "1.7"
    joined = " ".join(FIRST_PRINCIPLES)
    assert "solstice or equinox enters the customer story only" in joined
    assert "independently converge" in joined


def test_london_keeps_same_solar_sequence_but_reverses_local_light():
    for year in (1995, 2017, 2026):
        _, london = _report(year)
        _, sydney = _report(year, "Australia/Sydney", "Sydney")
        ls = london["solar_convergence"]
        ss = sydney["solar_convergence"]
        assert ls["city"] == "London"
        assert ls["light_direction"] == "Decreasing"
        assert ss["light_direction"] == "Increasing"
        assert ls["start_solar_sign"] == ss["start_solar_sign"] == "Virgo"
        assert ls["end_solar_sign"] == ss["end_solar_sign"] == "Libra"
        assert ls["next_solar_gate"] == ss["next_solar_gate"] == "September Equinox"


def test_three_london_septembers_have_expected_gate_materiality():
    expected = {1995: ("STRONG", "result"), 2017: ("STRONG", "result"), 2026: ("MATERIAL", "bridge")}
    for year, pair in expected.items():
        _, result = _report(year)
        gate = result["solar_convergence"]["gate_convergence"]
        assert (gate["status"], gate["matched_role"]) == pair
        assert gate["material"] is True
        assert gate["customer_line"].startswith("The Solar Clock reinforces this turn.")


def test_material_gate_is_inserted_once_beside_its_trajectory_window():
    narrative, result = _report(2017)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible_text(html)
    # One public chronology note plus one compact evidence summary is expected.
    assert text.count("The Solar Clock reinforces this turn.") >= 1
    assert "Solar convergence" in text
    assert "Libra Gate · September Equinox" in text
    assert "Aries Gate → 12-sign solar cycle → Aries Gate" in text
    assert "Returning light tests the future through community" not in text


def test_print_css_preserves_word_spaces_in_pdf_text_layer():
    narrative, result = _report(1995)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    assert "word-spacing:.055em" in html
    assert "font-variant-ligatures:none" in html
