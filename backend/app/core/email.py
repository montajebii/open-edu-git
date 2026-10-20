"""
Email utilities for OpenEdu Git.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)

# Placeholder from the shipped settings: SMTP is not actually configured.
_UNCONFIGURED_SMTP_HOSTS = {"", "smtp.example.com"}


def smtp_configured() -> bool:
    """True when a real SMTP server has been configured."""
    return settings.SMTP_SERVER not in _UNCONFIGURED_SMTP_HOSTS


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email using SMTP."""
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        # Connect to SMTP server
        with smtplib.SMTP(
            settings.SMTP_SERVER, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT
        ) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        logger.warning("Error sending email to %s: %s", to, e)
        return False


def send_verification_email(email: str, token: str) -> bool:
    """Send an email verification email.

    Falls back to logging the link when SMTP is not configured, so local
    development and CI can complete the flow without a mail server.
    """
    verification_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
    if not smtp_configured():
        logger.info(
            "SMTP is not configured - verification link for %s: %s", email, verification_link
        )
        return True
    subject = "تأیید ایمیل شما در OpenEdu Git"
    body = f"""
    <html>
        <body>
            <p>برای تأیید ایمیل خود، روی لینک زیر کلیک کنید:</p>
            <p><a href="{verification_link}">{verification_link}</a></p>
            <p>اگر شما این ایمیل را درخواست نکرده‌اید، آن را نادیده بگیرید.</p>
        </body>
    </html>
    """
    return send_email(email, subject, body)
