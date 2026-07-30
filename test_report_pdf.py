from datetime import date

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
    )
    pdf = build_report_pdf(
        result,
        main_focus="Love and relationships",
        personal_question="What should I understand about love and work this month?",
        order_reference="LC-MONTHLY-SAGITTARIUS-2026-08-AUSTRALIA-SYDNEY-F-LOVE-Q-TEST-ABC123",
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 15000
    print("Print-ready PDF generation test passed.")
    print(len(pdf))


if __name__ == "__main__":
    main()
