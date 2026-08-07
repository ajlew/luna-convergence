from datetime import date

from monthly_narrative_v1 import build_monthly_narrative
from monthly_qa import audit_batch_headlines
from synthesis import period_report


def main() -> None:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    reports = []
    for sign in signs:
        result = period_report(
            sign,
            date(2026, 8, 1),
            date(2026, 8, 31),
            "Australia/Sydney",
            "August 2026",
            transition_count=9,
            nearest_city="Sydney",
            main_focus="General overview",
        )
        reports.append(result)
        arc = result["monthly_arc"]
        assert arc["primary_house"]
        assert arc["secondary_house"]
        assert arc["selection_rationale"]
        assert result["monthly_qa"]["status"] == "pass", (sign, result["monthly_qa"])
        narrative = build_monthly_narrative(result)
        assert 3 <= len(narrative.chapters) <= 4
        assert narrative.love_story[0]
        assert narrative.work_story[0]
        assert narrative.money_story[0]
        eclipse_titles = [
            event["title"] for event in result["events"] if event["kind"] == "eclipse"
        ]
        evidence = " ".join(
            item for chapter in narrative.chapters for item in chapter.evidence
        )
        for title in eclipse_titles:
            assert title in evidence, (sign, title)

    batch = audit_batch_headlines(reports)
    assert batch["status"] == "pass", batch
    assert batch["unique"] == 12, batch

    by_sign = {report["sign"]: report for report in reports}
    expected_eclipse_axis = {
        "Aries": (5, 12),
        "Taurus": (4, 11),
        "Gemini": (3, 10),
        "Cancer": (2, 9),
        "Leo": (1, 8),
        "Virgo": (12, 7),
        "Libra": (11, 6),
        "Scorpio": (10, 5),
        "Sagittarius": (9, 4),
        "Capricorn": (8, 3),
        "Aquarius": (7, 2),
        "Pisces": (6, 1),
    }
    for sign, expected in expected_eclipse_axis.items():
        arc = by_sign[sign]["monthly_arc"]
        assert (arc["primary_house"], arc["secondary_house"]) == expected, (sign, arc)

    assert by_sign["Leo"]["monthly_arc"]["supporting_house"] == 9

    print("Monthly Narrative v3.1 full 12-sign event-led tests passed.")


if __name__ == "__main__":
    main()
