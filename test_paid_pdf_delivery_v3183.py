from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path

import email_delivery


def test_email_html_says_pdf_is_attached_when_present():
    html = email_delivery.build_report_email_html(
        report_name="Monthly Strategic Report",
        sign="Cancer",
        period="August 2026",
        report_url="https://example.com/payment-success?session_id=cs_test_123",
        order_reference="LC-TEST",
        pdf_attached=True,
    )
    assert "personalised PDF is attached" in html


def test_gmail_message_contains_pdf_attachment(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def login(self, username, password):
            captured["login"] = (username, password)
        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(email_delivery.smtplib, "SMTP_SSL", FakeSMTP)
    result = email_delivery.send_report_email(
        to_email="buyer@example.com",
        report_name="Monthly Strategic Report",
        sign="Cancer",
        period="August 2026",
        report_url="https://example.com/payment-success?session_id=cs_test_123",
        order_reference="LC-TEST",
        idempotency_key="x",
        smtp_user="luna@example.com",
        smtp_app_password="abcdefghijklmnop",
        smtp_from="luna@example.com",
        attachment_bytes=b"%PDF-1.4\nTEST",
        attachment_filename="luna-test.pdf",
    )
    assert result.sent
    message = captured["message"]
    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "luna-test.pdf"
    assert attachments[0].get_content_type() == "application/pdf"


def test_paid_success_page_has_top_pdf_and_email_attachment_flow():
    source = Path("app.py").read_text(encoding="utf-8")
    assert '"Download your personalised PDF"' in source
    assert "attachment_bytes=pdf_bytes" in source
    assert "Your personalised PDF has been emailed" in source
    assert "A private return link has been emailed" not in source
