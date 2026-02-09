from infobip.api.client import InfobipClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class InfobipService:
    """Service Infobip pour SMS et WhatsApp - Remplace Twilio 1:1"""
    
    def __init__(self):
        # Configuration Infobip
        configuration = {
            'base_url': settings.INFOBIP_BASE_URL,
            'api_key': settings.INFOBIP_API_KEY
        }
        self.client = InfobipClient(configuration)
        self.sender_number = settings.INFOBIP_SENDER_NUMBER

    async def send_sms(self, to: str, message: str, sender: str = None) -> dict:
        """Identique à Twilio.send_sms()"""
        try:
            from_number = sender or self.sender_number
            sms_request = {
                "messages": [{
                    "destinations": [{"to": to}],
                    "from": from_number,
                    "textMessage": {"text": message}
                }]
            }
            
            response = self.client.sms.sms_text_message.send_multiple_sms(sms_request)
            
            # Premier message ID (comme Twilio.sid)
            message_id = response.messages[0].message_id if response.messages else None
            status = response.messages[0].status.name if response.messages else "unknown"
            
            logger.info(f"SMS envoyé Infobip: {message_id} à {to}")
            return {
                "success": True,
                "message_id": message_id,
                "status": status,
                "to": to,
                "from": from_number
            }
        except Exception as e:
            logger.error(f"Erreur Infobip SMS: {e}")
            return {"success": False, "error": str(e)}

    async def send_whatsapp(self, to: str, message: str) -> dict:
        """Identique à Twilio.send_whatsapp()"""
        try:
            # Format Infobip WhatsApp
            whatsapp_request = {
                "messages": [{
                    "from": self.sender_number,
                    "to": to,
                    "messageId": f"wa-{hash(message)}",
                    "content": {"text": message}
                }]
            }
            
            response = self.client.whatsapp.whatsapp_text_message.send_whatsapp_message(whatsapp_request)
            
            message_id = response.messages[0].message_id if response.messages else None
            status = response.messages[0].status.name if response.messages else "unknown"
            
            logger.info(f"WhatsApp Infobip: {message_id} à {to}")
            return {
                "success": True,
                "message_id": message_id,
                "status": status,
                "to": to
            }
        except Exception as e:
            logger.error(f"Erreur WhatsApp Infobip: {e}")
            return {"success": False, "error": str(e)}
