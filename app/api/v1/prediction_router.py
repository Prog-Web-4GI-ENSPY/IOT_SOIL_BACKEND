from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import (
    PredictionCreate,
    PredictionUpdate,
    PredictionResponse
)
from app.core.dependencies import get_current_user
from app.models.user import User
from fastapi import HTTPException
import uuid

router = APIRouter(
    prefix="/predictions",
    tags=["Prédictions"]
)


@router.post(
    "/",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle prédiction"
)
async def create_prediction(
    data: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle prédiction.

    - **modele**: Nom du modèle utilisé (obligatoire)
    - **precision**: Précision du modèle en pourcentage (0-100)
    - **parcelle_id**: ID de la parcelle concernée
    """
    prediction = Prediction(
        id=str(uuid.uuid4()),
        user_id=str(current_user.id),
        modele=data.modele,
        input_data={},  # À adapter selon les besoins
        resultat={
            "precision": data.precision,
            "parcelle_id": data.parcelle_id
        },
        date_prediction=data.date_creation or datetime.utcnow()
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.get(
    "/",
    response_model=List[PredictionResponse],
    summary="Récupérer toutes les prédictions"
)
async def get_all_predictions(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    modele: Optional[str] = Query(None, description="Filtrer par modèle"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les prédictions de l'utilisateur.

    Possibilité de filtrer par modèle.
    """
    query = db.query(Prediction).filter(Prediction.user_id == str(current_user.id))

    if modele:
        query = query.filter(Prediction.modele.ilike(f"%{modele}%"))

    query = query.order_by(Prediction.date_prediction.desc())
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Récupérer une prédiction par son ID"
)
async def get_prediction(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une prédiction spécifique.
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == str(current_user.id)
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prédiction non trouvée"
        )

    return prediction


@router.put(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Mettre à jour une prédiction"
)
async def update_prediction(
    prediction_id: str,
    data: PredictionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une prédiction.

    Seuls les champs fournis seront mis à jour.
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == str(current_user.id)
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prédiction non trouvée"
        )

    if data.modele is not None:
        prediction.modele = data.modele

    if data.precision is not None:
        if not prediction.resultat:
            prediction.resultat = {}
        prediction.resultat["precision"] = data.precision

    if data.parcelle_id is not None:
        if not prediction.resultat:
            prediction.resultat = {}
        prediction.resultat["parcelle_id"] = data.parcelle_id

    db.commit()
    db.refresh(prediction)
    return prediction


@router.delete(
    "/{prediction_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une prédiction"
)
async def delete_prediction(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une prédiction.
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == str(current_user.id)
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prédiction non trouvée"
        )

    db.delete(prediction)
    db.commit()
    return {"message": "Prédiction supprimée avec succès"}


@router.get(
    "/statistics/summary",
    summary="Statistiques des prédictions"
)
async def get_prediction_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques des prédictions de l'utilisateur.

    Retourne le nombre de prédictions par modèle et la précision moyenne.
    """
    from sqlalchemy import func

    # Total des prédictions
    total = db.query(func.count(Prediction.id)).filter(
        Prediction.user_id == str(current_user.id)
    ).scalar()

    # Par modèle
    by_modele = db.query(
        Prediction.modele,
        func.count(Prediction.id).label('count')
    ).filter(
        Prediction.user_id == str(current_user.id)
    ).group_by(Prediction.modele).all()

    modele_stats = {modele: count for modele, count in by_modele}

    return {
        "total": total,
        "by_modele": modele_stats
    }


@router.get(
    "/latest/user",
    response_model=List[PredictionResponse],
    summary="Dernières prédictions de l'utilisateur"
)
async def get_latest_predictions(
    limit: int = Query(10, ge=1, le=50, description="Nombre de prédictions à retourner"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les dernières prédictions de l'utilisateur.
    """
    predictions = db.query(Prediction).filter(
        Prediction.user_id == str(current_user.id)
    ).order_by(Prediction.date_prediction.desc()).limit(limit).all()

    return predictions
