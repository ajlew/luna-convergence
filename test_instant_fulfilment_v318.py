from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path

import stripe_checkout
from email_delivery import build_report_email_html
from fulfilment_service import _stripe_signature_ok
from monthly_report_pipeline import build_production_monthly_report


def test_exact_order_metadata_survives_checkout_payload(monkeypatch):
    captured = {}

    def fake_request(method, path, secret_key, *, data=None, params=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = list(data or [])
        return {"id": "cs_test_123", "url": "https://checkout.stripe.com/c/pay/test"}

    monkeypatch.setattr(stripe_checkout, "_request", fake_request)
    order = {
        "product_code": "MONTHLY",
        "report_name": "Monthly Strategic Report",
        "email": "buyer@example.com",
        "sign": "Cancer",
        "period": "August 2026",
        "period_code": "2026-08",
        "timezone": "Australia/Sydney",
        "nearest_city": "Sydney",
        "location_basis": "Customer city",
        "main_focus": "Love and relationships",
        "personal_question": "Should I stay or move on?",
        "reference": "LC-MONTHLY-CANCER-TEST",
    }
    session = stripe_checkout.create_checkout_session(
        "sk_test_dummy",
        price_id="price_123",
        order=order,
        public_site_url="https://luna-convergence.streamlit.app",
    )
    assert session["id"] == "cs_test_123"
    values = dict(captured["data"])
    assert values["metadata[sign]"] == "Cancer"
    assert values["metadata[personal_question]"] == "Should I stay or move on?"
    assert values["metadata[timezone]"] == "Australia/Sydney"
    assert values["success_url"].endswith("/payment-success?session_id={CHECKOUT_SESSION_ID}")
    assert values["client_reference_id"] == "LC-MONTHLY-CANCER-TEST"


def test_checkout_paid_gate_requires_complete_and_paid():
    assert stripe_checkout.checkout_is_paid({"status": "complete", "payment_status": "paid"})
    assert not stripe_checkout.checkout_is_paid({"status": "open", "payment_status": "paid"})
    assert not stripe_checkout.checkout_is_paid({"status": "complete", "payment_status": "unpaid"})


def test_email_contains_private_return_link():
    html = build_report_email_html(
        report_name="Monthly Strategic Report",
        sign="Cancer",
        period="August 2026",
        report_url="https://luna-convergence.streamlit.app/payment-success?session_id=cs_test_123",
        order_reference="LC-TEST",
    )
    assert "Your Luna report is ready" in html
    assert "payment-success?session_id=cs_test_123" in html
    assert "LC-TEST" in html


def test_webhook_signature_verification():
    secret = "whsec_testsecret"
    payload = json.dumps({"id": "evt_123"}, separators=(",", ":")).encode()
    timestamp = int(time.time())
    signed = f"{timestamp}.".encode() + payload
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={digest}"
    assert _stripe_signature_ok(payload, header, secret)
    assert not _stripe_signature_ok(payload + b"x", header, secret)


def test_monthly_pipeline_preserves_personal_question():
    narrative, result = build_production_monthly_report(
        sign="Cancer",
        year=2026,
        month=8,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
        main_focus="Love and relationships",
        personal_question="Should I stay or move on?",
    )
    assert narrative.personal_question == "Should I stay or move on?"
    assert narrative.main_focus == "Love and relationships"
    assert result["sign"] == "Cancer"


def test_public_app_has_no_manual_24_hour_checkout_copy():
    source = Path("app.py").read_text(encoding="utf-8")
    forbidden = [
        "Email order details to Luna",
        "Download order details",
        "within 24 hours",
        "Manual delivery during launch",
    ]
    for phrase in forbidden:
        assert phrase not in source
    assert "payment-success" in source
    assert "Instant delivery" in source
