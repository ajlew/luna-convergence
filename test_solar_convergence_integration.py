from datetime import date
import json

from monthly_narrative_v1 import build_monthly_narrative, monthly_narrative_markdown
from order_capture import build_order_reference, order_payload_json, parse_order_reference
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="Love and relationships",
    )
    solar = result["solar_convergence"]
    assert solar["headline"] == "Returning light becomes visible direction"
    assert solar["start_house"] == 9
    assert solar["end_house"] == 10
    assert solar["location_basis"] == "customer city"

    narrative = build_monthly_narrative(
        result,
        main_focus="Love and relationships",
        personal_question="",
        order_reference="LC-TEST",
    )
    markdown = monthly_narrative_markdown(narrative)
    assert "# Your Solar Convergence" in markdown
    assert "Returning light becomes visible direction" in markdown
    assert "Solar rule for the month" in markdown
    assert "September Equinox" in markdown
    assert "Location basis" in narrative.technical_appendix_markdown

    reference = build_order_reference(
        "MONTHLY",
        "Sagittarius",
        "2026-08",
        "Australia/Sydney",
        "A1B2C3D4",
        main_focus="Love and relationships",
        personal_question="",
        nearest_city="Sydney",
    )
    parsed = parse_order_reference(reference)
    assert parsed["city_fragment"] == "SYDNEY"

    payload = json.loads(order_payload_json({
        "report_name": "Monthly Strategic Report",
        "email": "customer@example.com",
        "sign": "Sagittarius",
        "period": "August 2026",
        "period_code": "2026-08",
        "timezone": "Australia/Sydney",
        "nearest_city": "Sydney",
        "location_basis": "customer city",
        "main_focus": "Love and relationships",
        "personal_question": "",
        "reference": reference,
    }))
    assert payload["nearest_city"] == "Sydney"
    assert payload["location_basis"] == "customer city"

    yearly = period_report(
        "Sagittarius",
        date(2026, 1, 1),
        date(2026, 12, 31),
        "Australia/Sydney",
        "2026",
        nearest_city="Sydney",
        main_focus="Love and relationships",
    )
    assert len(yearly["solar_year_chapters"]) == 4
    assert "# The Solar Wheel - four strategic chapters" in yearly["markdown"]

    print("Solar Convergence integration tests passed.")
    print(reference)


if __name__ == "__main__":
    main()
