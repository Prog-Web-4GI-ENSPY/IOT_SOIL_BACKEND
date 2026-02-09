# WhatsAppService
from app.services.infobip_service import InfobipService  # ← Remplace

class WhatsAppService:
    def __init__(self, twilio_service=None):  # Garde le nom "twilio_service"
        self.twilio = twilio_service or InfobipService()  # ← Interface identique !

    async def send_whatsapp(self, to: str, message: str) -> dict:
        return await self.twilio.send_whatsapp(to, message)  # Délègue 1:1
