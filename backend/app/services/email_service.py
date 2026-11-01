"""Email service - sends password reset emails via SMTP (optional)."""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_reset_email(to_email: str, full_name: str, reset_link: str) -> bool:
    """Send a password reset email. Returns True if sent, False if SMTP not configured."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info("SMTP not configured - skipping email send for %s", to_email)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Smart Agriculture - Password Reset"
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #16A34A;">Smart Agriculture - Password Reset</h2>
            <p>Hello {full_name},</p>
            <p>You requested a password reset for your Smart Agriculture account.</p>
            <p>Click the link below to reset your password (valid for 1 hour):</p>
            <p><a href="http://localhost:5173{reset_link}"
                style="background:#16A34A;color:#fff;padding:10px 24px;border-radius:8px;
                text-decoration:none;display:inline-block;">Reset Password</a></p>
            <p>If you did not request this, please ignore this email.</p>
            <hr>
            <p style="font-size:12px;color:#999;">Smart Agriculture System</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

        logger.info("Password reset email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send reset email: %s", exc)
        return False
