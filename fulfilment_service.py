from __future__ import annotations

"""Tiny Stripe webhook WSGI service for Luna v3.18.

Deploy separately from Streamlit (for example with gunicorn). Its only job is
to receive Stripe's signed checkout completion event and send the customer the
private Luna report link immediately. No framework dependency is required.
"""

from hashlib import sha256
import hmac
import json
import os
import time
from typing import Callable

from email_delivery import send_report_email


def _secret(name: str, default: str = "") -> str:
    return str(os.environ.get(name, default) or default)


def _stripe_signature_ok(payload: bytes, signature_header: str, webhook_secret: str, tolerance: int = 300) -> bool:
    if not webhook_secret.startswith("whsec_"):
        return False
    parts: dict[str, list[str]] = {}
    for item in str(signature_header or "").split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts.setdefault(key.strip(), []).append(value.strip())
    try:
        timestamp = int((parts.get("t") or [""])[0])
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp) > tolerance:
        return False
    signed = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(webhook_secret.encode("utf-8"), signed, sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in parts.get("v1", []))


def _email_for_session(session: dict) -> str:
    details = session.get("customer_details") or {}
    return str(details.get("email") or session.get("customer_email") or "").strip()


def _send_for_session(session: dict) -> None:
    if str(session.get("payment_status") or "").lower() != "paid":
        return
    session_id = str(session.get("id") or "")
    metadata = dict(session.get("metadata") or {})
    email = _email_for_session(session)
    if not session_id.startswith("cs_") or not email:
        return
    site = _secret("PUBLIC_SITE_URL", "https://luna-convergence.streamlit.app").rstrip("/")
    report_url = f"{site}/payment-success?session_id={session_id}"
    send_report_email(
        to_email=email,
        report_name=str(metadata.get("report_name") or "Luna report"),
        sign=str(metadata.get("sign") or "Your sign"),
        period=str(metadata.get("period") or metadata.get("period_code") or ""),
        report_url=report_url,
        order_reference=str(metadata.get("order_reference") or session.get("client_reference_id") or ""),
        idempotency_key=f"luna-fulfil-{session_id}",
        resend_api_key=_secret("RESEND_API_KEY"),
        resend_from=_secret("RESEND_FROM"),
        smtp_user=_secret("SMTP_USER"),
        smtp_app_password=_secret("SMTP_APP_PASSWORD"),
        smtp_from=_secret("SMTP_FROM"),
    )


def _response(start_response: Callable, status: str, body: bytes, content_type: str = "text/plain"):
    start_response(status, [("Content-Type", content_type), ("Content-Length", str(len(body)))])
    return [body]


def application(environ, start_response):
    method = str(environ.get("REQUEST_METHOD") or "GET").upper()
    path = str(environ.get("PATH_INFO") or "/")

    if method == "GET" and path == "/health":
        return _response(start_response, "200 OK", b"ok")

    if method != "POST" or path != "/stripe/webhook":
        return _response(start_response, "404 Not Found", b"not found")

    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except (TypeError, ValueError):
        length = 0
    payload = environ["wsgi.input"].read(length) if length else b""
    signature = str(environ.get("HTTP_STRIPE_SIGNATURE") or "")
    if not _stripe_signature_ok(payload, signature, _secret("STRIPE_WEBHOOK_SECRET")):
        return _response(start_response, "400 Bad Request", b"invalid signature")

    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception:
        return _response(start_response, "400 Bad Request", b"invalid json")

    if str(event.get("type") or "") in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        session = ((event.get("data") or {}).get("object") or {})
        _send_for_session(session)

    return _response(start_response, "200 OK", b"ok")


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    port = int(os.environ.get("PORT", "8080"))
    with make_server("0.0.0.0", port, application) as server:
        server.serve_forever()
