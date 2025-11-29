from pydantic import Field, model_validator
from typing import Optional
from datetime import datetime
import re
from app.schemas.common import BaseSchema, ResponseBase 

# --- Schémas pour la Création/Mise à Jour ---

class CapteurBase(BaseSchema):
    nom: str = Field(..., min_length=2, max_length=200)
    dev_eui: str = Field(..., min_length=16, max_length=16, description="DevEUI LoRaWAN (16 caractères hexadécimaux)")
    parcelle_id: str = Field(..., description="UUID de la Parcelle associée")
    date_installation: datetime
    date_activation: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def validate_dev_eui(cls, data: dict):
        # Validation DevEUI comme hexadécimal (vérification avant la création du modèle)
        if 'dev_eui' in data and data['dev_eui']:
            v = data['dev_eui']
            if not re.match(r'^[0-9A-Fa-f]{16}$', v):
                raise ValueError('Le DevEUI doit être une chaîne hexadécimale de 16 caractères.')
            # Stocke en majuscule pour l'uniformité dans la base de données
            data['dev_eui'] = v.upper()
        return data

class CapteurCreate(CapteurBase):
    pass

class CapteurUpdate(BaseSchema):
    # Rendre tous les champs optionnels pour la mise à jour (PATCH)
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    dev_eui: Optional[str] = Field(None, min_length=16, max_length=16)
    parcelle_id: Optional[str] = None
    date_installation: Optional[datetime] = None
    date_activation: Optional[datetime] = None
    
    # La validation du DevEUI est toujours appliquée si le champ est fourni
    @model_validator(mode='before')
    @classmethod
    def validate_dev_eui_update(cls, data: dict):
        if 'dev_eui' in data and data['dev_eui']:
            v = data['dev_eui']
            if not re.match(r'^[0-9A-Fa-f]{16}$', v):
                raise ValueError('Le DevEUI doit être une chaîne hexadécimale de 16 caractères.')
            data['dev_eui'] = v.upper()
        return data


# --- Schéma de Réponse (pour Lecture) ---

class Capteur(ResponseBase, CapteurBase):
    """
    Schéma complet pour la réponse, héritant de l'ID et des timestamps.
    """

    pass