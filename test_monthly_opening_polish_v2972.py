from __future__ import annotations

from datetime import date
from io import BytesIO

from pypdf import PdfReader

from astrology_engine import SIGNS
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from monthly_report_pdf_v2 import build_monthly_editorial_pdf
from synthesis import period_report


def monthly_result(sign: str) -> dict:
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


def main() -> None:
    for sign in SIGNS:
        result = monthly_result(sign)
        narrative = build_monthly_narrative(result)
        html = build_monthly_experience_html(
            narrative,
            result,
            show_print=True,
            preview=False,
        )

        assert narrative.central_storyline.startswith("The month opens through ")
        assert "The first signal arrives through" not in narrative.central_storyline
        assert "The month’s larger movement runs from" not in narrative.central_storyline
        assert len(narrative.action_plan) == 3

        assert "font-size:clamp(1.65rem,3.1vw,2.75rem)" in html
        assert "text-align:justify" in html
        assert "text-align:left" in html
        assert "break-inside:avoid" in html
        assert (
            "Momentum builds first. Meaning sharpens next. By late month, "
            "the strongest possibility has found a workable form."
        ) in html

    aries = build_monthly_narrative(monthly_result("Aries"))
    assert aries.central_storyline == (
        "The month opens through a creative, romantic or entrepreneurial opening. "
        "As it develops, attention shifts toward the rhythm that could help it grow in real life."
    )
    assert aries.action_plan == (
        "Name the spark worth developing.",
        "Give the strongest spark one clear next stage.",
        "Create the rhythm that can carry the result beyond the month.",
    )
    assert aries.at_glance == (
        "The opening gathers momentum; the middle reveals the spark with enough response and substance to develop.",
        "Late in the month, a workload, routine or wellbeing adjustment gives the strongest option a clearer, workable form.",
    )

    pdf = build_monthly_editorial_pdf(monthly_result("Aries"))
    reader = PdfReader(BytesIO(pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert len(reader.pages) == 9
    assert "The month opens through a creative, romantic or entrepreneurial opening" in text
    assert "The first signal arrives through" not in text
    assert "Name the spark worth developing" in text
    assert "Give the strongest spark one clear next stage" in text
    assert "Create the rhythm that can carry the result beyond the month" in text

    print("v2.9.7.2 Monthly opening typography and copy checks passed.")


if __name__ == "__main__":
    main()
