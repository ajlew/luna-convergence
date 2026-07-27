from datetime import date
from urllib.parse import parse_qs, urlsplit

from order_capture import (
    build_order_reference,
    build_stripe_checkout_url,
    default_month_label,
    default_year,
    month_choices,
    valid_email,
    year_choices,
)


def main() -> None:
    today = date(2026, 7, 27)

    assert month_choices(today, count=4) == [
        ("July 2026", "2026-07"),
        ("August 2026", "2026-08"),
        ("September 2026", "2026-09"),
        ("October 2026", "2026-10"),
    ]
    assert default_month_label(today) == "August 2026"
    assert year_choices(today) == [2026, 2027, 2028]
    assert default_year(today) == 2027

    assert valid_email("customer@example.com")
    assert not valid_email("not-an-email")

    reference = build_order_reference(
        "MONTHLY",
        "Sagittarius",
        "2026-08",
        "Australia/Sydney",
        "A1B2C3D4",
    )
    assert reference == (
        "LC-MONTHLY-SAGITTARIUS-2026-08-"
        "AUSTRALIA-SYDNEY-A1B2C3D4"
    )

    checkout = build_stripe_checkout_url(
        "https://buy.stripe.com/test_example?locale=en",
        "customer+test@example.com",
        reference,
        "monthly-2026-08-sagittarius",
    )
    query = parse_qs(urlsplit(checkout).query)
    assert query["locale"] == ["en"]
    assert query["prefilled_email"] == ["customer+test@example.com"]
    assert query["client_reference_id"] == [reference]
    assert query["utm_source"] == ["luna_convergence"]

    print("Order-capture tests passed.")
    print(reference)
    print(checkout)


if __name__ == "__main__":
    main()
