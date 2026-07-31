from datetime import date
from io import BytesIO

from pypdf import PdfReader

from report_pdf import build_report_pdf
from synthesis import period_report


ORDER_REFERENCE = (
    "LC-MONTHLY-SAGITTARIUS-2026-08-AUSTRALIA-SYDNEY-"
    "F-LOVE-Q-NONE-AD0B4520"
)


def main() -> None:
    result = period_report(
        "Sagittarius",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=9,
    )
    pdf = build_report_pdf(
        result,
        main_focus="Love and relationships",
        personal_question="No optional question supplied",
        order_reference=ORDER_REFERENCE,
    )

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 10_000

    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) >= 8
    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)

    assert "Your love life wants a" in page_texts[0]
    assert "passport - and a plan" in page_texts[0]
    assert "Love wants a wider horizon" in page_texts[0]
    assert ORDER_REFERENCE not in page_texts[0]
    assert "Your month at a glance" in full_text
    assert "The month in three chapters" in full_text
    assert "Why this month feels different" in full_text
    assert "Monthly Sky Snapshot" in full_text
    assert "Technical appendix" in full_text
    assert ORDER_REFERENCE in full_text
    assert "No optional question supplied" not in full_text

    print(f"Monthly customer PDF tests passed ({len(reader.pages)} pages).")


if __name__ == "__main__":
    main()
