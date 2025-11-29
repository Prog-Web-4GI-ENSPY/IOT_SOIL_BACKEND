# app/schemas/culture.py

from pydantic import Field
from typing import Optional
from .common import BaseSchema, ResponseBase

# --- Schéma de Base (pour Création et Mise à Jour) ---
class CultureBase(BaseSchema):
    """
    Schéma de base contenant les attributs modifiables d'une culture.
    """
    nom: str = Field(..., max_length=100, description="Nom commun de la culture (ex: Maïs, Manioc).")
    description: Optional[str] = Field(None, description="Description ou notes spécifiques sur la variété.")
    type_culture: Optional[str] = Field(None, max_length=50, description="Catégorie (ex: Céréale).")

# --- Schéma pour la Création ---
class CultureCreate(CultureBase):
    """
    Schéma utilisé pour la création d'une nouvelle culture.
    """
    # Aucune modification nécessaire ici, hérite de CultureBase
    pass

# --- Schéma pour la Mise à Jour ---
class CultureUpdate(CultureBase):
    """
    Schéma utilisé pour la mise à jour des données d'une culture.
    Tous les champs sont optionnels.
    """
    nom: Optional[str] = None
    description: Optional[str] = None
    type_culture: Optional[str] = None

# --- Schéma de Réponse (pour Lecture) ---
class Culture(ResponseBase, CultureBase):
    """
    Schéma complet utilisé lors de la lecture des données, incluant ID et timestamps.
    """
    # Hérite de CultureBase et ResponseBase (id, created_at, updated_at)
    pass