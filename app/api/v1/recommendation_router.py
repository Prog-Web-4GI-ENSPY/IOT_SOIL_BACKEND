from fastapi import APIRouter, Depends, status, Query, Body, HTTPException, BackgroundTasks
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
from app.services.ml_service import MLService
from app.services.expert_system_service import ExpertSystemService
from app.schemas.ai_integration import (
    UnifiedRecommendationRequest, 
    UnifiedRecommendationResponse,
    ParcellePredictionRequest
)
from datetime import datetime

router = APIRouter(
    tags=["Recommandations"]
)


@router.get(
    "/",
    response_model=List[RecommendationResponse],
    summary="Récupérer l'historique des recommandations"
)
async def get_all_recommendations(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    priorite: Optional[str] = Query(None, description="Filtrer par priorité"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer l'historique de toutes les recommandations de l'utilisateur connecté.
    """
    return RecommendationService.get_all_recommendations(
        db, str(current_user.id), skip, limit, priorite
    )


@router.get(
    "/parcelle/{parcelle_id}",
    response_model=List[RecommendationResponse],
    summary="Récupérer l'historique par parcelle"
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
    Récupérer l'historique des recommandations d'une parcelle spécifique.
    """
    return RecommendationService.get_recommendations_by_parcelle(
        db, parcelle_id, str(current_user.id), skip, limit, priorite
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Détails d'une recommandation"
)
async def get_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une recommandation archivée.
    """
    return RecommendationService.get_recommendation_by_id(
        db, recommendation_id, str(current_user.id)
    )


@router.post(
    "/predict-crop",
    response_model=UnifiedRecommendationResponse,
    summary="Recommandation de culture (ML + Système Expert)"
)
async def predict_crop_unified(
    request_data: UnifiedRecommendationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint chef d'orchestre utilisant RecommendationService.
    """
    return await RecommendationService.run_unified_recommendation(
        db=db,
        user=current_user,
        background_tasks=background_tasks,
        parcelle_id=request_data.parcelle_id,
        soil_data=request_data.soil_data,
        region=request_data.region,
        query=request_data.query
    )


@router.post(
    "/parcelle/{parcelle_id}/predict-crop",
    response_model=UnifiedRecommendationResponse,
    summary="Prédire la culture pour une parcelle (utilise les dernières mesures)"
)
async def predict_parcelle_crop(
    parcelle_id: str,
    background_tasks: BackgroundTasks,
    request_data: Optional[ParcellePredictionRequest] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prédit la culture optimale pour une parcelle spécifique via RecommendationService.
    """
    return await RecommendationService.run_unified_recommendation(
        db=db,
        user=current_user,
        background_tasks=background_tasks,
        parcelle_id=parcelle_id,
        region=request_data.region if request_data else None,
        query=request_data.query if request_data else None
    )