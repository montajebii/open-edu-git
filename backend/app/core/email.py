"""
Email utilities for OpenEdu Git.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


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
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def send_verification_email(email: str, token: str) -> bool:
    """Send an email verification email."""
    verification_link = f"http://localhost:3000/verify-email?token={token}"
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
