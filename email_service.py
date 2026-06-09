"""
Email Service.

Sends report-completion notifications via SMTP. Silently no-ops if SMTP is not
configured so the rest of the system keeps working.
"""
from __future__ import annotations
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional, List
from backend.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.enabled = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        if not self.enabled:
            logger.info("Email disabled — would have sent '%s' to %s", subject, to)
            return False
        try:
            msg = EmailMessage()
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content("Your report is ready. Open this email in an HTML-capable client.")
            msg.add_alternative(body_html, subtype="html")

            for path in attachments or []:
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                    name = path.rsplit("/", 1)[-1]
                    msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=name)
                except Exception as e:
                    logger.warning("Could not attach %s: %s", path, e)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as srv:
                srv.starttls()
                srv.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                srv.send_message(msg)
            return True
        except Exception as e:
            logger.exception("Email send failed: %s", e)
            return False


email_service = EmailService()
