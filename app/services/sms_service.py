# app/services/sms_service.py
from app.services.infobip_service import InfobipService  # ← Remplace twilio_service

class SMSService:
    def __init__(self):
        self.infobip = InfobipService()  # ← Interface identique !

class SMSServiceFactory:
    @staticmethod
    def get_service(provider: str = None):
        return SMSService()  # Toujours Infobip maintenant
