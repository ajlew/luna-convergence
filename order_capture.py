from __future__ import annotations

from calendar import month_name
from datetime import date
import hashlib
import json
import re
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REFERENCE_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")
QUESTION_MAX_CHARS = 80

MONTHLY_FOCUS_CHOICES = [
    "General overview",
    "Love and relationships",
    "Career and work",
    "Money and security",
    "Home and family",
    "Personal growth",
]

YEARLY_FOCUS_CHOICES = [
    "General year ahead",
    "Love and relationships",
    "Career or business",
    "Money and security",
    "Home or relocation",
    "Personal reinvention",
]

FOCUS_CODES = {
    "General overview": "GENERAL",
    "General year ahead": "GENERAL",
    "Love and relationships": "LOVE",
    "Career and work": "CAREER",
    "Career or business": "CAREER",
    "Money and security": "MONEY",
    "Home and family": "HOME",
    "Home or relocation": "HOME",
    "Personal growth": "GROWTH",
    "Personal reinvention": "REINVENTION",
}


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


def focus_code(label: str) -> str:
    return FOCUS_CODES.get(label, safe_reference_fragment(label)[:20])


def question_reference_fragment(value: str, max_length: int = 72) -> str:
    """Create a readable Stripe-safe question fragment.

    Customer questions are limited to 80 characters in the public form. The fragment
    keeps the words readable inside Stripe's client_reference_id. If truncation is
    required, a short digest is appended so the reference still identifies the exact
    submitted wording.
    """
    raw = value.strip()
    if not raw:
        return "NONE"
    cleaned = safe_reference_fragment(raw)
    if len(cleaned) <= max_length:
        return cleaned
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()
    keep = max(8, max_length - len(digest) - 1)
    return f"{cleaned[:keep].rstrip('-')}-{digest}"


def build_order_reference(
    product_code: str,
    sign: str,
    period_code: str,
    timezone_name: str,
    token: str,
    main_focus: str = "",
    personal_question: str = "",
    nearest_city: str = "",
) -> str:
    """Build a Stripe-safe reference containing fulfilment essentials.

    Backwards compatibility: when focus and question are omitted, the historical
    reference format is preserved. New orders include focus and a readable question
    fragment while staying within Stripe's 200-character limit.
    """
    parts = [
        "LC",
        safe_reference_fragment(product_code),
        safe_reference_fragment(sign),
        safe_reference_fragment(period_code),
        safe_reference_fragment(timezone_name),
    ]

    if nearest_city:
        parts.extend(["C", safe_reference_fragment(nearest_city)[:24]])

    if main_focus or personal_question:
        parts.extend(
            [
                "F",
                focus_code(main_focus or "General overview"),
                "Q",
                question_reference_fragment(personal_question),
            ]
        )

    parts.append(safe_reference_fragment(token))
    reference = "-".join(parts)
    if len(reference) <= 200:
        return reference

    if main_focus or personal_question:
        digest = hashlib.sha256(personal_question.encode("utf-8")).hexdigest()[:8].upper()
        if "Q" in parts:
            q_index = parts.index("Q")
            parts[q_index + 1] = digest
        reference = "-".join(parts)

    if len(reference) > 200 and "C" in parts:
        city_index = parts.index("C")
        parts[city_index + 1] = parts[city_index + 1][:10]
        reference = "-".join(parts)

    return reference[:200]


def parse_order_reference(reference: str) -> dict[str, str]:
    """Parse fulfilment essentials from a Luna order reference."""
    parts = reference.split("-")
    if len(parts) < 7 or parts[0] != "LC":
        raise ValueError("Not a Luna Convergence order reference")

    product_code = parts[1]
    if product_code == "MONTHLY":
        period_code = "-".join(parts[3:5])
        timezone_start = 5
    else:
        period_code = parts[3]
        timezone_start = 4

    markers = {
        marker: parts.index(marker)
        for marker in ("C", "F", "Q")
        if marker in parts
    }
    first_marker = min(markers.values(), default=len(parts) - 1)
    timezone_fragment = "-".join(parts[timezone_start:first_marker])

    city_fragment = ""
    if "C" in markers:
        city_index = markers["C"]
        city_end = min(
            [index for marker, index in markers.items() if marker != "C" and index > city_index]
            or [len(parts) - 1]
        )
        city_fragment = "-".join(parts[city_index + 1:city_end])

    focus_fragment = ""
    if "F" in markers:
        focus_index = markers["F"]
        focus_fragment = parts[focus_index + 1] if focus_index + 1 < len(parts) else ""

    question_fragment = ""
    if "Q" in markers:
        question_index = markers["Q"]
        question_fragment = "-".join(parts[question_index + 1:-1])

    return {
        "product_code": product_code,
        "sign": parts[2],
        "period_code": period_code,
        "timezone_fragment": timezone_fragment,
        "city_fragment": city_fragment,
        "focus_code": focus_fragment,
        "question_fragment": question_fragment,
        "token": parts[-1],
    }


def order_payload_json(order: dict) -> str:
    """Return a stable, downloadable manual-fulfilment record."""
    ordered = {
        "report_name": order.get("report_name", ""),
        "delivery_email": order.get("email", ""),
        "star_sign": order.get("sign", ""),
        "period": order.get("period", ""),
        "period_code": order.get("period_code", ""),
        "timezone": order.get("timezone", ""),
        "nearest_city": order.get("nearest_city", ""),
        "location_basis": order.get("location_basis", ""),
        "main_focus": order.get("main_focus", ""),
        "personal_question": order.get("personal_question", ""),
        "order_reference": order.get("reference", ""),
        "delivery_method": "Personalised PDF by email",
        "delivery_timeframe": "Within 24 hours after payment",
    }
    return json.dumps(ordered, indent=2, ensure_ascii=False)


def order_details_mailto(
    recipient: str,
    order: dict,
) -> str:
    subject = quote(f"Luna order details - {order.get('reference', '')}")
    body = quote(
        "\n".join(
            [
                f"Report: {order.get('report_name', '')}",
                f"Delivery email: {order.get('email', '')}",
                f"Star sign: {order.get('sign', '')}",
                f"Period: {order.get('period', '')}",
                f"Timezone: {order.get('timezone', '')}",
                f"Nearest city: {order.get('nearest_city', '') or 'Timezone estimate'}",
                f"Location basis: {order.get('location_basis', '') or 'Timezone estimate'}",
                f"Main focus: {order.get('main_focus', '')}",
                f"Personal question: {order.get('personal_question', '') or 'None supplied'}",
                f"Order reference: {order.get('reference', '')}",
                "",
                "The personalised PDF will be prepared manually and emailed within 24 hours after payment.",
            ]
        )
    )
    return f"mailto:{recipient}?subject={subject}&body={body}"


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
