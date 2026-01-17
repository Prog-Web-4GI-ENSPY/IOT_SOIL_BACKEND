from pydantic import Field, model_validator
from typing import Optional,Any
from datetime import datetime
import re
from app.schemas.common import BaseSchema, ResponseBase 

# --- Schémas pour la Création/Mise à Jour ---

class CapteurBase(BaseSchema):
    nom: str = Field(..., min_length=2, max_length=200)
    dev_eui: str = Field(..., min_length=16, max_length=16, description="DevEUI LoRaWAN (16 caractères hexadécimaux)")
    code:str =Field(..., description=" code de reference associée")
    date_installation: datetime
    date_activation: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def validate_dev_eui(cls, data: Any) -> Any:
        # Si c'est un objet SQLAlchemy (après création)
        if not isinstance(data, dict):
            return data
            
        # Si c'est un dictionnaire (pendant la requête POST)
        dev_eui = data.get('dev_eui')
        if dev_eui:
            if len(dev_eui) != 16:
                raise ValueError("Le DevEUI doit faire exactement 16 caractères")
            # Vérifier si c'est de l'hexadécimal
            try:
                int(dev_eui, 16)
            except ValueError:
                raise ValueError("Le DevEUI doit être une chaîne hexadécimale valide")
        return data

class CapteurCreate(CapteurBase):
    pass

class CapteurUpdate(BaseSchema):
    # Rendre tous les champs optionnels pour la mise à jour (PATCH)
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    dev_eui: Optional[str] = Field(None, min_length=16, max_length=16)
    date_installation: Optional[datetime] = None
    date_activation: Optional[datetime] = None
    
    # La validation du DevEUI est toujours appliquée si le champ est fourni
    @model_validator(mode='before')
    @classmethod
    def validate_dev_eui_update(cls, data: Any):
        if not isinstance(data, dict): # Ajoutez cette sécurité
            return data
        if 'dev_eui' in data and data['dev_eui']:
            v = data['dev_eui']
            if not re.match(r'^[0-9A-Fa-f]{16}$', v):
                raise ValueError('Le DevEUI doit être une chaîne hexadécimale de 16 caractères.')
            data['dev_eui'] = v.upper()
        return data


# --- Schéma de Réponse (pour Lecture) ---

class Capteur(ResponseBase, CapteurBase):
    """
    Schéma complet pour la réponse.
    On force l'ID en str pour accepter les UUID de la base de données.
    """
    id: str
    
    model_config = {"from_attributes": True} 