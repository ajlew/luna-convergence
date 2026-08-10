from __future__ import annotations

"""Stripe Checkout helpers for Luna v3.18 instant fulfilment.

The public app creates a fresh Checkout Session for each prepared order. The
full fulfilment inputs are stored in Stripe Checkout Session metadata so the
success page and webhook can regenerate the exact customer report without a
separate customer database.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

STRIPE_API = "https://api.stripe.com/v1"
DEFAULT_TIMEOUT = 20


class StripeCheckoutError(RuntimeError):
    pass


def _base_payment_link(url: str) -> str:
    parts = urlsplit(str(url or ""))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _request(
    method: str,
    path: str,
    secret_key: str,
    *,
    data: dict[str, Any] | list[tuple[str, Any]] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not str(secret_key or "").startswith("sk_"):
        raise StripeCheckoutError("Stripe secret key is not configured.")

    response = requests.request(
        method,
        f"{STRIPE_API}{path}",
        auth=(secret_key, ""),
        data=data,
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )
    try:
        payload = response.json()
    except Exception:
        payload = {"error": {"message": response.text or "Stripe returned a non-JSON response."}}

    if response.status_code >= 400:
        message = str((payload.get("error") or {}).get("message") or "Stripe request failed.")
        raise StripeCheckoutError(message)
    return payload


def resolve_price_id(
    secret_key: str,
    *,
    explicit_price_id: str = "",
    payment_link_url: str = "",
) -> str:
    """Return a Price ID, optionally discovering it from an existing Payment Link.

    This preserves the owner's existing Stripe Payment Link setup: once
    STRIPE_SECRET_KEY is added, Luna can discover the first price attached to
    STRIPE_MONTHLY_URL / STRIPE_YEARLY_URL rather than forcing the owner to
    manually find and copy price IDs.
    """
    explicit = str(explicit_price_id or "").strip()
    if explicit.startswith("price_"):
        return explicit

    target = _base_payment_link(payment_link_url)
    if not target:
        return ""

    starting_after = ""
    for _ in range(5):
        params: dict[str, Any] = {"active": "true", "limit": 100}
        if starting_after:
            params["starting_after"] = starting_after
        page = _request("GET", "/payment_links", secret_key, params=params)
        rows = list(page.get("data") or [])
        for link in rows:
            if _base_payment_link(str(link.get("url") or "")) != target:
                continue
            link_id = str(link.get("id") or "")
            if not link_id:
                continue
            line_items = _request(
                "GET",
                f"/payment_links/{link_id}/line_items",
                secret_key,
                params={"limit": 1},
            )
            data = list(line_items.get("data") or [])
            if data:
                price = data[0].get("price") or {}
                price_id = str(price.get("id") or "")
                if price_id.startswith("price_"):
                    return price_id
        if not page.get("has_more") or not rows:
            break
        starting_after = str(rows[-1].get("id") or "")
    return ""


def order_metadata(order: dict[str, Any]) -> dict[str, str]:
    """Return exact fulfilment inputs safe for Stripe Session metadata."""
    fields = {
        "product_code": order.get("product_code", ""),
        "report_name": order.get("report_name", ""),
        "sign": order.get("sign", ""),
        "period": order.get("period", ""),
        "period_code": order.get("period_code", ""),
        "timezone": order.get("timezone", ""),
        "nearest_city": order.get("nearest_city", ""),
        "location_basis": order.get("location_basis", ""),
        "main_focus": order.get("main_focus", ""),
        "personal_question": order.get("personal_question", ""),
        "order_reference": order.get("reference", ""),
        "fulfilment_version": "3.18",
    }
    # Stripe metadata values are strings. Keep each comfortably below the
    # documented per-value limit; the public question is already capped at 80.
    return {key: str(value or "")[:450] for key, value in fields.items()}


def create_checkout_session(
    secret_key: str,
    *,
    price_id: str,
    order: dict[str, Any],
    public_site_url: str,
    cancel_path: str = "/reports",
) -> dict[str, Any]:
    if not str(price_id or "").startswith("price_"):
        raise StripeCheckoutError("Stripe price is not configured for this report.")

    site = str(public_site_url or "").rstrip("/")
    if not site.startswith("https://"):
        raise StripeCheckoutError("PUBLIC_SITE_URL must be an HTTPS URL.")

    metadata = order_metadata(order)
    data: list[tuple[str, Any]] = [
        ("mode", "payment"),
        ("line_items[0][price]", price_id),
        ("line_items[0][quantity]", 1),
        ("customer_email", str(order.get("email") or "").strip()),
        ("client_reference_id", str(order.get("reference") or "")[:200]),
        ("success_url", f"{site}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"),
        ("cancel_url", f"{site}{cancel_path}?checkout=cancelled"),
        ("payment_intent_data[description]", str(order.get("report_name") or "Luna Convergence report")[:255]),
    ]
    for key, value in metadata.items():
        data.append((f"metadata[{key}]", value))
        data.append((f"payment_intent_data[metadata][{key}]", value))

    return _request("POST", "/checkout/sessions", secret_key, data=data)


def retrieve_checkout_session(secret_key: str, session_id: str) -> dict[str, Any]:
    session_id = str(session_id or "").strip()
    if not session_id.startswith("cs_"):
        raise StripeCheckoutError("Invalid Checkout Session ID.")
    return _request("GET", f"/checkout/sessions/{session_id}", secret_key)


def checkout_is_paid(session: dict[str, Any]) -> bool:
    return (
        str(session.get("status") or "").lower() == "complete"
        and str(session.get("payment_status") or "").lower() == "paid"
    )


def checkout_email(session: dict[str, Any]) -> str:
    customer_details = session.get("customer_details") or {}
    return str(customer_details.get("email") or session.get("customer_email") or "").strip()


def checkout_metadata(session: dict[str, Any]) -> dict[str, str]:
    return {str(k): str(v or "") for k, v in dict(session.get("metadata") or {}).items()}


def checkout_amount(session: dict[str, Any]) -> tuple[float, str]:
    amount = int(session.get("amount_total") or 0) / 100.0
    currency = str(session.get("currency") or "aud").upper()
    return amount, currency
