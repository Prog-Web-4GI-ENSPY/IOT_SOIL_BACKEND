from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import BaseModel


class TypeTerrain(str, enum.Enum):
    AGRICOLE = "agricole"
    PASTORAL = "pastoral"
    MIXTE = "mixte"
    EXPERIMENTAL = "experimental"


class StatutTerrain(str, enum.Enum):
    ACTIF = "actif"
    EN_JACHERE = "en_jachère"
    EN_PREPARATION = "en_préparation"
    ABANDONNE = "abandonné"


class Terrain(BaseModel):
    __tablename__ = "terrains"

    nom = Column(String(200), nullable=False, index=True)
    description = Column(String(1000))
    type_terrain = Column(SQLEnum(TypeTerrain), nullable=False)
    statut = Column(SQLEnum(StatutTerrain), default=StatutTerrain.ACTIF, nullable=False)
    
    # Localisation
    localite_id = Column(String(36), ForeignKey("localites.id"), nullable=False, index=True)

    @property
    def latitude(self):
        return self.localite.latitude if self.localite else None

    @property
    def longitude(self):
        return self.localite.longitude if self.localite else None

    @property
    def nombre_parcelles(self):
        return len(self.parcelles)
        
    # Caractéristiques
    superficie_totale = Column(Float, nullable=False)  # hectares
    perimetre = Column(Float)  # mètres
    altitude_moyenne = Column(Float)  # mètres
    pente = Column(Float)  # degrés
    
    # Propriétaire
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Dates
    date_acquisition = Column(DateTime)


    # Relations
    localite = relationship("Localite", back_populates="terrains")
    proprietaire = relationship("User", back_populates="terrains")
    parcelles = relationship("Parcelle", back_populates="terrain", cascade="all, delete-orphan")

