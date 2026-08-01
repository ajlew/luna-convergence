from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
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
        main_focus="General overview",
    )
    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(
        narrative,
        result,
        show_print=True,
        preview=False,
    )

    story_words = sum(len(paragraph.split()) for paragraph in narrative.luna_says)
    chapter_words = sum(
        len(paragraph.split())
        for chapter in narrative.chapters
        for paragraph in chapter.paragraphs
    )

    assert story_words >= 160
    assert chapter_words >= 160
    assert len(narrative.luna_says) >= 5
    assert len(narrative.chapters) == 3
    assert len(narrative.key_dates) >= 4
    assert result.get("monthly_arc")

    assert "min-height:0 !important" in html
    assert "position:sticky" not in html
    assert "Dates worth circling" in html
    assert html.count('class="luna-story-date-card"') >= 4
    assert html.count('class="luna-story-act"') == 3
    assert "detail.open = true" in html
    assert "Monthly arc equation" in html
    assert "Ranked scenario families" in html

    print("Monthly Story with Arc Engine tests passed.")


if __name__ == "__main__":
    main()
