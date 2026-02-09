from fastapi import APIRouter, Depends, status, Query, Body, HTTPException
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint chef d'orchestre qui :
    1. Appelle le service de Machine Learning pour prédire la culture idéale.
    2. Utilise le Système Expert pour justifier et donner des conseils sur cette culture.
    3. Agrège les résultats pour le frontend.
    """
    # 1. Prédire la culture d'abord (enveloppé dans une liste)
    ml_result = await MLService.predict_crop([request_data.soil_data])
    recommended_crop = ml_result.recommended_crop

    # 2. Système Expert Multi-Requêtes
    current_region = request_data.region or "Centre"
    
    queries = {
        "plantation": request_data.query or f"Quelle est la période optimale de plantation pour le {recommended_crop} dans la région {current_region} ?",
        "irrigation": f"Quels sont les besoins en irrigation spécifiques pour le {recommended_crop} ?",
        "engrais": f"Quels engrais et amendements du sol recommandez-vous pour le {recommended_crop} ?",
        "prevention": f"Comment prévenir les maladies et ravageurs communs du {recommended_crop} ?"
    }

    results_justification = {}
    full_justification = ""
    
    for key, q in queries.items():
        expert_res = await ExpertSystemService.query_expert_system(query=q, region=current_region)
        if expert_res:
            results_justification[key] = expert_res.final_response
            full_justification += f"\n\n### {key.capitalize()}\n{expert_res.final_response}"
        else:
            results_justification[key] = "Pas de réponse disponible."
            full_justification += f"\n\n### {key.capitalize()}\nPas de réponse disponible."

    # 4. Stockage en base de données (si parcelle_id est fourni)
    if request_data.parcelle_id:
        from app.models.recommendation import Recommendation
        import uuid
        
        new_rec = Recommendation(
            id=str(uuid.uuid4()),
            titre=f"Recommandation Manuelle pour {recommended_crop}",
            contenu=full_justification.strip(),
            priorite="Normal",
            parcelle_id=request_data.parcelle_id,
            user_id=str(current_user.id),
            expert_metadata={
                "source": "AI_Orchestrator_Manual",
                "ml_confidence": ml_result.confidence,
                "recommended_crop": recommended_crop,
                "detailed_responses": results_justification,
                "ml_details": ml_result.dict()
            }
        )
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)

    # 5. Notification Multi-canaux
    from app.services.notification_service import NotificationService
    notif_service = NotificationService()
    user_pref_modes = getattr(current_user, 'notification_modes', ['email'])
    
    message_title = f"AgroPredict: Nouvelle recommandation ({recommended_crop})"
    message_body = f"Culture: {recommended_crop}\nConfiance: {ml_result.confidence:.2f}\n\n{full_justification.strip()}"
    
    for mode in user_pref_modes:
        try:
            if mode == 'email':
                await notif_service.send_email(current_user.email, message_title, message_body)
            elif mode == 'sms' and current_user.telephone:
                await notif_service.send_sms(current_user.telephone, message_body)
            elif mode == 'whatsapp' and current_user.telephone:
                await notif_service.send_whatsapp(current_user.telephone, message_body)
            elif mode == 'telegram':
                await notif_service.send_telegram(message_body)
        except Exception:
            pass

    return UnifiedRecommendationResponse(
        recommended_crop=recommended_crop,
        confidence_score=ml_result.confidence,
        justification=full_justification.strip(),
        detailed_justifications=results_justification,
        ml_details=ml_result,
        generated_at=datetime.utcnow().isoformat()
    )


@router.post(
    "/parcelle/{parcelle_id}/predict-crop",
    response_model=UnifiedRecommendationResponse,
    summary="Prédire la culture pour une parcelle (utilise les dernières mesures)"
)
async def predict_parcelle_crop(
    parcelle_id: str,
    request_data: Optional[ParcellePredictionRequest] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prédit la culture optimale pour une parcelle spécifique en utilisant ses dernières mesures de capteurs.
    Si des données sont fournies dans le body, elles surchargent celles de la base de données (optionnel).
    """
    # 1. Récupérer la parcelle
    from app.services.parcelle_service import ParcelleService
    # On utilise get_parcelle_by_id qui vérifie aussi l'appartenance à l'utilisateur (via terrain)
    try:
        parcelle = ParcelleService.get_parcelle_by_id(db, parcelle_id, str(current_user.id))
    except HTTPException:
        # Si la méthode lève une 404, on la laisse passer ou on la relance
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcelle non trouvée"
        )

    # 2. Récupérer l'ensemble des données prélevées le jour le plus récent
    from app.models.sensor_data import SensorMeasurements
    from sqlalchemy import func
    
    # Trouver le timestamp de la mesure la plus récente pour cette parcelle
    latest_timestamp = db.query(func.max(SensorMeasurements.timestamp))\
        .filter(SensorMeasurements.parcelle_id == parcelle_id)\
        .scalar()

    if not latest_timestamp:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune mesure de capteur trouvée pour cette parcelle. Impossible de faire une prédiction."
        )

    # Récupérer toutes les mesures de ce jour précis
    latest_date = latest_timestamp.date()
    daily_measurements = db.query(SensorMeasurements)\
        .filter(
            SensorMeasurements.parcelle_id == parcelle_id,
            func.date(SensorMeasurements.timestamp) == latest_date
        )\
        .order_by(SensorMeasurements.timestamp.asc())\
        .all()

    # 3. Préparer le lot de données du sol (mapping Float -> int pour N, P, K)
    from app.schemas.ai_integration import SoilData
    
    soil_data_list = [
        SoilData(
            N=int(m.azote) if m.azote is not None else 0,
            P=int(m.phosphore) if m.phosphore is not None else 0,
            K=int(m.potassium) if m.potassium is not None else 0,
            temperature=m.temperature if m.temperature is not None else 0.0,
            humidity=m.humidity if m.humidity is not None else 0.0,
            ph=m.ph if m.ph is not None else 0.0
        ) for m in daily_measurements
    ]

    # 4. Appeler le service ML avec l'ensemble des données du jour
    ml_result = await MLService.predict_crop(soil_data_list)
    recommended_crop = ml_result.recommended_crop

    # 5. Système Expert Multi-Requêtes
    # On récupère la région depuis la parcelle -> terrain -> localite
    db_region = "Centre"
    if parcelle.terrain and parcelle.terrain.localite:
        db_region = parcelle.terrain.localite.region or "Centre"
    
    current_region = db_region
    user_query = None
    
    if request_data:
        if request_data.region:
            current_region = request_data.region
        if request_data.query:
            user_query = request_data.query

    # Les 4 questions standard
    queries = {
        "plantation": user_query or f"Quelle est la période optimale de plantation pour le {recommended_crop} dans la région {current_region} ?",
        "irrigation": f"Quels sont les besoins en irrigation spécifiques pour le {recommended_crop} ?",
        "engrais": f"Quels engrais et amendements du sol recommandez-vous pour le {recommended_crop} ?",
        "prevention": f"Comment prévenir les maladies et ravageurs communs du {recommended_crop} ?"
    }

    results_justification = {}
    full_justification = ""
    
    for key, q in queries.items():
        expert_res = await ExpertSystemService.query_expert_system(query=q, region=current_region)
        if expert_res:
            results_justification[key] = expert_res.final_response
            full_justification += f"\n\n### {key.capitalize()}\n{expert_res.final_response}"
        else:
            results_justification[key] = "Pas de réponse disponible."
            full_justification += f"\n\n### {key.capitalize()}\nPas de réponse disponible."

    # 6. Sauvegarder la recommandation
    from app.models.recommendation import Recommendation
    import uuid
    
    new_rec = Recommendation(
        id=str(uuid.uuid4()),
        titre=f"Analyse Complète pour {recommended_crop}",
        contenu=full_justification.strip(),
        priorite="Normal",
        parcelle_id=parcelle_id,
        user_id=str(current_user.id),
        expert_metadata={
            "source": "AI_Orchestrator_MultiQuery",
            "ml_confidence": ml_result.confidence,
            "recommended_crop": recommended_crop,
            "detailed_responses": results_justification,
            "ml_details": ml_result.dict()
        }
    )
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)

    # 7. Notification Multi-canaux
    from app.services.notification_service import NotificationService
    notif_service = NotificationService()
    
    user_pref_modes = getattr(current_user, 'notification_modes', ['email'])
    
    message_title = f"AgroPredict: Recommandation pour {recommended_crop}"
    message_body = f"Culture recommandée: {recommended_crop}\nConfiance: {ml_result.confidence:.2f}\n\nJustification:\n{full_justification.strip()}"
    
    # Envoi asynchrone (best effort)
    for mode in user_pref_modes:
        if mode == 'email':
            await notif_service.send_email(current_user.email, message_title, message_body)
        elif mode == 'sms' and current_user.telephone:
            await notif_service.send_sms(current_user.telephone, message_body)
        elif mode == 'whatsapp' and current_user.telephone:
            await notif_service.send_whatsapp(current_user.telephone, message_body)
        elif mode == 'telegram':
            # Note: telegram chat_id might be different from user id, assuming it's linked
            await notif_service.send_telegram(message_body)

    return UnifiedRecommendationResponse(
        recommended_crop=recommended_crop,
        confidence_score=ml_result.confidence,
        justification=full_justification.strip(),
        detailed_justifications=results_justification,
        ml_details=ml_result,
        generated_at=datetime.utcnow().isoformat()
    )