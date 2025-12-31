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
from app.services.ml_service import MLService
from app.services.expert_system_service import ExpertSystemService
from app.schemas.ai_integration import UnifiedRecommendationRequest, UnifiedRecommendationResponse
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint chef d'orchestre qui :
    1. Appelle le service de Machine Learning pour prédire la culture idéale.
    2. Utilise le Système Expert pour justifier et donner des conseils sur cette culture.
    3. Agrège les résultats pour le frontend.
    """
    # 1. Appel du service ML
    ml_result = await MLService.predict_crop(request_data.soil_data)
    recommended_crop = ml_result.majority_crop
    
    # 2. Appel du Système Expert pour la justification/conseils
    expert_result = await ExpertSystemService.query_expert_system(
        crop_name=recommended_crop,
        region=request_data.region or "Centre"
    )
    
    # 3. Agrégation et formatage de la réponse
    justification = "Pas de justification disponible du système expert."
    if expert_result:
        justification = expert_result.final_response
        
    # 4. Stockage en base de données (si parcelle_id est fourni)
    if request_data.parcelle_id:
        from app.models.recommendation import Recommendation
        import uuid
        
        new_rec = Recommendation(
            id=str(uuid.uuid4()),
            titre=f"Recommandation pour {recommended_crop}",
            contenu=justification,
            priorite="Normal",
            parcelle_id=request_data.parcelle_id,
            user_id=str(current_user.id),
            expert_metadata={
                "source": "AI_Orchestrator",
                "ml_confidence": ml_result.confidence,
                "recommended_crop": recommended_crop,
                "ml_details": ml_result.dict(),
                "expert_details": expert_result.dict() if expert_result else None
            }
        )
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)
        
    return UnifiedRecommendationResponse(
        recommended_crop=recommended_crop,
        confidence_score=ml_result.confidence,
        justification=justification,
        ml_details=ml_result,
        expert_details=expert_result,
        generated_at=datetime.utcnow().isoformat()
    )