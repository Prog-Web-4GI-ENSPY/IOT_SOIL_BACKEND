from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.alert import Alert, TypeAlerte, SeveriteAlerte
from app.schemas.alert import AlertBase, AlertResponse
from app.core.dependencies import get_current_user
from app.models.user import User
from fastapi import HTTPException
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/alerts",
    tags=["Alertes"]
)


@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle alerte"
)
async def create_alert(
    alert_data: AlertBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle alerte pour une parcelle.

    - **niveau**: Niveau de l'alerte (Critique, Avertissement, Info)
    - **message**: Message descriptif de l'alerte
    - **parcelle_id**: ID de la parcelle concernée
    - **type_alerte**: Type d'alerte (humidite, temperature, ph, batterie)
    - **severite**: Sévérité (faible, moyenne, critique)
    """
    alert = Alert(
        id=str(uuid.uuid4()),
        niveau=alert_data.niveau,
        message=alert_data.message,
        parcelle_id=alert_data.parcelle_id,
        user_id=str(current_user.id),
        date_declenchement=alert_data.date_declenchement or datetime.utcnow(),
        est_resolue=alert_data.est_resolue
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="Récupérer toutes les alertes"
)
async def get_all_alerts(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    est_resolue: Optional[bool] = Query(None, description="Filtrer par statut de résolution"),
    severite: Optional[SeveriteAlerte] = Query(None, description="Filtrer par sévérité"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les alertes de l'utilisateur.

    Possibilité de filtrer par statut de résolution et sévérité.
    """
    query = db.query(Alert).filter(Alert.user_id == str(current_user.id))

    if est_resolue is not None:
        query = query.filter(Alert.est_resolue == est_resolue)

    if severite:
        query = query.filter(Alert.severite == severite)

    query = query.order_by(Alert.date_declenchement.desc())
    return query.offset(skip).limit(limit).all()


@router.get(
    "/parcelle/{parcelle_id}",
    response_model=List[AlertResponse],
    summary="Récupérer les alertes d'une parcelle"
)
async def get_alerts_by_parcelle(
    parcelle_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    est_resolue: Optional[bool] = Query(None, description="Filtrer par statut de résolution"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les alertes d'une parcelle spécifique.
    """
    query = db.query(Alert).filter(
        Alert.parcelle_id == parcelle_id,
        Alert.user_id == str(current_user.id)
    )

    if est_resolue is not None:
        query = query.filter(Alert.est_resolue == est_resolue)

    query = query.order_by(Alert.date_declenchement.desc())
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Récupérer une alerte par son ID"
)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une alerte spécifique.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == str(current_user.id)
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée"
        )

    return alert


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Marquer une alerte comme résolue"
)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marquer une alerte comme résolue.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == str(current_user.id)
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée"
        )

    alert.est_resolue = True
    db.commit()
    db.refresh(alert)
    return alert


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une alerte"
)
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une alerte.
    """
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == str(current_user.id)
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerte non trouvée"
        )

    db.delete(alert)
    db.commit()
    return {"message": "Alerte supprimée avec succès"}


@router.get(
    "/statistics/summary",
    summary="Statistiques des alertes"
)
async def get_alert_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques des alertes de l'utilisateur.

    Retourne le nombre d'alertes par sévérité et statut de résolution.
    """
    from sqlalchemy import func

    # Total des alertes
    total = db.query(func.count(Alert.id)).filter(
        Alert.user_id == str(current_user.id)
    ).scalar()

    # Alertes non résolues
    non_resolues = db.query(func.count(Alert.id)).filter(
        Alert.user_id == str(current_user.id),
        Alert.est_resolue == False
    ).scalar()

    # Par sévérité
    by_severite = {}
    for severite in SeveriteAlerte:
        count = db.query(func.count(Alert.id)).filter(
            Alert.user_id == str(current_user.id),
            Alert.severite == severite,
            Alert.est_resolue == False
        ).scalar()
        by_severite[severite.value] = count

    return {
        "total": total,
        "non_resolues": non_resolues,
        "resolues": total - non_resolues,
        "by_severite": by_severite
    }
