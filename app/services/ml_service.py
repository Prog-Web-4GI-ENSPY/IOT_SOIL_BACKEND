import httpx
import logging
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.ai_integration import MLPredictRequest, MLPredictResponse, SoilData

logger = logging.getLogger(__name__)

class MLService:
    """Service pour interagir avec l'API de Machine Learning externe"""
    
    BASE_URL = str(settings.ML_SERVICE_URL).rstrip("/")
    PREDICT_ENDPOINT = f"{BASE_URL}/predict/batch"

    @staticmethod
    async def predict_crop(soil_data: SoilData) -> MLPredictResponse:
        """
        Appelle le service ML pour prédire la culture la plus adaptée
        """
        # On prépare un batch simplifié avec un seul échantillon pour l'instant
        # car le frontend fournit généralement un état instantané
        payload = {
            "samples": [soil_data.dict()]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    MLService.PREDICT_ENDPOINT,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Erreur service ML: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Le service de prédiction ML est temporairement indisponible"
                    )
                
                data = response.json()
                return MLPredictResponse(**data)
                
            except httpx.RequestError as e:
                logger.error(f"Erreur de connexion au service ML: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Impossible de contacter le service de prédiction ML"
                )
            except Exception as e:
                logger.error(f"Erreur inattendue service ML: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur lors de la récupération de la prédiction ML"
                )
