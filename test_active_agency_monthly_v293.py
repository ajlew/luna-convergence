from __future__ import annotations

from datetime import date
from pathlib import Path

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from sanity_check_monthly import _duplicate_groups
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
    html = build_monthly_experience_html(narrative, result, show_print=True)

    assert narrative.hook_headline == (
        "A possibility becomes real when you choose where it belongs"
    )
    assert narrative.agency_rule == "From reading the future to writing it."
    assert [chapter.hook for chapter in narrative.chapters] == [
        "You turn possibility into momentum",
        "You bring the details into focus",
        "You see whether the spark can hold",
        "You choose what belongs in your life",
    ]
    assert narrative.action_plan == (
        "Choose the possibility that feels both alive and aligned.",
        "Name the standard that will guide your yes.",
        "Write one next move that turns insight into direction.",
    )
    assert not _duplicate_groups(narrative)

    for required in (
        "Moments to notice",
        "Write the next move when the story changes",
        "From reading the future to writing it.",
        "are they showing up for you, or only enjoying the moment?",
    ):
        assert required in html, required

    for rejected in (
        "Shift from applicant to gatekeeper",
        "The invitation gets serious when it needs a place in your life",
        "Attention meets the evidence test",
        "The public result must fit private life",
        "Let the month come toward you",
    ):
        assert rejected not in html, rejected

    config = Path("site_config.py").read_text(encoding="utf-8")
    assert 'PUBLIC_YEARLY_ENABLED = _environment_flag("LUNA_PUBLIC_YEARLY", False)' in config
    assert 'BUILD_LABEL = "Luna Active Agency Monthly v2.9.3"' in config

    print("Active Agency Monthly v2.9.3 tests passed.")


if __name__ == "__main__":
    main()
