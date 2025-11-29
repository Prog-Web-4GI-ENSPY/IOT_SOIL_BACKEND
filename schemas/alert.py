from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    niveau: str = Field(..., min_length=3, max_length=50)  # Ex: 'Critique', 'Avertissement'
    message: str = Field(..., min_length=10)
    date_declenchement: Optional[datetime] = None
    est_resolue: bool = False
    parcelle_id: int

    @validator('niveau')
    def validate_niveau(cls, v):
        allowed_levels = {'Critique', 'Avertissement', 'Info'}
        if v not in allowed_levels:
            raise ValueError(f'Niveau doit être l\'un de {allowed_levels}')
        return v

class AlertResponse(BaseModel):
    id: int
    niveau: str
    message: str
    date_declenchement: datetime
    est_resolue: bool
    parcelle_id: int

    class Config:
        orm_mode = True

