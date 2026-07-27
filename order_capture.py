from __future__ import annotations

from calendar import month_name
from datetime import date
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REFERENCE_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")


def month_choices(
    today: date | None = None,
    count: int = 18,
) -> list[tuple[str, str]]:
    """Return customer-facing month labels and YYYY-MM values."""
    current = today or date.today()
    first = date(current.year, current.month, 1)
    choices: list[tuple[str, str]] = []

    for offset in range(count):
        absolute_month = first.month - 1 + offset
        year = first.year + absolute_month // 12
        month = absolute_month % 12 + 1
        choices.append(
            (
                f"{month_name[month]} {year}",
                f"{year:04d}-{month:02d}",
            )
        )
    return choices


def default_month_label(today: date | None = None) -> str:
    """Prefer next month once the current month is already advanced."""
    current = today or date.today()
    offset = 1 if current.day >= 20 else 0
    absolute_month = current.month - 1 + offset
    year = current.year + absolute_month // 12
    month = absolute_month % 12 + 1
    return f"{month_name[month]} {year}"


def year_choices(
    today: date | None = None,
    count: int = 3,
) -> list[int]:
    current = today or date.today()
    return [current.year + offset for offset in range(count)]


def default_year(today: date | None = None) -> int:
    """Prefer next calendar year from July onward."""
    current = today or date.today()
    return current.year + (1 if current.month >= 7 else 0)


def valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(value.strip()))


def safe_reference_fragment(value: str) -> str:
    cleaned = REFERENCE_PATTERN.sub("-", value.strip().upper())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-_")
    return cleaned or "NA"


def build_order_reference(
    product_code: str,
    sign: str,
    period_code: str,
    timezone_name: str,
    token: str,
) -> str:
    """Build a Stripe-safe reference containing fulfilment essentials."""
    parts = [
        "LC",
        safe_reference_fragment(product_code),
        safe_reference_fragment(sign),
        safe_reference_fragment(period_code),
        safe_reference_fragment(timezone_name),
        safe_reference_fragment(token),
    ]
    return "-".join(parts)[:200]


def build_stripe_checkout_url(
    payment_url: str,
    delivery_email: str,
    client_reference_id: str,
    campaign: str,
) -> str:
    """Attach Payment Link parameters without changing the base link."""
    if not payment_url:
        return ""

    parts = urlsplit(payment_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(
        {
            "prefilled_email": delivery_email.strip(),
            "client_reference_id": client_reference_id,
            "utm_source": "luna_convergence",
            "utm_medium": "website",
            "utm_campaign": safe_reference_fragment(campaign).lower(),
        }
    )
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )
