from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.parcelle import Parcelle, HistoriqueCulture
from app.schemas.parcelle import ParcelleCreate, ParcelleUpdate
import uuid
from datetime import datetime


class ParcelleService:
    """Service pour la gestion des parcelles"""
    
    @staticmethod
    def generate_code(db: Session) -> str:
        """Générer un code numérique unique pour la parcelle (1, 2, 3...)"""
        # Récupérer le code le plus élevé
        # On essaie de convertir en entier pour le tri si possible, sinon tri alphabétique
        all_codes = db.query(Parcelle.code).all()
        
        numeric_codes = []
        for c in all_codes:
            try:
                numeric_codes.append(int(c[0]))
            except (ValueError, TypeError):
                continue
        
        if not numeric_codes:
            return "1"
            
        return str(max(numeric_codes) + 1)
    
    @staticmethod
    def get_parcelle_by_code(db: Session, code: str, user_id: str) -> Parcelle:
        """Récupérer une parcelle par son code unique"""
        from app.models.terrain import Terrain

        # On fait une jointure avec Terrain pour vérifier que la parcelle 
        # appartient bien à un terrain possédé par l'utilisateur
        parcelle = db.query(Parcelle).join(Terrain).filter(
            Parcelle.code == code,
            Terrain.user_id == user_id,
            Parcelle.deleted_at.is_(None)
        ).first()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parcelle avec le code '{code}' non trouvée"
            )
        
        return parcelle
        
    @staticmethod
    def create_parcelle(
        db: Session, 
        parcelle_data: ParcelleCreate, 
        user_id: str
    ) -> Parcelle:
        """Créer une nouvelle parcelle"""
        # Vérifier que le terrain appartient à l'utilisateur
        from app.models.terrain import Terrain
        terrain = db.query(Terrain).filter(
            Terrain.id == parcelle_data.terrain_id,
            Terrain.user_id == user_id,
            Terrain.deleted_at.is_(None)
        ).first()
        
        if not terrain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Terrain non trouvé ou accès refusé"
            )
        
        try:
            code = ParcelleService.generate_code(db)
            
            parcelle = Parcelle(
                id=str(uuid.uuid4()),
                nom=parcelle_data.nom,
                code=code,
                description=parcelle_data.description,
                terrain_id=parcelle_data.terrain_id,
                superficie=parcelle_data.superficie
            )
            
            db.add(parcelle)
            db.commit()
            db.refresh(parcelle)
            return parcelle
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de la parcelle: {str(e)}"
            )
    
    @staticmethod
    def get_parcelle_by_id(db: Session, parcelle_id: str, user_id: str) -> Parcelle:
        """Récupérer une parcelle par son ID"""
        from app.models.terrain import Terrain

        parcelle = db.query(Parcelle).join(Terrain).filter(
            Parcelle.id == parcelle_id,
            Terrain.user_id == user_id,
            Parcelle.deleted_at.is_(None)
        ).first()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcelle non trouvée"
            )
        
        return parcelle
    
    @staticmethod
    def get_parcelles_by_terrain(
        db: Session, 
        terrain_id: str, 
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Parcelle]:
        """Récupérer toutes les parcelles d'un terrain"""
        from app.models.terrain import Terrain

        # Vérifier que le terrain appartient à l'utilisateur
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
        
        return db.query(Parcelle).filter(
            Parcelle.terrain_id == terrain_id,
            Parcelle.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_parcelles_admin(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Parcelle]:
        """Récupérer toutes les parcelles du système (Admin uniquement)"""
        return db.query(Parcelle).filter(
            Parcelle.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_parcelle(
        db: Session, 
        parcelle_id: str, 
        parcelle_data: ParcelleUpdate, 
        user_id: str
    ) -> Parcelle:
        """Mettre à jour une parcelle"""
        parcelle = ParcelleService.get_parcelle_by_id(db, parcelle_id, user_id)
        
        update_data = parcelle_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(parcelle, field, value)
        
        try:
            db.commit()
            db.refresh(parcelle)
            return parcelle
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la mise à jour: {str(e)}"
            )
    
    @staticmethod
    def delete_parcelle(db: Session, parcelle_id: str, user_id: str) -> dict:
        """Supprimer une parcelle (soft delete)"""
        parcelle = ParcelleService.get_parcelle_by_id(db, parcelle_id, user_id)
        
        try:
            parcelle.soft_delete()
            db.commit()
            return {"message": "Parcelle supprimée avec succès"}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )
    
    @staticmethod
    def archive_culture(db: Session, parcelle: Parcelle) -> HistoriqueCulture:
        """Archiver la culture actuelle dans l'historique"""
        # FIX: Cette méthode est conservée pour la compatibilité mais ne fait plus rien 
        # car les champs culture_actuelle_id et date_plantation ont été supprimés de Parcelle.
        return None
    
    @staticmethod
    def get_historique_cultures(
        db: Session, 
        parcelle_id: str, 
        user_id: str
    ) -> List[HistoriqueCulture]:
        """Récupérer l'historique des cultures d'une parcelle"""
        parcelle = ParcelleService.get_parcelle_by_id(db, parcelle_id, user_id)
        
        return db.query(HistoriqueCulture).filter(
            HistoriqueCulture.parcelle_id == parcelle.id,
            HistoriqueCulture.deleted_at.is_(None)
        ).order_by(HistoriqueCulture.date_plantation.desc()).all()
    
    @staticmethod
    def get_parcelle_statistics(db: Session, terrain_id: str, user_id: str) -> dict:
        """Obtenir les statistiques des parcelles d'un terrain"""
        from app.models.terrain import Terrain

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
        
        stats = db.query(
            func.count(Parcelle.id).label('total'),
            func.sum(Parcelle.superficie).label('superficie_totale')
        ).filter(
            Parcelle.terrain_id == terrain_id,
            Parcelle.deleted_at.is_(None)
        ).first()
        
        return {
            "terrain_id": terrain_id,
            "total_parcelles": stats.total or 0,
            "superficie_totale": float(stats.superficie_totale or 0)
        }