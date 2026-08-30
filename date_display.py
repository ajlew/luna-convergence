from __future__ import annotations

from datetime import date, datetime


def _coerce_date(value: object) -> date:
    """Return a date from date/datetime/ISO-like values."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value or "").strip()
    if not text:
        raise ValueError("A date value is required")

    # Customer-facing data normally uses YYYY-MM-DD. Accept a full ISO
    # timestamp as a defensive fallback without changing its calendar date.
    if "T" in text:
        text = text.split("T", 1)[0]
    return date.fromisoformat(text)


def human_date(value: object) -> str:
    """Format a customer date as a day, full month name and selected year."""
    parsed = _coerce_date(value)
    return f"{parsed.day} {parsed.strftime('%B')} {parsed.year}"


def human_date_range(start: object, end: object) -> str:
    """Format a compact customer date range using day-month-year order."""
    first = _coerce_date(start)
    last = _coerce_date(end)

    # Customer-facing safety: never print a backwards range. The monthly QA
    # layer still flags inverted source windows so the underlying data is not
    # silently treated as correct.
    if first > last:
        first, last = last, first

    if first == last:
        return human_date(first)

    if first.year == last.year and first.month == last.month:
        return f"{first.day}-{last.day} {first.strftime('%B')} {first.year}"

    if first.year == last.year:
        return (
            f"{first.day} {first.strftime('%B')}-"
            f"{last.day} {last.strftime('%B')} {first.year}"
        )

    return f"{human_date(first)}-{human_date(last)}"
