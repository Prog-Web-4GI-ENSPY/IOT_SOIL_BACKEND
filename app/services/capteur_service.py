from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from datetime import datetime

from app.models.capteur import Capteur, StatutCapteur
from app.models.parcelle import Parcelle
from app.schemas.capteur import CapteurCreate, CapteurUpdate
import uuid

class CapteurService:
    
    def get_capteur(self, db: Session, capteur_id: str) -> Optional[Capteur]:
        """Récupérer un capteur par ID"""
        return db.query(Capteur).filter(Capteur.id == capteur_id).first()
    
    def get_capteur_by_dev_eui(
        self,
        db: Session,
        dev_eui: str
    ) -> Optional[Capteur]:
        """Récupérer un capteur par DevEUI"""
        return db.query(Capteur).filter(Capteur.dev_eui == dev_eui).first()
    
    def get_capteur_by_code(
        self, 
        db: Session, 
        code: str, 
        user_id: Optional[str] = None
    ) -> Optional[Capteur]:
        """Récupérer un capteur par son code unique"""
        query = db.query(Capteur)
        
        # Si un user_id est fourni, on sécurise la requête par une jointure
        if user_id:
            from app.models.terrain import Terrain
            query = query.join(Parcelle).join(Terrain).filter(
                Terrain.user_id == user_id
            )
            
        capteur = query.filter(Capteur.code == code).first()
        
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capteur avec le code '{code}' non trouvé"
            )
            
        return capteur
        
    def get_capteurs(
        self,
        db: Session,
        user_id: Optional[str] = None,
        parcelle_id: Optional[str] = None,
        terrain_id: Optional[str] = None,
        statut: Optional[StatutCapteur] = None,
        type_capteur: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Capteur]:
        """Récupérer une liste de capteurs avec filtres"""
        query = db.query(Capteur)
        
        # Filtrer par parcelle
        if parcelle_id:
            query = query.filter(Capteur.parcelle_id == parcelle_id)
        
        # Filtrer par terrain (via parcelle)
        if terrain_id:
            query = query.join(Parcelle).filter(
                Parcelle.terrain_id == terrain_id
            )
        
        # Filtrer par user (via terrain et parcelle)
        if user_id:
            from app.models.terrain import Terrain
            query = query.join(Parcelle).join(Terrain).filter(
                Terrain.user_id == user_id
            )
        
        # Filtrer par statut
        if statut:
            query = query.filter(Capteur.statut == statut)
        
        # Filtrer par type
        if type_capteur:
            query = query.filter(Capteur.type_capteur == type_capteur)
        
        return query.offset(skip).limit(limit).all()
    
    def create_capteur(self, db: Session, capteur_data: CapteurCreate) -> Capteur:
        """Créer un nouveau capteur"""
        # 1. Vérifier que la parcelle existe (si fournie)
        if capteur_data.parcelle_id:
            target_parcelle_id = str(capteur_data.parcelle_id)
            parcelle = db.query(Parcelle).filter(
                Parcelle.id == target_parcelle_id
            ).first()
            
            if not parcelle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parcelle {target_parcelle_id} non trouvée"
                )
        
        # 3. Vérifier l'unicité du DevEUI
        if capteur_data.dev_eui:
            existing_dev_eui = db.query(Capteur).filter(
                Capteur.dev_eui == capteur_data.dev_eui
            ).first()
            
            if existing_dev_eui:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce DevEUI est déjà utilisé"
                )
        
        # 4. Vérifier l'unicité du code
        if capteur_data.code:
            existing_code = db.query(Capteur).filter(
                Capteur.code == capteur_data.code
            ).first()
            
            if existing_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce code est déjà utilisé"
                )
        
        # 5. Créer l'objet
        capteur_dict = capteur_data.dict()
        if capteur_dict.get('parcelle_id'):
            capteur_dict['parcelle_id'] = str(capteur_dict['parcelle_id'])
        
        db_capteur = Capteur(
            **capteur_dict,
            statut=StatutCapteur.INACTIF
        )
        
        db.add(db_capteur)
        db.commit()
        db.refresh(db_capteur)
        
        return db_capteur
    
    def update_capteur(
        self,
        db: Session,
        capteur_id: str,
        capteur_data: CapteurUpdate
    ) -> Capteur:
        """Mettre à jour un capteur"""
        capteur = self.get_capteur(db, capteur_id)
        
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Capteur non trouvé"
            )
        
        # Mettre à jour les champs fournis
        update_data = capteur_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(capteur, field, value)
        
        capteur.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(capteur)
        
        return capteur
    
    def delete_capteur(self, db: Session, capteur_id: str) -> bool:
        """Supprimer un capteur"""
        capteur = self.get_capteur(db, capteur_id)
        
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Capteur non trouvé"
            )
        
        db.delete(capteur)
        db.commit()
        
        return True
    
    def update_capteur_status(
        self,
        db: Session,
        capteur_id: str,
        statut: StatutCapteur,
        last_seen: Optional[datetime] = None,
        battery_level: Optional[int] = None,
        signal_quality: Optional[int] = None
    ) -> Capteur:
        """Mettre à jour le statut d'un capteur"""
        capteur = self.get_capteur(db, capteur_id)
        
        if not capteur:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Capteur non trouvé"
            )
        
        capteur.statut = statut
        
        if last_seen:
            capteur.last_seen = last_seen
        
        if battery_level is not None:
            capteur.battery_level = battery_level
            
            # Mettre le statut à BATTERIE_FAIBLE si < 20%
            if battery_level < 20:
                capteur.statut = StatutCapteur.BATTERIE_FAIBLE
        
        if signal_quality is not None:
            capteur.signal_quality = signal_quality
        
        capteur.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(capteur)
        
        return capteur
    
    def get_capteurs_offline(
        self,
        db: Session,
        minutes_threshold: int = 30
    ) -> List[Capteur]:
        """Récupérer les capteurs hors ligne"""
        threshold_time = datetime.utcnow() - timedelta(minutes=minutes_threshold)
        
        return db.query(Capteur).filter(
            or_(
                Capteur.last_seen < threshold_time,
                Capteur.last_seen.is_(None)
            )
        ).all()
    
    def get_capteurs_low_battery(
        self,
        db: Session,
        threshold: int = 20
    ) -> List[Capteur]:
        """Récupérer les capteurs avec batterie faible"""
        return db.query(Capteur).filter(
            Capteur.battery_level < threshold
        ).all()
    
    def get_statistics(
        self,
        db: Session,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtenir les statistiques des capteurs"""
        query = db.query(Capteur)
        
        if user_id:
            from app.models.terrain import Terrain
            query = query.join(Parcelle).join(Terrain).filter(
                Terrain.user_id == user_id
            )
        
        total = query.count()
        online = query.filter(Capteur.statut == StatutCapteur.ACTIF).count()
        offline = query.filter(Capteur.statut == StatutCapteur.INACTIF).count()
        maintenance = query.filter(
            Capteur.statut == StatutCapteur.MAINTENANCE
        ).count()
        low_battery = query.filter(
            Capteur.battery_level < 20
        ).count()
        
        return {
            "total": total,
            "online": online,
            "offline": offline,
            "maintenance": maintenance,
            "low_battery": low_battery,
            "online_percentage": (online / total * 100) if total > 0 else 0
        }


capteur_service = CapteurService()
