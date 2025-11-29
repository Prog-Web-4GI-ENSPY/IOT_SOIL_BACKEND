from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class PredictionBase(BaseModel):
    modele: str = Field(..., min_length=3, max_length=100)
    precision: float = Field(..., ge=0.0, le=100.0, description="Précision du modèle en pourcentage")
    date_creation: Optional[datetime] = None
    parcelle_id: int

    @validator('modele')
    def validate_modele(cls, v):
        if not v.strip():
            raise ValueError('Le nom du modèle ne peut pas être vide ou ne contenir que des espaces')
        return v
    
class PredictionCreate(PredictionBase):
    pass

class PredictionUpdate(PredictionBase):
    pass

class PredictionResponse(BaseModel):
    id: int
    modele: str
    precision: float
    date_creation: datetime
    parcelle_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True