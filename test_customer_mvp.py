from datetime import date

from customer_experience import free_daily_reading, prepared_order_email


def main() -> None:
    reading = free_daily_reading(
        "Sagittarius",
        date(2026, 7, 26),
        "Australia/Sydney",
    )
    assert reading.sign == "Sagittarius"
    assert reading.sun_house == 9
    assert "House 9 governs" in reading.conclusion
    assert "House reference matrix" not in reading.house_matrix
    assert "| 9 | Leo |" in reading.house_matrix
    assert len(reading.aspects) == 3

    mailto = prepared_order_email(
        "owner@example.com",
        "Monthly Strategic Report",
        "Customer",
        "customer@example.com",
        "Sagittarius",
        "August 2026",
        "Australia/Sydney",
    )
    assert mailto.startswith("mailto:owner@example.com")
    assert "Monthly%20Strategic%20Report" in mailto

    print("Customer MVP tests passed.")
    print(reading.conclusion)


if __name__ == "__main__":
    main()
