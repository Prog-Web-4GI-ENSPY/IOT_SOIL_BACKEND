from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class RecommendationBase(BaseModel):
    titre: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    date_creation: Optional[datetime] = None
    parcelle_id: int

    @validator('titre')
    def validate_titre(cls, v):
        if not v.strip():
            raise ValueError('Le titre ne peut pas être vide ou ne contenir que des espaces')
        return v

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationUpdate(RecommendationBase):
    pass

class RecommendationResponse(BaseModel):
    id: int
    titre: str
    description: str
    date_creation: datetime
    parcelle_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 
