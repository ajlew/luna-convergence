from datetime import date
import json
from pathlib import Path

from forecast_inventory import (
    build_daily_core,
    build_monthly_core,
    build_yearly_core,
    inventory_json,
)
from luna_voice import narrator_principle, voice_profile
from synthesis import period_report
from yearly_experience_v1 import build_yearly_experience_html
from yearly_game_engine import build_yearly_game_map


def main() -> None:
    # One narrator, three distances.
    assert voice_profile("daily").narrator_role == "Sharp observer"
    assert voice_profile("monthly").narrator_role == "Storyteller"
    assert voice_profile("yearly").narrator_role == "Strategist and game narrator"
    assert "reader in control" in narrator_principle()

    # August 2026: preserve the independent relationship test.
    august = period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=12,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    arc = august["monthly_arc"]
    assert arc["headline"] == (
        "A possibility becomes real through the choices that give it shape"
    )
    assert "what earns your trust" in arc["central_storyline"]
    assert "are they showing up for you" in (
        " ".join(arc["relationship_test"])
    )

    relationship = next(
        beat for beat in arc["beats"] if beat["role"] == "relationship test"
    )
    assert relationship["start_date"] == "2026-08-17"
    assert relationship["end_date"] == "2026-08-21"
    assert relationship["title"] == "Venus sextile Jupiter"

    # The eclipse cluster must not be reused as opening, complication and pivot.
    roles = {beat["role"]: beat for beat in arc["beats"]}
    assert roles["inciting event"]["end_date"] < roles["complication"]["start_date"]
    assert roles["relationship test"]["start_date"] > roles["complication"]["start_date"]
    assert roles["climax"]["start_date"] > roles["relationship test"]["start_date"]

    # Yearly: top-down game map, checked against twelve monthly rounds.
    game_map = build_yearly_game_map(
        "Sagittarius",
        2027,
        "Australia/Sydney",
        "Sydney",
        "General year ahead",
    )
    assert len(game_map.games) == 3
    assert 3 <= len(game_map.acts) <= 5
    assert len(game_map.rounds) == 12
    assert game_map.games[0].title == "Attraction versus evidence"
    assert "twelve monthly rounds" in game_map.equation
    assert all(round_.role for round_ in game_map.rounds)

    yearly_result = period_report(
        "Sagittarius",
        date(2027, 1, 1),
        date(2027, 12, 31),
        "Australia/Sydney",
        "2027",
        transition_count=12,
        nearest_city="Sydney",
        main_focus="General year ahead",
    )
    yearly_html = build_yearly_experience_html(yearly_result, show_print=True)
    for required in (
        "Three games organise the year",
        "How the rules change",
        "The year in twelve moves",
        "Annual players and leverage",
        "Why Luna sees this",
        "Print or save report",
    ):
        assert required in yearly_html, required

    # Precomputed inventory carries version, status and a stable hash.
    daily = build_daily_core(
        "Sagittarius",
        date(2026, 8, 1),
        "Australia/Sydney",
        "Sydney",
        status="editorially reviewed",
    )
    monthly = build_monthly_core(
        "Sagittarius",
        2026,
        8,
        "Australia/Sydney",
        "Sydney",
        "Love and relationships",
        status="approved",
    )
    yearly = build_yearly_core(
        "Sagittarius",
        2027,
        "Australia/Sydney",
        "Sydney",
        "General year ahead",
        status="draft",
    )
    assert daily.status == "editorially reviewed"
    assert monthly.status == "approved"
    assert yearly.status == "draft"
    assert len(daily.calculation_hash) == 16
    assert monthly.payload["result"]["monthly_arc"]["relationship_test"]
    assert yearly.payload["result"]["yearly_game_map"]["rounds"]

    document = json.loads(inventory_json((daily, monthly, yearly)))
    assert document["record_count"] == 3
    assert [item["report_type"] for item in document["records"]] == [
        "daily",
        "monthly",
        "yearly",
    ]

    # The editorial library is present in the customer app only in preview mode.
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    assert '("forecast-library", "Forecast library")' in app
    assert 'url_path="forecast-library"' in app
    assert "EDITOR_PREVIEW_ENABLED" in app

    print("Luna Narrator + Forecast Inventory v2.8 tests passed.")


if __name__ == "__main__":
    main()
