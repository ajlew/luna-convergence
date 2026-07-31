from datetime import date
from io import BytesIO

from pypdf import PdfReader

from report_pdf import build_report_pdf
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
    pdf = build_report_pdf(
        result,
        main_focus="General overview",
        order_reference="LC-EDITORIAL-V2-TEST",
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 20_000

    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) == 9
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    compact = "".join(text.lower().split())

    required_compact = (
        "yoursparkwantsapassport",
        "romance&creativityxtravel&learning",
        "augustwantsmorethanaspark",
        "themonthmovesinthreeacts",
        "love,workandmoney",
        "makeoneopeningreal",
        "themonthbeneaththemonth",
        "whythismonthfeelsdifferent",
        "technicalappendix",
        "lc-editorial-v2-test",
    )
    for phrase in required_compact:
        assert phrase in compact, phrase

    print(f"Monthly Editorial PDF compatibility tests passed ({len(reader.pages)} pages).")


if __name__ == "__main__":
    main()
