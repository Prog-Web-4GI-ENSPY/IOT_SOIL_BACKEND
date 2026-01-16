from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.terrain import Terrain
from app.models.parcelle import Parcelle
from app.models.capteur import Capteur
from app.schemas.terrain import TerrainResponse
from app.schemas.parcelle import ParcelleResponse
from app.services.terrain_service import TerrainService
from app.services.parcelle_service import ParcelleService
from sqlalchemy import func

router = APIRouter(
    prefix="/admin",
    tags=["Administration"]
)

@router.get("/dashboard", summary="Tableau de bord administrateur")
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Obtenir les statistiques globales du système.
    """
    user_count = db.query(func.count(User.id)).scalar()
    terrain_count = db.query(func.count(Terrain.id)).filter(Terrain.deleted_at.is_(None)).scalar()
    parcelle_count = db.query(func.count(Parcelle.id)).filter(Parcelle.deleted_at.is_(None)).scalar()
    capteur_count = db.query(func.count(Capteur.id)).scalar()

    return {
        "users": user_count or 0,
        "terrains": terrain_count or 0,
        "parcelles": parcelle_count or 0,
        "capteurs": capteur_count or 0
    }

@router.get("/terrains", response_model=List[TerrainResponse], summary="Lister tous les terrains (Admin)")
async def get_all_terrains_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Récupérer tous les terrains de tous les utilisateurs.
    """
    return TerrainService.get_all_terrains_admin(db, skip, limit)

@router.get("/parcelles", response_model=List[ParcelleResponse], summary="Lister toutes les parcelles (Admin)")
async def get_all_parcelles_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Récupérer toutes les parcelles de tous les utilisateurs.
    """
    return ParcelleService.get_all_parcelles_admin(db, skip, limit)
