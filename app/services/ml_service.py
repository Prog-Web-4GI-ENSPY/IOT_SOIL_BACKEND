import httpx
import logging
from typing import List
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.ai_integration import MLPredictRequest, MLPredictResponse, SoilData
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class MLService:
    """Service pour interagir avec l'API de Machine Learning externe"""
    
    BASE_URL = str(settings.ML_SERVICE_URL).rstrip("/")
    PREDICT_ENDPOINT = f"{BASE_URL}/predict/batch"

    @staticmethod
    async def predict_crop(soil_data_list: List[SoilData], notify: bool = False, user_email: str = None) -> MLPredictResponse:
        """
        Appelle le service ML pour prédire la culture la plus adaptée à partir d'un lot d'échantillons
        """
        # On prépare le payload avec tous les échantillons
        payload = {
            "samples": [sd.dict() for sd in soil_data_list]
        }
        
        # Configuration détaillée du timeout
        timeout = httpx.Timeout(
            20.0,           # Global timeout (augmenté pour le batch)
            connect=5.0,    
            read=15.0       
        )

        
        async with httpx.AsyncClient(timeout=timeout) as client:
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
                result = MLPredictResponse(**data)
                # Notification optionnelle
                if notify and user_email:
                    notif = NotificationService()
                    await notif.send_email(user_email, "Résultat de prédiction ML", f"Votre prédiction: {result.recommended_crop}")
                return result
                
            except httpx.ConnectError as e:
                logger.error(f"Erreur de connexion (DNS/Réseau) au service ML: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Impossible de résoudre ou contacter le service de prédiction ML (Vérifiez l'URL ou la connexion)"
                )
            except httpx.TimeoutException as e:
                logger.error(f"Timeout lors de l'appel au service ML: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Le service de prédiction ML a mis trop de temps à répondre"
                )
            except httpx.RequestError as e:
                logger.error(f"Erreur de requête au service ML: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Erreur lors de la communication avec le service de prédiction ML"
                )
            except Exception as e:
                logger.error(f"Erreur inattendue service ML: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur interne lors de la récupération de la prédiction ML"
                )
