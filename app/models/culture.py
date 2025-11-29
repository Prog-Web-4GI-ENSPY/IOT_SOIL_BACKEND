# app/models/culture.py

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base import BaseModel 

class Culture(BaseModel):
    """
    Modèle SQLAlchemy pour une culture (Crop).
    """
    __tablename__ = "cultures"

    # Champs de base
    nom = Column(String(100), index=True, unique=True, nullable=False)
    description = Column(Text)
    type_culture = Column(String(50)) # Ex: 'Céréale', 'Légumineuse', 'Racine'
    
    # Relations (si nécessaire pour un futur lien avec les Parcelles)
    # parcelles = relationship("Parcelle", back_populates="culture")

    def __repr__(self):
        return f"<Culture(id={self.id}, nom='{self.nom}')>"