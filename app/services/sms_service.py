# app/services/sms_service.py
from app.services.infobip_service import InfobipService  # ← Remplace twilio_service

class SMSService:
    def __init__(self):
        self.infobip = InfobipService()

    async def send_sms(self, to: str, message: str) -> dict:
        return await self.infobip.send_sms(to, message)

class SMSServiceFactory:
    @staticmethod
    def get_service(provider: str = None):
        return SMSService()  # Toujours Infobip maintenant
