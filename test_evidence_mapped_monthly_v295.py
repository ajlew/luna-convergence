from __future__ import annotations

from datetime import date
from itertools import combinations
from pathlib import Path
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from monthly_report_pdf_home_v3 import build_monthly_homepage_pdf
from monthly_story_profiles import profile_from_dict
from synthesis import period_report


SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _report(sign: str) -> dict:
    return period_report(
        sign,
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General overview",
    )


def _customer_trigrams(html: str) -> set[tuple[str, str, str]]:
    text = " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())
    text = text.split("Why Luna sees this", 1)[0].lower()
    words = re.findall(r"[a-z']+", text)
    return set(zip(words, words[1:], words[2:]))


def main() -> None:
    headlines: set[str] = set()
    relationship_questions: set[str] = set()
    action_plans: set[tuple[str, ...]] = set()
    chapter_hooks: set[str] = set()
    customer_grams: dict[str, set[tuple[str, str, str]]] = {}

    for sign in SIGNS:
        result = _report(sign)
        arc = result["monthly_arc"]
        narrative = build_monthly_narrative(result)
        html = build_monthly_experience_html(narrative, result, show_print=True)

        profile = profile_from_dict(arc.get("story_profile"))
        assert profile is not None
        assert (arc["primary_house"], arc["secondary_house"]) == profile.expected_pair
        assert narrative.hook_headline == profile.headline
        assert tuple(chapter.hook for chapter in narrative.chapters) == profile.act_hooks
        assert narrative.action_plan == profile.action_plan
        assert narrative.romance_active == profile.romance_active
        assert narrative.romance_quiet == profile.romance_quiet

        headlines.add(narrative.hook_headline)
        relationship_questions.add(narrative.relationship_test[0])
        action_plans.add(narrative.action_plan)
        chapter_hooks.update(chapter.hook for chapter in narrative.chapters)
        customer_grams[sign] = _customer_trigrams(html)

        # Every actual beat must retain its evidence and scenario mapping.
        for beat in arc["beats"]:
            if float(beat.get("score", 0.0)) <= 0:
                continue
            assert beat.get("evidence"), (sign, beat.get("role"))
            assert beat.get("scenario_keys"), (sign, beat.get("role"))

        # One trigger gets one visible calendar card.
        fingerprints = [
            (item.date_label, item.evidence.casefold())
            for item in narrative.key_dates
        ]
        assert len(fingerprints) == len(set(fingerprints)), (sign, fingerprints)
        evidence_names = [item.evidence.casefold() for item in narrative.key_dates]
        assert len(evidence_names) == len(set(evidence_names)), (sign, evidence_names)

        # Browser print controls are removed; the server-generated searchable
        # A4 PDF is the only customer output path.
        assert "Print or save report" not in html
        assert "isolatedReportClone" not in html
        assert 'document.createElement("iframe")' not in html
        assert "Evidence-to-scenario trace" in html
        assert 'font-family:"Josefin Sans"' in html
        assert 'font-family:"Bodoni MT"' in html

    assert len(headlines) == 12
    assert len(relationship_questions) == 12
    assert len(action_plans) == 12
    assert len(chapter_hooks) >= 30

    # Cross-sign copy should no longer resemble one repeated report.
    for first, second in combinations(SIGNS, 2):
        a = customer_grams[first]
        b = customer_grams[second]
        similarity = len(a & b) / max(1, len(a | b))
        assert similarity < 0.65, (first, second, similarity)

    # PDF isolation: one sign, one document, one nine-page report.
    aries_pdf = build_monthly_homepage_pdf(_report("Aries"), order_reference="LC-V297-ARIES")
    output = Path("_v297_aries_test.pdf")
    output.write_bytes(aries_pdf)
    try:
        reader = PdfReader(str(output))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert len(reader.pages) == 9
        assert "ARIES / AUGUST 2026" in text
        assert "SAGITTARIUS / AUGUST 2026" not in text
        normalised = " ".join(text.split())
        assert "The spark becomes real when the week can carry it" in normalised
        assert "Sun enters Virgo" in normalised
        assert "From reading the future to writing it" in normalised
        assert "primary story drivers" in normalised.casefold()
        for merged in ("checksthe", "upgradesthe", "detailsinto", "whatremainsin", "sparkbecomes"):
            assert merged not in text.lower()
    finally:
        output.unlink(missing_ok=True)

    print("Universal Monthly Evidence Engine v2.9.7 compatibility tests passed for all 12 signs.")


if __name__ == "__main__":
    main()
