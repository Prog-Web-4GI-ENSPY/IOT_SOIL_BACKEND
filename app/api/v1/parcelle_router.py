from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from services.parcelle_service import ParcelleService
from schemas.parcelle import ParcelleCreate, ParcelleUpdate, ParcelleResponse
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/parcelles",
    tags=["Parcelles"]
)


@router.post(
    "/",
    response_model=ParcelleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle parcelle"
)
async def create_parcelle(
    parcelle_data: ParcelleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle parcelle dans un terrain.
    
    - **nom**: Nom de la parcelle (obligatoire)
    - **terrain_id**: ID du terrain parent (obligatoire)
    - **superficie**: Superficie en hectares (obligatoire)
    - **type_sol**: Type de sol
    - **systeme_irrigation**: Système d'irrigation utilisé
    
    La superficie totale des parcelles ne peut pas dépasser celle du terrain.
    Un code unique sera automatiquement généré si non fourni.
    """
    return ParcelleService.create_parcelle(db, parcelle_data, current_user["id"])


@router.get(
    "/terrain/{terrain_id}",
    response_model=List[ParcelleResponse],
    summary="Récupérer les parcelles d'un terrain"
)
async def get_parcelles_by_terrain(
    terrain_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les parcelles d'un terrain spécifique.
    """
    return ParcelleService.get_parcelles_by_terrain(
        db, terrain_id, current_user["id"], skip, limit
    )


@router.get(
    "/terrain/{terrain_id}/statistics",
    summary="Statistiques des parcelles d'un terrain"
)
async def get_parcelle_statistics(
    terrain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques des parcelles d'un terrain.
    
    Retourne le nombre de parcelles et la superficie totale par statut.
    """
    return ParcelleService.get_parcelle_statistics(db, terrain_id, current_user["id"])


@router.get(
    "/{parcelle_id}",
    response_model=ParcelleResponse,
    summary="Récupérer une parcelle par son ID"
)
async def get_parcelle(
    parcelle_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une parcelle spécifique.
    """
    return ParcelleService.get_parcelle_by_id(db, parcelle_id, current_user["id"])


@router.put(
    "/{parcelle_id}",
    response_model=ParcelleResponse,
    summary="Mettre à jour une parcelle"
)
async def update_parcelle(
    parcelle_id: str,
    parcelle_data: ParcelleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les informations d'une parcelle.
    
    Seuls les champs fournis seront mis à jour.
    Si la culture actuelle est modifiée, l'ancienne culture sera archivée.
    """
    return ParcelleService.update_parcelle(
        db, parcelle_id, parcelle_data, current_user["id"]
    )


@router.delete(
    "/{parcelle_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une parcelle"
)
async def delete_parcelle(
    parcelle_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une parcelle (suppression logique).
    
    La parcelle ne sera pas physiquement supprimée mais marquée comme supprimée.
    """
    return ParcelleService.delete_parcelle(db, parcelle_id, current_user["id"])


@router.get(
    "/{parcelle_id}/historique",
    summary="Historique des cultures d'une parcelle"
)
async def get_historique_cultures(
    parcelle_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer l'historique des cultures d'une parcelle.
    
    Retourne toutes les cultures qui ont été plantées sur cette parcelle,
    avec les dates de plantation et de récolte, ainsi que les rendements.
    """
    return ParcelleService.get_historique_cultures(db, parcelle_id, current_user["id"])
