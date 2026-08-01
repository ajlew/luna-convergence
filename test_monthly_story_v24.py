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

    story_words = sum(
        len(paragraph.split())
        for paragraph in narrative.luna_says
    )
    chapter_words = sum(
        len(paragraph.split())
        for chapter in narrative.chapters
        for paragraph in chapter.paragraphs
    )

    assert story_words >= 170
    assert chapter_words >= 180
    assert len(narrative.luna_says) == 4
    assert len(narrative.chapters) == 3
    assert len(narrative.key_dates) >= 6

    assert "min-height:0 !important" in html
    assert "position:sticky" not in html
    assert "Dates worth circling" in html
    assert html.count('class="luna-story-date-card"') >= 3
    assert html.count('class="luna-story-act"') == 3
    assert "detail.open = true" in html
    assert "A message, invitation, flirtation" in html
    assert "shared cost" in html
    assert "A real connection can discuss timing" in html

    print("Monthly Story + Compact Hero v2.4 tests passed.")


if __name__ == "__main__":
    main()
