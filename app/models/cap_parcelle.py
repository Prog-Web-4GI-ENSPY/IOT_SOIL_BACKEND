from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class CapParcelle(BaseModel):
    __tablename__ = "cap_parcelles"

    capteur_id = Column(String(36), ForeignKey("capteurs.id"), nullable=False, index=True)
    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)
    
    date_assignation = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_desassignation = Column(DateTime, nullable=True)

    # Relations
    capteur = relationship("Capteur", backref="assignments")
    parcelle = relationship("Parcelle", backref="assignments")
