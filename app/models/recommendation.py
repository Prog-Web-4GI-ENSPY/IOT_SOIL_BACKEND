from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class Recommendation(BaseModel):
    """
    Modèle SQLAlchemy pour une recommandation d'action agricole.
    """
    __tablename__ = "recommendations"

    # Fields
    titre = Column(String, nullable=False)
    contenu = Column(Text, nullable=False)
    priorite = Column(String, default="Normal", nullable=False) # Ex: 'Urgent', 'Normal', 'Faible'
    date_emission = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="recommendations")
    
    # Relationships
    parcelle_id = Column(String(36), ForeignKey("parcelles.id"), nullable=False, index=True)
    parcelle = relationship("Parcelle", back_populates="recommandations")

    # Optional: Link to the prediction that triggered it
    # prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    # prediction = relationship("Prediction")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False) 


    def __repr__(self):
        return f"<Recommendation(id={self.id}, titre='{self.titre}', priorite='{self.priorite}')>"
