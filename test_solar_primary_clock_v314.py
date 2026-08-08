from __future__ import annotations

import re
from datetime import date

from luna_first_principles import FIRST_PRINCIPLES, LUNA_FIRST_PRINCIPLES_VERSION, PIPELINE, methodology_metadata
from monthly_experience_v1 import build_monthly_experience_html
from monthly_report_pipeline import build_production_monthly_report
from solar_cycle import daily_solar_convergence, monthly_solar_convergence, solar_gate_label


def _visible(html: str) -> str:
    html = re.sub(r"<style.*?</style>|<script.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def test_sun_is_first_principle_and_first_pipeline_reference():
    assert LUNA_FIRST_PRINCIPLES_VERSION == "1.6"
    assert FIRST_PRINCIPLES[0] == "The Sun is Luna's primary natural clock."
    assert PIPELINE[:6] == (
        "Sun / Solar Clock",
        "Local Light",
        "Planetary Weather",
        "Pattern",
        "Trajectory",
        "Convergence",
    )
    meta = methodology_metadata()
    assert meta["solar_clock_policy"] == "sun_primary_clock_aries_gate_head_local_light_location_aware"
    assert meta["local_light_policy"] == "location_changes_daylight_experience_never_zodiac_order"
    assert meta["season_label_policy"] == "do_not_use_hemisphere_season_names_as_structural_inputs"


def test_sydney_and_london_share_solar_clock_but_observe_opposite_light():
    d = date(2026, 9, 15)
    sydney = daily_solar_convergence("Sagittarius", d, "Australia/Sydney", nearest_city="Sydney")
    london = daily_solar_convergence("Sagittarius", d, "Europe/London", nearest_city="London")

    assert sydney.solar_sign == london.solar_sign == "Virgo"
    assert sydney.next_solar_gate == london.next_solar_gate == "September Equinox"
    assert solar_gate_label(sydney.next_solar_gate) == "Libra Gate · September Equinox"
    assert sydney.light_direction == "Increasing"
    assert london.light_direction == "Decreasing"
    assert "Aries-to-Pisces solar sequence" in sydney.meaning[1]
    assert "Aries-to-Pisces solar sequence" in london.meaning[1]
    assert "Sydney" in sydney.meaning[1]
    assert "London" in london.meaning[1]


def test_monthly_solar_clock_is_location_aware_without_season_labels():
    sydney = monthly_solar_convergence("Sagittarius", 2026, 9, "Australia/Sydney", nearest_city="Sydney")
    london = monthly_solar_convergence("Sagittarius", 2026, 9, "Europe/London", nearest_city="London")
    assert sydney.light_direction == "Increasing"
    assert london.light_direction == "Decreasing"
    assert "Libra Gate · September Equinox" in sydney.meaning[2]
    assert "Libra Gate · September Equinox" in london.meaning[2]
    forbidden = ("Spring", "Summer", "Autumn", "Winter")
    joined = " ".join(sydney.meaning + london.meaning)
    assert not any(word in joined for word in forbidden)


def test_customer_monthly_report_surfaces_solar_clock_near_front():
    narrative, result = build_production_monthly_report(
        sign="Sagittarius",
        year=2026,
        month=9,
        timezone_name="Europe/London",
        nearest_city="London",
    )
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible(html)
    assert "First principle · The Sun is Luna's primary natural clock" in text
    assert "Your Sun Sagittarius" in text
    assert "Current Sun Virgo → Libra" in text
    assert "Libra Gate · September Equinox" in text
    assert "Local light Decreasing · London" in text
    assert "Local geography changes the light you experience, not the universal Aries-to-Pisces solar sequence." in text
    assert "Local season" not in text
