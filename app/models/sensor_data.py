from sqlalchemy import Column, String, DateTime,Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class SensorMeasurements(BaseModel):
    __tablename__ = "sensor_measurements"

    ph = Column(Float)
    azote = Column(Float)  # kg/ha
    phosphore = Column(Float)  # kg/ha
    potassium = Column(Float)  # kg/ha
    humidity = Column(Float) 
    temperature = Column(Float)  # °C
    capteur_id = Column(String(36), ForeignKey("capteurs.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    measurements = Column(JSON, nullable=False)  # Stocke les mesures du capteur en JSON

    # Relations
    capteur = relationship("Capteur", back_populates="donnees")
    parcelle = relationship("Parcelle", back_populates="donnees_capteurs")