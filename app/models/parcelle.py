from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import BaseModel
import uuid


class Parcelle(BaseModel):
    __tablename__ = "parcelles"

    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True)
    description = Column(String(1000))
    
    # Relation terrain
    terrain_id = Column(String(36), ForeignKey("terrains.id"), nullable=False, index=True)
    
    # Géométrie
    superficie = Column(Float, nullable=False)  # hectares

    sensor_measurements = relationship( "SensorMeasurements", back_populates="parcelle" ) 

    # Relations
    terrain = relationship("Terrain", back_populates="parcelles")
    recommandations = relationship("Recommendation", back_populates="parcelle")
    capteurs = relationship("Capteur", back_populates="parcelle", cascade="all, delete-orphan")
    historique_cultures = relationship("HistoriqueCulture", back_populates="parcelle", cascade="all, delete-orphan")


class HistoriqueCulture(BaseModel):
    __tablename__ = "historique_cultures"

    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)
    culture_nom = Column(String(100), nullable=False)  # Nom de la culture en texte simple
    date_plantation = Column(DateTime, nullable=False)
    date_recolte = Column(DateTime)
    rendement = Column(Float)  # tonnes/ha
    qualite = Column(String(50))  # excellente | bonne | moyenne | faible
    notes = Column(String(1000))

    # Relations
    parcelle = relationship("Parcelle", back_populates="historique_cultures")
