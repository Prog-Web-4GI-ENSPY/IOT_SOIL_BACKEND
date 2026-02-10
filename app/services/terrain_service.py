from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.terrain import Terrain
from app.schemas.terrain import TerrainCreate, TerrainUpdate
import uuid


class TerrainService:
    """Service pour la gestion des terrains"""
    
    @staticmethod
    def create_terrain(db: Session, terrain_data: TerrainCreate, user_id: str) -> Terrain:
        """Créer un nouveau terrain"""
        try:
            terrain = Terrain(
                id=str(uuid.uuid4()),
                nom=terrain_data.nom,
                description=terrain_data.description,
                localite_id=terrain_data.localite_id,
                superficie=terrain_data.superficie,
                user_id=user_id
            )
            
            db.add(terrain)
            db.commit()
            db.refresh(terrain)
            return terrain
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création du terrain: {str(e)}"
            )
    
    @staticmethod
    def get_terrain_by_id(db: Session, terrain_id: str, user_id: str) -> Terrain:
        """Récupérer un terrain par son ID"""
        terrain = db.query(Terrain).filter(
            Terrain.id == terrain_id,
            Terrain.user_id == user_id,
            Terrain.deleted_at.is_(None)
        ).first()
        
        if not terrain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Terrain non trouvé"
            )
        
        return terrain
    
    @staticmethod
    def get_all_terrains(
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Terrain]:
        """Récupérer tous les terrains d'un utilisateur"""
        query = db.query(Terrain).filter(
            Terrain.user_id == user_id,
            Terrain.deleted_at.is_(None)
        )
        
        return query.order_by(Terrain.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_terrains_admin(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Terrain]:
        """Récupérer tous les terrains du système (Admin uniquement)"""
        return db.query(Terrain).filter(
            Terrain.deleted_at.is_(None)
        ).order_by(Terrain.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_terrain(
        db: Session, 
        terrain_id: str, 
        terrain_data: TerrainUpdate, 
        user_id: str
    ) -> Terrain:
        """Mettre à jour un terrain"""
        terrain = TerrainService.get_terrain_by_id(db, terrain_id, user_id)
        
        update_data = terrain_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(terrain, field, value)
        
        try:
            db.commit()
            db.refresh(terrain)
            return terrain
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la mise à jour: {str(e)}"
            )
    
    @staticmethod
    def delete_terrain(db: Session, terrain_id: str, user_id: str) -> dict:
        """Supprimer un terrain (soft delete)"""
        terrain = TerrainService.get_terrain_by_id(db, terrain_id, user_id)
        
        try:
            terrain.soft_delete()
            db.commit()
            return {"message": "Terrain supprimé avec succès"}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )
    
    @staticmethod
    def get_terrain_statistics(db: Session, user_id: str) -> dict:
        """Obtenir les statistiques des terrains"""
        total = db.query(func.count(Terrain.id)).filter(
            Terrain.user_id == user_id,
            Terrain.deleted_at.is_(None)
        ).scalar()
        
        return {
            "total_terrains": total or 0
        }
