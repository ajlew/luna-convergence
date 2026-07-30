from datetime import date
from urllib.parse import parse_qs, urlsplit

from order_capture import (
    QUESTION_MAX_CHARS,
    build_order_reference,
    build_stripe_checkout_url,
    order_payload_json,
    parse_order_reference,
)


def main() -> None:
    question = "What should I know about changing careers this August?"
    assert len(question) <= QUESTION_MAX_CHARS
    reference = build_order_reference(
        "MONTHLY",
        "Sagittarius",
        "2026-08",
        "Australia/Sydney",
        "A1B2C3D4",
        main_focus="Career and work",
        personal_question=question,
    )
    assert len(reference) <= 200
    assert "F-CAREER" in reference
    assert "CHANGING-CAREERS" in reference

    parsed = parse_order_reference(reference)
    assert parsed["product_code"] == "MONTHLY"
    assert parsed["sign"] == "SAGITTARIUS"
    assert parsed["period_code"] == "2026-08"
    assert parsed["focus_code"] == "CAREER"
    assert "CHANGING-CAREERS" in parsed["question_fragment"]
    assert parsed["token"] == "A1B2C3D4"

    checkout = build_stripe_checkout_url(
        "https://buy.stripe.com/test_example",
        "customer@example.com",
        reference,
        "monthly-2026-08-sagittarius",
    )
    query = parse_qs(urlsplit(checkout).query)
    assert query["client_reference_id"] == [reference]
    assert query["prefilled_email"] == ["customer@example.com"]

    yearly_reference = build_order_reference(
        "YEAR",
        "Pisces",
        "2027",
        "Europe/London",
        "Y1Y2Y3Y4",
        main_focus="Personal reinvention",
        personal_question="Should I relocate and change direction?",
    )
    yearly_parsed = parse_order_reference(yearly_reference)
    assert yearly_parsed["period_code"] == "2027"
    assert yearly_parsed["timezone_fragment"] == "EUROPE-LONDON"
    assert yearly_parsed["focus_code"] == "REINVENTION"

    payload = order_payload_json({
        "report_name": "Monthly Strategic Report",
        "email": "customer@example.com",
        "sign": "Sagittarius",
        "period": "August 2026",
        "period_code": "2026-08",
        "timezone": "Australia/Sydney",
        "main_focus": "Career and work",
        "personal_question": question,
        "reference": reference,
    })
    assert question in payload
    assert "Within 24 hours" in payload

    print("Paid-order handoff tests passed.")
    print(reference)


if __name__ == "__main__":
    main()
