from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import BaseModel
import uuid


class TypeSol(str, enum.Enum):
    ARGILEUX = "argileux"
    SABLEUX = "sableux"
    LIMONEUX = "limoneux"
    HUMIFERE = "humifère"
    CALCAIRE = "calcaire"
    TOURBEUX = "tourbeux"


class StatutParcelle(str, enum.Enum):
    ACTIVE = "active"
    EN_CULTURE = "en_culture"
    EN_JACHERE = "en_jachère"
    EN_PREPARATION = "en_préparation"
    RECOLTE_EN_COURS = "récolte_en_cours"



class SystemeIrrigation(str, enum.Enum):
    GOUTTE_A_GOUTTE = "goutte_à_goutte"
    ASPERSION = "aspersion"
    GRAVITAIRE = "gravitaire"
    PIVOT = "pivot"
    AUCUN = "aucun"


class Parcelle(BaseModel):
    __tablename__ = "parcelles"

    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True)
    description = Column(String(1000))
    
    # Relation terrain
    terrain_id = Column(String(36), ForeignKey("terrains.id"), nullable=False, index=True)
    
    # Géométrie
    superficie = Column(Float, nullable=False)  # hectares

    
    # Caractéristiques du sol (JSON pour flexibilité)
    type_sol = Column(SQLEnum(TypeSol), nullable=False)

    
    # Statut et culture
    statut = Column(SQLEnum(StatutParcelle), default=StatutParcelle.ACTIVE, nullable=False)
    culture_actuelle_id = Column(String(36), ForeignKey("cultures.id"), index=True)
    date_plantation = Column(DateTime)
    date_recolte_estimee = Column(DateTime)
    
    # Irrigation
    systeme_irrigation = Column(SQLEnum(SystemeIrrigation))
    source_eau = Column(String(200))

    sensor_measurements = relationship( "SensorData", back_populates="parcelle" ) 

    # Relations
    terrain = relationship("Terrain", back_populates="parcelles")
    culture_actuelle = relationship("Culture")
    capteurs = relationship("Capteur", back_populates="parcelle", cascade="all, delete-orphan")
    historique_cultures = relationship("HistoriqueCulture", back_populates="parcelle", cascade="all, delete-orphan")


class HistoriqueCulture(BaseModel):
    __tablename__ = "historique_cultures"

    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)
    culture_id = Column(String(36), ForeignKey("cultures.id"), nullable=False, index=True)
    date_plantation = Column(DateTime, nullable=False)
    date_recolte = Column(DateTime)
    rendement = Column(Float)  # tonnes/ha
    qualite = Column(String(50))  # excellente | bonne | moyenne | faible
    notes = Column(String(1000))

    # Relations
    parcelle = relationship("Parcelle", back_populates="historique_cultures")
    culture = relationship("Culture")
