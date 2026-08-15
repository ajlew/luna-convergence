from __future__ import annotations

import re
from datetime import datetime

from luna_first_principles import LUNA_FIRST_PRINCIPLES_VERSION, methodology_metadata
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


def _visible(html: str) -> str:
    html = re.sub(r"<style.*?</style>|<script.*?</script>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def _story_articles(html: str) -> list[str]:
    return re.findall(r'<article class="luna-story-act">(.*?)</article>', html, flags=re.S)


def test_first_principles_v15_uses_relief_and_one_window_one_move():
    assert LUNA_FIRST_PRINCIPLES_VERSION == "1.7"
    meta = methodology_metadata()
    assert meta["customer_relief_label"] == "Relief"
    assert meta["window_chapter_policy"] == "one_trajectory_window_one_customer_chapter_one_move"
    assert meta["event_window_policy"] == "customer_event_date_must_fall_inside_displayed_window"


def test_customer_uses_relief_not_countercurrent():
    narrative, result = _report(2017)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible(html)
    assert "Relief:" in text
    assert "countercurrent" not in text.lower()
    assert "genuine relief" in text.lower()


def test_each_trajectory_window_renders_as_one_card_with_one_move():
    for year in (1995, 2017, 2026):
        narrative, result = _report(year)
        html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
        articles = _story_articles(html)
        assert len(articles) == 3
        for article in articles:
            assert article.count('class="luna-chapter-move"') == 1


def test_1995_windows_are_separate_and_timed_advance_names_what_moves():
    narrative, result = _report(1995)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible(html)
    assert "09 SEP Full Moon in Pisces Influence: 1-10 September 1995" in text
    assert "15 SEP Sun opposition Saturn" in text and "Influence: 11-20 September 1995" in text
    assert "25 SEP New Moon in Libra Influence: 21-30 September 1995" in text
    assert "Negotiate home and family conditions" in narrative.portfolio_rationale + " " + " ".join(narrative.action_plan)
    assert "Advance the workable part of home and family" in " ".join(narrative.action_plan)


def test_2026_event_dates_stay_inside_windows_and_full_moon_returns_as_result():
    narrative, result = _report(2026)
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible(html)
    assert "01 SEP Mercury sextile Mars" in text and "Influence: 1-10 September 2026" in text
    assert "11 SEP New Moon in Virgo Influence: 11-20 September 2026" in text
    assert "27 SEP Full Moon in Aries Influence: 21-30 September 2026" in text
    assert "16-18 September 2026 · Venus square Pluto" in text
    assert "Neptune sextile Pluto Influence window: 21-30 September 2026" not in text


def test_2026_bridge_is_explained_in_customer_story_with_nature_evidence():
    narrative, result = _report(2026)
    bridge = result["monthly_trajectory"]["bridge"]
    assert bridge and bridge["house"] == 11
    assert "Mercury enters Libra" in " ".join(bridge["movements"])
    assert "Sun enters Libra" in " ".join(bridge["movements"])
    html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    text = _visible(html)
    assert "form the bridge" not in text
