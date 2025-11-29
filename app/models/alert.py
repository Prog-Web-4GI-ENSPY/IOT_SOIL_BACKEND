from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

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
    
    # Relationships
    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)
    parcelle = relationship("Parcelle", back_populates="alerts")

    # Optional: Link to the sensor data that triggered it
    # sensor_data_id = Column(Integer, ForeignKey("sensor_data.id"), nullable=True)
    # sensor_data = relationship("SensorData")

    def __repr__(self):
        return f"<Alert(id={self.id}, niveau='{self.niveau}', resolue={self.est_resolue})>"