from __future__ import annotations

"""Immediate Luna report email delivery.

Supports either Resend or Gmail/SMTP. Resend is preferred when configured;
Gmail App Password SMTP is a practical beta fallback for lunaconvergence@gmail.com.
"""

from dataclasses import dataclass
from email.message import EmailMessage
from html import escape
import smtplib
import ssl
from typing import Any

import requests


@dataclass(frozen=True)
class EmailResult:
    sent: bool
    provider: str
    message_id: str = ""
    error: str = ""


def build_report_email_html(
    *,
    report_name: str,
    sign: str,
    period: str,
    report_url: str,
    order_reference: str,
) -> str:
    return f"""
<!doctype html>
<html>
<body style="font-family:Arial,sans-serif;color:#151515;line-height:1.55;max-width:640px;margin:auto;padding:24px;">
  <div style="font-size:12px;letter-spacing:.16em;text-transform:uppercase;">Luna Convergence</div>
  <h1 style="font-size:28px;margin:18px 0 8px;">Your Luna report is ready.</h1>
  <p><strong>{escape(sign)}</strong> · {escape(period)}</p>
  <p>Your payment has been confirmed. Your complete {escape(report_name.lower())} is available now.</p>
  <p style="margin:28px 0;">
    <a href="{escape(report_url, quote=True)}" style="background:#050505;color:white;text-decoration:none;padding:14px 20px;display:inline-block;">
      Read your report now
    </a>
  </p>
  <p>The private report page also contains the PDF download when available.</p>
  <p style="font-size:12px;color:#696963;">Order reference: {escape(order_reference)}</p>
  <p style="font-size:12px;color:#696963;">Keep this email so you can return to your report. Do not share the private report link.</p>
</body>
</html>
""".strip()


def send_report_email(
    *,
    to_email: str,
    report_name: str,
    sign: str,
    period: str,
    report_url: str,
    order_reference: str,
    idempotency_key: str,
    resend_api_key: str = "",
    resend_from: str = "",
    smtp_user: str = "",
    smtp_app_password: str = "",
    smtp_from: str = "",
) -> EmailResult:
    recipient = str(to_email or "").strip()
    if not recipient or "@" not in recipient:
        return EmailResult(False, "none", error="No customer email was available.")

    subject = f"Your {sign} Luna report is ready"
    html = build_report_email_html(
        report_name=report_name,
        sign=sign,
        period=period,
        report_url=report_url,
        order_reference=order_reference,
    )

    resend_key = str(resend_api_key or "").strip()
    resend_sender = str(resend_from or "").strip()
    if resend_key and resend_sender:
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": str(idempotency_key or order_reference)[:256],
                },
                json={
                    "from": resend_sender,
                    "to": [recipient],
                    "subject": subject,
                    "html": html,
                },
                timeout=20,
            )
            data: dict[str, Any] = {}
            try:
                data = response.json()
            except Exception:
                pass
            if response.ok:
                return EmailResult(True, "resend", message_id=str(data.get("id") or ""))
            return EmailResult(False, "resend", error=str(data.get("message") or response.text)[:500])
        except Exception as exc:
            return EmailResult(False, "resend", error=str(exc))

    smtp_username = str(smtp_user or "").strip()
    smtp_password = str(smtp_app_password or "").strip()
    if smtp_username and smtp_password:
        sender = str(smtp_from or smtp_username).strip()
        try:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = recipient
            message.set_content(
                f"Your Luna report is ready: {report_url}\n\nOrder reference: {order_reference}"
            )
            message.add_alternative(html, subtype="html")
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=20) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(message)
            return EmailResult(True, "gmail-smtp")
        except Exception as exc:
            return EmailResult(False, "gmail-smtp", error=str(exc))

    return EmailResult(
        False,
        "none",
        error="No email provider is configured. Add Resend or Gmail SMTP secrets.",
    )
