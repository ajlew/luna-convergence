from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from pypdf import PdfReader

from astrology_engine import SIGNS
from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import (
    _daily_print_document_html,
    build_daily_narrative,
)
from daily_report_pdf import build_daily_report_pdf, daily_report_filename
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from report_pdf import build_report_pdf, report_filename
from synthesis import period_report


def daily_narrative(sign: str, day: date):
    reading = free_daily_reading(sign, day, "Australia/Sydney")
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=day,
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=[],
    )


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
    # Every 2026 Daily sign/date must render without an editorial-hook exception.
    start = date(2026, 1, 1)
    for offset in range(365):
        day = start + timedelta(days=offset)
        for sign in SIGNS:
            narrative = daily_narrative(sign, day)
            assert narrative.hook_headline
            assert len(narrative.reflection_questions) == 1

    # Capricorn's former false-positive hook is now valid and customer friendly.
    capricorn = daily_narrative("Capricorn", date(2026, 8, 3))
    assert capricorn.hook_headline == "The family meeting has entered the chat"
    assert "both influences concentrate" in capricorn.why_today_points[2].lower()
    assert "connects home" not in capricorn.why_today_points[2].lower()
    assert "concentrates both planets in house 4" in capricorn.daily_theme.lower()

    # Same-house conjunction language must be correct for the entire sign rotation.
    for sign in SIGNS:
        narrative = daily_narrative(sign, date(2026, 8, 3))
        assert " with " not in narrative.why_today_points[2].split("concentrate", 1)[-1].lower()
        assert "both influences concentrate" in narrative.why_today_points[2].lower()
        assert "connects house" not in narrative.daily_theme.lower()

    # Daily browser print document is isolated A4 and opens full evidence by construction.
    full_daily_html = _daily_print_document_html(capricorn, None, include_evidence=True)
    assert "@page { size:A4 portrait" in full_daily_html
    assert "Full technical evidence" in full_daily_html
    assert "The 12-house reference matrix" in full_daily_html
    assert "2026-08-03_Capricorn_Daily" in full_daily_html

    # Daily PDFs are searchable, canonical and isolated.
    for include_evidence in (False, True):
        pdf = build_daily_report_pdf(capricorn, None, include_evidence=include_evidence)
        reader = PdfReader(BytesIO(pdf))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "The family meeting has entered the chat" in text
        assert "Capricorn" in text
        assert len(text) > 500
    assert daily_report_filename(capricorn) == "2026-08-03_Capricorn_Daily.pdf"

    # Monthly reports expose traceability and print in one isolated A4 window.
    for sign in SIGNS:
        result = monthly_result(sign)
        narrative = build_monthly_narrative(result)
        html = build_monthly_experience_html(narrative, result, show_print=True, preview=False)
        assert "Evidence-to-scenario trace" in html
        assert "isolatedReportClone" in html
        assert "destroyLegacyPrintArtifacts" in html
        assert 'document.createElement("iframe")' in html
        assert "document.body.appendChild(printPortal)" not in html
        assert "A4 portrait" in html
        assert 'querySelectorAll("details")' in html
        assert 'detail.setAttribute("open", "")' in html
        assert len(result["monthly_arc"].get("mapping_audit") or []) >= 3

    # Searchable Monthly PDF uses canonical name and contains one sign only.
    aries_result = monthly_result("Aries")
    monthly_pdf = build_report_pdf(aries_result)
    reader = PdfReader(BytesIO(monthly_pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert len(text) > 4000
    assert "ARIES / AUGUST 2026" in text
    for other in SIGNS:
        if other != "Aries":
            assert f"{other.upper()} / AUGUST 2026" not in text
    assert report_filename(aries_result) == "2026-08_Aries_Monthly.pdf"

    print("v2.9.7.1 reliability and evidence-traceability checks passed.")


if __name__ == "__main__":
    main()
