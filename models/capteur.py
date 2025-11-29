from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class Capteur(BaseModel):
    __tablename__ = "capteurs"

    nom = Column(String(200), nullable=False, index=True)

    # Configuration LoRaWAN
    dev_eui = Column(String(16), unique=True, nullable=False, index=True)  # 16 caractères hex

    # Localisation
    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)

    # Métadonnées
    date_installation = Column(DateTime, nullable=False)
    date_activation = Column(DateTime)


    # Relations
    parcelle = relationship("Parcelle", back_populates="capteurs")
    donnees = relationship("DonneeCapteur", back_populates="capteur", cascade="all, delete-orphan")

