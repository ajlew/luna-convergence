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

    chapter_words = sum(
        len(paragraph.split())
        for chapter in narrative.chapters
        for paragraph in chapter.paragraphs
    )

    assert chapter_words >= 150
    assert len(narrative.chapters) == 4
    assert narrative.chapters[2].title == "Relationship test"
    assert len(narrative.key_dates) >= 4
    assert result.get("monthly_arc")

    assert "min-height:0 !important" in html
    assert "position:sticky" not in html
    assert "Moments to notice" in html
    assert "Dates worth circling" not in html
    assert html.count('class="luna-story-date-card"') >= 4
    assert html.count('class="luna-story-act"') == 4
    assert "detail.open = true" in html
    assert "Evidence path" in html
    assert "Ranked scenario families" in html

    print("Monthly four-act Story Engine tests passed.")


if __name__ == "__main__":
    main()
