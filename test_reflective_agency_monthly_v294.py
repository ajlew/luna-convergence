from __future__ import annotations

from datetime import date
import re

from bs4 import BeautifulSoup

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


EXPECTED_HOOKS = [
    "Shaping possibility into momentum",
    "Bringing details into focus",
    "Watching whether the spark holds",
    "Selecting what remains in life",
]


def _customer_text(html: str) -> str:
    text = " ".join(
        item.strip()
        for item in BeautifulSoup(html, "html.parser").get_text(" ").split()
        if item.strip()
    )
    return text.split("Why Luna sees this", 1)[0]


def _second_person_count(text: str) -> int:
    return len(
        re.findall(
            r"\b(?:you|your|you\'re|you\'ve|you\'ll|yourself)\b",
            text.lower(),
        )
    )


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
    customer_text = _customer_text(html)

    assert [chapter.hook for chapter in narrative.chapters] == EXPECTED_HOOKS
    assert narrative.hook_headline == (
        "A possibility becomes real through the choices that give it shape"
    )
    assert narrative.agency_rule == "From reading the future to writing it."

    for rejected in (
        "You turn possibility into momentum",
        "You bring the details into focus",
        "You see whether the spark can hold",
        "You choose what belongs in your life",
        "Where you take the story",
    ):
        assert rejected not in html, rejected

    # Direct address remains available for emotional intimacy, but it should
    # not dominate the narrator. August stays below one second-person reference
    # per 100 customer-facing words.
    words = re.findall(r"\b\w+[’']?\w*\b", customer_text)
    second_person = _second_person_count(customer_text)
    assert second_person <= 6, second_person
    assert second_person / max(1, len(words)) < 0.01

    print(
        "Reflective Agency Monthly v2.9.4 tests passed: "
        f"{second_person} second-person references across {len(words)} words."
    )


if __name__ == "__main__":
    main()
