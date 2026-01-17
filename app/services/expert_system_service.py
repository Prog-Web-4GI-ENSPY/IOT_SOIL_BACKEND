import httpx
import logging
from fastapi import HTTPException, status
from typing import List, Optional
from app.core.config import settings
from app.schemas.ai_integration import ExpertSystemResponse
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class ExpertSystemService:
    """Service pour interagir avec le Système Expert externe"""
    
    BASE_URL = str(settings.EXPERT_SYSTEM_URL).rstrip("/")
    QUERY_ENDPOINT = f"{BASE_URL}/api/query"

    @staticmethod
    async def query_expert_system(query: str, region: str = "Centre", notify: bool = False, user_email: str = None) -> Optional[ExpertSystemResponse]:
        """
        Interroge le système expert pour obtenir des conseils sur une culture spécifique
        """
        payload = {
        "query": query,
        "region": region
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    ExpertSystemService.QUERY_ENDPOINT,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Erreur SE: {response.status_code} - {response.text}")
                    # On ne veut pas forcément bloquer si le SE échoue, 
                    # mais on log l'erreur. La logique d'orchestration 
                    # décidera si c'est fatal.
                    return None
                
                data = response.json()
                result = ExpertSystemResponse(**data)
                # Notification optionnelle
                if notify and user_email:
                    notif = NotificationService()
                    await notif.send_email(user_email, "Réponse Système Expert", f"{result.final_response}")
                return result
                
            except httpx.RequestError as e:
                logger.error(f"Erreur de connexion au SE: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Erreur inattendue SE: {str(e)}")
                return None
