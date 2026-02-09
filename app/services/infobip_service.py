import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class InfobipService:
    """Service Infobip pour SMS et WhatsApp - Utilise httpx directement"""
    
    def __init__(self):
        # Configuration Infobip :
        self.base_url = settings.INFOBIP_BASE_URL.rstrip('/')
        self.api_key = settings.INFOBIP_API_KEY
        self.sender_number = settings.INFOBIP_SENDER_NUMBER
        self.headers = {
            "Authorization": f"App {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def send_sms(self, to: str, message: str, sender: str = None) -> dict:
        """Envoi de SMS via Infobip API"""
        try:
            from_number = sender or self.sender_number
            url = f"{self.base_url}/sms/2/text/advanced"
            
            payload = {
                "messages": [{
                    "destinations": [{"to": to}],
                    "from": from_number,
                    "text": message
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            
            # Extraction des informations de réponse
            msg_data = data.get("messages", [{}])[0]
            message_id = msg_data.get("messageId")
            status_name = msg_data.get("status", {}).get("name", "unknown")
            
            logger.info(f"SMS envoyé Infobip: {message_id} à {to}")
            return {
                "success": True,
                "message_id": message_id,
                "status": status_name,
                "to": to,
                "from": from_number
            }
        except Exception as e:
            logger.error(f"Erreur Infobip SMS: {e}")
            return {"success": False, "error": str(e)}

    async def send_whatsapp(self, to: str, message: str) -> dict:
        """Envoi de message WhatsApp via Infobip API"""
        try:
            url = f"{self.base_url}/whatsapp/1/message/text"
            
            # Format Infobip WhatsApp
            payload = {
                "from": self.sender_number,
                "to": to,
                "content": {"text": message}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            
            # Extraction des informations de réponse
            message_id = data.get("messageId")
            status_name = data.get("status", {}).get("name", "PENDING")
            
            logger.info(f"WhatsApp Infobip: {message_id} à {to}")
            return {
                "success": True,
                "message_id": message_id,
                "status": status_name,
                "to": to
            }
        except Exception as e:
            logger.error(f"Erreur WhatsApp Infobip: {e}")
            return {"success": False, "error": str(e)}

# Instance globale
infobip_service = InfobipService()
