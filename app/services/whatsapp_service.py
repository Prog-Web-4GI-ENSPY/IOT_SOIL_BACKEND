import logging
from app.core.config import settings
from app.services.twilio_service import TwilioService

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service pour l'envoi de messages WhatsApp (Twilio API)"""
    def __init__(self, twilio_service=None):
        self.twilio = twilio_service or TwilioService()

    async def send_whatsapp(self, to: str, message: str) -> dict:
        try:
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            from_number = f'whatsapp:{settings.TWILIO_PHONE_NUMBER}'
            result = self.twilio.client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            logger.info(f"WhatsApp envoyé: {result.sid} à {to}")
            return {"success": True, "message_id": result.sid, "status": result.status, "to": to}
        except Exception as e:
            logger.error(f"Erreur WhatsApp: {e}")
            return {"success": False, "error": str(e)}