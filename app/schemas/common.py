from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# --- Configuration Pydantic v2 ---

# Model config pour tous les schémas, permettant de lire les données
# directement depuis les objets SQLAlchemy (from_attributes = True)
CustomConfig = ConfigDict(
    from_attributes = True,
    # Permet de convertir les champs (ex: CamelCase des JSON en snake_case Python) si nécessaire.
    # alias_generator = to_snake_case 

)
# --- 1. BaseSchema (Pour Création/Mise à Jour) ---

class BaseSchema(BaseModel):
    """
    Schéma de base pour les requêtes (POST, PUT). 
    N'inclut pas l'ID ni les horodatages générés par la base de données.
    """
    model_config = CustomConfig
    pass # Peut être vide, ou contenir des configurations de validation globales

# --- 2. ResponseBase (Pour Lecture/Réponse) ---

class ResponseBase(BaseSchema):
    """
    Schéma de base pour les réponses API (GET).
    Ajoute les champs d'identification et d'horodatage.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
# --- 3. Message de Succès/Erreur (Optionnel mais Utile) ---

class HTTPError(BaseModel):
    """
    Schéma générique pour les réponses d'erreur.
    """
    detail: str

class SuccessResponse(BaseModel):
    """
    Schéma pour une réponse de succès simple.
    """
    message: str = "Opération réussie."
    
