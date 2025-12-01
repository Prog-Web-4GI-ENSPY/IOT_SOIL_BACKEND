import enum
from sqlalchemy import Column, String, DateTime, ForeignKey,Enum
from sqlalchemy.orm import relationship
from .base import BaseModel

class StatutCapteur(str, enum.Enum):
    """
    Énumération des statuts possibles pour un capteur.
    Hérite de 'str' pour une meilleure compatibilité avec Pydantic et l'API.
    """
    ACTIF = "actif"
    INACTIF = "inactif"
    MAINTENANCE = "maintenance"
    ERREUR = "erreur"
    
class Capteur(BaseModel):
    __tablename__ = "capteurs"

    nom = Column(String(200), nullable=False, index=True)

    # Configuration LoRaWAN
    dev_eui = Column(String(16), unique=True, nullable=False, index=True)  # 16 caractères hex

    # Localisation
    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)

    # Colonne Enum utilisant la classe StatutCapteur
    """
    statut = Column(
        Enum(StatutCapteur, values_callable=lambda x: [e.value for e in x]),
        default=StatutCapteur.INACTIF,
        nullable=False
    )
    """
    # Métadonnées
    date_installation = Column(DateTime, nullable=False)
    date_activation = Column(DateTime)


    # Relations
    parcelle = relationship("Parcelle", back_populates="capteurs")
    donnees = relationship("SensorMeasurements", back_populates="capteur", cascade="all, delete-orphan")

