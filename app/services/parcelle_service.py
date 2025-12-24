from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.parcelle import Parcelle, StatutParcelle, HistoriqueCulture
from app.schemas.parcelle import ParcelleCreate, ParcelleUpdate
import uuid
from datetime import datetime


class ParcelleService:
    """Service pour la gestion des parcelles"""
    
    @staticmethod
    def generate_code(db: Session, terrain_id: str) -> str:
        """Générer un code unique pour la parcelle"""
        count = db.query(func.count(Parcelle.id)).filter(
            Parcelle.terrain_id == terrain_id
        ).scalar()
        
        return f"PARC-{terrain_id[:8]}-{count + 1:04d}"
    
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
        
        # Vérifier que la superficie de la parcelle ne dépasse pas celle du terrain
        superficie_parcelles = db.query(func.sum(Parcelle.superficie)).filter(
            Parcelle.terrain_id == parcelle_data.terrain_id,
            Parcelle.deleted_at.is_(None)
        ).scalar() or 0
        
        if superficie_parcelles + parcelle_data.superficie > terrain.superficie_totale:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La superficie totale des parcelles dépasse celle du terrain"
            )
        
        try:
            code = parcelle_data.code or ParcelleService.generate_code(db, parcelle_data.terrain_id)
            
            parcelle = Parcelle(
                id=str(uuid.uuid4()),
                nom=parcelle_data.nom,
                code=code,
                description=parcelle_data.description,
                terrain_id=parcelle_data.terrain_id,
                superficie=parcelle_data.superficie,
                type_sol=parcelle_data.type_sol or "Non spécifié",
                systeme_irrigation=parcelle_data.systeme_irrigation,
                source_eau=parcelle_data.source_eau
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
    def update_parcelle(
        db: Session, 
        parcelle_id: str, 
        parcelle_data: ParcelleUpdate, 
        user_id: str
    ) -> Parcelle:
        """Mettre à jour une parcelle"""
        parcelle = ParcelleService.get_parcelle_by_id(db, parcelle_id, user_id)
        
        update_data = parcelle_data.dict(exclude_unset=True)
        
        # Si on met à jour la culture, enregistrer dans l'historique
        if 'culture_actuelle_id' in update_data and update_data['culture_actuelle_id']:
            if parcelle.culture_actuelle_id and parcelle.culture_actuelle_id != update_data['culture_actuelle_id']:
                ParcelleService.archive_culture(db, parcelle)
        
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
        if not parcelle.culture_actuelle_id:
            return None
        
        historique = HistoriqueCulture(
            id=str(uuid.uuid4()),
            parcelle_id=parcelle.id,
            culture_id=parcelle.culture_actuelle_id,
            date_plantation=parcelle.date_plantation or datetime.utcnow(),
            date_recolte=datetime.utcnow()
        )
        
        db.add(historique)
        return historique
    
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
            func.sum(Parcelle.superficie).label('superficie_totale'),
            Parcelle.statut
        ).filter(
            Parcelle.terrain_id == terrain_id,
            Parcelle.deleted_at.is_(None)
        ).group_by(Parcelle.statut).all()
        
        return {
            "terrain_id": terrain_id,
            "statistiques": [
                {
                    "statut": stat.statut,
                    "nombre": stat.total,
                    "superficie": float(stat.superficie_totale or 0)
                }
                for stat in stats
            ]
        }