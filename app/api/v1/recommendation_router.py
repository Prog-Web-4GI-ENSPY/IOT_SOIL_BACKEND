from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationResponse
)
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommandations"]
)


@router.post(
    "/",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle recommandation"
)
async def create_recommendation(
    recommendation_data: RecommendationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle recommandation agricole pour une parcelle.
    
    - **titre**: Titre de la recommandation (5-200 caractères)
    - **description**: Description détaillée (minimum 10 caractères)
    - **parcelle_id**: ID de la parcelle concernée
    - **priorite**: Niveau de priorité (Urgent, Normal, Faible)
    """
    return RecommendationService.create_recommendation(
        db, recommendation_data, str(current_user.id)
    )


@router.get(
    "/",
    response_model=List[RecommendationResponse],
    summary="Récupérer toutes les recommandations"
)
async def get_all_recommendations(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    priorite: Optional[str] = Query(None, description="Filtrer par priorité"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les recommandations de l'utilisateur connecté.
    
    Possibilité de filtrer par priorité et paginer les résultats.
    Les recommandations sont triées par date d'émission décroissante.
    """
    return RecommendationService.get_all_recommendations(
        db, str(current_user.id), skip, limit, priorite
    )


@router.get(
    "/parcelle/{parcelle_id}",
    response_model=List[RecommendationResponse],
    summary="Récupérer les recommandations d'une parcelle"
)
async def get_recommendations_by_parcelle(
    parcelle_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    priorite: Optional[str] = Query(None, description="Filtrer par priorité"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les recommandations d'une parcelle spécifique.
    
    Les recommandations sont triées par date d'émission décroissante.
    """
    return RecommendationService.get_recommendations_by_parcelle(
        db, parcelle_id, str(current_user.id), skip, limit, priorite
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Récupérer une recommandation par son ID"
)
async def get_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une recommandation spécifique.
    """
    return RecommendationService.get_recommendation_by_id(
        db, recommendation_id, str(current_user.id)
    )


@router.put(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Mettre à jour une recommandation"
)
async def update_recommendation(
    recommendation_id: str,
    recommendation_data: RecommendationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les informations d'une recommandation.
    
    Seuls les champs fournis seront mis à jour.
    """
    return RecommendationService.update_recommendation(
        db, recommendation_id, recommendation_data, str(current_user.id)
    )


@router.delete(
    "/{recommendation_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une recommandation"
)
async def delete_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une recommandation (suppression logique).
    
    La recommandation ne sera pas physiquement supprimée mais marquée comme supprimée.
    """
    return RecommendationService.delete_recommendation(
        db, recommendation_id, str(current_user.id)
    )


@router.post(
    "/generate/weather/{parcelle_id}",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer une recommandation basée sur la météo"
)
async def generate_weather_based_recommendation(
    parcelle_id: str,
    weather_data: dict = Body(
        ...,
        example={
            "temperature": 28.5,
            "humidity": 65,
            "precipitation": 10.5,
            "wind_speed": 15,
            "forecast_date": "2025-01-30"
        }
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Générer automatiquement une recommandation basée sur les données météorologiques.
    
    L'algorithme analyse:
    - La température prévue
    - Le taux d'humidité
    - Les précipitations attendues
    - La vitesse du vent
    
    Et génère des recommandations adaptées (irrigation, protection contre le gel, 
    drainage, etc.)
    
    **Données météo attendues:**
    - **temperature**: Température en °C
    - **humidity**: Humidité en %
    - **precipitation**: Précipitations en mm
    - **wind_speed**: Vitesse du vent en km/h (optionnel)
    - **forecast_date**: Date de la prévision (optionnel)
    """
    return RecommendationService.generate_weather_based_recommendation(
        db, parcelle_id, str(current_user.id), weather_data
    )