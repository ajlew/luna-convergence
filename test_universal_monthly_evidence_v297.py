from __future__ import annotations

from calendar import monthrange
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
MONTHS = (7, 8, 9)


def _report(sign: str, month: int) -> dict:
    start = date(2026, month, 1)
    end = date(2026, month, monthrange(2026, month)[1])
    return period_report(
        sign,
        start,
        end,
        "Australia/Sydney",
        start.strftime("%B %Y"),
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
    reports: dict[tuple[str, int], dict] = {}
    narratives = {}
    customer_grams: dict[tuple[str, int], set[tuple[str, str, str]]] = {}

    for month in MONTHS:
        monthly_headlines: set[str] = set()
        monthly_pairs: set[tuple[int, int]] = set()
        august_questions: set[str] = set()

        for sign in SIGNS:
            result = _report(sign, month)
            narrative = build_monthly_narrative(result)
            html = build_monthly_experience_html(narrative, result, show_print=True)
            arc = result["monthly_arc"]
            formula = arc.get("evidence_formula") or {}
            profile = profile_from_dict(arc.get("story_profile"))

            assert formula.get("formula_version") == "2.9.7"
            assert profile is not None
            assert profile.source == "universal_house_scenario_formula"
            assert profile.expected_pair == (arc["primary_house"], arc["secondary_house"])
            assert narrative.hook_headline == profile.headline
            expected_hooks = (
                profile.act_hooks
                if narrative.relationship_test
                else (profile.act_hooks[0], profile.act_hooks[1], profile.act_hooks[3])
            )
            assert tuple(chapter.hook for chapter in narrative.chapters) == expected_hooks
            assert narrative.action_plan == profile.action_plan

            # Every active narrative role retains an evidence path and scenario.
            for item in arc.get("mapping_audit") or []:
                if item.get("role") == "relationship test" and not item.get("evidence"):
                    continue
                assert item.get("evidence"), (sign, month, item)
                assert item.get("scenario_key"), (sign, month, item)

            for beat in arc.get("beats") or []:
                if float(beat.get("score", 0.0)) <= 0:
                    continue
                assert beat.get("evidence"), (sign, month, beat.get("role"))
                assert beat.get("scenario_keys"), (sign, month, beat.get("role"))

            # One astronomical trigger gets one customer calendar card.
            fingerprints = [
                (item.date_label, item.evidence.casefold())
                for item in narrative.key_dates
            ]
            assert len(fingerprints) == len(set(fingerprints)), (sign, month, fingerprints)
            evidence_names = [item.evidence.casefold() for item in narrative.key_dates]
            assert len(evidence_names) == len(set(evidence_names)), (sign, month, evidence_names)

            # Existing Luna format remains; browser printing is removed in favour
            # of the server-generated searchable A4 PDF.
            assert "Print or save report" not in html
            assert "isolatedReportClone" not in html
            assert 'document.createElement("iframe")' not in html
            assert "Evidence-to-scenario trace" in html
            assert 'font-family:"Josefin Sans"' in html
            assert 'font-family:"Bodoni MT"' in html

            monthly_headlines.add(narrative.hook_headline)
            monthly_pairs.add((arc["primary_house"], arc["secondary_house"]))
            if month == 8 and narrative.relationship_test:
                august_questions.add(narrative.relationship_test[0])

            reports[(sign, month)] = result
            narratives[(sign, month)] = narrative
            customer_grams[(sign, month)] = _customer_trigrams(html)

        assert len(monthly_headlines) == 12, (month, monthly_headlines)
        assert len(monthly_pairs) == 12, (month, monthly_pairs)
        if month == 8:
            assert len(august_questions) == 12, august_questions

        # Universal architecture may share structure, but no report may become
        # a near-clone of another sign in the same month.
        for first, second in combinations(SIGNS, 2):
            a = customer_grams[(first, month)]
            b = customer_grams[(second, month)]
            similarity = len(a & b) / max(1, len(a | b))
            assert similarity < 0.65, (month, first, second, similarity)

    # A sign must change story as the sky changes; no fixed sign profile.
    for sign in SIGNS:
        headlines = {narratives[(sign, month)].hook_headline for month in MONTHS}
        pairs = {
            (
                reports[(sign, month)]["monthly_arc"]["primary_house"],
                reports[(sign, month)]["monthly_arc"]["secondary_house"],
            )
            for month in MONTHS
        }
        assert len(headlines) == len(MONTHS), (sign, headlines)
        assert len(pairs) == len(MONTHS), (sign, pairs)

    # The solar path is recorded but not hard-wired as the answer. September's
    # eclipse axis creates a different source/destination path for this batch.
    assert any(
        (
            reports[(sign, 9)]["monthly_arc"]["primary_house"],
            reports[(sign, 9)]["monthly_arc"]["secondary_house"],
        )
        != (
            reports[(sign, 9)]["monthly_arc"]["evidence_formula"].get("solar_source_house"),
            reports[(sign, 9)]["monthly_arc"]["evidence_formula"].get("solar_destination_house"),
        )
        for sign in SIGNS
    )

    # PDF output remains Luna's existing nine-page format and one-sign isolation.
    for sign in ("Aries", "Gemini", "Sagittarius"):
        pdf = build_monthly_homepage_pdf(
            reports[(sign, 8)],
            order_reference=f"LC-V297-{sign.upper()}-AUGUST-2026",
        )
        output = Path(f"_v297_{sign.lower()}_test.pdf")
        output.write_bytes(pdf)
        try:
            reader = PdfReader(str(output))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            normalised = " ".join(text.split())
            assert len(reader.pages) == 9
            assert f"{sign.upper()} / AUGUST 2026" in text
            for other in SIGNS:
                if other == sign:
                    continue
                assert f"{other.upper()} / AUGUST 2026" not in text
            assert narratives[(sign, 8)].hook_headline in normalised
            assert "From reading the future to writing it" in normalised
            for merged in (
                "checksthe", "upgradesthe", "detailsinto", "whatremainsin",
                "sparkbecomes", "whetherthe", "nexttellsthe",
            ):
                assert merged not in text.lower()
        finally:
            output.unlink(missing_ok=True)

    print("Universal Monthly Evidence Engine v2.9.7 tests passed: 36 reports and 3 PDFs.")


if __name__ == "__main__":
    main()
