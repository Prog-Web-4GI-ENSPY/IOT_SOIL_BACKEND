from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.models.capteur import Capteur
from app.schemas.capteur import CapteurCreate, CapteurUpdate


class CRUDCapteur:
    """
    Opérations CRUD sur le modèle Capteur.
    """
    
    # --- GET et GET_BY_DEVEUI ---

    def get(self, db: Session, capteur_id: str) -> Optional[Capteur]:
        """Récupère un capteur par son ID (UUID)."""
        return db.query(Capteur).filter(Capteur.id == capteur_id).first()

    def get_by_dev_eui(self, db: Session, dev_eui: str) -> Optional[Capteur]:
        """Récupère un capteur par son DevEUI unique."""
        # Note: Le DevEUI est stocké en majuscule grâce à la validation du schéma
        return db.query(Capteur).filter(Capteur.dev_eui == dev_eui.upper()).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Capteur]:
        """Récupère plusieurs capteurs (avec pagination)."""
        return db.query(Capteur).offset(skip).limit(limit).all()

    # --- CRÉATION (POST) ---
    
    def create(self, db: Session, obj_in: CapteurCreate) -> Capteur:
        """Crée un nouveau capteur."""
        
        # 1. Vérifie l'unicité du DevEUI
        if self.get_by_dev_eui(db, obj_in.dev_eui):
            raise ValueError(f"Un capteur avec le DevEUI '{obj_in.dev_eui}' existe déjà.")

        # 2. Crée l'objet modèle à partir du schéma
        # obj_in.model_dump() contient déjà les champs avec le DevEUI en majuscule
        db_obj = Capteur(**obj_in.model_dump())
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # --- MISE À JOUR (PUT/PATCH) ---
    
    def update(self, db: Session, db_obj: Capteur, obj_in: CapteurUpdate) -> Capteur:
        """Met à jour les attributs d'un capteur existant."""
        
        update_data = obj_in.model_dump(exclude_unset=True) 

        # Si le DevEUI est mis à jour, il est déjà validé et en majuscule par le schéma CapteurUpdate
        if 'dev_eui' in update_data:
            # Assurez-vous qu'il n'y a pas de conflit avec un autre capteur
            if self.get_by_dev_eui(db, update_data['dev_eui']) and update_data['dev_eui'] != db_obj.dev_eui:
                raise ValueError(f"Ce DevEUI est déjà utilisé par un autre capteur.")
                
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # --- SUPPRESSION (DELETE) ---
    
    def remove(self, db: Session, capteur_id: str) -> Capteur:
        """Supprime un capteur par son ID."""
        db_obj = self.get(db, capteur_id)
        if not db_obj:
            raise ValueError(f"Capteur avec ID {capteur_id} non trouvé.")
            
        db.delete(db_obj)
        db.commit()
        return db_obj

# Instanciation pour l'importation par le routeur
capteur_crud = CRUDCapteur()