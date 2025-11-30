import enum
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey,Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class TypeAlerte(str, enum.Enum):
    """
    Définit les types d'alerte possibles (par exemple, ce qui est mesuré).
    """
    HUMIDITE = "humidite"
    TEMPERATURE = "temperature"
    PH = "ph"
    BATTERIE = "batterie" # Alerte technique

class SeveriteAlerte(str, enum.Enum):
    """
    Définit la gravité de l'alerte.
    """
    FAIBLE = "faible"
    MOYENNE = "moyenne"
    CRITIQUE = "critique"
    
class Alert(BaseModel):
    """
    Modèle SQLAlchemy pour une alerte critique.
    """
    __tablename__ = "alerts"

    # Fields
    niveau = Column(String, nullable=False) # Ex: 'Critique', 'Avertissement'
    message = Column(Text, nullable=False)
    date_declenchement = Column(DateTime, default=datetime.utcnow, nullable=False)
    est_resolue = Column(Boolean, default=False, nullable=False)
    
    # Utilisation des Enums dans les colonnes SQLAlchemy
    type_alerte = Column(
        Enum(TypeAlerte, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    severite = Column(
        Enum(SeveriteAlerte, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # Relationships
    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)
    parcelle = relationship("Parcelle", back_populates="alerts")

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False) 

    # Définition de la relation inverse (pour le back_populates)
    user = relationship("User", back_populates="alerts")
    # Optional: Link to the sensor data that triggered it
    # sensor_data_id = Column(Integer, ForeignKey("sensor_data.id"), nullable=True)
    # sensor_data = relationship("SensorData")

    def __repr__(self):
        return f"<Alert(id={self.id}, niveau='{self.niveau}', resolue={self.est_resolue})>"
