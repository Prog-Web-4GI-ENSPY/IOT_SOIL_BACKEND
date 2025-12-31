import httpx
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.ai_integration import ExpertSystemRequest, ExpertSystemResponse

logger = logging.getLogger(__name__)

class ExpertSystemService:
    """Service pour interagir avec le Système Expert externe"""
    
    BASE_URL = str(settings.EXPERT_SYSTEM_URL).rstrip("/")
    QUERY_ENDPOINT = f"{BASE_URL}/api/query"

    @staticmethod
    async def query_expert_system(crop_name: str, region: str = "Centre") -> ExpertSystemResponse:
        """
        Interroge le système expert pour obtenir des conseils sur une culture spécifique
        """
        query_text = f"Donne-moi des conseils d'experts pour la culture du {crop_name} dans la région {region}"
        
        payload = {
            "query": query_text,
            "region": region
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
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
                return ExpertSystemResponse(**data)
                
            except httpx.RequestError as e:
                logger.error(f"Erreur de connexion au SE: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Erreur inattendue SE: {str(e)}")
                return None
