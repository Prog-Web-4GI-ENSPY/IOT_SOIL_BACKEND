import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service pour l'envoi d'emails via SMTP"""
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL or self.smtp_user

    def send_email(self, to: str, subject: str, body: str) -> dict:
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to, msg.as_string())
            logger.info(f"Email envoyé à {to}")
            return {"success": True, "to": to, "subject": subject}
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return {"success": False, "error": str(e)}