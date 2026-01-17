from app.services.twilio_service import TwilioService
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """Service pour l'envoi de SMS via Twilio"""
    def __init__(self):
        self.twilio = TwilioService()

    async def send_sms(self, to: str, message: str) -> dict:
        return await self.twilio.send_sms(to, message)

class SMSServiceFactory:
    @staticmethod
    def get_service(provider: str = None):
        # Pour l'instant, retourne toujours Twilio
        return SMSService()
