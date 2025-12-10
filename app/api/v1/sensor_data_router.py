from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.sensor_data import SensorMeasurements
from app.schemas.sensor_data import (
    SensorMeasurementsCreate,
    SensorMeasurementsUpdate,
    SensorMeasurementsResponse
)
from app.core.dependencies import get_current_user
from app.models.user import User
from fastapi import HTTPException
import uuid

router = APIRouter(
    prefix="/sensor-data",
    tags=["Données de Capteurs"]
)


@router.post(
    "/",
    response_model=SensorMeasurementsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle mesure de capteur"
)
async def create_sensor_measurement(
    data: SensorMeasurementsCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle mesure de capteur.

    - **capteur_id**: ID du capteur (obligatoire)
    - **parcelle_id**: ID de la parcelle (obligatoire)
    - **measurements**: Données JSON des mesures (obligatoire)
    - **ph**, **azote**, **phosphore**, **potassium**, **humidity**, **temperature**: Valeurs optionnelles
    """
    measurement = SensorMeasurements(
        id=str(uuid.uuid4()),
        capteur_id=data.capteur_id,
        parcelle_id=data.parcelle_id,
        ph=data.ph,
        azote=data.azote,
        phosphore=data.phosphore,
        potassium=data.potassium,
        humidity=data.humidity,
        temperature=data.temperature,
        measurements=data.measurements,
        timestamp=data.timestamp or datetime.utcnow()
    )

    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get(
    "/",
    response_model=List[SensorMeasurementsResponse],
    summary="Récupérer toutes les mesures"
)
async def get_all_measurements(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les mesures de capteurs.
    """
    measurements = db.query(SensorMeasurements).order_by(
        SensorMeasurements.timestamp.desc()
    ).offset(skip).limit(limit).all()
    return measurements


@router.get(
    "/capteur/{capteur_id}",
    response_model=List[SensorMeasurementsResponse],
    summary="Récupérer les mesures d'un capteur"
)
async def get_measurements_by_capteur(
    capteur_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les mesures d'un capteur spécifique.

    Possibilité de filtrer par plage de dates.
    """
    query = db.query(SensorMeasurements).filter(
        SensorMeasurements.capteur_id == capteur_id
    )

    if start_date:
        query = query.filter(SensorMeasurements.timestamp >= start_date)

    if end_date:
        query = query.filter(SensorMeasurements.timestamp <= end_date)

    query = query.order_by(SensorMeasurements.timestamp.desc())
    return query.offset(skip).limit(limit).all()


@router.get(
    "/parcelle/{parcelle_id}",
    response_model=List[SensorMeasurementsResponse],
    summary="Récupérer les mesures d'une parcelle"
)
async def get_measurements_by_parcelle(
    parcelle_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les mesures d'une parcelle.

    Possibilité de filtrer par plage de dates.
    """
    query = db.query(SensorMeasurements).filter(
        SensorMeasurements.parcelle_id == parcelle_id
    )

    if start_date:
        query = query.filter(SensorMeasurements.timestamp >= start_date)

    if end_date:
        query = query.filter(SensorMeasurements.timestamp <= end_date)

    query = query.order_by(SensorMeasurements.timestamp.desc())
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{measurement_id}",
    response_model=SensorMeasurementsResponse,
    summary="Récupérer une mesure par son ID"
)
async def get_measurement(
    measurement_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une mesure spécifique.
    """
    measurement = db.query(SensorMeasurements).filter(
        SensorMeasurements.id == measurement_id
    ).first()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesure non trouvée"
        )

    return measurement


@router.put(
    "/{measurement_id}",
    response_model=SensorMeasurementsResponse,
    summary="Mettre à jour une mesure"
)
async def update_measurement(
    measurement_id: str,
    data: SensorMeasurementsUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une mesure de capteur.

    Seuls les champs fournis seront mis à jour.
    """
    measurement = db.query(SensorMeasurements).filter(
        SensorMeasurements.id == measurement_id
    ).first()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesure non trouvée"
        )

    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(measurement, field, value)

    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete(
    "/{measurement_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une mesure"
)
async def delete_measurement(
    measurement_id: str,
    db: Session = Depends(get_db)
):
    """
    Supprimer une mesure de capteur.
    """
    measurement = db.query(SensorMeasurements).filter(
        SensorMeasurements.id == measurement_id
    ).first()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesure non trouvée"
        )

    db.delete(measurement)
    db.commit()
    return {"message": "Mesure supprimée avec succès"}


@router.get(
    "/statistics/capteur/{capteur_id}",
    summary="Statistiques d'un capteur"
)
async def get_capteur_statistics(
    capteur_id: str,
    days: int = Query(7, ge=1, le=365, description="Nombre de jours à analyser"),
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques des mesures d'un capteur sur une période donnée.

    Retourne les moyennes, min et max pour chaque paramètre mesuré.
    """
    from sqlalchemy import func

    start_date = datetime.utcnow() - timedelta(days=days)

    stats = db.query(
        func.avg(SensorMeasurements.ph).label('avg_ph'),
        func.min(SensorMeasurements.ph).label('min_ph'),
        func.max(SensorMeasurements.ph).label('max_ph'),
        func.avg(SensorMeasurements.temperature).label('avg_temp'),
        func.min(SensorMeasurements.temperature).label('min_temp'),
        func.max(SensorMeasurements.temperature).label('max_temp'),
        func.avg(SensorMeasurements.humidity).label('avg_humidity'),
        func.min(SensorMeasurements.humidity).label('min_humidity'),
        func.max(SensorMeasurements.humidity).label('max_humidity'),
        func.avg(SensorMeasurements.azote).label('avg_azote'),
        func.avg(SensorMeasurements.phosphore).label('avg_phosphore'),
        func.avg(SensorMeasurements.potassium).label('avg_potassium'),
        func.count(SensorMeasurements.id).label('total_measurements')
    ).filter(
        SensorMeasurements.capteur_id == capteur_id,
        SensorMeasurements.timestamp >= start_date
    ).first()

    return {
        "capteur_id": capteur_id,
        "period_days": days,
        "total_measurements": stats.total_measurements,
        "ph": {
            "average": float(stats.avg_ph) if stats.avg_ph else None,
            "min": float(stats.min_ph) if stats.min_ph else None,
            "max": float(stats.max_ph) if stats.max_ph else None
        },
        "temperature": {
            "average": float(stats.avg_temp) if stats.avg_temp else None,
            "min": float(stats.min_temp) if stats.min_temp else None,
            "max": float(stats.max_temp) if stats.max_temp else None
        },
        "humidity": {
            "average": float(stats.avg_humidity) if stats.avg_humidity else None,
            "min": float(stats.min_humidity) if stats.min_humidity else None,
            "max": float(stats.max_humidity) if stats.max_humidity else None
        },
        "nutrients": {
            "azote_avg": float(stats.avg_azote) if stats.avg_azote else None,
            "phosphore_avg": float(stats.avg_phosphore) if stats.avg_phosphore else None,
            "potassium_avg": float(stats.avg_potassium) if stats.avg_potassium else None
        }
    }


@router.get(
    "/latest/capteur/{capteur_id}",
    response_model=SensorMeasurementsResponse,
    summary="Dernière mesure d'un capteur"
)
async def get_latest_measurement(
    capteur_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer la dernière mesure enregistrée par un capteur.
    """
    measurement = db.query(SensorMeasurements).filter(
        SensorMeasurements.capteur_id == capteur_id
    ).order_by(SensorMeasurements.timestamp.desc()).first()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune mesure trouvée pour ce capteur"
        )

    return measurement
