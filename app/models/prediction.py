from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class Prediction(BaseModel):
    __tablename__ = "predictions"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    modele = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=False)
    resultat = Column(JSON, nullable=False)
    date_prediction = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relations
    user = relationship("User", back_populates="predictions")