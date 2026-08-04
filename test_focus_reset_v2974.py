from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from customer_experience import HOUSE_VOICE, free_daily_reading
from daily_narrative_v3 import _daily_print_document_html, build_daily_narrative
from daily_report_pdf import build_daily_report_pdf
from luna_focus_reset import (
    FOCUS_RESET_ASSET,
    FOCUS_RESET_CUE,
    FOCUS_RESET_LABEL,
    FOCUS_RESET_METHOD,
    focus_reset_web_html,
)
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from monthly_report_pdf_home_v3 import build_monthly_homepage_html, build_monthly_homepage_pdf
from monthly_report_pdf_v2 import build_monthly_editorial_pdf
from synthesis import period_report


def _pdf_text(pdf: bytes) -> str:
    reader = PdfReader(BytesIO(pdf))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main() -> None:
    assert FOCUS_RESET_ASSET.exists()
    assert FOCUS_RESET_ASSET.stat().st_size > 20_000
    assert Path(FOCUS_RESET_ASSET).suffix.lower() == ".png"

    card = focus_reset_web_html()
    assert FOCUS_RESET_LABEL in card
    assert FOCUS_RESET_METHOD in card
    assert FOCUS_RESET_CUE in card
    assert "data:image/png;base64," in card
    assert "Inhale" not in card and "4 counts" not in card

    reading = free_daily_reading("Capricorn", date(2026, 8, 3), "Australia/Sydney")
    daily = build_daily_narrative(
        reading,
        sign="Capricorn",
        reading_date=date(2026, 8, 3),
        timezone_name="Australia/Sydney",
        house_voice=HOUSE_VOICE,
        previous_texts=[],
    )
    daily_html = _daily_print_document_html(daily, None, include_evidence=False)
    assert FOCUS_RESET_METHOD in daily_html
    assert FOCUS_RESET_CUE in daily_html
    assert "data:image/png;base64," in daily_html

    daily_pdf = build_daily_report_pdf(daily, None, include_evidence=False)
    daily_text = _pdf_text(daily_pdf)
    assert FOCUS_RESET_METHOD in daily_text
    assert FOCUS_RESET_CUE in daily_text
    assert "4 counts" not in daily_text

    result = period_report(
        "Aries",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=9,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    narrative = build_monthly_narrative(result)
    monthly_web = build_monthly_experience_html(narrative, result, show_print=True, preview=False)
    assert monthly_web.count(FOCUS_RESET_METHOD) == 1
    assert FOCUS_RESET_CUE in monthly_web
    assert "data:image/png;base64," in monthly_web

    homepage_html = build_monthly_homepage_html(result)
    assert FOCUS_RESET_METHOD in homepage_html
    assert FOCUS_RESET_CUE in homepage_html
    assert "focus-reset-inline" in homepage_html

    monthly_pdf = build_monthly_homepage_pdf(result)
    monthly_text = _pdf_text(monthly_pdf)
    assert FOCUS_RESET_METHOD in monthly_text
    assert FOCUS_RESET_CUE in monthly_text
    assert "4 counts" not in monthly_text

    fallback_pdf = build_monthly_editorial_pdf(result)
    fallback_text = _pdf_text(fallback_pdf)
    assert FOCUS_RESET_METHOD in fallback_text
    assert FOCUS_RESET_CUE in fallback_text

    print("v2.9.7.4 Luna Signature Focus Reset checks passed.")


if __name__ == "__main__":
    main()
