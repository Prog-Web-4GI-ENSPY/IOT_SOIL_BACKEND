import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    """Service pour l'envoi de notifications Telegram via Bot API"""
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_telegram(self, message: str, chat_id: str = None) -> dict:
        chat_id = chat_id or self.chat_id
        if not self.bot_token or not chat_id:
            return {"success": False, "error": "Bot token ou chat_id manquant"}
        payload = {"chat_id": chat_id, "text": message}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Message Telegram envoyé à {chat_id}")
                    return {"success": True, "chat_id": chat_id}
                else:
                    logger.error(f"Erreur Telegram: {response.text}")
                    return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Erreur Telegram: {e}")
            return {"success": False, "error": str(e)}