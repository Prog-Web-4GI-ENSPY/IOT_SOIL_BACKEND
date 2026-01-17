from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService
from app.services.telegram_service import TelegramService
from app.services.sms_service import SMSServiceFactory

class NotificationService:
    """Service unifié pour envoyer des notifications via plusieurs canaux."""
    def __init__(self):
        self.email_service = EmailService()
        self.whatsapp_service = WhatsAppService()
        self.telegram_service = TelegramService()
        self.sms_service = SMSServiceFactory.get_service()

    async def send_email(self, to: str, subject: str, body: str) -> dict:
        return self.email_service.send_email(to, subject, body)

    async def send_sms(self, to: str, message: str) -> dict:
        return await self.sms_service.send_sms(to, message)

    async def send_whatsapp(self, to: str, message: str) -> dict:
        return await self.whatsapp_service.send_whatsapp(to, message)

    async def send_telegram(self, message: str, chat_id: str = None) -> dict:
        return await self.telegram_service.send_telegram(message, chat_id)