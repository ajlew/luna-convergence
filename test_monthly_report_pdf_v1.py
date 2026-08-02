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
    assert len(reader.pages) == 9
    page_texts = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(page_texts)
    compact = "".join(full_text.lower().split())
    first_compact = "".join(page_texts[0].lower().split())

    assert "apossibilitybecomesrealthroughthechoicesthatgiveitshape" in first_compact
    assert ORDER_REFERENCE not in page_texts[0]
    assert "augustwantsmorethanaspark" in compact
    assert "themonthmovesinfouracts" in compact
    assert "whythismonthfeelsdifferent" in compact
    assert "technicalappendix" in compact
    assert ORDER_REFERENCE.lower().replace("-", "") in compact.replace("-", "")
    assert "nooptionalquestionsupplied" not in compact

    print(f"Monthly customer PDF tests passed ({len(reader.pages)} pages).")


if __name__ == "__main__":
    main()
