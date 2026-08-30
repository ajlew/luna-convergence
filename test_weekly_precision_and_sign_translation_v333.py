from datetime import date
from pathlib import Path

from astrology_engine import SIGNS
from luna_life_scenes import domain_key
from weekly_view import (
    build_weekly_sign_translation,
    build_weekly_synthesis,
    build_weekly_view,
    weekly_social_card_copy,
)


MONDAY = date(2026, 8, 31)
TZ = "Australia/Sydney"


def _week():
    return build_weekly_view(MONDAY, TZ)


def test_weekly_uses_closest_local_day_orb_and_exact_time():
    monday = _week()[0]

    assert monday.headline == "THE MOOD NEEDS STRUCTURE."
    assert "exact today" in monday.evidence
    assert "approximately 1:18 pm AEST" in monday.evidence
    assert "make louder" not in " ".join(
        (monday.line_one, monday.line_two, monday.action)
    ).lower()
    assert "Set one boundary" in monday.action


def test_pair_specific_copy_replaces_generic_conjunction_and_square_language():
    by_day = {item.weekday: item for item in _week()}

    assert by_day["Wednesday"].headline == "THE INNER AND OUTER ANSWERS AGREE."
    assert by_day["Friday"].headline == "THE FEELING CHANGED FASTER THAN THE PLAN."
    assert by_day["Saturday"].headline == "THE FEELING AND THE MESSAGE DISAGREE."
    assert "Check the message before sending" in by_day["Saturday"].action
    assert by_day["Sunday"].action


def test_weekly_synthesis_connects_support_and_pressure():
    synthesis = build_weekly_synthesis(_week())
    text = " ".join((*synthesis["paragraphs"], synthesis["rule"]))

    assert synthesis["headline"] == "BUILD THE OPENING TO LAST."
    assert "Moon conjunct Saturn" in text
    assert "Jupiter trine Saturn" in text
    assert "Mars square Saturn" in text
    assert "more force" in text


def test_aries_translation_uses_event_houses_and_complete_social_copy():
    days = _week()
    summary = build_weekly_sign_translation("Aries", MONDAY, TZ, days)
    card = weekly_social_card_copy(summary, MONDAY)

    assert summary["houses"] == [1, 4, 5]
    assert "Moon conjunct Saturn" in summary["interpretation"]
    assert "Jupiter trine Saturn" in summary["interpretation"]
    assert "Mars square Saturn" in summary["interpretation"]
    assert "YOU · HOME · CREATIVE DIRECTION" in card
    assert "CHOOSE ONE DIRECTION. BUILD ITS SUPPORT." in card
    assert "BELONGS TO." not in card


def test_all_twelve_cards_use_complete_precompressed_commands():
    days = _week()
    stop_words = {"A", "AN", "THE", "TO", "YOU", "YOUR", "BEFORE", "WITH"}

    for sign in SIGNS:
        summary = build_weekly_sign_translation(sign, MONDAY, TZ, days)
        card = weekly_social_card_copy(summary, MONDAY)
        move = card.split("YOUR MOVE\n", 1)[1].split("\n", 1)[0].rstrip(".")

        assert summary["headline"].rstrip(".").upper() != move
        assert len(move.split()) <= 7
        assert move.split()[-1] not in stop_words
        assert card.endswith("LUNA CONVERGENCE")


def test_house_three_is_communication_not_travel():
    assert domain_key("communication, sales, learning and local movement") == "communication"
    aquarius = build_weekly_sign_translation("Aquarius", MONDAY, TZ, _week())
    assert aquarius["houses"][0] == 3
    assert aquarius["social_area"].startswith("MESSAGE")


def test_weekly_studio_uses_non_anchor_content_headings_and_no_word_chopper():
    source = Path("app.py").read_text(encoding="utf-8")

    assert '<div class="weekly-card-title" role="heading"' in source
    assert '<h2>{escape(item.headline)}</h2>' not in source
    assert 'words if len(words) <= 6 else words[:6]' not in source
    assert 'st.markdown("## 12 sign translations")' not in source
    assert 'st.markdown("## Monday-Sunday source cards")' not in source
