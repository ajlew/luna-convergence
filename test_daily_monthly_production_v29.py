from __future__ import annotations

from datetime import date
from pathlib import Path

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import _story_is_duplicate, build_daily_narrative
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    config = (root / "site_config.py").read_text(encoding="utf-8")
    daily_source = (root / "daily_narrative_v3.py").read_text(encoding="utf-8")

    # Public product gates.
    assert 'PUBLIC_YEARLY_ENABLED = _environment_flag("LUNA_PUBLIC_YEARLY", False)' in config
    assert 'EDITOR_PREVIEW_ENABLED = _environment_flag("LUNA_EDITOR_PREVIEW", False)' in config
    assert "if PUBLIC_YEARLY_ENABLED:" in app
    assert "monthly_tab = st.container()" in app
    assert "Year-ahead reports are being held back" not in app
    assert "Sagittarius August 2026 Monthly Report Sample" in app

    # Daily: customer story first, CTA high, development-only translation removed.
    assert "daily-monthly-offer" in daily_source
    assert "monthly_price=MONTHLY_PRICE" in app
    assert 'monthly_url=f"/reports?sign={sign}"' in app
    assert "Editorial translation" not in daily_source
    assert "st.expander(TECHNICAL_LABEL, expanded=False)" in daily_source
    assert "### Planetary positions" in daily_source
    assert "### The 12-house reference matrix" in daily_source

    reading = free_daily_reading(
        "Sagittarius",
        date(2026, 8, 2),
        "Australia/Sydney",
    )
    narrative = build_daily_narrative(
        reading,
        sign="Sagittarius",
        reading_date=date(2026, 8, 2),
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=[],
    )
    assert any(
        _story_is_duplicate(paragraph, narrative.relationship_story)
        for paragraph in narrative.today_story[2:]
    )
    assert len(narrative.reflection_questions) == 1
    assert narrative.reflection_questions[0] == "What private truth is shaping the atmosphere at home?"

    # Monthly: one chronological four-act spine with the relationship test inside it.
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
    monthly = build_monthly_narrative(result)
    assert [chapter.label for chapter in monthly.chapters] == [
        "Act I",
        "Act II",
        "Act III",
        "Act IV",
    ]
    assert monthly.chapters[2].title == "Watch what happens next"
    assert monthly.chapters[2].date_range == "17-21 August 2026"

    html = build_monthly_experience_html(monthly, result, show_print=True)
    relationship_line = "steady presence or a passing moment?"
    assert html.count('class="luna-story-act"') == 4
    assert html.count(relationship_line) == 1
    assert '<section class="luna-monthly-section luna-relationship-test">' not in html
    assert "How August unfolds — four acts" in html
    assert "Moments to notice" in html
    assert "Write the next move when the story changes" in html
    assert "Dates worth circling" not in html

    print("Luna Daily + Monthly Production Pass v2.9 tests passed.")


if __name__ == "__main__":
    main()
