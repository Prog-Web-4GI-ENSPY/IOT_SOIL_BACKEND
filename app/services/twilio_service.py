from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    """Service Twilio pour SMS et WhatsApp"""
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID

    async def send_sms(self, to: str, message: str, sender: str = None) -> dict:
        try:
            from_number = sender or self.phone_number
            sms = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            logger.info(f"SMS envoyé: {sms.sid} à {to}")
            return {
                "success": True,
                "message_id": sms.sid,
                "status": sms.status,
                "to": to,
                "from": from_number
            }
        except TwilioRestException as e:
            logger.error(f"Erreur Twilio: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return {"success": False, "error": str(e)}

    async def send_whatsapp(self, to: str, message: str) -> dict:
        try:
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            from_number = f'whatsapp:{self.phone_number}'
            msg = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            logger.info(f"WhatsApp envoyé: {msg.sid} à {to}")
            return {"success": True, "message_id": msg.sid, "status": msg.status, "to": to}
        except Exception as e:
            logger.error(f"Erreur WhatsApp: {e}")
            return {"success": False, "error": str(e)}
