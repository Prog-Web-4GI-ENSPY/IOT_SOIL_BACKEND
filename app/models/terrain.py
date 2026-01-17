from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class Terrain(BaseModel):
    __tablename__ = "terrains"

    nom = Column(String(200), nullable=False, index=True)
    description = Column(String(1000))
    
    # Localisation
    localite_id = Column(String(36), ForeignKey("localites.id"), nullable=False, index=True)

    @property
    def nombre_parcelles(self):
        return len(self.parcelles)
        
    # Caractéristiques
    altitude_moyenne = Column(Float)  # mètres
    
    # Propriétaire
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)


    # Relations
    localite = relationship("Localite", back_populates="terrains")
    proprietaire = relationship("User", back_populates="terrains")
    parcelles = relationship("Parcelle", back_populates="terrain", cascade="all, delete-orphan")
