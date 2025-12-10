from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.terrain_service import TerrainService
from app.schemas.terrain import TerrainCreate, TerrainUpdate, TerrainResponse
from app.models.terrain import StatutTerrain
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/terrains",
    tags=["Terrains"]
)


@router.post(
    "/",
    response_model=TerrainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau terrain"
)
async def create_terrain(
    terrain_data: TerrainCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau terrain agricole.
    
    - **nom**: Nom du terrain (obligatoire)
    - **type_terrain**: Type de terrain (agricole, pastoral, mixte, experimental)
    - **localite_id**: ID de la localité
    - **superficie_totale**: Superficie en hectares
    - **latitude**: Latitude GPS
    - **longitude**: Longitude GPS
    """
    return TerrainService.create_terrain(db, terrain_data, str(current_user.id))


@router.get(
    "/",
    response_model=List[TerrainResponse],
    summary="Récupérer tous les terrains"
)
async def get_all_terrains(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    statut: Optional[StatutTerrain] = Query(None, description="Filtrer par statut"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer tous les terrains de l'utilisateur connecté.
    
    Possibilité de filtrer par statut et paginer les résultats.
    """
    return TerrainService.get_all_terrains(
        db, str(current_user.id), skip, limit, statut
    )


@router.get(
    "/statistics",
    summary="Statistiques des terrains"
)
async def get_terrain_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques des terrains de l'utilisateur.
    
    Retourne le nombre de terrains et la superficie totale par statut.
    """
    return TerrainService.get_terrain_statistics(db, str(current_user.id))


@router.get(
    "/{terrain_id}",
    response_model=TerrainResponse,
    summary="Récupérer un terrain par son ID"
)
async def get_terrain(
    terrain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'un terrain spécifique.
    """
    return TerrainService.get_terrain_by_id(db, terrain_id, str(current_user.id))


@router.put(
    "/{terrain_id}",
    response_model=TerrainResponse,
    summary="Mettre à jour un terrain"
)
async def update_terrain(
    terrain_id: str,
    terrain_data: TerrainUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les informations d'un terrain.
    
    Seuls les champs fournis seront mis à jour.
    """
    return TerrainService.update_terrain(
        db, terrain_id, terrain_data, str(current_user.id)
    )


@router.delete(
    "/{terrain_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer un terrain"
)
async def delete_terrain(
    terrain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer un terrain (suppression logique).
    
    Le terrain ne sera pas physiquement supprimé mais marqué comme supprimé.
    """
    return TerrainService.delete_terrain(db, terrain_id, str(current_user.id))